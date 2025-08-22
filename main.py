from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import mysql.connector
import os
import csv
import io
import json
from flask_mail import Mail, Message
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Load environment variables
def load_env_config():
    env_path = '.env'
    config = {}
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    # Set defaults
    config.setdefault('DB_USER', 'root')
    config.setdefault('DB_PASSWORD', 'root')
    config.setdefault('DB_HOST', 'localhost')
    config.setdefault('DB_NAME', 'inventory_ai')
    config.setdefault('MAIL_SERVER', 'smtp.gmail.com')
    config.setdefault('MAIL_PORT', '587')
    config.setdefault('MAIL_USERNAME', '')
    config.setdefault('MAIL_PASSWORD', '')
    config.setdefault('MAIL_USE_TLS', 'True')
    config.setdefault('MAIL_USE_SSL', 'False')
    config.setdefault('ADMIN_EMAIL', 'admin@example.com')
    config.setdefault('COMPANY_NAME', 'Your Company')
    
    return config

env_config = load_env_config()

# Flask-Mail configuration
app.config['MAIL_SERVER'] = env_config['MAIL_SERVER']
app.config['MAIL_PORT'] = int(env_config['MAIL_PORT'])
app.config['MAIL_USERNAME'] = env_config['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = env_config['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = env_config['MAIL_USE_TLS'].lower() == 'true'
app.config['MAIL_USE_SSL'] = env_config['MAIL_USE_SSL'].lower() == 'true'
app.config['MAIL_DEFAULT_SENDER'] = env_config.get('MAIL_DEFAULT_SENDER', env_config['MAIL_USERNAME'])

mail = Mail(app)

# AI Engine Configuration
AI_CONFIG = {
    'LOW_STOCK_THRESHOLD': 10,
    'NON_MOVABLE_DAYS': 90,
    'EXPIRY_WARNING_DAYS': 30,
    'REORDER_MULTIPLIER': 1.5
}

# Database configuration
DB_CONFIG = {
    'host': env_config['DB_HOST'],
    'user': env_config['DB_USER'],
    'password': env_config['DB_PASSWORD'],
    'database': env_config['DB_NAME']
}

# Available tables for export
AVAILABLE_TABLES = ["ai_recommendations", "categories", "order_history", "products", "sales_history", "suppliers"]

COMPANY_INFO = {
    'ADMIN_EMAIL': env_config['ADMIN_EMAIL'],
    'COMPANY_NAME': env_config['COMPANY_NAME']
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    """Initialize database with comprehensive schema"""
    conn = get_db_connection()
    c = conn.cursor()

    # Suppliers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            supplier_id VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            email VARCHAR(255),
            address TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Categories table
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Products table with AI fields
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            category_id INT,
            supplier_id INT,
            price DOUBLE,
            current_stock INT DEFAULT 0,
            minimum_stock INT DEFAULT 5,
            expiry_date DATE,
            date_added DATE NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            total_sold INT DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    ''')

    # Sales history table
        # Sales history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT,
            product_name VARCHAR(255),
            quantity_sold INT,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            amount DOUBLE,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')



    # AI Recommendations table
    c.execute('''
        CREATE TABLE IF NOT EXISTS ai_recommendations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            type VARCHAR(50) NOT NULL,
            product_id INT,
            message TEXT NOT NULL,
            priority INT DEFAULT 1,
            status VARCHAR(50) DEFAULT 'active',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Order history table
    c.execute("""
        CREATE TABLE IF NOT EXISTS order_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            supplier_name VARCHAR(255),
            supplier_email VARCHAR(255),
            products_details TEXT,
            total_products INT,
            custom_message TEXT,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'sent'
        )
    """)

    conn.commit()
    c.close()
    conn.close()
    print("✅ Database initialized successfully")

# AI Analytics Engine
class InventoryAI:
    def __init__(self):
        self.conn = get_db_connection()
        self.conn.autocommit = False

    def analyze_inventory(self):
        recommendations = []

        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("DELETE FROM ai_recommendations WHERE status = 'active'")
        self.conn.commit()

        recommendations.extend(self._analyze_low_stock())
        recommendations.extend(self._analyze_non_movable_stock())
        recommendations.extend(self._analyze_expiry_warnings())
        recommendations.extend(self._analyze_reorder_suggestions())

        for rec in recommendations:
            cursor.execute("""
                INSERT INTO ai_recommendations (type, product_id, message, priority)
                VALUES (%s, %s, %s, %s)
            """, (rec['type'], rec['product_id'], rec['message'], rec['priority']))

        self.conn.commit()
        cursor.close()
        self.conn.close()
        return recommendations

    def _analyze_low_stock(self):
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            WHERE p.current_stock <= p.minimum_stock AND p.current_stock > 0
        """)
        results = cursor.fetchall()
        cursor.close()

        recommendations = []
        for product in results:
            recommendations.append({
                'type': 'LOW_STOCK',
                'product_id': product['id'],
                'message': f"⚠️ {product['name']} is running low (Stock: {product['current_stock']}, Min: {product['minimum_stock']})",
                'priority': 3
            })
        return recommendations

    def _analyze_non_movable_stock(self):
        ninety_days_ago = (datetime.now() - timedelta(days=AI_CONFIG['NON_MOVABLE_DAYS'])).date()

        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.current_stock > 0 
            AND p.date_added <= %s
            AND p.total_sold = 0
        """, (ninety_days_ago,))
        results = cursor.fetchall()
        cursor.close()

        recommendations = []
        for product in results:
            date_added = product['date_added']
            if date_added:
                days_in_stock = (datetime.now().date() - date_added).days
                if days_in_stock >= AI_CONFIG['NON_MOVABLE_DAYS']:
                    recommendations.append({
                        'type': 'NON_MOVABLE',
                        'product_id': product['id'],
                        'message': f"📦 {product['name']} hasn't moved for {days_in_stock} days since {product['date_added']}. Consider promotion.",
                        'priority': 2
                    })
        return recommendations

    def _analyze_expiry_warnings(self):
        warning_date = datetime.now() + timedelta(days=AI_CONFIG['EXPIRY_WARNING_DAYS'])

        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            WHERE p.expiry_date IS NOT NULL 
            AND p.expiry_date <= %s 
            AND p.current_stock > 0
        """, (warning_date.date(),))
        results = cursor.fetchall()
        cursor.close()

        recommendations = []
        for product in results:
            expiry_date = product['expiry_date']
            days_to_expiry = (expiry_date - datetime.now().date()).days

            if days_to_expiry <= 0:
                priority = 5
                message = f"🚨 {product['name']} has EXPIRED! Remove from inventory immediately."
            elif days_to_expiry <= 7:
                priority = 4
                message = f"⏰ {product['name']} expires in {days_to_expiry} days. Urgent clearance needed!"
            else:
                priority = 3
                message = f"📅 {product['name']} expires in {days_to_expiry} days. Plan clearance sale."

            recommendations.append({
                'type': 'EXPIRY_WARNING',
                'product_id': product['id'],
                'message': message,
                'priority': priority
            })

        return recommendations

    def _analyze_reorder_suggestions(self):
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.current_stock <= p.minimum_stock
            AND p.current_stock >= 0
        """)
        results = cursor.fetchall()
        cursor.close()

        recommendations = []
        for product in results:
            recommended_order = max(product['minimum_stock'] * 2, 20)
            recommendations.append({
                'type': 'REORDER_SUGGESTION',
                'product_id': product['id'],
                'message': f"📈 {product['name']} needs restocking. Recommend ordering {recommended_order} units.",
                'priority': 2
            })

        return recommendations

