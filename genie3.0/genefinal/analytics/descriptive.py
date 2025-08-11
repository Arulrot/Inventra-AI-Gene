import pymysql
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from scipy import stats
from scipy.stats import pearsonr
import warnings

warnings.filterwarnings('ignore')
sns.set_style("whitegrid")
pio.renderers.default = "browser"

# Enhanced Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'inventory_ai',
    'connect_timeout': 10,
    'read_timeout': 30,
    'write_timeout': 30,
    'charset': 'utf8mb4',
    'autocommit': True
}

class EnterpriseInventoryAnalytics:
    """
    Enterprise-Grade Inventory Analytics System
    Features: Advanced ML, Interactive Dashboards, Predictive Models, Business Intelligence
    """
    
    def __init__(self):
        """Initialize with enhanced connection and data structures"""
        self.connection = self._establish_connection()
        self.df_products = pd.DataFrame()
        self.df_sales = pd.DataFrame()
        self.df_suppliers = pd.DataFrame()
        self.df_categories = pd.DataFrame()
        self.insights = {}
        
    def _establish_connection(self):
        """Establish robust database connection"""
        try:
            conn = pymysql.connect(**DB_CONFIG)
            print("✅ Enterprise connection established with PyMySQL!")
            return conn
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            raise
    
    def load_and_enrich_data(self):
        """Load data with advanced preprocessing and feature engineering"""
        print("📊 Loading and enriching data with advanced features...")
        
        # Enhanced Products Query with calculated fields
        products_query = """
        SELECT p.*, 
               c.name as category_name, 
               s.name as supplier_name,
               DATEDIFF(p.expiry_date, CURDATE()) as days_to_expiry,
               (p.price * p.current_stock) as inventory_value,
               CASE 
                   WHEN p.current_stock <= p.minimum_stock * 0.5 THEN 'Critical'
                   WHEN p.current_stock <= p.minimum_stock THEN 'Low' 
                   WHEN p.current_stock <= p.minimum_stock * 2 THEN 'Medium'
                   ELSE 'High'
               END as stock_status
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        """
        
        self.df_products = pd.read_sql(products_query, self.connection)
        
        # Enhanced Sales Query with time features
        sales_query = """
        SELECT sh.*, 
               p.name as product_name, 
               p.price,
               c.name as category_name,
               DAYOFWEEK(sh.sale_date) as day_of_week,
               MONTH(sh.sale_date) as month,
               QUARTER(sh.sale_date) as quarter,
               HOUR(sh.sale_date) as hour
        FROM sales_history sh
        JOIN products p ON sh.product_id = p.id
        LEFT JOIN categories c ON p.category_id = c.id
        """
        
        self.df_sales = pd.read_sql(sales_query, self.connection)
        
        # Load reference tables
        self.df_suppliers = pd.read_sql("SELECT * FROM suppliers", self.connection)
        self.df_categories = pd.read_sql("SELECT * FROM categories", self.connection)
        
        print(f"   ✅ Loaded {len(self.df_products)} products with {self.df_products.shape[1]} features")
        print(f"   ✅ Loaded {len(self.df_sales)} sales records with temporal features")
        
        # Advanced preprocessing
        self._advanced_preprocessing()
        
    def _advanced_preprocessing(self):
        """Advanced data preprocessing and feature engineering - FIXED"""
        print("🔧 Performing advanced preprocessing...")
        
        # Date conversions
        self.df_sales['sale_date'] = pd.to_datetime(self.df_sales['sale_date'])
        self.df_products['date_added'] = pd.to_datetime(self.df_products['date_added'])
        self.df_products['expiry_date'] = pd.to_datetime(self.df_products['expiry_date'])
        
        # Advanced time features for sales
        self.df_sales['is_weekend'] = self.df_sales['day_of_week'].isin([1, 7])
        self.df_sales['season'] = self.df_sales['month'].map({
            12: 'Winter', 1: 'Winter', 2: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring', 
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Fall', 10: 'Fall', 11: 'Fall'
        })
        
        # Price categorization - Handle edge cases
        try:
            # Remove NaN values and ensure we have enough unique values for quartiles
            valid_prices = self.df_products['price'].dropna()
            if len(valid_prices.unique()) >= 4:
                self.df_products['price_category'] = pd.qcut(
                    self.df_products['price'].fillna(valid_prices.median()), 
                    q=4, 
                    labels=['Budget', 'Mid-Range', 'Premium', 'Luxury'],
                    duplicates='drop'
                )
            else:
                # If not enough unique values, create simple categories
                median_price = valid_prices.median()
                self.df_products['price_category'] = self.df_products['price'].apply(
                    lambda x: 'Budget' if pd.isna(x) or x < median_price else 'Premium'
                )
        except Exception as e:
            print(f"   ⚠️ Price categorization warning: {e}")
            # Fallback: simple binary categorization
            median_price = self.df_products['price'].median()
            self.df_products['price_category'] = self.df_products['price'].apply(
                lambda x: 'Budget' if pd.isna(x) or x < median_price else 'Premium'
            )
        
        # Velocity metrics
        self.df_products['days_since_added'] = (datetime.now() - self.df_products['date_added']).dt.days
        self.df_products['sales_velocity'] = self.df_products['total_sold'] / (self.df_products['days_since_added'] + 1)
        
        # Aggregate sales metrics per product
        if not self.df_sales.empty:
            sales_agg = self.df_sales.groupby('product_id').agg({
                'quantity_sold': ['sum', 'mean', 'std'],
                'amount': ['sum', 'mean', 'std'],
                'sale_date': ['count', 'min', 'max']
            }).round(2)
            
            sales_agg.columns = ['total_qty_sold', 'avg_qty_per_sale', 'qty_std',
                                'total_revenue', 'avg_revenue_per_sale', 'revenue_std',
                                'total_transactions', 'first_sale', 'last_sale']
            
            # Merge back to products
            self.df_products = self.df_products.merge(
                sales_agg, left_on='id', right_index=True, how='left'
            )
        
        # Smart fillna that handles different data types
        numeric_columns = self.df_products.select_dtypes(include=[np.number]).columns
        categorical_columns = self.df_products.select_dtypes(include=['category']).columns
        
        # Fill numeric columns with 0
        self.df_products[numeric_columns] = self.df_products[numeric_columns].fillna(0)
        
        # Handle categorical columns properly
        for col in categorical_columns:
            if self.df_products[col].isna().any():
                # Add 'Unknown' as a category and fill NaN
                self.df_products[col] = self.df_products[col].cat.add_categories(['Unknown']).fillna('Unknown')
        
        print("   ✅ Advanced preprocessing completed")


    def create_enterprise_dashboard(self):
        """Create comprehensive enterprise dashboard"""
        print("\n🎨 Creating Enterprise Analytics Dashboard...")
        
        # Create comprehensive subplot dashboard
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=[
                'Revenue Trend with Forecast', 'Category Performance Matrix', 'Stock Status Alert System',
                'Price-Sales Correlation', 'Seasonal Sales Pattern', 'Supplier Performance',
                'Product Lifecycle Analysis', 'Inventory Turnover', 'Profitability Analysis'
            ],
            specs=[[{"secondary_y": True}, {"type": "scatter"}, {"type": "pie"}],
                   [{"type": "scatter"}, {"type": "bar"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "bar"}, {"type": "bar"}]]
        )
        
        # 1. Revenue Trend with Moving Average
        daily_revenue = self.df_sales.groupby(self.df_sales['sale_date'].dt.date)['amount'].sum()
        ma_7 = daily_revenue.rolling(window=7).mean()
        
        fig.add_trace(
            go.Scatter(x=daily_revenue.index, y=daily_revenue.values, 
                      name='Daily Revenue', line=dict(color='blue')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=daily_revenue.index, y=ma_7.values, 
                      name='7-Day MA', line=dict(color='red', width=3)),
            row=1, col=1
        )
        
        # 2. Category Performance Matrix
        category_perf = self.df_products.groupby('category_name').agg({
            'total_revenue': 'sum',
            'total_qty_sold': 'sum',
            'inventory_value': 'sum'
        }).reset_index()
        
        fig.add_trace(
            go.Scatter(x=category_perf['total_revenue'], y=category_perf['total_qty_sold'],
                      mode='markers+text', text=category_perf['category_name'],
                      marker=dict(size=category_perf['inventory_value']/1000, color='green'),
                      name='Category Performance'),
            row=1, col=2
        )
        
        # 3. Stock Status Distribution
        stock_counts = self.df_products['stock_status'].value_counts()
        colors = {'Critical': 'red', 'Low': 'orange', 'Medium': 'yellow', 'High': 'green'}
        
        fig.add_trace(
            go.Pie(labels=stock_counts.index, values=stock_counts.values,
                  marker=dict(colors=[colors.get(x, 'gray') for x in stock_counts.index]),
                  name='Stock Status'),
            row=1, col=3
        )
        
        # 4. Price-Sales Correlation
        fig.add_trace(
            go.Scatter(x=self.df_products['price'], y=self.df_products['total_qty_sold'],
                      mode='markers', marker=dict(color='purple', size=8),
                      name='Price vs Sales'),
            row=2, col=1
        )
        
        # 5. Seasonal Sales Pattern
        seasonal_sales = self.df_sales.groupby('season')['amount'].sum()
        fig.add_trace(
            go.Bar(x=seasonal_sales.index, y=seasonal_sales.values,
                  marker=dict(color='teal'), name='Seasonal Sales'),
            row=2, col=2
        )
        
        # 6. Supplier Performance
        supplier_perf = self.df_products.groupby('supplier_name')['total_revenue'].sum().head(5)
        fig.add_trace(
            go.Bar(x=supplier_perf.index, y=supplier_perf.values,
                  marker=dict(color='orange'), name='Top Suppliers'),
            row=2, col=3
        )
        
        # 7. Product Lifecycle (Days since added vs Sales velocity)
        fig.add_trace(
            go.Scatter(x=self.df_products['days_since_added'], y=self.df_products['sales_velocity'],
                      mode='markers', marker=dict(color='brown', size=6),
                      name='Product Lifecycle'),
            row=3, col=1
        )
        
        # 8. Inventory Turnover by Category
        turnover = self.df_products.groupby('category_name')['sales_velocity'].mean()
        fig.add_trace(
            go.Bar(x=turnover.index, y=turnover.values,
                  marker=dict(color='pink'), name='Turnover Rate'),
            row=3, col=2
        )
        
        # 9. Profitability Analysis (Revenue per unit stock)
        self.df_products['revenue_per_stock'] = self.df_products['total_revenue'] / (self.df_products['current_stock'] + 1)
        profit_analysis = self.df_products.groupby('price_category')['revenue_per_stock'].mean()
        
        fig.add_trace(
            go.Bar(x=profit_analysis.index, y=profit_analysis.values,
                  marker=dict(color='gold'), name='Revenue Efficiency'),
            row=3, col=3
        )
        
        fig.update_layout(
            height=1200, width=1800,
            title_text="📊 Enterprise Inventory Analytics Dashboard",
            showlegend=False
        )
        
        fig.show()

    def advanced_predictive_modeling(self):
        """Advanced predictive modeling with multiple algorithms"""
        print("\n🔮 Running Advanced Predictive Models...")
        
        # 1. Sales Forecasting with Random Forest
        daily_sales = self.df_sales.groupby(self.df_sales['sale_date'].dt.date)['amount'].sum()
        daily_sales.index = pd.to_datetime(daily_sales.index)
        
        # Create features for time series
        forecast_df = pd.DataFrame({
            'date': daily_sales.index,
            'sales': daily_sales.values
        })
        
        forecast_df['day_of_year'] = forecast_df['date'].dt.dayofyear
        forecast_df['day_of_week'] = forecast_df['date'].dt.dayofweek
        forecast_df['month'] = forecast_df['date'].dt.month
        forecast_df['quarter'] = forecast_df['date'].dt.quarter
        
        # Add lag features
        for lag in [1, 7, 14]:
            forecast_df[f'sales_lag_{lag}'] = forecast_df['sales'].shift(lag)
        
        # Add rolling averages
        for window in [7, 14, 30]:
            forecast_df[f'sales_ma_{window}'] = forecast_df['sales'].rolling(window=window).mean()
        
        # Remove NaN rows
        forecast_df = forecast_df.dropna()
        
        if len(forecast_df) > 30:
            # Features and target
            feature_cols = ['day_of_year', 'day_of_week', 'month', 'quarter'] + \
                          [f'sales_lag_{lag}' for lag in [1, 7, 14]] + \
                          [f'sales_ma_{window}' for window in [7, 14, 30]]
            
            X = forecast_df[feature_cols]
            y = forecast_df['sales']
            
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Train models
            models = {
                'Linear Regression': LinearRegression(),
                'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42)
            }
            
            results = {}
            for name, model in models.items():
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                mae = mean_absolute_error(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                r2 = r2_score(y_test, y_pred)
                
                results[name] = {'MAE': mae, 'RMSE': rmse, 'R²': r2, 'predictions': y_pred}
                
                print(f"{name} - MAE: ${mae:.2f}, RMSE: ${rmse:.2f}, R²: {r2:.3f}")
            
            # Visualize best model predictions
            best_model = min(results.keys(), key=lambda x: results[x]['RMSE'])
            
            plt.figure(figsize=(14, 8))
            plt.plot(X_test.index, y_test.values, label='Actual Sales', linewidth=2, color='blue')
            plt.plot(X_test.index, results[best_model]['predictions'], 
                    label=f'{best_model} Predictions', linewidth=2, color='red', linestyle='--')
            plt.title(f'Sales Forecasting - {best_model} (Best Model)', fontsize=16, fontweight='bold')
            plt.xlabel('Time Period')
            plt.ylabel('Sales Amount ($)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()

    def advanced_clustering_analysis(self):
        """Advanced customer/product segmentation using ML"""
        print("\n📊 Running Advanced Clustering Analysis...")
        
        # Product segmentation based on multiple features
        features = ['price', 'total_qty_sold', 'sales_velocity', 'inventory_value', 'days_to_expiry']
        X = self.df_products[features].fillna(0)
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # K-means clustering
        optimal_k = 4  # You can use elbow method to find optimal k
        kmeans = KMeans(n_clusters=optimal_k, random_state=42)
        clusters = kmeans.fit_predict(X_scaled)
        
        self.df_products['cluster'] = clusters
        
        # Create cluster analysis
        cluster_analysis = self.df_products.groupby('cluster').agg({
            'price': 'mean',
            'total_qty_sold': 'mean', 
            'sales_velocity': 'mean',
            'inventory_value': 'mean',
            'days_to_expiry': 'mean'
        }).round(2)
        
        print("\n🎯 Cluster Analysis:")
        print(cluster_analysis)
        
        # Visualize clusters
        fig = px.scatter_3d(
            self.df_products, 
            x='price', y='total_qty_sold', z='sales_velocity',
            color='cluster',
            hover_name='name',
            title='3D Product Clustering Analysis',
            labels={'price': 'Price ($)', 'total_qty_sold': 'Total Sold', 'sales_velocity': 'Sales Velocity'}
        )
        fig.show()

    def anomaly_detection_system(self):
        """Advanced anomaly detection for sales and inventory"""
        print("\n🚨 Running Anomaly Detection System...")
        
        # Sales anomaly detection
        daily_sales = self.df_sales.groupby(self.df_sales['sale_date'].dt.date)['amount'].sum()
        
        # Use Isolation Forest for anomaly detection
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        sales_data = daily_sales.values.reshape(-1, 1)
        anomalies = iso_forest.fit_predict(sales_data)
        
        # Identify anomalous days
        anomaly_dates = daily_sales.index[anomalies == -1]
        
        plt.figure(figsize=(14, 6))
        plt.plot(daily_sales.index, daily_sales.values, label='Daily Sales', color='blue', alpha=0.7)
        plt.scatter(anomaly_dates, daily_sales[anomaly_dates], 
                   color='red', s=100, label='Anomalies', zorder=5)
        plt.title('Sales Anomaly Detection', fontsize=16, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Sales Amount ($)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
        
        print(f"🚨 Detected {len(anomaly_dates)} anomalous sales days")
        if len(anomaly_dates) > 0:
            print("Anomalous dates:", anomaly_dates.tolist()[:5])

    def comprehensive_business_intelligence(self):
        """Generate comprehensive business intelligence report"""
        print("\n💡 COMPREHENSIVE BUSINESS INTELLIGENCE REPORT")
        print("=" * 80)
        
        # Store insights
        insights = {}
        
        # 1. Financial Performance
        total_revenue = self.df_sales['amount'].sum()
        total_transactions = len(self.df_sales)
        avg_transaction_value = self.df_sales['amount'].mean()
        total_inventory_value = self.df_products['inventory_value'].sum()
        
        insights['financial'] = {
            'total_revenue': total_revenue,
            'total_transactions': total_transactions,
            'avg_transaction_value': avg_transaction_value,
            'total_inventory_value': total_inventory_value,
            'revenue_per_day': total_revenue / max(1, len(self.df_sales['sale_date'].dt.date.unique()))
        }
        
        # 2. Inventory Health
        critical_stock_count = len(self.df_products[self.df_products['stock_status'] == 'Critical'])
        expiring_soon_count = len(self.df_products[self.df_products['days_to_expiry'] <= 30])
        slow_movers = len(self.df_products[self.df_products['sales_velocity'] < self.df_products['sales_velocity'].quantile(0.25)])
        
        insights['inventory'] = {
            'critical_stock_items': critical_stock_count,
            'expiring_soon': expiring_soon_count,
            'slow_moving_products': slow_movers,
            'avg_stock_level': self.df_products['current_stock'].mean()
        }
        
        # 3. Performance Metrics
        top_category = self.df_products.groupby('category_name')['total_revenue'].sum().idxmax()
        top_supplier = self.df_products.groupby('supplier_name')['total_revenue'].sum().idxmax()
        best_selling_product = self.df_products.loc[self.df_products['total_qty_sold'].idxmax(), 'name']
        
        insights['performance'] = {
            'top_category': top_category,
            'top_supplier': top_supplier,
            'best_selling_product': best_selling_product
        }
        
        # Print report
        print(f"💰 FINANCIAL OVERVIEW:")
        print(f"   Total Revenue: ${insights['financial']['total_revenue']:,.2f}")
        print(f"   Total Transactions: {insights['financial']['total_transactions']:,}")
        print(f"   Average Transaction: ${insights['financial']['avg_transaction_value']:.2f}")
        print(f"   Total Inventory Value: ${insights['financial']['total_inventory_value']:,.2f}")
        print(f"   Daily Revenue Rate: ${insights['financial']['revenue_per_day']:,.2f}")
        
        print(f"\n📦 INVENTORY HEALTH:")
        print(f"   Critical Stock Items: {insights['inventory']['critical_stock_items']}")
        print(f"   Items Expiring Soon (30 days): {insights['inventory']['expiring_soon']}")
        print(f"   Slow Moving Products: {insights['inventory']['slow_moving_products']}")
        print(f"   Average Stock Level: {insights['inventory']['avg_stock_level']:.1f} units")
        
        print(f"\n🏆 TOP PERFORMERS:")
        print(f"   Best Category: {insights['performance']['top_category']}")
        print(f"   Best Supplier: {insights['performance']['top_supplier']}")
        print(f"   Best Selling Product: {insights['performance']['best_selling_product']}")
        
        # 4. Strategic Recommendations
        print(f"\n🎯 STRATEGIC RECOMMENDATIONS:")
        
        if critical_stock_count > 0:
            print(f"   🔴 URGENT: Reorder {critical_stock_count} critical stock items immediately")
        
        if expiring_soon_count > 0:
            print(f"   ⏰ PRIORITY: Plan clearance for {expiring_soon_count} items expiring soon")
        
        if slow_movers > 0:
            print(f"   📈 MARKETING: Boost promotion for {slow_movers} slow-moving products")
        
        # Profitability analysis
        high_price_low_sales = self.df_products[
            (self.df_products['price'] > self.df_products['price'].median()) & 
            (self.df_products['total_qty_sold'] < self.df_products['total_qty_sold'].median())
        ]
        
        if len(high_price_low_sales) > 0:
            print(f"   💰 PRICING: Review pricing for {len(high_price_low_sales)} overpriced items")
        
        # Best opportunities
        high_velocity_products = self.df_products[
            self.df_products['sales_velocity'] > self.df_products['sales_velocity'].quantile(0.75)
        ]
        
        if len(high_velocity_products) > 0:
            print(f"   🚀 OPPORTUNITY: Scale up {len(high_velocity_products)} high-velocity products")
        
        self.insights = insights
        return insights

    def run_complete_enterprise_analysis(self):
        """Execute complete enterprise-grade analysis workflow"""
        print("🚀 ENTERPRISE INVENTORY ANALYTICS SYSTEM")
        print("=" * 80)
        
        try:
            # Load and prepare data
            self.load_and_enrich_data()
            
            # Create comprehensive dashboard
            self.create_enterprise_dashboard()
            
            # Advanced analytics
            self.advanced_predictive_modeling()
            self.advanced_clustering_analysis()
            self.anomaly_detection_system()
            
            # Business intelligence
            self.comprehensive_business_intelligence()
            
            print("\n" + "="*80)
            print("🎉 ENTERPRISE ANALYSIS COMPLETED SUCCESSFULLY!")
            print("="*80)
            print("📊 All advanced visualizations and insights generated.")
            print("🤖 Machine learning models trained and evaluated.")
            print("💡 Strategic recommendations provided.")
            print("🏢 Ready for executive presentation!")
            
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if hasattr(self, 'connection') and self.connection:
                self.connection.close()
                print("🔌 Database connection closed.")

# Execute the enterprise analysis
if __name__ == "__main__":
    print("🎨 ENTERPRISE INVENTORY ANALYTICS FOR FINAL YEAR PROJECT")
    print("=" * 80)
    print("🎓 Advanced Machine Learning • Interactive Dashboards • Business Intelligence")
    print("=" * 80)
    
    try:
        analytics = EnterpriseInventoryAnalytics()
        analytics.run_complete_enterprise_analysis()
        
    except Exception as e:
        print(f"❌ Error: {e}")
