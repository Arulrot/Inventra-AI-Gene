from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
import numpy as np
from datetime import datetime
import json
import os
import google.generativeai as genai
from final.hybrid_analytics_engine import HybridAnalyticsEngine, format_rupees

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-to-random-string'

# Inventra AI Gene Configuration
INVENTRA_AI_API_KEY = "AIzaSyBZPHzSV7AfiOPZDb2VsnavkU4xQEkZzHU"
genai.configure(api_key=INVENTRA_AI_API_KEY)
inventra_model = genai.GenerativeModel('gemini-1.5-flash')

print("🤖 Inventra AI Gene (Powered by Google Gemini) initialized successfully!")

# Simple caching system
analysis_cache = {}

def safe_get(data, key, default=None):
    """Safely get value from dict"""
    if data is None:
        return default
    return data.get(key, default)

def serialize_analysis_data(analysis_data):
    """Convert analysis data to JSON-serializable format"""
    if not analysis_data:
        return None
    
    # Store the full data in cache with session ID
    session_id = session.get('session_id', str(datetime.now().timestamp()))
    session['session_id'] = session_id
    analysis_cache[session_id] = analysis_data
    
    # Return simple metadata for session
    return {
        'success': True,
        'timestamp': datetime.now().isoformat()
    }

def get_analysis_data():
    """Retrieve analysis data from cache"""
    session_id = session.get('session_id')
    if session_id and session_id in analysis_cache:
        return analysis_cache[session_id]
    return None

def prepare_inventra_context(analysis_results):
    """Prepare data context for Inventra AI Gene"""
    if not analysis_results or 'descriptive' not in analysis_results:
        return "No analysis data available"
    
    desc = analysis_results.get('descriptive', {})
    basic_metrics = desc.get('basic_metrics', {})
    
    context = f"""
BUSINESS DATA SUMMARY:
- Total Revenue: ₹{basic_metrics.get('total_revenue', 0):,.2f}
- Total Transactions: {basic_metrics.get('total_transactions', 0):,}
- Unique Products: {basic_metrics.get('unique_products', 0)}
- Unique Customers: {basic_metrics.get('unique_customers', 0)}
- Profit Margin: {basic_metrics.get('profit_margin', 0):.2f}%
- Analysis Period: {basic_metrics.get('min_sale_date', 'N/A')} to {basic_metrics.get('max_sale_date', 'N/A')}

TOP PRODUCTS: {json.dumps(list(desc.get('top_products', {}).keys())[:10])}
CATEGORIES: {json.dumps(list(desc.get('category_performance', {}).keys()))}
CUSTOMER SEGMENTS: {json.dumps(desc.get('customer_segments', {}))}
EXPIRING PRODUCTS: {json.dumps(list(desc.get('expiring_products', {}).keys())[:10])}
INVENTORY ISSUES: 
- Understocked: {analysis_results.get('diagnostic', {}).get('inventory_issues', {}).get('understocked', [])}
- Overstocked: {analysis_results.get('diagnostic', {}).get('inventory_issues', {}).get('overstocked', [])}
    """
    return context

@app.route('/')
def index():
    """Main dashboard route"""
    return render_template('inventra_index.html')

