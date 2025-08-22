"""
Hybrid Retail Analytics Engine - FIXED VERSION
Traditional ML/Stats for analysis + Gemini API only for chatbot queries
"""

import pandas as pd
import numpy as np
import mysql.connector
from datetime import datetime, timedelta
import warnings
import logging
from typing import Dict, Any
import json
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import google.generativeai as genai

# Suppress warnings
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)

# Configure Gemini API (only for chatbot)
GEMINI_API_KEY = "AIzaSyAke42UTE7CjuOfnIHEHwfcaC6tMHH49Zk"
genai.configure(api_key=GEMINI_API_KEY)

def format_rupees(amount):
    """Format amount in Indian Rupees"""
    if amount >= 10000000:
        return f"₹{amount/10000000:.1f}Cr"
    elif amount >= 100000:
        return f"₹{amount/100000:.1f}L"
    elif amount >= 1000:
        return f"₹{amount/1000:.1f}K"
    else:
        return f"₹{amount:.0f}"

class TraditionalDataConnector:
    """Traditional data connector with FIXED datetime handling"""
    
    def __init__(self):
        self.connection_params = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'database': 'inventory_ai'
        }
        
    def get_data(self) -> pd.DataFrame:
        """Get retail data with proper datetime handling"""
        try:
            conn = mysql.connector.connect(**self.connection_params)
            
            query = """
            SELECT 
                sh.id as sale_id,
                sh.product_id,
                sh.product_name,
                sh.quantity_sold,
                sh.amount,
                sh.sale_date,
                p.current_stock,
                p.minimum_stock,
                p.price as unit_price,
                p.expiry_date,
                c.name as category,
                s.name as supplier_name
            FROM sales_history sh
            LEFT JOIN products p ON sh.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE sh.sale_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            ORDER BY sh.sale_date DESC
            LIMIT 10000
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            # FIXED: Proper datetime conversion BEFORE processing
            df['sale_date'] = pd.to_datetime(df['sale_date'], errors='coerce')
            df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
            
            # Drop rows with invalid sale_date
            df = df.dropna(subset=['sale_date'])
            
            if df.empty:
                print("No valid data from database, creating sample data...")
                return self._create_sample_data()
            
            return self._process_data(df)
            
        except Exception as e:
            print(f"Database error: {e}")
            return self._create_sample_data()
    
    def _process_data(self, df):
        """Process data with Indian pricing - FIXED datetime operations"""
        
        # Ensure datetime columns are properly converted
        if not pd.api.types.is_datetime64_any_dtype(df['sale_date']):
            df['sale_date'] = pd.to_datetime(df['sale_date'], errors='coerce')
        
        if 'expiry_date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['expiry_date']):
            df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
        
        # Drop any remaining invalid dates
        df = df.dropna(subset=['sale_date'])
        
        # Convert to Indian Rupees
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce') * 83
        df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce') * 83
        
        # Now safe to use .dt accessor
        df['month'] = df['sale_date'].dt.month
        df['quarter'] = df['sale_date'].dt.quarter
        df['weekday'] = df['sale_date'].dt.day_name()
        
        # Financial calculations
        df['cost'] = df['amount'] * 0.7
        df['profit'] = df['amount'] - df['cost']
        df['profit_margin'] = np.where(df['amount'] > 0, (df['profit'] / df['amount']) * 100, 0)
        
        # Customer simulation
        np.random.seed(42)
        df['customer_id'] = np.random.choice(range(1, 1000), size=len(df))
        
        # Inventory processing
        df['current_stock'] = pd.to_numeric(df['current_stock'], errors='coerce').fillna(0)
        df['minimum_stock'] = pd.to_numeric(df['minimum_stock'], errors='coerce').fillna(5)
        df['stock_ratio'] = np.where(df['minimum_stock'] > 0, 
                                   df['current_stock'] / df['minimum_stock'], 1)
        
        # Days to expiry (only if expiry_date exists)
        if 'expiry_date' in df.columns:
            current_time = pd.Timestamp.now()
            df['days_to_expiry'] = (df['expiry_date'] - current_time).dt.days
            df['is_expiring_soon'] = df['days_to_expiry'] < 30
        else:
            df['days_to_expiry'] = np.nan
            df['is_expiring_soon'] = False
        
        return df
    
    def _create_sample_data(self):
        """Create Indian retail sample data with PROPER datetime types"""
        np.random.seed(42)
        
        indian_products = {
            'Electronics': [
                ('iPhone 15', 129900, 'Apple Store India', 15, 5, '2026-12-31'),
                ('Samsung Galaxy S24', 79999, 'Samsung India', 25, 10, '2026-12-31'),
                ('OnePlus 12', 64999, 'OnePlus India', 30, 12, '2026-12-31'),
                ('Boat Airdopes', 2999, 'Boat Lifestyle', 80, 30, '2026-12-31')
            ],
            'Fashion & Lifestyle': [
                ('Nike Air Force 1', 7995, 'Nike India', 60, 25, '2026-12-31'),
                ('Adidas Ultraboost', 16999, 'Adidas', 45, 18, '2026-12-31'),
                ('Levi\'s 511 Jeans', 3999, 'Levi\'s', 70, 30, '2026-12-31')
            ],
            'Home & Kitchen': [
                ('Prestige Pressure Cooker', 2999, 'Prestige', 60, 25, '2030-12-31'),
                ('Bajaj Mixer Grinder', 4999, 'Bajaj', 45, 20, '2030-12-31'),
                ('Philips Air Fryer', 12999, 'Philips India', 25, 10, '2030-12-31')
            ],
            'Grocery & Food': [
                ('Amul Butter 500g', 250, 'Amul', 300, 120, '2025-12-31'),
                ('Tata Salt 1kg', 25, 'Tata Consumer', 500, 200, '2026-12-31'),
                ('Maggi Noodles', 14, 'Nestle', 800, 300, '2025-11-30'),
                ('Britannia Biscuits', 35, 'Britannia', 400, 150, '2025-10-31')
            ],
            'Personal Care': [
                ('Himalaya Face Wash', 149, 'Himalaya', 100, 40, '2026-06-30'),
                ('Lakme Lipstick', 599, 'Lakme', 80, 32, '2027-12-31'),
                ('Dove Soap', 89, 'HUL', 200, 80, '2026-12-31')
            ]
        }
        
        sample_data = []
        start_date = datetime.now() - timedelta(days=365)
        
        for category, product_list in indian_products.items():
            for product_name, price, supplier, max_stock, min_stock, expiry in product_list:
                
                num_sales = np.random.randint(200, 500)
                
                for _ in range(num_sales):
                    sale_date = start_date + timedelta(days=np.random.randint(0, 365))
                    
                    # Seasonal patterns
                    month = sale_date.month
                    seasonal_factor = 1.0
                    
                    if month in [10, 11]:  # Diwali season
                        seasonal_factor = 1.6
                    elif month in [12, 1, 2]:  # Wedding season
                        seasonal_factor = 1.3
                    elif month in [6, 7, 8]:  # Monsoon
                        seasonal_factor = 0.8
                    elif month in [4, 5]:  # Summer sales
                        seasonal_factor = 1.1
                    
                    quantity = max(1, int(np.random.poisson(2) * seasonal_factor))
                    final_price = price * quantity * np.random.uniform(0.95, 1.05)
                    
                    sample_data.append({
                        'sale_id': len(sample_data) + 1,
                        'product_id': hash(product_name) % 10000,
                        'product_name': product_name,
                        'quantity_sold': quantity,
                        'amount': round(final_price, 2),
                        'sale_date': sale_date,  # Already datetime object
                        'current_stock': np.random.randint(min_stock, max_stock),
                        'minimum_stock': min_stock,
                        'unit_price': price,
                        'expiry_date': expiry,  # Will be converted to datetime in _process_data
                        'category': category,
                        'supplier_name': supplier,
                        'customer_id': np.random.randint(1, 1000)
                    })
        
        df = pd.DataFrame(sample_data)
        
        # CRITICAL: Ensure proper datetime conversion for sample data
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        df['expiry_date'] = pd.to_datetime(df['expiry_date'])
        
        return self._process_data(df)

class TraditionalAnalyticsEngine:
    """Traditional ML/Statistical Analysis Engine - FIXED VERSION"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.logger = logging.getLogger(__name__)
        
        # Validate datetime columns
        if not pd.api.types.is_datetime64_any_dtype(self.data['sale_date']):
            self.logger.warning("sale_date is not datetime type, converting...")
            self.data['sale_date'] = pd.to_datetime(self.data['sale_date'], errors='coerce')
            self.data = self.data.dropna(subset=['sale_date'])
        
    def run_complete_analysis(self) -> Dict[str, Any]:
        """Run traditional analytics with ML and statistics"""
        
        try:
            results = {}
            
            # Descriptive Analytics
            results['descriptive'] = self._descriptive_analysis()
            
            # Diagnostic Analytics
            results['diagnostic'] = self._diagnostic_analysis()
            
            # Predictive Analytics
            results['predictive'] = self._predictive_analysis()
            
            # Prescriptive Analytics
            results['prescriptive'] = self._prescriptive_analysis()
            
            # Metadata
            results['metadata'] = {
                'timestamp': datetime.now().isoformat(),
                'total_records': len(self.data),
                'analysis_period': {
                    'start': self.data['sale_date'].min().strftime('%Y-%m-%d'),
                    'end': self.data['sale_date'].max().strftime('%Y-%m-%d')
                },
                'currency': 'INR'
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {'error': str(e)}
    
    def _descriptive_analysis(self) -> Dict[str, Any]:
        """Traditional descriptive statistics with FIXED datetime operations"""
        
        # Basic metrics
        basic_metrics = {
            'total_revenue': float(self.data['amount'].sum()),
            'total_profit': float(self.data['profit'].sum()),
            'total_transactions': len(self.data),
            'unique_products': self.data['product_name'].nunique(),
            'unique_customers': self.data['customer_id'].nunique(),
            'avg_order_value': float(self.data['amount'].mean()),
            'profit_margin': float((self.data['profit'].sum() / self.data['amount'].sum()) * 100),
            'max_sale_date': self.data['sale_date'].max().strftime('%Y-%m-%d'),
            'min_sale_date': self.data['sale_date'].min().strftime('%Y-%m-%d'),
            'max_sale_amount': float(self.data['amount'].max()),
            'min_sale_amount': float(self.data['amount'].min())
        }
        
        # Product analysis
        try:
            product_summary = self.data.groupby('product_name').agg({
                'amount': ['sum', 'mean', 'count'],
                'quantity_sold': 'sum',
                'current_stock': 'first',
                'minimum_stock': 'first',
                'category': 'first',
                'days_to_expiry': 'first'
            }).round(2)
            
            product_summary.columns = ['total_revenue', 'avg_price', 'transaction_count', 
                                     'total_units_sold', 'current_stock', 'minimum_stock', 
                                     'category', 'days_to_expiry']
            
            # Top performers
            top_products = product_summary.nlargest(10, 'total_revenue')
        except Exception as e:
            self.logger.error(f"Product analysis failed: {e}")
            top_products = pd.DataFrame()
        
        # Category analysis
        try:
            category_performance = self.data.groupby('category').agg({
                'amount': 'sum',
                'quantity_sold': 'sum',
                'profit': 'sum'
            }).round(2)
        except Exception as e:
            self.logger.error(f"Category analysis failed: {e}")
            category_performance = pd.DataFrame()
        
        # Monthly trends with FIXED datetime operations
        try:
            # Use proper period conversion
            monthly_sales = self.data.groupby(self.data['sale_date'].dt.to_period('M'))['amount'].sum()
            monthly_trend = {str(k): float(v) for k, v in monthly_sales.items()}
        except Exception as e:
            self.logger.error(f"Monthly trend analysis failed: {e}")
            monthly_trend = {}
        
        # Customer segmentation
        try:
            customer_metrics = self.data.groupby('customer_id').agg({
                'amount': ['sum', 'mean', 'count'],
                'sale_date': 'max'
            })
            customer_metrics.columns = ['total_spent', 'avg_order', 'frequency', 'last_purchase']
            
            # Calculate recency safely
            current_time = self.data['sale_date'].max()
            customer_metrics['recency'] = (current_time - customer_metrics['last_purchase']).dt.days
            
            # Simple RFM segmentation
            def segment_customer(row):
                if row['total_spent'] > customer_metrics['total_spent'].quantile(0.8) and row['recency'] < 30:
                    return 'VIP'
                elif row['frequency'] > 5 and row['recency'] < 60:
                    return 'Loyal'
                elif row['recency'] > 90:
                    return 'At Risk'
                else:
                    return 'Regular'
            
            customer_metrics['segment'] = customer_metrics.apply(segment_customer, axis=1)
            customer_segments = customer_metrics['segment'].value_counts().to_dict()
        except Exception as e:
            self.logger.error(f"Customer segmentation failed: {e}")
            customer_segments = {}
        
        # Products expiring soon
        try:
            if 'is_expiring_soon' in self.data.columns:
                expiring_products = self.data[self.data['is_expiring_soon'] == True]['product_name'].value_counts().to_dict()
            else:
                expiring_products = {}
        except Exception as e:
            self.logger.error(f"Expiring products analysis failed: {e}")
            expiring_products = {}
        
        return {
            'basic_metrics': basic_metrics,
            'top_products': top_products.to_dict('index') if not top_products.empty else {},
            'category_performance': category_performance.to_dict('index') if not category_performance.empty else {},
            'monthly_trend': monthly_trend,
            'customer_segments': customer_segments,
            'expiring_products': expiring_products,
            'product_summary': product_summary.to_dict('index') if 'product_summary' in locals() and not product_summary.empty else {}
        }
    
    def _diagnostic_analysis(self) -> Dict[str, Any]:
        """ML-powered diagnostic analysis with FIXED datetime operations"""
        
        # Anomaly detection using Isolation Forest
        try:
            daily_sales = self.data.groupby(self.data['sale_date'].dt.date).agg({
                'amount': 'sum',
                'quantity_sold': 'sum',
                'customer_id': 'nunique'
            }).fillna(0)
            
            # ML anomaly detection
            if len(daily_sales) > 10:
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                anomaly_labels = iso_forest.fit_predict(daily_sales)
                anomaly_dates = daily_sales[anomaly_labels == -1].index.tolist()
                
                anomalies = {
                    'ml_anomalies': [str(date) for date in anomaly_dates],
                    'count': len(anomaly_dates)
                }
            else:
                anomalies = {'ml_anomalies': [], 'count': 0}
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
            anomalies = {'ml_anomalies': [], 'count': 0}
        
        # Correlation analysis
        try:
            numeric_cols = ['amount', 'quantity_sold', 'profit', 'profit_margin']
            available_cols = [col for col in numeric_cols if col in self.data.columns]
            
            if len(available_cols) > 1:
                correlation_matrix = self.data[available_cols].corr().round(3).to_dict()
            else:
                correlation_matrix = {}
        except Exception as e:
            self.logger.error(f"Correlation analysis failed: {e}")
            correlation_matrix = {}
        
        # Declining products analysis with FIXED datetime operations
        try:
            product_trends = {}
            for product in self.data['product_name'].unique():
                product_data = self.data[self.data['product_name'] == product]
                
                # Use proper period grouping
                monthly_sales = product_data.groupby(product_data['sale_date'].dt.to_period('M'))['amount'].sum()
                
                if len(monthly_sales) >= 3:
                    recent_avg = monthly_sales.tail(2).mean()
                    earlier_avg = monthly_sales.head(2).mean()
                    
                    if earlier_avg > 0:
                        trend_change = ((recent_avg - earlier_avg) / earlier_avg) * 100
                        if trend_change < -15:
                            product_trends[product] = float(trend_change)
        except Exception as e:
            self.logger.error(f"Product trends analysis failed: {e}")
            product_trends = {}
        
        # Inventory issues
        try:
            inventory_analysis = self.data.groupby('product_name').agg({
                'current_stock': 'first',
                'minimum_stock': 'first',
                'amount': 'sum'
            })
            
            understocked = inventory_analysis[inventory_analysis['current_stock'] < inventory_analysis['minimum_stock']]
            overstocked = inventory_analysis[inventory_analysis['current_stock'] > inventory_analysis['minimum_stock'] * 3]
        except Exception as e:
            self.logger.error(f"Inventory analysis failed: {e}")
            understocked = pd.DataFrame()
            overstocked = pd.DataFrame()
        
        return {
            'anomalies': anomalies,
            'correlations': correlation_matrix,
            'declining_products': product_trends,
            'inventory_issues': {
                'understocked': understocked.index.tolist(),
                'overstocked': overstocked.index.tolist(),
                'understocked_count': len(understocked),
                'overstocked_count': len(overstocked)
            }
        }
    
    def _predictive_analysis(self) -> Dict[str, Any]:
        """ML-powered predictive analysis with FIXED datetime operations"""
        
        # Sales forecasting using Linear Regression
        try:
            daily_sales = self.data.groupby(self.data['sale_date'].dt.date)['amount'].sum().reset_index()
            daily_sales['days'] = (daily_sales['sale_date'] - daily_sales['sale_date'].min()).dt.days
            
            if len(daily_sales) > 5:
                # Simple linear trend model
                X = daily_sales[['days']]
                y = daily_sales['amount']
                
                model = LinearRegression()
                model.fit(X, y)
                
                # Forecast next 30 days
                future_days = np.arange(daily_sales['days'].max() + 1, daily_sales['days'].max() + 31).reshape(-1, 1)
                forecast = model.predict(future_days)
                
                forecast_total = float(sum(forecast))
                trend = 'increasing' if model.coef_[0] > 0 else 'decreasing'
                
                sales_forecast = {
                    'next_30_days_total': forecast_total,
                    'daily_average': float(forecast_total / 30),
                    'trend': trend,
                    'confidence': float(model.score(X, y))
                }
            else:
                sales_forecast = {'error': 'Insufficient data for forecasting'}
        except Exception as e:
            self.logger.error(f"Sales forecasting failed: {e}")
            sales_forecast = {'error': str(e)}
        
        # Customer churn prediction (rule-based)
        try:
            customer_last_purchase = self.data.groupby('customer_id')['sale_date'].max()
            current_date = self.data['sale_date'].max()
            days_since_last = (current_date - customer_last_purchase).dt.days
            
            at_risk_customers = days_since_last[days_since_last > 60].index.tolist()
            churn_risk = {
                'at_risk_count': len(at_risk_customers),
                'at_risk_customers': at_risk_customers[:20],
                'churn_rate': float(len(at_risk_customers) / len(days_since_last) * 100)
            }
        except Exception as e:
            self.logger.error(f"Churn prediction failed: {e}")
            churn_risk = {'error': str(e)}
        
        # Demand forecasting for top products
        try:
            top_products = self.data['product_name'].value_counts().head(10).index
            demand_forecast = {}
            
            for product in top_products:
                product_data = self.data[self.data['product_name'] == product]
                monthly_demand = product_data.groupby(product_data['sale_date'].dt.to_period('M'))['quantity_sold'].sum()
                
                if len(monthly_demand) > 0:
                    avg_monthly_demand = monthly_demand.mean()
                    demand_forecast[product] = float(avg_monthly_demand)
        except Exception as e:
            self.logger.error(f"Demand forecasting failed: {e}")
            demand_forecast = {}
        
        return {
            'sales_forecast': sales_forecast,
            'churn_prediction': churn_risk,
            'demand_forecast': demand_forecast
        }
    
    def _prescriptive_analysis(self) -> Dict[str, Any]:
        """Rule-based prescriptive recommendations"""
        
        recommendations = []
        
        try:
            # Get analysis results
            desc_results = self._descriptive_analysis()
            diag_results = self._diagnostic_analysis()
            pred_results = self._predictive_analysis()
            
            # Profit margin recommendation
            profit_margin = desc_results['basic_metrics'].get('profit_margin', 0)
            if profit_margin < 25:
                recommendations.append({
                    'type': 'Revenue Optimization',
                    'priority': 'High',
                    'title': 'Improve Profit Margins',
                    'description': f"Current margin {profit_margin:.1f}% is below target of 25%",
                    'actions': [
                        'Review pricing strategy for low-margin products',
                        'Negotiate better supplier terms',
                        'Focus marketing on high-margin products',
                        'Implement cost reduction measures'
                    ],
                    'expected_impact': 'Increase profit margin by 5-8%',
                    'timeline': '2-3 months'
                })
            
            # Inventory recommendations
            inventory_issues = diag_results.get('inventory_issues', {})
            understocked_count = inventory_issues.get('understocked_count', 0)
            
            if understocked_count > 0:
                understocked_products = inventory_issues.get('understocked', [])
                recommendations.append({
                    'type': 'Inventory Management',
                    'priority': 'High',
                    'title': 'Urgent Restocking Required',
                    'description': f"{understocked_count} products are below minimum stock",
                    'actions': [
                        f"Immediately restock: {', '.join(understocked_products[:5])}",
                        'Implement automatic reorder points',
                        'Improve demand forecasting',
                        'Establish safety stock buffers'
                    ],
                    'expected_impact': 'Prevent stockouts and lost sales',
                    'timeline': '1-2 weeks'
                })
            
            # Customer retention
            if 'churn_prediction' in pred_results and 'error' not in pred_results['churn_prediction']:
                churn_count = pred_results['churn_prediction'].get('at_risk_count', 0)
                if churn_count > 0:
                    recommendations.append({
                        'type': 'Customer Retention',
                        'priority': 'Medium',
                        'title': 'Customer Churn Prevention',
                        'description': f"{churn_count} customers at risk of churning",
                        'actions': [
                            'Launch targeted retention campaigns',
                            'Offer personalized discounts to at-risk customers',
                            'Improve customer service touchpoints',
                            'Implement loyalty reward programs'
                        ],
                        'expected_impact': 'Reduce churn rate by 30-40%',
                        'timeline': '1-2 months'
                    })
            
            # Product focus recommendations
            declining = diag_results.get('declining_products', {})
            if declining:
                worst_products = list(declining.keys())[:3]
                recommendations.append({
                    'type': 'Product Strategy',
                    'priority': 'Medium',
                    'title': 'Address Declining Products',
                    'description': f"{len(declining)} products showing sales decline",
                    'actions': [
                        f"Review strategy for: {', '.join(worst_products)}",
                        'Consider promotional campaigns',
                        'Analyze competitor pricing',
                        'Evaluate product discontinuation'
                    ],
                    'expected_impact': 'Stabilize or improve declining sales',
                    'timeline': '2-3 months'
                })
            
            # Expiring products
            expiring = desc_results.get('expiring_products', {})
            if expiring:
                recommendations.append({
                    'type': 'Inventory Management',
                    'priority': 'High',
                    'title': 'Handle Expiring Products',
                    'description': f"{len(expiring)} products expiring within 30 days",
                    'actions': [
                        'Launch clearance sales for expiring products',
                        'Offer bulk discounts to clear inventory',
                        'Improve inventory rotation practices',
                        'Negotiate supplier return agreements'
                    ],
                    'expected_impact': 'Minimize losses from expired products',
                    'timeline': '2-4 weeks'
                })
                
        except Exception as e:
            self.logger.error(f"Prescriptive analysis failed: {e}")
            recommendations.append({
                'type': 'System',
                'priority': 'High',
                'title': 'Analysis System Error',
                'description': f"Error generating recommendations: {str(e)}",
                'actions': ['Check data quality', 'Verify system configuration'],
                'expected_impact': 'Restore full analytics capability',
                'timeline': 'Immediate'
            })
        
        return {
            'recommendations': recommendations,
            'priority_summary': {
                'high_priority': len([r for r in recommendations if r.get('priority') == 'High']),
                'medium_priority': len([r for r in recommendations if r.get('priority') == 'Medium']),
                'total_actions': len(recommendations)
            }
        }

class GeminiDataChatbot:
    """Gemini API integration ONLY for chatbot queries about data"""
    
    def __init__(self, data: pd.DataFrame, analysis_results: Dict[str, Any]):
        self.data = data
        self.analysis_results = analysis_results
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.conversation_history = []
    
    def query_data(self, question: str) -> str:
        """Use Gemini API to answer specific questions about the data"""
        
        # Prepare data context for Gemini
        data_context = self._prepare_data_context()
        
        prompt = f"""
        You are a data analyst assistant. Answer the user's question about this retail business data.
        
        AVAILABLE DATA CONTEXT:
        {data_context}
        
        USER QUESTION: {question}
        
        Rules:
        1. Answer ONLY based on the provided data
        2. Give specific numbers and dates when asked
        3. If data is not available, say so clearly
        4. Be concise and accurate
        5. Format currency in Indian Rupees (₹)
        6. For dates, use YYYY-MM-DD format
        
        Provide a direct, data-driven answer to the question.
        """
        
        try:
            response = self.model.generate_content(prompt)
            answer = response.text
            
            # Store conversation
            self.conversation_history.append({
                'question': question,
                'answer': answer
            })
            
            return answer
            
        except Exception as e:
            return f"Sorry, I couldn't process your question: {e}"
    
    def _prepare_data_context(self) -> str:
        """Prepare comprehensive data context for Gemini"""
        
        if not self.analysis_results or 'descriptive' not in self.analysis_results:
            return "No analysis data available"
        
        # Extract key data points
        desc = self.analysis_results.get('descriptive', {})
        basic_metrics = desc.get('basic_metrics', {})
        
        # Prepare specific data points that users commonly ask about
        context = f"""
BUSINESS OVERVIEW:
- Total Revenue: ₹{basic_metrics.get('total_revenue', 0):,.2f}
- Total Transactions: {basic_metrics.get('total_transactions', 0):,}
- Unique Products: {basic_metrics.get('unique_products', 0)}
- Unique Customers: {basic_metrics.get('unique_customers', 0)}
- Profit Margin: {basic_metrics.get('profit_margin', 0):.2f}%
- Maximum Sale Date: {basic_metrics.get('max_sale_date', 'N/A')}
- Minimum Sale Date: {basic_metrics.get('min_sale_date', 'N/A')}
- Highest Sale Amount: ₹{basic_metrics.get('max_sale_amount', 0):,.2f}
- Lowest Sale Amount: ₹{basic_metrics.get('min_sale_amount', 0):,.2f}

TOP SELLING PRODUCTS:
{json.dumps(list(desc.get('top_products', {}).keys())[:10], indent=2)}

CATEGORIES:
{json.dumps(list(desc.get('category_performance', {}).keys()), indent=2)}

CUSTOMER SEGMENTS:
{json.dumps(desc.get('customer_segments', {}), indent=2)}

PRODUCTS EXPIRING SOON:
{json.dumps(list(desc.get('expiring_products', {}).keys())[:10], indent=2)}

INVENTORY ISSUES:
- Understocked Products: {json.dumps(self.analysis_results.get('diagnostic', {}).get('inventory_issues', {}).get('understocked', [])[:10], indent=2)}
- Overstocked Products: {json.dumps(self.analysis_results.get('diagnostic', {}).get('inventory_issues', {}).get('overstocked', [])[:10], indent=2)}

DECLINING PRODUCTS:
{json.dumps(list(self.analysis_results.get('diagnostic', {}).get('declining_products', {}).keys())[:10], indent=2)}

SALES FORECAST:
{json.dumps(self.analysis_results.get('predictive', {}).get('sales_forecast', {}), indent=2)}

ANALYSIS PERIOD: {self.analysis_results.get('metadata', {}).get('analysis_period', {})}
        """
        
        return context

class HybridAnalyticsEngine:
    """Main engine combining traditional analytics + Gemini chatbot"""
    
    def __init__(self):
        self.data_connector = TraditionalDataConnector()
        
    def run_analysis(self):
        """Run complete hybrid analysis"""
        
        print("🔄 Loading data...")
        data = self.data_connector.get_data()
        
        # Validate data
        if data.empty:
            raise ValueError("No data available for analysis")
        
        print(f"✅ Loaded {len(data)} records")
        print(f"📅 Date range: {data['sale_date'].min().strftime('%Y-%m-%d')} to {data['sale_date'].max().strftime('%Y-%m-%d')}")
        
        print("📊 Running traditional analytics...")
        analytics_engine = TraditionalAnalyticsEngine(data)
        analysis_results = analytics_engine.run_complete_analysis()
        
        if 'error' in analysis_results:
            raise ValueError(f"Analysis failed: {analysis_results['error']}")
        
        print("🤖 Initializing Gemini chatbot...")
        chatbot = GeminiDataChatbot(data, analysis_results)
        
        print("✅ Analysis complete!")
        
        return {
            'data': data,
            'analysis_results': analysis_results,
            'chatbot': chatbot
        }

if __name__ == "__main__":
    # Test the system
    try:
        engine = HybridAnalyticsEngine()
        results = engine.run_analysis()
        
        # Test chatbot
        chatbot = results['chatbot']
        
        # Example queries
        test_queries = [
            "What is the maximum sale date?",
            "Which products are expiring soon?",
            "What is the total revenue?",
            "Which products need restocking?",
            "What are the top 5 selling products?"
        ]
        
        print("\n🤖 Testing Gemini Chatbot:")
        for query in test_queries:
            print(f"\nQ: {query}")
            answer = chatbot.query_data(query)
            print(f"A: {answer}")
            
    except Exception as e:
        print(f"❌ System error: {e}")