# =========================
# HTML PAGE ROUTES
# =========================

@app.route('/')
def home():
    return send_from_directory('.', 'loginpage.html')

@app.route('/loginpage.html')
def loginpage():
    return send_from_directory('.', 'loginpage.html')

@app.route('/dashboard.html')
def dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.route('/category.html')
def categories():
    return send_from_directory('.', 'category.html')

@app.route('/supplier.html')
def suppliers():
    return send_from_directory('.', 'supplier.html')

@app.route('/addproducts.html')
def add_products():
    return send_from_directory('.', 'addproducts.html')

@app.route('/automation.html')
def automation():
    return send_from_directory('.', 'automation.html')

@app.route('/aianalytics.html')
def ai_analytics():
    return send_from_directory('.', 'aianalytics.html')

@app.route('/reports.html')
def reports():
    return send_from_directory('.', 'reports.html')


@app.route('/billing.html')
def billing():
    return send_from_directory('./billing', 'billing.html')


# =========================
# DASHBOARD API ROUTES
# =========================

@app.route('/api/stats')
def get_stats():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM suppliers")
        suppliers_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM categories")
        categories_count = c.fetchone()
        
        c.execute("SELECT COUNT(*) FROM products")
        products_count = c.fetchone()

        c.execute("SELECT SUM(current_stock) FROM products")
        total_stock = c.fetchone()
        if total_stock is None:
            total_stock = 0
        
        c.execute("SELECT COUNT(*) FROM products WHERE current_stock <= minimum_stock")
        low_stock_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM ai_recommendations WHERE status = 'active'")
        active_recommendations = c.fetchone()[0]

        c.close()
        conn.close()
        
        return jsonify({
            'suppliers': suppliers_count,
            'categories': categories_count,
            'products': products_count,
            'total_stock': total_stock,
            'low_stock_alerts': low_stock_count,
            'ai_recommendations': active_recommendations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/billing/<path:filename>')
def billing_files(filename):
    return send_from_directory('./billing', filename)



@app.route('/api/ai/analyze')
def run_ai_analysis():
    try:
        ai_engine = InventoryAI()
        recommendations = ai_engine.analyze_inventory()
        return jsonify({
            'success': True,
            'recommendations_generated': len(recommendations),
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/recommendations')
def get_recommendations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.*, p.name as product_name, p.current_stock, p.minimum_stock
            FROM ai_recommendations r
            LEFT JOIN products p ON r.product_id = p.id
            WHERE r.status = 'active'
            ORDER BY r.priority DESC, r.created_date DESC
        """)
        recommendations = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =========================
# SUPPLIERS API
# =========================

@app.route('/api/suppliers', methods=['GET', 'POST'])
def suppliers_api():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT * FROM suppliers ORDER BY name")
        suppliers = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(suppliers)

    elif request.method == 'POST':
        try:
            data = request.json
            cursor.execute("""
                INSERT INTO suppliers (supplier_id, name, phone, email, address)
                VALUES (%s, %s, %s, %s, %s)
            """, (data['supplier_id'], data['name'], data.get('phone'), data.get('email'), data.get('address')))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

@app.route('/api/suppliers/<int:supplier_id>', methods=['GET', 'PUT', 'DELETE'])
def supplier_detail(supplier_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT * FROM suppliers WHERE id = %s", (supplier_id,))
        supplier = cursor.fetchone()
        cursor.close()
        conn.close()
        if supplier:
            return jsonify(supplier)
        return jsonify({'error': 'Supplier not found'}), 404

    elif request.method == 'PUT':
        try:
            data = request.json
            cursor.execute("""
                UPDATE suppliers SET name=%s, phone=%s, email=%s, address=%s WHERE id=%s
            """, (data['name'], data.get('phone'), data.get('email'), data.get('address'), supplier_id))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            cursor.execute("DELETE FROM suppliers WHERE id=%s", (supplier_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

# =========================
# CATEGORIES API
# =========================

@app.route('/api/categories', methods=['GET', 'POST'])
def categories_api():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT * FROM categories ORDER BY name")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(categories)

    elif request.method == 'POST':
        try:
            data = request.json
            cursor.execute("""
                INSERT INTO categories (name, description)
                VALUES (%s, %s)
            """, (data['name'], data.get('description')))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

@app.route('/api/categories/<int:category_id>', methods=['GET', 'PUT', 'DELETE'])
def category_detail(category_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
        category = cursor.fetchone()
        cursor.close()
        conn.close()
        if category:
            return jsonify(category)
        return jsonify({'error': 'Category not found'}), 404

    elif request.method == 'PUT':
        try:
            data = request.json
            cursor.execute("""
                UPDATE categories SET name=%s, description=%s WHERE id=%s
            """, (data['name'], data.get('description'), category_id))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            cursor.execute("DELETE FROM categories WHERE id=%s", (category_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

# =========================
# PRODUCTS API
# =========================

@app.route('/api/products', methods=['GET', 'POST'])
def products_api():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        try:
            cursor.execute("""
                SELECT p.*, c.name as category_name, s.name as supplier_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                ORDER BY p.date_added DESC, p.name
            """)
            products = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify(products)
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        try:
            data = request.json
            # Validate required fields
            required_fields = ['product_id', 'name', 'category_id', 'supplier_id', 'price', 'current_stock', 'minimum_stock', 'date_added']
            for field in required_fields:
                if field not in data or data[field] is None or data[field] == '':
                    cursor.close()
                    conn.close()
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            cursor.execute("""
                INSERT INTO products (
                    product_id, name, category_id, supplier_id, price,
                    current_stock, minimum_stock, expiry_date, date_added
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['product_id'],
                data['name'],
                int(data['category_id']),
                int(data['supplier_id']),
                float(data['price']),
                int(data['current_stock']),
                int(data['minimum_stock']),
                data.get('expiry_date'),
                data['date_added']
            ))
            conn.commit()

            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Product added successfully'})

        except Exception as e:
            cursor.close()
            conn.close()
            print(f"❌ Error adding product: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/products/<int:product_id>', methods=['GET', 'PUT', 'DELETE'])
def product_detail(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        try:
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            cursor.close()
            conn.close()
            if product:
                return jsonify(product)
            return jsonify({'error': 'Product not found'}), 404
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

    elif request.method == 'PUT':
        try:
            data = request.json
            cursor.execute("""
                UPDATE products SET 
                    name=%s, category_id=%s, supplier_id=%s, price=%s,
                    current_stock=%s, minimum_stock=%s, expiry_date=%s,
                    last_updated=CURRENT_TIMESTAMP
                WHERE id=%s
            """, (
                data['name'],
                int(data['category_id']),
                int(data['supplier_id']),
                float(data['price']),
                int(data['current_stock']),
                int(data['minimum_stock']),
                data.get('expiry_date'),
                product_id
            ))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            cursor.execute("DELETE FROM products WHERE id=%s", (product_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

# =========================
# AUTOMATION ROUTES (Email & Export)
# =========================

@app.route('/api/low-stock')
def get_low_stock():
    """Get low stock products with supplier details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                p.id, p.product_id, p.name as product_name, p.current_stock, p.minimum_stock,
                s.id as supplier_id, s.name as supplier_name, s.email as supplier_email,
                c.name as category_name
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.current_stock <= p.minimum_stock 
            AND s.email IS NOT NULL AND s.email != ''
            ORDER BY p.current_stock ASC
        """)
        
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Group by supplier
        suppliers = {}
        for product in products:
            supplier_id = product['supplier_id']
            if supplier_id not in suppliers:
                suppliers[supplier_id] = {
                    'supplier_id': supplier_id,
                    'supplier_name': product['supplier_name'],
                    'supplier_email': product['supplier_email'],
                    'custom_message': '',
                    'products': []
                }
            
            required_qty = max(product['minimum_stock'] * 2, 20)
            product['required_quantity'] = required_qty
            suppliers[supplier_id]['products'].append(product)
        
        return jsonify(list(suppliers.values()))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-emails', methods=['POST'])
def send_emails():
    """Send simple emails to suppliers"""
    try:
        data = request.json
        selected_suppliers = data.get('suppliers', [])
        
        if not selected_suppliers:
            return jsonify({'success': False, 'message': 'No suppliers selected'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        emails_sent = 0
        emails_failed = 0
        
        for supplier_data in selected_suppliers:
            try:
                if send_supplier_email(supplier_data):
                    cursor.execute("""
                        INSERT INTO order_history 
                        (supplier_name, supplier_email, products_details, total_products, custom_message)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        supplier_data['supplier_name'],
                        supplier_data['supplier_email'],
                        json.dumps(supplier_data['products']),
                        len(supplier_data['products']),
                        supplier_data.get('custom_message', '')
                    ))
                    emails_sent += 1
                else:
                    emails_failed += 1
                    
            except Exception as e:
                emails_failed += 1
                print(f"Error: {str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'emails_sent': emails_sent,
            'emails_failed': emails_failed,
            'message': f'Sent {emails_sent} emails, {emails_failed} failed'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def send_supplier_email(supplier_data):
    """Send simple email to supplier"""
    try:
        # Build products table
        products_html = ""
        total_items = 0
        for product in supplier_data['products']:
            qty = product.get('required_quantity', 20)
            total_items += qty
            products_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{product['product_id']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{product['product_name']}</td>
                <td style="padding: 8px; border: 1px solid #ddd; color: red; font-weight: bold;">{product['current_stock']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{product['minimum_stock']}</td>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; color: blue;">{qty}</td>
            </tr>
            """
        
        # Custom message
        custom_message_html = ""
        if supplier_data.get('custom_message', '').strip():
            custom_message_html = f"""
            <div style="background: #e7f3ff; padding: 15px; margin: 20px 0; border-left: 4px solid #2196f3;">
                <h3 style="margin: 0 0 10px 0; color: #1976d2;">📝 Special Instructions:</h3>
                <p style="margin: 0;">{supplier_data['custom_message']}</p>
            </div>
            """
        
        email_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 800px; margin: 0 auto; background: white;">
                <div style="background: #4CAF50; color: white; padding: 20px; text-align: center;">
                    <h1>Stock Reorder Request</h1>
                    <p>{COMPANY_INFO['COMPANY_NAME']}</p>
                </div>
                <div style="padding: 20px;">
                    <h2>Dear {supplier_data['supplier_name']},</h2>
                    <p>We need to reorder the following products:</p>
                    
                    <ul>
                        <li><strong>{len(supplier_data['products'])} products</strong> need restocking</li>
                        <li><strong>{total_items} total units</strong> requested</li>
                        <li><strong>Order date:</strong> {datetime.now().strftime('%B %d, %Y')}</li>
                    </ul>
                    
                    {custom_message_html}
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr style="background: #f2f2f2;">
                            <th style="padding: 10px; border: 1px solid #ddd;">Product ID</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Product Name</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Current Stock</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Minimum Stock</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Required Quantity</th>
                        </tr>
                        {products_html}
                    </table>
                    
                    <p>Please confirm receipt and provide delivery timeline.</p>
                    <p><strong>Contact:</strong> {COMPANY_INFO['ADMIN_EMAIL']}</p>
                </div>
                <div style="background: #333; color: white; padding: 20px; text-align: center;">
                    <p>Thank you for your business!</p>
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject=f"Stock Reorder Request - {len(supplier_data['products'])} Items",
            recipients=[supplier_data['supplier_email']],
            html=email_content,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False

@app.route('/api/order-history')
def get_order_history():
    """Get order history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM order_history 
            ORDER BY order_date DESC 
            LIMIT 50
        """)
        
        history = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(history)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =========================
# CSV EXPORT FEATURES
# =========================

@app.route('/api/tables')
def get_tables():
    """Get list of available tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        table_info = []
        for table in AVAILABLE_TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_info.append({
                    'name': table,
                    'display_name': table.replace('_', ' ').title(),
                    'row_count': count
                })
            except Exception as e:
                table_info.append({
                    'name': table,
                    'display_name': table.replace('_', ' ').title(),
                    'row_count': 0,
                    'error': str(e)
                })
        
        cursor.close()
        conn.close()
        return jsonify({'tables': table_info})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/table-data')
def get_table_data():
    """Get data from specific table"""
    table = request.args.get('table')
    
    if table not in AVAILABLE_TABLES:
        return jsonify({'error': 'Invalid table name'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(f"SELECT * FROM {table} LIMIT 100")
        rows = cursor.fetchall()
        
        # Get column names
        if rows:
            columns = list(rows[0].keys())
        else:
            cursor.execute(f"DESCRIBE {table}")
            columns = [col for col in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'columns': columns,
            'rows': rows
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download')
def download_table():
    """Download table data as CSV"""
    table = request.args.get('table')
    
    if table not in AVAILABLE_TABLES:
        return jsonify({'error': 'Invalid table name'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        headers = [desc[0] for desc in cursor.description]
        
        cursor.close()
        conn.close()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        
        for row in rows:
            formatted_row = []
            for item in row:
                if isinstance(item, datetime):
                    formatted_row.append(item.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    formatted_row.append(str(item) if item is not None else '')
            writer.writerow(formatted_row)
        
        output.seek(0)
        filename = f"{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =========================
# UTILITY ROUTES
# =========================

@app.route('/health')
def health():
    return jsonify({'status': 'running', 'service': 'Combined Inventory Management System'})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    init_db()

    if not os.path.exists('./images'):
        os.makedirs('./images')
        print("✅ Created images directory")

    print("🤖 Combined Inventor AI Genie System")
    print("=" * 60)
    print("🏠 Dashboard: http://localhost:5000")
    print("🔧 Automation: http://localhost:5000/automation.html")
    print("📝 Add Products: http://localhost:5000/addproducts.html")
    print("📊 AI Analytics: http://localhost:5000/aianalytics.html")
    print("📧 Email Service: Flask-Mail Enabled")
    print("📊 Export Feature: CSV downloads")
    print("💾 Database: MySQL (inventory_ai)")
    print("🤖 AI Engine: Active with Date Tracking")
    print("=" * 60)

    app.run(debug=True, port=5000)
