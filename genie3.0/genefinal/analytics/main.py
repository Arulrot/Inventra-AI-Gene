import pandas as pd
import numpy as np
import mysql.connector
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import warnings
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from scipy import stats
from scipy.stats import pearsonr
import networkx as nx
import plotly.figure_factory as ff
from wordcloud import WordCloud
import squarify
import warnings
from textwrap import wrap

warnings.filterwarnings('ignore')

# Configuration
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
pio.renderers.default = "browser"

# MySQL connection config
MYSQL_CONFIG = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'inventory_ai'
}

class AdvancedInventoryAnalytics:
    def __init__(self):
        """Initialize the analytics system with database connection"""
        self.conn = mysql.connector.connect(**MYSQL_CONFIG)
        self.df_products = None
        self.df_sales = None
        self.df_suppliers = None
        self.df_categories = None
        self.df_recommendations = None
        
        # Color schemes for consistency
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#F18F01',
            'warning': '#C73E1D',
            'info': '#9D84B7',
            'dark': '#2D3436',
            'light': '#DDD',
            'gradient': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        }
        
        self.load_and_preprocess_data()
    
    def load_and_preprocess_data(self):
        """Load and preprocess all data from database"""
        print("📊 Loading and preprocessing data...")
        
        try:
            # Products data with joins
            products_query = """
            SELECT p.*, c.name as category_name, s.name as supplier_name, s.email as supplier_email
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            """
            self.df_products = pd.read_sql(products_query, self.conn)
            
            # Sales history with product details
            sales_query = """
            SELECT sh.*, p.name as product_name, p.category_id, p.price, c.name as category_name
            FROM sales_history sh
            JOIN products p ON sh.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            """
            self.df_sales = pd.read_sql(sales_query, self.conn)
            
            # Load other tables
            self.df_suppliers = pd.read_sql("SELECT * FROM suppliers", self.conn)
            self.df_categories = pd.read_sql("SELECT * FROM categories", self.conn)
            self.df_recommendations = pd.read_sql("SELECT * FROM ai_recommendations", self.conn)
            
            # Preprocessing
            self._preprocess_data()
            
            print(f"✅ Data loaded successfully:")
            print(f"   - Products: {len(self.df_products)}")
            print(f"   - Sales: {len(self.df_sales)}")
            print(f"   - Categories: {len(self.df_categories)}")
            print(f"   - Suppliers: {len(self.df_suppliers)}")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            raise
    
    def _preprocess_data(self):
        """Advanced data preprocessing and feature engineering"""
        # Sales data preprocessing
        if not self.df_sales.empty:
            self.df_sales['sale_date'] = pd.to_datetime(self.df_sales['sale_date'])
            self.df_sales['year'] = self.df_sales['sale_date'].dt.year
            self.df_sales['month'] = self.df_sales['sale_date'].dt.month
            self.df_sales['day'] = self.df_sales['sale_date'].dt.day
            self.df_sales['weekday'] = self.df_sales['sale_date'].dt.dayofweek
            self.df_sales['hour'] = self.df_sales['sale_date'].dt.hour
            self.df_sales['is_weekend'] = self.df_sales['weekday'].isin([5, 6])
            self.df_sales['quarter'] = self.df_sales['sale_date'].dt.quarter
            
        # Products data preprocessing
        if not self.df_products.empty:
            self.df_products['date_added'] = pd.to_datetime(self.df_products['date_added'])
            self.df_products['expiry_date'] = pd.to_datetime(self.df_products['expiry_date'])
            self.df_products['days_to_expiry'] = (self.df_products['expiry_date'] - datetime.now()).dt.days
            self.df_products['days_since_added'] = (datetime.now() - self.df_products['date_added']).dt.days
            
            # Stock status categories
            self.df_products['stock_status'] = self.df_products.apply(
                lambda x: 'Critical' if x['current_stock'] <= x['minimum_stock'] * 0.5
                else 'Low' if x['current_stock'] <= x['minimum_stock']
                else 'Medium' if x['current_stock'] <= x['minimum_stock'] * 2
                else 'High', axis=1
            )
            
            # Price categories
            self.df_products['price_category'] = pd.cut(
                self.df_products['price'], 
                bins=4, 
                labels=['Budget', 'Mid-Range', 'Premium', 'Luxury']
            )
            
            # Performance metrics
            if not self.df_sales.empty:
                # Calculate advanced metrics
                product_sales = self.df_sales.groupby('product_id').agg({
                    'quantity_sold': 'sum',
                    'amount': 'sum',
                    'sale_date': ['count', 'min', 'max']
                }).round(2)
                product_sales.columns = ['total_quantity', 'total_revenue', 'transaction_count', 'first_sale', 'last_sale']
                
                # Merge with products
                self.df_products = self.df_products.merge(
                    product_sales, left_on='id', right_index=True, how='left'
                ).fillna(0)

    def generate_comprehensive_dashboard(self):
        """Generate a comprehensive analytics dashboard"""
        print("\n🎨 Generating Comprehensive Analytics Dashboard")
        print("=" * 70)
        
        # Create main dashboard with multiple visualizations
        fig = plt.figure(figsize=(24, 20))
        gs = fig.add_gridspec(6, 4, hspace=0.3, wspace=0.3)
        
        # 1. Revenue Trend Analysis (Top row - spans 2 columns)
        self._plot_revenue_trends(fig, gs[0, :2])
        
        # 2. Product Performance Heatmap (Top right)
        self._plot_performance_heatmap(fig, gs[0, 2:])
        
        # 3. Category Analysis (Second row)
        self._plot_category_sunburst(fig, gs[1, :2])
        self._plot_stock_distribution(fig, gs[1, 2:])
        
        # 4. Supplier Performance (Third row)
        self._plot_supplier_network(fig, gs[2, :2])
        self._plot_price_analysis(fig, gs[2, 2:])
        
        # 5. Time Series Analysis (Fourth row)
        self._plot_seasonal_patterns(fig, gs[3, :])
        
        # 6. Advanced Analytics (Fifth row)
        self._plot_correlation_matrix(fig, gs[4, :2])
        self._plot_anomaly_detection(fig, gs[4, 2:])
        
        # 7. Predictive Insights (Bottom row)
        self._plot_forecasting(fig, gs[5, :])
        
        plt.suptitle('🏢 Advanced Inventory Analytics Dashboard\n📊 Enterprise-Grade Business Intelligence', 
                     fontsize=20, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        plt.show()
        
        # Generate additional interactive plots
        self._generate_interactive_plots()

    def _plot_revenue_trends(self, fig, gs_pos):
        """Advanced revenue trend analysis with multiple metrics"""
        ax = fig.add_subplot(gs_pos)
        
        if self.df_sales.empty:
            ax.text(0.5, 0.5, 'No Sales Data Available', ha='center', va='center', fontsize=16)
            ax.set_title('Revenue Trends', fontsize=14, fontweight='bold')
            return
        
        # Daily revenue with moving averages
        daily_sales = self.df_sales.groupby(self.df_sales['sale_date'].dt.date).agg({
            'amount': 'sum',
            'quantity_sold': 'sum'
        })
        
        # Calculate moving averages
        daily_sales['7_day_ma'] = daily_sales['amount'].rolling(window=7).mean()
        daily_sales['30_day_ma'] = daily_sales['amount'].rolling(window=30).mean()
        
        # Plot
        ax.plot(daily_sales.index, daily_sales['amount'], alpha=0.7, color=self.colors['primary'], label='Daily Revenue')
        ax.plot(daily_sales.index, daily_sales['7_day_ma'], color=self.colors['secondary'], label='7-Day MA', linewidth=2)
        ax.plot(daily_sales.index, daily_sales['30_day_ma'], color=self.colors['success'], label='30-Day MA', linewidth=2)
        
        # Add trend arrow
        recent_trend = daily_sales['amount'].tail(7).mean() - daily_sales['amount'].tail(14).head(7).mean()
        trend_color = 'green' if recent_trend > 0 else 'red'
        trend_symbol = '↗' if recent_trend > 0 else '↘'
        
        ax.set_title(f'📈 Revenue Trends {trend_symbol}', fontsize=14, fontweight='bold', color=trend_color)
        ax.set_xlabel('Date')
        ax.set_ylabel('Revenue ($)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.tick_params(axis='x', rotation=45)

    def _plot_performance_heatmap(self, fig, gs_pos):
        """Product performance heatmap"""
        ax = fig.add_subplot(gs_pos)
        
        if self.df_products.empty:
            ax.text(0.5, 0.5, 'No Product Data', ha='center', va='center')
            return
        
        # Create performance matrix
        performance_data = self.df_products.pivot_table(
            values='total_sold', 
            index='category_name', 
            columns='stock_status', 
            aggfunc='mean', 
            fill_value=0
        )
        
        # Create heatmap
        sns.heatmap(performance_data, annot=True, cmap='RdYlGn', ax=ax, 
                   cbar_kws={'label': 'Average Units Sold'})
        ax.set_title('🔥 Performance Heatmap\n(Category vs Stock Status)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Stock Status')
        ax.set_ylabel('Category')

    def _plot_category_sunburst(self, fig, gs_pos):
        """Category distribution with nested pie charts"""
        ax = fig.add_subplot(gs_pos)
        
        if self.df_products.empty:
            ax.text(0.5, 0.5, 'No Category Data', ha='center', va='center')
            return
        
        # Category distribution
        category_data = self.df_products['category_name'].value_counts()
        
        # Create nested pie chart
        colors = plt.cm.Set3(np.linspace(0, 1, len(category_data)))
        
        # Inner pie (categories)
        wedges, texts, autotexts = ax.pie(category_data.values, labels=category_data.index, 
                                         autopct='%1.1f%%', colors=colors, radius=0.8,
                                         wedgeprops=dict(width=0.3))
        
        # Outer ring (stock status within categories)
        stock_by_category = self.df_products.groupby(['category_name', 'stock_status']).size().unstack(fill_value=0)
        
        ax.set_title('🎯 Category Distribution\n& Stock Status', fontsize=12, fontweight='bold')
        
        # Add total in center
        total_products = len(self.df_products)
        ax.text(0, 0, f'Total\nProducts\n{total_products}', ha='center', va='center', 
               fontsize=14, fontweight='bold')

    def _plot_stock_distribution(self, fig, gs_pos):
        """Advanced stock distribution analysis"""
        ax = fig.add_subplot(gs_pos)
        
        if self.df_products.empty:
            return
        
        # Stock status distribution
        stock_counts = self.df_products['stock_status'].value_counts()
        colors = {'Critical': '#ff4757', 'Low': '#ff7675', 'Medium': '#fdcb6e', 'High': '#00b894'}
        
        # Create bars with gradient effect
        bars = ax.bar(stock_counts.index, stock_counts.values, 
                     color=[colors.get(x, '#ddd') for x in stock_counts.index])
        
        # Add value labels on bars
        for bar, value in zip(bars, stock_counts.values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{value}', ha='center', va='bottom', fontweight='bold')
        
        ax.set_title('📦 Stock Status Distribution', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Products')
        
        # Add percentage annotations
        total = stock_counts.sum()
        for i, (status, count) in enumerate(stock_counts.items()):
            percentage = (count / total) * 100
            ax.text(i, count/2, f'{percentage:.1f}%', ha='center', va='center', 
                   color='white', fontweight='bold')

    def _plot_supplier_network(self, fig, gs_pos):
        """Supplier performance network visualization"""
        ax = fig.add_subplot(gs_pos)
        
        if self.df_suppliers.empty or self.df_products.empty:
            ax.text(0.5, 0.5, 'No Supplier Data', ha='center', va='center')
            return
        
        # Supplier performance metrics
        supplier_perf = self.df_products.groupby('supplier_name').agg({
            'total_sold': 'sum',
            'price': 'mean',
            'current_stock': 'sum'
        }).fillna(0)
        
        # Create scatter plot
        scatter = ax.scatter(supplier_perf['price'], supplier_perf['total_sold'], 
                           s=supplier_perf['current_stock']/5, alpha=0.7,
                           c=range(len(supplier_perf)), cmap='viridis')
        
        # Add supplier labels
        for i, supplier in enumerate(supplier_perf.index):
            ax.annotate(supplier[:15], 
                       (supplier_perf['price'].iloc[i], supplier_perf['total_sold'].iloc[i]),
                       xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        ax.set_title('🏭 Supplier Performance Network\n(Bubble size = Stock)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Average Price ($)')
        ax.set_ylabel('Total Units Sold')

    def _plot_price_analysis(self, fig, gs_pos):
        """Advanced price analysis with distribution"""
        ax = fig.add_subplot(gs_pos)
        
        if self.df_products.empty:
            return
        
        # Price distribution by category
        categories = self.df_products['category_name'].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(categories)))
        
        for i, category in enumerate(categories):
            cat_data = self.df_products[self.df_products['category_name'] == category]['price']
            ax.hist(cat_data, alpha=0.6, label=category, bins=10, color=colors[i])
        
        ax.set_title('💰 Price Distribution by Category', fontsize=12, fontweight='bold')
        ax.set_xlabel('Price ($)')
        ax.set_ylabel('Frequency')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_seasonal_patterns(self, fig, gs_pos):
        """Seasonal patterns and time series analysis"""
        ax = fig.add_subplot(gs_pos)
        
        if self.df_sales.empty:
            ax.text(0.5, 0.5, 'No Sales Data Available', ha='center', va='center')
            return
        
        # Monthly seasonality
        monthly_sales = self.df_sales.groupby('month')['amount'].sum()
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Create area plot
        ax.fill_between(monthly_sales.index, monthly_sales.values, alpha=0.7, color=self.colors['primary'])
        ax.plot(monthly_sales.index, monthly_sales.values, color=self.colors['dark'], linewidth=3)
        
        # Add markers for peaks
        peak_month = monthly_sales.idxmax()
        ax.scatter(peak_month, monthly_sales[peak_month], color='red', s=100, zorder=5)
        ax.annotate(f'Peak: {months[peak_month-1]}', 
                   xy=(peak_month, monthly_sales[peak_month]),
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
        
        ax.set_title('📅 Seasonal Sales Patterns', fontsize=14, fontweight='bold')
        ax.set_xlabel('Month')
        ax.set_ylabel('Total Sales ($)')
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(months)
        ax.grid(True, alpha=0.3)

    def _plot_correlation_matrix(self, fig, gs_pos):
        """Advanced correlation analysis"""
        ax = fig.add_subplot(gs_pos)
        
        if self.df_products.empty:
            return
        
        # Select numeric columns for correlation
        numeric_cols = ['price', 'current_stock', 'minimum_stock', 'total_sold', 'days_to_expiry']
        corr_data = self.df_products[numeric_cols].corr()
        
        # Create custom colormap
        mask = np.triu(np.ones_like(corr_data, dtype=bool))
        
        # Generate heatmap
        sns.heatmap(corr_data, mask=mask, annot=True, cmap='RdBu_r', center=0,
                   square=True, ax=ax, cbar_kws={"shrink": .8})
        
        ax.set_title('🔗 Correlation Matrix\n(Product Attributes)', fontsize=12, fontweight='bold')

    def _plot_anomaly_detection(self, fig, gs_pos):
        """Anomaly detection visualization"""
        ax = fig.add_subplot(gs_pos)
        
        if self.df_sales.empty:
            ax.text(0.5, 0.5, 'No Sales Data', ha='center', va='center')
            return
        
        # Daily sales for anomaly detection
        daily_sales = self.df_sales.groupby(self.df_sales['sale_date'].dt.date)['amount'].sum()
        
        # Use Isolation Forest for anomaly detection
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomalies = iso_forest.fit_predict(daily_sales.values.reshape(-1, 1))
        
        # Plot normal and anomalous days
        normal_mask = anomalies == 1
        anomaly_mask = anomalies == -1
        
        ax.scatter(daily_sales.index[normal_mask], daily_sales.values[normal_mask], 
                  alpha=0.7, label='Normal Days', color=self.colors['primary'])
        ax.scatter(daily_sales.index[anomaly_mask], daily_sales.values[anomaly_mask], 
                  color='red', s=100, label='Anomalies', marker='x')
        
        ax.set_title('🚨 Sales Anomaly Detection', fontsize=12, fontweight='bold')
        ax.set_ylabel('Daily Sales ($)')
        ax.legend()
        ax.tick_params(axis='x', rotation=45)

    def _plot_forecasting(self, fig, gs_pos):
        """Advanced sales forecasting visualization"""
        ax = fig.add_subplot(gs_pos)
        
        if self.df_sales.empty:
            ax.text(0.5, 0.5, 'No Sales Data for Forecasting', ha='center', va='center')
            return
        
        # Prepare data for forecasting
        daily_sales = self.df_sales.groupby(self.df_sales['sale_date'].dt.date)['amount'].sum()
        daily_sales.index = pd.to_datetime(daily_sales.index)
        
        if len(daily_sales) < 10:
            ax.text(0.5, 0.5, 'Insufficient Data for Forecasting', ha='center', va='center')
            return
        
        # Split data
        split_point = int(len(daily_sales) * 0.8)
        train_data = daily_sales[:split_point]
        test_data = daily_sales[split_point:]
        
        # Simple linear regression for forecasting
        X = np.arange(len(train_data)).reshape(-1, 1)
        y = train_data.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predictions
        future_days = 30
        future_X = np.arange(len(train_data), len(train_data) + future_days).reshape(-1, 1)
        future_pred = model.predict(future_X)
        
        # Plot historical data
        ax.plot(train_data.index, train_data.values, label='Historical Data', 
               color=self.colors['primary'], linewidth=2)
        
        if len(test_data) > 0:
            ax.plot(test_data.index, test_data.values, label='Actual', 
                   color=self.colors['secondary'], linewidth=2)
        
        # Plot forecast
        future_dates = pd.date_range(start=daily_sales.index[-1] + timedelta(days=1), 
                                   periods=future_days, freq='D')
        ax.plot(future_dates, future_pred, label='Forecast', 
               color=self.colors['warning'], linestyle='--', linewidth=2)
        
        # Add confidence interval
        std_error = np.std(y - model.predict(X))
        ax.fill_between(future_dates, future_pred - 2*std_error, future_pred + 2*std_error,
                       alpha=0.3, color=self.colors['warning'])
        
        ax.set_title('🔮 Sales Forecasting (30 Days)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Sales Amount ($)')
        ax.legend()
        ax.tick_params(axis='x', rotation=45)

    def _generate_interactive_plots(self):
        """Generate interactive Plotly visualizations"""
        print("\n🎪 Generating Interactive Visualizations...")
        
        # 1. Interactive Sales Dashboard
        self._create_interactive_sales_dashboard()
        
        # 2. 3D Product Analysis
        self._create_3d_product_analysis()
        
        # 3. Interactive Supply Chain Network
        self._create_supply_chain_network()
        
        # 4. Advanced Time Series Analysis
        self._create_time_series_analysis()

    def _create_interactive_sales_dashboard(self):
        """Create interactive sales dashboard with Plotly"""
        if self.df_sales.empty:
            print("⚠️ No sales data for interactive dashboard")
            return
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Daily Sales Trend', 'Category Performance', 
                          'Hourly Pattern', 'Weekday Analysis'),
            specs=[[{"secondary_y": True}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Daily sales trend
        daily_sales = self.df_sales.groupby(self.df_sales['sale_date'].dt.date).agg({
            'amount': 'sum',
            'quantity_sold': 'sum'
        }).reset_index()
        
        fig.add_trace(
            go.Scatter(x=daily_sales['sale_date'], y=daily_sales['amount'],
                      name='Revenue', line=dict(color='#3498db', width=3)),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=daily_sales['sale_date'], y=daily_sales['quantity_sold'],
                      name='Quantity', line=dict(color='#e74c3c', width=2), yaxis='y2'),
            row=1, col=1, secondary_y=True
        )
        
        # Category pie chart
        category_sales = self.df_sales.groupby('category_name')['amount'].sum()
        fig.add_trace(
            go.Pie(labels=category_sales.index, values=category_sales.values,
                   name="Category Sales", hole=0.4),
            row=1, col=2
        )
        
        # Hourly pattern
        hourly_sales = self.df_sales.groupby('hour')['amount'].sum()
        fig.add_trace(
            go.Bar(x=hourly_sales.index, y=hourly_sales.values,
                   name='Hourly Sales', marker_color='lightblue'),
            row=2, col=1
        )
        
        # Weekday analysis
        weekday_sales = self.df_sales.groupby('weekday')['amount'].sum()
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        fig.add_trace(
            go.Bar(x=[weekday_names[i] for i in weekday_sales.index], 
                   y=weekday_sales.values,
                   name='Weekday Sales', marker_color='lightgreen'),
            row=2, col=2
        )
        
        fig.update_layout(height=800, showlegend=True,
                         title_text="📊 Interactive Sales Dashboard")
        fig.show()

    def _create_3d_product_analysis(self):
        """Create 3D scatter plot for product analysis"""
        if self.df_products.empty:
            return
        
        fig = go.Figure(data=[go.Scatter3d(
            x=self.df_products['price'],
            y=self.df_products['current_stock'],
            z=self.df_products['total_sold'],
            mode='markers',
            marker=dict(
                size=8,
                color=self.df_products['days_to_expiry'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Days to Expiry")
            ),
            text=self.df_products['name'],
            hovertemplate='<b>%{text}</b><br>' +
                         'Price: $%{x}<br>' +
                         'Stock: %{y}<br>' +
                         'Sales: %{z}<br>' +
                         '<extra></extra>'
        )])
        
        fig.update_layout(
            title='🎯 3D Product Analysis<br><sub>Price vs Stock vs Sales (Color = Days to Expiry)</sub>',
            scene=dict(
                xaxis_title='Price ($)',
                yaxis_title='Current Stock',
                zaxis_title='Total Sold'
            ),
            width=900,
            height=700
        )
        
        fig.show()

    def _create_supply_chain_network(self):
        """Create interactive supply chain network visualization"""
        if self.df_suppliers.empty or self.df_products.empty:
            return
        
        # Create network graph
        G = nx.Graph()
        
        # Add supplier nodes
        for _, supplier in self.df_suppliers.iterrows():
            G.add_node(f"S_{supplier['name']}", type='supplier', size=30)
        
        # Add product nodes and edges
        for _, product in self.df_products.iterrows():
            product_node = f"P_{product['name'][:20]}"
            supplier_node = f"S_{product['supplier_name']}"
            
            G.add_node(product_node, type='product', size=10)
            if supplier_node in G.nodes():
                G.add_edge(supplier_node, product_node, weight=product['total_sold'])
        
        # Get positions
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Create edge traces
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(x=edge_x, y=edge_y,
                               line=dict(width=0.5, color='#888'),
                               hoverinfo='none',
                               mode='lines')
        
        # Create node traces
        supplier_x = []
        supplier_y = []
        supplier_text = []
        product_x = []
        product_y = []
        product_text = []
        
        for node in G.nodes():
            x, y = pos[node]
            if node.startswith('S_'):
                supplier_x.append(x)
                supplier_y.append(y)
                supplier_text.append(node[2:])  # Remove 'S_' prefix
            else:
                product_x.append(x)
                product_y.append(y)
                product_text.append(node[2:])  # Remove 'P_' prefix
        
        supplier_trace = go.Scatter(x=supplier_x, y=supplier_y,
                                   mode='markers+text',
                                   marker=dict(size=20, color='red'),
                                   text=supplier_text,
                                   textposition="middle center",
                                   name='Suppliers')
        
        product_trace = go.Scatter(x=product_x, y=product_y,
                                  mode='markers',
                                  marker=dict(size=8, color='blue'),
                                  text=product_text,
                                  name='Products')
        
        fig = go.Figure(data=[edge_trace, supplier_trace, product_trace],
                       layout=go.Layout(
                           title='🔗 Supply Chain Network',
                           titlefont_size=16,
                           showlegend=True,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Interactive Supply Chain Visualization",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002 ) ],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                       )
        fig.show()

    def _create_time_series_analysis(self):
        """Advanced time series analysis with decomposition"""
        if self.df_sales.empty:
            return
        
        # Prepare time series data
        daily_sales = self.df_sales.groupby(self.df_sales['sale_date'].dt.date)['amount'].sum()
        daily_sales.index = pd.to_datetime(daily_sales.index)
        
        if len(daily_sales) < 30:
            print("⚠️ Insufficient data for time series analysis")
            return
        
        # Create multiple time series visualizations
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Sales Trend with Moving Averages', 
                          'Sales Volume Distribution', 
                          'Cumulative Sales Growth'),
            vertical_spacing=0.1
        )
        
        # 1. Trend with moving averages
        fig.add_trace(
            go.Scatter(x=daily_sales.index, y=daily_sales.values,
                      name='Daily Sales', line=dict(color='blue', width=1)),
            row=1, col=1
        )
        
        # Add moving averages
        ma_7 = daily_sales.rolling(window=7).mean()
        ma_30 = daily_sales.rolling(window=min(30, len(daily_sales)//2)).mean()
        
        fig.add_trace(
            go.Scatter(x=daily_sales.index, y=ma_7.values,
                      name='7-Day MA', line=dict(color='red', width=2)),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=daily_sales.index, y=ma_30.values,
                      name='30-Day MA', line=dict(color='green', width=2)),
            row=1, col=1
        )
        
        # 2. Distribution
        fig.add_trace(
            go.Histogram(x=daily_sales.values, name='Sales Distribution',
                        marker_color='lightblue', opacity=0.7),
            row=2, col=1
        )
        
        # 3. Cumulative growth
        cumulative_sales = daily_sales.cumsum()
        fig.add_trace(
            go.Scatter(x=daily_sales.index, y=cumulative_sales.values,
                      name='Cumulative Sales', 
                      fill='tonexty', line=dict(color='purple', width=2)),
            row=3, col=1
        )
        
        fig.update_layout(height=1000, showlegend=True,
                         title_text="📈 Advanced Time Series Analysis")
        fig.show()

    def generate_predictive_analytics(self):
        """Generate advanced predictive analytics"""
        print("\n🔮 Generating Predictive Analytics...")
        print("=" * 50)
        
        # 1. Sales Forecasting with Confidence Intervals
        self._advanced_sales_forecasting()
        
        # 2. Stock Optimization Recommendations
        self._stock_optimization_analysis()
        
        # 3. Customer Segmentation
        self._customer_segmentation_analysis()
        
        # 4. Price Optimization
        self._price_optimization_analysis()

    def _advanced_sales_forecasting(self):
        """Advanced sales forecasting with multiple models"""
        if self.df_sales.empty:
            print("⚠️ No sales data for forecasting")
            return
        
        print("📈 Advanced Sales Forecasting Analysis")
        
        # Prepare data
        daily_sales = self.df_sales.groupby(self.df_sales['sale_date'].dt.date)['amount'].sum()
        daily_sales.index = pd.to_datetime(daily_sales.index)
        
        if len(daily_sales) < 20:
            print("⚠️ Insufficient data for reliable forecasting")
            return
        
        # Split data
        split_point = int(len(daily_sales) * 0.8)
        train_data = daily_sales[:split_point]
        test_data = daily_sales[split_point:]
        
        # Multiple forecasting models
        models = {}
        predictions = {}
        
        # Model 1: Linear Regression
        X_train = np.arange(len(train_data)).reshape(-1, 1)
        X_test = np.arange(len(train_data), len(daily_sales)).reshape(-1, 1)
        
        lr_model = LinearRegression()
        lr_model.fit(X_train, train_data.values)
        
        models['Linear Regression'] = lr_model
        if len(test_data) > 0:
            predictions['Linear Regression'] = lr_model.predict(X_test)
        
        # Model 2: Random Forest
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        
        # Create features (day of week, month, day of month)
        train_features = []
        for date in train_data.index:
            train_features.append([date.weekday(), date.month, date.day])
        
        rf_model.fit(train_features, train_data.values)
        models['Random Forest'] = rf_model
        
        if len(test_data) > 0:
            test_features = []
            for date in test_data.index:
                test_features.append([date.weekday(), date.month, date.day])
            predictions['Random Forest'] = rf_model.predict(test_features)
        
        # Visualization
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Plot 1: Model Comparison
        ax1.plot(train_data.index, train_data.values, label='Training Data', color='blue', linewidth=2)
        
        if len(test_data) > 0:
            ax1.plot(test_data.index, test_data.values, label='Actual', color='green', linewidth=2)
            
            for model_name, pred in predictions.items():
                ax1.plot(test_data.index, pred, label=f'{model_name} Prediction', 
                        linestyle='--', linewidth=2)
        
        # Future forecast
        future_days = 30
        future_dates = pd.date_range(start=daily_sales.index[-1] + timedelta(days=1), 
                                   periods=future_days, freq='D')
        
        # Linear regression future prediction
        future_X = np.arange(len(daily_sales), len(daily_sales) + future_days).reshape(-1, 1)
        future_pred_lr = lr_model.predict(future_X)
        
        ax1.plot(future_dates, future_pred_lr, label='Future Forecast (LR)', 
                color='red', linestyle=':', linewidth=3)
        
        # Add confidence interval
        std_error = np.std(train_data.values - lr_model.predict(X_train))
        ax1.fill_between(future_dates, future_pred_lr - 2*std_error, future_pred_lr + 2*std_error,
                        alpha=0.3, color='red', label='Confidence Interval')
        
        ax1.set_title('🔮 Advanced Sales Forecasting - Model Comparison', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Sales Amount ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Forecast Components
        # Trend
        trend = daily_sales.rolling(window=min(30, len(daily_sales)//3)).mean()
        ax2.plot(daily_sales.index, trend.values, label='Trend', color='blue', linewidth=2)
        
        # Seasonality (weekly)
        weekly_pattern = daily_sales.groupby(daily_sales.index.dayofweek).mean()
        seasonal_component = daily_sales.index.map(lambda x: weekly_pattern[x.weekday()])
        ax2.plot(daily_sales.index, seasonal_component, label='Weekly Seasonality', 
                color='orange', alpha=0.7)
        
        ax2.set_title('📊 Forecast Components Analysis', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Component Value')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        # Model Performance
        if len(test_data) > 0 and len(predictions) > 0:
            print("\n📊 Model Performance Comparison:")
            print("-" * 40)
            for model_name, pred in predictions.items():
                mae = mean_absolute_error(test_data.values, pred)
                rmse = np.sqrt(mean_squared_error(test_data.values, pred))
                print(f"{model_name:15} | MAE: ${mae:7.2f} | RMSE: ${rmse:7.2f}")
            
            # Forecast insights
            avg_forecast = np.mean(future_pred_lr)
            total_forecast = np.sum(future_pred_lr)
            
            print(f"\n🔮 30-Day Forecast Summary:")
            print(f"   Average Daily Sales: ${avg_forecast:,.2f}")
            print(f"   Total Predicted Sales: ${total_forecast:,.2f}")
            
            # Trend analysis
            recent_avg = daily_sales.tail(7).mean()
            if avg_forecast > recent_avg * 1.1:
                print(f"   📈 Trend: GROWING (+{((avg_forecast/recent_avg-1)*100):.1f}%)")
            elif avg_forecast < recent_avg * 0.9:
                print(f"   📉 Trend: DECLINING ({((avg_forecast/recent_avg-1)*100):.1f}%)")
            else:
                print(f"   ➡️  Trend: STABLE")

    def _stock_optimization_analysis(self):
        """Advanced stock optimization with economic models"""
        if self.df_products.empty:
            print("⚠️ No product data for stock optimization")
            return
        
        print("\n📦 Stock Optimization Analysis")
        
        # Calculate optimal stock levels
        optimization_results = []
        
        for _, product in self.df_products.iterrows():
            # Basic EOQ calculation (simplified)
            if product['total_sold'] > 0:
                annual_demand = product['total_sold'] * 4  # Extrapolate quarterly to annual
                holding_cost_rate = 0.25  # 25% annual holding cost
                ordering_cost = 50  # Fixed ordering cost
                
                if annual_demand > 0 and holding_cost_rate > 0:
                    # Economic Order Quantity
                    eoq = np.sqrt((2 * annual_demand * ordering_cost) / 
                                (product['price'] * holding_cost_rate))
                    
                    # Reorder point (assuming 7-day lead time)
                    daily_demand = annual_demand / 365
                    reorder_point = daily_demand * 7 + product['minimum_stock']
                    
                    # Safety stock
                    safety_stock = product['minimum_stock']
                    
                    optimization_results.append({
                        'product_name': product['name'],
                        'current_stock': product['current_stock'],
                        'optimal_order_qty': eoq,
                        'reorder_point': reorder_point,
                        'safety_stock': safety_stock,
                        'annual_demand': annual_demand,
                        'status': 'Critical' if product['current_stock'] < reorder_point else 'OK'
                    })
        
        if optimization_results:
            opt_df = pd.DataFrame(optimization_results)
            
            # Visualization
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # 1. Current vs Optimal Stock
            products_to_show = opt_df.head(10)  # Show top 10
            x_pos = np.arange(len(products_to_show))
            
            ax1.bar(x_pos - 0.2, products_to_show['current_stock'], 0.4, 
                   label='Current Stock', color='lightblue')
            ax1.bar(x_pos + 0.2, products_to_show['optimal_order_qty'], 0.4, 
                   label='Optimal Order Qty', color='orange')
            
            ax1.set_title('📊 Current vs Optimal Stock Levels', fontweight='bold')
            ax1.set_xlabel('Products')
            ax1.set_ylabel('Quantity')
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels([name[:15] for name in products_to_show['product_name']], 
                               rotation=45, ha='right')
            ax1.legend()
            
            # 2. Reorder Point Analysis
            ax2.scatter(opt_df['annual_demand'], opt_df['reorder_point'], 
                       c=opt_df['current_stock'], cmap='RdYlGn', alpha=0.7)
            ax2.set_title('🎯 Reorder Point vs Demand', fontweight='bold')
            ax2.set_xlabel('Annual Demand')
            ax2.set_ylabel('Reorder Point')
            
            # Add colorbar
            cbar = plt.colorbar(ax2.collections[0], ax=ax2)
            cbar.set_label('Current Stock')
            
            # 3. Stock Status Distribution
            status_counts = opt_df['status'].value_counts()
            colors = ['red' if status == 'Critical' else 'green' for status in status_counts.index]
            ax3.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%',
                   colors=colors, startangle=90)
            ax3.set_title('⚠️ Stock Status Distribution', fontweight='bold')
            
            # 4. Optimization Savings Potential
            opt_df['potential_savings'] = (opt_df['current_stock'] - opt_df['optimal_order_qty']).abs()
            top_savings = opt_df.nlargest(10, 'potential_savings')
            
            ax4.barh(range(len(top_savings)), top_savings['potential_savings'], 
                    color='gold')
            ax4.set_title('💰 Top Optimization Opportunities', fontweight='bold')
            ax4.set_xlabel('Potential Stock Reduction')
            ax4.set_yticks(range(len(top_savings)))
            ax4.set_yticklabels([name[:15] for name in top_savings['product_name']])
            
            plt.tight_layout()
            plt.show()
            
            # Print recommendations
            critical_items = opt_df[opt_df['status'] == 'Critical']
            if not critical_items.empty:
                print(f"\n🚨 CRITICAL STOCK ALERTS ({len(critical_items)} items):")
                print("-" * 60)
                for _, item in critical_items.head(10).iterrows():
                    print(f"   {item['product_name'][:25]:25} | "
                          f"Current: {item['current_stock']:3.0f} | "
                          f"Reorder at: {item['reorder_point']:3.0f}")

    def _customer_segmentation_analysis(self):
        """Advanced customer segmentation using RFM analysis"""
        if self.df_sales.empty:
            print("⚠️ No sales data for customer segmentation")
            return
        
        print("\n👥 Customer Segmentation Analysis (Product-based)")
        
        # Create RFM-like analysis for products (treating products as customer proxies)
        current_date = self.df_sales['sale_date'].max()
        
        rfm_data = self.df_sales.groupby('product_id').agg({
            'sale_date': lambda x: (current_date - x.max()).days,  # Recency
            'id': 'count',  # Frequency
            'amount': 'sum'  # Monetary
        }).round(2)
        
        rfm_data.columns = ['Recency', 'Frequency', 'Monetary']
        
        # Add product names
        product_names = self.df_products.set_index('id')['name'].to_dict()
        rfm_data['product_name'] = rfm_data.index.map(product_names)
        
        # Create RFM scores
        rfm_data['R_Score'] = pd.qcut(rfm_data['Recency'], 5, labels=[5,4,3,2,1])
        rfm_data['F_Score'] = pd.qcut(rfm_data['Frequency'], 5, labels=[1,2,3,4,5])
        rfm_data['M_Score'] = pd.qcut(rfm_data['Monetary'], 5, labels=[1,2,3,4,5])
        
        # Combined RFM score
        rfm_data['RFM_Score'] = (rfm_data['R_Score'].astype(int) + 
                                rfm_data['F_Score'].astype(int) + 
                                rfm_data['M_Score'].astype(int))
        
        # K-means clustering
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(rfm_data[['Recency', 'Frequency', 'Monetary']])
        
        kmeans = KMeans(n_clusters=4, random_state=42)
        rfm_data['Cluster'] = kmeans.fit_predict(scaled_features)
        
        # Visualization
        fig = plt.figure(figsize=(20, 15))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. 3D Scatter plot
        ax1 = fig.add_subplot(gs[0, :], projection='3d')
        colors = ['red', 'blue', 'green', 'orange']
        
        for i, cluster in enumerate(rfm_data['Cluster'].unique()):
            cluster_data = rfm_data[rfm_data['Cluster'] == cluster]
            ax1.scatter(cluster_data['Recency'], cluster_data['Frequency'], 
                       cluster_data['Monetary'], c=colors[i], 
                       label=f'Cluster {cluster}', s=60, alpha=0.6)
        
        ax1.set_title('🎯 3D Product Segmentation (RFM Analysis)', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Recency (Days)')
        ax1.set_ylabel('Frequency')
        ax1.set_zlabel('Monetary ($)')
        ax1.legend()
        
        # 2. RFM Score Distribution
        ax2 = fig.add_subplot(gs[1, 0])
        rfm_data['RFM_Score'].hist(bins=15, color='skyblue', alpha=0.7, ax=ax2)
        ax2.set_title('📊 RFM Score Distribution', fontweight='bold')
        ax2.set_xlabel('RFM Score')
        ax2.set_ylabel('Number of Products')
        
        # 3. Cluster Characteristics
        ax3 = fig.add_subplot(gs[1, 1])
        cluster_summary = rfm_data.groupby('Cluster')[['Recency', 'Frequency', 'Monetary']].mean()
        
        x = np.arange(len(cluster_summary.columns))
        width = 0.2
        
        for i, cluster in enumerate(cluster_summary.index):
            values = cluster_summary.loc[cluster].values
            ax3.bar(x + i*width, values/values.max(), width, 
                   label=f'Cluster {cluster}', color=colors[i], alpha=0.7)
        
        ax3.set_title('📈 Cluster Characteristics (Normalized)', fontweight='bold')
        ax3.set_xlabel('RFM Metrics')
        ax3.set_ylabel('Normalized Value')
        ax3.set_xticks(x + width * 1.5)
        ax3.set_xticklabels(['Recency', 'Frequency', 'Monetary'])
        ax3.legend()
        
        # 4. Top Performers by Cluster
        ax4 = fig.add_subplot(gs[1, 2])
        top_products = rfm_data.nlargest(10, 'RFM_Score')
        
        bars = ax4.barh(range(len(top_products)), top_products['RFM_Score'])
        ax4.set_title('🏆 Top RFM Performers', fontweight='bold')
        ax4.set_xlabel('RFM Score')
        ax4.set_yticks(range(len(top_products)))
        ax4.set_yticklabels([name[:15] for name in top_products['product_name']])
        
        # Color bars by cluster
        for i, (bar, cluster) in enumerate(zip(bars, top_products['Cluster'])):
            bar.set_color(colors[cluster])
        
        # 5. Recency vs Monetary
        ax5 = fig.add_subplot(gs[2, 0])
        scatter = ax5.scatter(rfm_data['Recency'], rfm_data['Monetary'], 
                             c=rfm_data['Cluster'], cmap='viridis', alpha=0.7)
        ax5.set_title('💰 Recency vs Monetary Value', fontweight='bold')
        ax5.set_xlabel('Recency (Days)')
        ax5.set_ylabel('Monetary Value ($)')
        plt.colorbar(scatter, ax=ax5)
        
        # 6. Frequency vs Monetary
        ax6 = fig.add_subplot(gs[2, 1])
        scatter = ax6.scatter(rfm_data['Frequency'], rfm_data['Monetary'], 
                             c=rfm_data['Cluster'], cmap='plasma', alpha=0.7)
        ax6.set_title('📈 Frequency vs Monetary Value', fontweight='bold')
        ax6.set_xlabel('Frequency')
        ax6.set_ylabel('Monetary Value ($)')
        plt.colorbar(scatter, ax=ax6)
        
        # 7. Cluster Size Distribution
        ax7 = fig.add_subplot(gs[2, 2])
        cluster_sizes = rfm_data['Cluster'].value_counts().sort_index()
        wedges, texts, autotexts = ax7.pie(cluster_sizes.values, 
                                          labels=[f'Cluster {i}' for i in cluster_sizes.index],
                                          colors=colors, autopct='%1.1f%%', startangle=90)
        ax7.set_title('🥧 Cluster Distribution', fontweight='bold')
        
        plt.suptitle('👥 Advanced Customer Segmentation Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.show()
        
        # Segment insights
        print("\n📊 SEGMENTATION INSIGHTS:")
        print("-" * 50)
        for cluster in sorted(rfm_data['Cluster'].unique()):
            cluster_data = rfm_data[rfm_data['Cluster'] == cluster]
            avg_recency = cluster_data['Recency'].mean()
            avg_frequency = cluster_data['Frequency'].mean()
            avg_monetary = cluster_data['Monetary'].mean()
            
            # Determine segment type
            if avg_frequency > rfm_data['Frequency'].median() and avg_monetary > rfm_data['Monetary'].median():
                segment_type = "🌟 Champions"
            elif avg_recency < rfm_data['Recency'].median() and avg_frequency > rfm_data['Frequency'].median():
                segment_type = "💎 Loyal Customers"
            elif avg_monetary > rfm_data['Monetary'].median():
                segment_type = "💰 Big Spenders"
            else:
                segment_type = "🔄 Potential"
            
            print(f"\nCluster {cluster} - {segment_type}:")
            print(f"   Size: {len(cluster_data)} products ({len(cluster_data)/len(rfm_data)*100:.1f}%)")
            print(f"   Avg Recency: {avg_recency:.1f} days")
            print(f"   Avg Frequency: {avg_frequency:.1f} transactions")
            print(f"   Avg Monetary: ${avg_monetary:.2f}")

    def _price_optimization_analysis(self):
        """Advanced price optimization using elasticity analysis"""
        if self.df_products.empty or self.df_sales.empty:
            print("⚠️ Insufficient data for price optimization")
            return
        
        print("\n💰 Price Optimization Analysis")
        
        # Price elasticity analysis
        price_analysis = []
        
        for product_id in self.df_products['id'].unique():
            product_sales = self.df_sales[self.df_sales['product_id'] == product_id]
            product_info = self.df_products[self.df_products['id'] == product_id].iloc[0]
            
            if len(product_sales) > 5:  # Need sufficient data
                # Simple price elasticity calculation
                avg_price = product_info['price']
                total_quantity = product_sales['quantity_sold'].sum()
                avg_quantity_per_transaction = product_sales['quantity_sold'].mean()
                revenue = product_sales['amount'].sum()
                
                # Price sensitivity analysis (simplified)
                price_points = np.linspace(avg_price * 0.7, avg_price * 1.3, 20)
                estimated_quantities = []
                estimated_revenues = []
                
                # Simple demand curve (assumes linear relationship)
                base_elasticity = -1.5  # Assumed elasticity
                
                for price in price_points:
                    price_change = (price - avg_price) / avg_price
                    quantity_change = base_elasticity * price_change
                    estimated_quantity = total_quantity * (1 + quantity_change)
                    estimated_quantity = max(0, estimated_quantity)  # Can't be negative
                    
                    estimated_quantities.append(estimated_quantity)
                    estimated_revenues.append(price * estimated_quantity)
                
                # Find optimal price (max revenue)
                optimal_price_idx = np.argmax(estimated_revenues)
                optimal_price = price_points[optimal_price_idx]
                optimal_revenue = estimated_revenues[optimal_price_idx]
                
                price_analysis.append({
                    'product_id': product_id,
                    'product_name': product_info['name'],
                    'current_price': avg_price,
                    'optimal_price': optimal_price,
                    'current_revenue': revenue,
                    'potential_revenue': optimal_revenue,
                    'price_change_pct': ((optimal_price - avg_price) / avg_price) * 100,
                    'revenue_change_pct': ((optimal_revenue - revenue) / revenue) * 100 if revenue > 0 else 0,
                    'price_points': price_points,
                    'revenue_curve': estimated_revenues
                })
        
        if price_analysis:
            price_df = pd.DataFrame(price_analysis)
            
            # Visualization
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # 1. Price vs Revenue Optimization
            top_opportunities = price_df.nlargest(5, 'revenue_change_pct')
            
            for i, row in enumerate(top_opportunities.iterrows()):
                _, product = row
                ax1.plot(product['price_points'], product['revenue_curve'], 
                        label=product['product_name'][:15], linewidth=2)
                
                # Mark current and optimal points
                current_idx = np.argmin(np.abs(product['price_points'] - product['current_price']))
                optimal_idx = np.argmax(product['revenue_curve'])
                
                ax1.scatter(product['current_price'], product['revenue_curve'][current_idx], 
                           color='red', marker='o', s=100, zorder=5)
                ax1.scatter(product['optimal_price'], product['revenue_curve'][optimal_idx], 
                           color='green', marker='*', s=150, zorder=5)
            
            ax1.set_title('📈 Price vs Revenue Optimization Curves', fontweight='bold')
            ax1.set_xlabel('Price ($)')
            ax1.set_ylabel('Estimated Revenue ($)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. Current vs Optimal Pricing
            products_to_show = price_df.head(10)
            x_pos = np.arange(len(products_to_show))
            
            ax2.bar(x_pos - 0.2, products_to_show['current_price'], 0.4, 
                   label='Current Price', color='lightblue', alpha=0.7)
            ax2.bar(x_pos + 0.2, products_to_show['optimal_price'], 0.4, 
                   label='Optimal Price', color='orange', alpha=0.7)
            
            ax2.set_title('💰 Current vs Optimal Pricing', fontweight='bold')
            ax2.set_xlabel('Products')
            ax2.set_ylabel('Price ($)')
            ax2.set_xticks(x_pos)
            ax2.set_xticklabels([name[:15] for name in products_to_show['product_name']], 
                               rotation=45, ha='right')
            ax2.legend()
            
            # 3. Revenue Impact Analysis
            ax3.scatter(price_df['price_change_pct'], price_df['revenue_change_pct'], 
                       s=price_df['current_revenue']/100, alpha=0.6, c='green')
            
            ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            ax3.axvline(x=0, color='black', linestyle='--', alpha=0.5)
            
            ax3.set_title('🎯 Price Change vs Revenue Impact', fontweight='bold')
            ax3.set_xlabel('Price Change (%)')
            ax3.set_ylabel('Revenue Change (%)')
            ax3.grid(True, alpha=0.3)
            
            # Add quadrant labels
            ax3.text(10, 10, 'Price ↑\nRevenue ↑', ha='center', va='center', 
                    bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
            ax3.text(-10, 10, 'Price ↓\nRevenue ↑', ha='center', va='center', 
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
            
            # 4. Top Optimization Opportunities
            opportunities = price_df.nlargest(10, 'revenue_change_pct')
            
            bars = ax4.barh(range(len(opportunities)), opportunities['revenue_change_pct'], 
                           color='gold', alpha=0.8)
            
            ax4.set_title('🏆 Top Revenue Optimization Opportunities', fontweight='bold')
            ax4.set_xlabel('Potential Revenue Increase (%)')
            ax4.set_yticks(range(len(opportunities)))
            ax4.set_yticklabels([name[:15] for name in opportunities['product_name']])
            
            # Add value labels
            for i, (bar, value) in enumerate(zip(bars, opportunities['revenue_change_pct'])):
                ax4.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                        f'+{value:.1f}%', va='center', fontweight='bold')
            
            plt.tight_layout()
            plt.show()
            
            # Print recommendations
            high_impact = price_df[price_df['revenue_change_pct'] > 5]  # >5% revenue increase
            
            if not high_impact.empty:
                print(f"\n🎯 HIGH-IMPACT PRICING OPPORTUNITIES ({len(high_impact)} products):")
                print("-" * 70)
                print(f"{'Product':<25} {'Current':<10} {'Optimal':<10} {'Revenue↑':<12}")
                print("-" * 70)
                
                for _, item in high_impact.head(10).iterrows():
                    print(f"{item['product_name'][:24]:<25} "
                          f"${item['current_price']:<9.2f} "
                          f"${item['optimal_price']:<9.2f} "
                          f"+{item['revenue_change_pct']:<11.1f}%")
                
                print(f"\n💡 PRICING STRATEGY INSIGHTS:")
                print(f"   • Products with price increase potential: {len(high_impact[high_impact['price_change_pct'] > 0])}")
                print(f"   • Products with price decrease potential: {len(high_impact[high_impact['price_change_pct'] < 0])}")
                print(f"   • Average potential revenue increase: {high_impact['revenue_change_pct'].mean():.1f}%")

    def generate_executive_summary(self):
        """Generate executive summary report"""
        print("\n📋 EXECUTIVE SUMMARY REPORT")
        print("=" * 60)
        
        # Key metrics
        if not self.df_sales.empty:
            total_revenue = self.df_sales['amount'].sum()
            total_transactions = len(self.df_sales)
            avg_transaction = self.df_sales['amount'].mean()
            
            print(f"💰 FINANCIAL PERFORMANCE:")
            print(f"   Total Revenue: ${total_revenue:,.2f}")
            print(f"   Total Transactions: {total_transactions:,}")
            print(f"   Average Transaction: ${avg_transaction:.2f}")
        
        if not self.df_products.empty:
            total_products = len(self.df_products)
            low_stock = len(self.df_products[self.df_products['current_stock'] <= self.df_products['minimum_stock']])
            expiring_soon = len(self.df_products[self.df_products['days_to_expiry'] <= 30])
            
            print(f"\n📦 INVENTORY STATUS:")
            print(f"   Total Products: {total_products:,}")
            print(f"   Low Stock Alert: {low_stock} items")
            print(f"   Expiring Soon: {expiring_soon} items")
        
        print(f"\n🏭 OPERATIONAL METRICS:")
        print(f"   Active Categories: {len(self.df_categories)}")
        print(f"   Active Suppliers: {len(self.df_suppliers)}")
        
        if not self.df_recommendations.empty:
            print(f"   AI Recommendations: {len(self.df_recommendations)}")
        
        print(f"\n✅ ANALYSIS COMPLETE!")
        print(f"   Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def run_complete_analysis(self):
        """Run the complete advanced analytics suite"""
        print("🚀 STARTING COMPREHENSIVE ADVANCED ANALYTICS")
        print("=" * 80)
        
        try:
            # 1. Generate main dashboard
            self.generate_comprehensive_dashboard()
            
            print("\n" + "="*60)
            input("Press Enter to continue to Predictive Analytics...")
            
            # 2. Predictive analytics
            self.generate_predictive_analytics()
            
            print("\n" + "="*60)
            input("Press Enter to continue to Executive Summary...")
            
            # 3. Executive summary
            self.generate_executive_summary()
            
            print("\n" + "="*80)
            print("🎉 ADVANCED ANALYTICS COMPLETE!")
            print("=" * 80)
            print("📊 All visualizations and insights have been generated.")
            print("💡 Use these insights for strategic decision making.")
            print("🔄 Regular analysis ensures optimal inventory performance.")
            
        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            if hasattr(self, 'conn'):
                self.conn.close()

# ============ MAIN EXECUTION ============

def main():
    """Main execution function"""
    print("🎨 ADVANCED INVENTORY ANALYTICS SYSTEM")
    print("=" * 80)
    print("🏢 Enterprise-Grade Graphical Analysis")
    print("📊 Comprehensive Visual Analytics Suite")
    print("🤖 Machine Learning & Predictive Insights")
    print("=" * 80)
    
    try:
        # Initialize analytics system
        print("\n🔧 Initializing Advanced Analytics System...")
        analytics = AdvancedInventoryAnalytics()
        
        print("\n📋 Choose Analysis Mode:")
        print("1. 🎨 Complete Visual Analytics Suite")
        print("2. 📊 Dashboard + Predictive Analytics")
        print("3. 🔍 Custom Analysis Menu")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            analytics.run_complete_analysis()
        elif choice == '2':
            analytics.generate_comprehensive_dashboard()
            analytics.generate_predictive_analytics()
        elif choice == '3':
            print("\n📋 Custom Analysis Options:")
            print("a. 🎨 Comprehensive Dashboard")
            print("b. 🔮 Predictive Analytics")
            print("c. 📈 Interactive Visualizations")
            
            sub_choice = input("Enter your choice (a-c): ").strip().lower()
            
            if sub_choice == 'a':
                analytics.generate_comprehensive_dashboard()
            elif sub_choice == 'b':
                analytics.generate_predictive_analytics()
            elif sub_choice == 'c':
                analytics._generate_interactive_plots()
        else:
            print("Running complete analysis by default...")
            analytics.run_complete_analysis()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
