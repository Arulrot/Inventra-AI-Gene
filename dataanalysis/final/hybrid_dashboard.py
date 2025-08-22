"""
Hybrid Dashboard: Traditional Analytics + Gemini Chatbot
Fixed version with comprehensive error handling
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import json
from final.hybrid_analytics_engine import HybridAnalyticsEngine, format_rupees

# Page configuration
st.set_page_config(
    page_title="🤖 Hybrid Retail Analytics",
    page_icon="🤖",
    layout="wide"
)

# CSS styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    .recommendation-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #28a745;
    }
    
    .alert-card {
        background: #fff3cd;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #ffc107;
    }
    
    .chat-user {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: right;
    }
    
    .chat-bot {
        background: #f5f5f5;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)

def safe_get(data, key, default=None):
    """Safely get value from dict"""
    if data is None:
        return default
    return data.get(key, default)

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 Hybrid Retail Analytics</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Traditional ML/Stats Analysis + Gemini AI Chatbot</p>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = None
    
    # Sidebar
    with st.sidebar:
        st.title("🎛️ Analytics Control")
        
        if st.button("🚀 Run Analytics Engine", type="primary"):
            with st.spinner("🔄 Running hybrid analytics..."):
                try:
                    engine = HybridAnalyticsEngine()
                    st.session_state.analysis_data = engine.run_analysis()
                    st.success("✅ Analysis Complete!")
                except Exception as e:
                    st.error(f"❌ Analysis failed: {e}")
                    st.session_state.analysis_data = None
        
        # Show quick stats only if data exists
        if st.session_state.analysis_data:
            results = safe_get(st.session_state.analysis_data, 'analysis_results')
            if results and 'descriptive' in results:
                st.markdown("---")
                st.markdown("### 📊 Quick Stats")
                metrics = safe_get(results['descriptive'], 'basic_metrics', {})
                st.metric("💰 Revenue", format_rupees(metrics.get('total_revenue', 0)))
                st.metric("📊 Profit", f"{metrics.get('profit_margin', 0):.1f}%")
                st.metric("🛒 Transactions", f"{metrics.get('total_transactions', 0):,}")
    
    # Main content
    if st.session_state.analysis_data is None:
        show_welcome_screen()
    else:
        show_hybrid_dashboard()

def show_welcome_screen():
    """Welcome screen"""
    
    st.markdown("""
    <div style="text-align: center; padding: 3rem;">
        <h2>🤖 Welcome to Hybrid Analytics</h2>
        <p style="font-size: 1.2rem; color: #666;">
            Combining the power of traditional ML/Statistics with Gemini AI
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="recommendation-card">
            <h3>📊 Traditional Analytics</h3>
            <p>• Machine Learning models for predictions</p>
            <p>• Statistical analysis for insights</p>
            <p>• Automated chart generation</p>
            <p>• Rule-based recommendations</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="alert-card">
            <h3>🤖 Gemini AI Chatbot</h3>
            <p>• Natural language data queries</p>
            <p>• Specific questions about your data</p>
            <p>• Real-time data exploration</p>
            <p>• Context-aware responses</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.info("👈 Click 'Run Analytics Engine' in the sidebar to start!")

def show_hybrid_dashboard():
    """Main hybrid dashboard with error handling"""
    
    # Safely extract data
    data = safe_get(st.session_state.analysis_data, 'data')
    results = safe_get(st.session_state.analysis_data, 'analysis_results')
    chatbot = safe_get(st.session_state.analysis_data, 'chatbot')
    
    # Check if we have results
    if results is None:
        st.error("❌ Analysis results not available. Please run the analysis again.")
        return
    
    if 'error' in results:
        st.error(f"❌ Analysis error: {results['error']}")
        return
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", 
        "🔍 Analysis", 
        "📈 Charts", 
        "💡 Recommendations",
        "🤖 Ask Gemini"
    ])
    
    with tab1:
        show_dashboard_overview(results)
    
    with tab2:
        show_detailed_analysis(results)
    
    with tab3:
        show_charts(data, results)
    
    with tab4:
        show_recommendations(results)
    
    with tab5:
        if chatbot:
            show_gemini_chatbot(chatbot)
        else:
            st.error("Chatbot not available. Please run analysis first.")