@app.route('/run_analysis', methods=['POST'])
def run_analysis():
    """Run the analytics engine"""
    try:
        print("🔄 Starting Analytics Engine...")
        engine = HybridAnalyticsEngine()
        analysis_data = engine.run_analysis()
        
        # Store in cache
        serializable_data = serialize_analysis_data(analysis_data)
        session['analysis_data'] = serializable_data
        
        # Extract quick stats
        results = safe_get(analysis_data, 'analysis_results')
        quick_stats = {}
        
        if results and 'descriptive' in results:
            metrics = safe_get(results['descriptive'], 'basic_metrics', {})
            quick_stats = {
                'revenue': format_rupees(metrics.get('total_revenue', 0)),
                'profit': f"{metrics.get('profit_margin', 0):.1f}%",
                'transactions': f"{metrics.get('total_transactions', 0):,}"
            }
        
        print("✅ Analysis Complete!")
        
        return jsonify({
            'success': True,
            'quick_stats': quick_stats,
            'message': 'Analysis Complete! Inventra AI Gene is ready!'
        })
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_dashboard_data')
def get_dashboard_data():
    """Get dashboard data"""
    analysis_data = get_analysis_data()
    if not analysis_data:
        return jsonify({'error': 'No analysis data available'})
    
    results = safe_get(analysis_data, 'analysis_results')
    if not results:
        return jsonify({'error': 'Analysis results not available'})
    
    desc = safe_get(results, 'descriptive', {})
    metrics = safe_get(desc, 'basic_metrics', {})
    
    return jsonify({
        'revenue': format_rupees(metrics.get('total_revenue', 0)),
        'profit': format_rupees(metrics.get('total_profit', 0)),
        'profit_margin': f"{metrics.get('profit_margin', 0):.1f}%",
        'orders': f"{metrics.get('total_transactions', 0):,}",
        'avg_order': format_rupees(metrics.get('avg_order_value', 0)),
        'customers': f"{metrics.get('unique_customers', 0):,}",
        'products': metrics.get('unique_products', 0),
        'min_date': metrics.get('min_sale_date', 'N/A'),
        'max_date': metrics.get('max_sale_date', 'N/A'),
        'max_sale': format_rupees(metrics.get('max_sale_amount', 0))
    })

@app.route('/get_detailed_analysis')
def get_detailed_analysis():
    """Get detailed analysis data"""
    analysis_data = get_analysis_data()
    if not analysis_data:
        return jsonify({'error': 'No analysis data available'})
    
    results = safe_get(analysis_data, 'analysis_results')
    desc = safe_get(results, 'descriptive', {})
    diag = safe_get(results, 'diagnostic', {})
    pred = safe_get(results, 'predictive', {})
    
    # Top products
    top_products = safe_get(desc, 'top_products', {})
    top_products_list = []
    if top_products:
        for product, data in list(top_products.items())[:10]:
            top_products_list.append({
                'product': product,
                'revenue': format_rupees(data.get('total_revenue', 0)),
                'transactions': data.get('transaction_count', 0),
                'avg_price': format_rupees(data.get('avg_price', 0)),
                'units_sold': data.get('total_units_sold', 0)
            })
    
    # Category performance
    category_perf = safe_get(desc, 'category_performance', {})
    categories_list = []
    if category_perf:
        for category, data in category_perf.items():
            categories_list.append({
                'category': category,
                'amount': format_rupees(data.get('amount', 0)),
                'quantity': data.get('quantity_sold', 0)
            })
    
    # Other data
    segments = safe_get(desc, 'customer_segments', {})
    inventory_issues = safe_get(diag, 'inventory_issues', {})
    sales_forecast = safe_get(pred, 'sales_forecast', {})
    expiring = safe_get(desc, 'expiring_products', {})
    expiring_list = [{'product': k, 'count': v} for k, v in list(expiring.items())[:10]]
    
    return jsonify({
        'top_products': top_products_list,
        'categories': categories_list,
        'segments': segments,
        'inventory': {
            'understocked': inventory_issues.get('understocked', [])[:5],
            'overstocked': inventory_issues.get('overstocked', [])[:5],
            'understocked_count': inventory_issues.get('understocked_count', 0),
            'overstocked_count': inventory_issues.get('overstocked_count', 0)
        },
        'forecast': {
            'total': format_rupees(sales_forecast.get('next_30_days_total', 0)) if 'error' not in sales_forecast else 'N/A',
            'daily_avg': format_rupees(sales_forecast.get('daily_average', 0)) if 'error' not in sales_forecast else 'N/A',
            'trend': sales_forecast.get('trend', 'unknown') if 'error' not in sales_forecast else 'unknown'
        },
        'expiring': expiring_list
    })

@app.route('/get_charts_data')
def get_charts_data():
    """Get data for charts"""
    analysis_data = get_analysis_data()
    if not analysis_data:
        return jsonify({'error': 'No analysis data available'})
    
    results = safe_get(analysis_data, 'analysis_results')
    data = safe_get(analysis_data, 'data')
    desc = safe_get(results, 'descriptive', {})
    
    charts_data = {}
    
    # Monthly trend
    monthly_trend = safe_get(desc, 'monthly_trend', {})
    if monthly_trend:
        charts_data['monthly_trend'] = {
            'months': list(monthly_trend.keys()),
            'values': list(monthly_trend.values())
        }
    
    # Top products chart
    top_products = safe_get(desc, 'top_products', {})
    if top_products:
        products = list(top_products.keys())[:8]
        revenues = [top_products[p].get('total_revenue', 0) for p in products]
        charts_data['top_products'] = {
            'products': products,
            'revenues': revenues
        }
    
    # Category pie chart
    category_perf = safe_get(desc, 'category_performance', {})
    if category_perf:
        categories = list(category_perf.keys())
        amounts = [category_perf[cat].get('amount', 0) for cat in categories]
        charts_data['categories'] = {
            'names': categories,
            'values': amounts
        }
    
    # Weekly pattern
    if data is not None and 'weekday' in data.columns and 'amount' in data.columns:
        try:
            weekly_data = data.groupby('weekday')['amount'].mean().reindex([
                'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
            ])
            charts_data['weekly_pattern'] = {
                'days': weekly_data.index.tolist(),
                'amounts': weekly_data.values.tolist()
            }
        except Exception as e:
            print(f"Weekly pattern error: {e}")
    
    return jsonify(charts_data)

@app.route('/get_recommendations')
def get_recommendations():
    """Get recommendations data"""
    analysis_data = get_analysis_data()
    if not analysis_data:
        return jsonify({'error': 'No analysis data available'})
    
    results = safe_get(analysis_data, 'analysis_results')
    prescriptive = safe_get(results, 'prescriptive', {})
    
    if not prescriptive:
        return jsonify({'error': 'Prescriptive analytics not available'})
    
    recommendations = safe_get(prescriptive, 'recommendations', [])
    priority_summary = safe_get(prescriptive, 'priority_summary', {})
    
    return jsonify({
        'recommendations': recommendations,
        'priority_summary': priority_summary
    })

@app.route('/chat_with_inventra_ai', methods=['POST'])
def chat_with_inventra_ai():
    """Handle Inventra AI Gene chatbot queries"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        print(f"🤖 Inventra AI Gene received: {question}")
        
        analysis_data = get_analysis_data()
        if not analysis_data:
            return jsonify({'error': 'No analysis data available'})
        
        results = safe_get(analysis_data, 'analysis_results')
        if not results:
            return jsonify({'error': 'Analysis results not available'})
        
        # Prepare context
        context = prepare_inventra_context(results)
        
        # Create prompt
        prompt = f"""
You are Inventra AI Gene, a professional business analytics assistant powered by Google Gemini.

BUSINESS DATA:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer based only on the provided business data
2. Provide specific numbers and insights
3. Format currency in Indian Rupees (₹)
4. Be professional and concise
5. If data is not available, clearly state so
6. Sign as "- Inventra AI Gene 🤖"

Provide a professional response:
        """
        
        print("🚀 Calling Google Gemini API...")
        response = inventra_model.generate_content(prompt)
        answer = response.text
        
        print(f"✅ Inventra AI Gene responded successfully")
        
        return jsonify({
            'success': True,
            'answer': answer
        })
    
    except Exception as e:
        print(f"❌ Inventra AI Gene error: {e}")
        return jsonify({
            'success': False,
            'error': f'Inventra AI Gene error: {str(e)}'
        })

if __name__ == '__main__':
    print("🚀 Starting Professional Hybrid Analytics with Inventra AI Gene...")
    app.run(debug=True, host='0.0.0.0', port=5001)