def show_dashboard_overview(results):
    """Dashboard overview with error handling"""
    
    # Safely get descriptive results
    desc = safe_get(results, 'descriptive')
    if not desc:
        st.error("❌ Descriptive analytics not available.")
        return
    
    metrics = safe_get(desc, 'basic_metrics', {})
    if not metrics:
        st.error("❌ Basic metrics not available.")
        return
    
    st.subheader("📊 Business Dashboard")
    
    # Key metrics with safe access
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💰 Revenue</h3>
            <h2>{format_rupees(metrics.get('total_revenue', 0))}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 Profit</h3>
            <h2>{format_rupees(metrics.get('total_profit', 0))}</h2>
            <p>{metrics.get('profit_margin', 0):.1f}% margin</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🛒 Orders</h3>
            <h2>{metrics.get('total_transactions', 0):,}</h2>
            <p>{format_rupees(metrics.get('avg_order_value', 0))} avg</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>👥 Customers</h3>
            <h2>{metrics.get('unique_customers', 0):,}</h2>
            <p>{metrics.get('unique_products', 0)} products</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Date range info
    col1, col2 = st.columns(2)
    with col1:
        min_date = metrics.get('min_sale_date', 'N/A')
        max_date = metrics.get('max_sale_date', 'N/A')
        st.info(f"📅 **Analysis Period**: {min_date} to {max_date}")
    with col2:
        max_sale = metrics.get('max_sale_amount', 0)
        st.success(f"💰 **Highest Sale**: {format_rupees(max_sale)}")

def show_detailed_analysis(results):
    """Detailed analysis with error handling"""
    
    st.subheader("🔍 Detailed Analysis")
    
    # Safely get all result sections
    desc = safe_get(results, 'descriptive', {})
    diag = safe_get(results, 'diagnostic', {})
    pred = safe_get(results, 'predictive', {})
    
    if not desc:
        st.warning("Descriptive analytics not available.")
        return
    
    # Top products
    st.markdown("### 🏆 Top Performing Products")
    top_products = safe_get(desc, 'top_products', {})
    
    if top_products:
        try:
            products_df = pd.DataFrame.from_dict(top_products, orient='index')
            products_df = products_df.round(2)
            st.dataframe(products_df.head(10), use_container_width=True)
        except Exception as e:
            st.error(f"Error displaying top products: {e}")
    else:
        st.info("No top products data available.")
    
    # Category performance
    st.markdown("### 🏷️ Category Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        category_perf = safe_get(desc, 'category_performance', {})
        if category_perf:
            try:
                cat_df = pd.DataFrame.from_dict(category_perf, orient='index')
                cat_df = cat_df.round(2)
                st.dataframe(cat_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying categories: {e}")
        else:
            st.info("No category data available.")
    
    with col2:
        # Customer segments
        segments = safe_get(desc, 'customer_segments', {})
        if segments:
            try:
                fig = px.pie(values=list(segments.values()), names=list(segments.keys()),
                            title="👥 Customer Segments")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating segments chart: {e}")
        else:
            st.info("No customer segments data available.")
    
    # Inventory issues
    if diag:
        st.markdown("### 📦 Inventory Issues")
        inventory_issues = safe_get(diag, 'inventory_issues', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            understocked = safe_get(inventory_issues, 'understocked', [])
            if understocked:
                count = safe_get(inventory_issues, 'understocked_count', len(understocked))
                st.error(f"🚨 **{count} Understocked Products:**")
                for product in understocked[:5]:
                    st.write(f"• {product}")
            else:
                st.success("✅ No understocked products")
        
        with col2:
            overstocked = safe_get(inventory_issues, 'overstocked', [])
            if overstocked:
                count = safe_get(inventory_issues, 'overstocked_count', len(overstocked))
                st.warning(f"📈 **{count} Overstocked Products:**")
                for product in overstocked[:5]:
                    st.write(f"• {product}")
            else:
                st.success("✅ No overstocked products")
    
    # Predictions
    if pred:
        st.markdown("### 🔮 Predictions")
        
        sales_forecast = safe_get(pred, 'sales_forecast', {})
        if sales_forecast and 'error' not in sales_forecast:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                forecast_total = sales_forecast.get('next_30_days_total', 0)
                st.metric("📈 30-Day Forecast", format_rupees(forecast_total))
            with col2:
                daily_avg = sales_forecast.get('daily_average', 0)
                st.metric("📊 Daily Average", format_rupees(daily_avg))
            with col3:
                trend = sales_forecast.get('trend', 'unknown')
                trend_emoji = "📈" if trend == 'increasing' else "📉"
                st.metric("📉 Trend", f"{trend_emoji} {trend.title()}")
        else:
            st.info("Sales forecast not available.")
    
    # Expiring products
    expiring = safe_get(desc, 'expiring_products', {})
    if expiring:
        st.markdown("### ⚠️ Products Expiring Soon")
        st.error(f"🚨 {len(expiring)} products expiring within 30 days")
        
        for product, count in list(expiring.items())[:10]:
            st.write(f"• **{product}**: {count} units")

def show_charts(data, results):
    """Charts with error handling"""
    
    st.subheader("📈 Analytics Charts")
    
    if data is None:
        st.error("❌ Data not available for charts.")
        return
    
    desc = safe_get(results, 'descriptive', {})
    if not desc:
        st.error("❌ Descriptive results not available for charts.")
        return
    
    # Monthly sales trend
    st.markdown("### 📅 Monthly Sales Trend")
    monthly_trend = safe_get(desc, 'monthly_trend', {})
    
    if monthly_trend:
        try:
            months = list(monthly_trend.keys())
            values = list(monthly_trend.values())
            
            fig1 = px.line(x=months, y=values, title="Monthly Revenue Trend",
                          labels={'x': 'Month', 'y': 'Revenue (₹)'})
            fig1.update_traces(line=dict(width=3, color='#1f77b4'))
            st.plotly_chart(fig1, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating monthly trend chart: {e}")
    else:
        st.info("No monthly trend data available.")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        # Top products chart
        top_products = safe_get(desc, 'top_products', {})
        if top_products:
            try:
                products = list(top_products.keys())[:8]
                revenues = [top_products[p].get('total_revenue', 0) for p in products]
                
                fig2 = px.bar(x=revenues, y=products, orientation='h',
                             title="🏆 Top Products by Revenue")
                fig2.update_traces(marker_color='#2ca02c')
                fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig2, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating products chart: {e}")
    
    with col2:
        # Category performance
        category_perf = safe_get(desc, 'category_performance', {})
        if category_perf:
            try:
                categories = list(category_perf.keys())
                amounts = [category_perf[cat].get('amount', 0) for cat in categories]
                
                fig3 = px.pie(values=amounts, names=categories,
                             title="🏷️ Revenue by Category")
                st.plotly_chart(fig3, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating category chart: {e}")
    
    # Weekly patterns
    if 'weekday' in data.columns and 'amount' in data.columns:
        st.markdown("### 📊 Weekly Sales Pattern")
        try:
            weekly_data = data.groupby('weekday')['amount'].mean().reindex([
                'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
            ])
            
            fig4 = px.bar(x=weekly_data.index, y=weekly_data.values,
                         title="Average Sales by Day of Week")
            fig4.update_traces(marker_color='#ff7f0e')
            st.plotly_chart(fig4, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating weekly pattern chart: {e}")

def show_recommendations(results):
    """Recommendations with error handling"""
    
    st.subheader("💡 Smart Recommendations")
    
    prescriptive = safe_get(results, 'prescriptive', {})
    if not prescriptive:
        st.error("❌ Prescriptive analytics not available.")
        return
    
    recommendations = safe_get(prescriptive, 'recommendations', [])
    priority_summary = safe_get(prescriptive, 'priority_summary', {})
    
    if not recommendations:
        st.info("No recommendations available at this time.")
        return
    
    # Priority summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🔴 High Priority", priority_summary.get('high_priority', 0))
    with col2:
        st.metric("🟡 Medium Priority", priority_summary.get('medium_priority', 0))
    with col3:
        st.metric("📋 Total Actions", priority_summary.get('total_actions', 0))
    
    # Display recommendations
    high_priority = [r for r in recommendations if r.get('priority') == 'High']
    medium_priority = [r for r in recommendations if r.get('priority') == 'Medium']
    
    if high_priority:
        st.markdown("### 🚨 High Priority Actions")
        for rec in high_priority:
            st.markdown(f"""
            <div class="alert-card">
                <h4>🎯 {rec.get('title', 'Recommendation')}</h4>
                <p><strong>Type:</strong> {rec.get('type', 'General')}</p>
                <p>{rec.get('description', 'No description available')}</p>
                <p><strong>Actions:</strong></p>
                <ul>
                    {''.join([f'<li>{action}</li>' for action in rec.get('actions', [])])}
                </ul>
                <p><strong>Expected Impact:</strong> {rec.get('expected_impact', 'Not specified')}</p>
                <p><strong>Timeline:</strong> {rec.get('timeline', 'Not specified')}</p>
            </div>
            """, unsafe_allow_html=True)
    
    if medium_priority:
        st.markdown("### 📋 Medium Priority Actions")
        for rec in medium_priority:
            st.markdown(f"""
            <div class="recommendation-card">
                <h4>📊 {rec.get('title', 'Recommendation')}</h4>
                <p><strong>Type:</strong> {rec.get('type', 'General')}</p>
                <p>{rec.get('description', 'No description available')}</p>
                <p><strong>Actions:</strong></p>
                <ul>
                    {''.join([f'<li>{action}</li>' for action in rec.get('actions', [])])}
                </ul>
                <p><strong>Expected Impact:</strong> {rec.get('expected_impact', 'Not specified')}</p>
                <p><strong>Timeline:</strong> {rec.get('timeline', 'Not specified')}</p>
            </div>
            """, unsafe_allow_html=True)

def show_gemini_chatbot(chatbot):
    """Gemini chatbot with error handling"""
    
    st.subheader("🤖 Ask Gemini About Your Data")
    
    if chatbot is None:
        st.error("❌ Chatbot not available. Please run analysis first.")
        return
    
    st.markdown("""
    <div class="recommendation-card">
        <strong>💬 Data Query Assistant</strong><br>
        Ask specific questions about your business data using natural language!<br>
        <em>Examples: "What is the maximum sale date?", "Which products are expiring soon?", "What's the total revenue?"</em>
    </div>
    """, unsafe_allow_html=True)
    
    # Suggested questions
    st.markdown("### 💡 Try These Questions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📅 What is the maximum sale date?"):
            st.session_state.gemini_query = "What is the maximum sale date in my data?"
        if st.button("💰 What's my total revenue?"):
            st.session_state.gemini_query = "What is my total revenue?"
        if st.button("🏆 Top 5 selling products?"):
            st.session_state.gemini_query = "What are my top 5 selling products?"
    
    with col2:
        if st.button("⚠️ Products expiring soon?"):
            st.session_state.gemini_query = "Which products are expiring soon?"
        if st.button("📦 Products out of stock?"):
            st.session_state.gemini_query = "Which products need restocking urgently?"
        if st.button("👥 Customer segments breakdown?"):
            st.session_state.gemini_query = "What is the breakdown of my customer segments?"
    
    # Chat interface
    if "gemini_messages" not in st.session_state:
        st.session_state.gemini_messages = []
    
    # Display chat history
    for message in st.session_state.gemini_messages:
        st.markdown(f"""
        <div class="chat-user">
            <strong>You:</strong> {message.get('question', 'N/A')}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="chat-bot">
            <strong>🤖 Gemini:</strong> {message.get('answer', 'N/A')}
        </div>
        """, unsafe_allow_html=True)
    
    # Handle suggested questions
    if hasattr(st.session_state, 'gemini_query'):
        query = st.session_state.gemini_query
        delattr(st.session_state, 'gemini_query')
        
        with st.spinner("🤖 Gemini is analyzing your data..."):
            try:
                response = chatbot.query_data(query)
                
                st.session_state.gemini_messages.append({
                    'question': query,
                    'answer': response
                })
            except Exception as e:
                st.error(f"Error querying chatbot: {e}")
        
        st.rerun()
    
    # Text input for custom questions
    user_question = st.text_input("Ask a question about your data:", 
                                 placeholder="e.g., Which category has the highest profit margin?")
    
    if st.button("Send 🚀") and user_question:
        with st.spinner("🤖 Gemini is processing your question..."):
            try:
                response = chatbot.query_data(user_question)
                
                st.session_state.gemini_messages.append({
                    'question': user_question,
                    'answer': response
                })
            except Exception as e:
                st.error(f"Error processing question: {e}")
        
        st.rerun()

if __name__ == "__main__":
    main()
