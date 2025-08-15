from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import mysql.connector
from datetime import datetime, timedelta
import json
import os
import time

# Configure Flask to work with your folder structure
app = Flask(__name__, 
           template_folder='billing/templates',  # Point to your billing templates
           static_folder='billing/static')       # Point to your billing static files

app.secret_key = 'your-unified-secret-key-here'

# MySQL connection config
MYSQL_CONFIG = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'inventory_ai'
}

# AI Engine Configuration
AI_CONFIG = {
    'LOW_STOCK_THRESHOLD': 10,
    'NON_MOVABLE_DAYS': 90,
    'EXPIRY_WARNING_DAYS': 30,
    'REORDER_MULTIPLIER': 1.5
}

def get_db_connection():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    return conn

def init_db():
    """Initialize unified database with comprehensive schema for both admin and billing"""
    conn = get_db_connection()
    c = conn.cursor()

    # Suppliers table (Admin)
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

    # Categories table (Admin)
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Unified Products table (Admin + Billing compatible)
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            category_id INT,
            supplier_id INT,
            price DECIMAL(15,2) NOT NULL,
            current_stock INT DEFAULT 0,
            minimum_stock INT DEFAULT 5,
            expiry_date DATE,
            date_added DATE NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            total_sold INT DEFAULT 0,
            status VARCHAR(20) DEFAULT 'Active',
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    ''')

    # Unified Customers table (Billing + Admin analytics)
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            contact VARCHAR(50) UNIQUE NOT NULL,
            loyalty_points INT DEFAULT 0,
            total_purchases DECIMAL(15,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Unified Sales table (Billing + Admin reporting)
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INT AUTO_INCREMENT PRIMARY KEY,
            invoice_no VARCHAR(255) UNIQUE NOT NULL,
            customer_name VARCHAR(255) NOT NULL,
            customer_contact VARCHAR(50) NOT NULL,
            customer_email VARCHAR(255),
            bill_amount DECIMAL(15,2) NOT NULL,
            discount_amount DECIMAL(15,2) DEFAULT 0.00,
            coupon_discount DECIMAL(15,2) DEFAULT 0.00,
            points_used INT DEFAULT 0,
            net_amount DECIMAL(15,2) NOT NULL,
            points_earned INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            items_json TEXT NOT NULL
        )
    ''')

    # Coupons table (Admin managed, Billing used)
    c.execute('''
        CREATE TABLE IF NOT EXISTS coupons (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(100) UNIQUE NOT NULL,
            discount_type VARCHAR(20) NOT NULL,
            discount_value DECIMAL(10,2) NOT NULL,
            min_amount DECIMAL(15,2) DEFAULT 0.00,
            max_discount DECIMAL(15,2) DEFAULT 0.00,
            usage_limit INT DEFAULT 1,
            used_count INT DEFAULT 0,
            valid_from DATE DEFAULT (CURDATE()),
            valid_until DATE NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')

    # Sales history table (Admin analytics)
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT,
            quantity_sold INT,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            amount DECIMAL(15,2),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # AI Recommendations table (Admin)
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

    # Insert sample data
    insert_sample_data(c, conn)

    conn.commit()
    c.close()
    conn.close()
    print("✅ Unified database initialized successfully")

def insert_sample_data(cursor, conn):
    """Insert sample data for both admin and billing"""
    try:
        # Sample categories
        cursor.execute("INSERT IGNORE INTO categories (name, description) VALUES ('Electronics', 'Electronic items')")
        cursor.execute("INSERT IGNORE INTO categories (name, description) VALUES ('Mobile', 'Mobile phones')")
        cursor.execute("INSERT IGNORE INTO categories (name, description) VALUES ('Computers', 'Computer accessories')")
        
        # Sample suppliers
        cursor.execute("INSERT IGNORE INTO suppliers (supplier_id, name, phone, email, address) VALUES ('SUP001', 'Tech Supplies Co.', '9876543210', 'tech@supplier.com', '123 Tech Street')")
        
        # Sample products (compatible with both systems)
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ('PROD001', 'Laptop Dell XPS', 3, 1, 85000.00, 10, 5, None, '2024-01-01'),
                ('PROD002', 'iPhone 14 Pro', 2, 1, 125000.00, 5, 2, None, '2024-01-01'),
                ('PROD003', 'Samsung Galaxy S23', 2, 1, 95000.00, 8, 3, None, '2024-01-01'),
                ('PROD004', 'MacBook Air M2', 3, 1, 115000.00, 3, 1, None, '2024-01-01'),
                ('PROD005', 'Sony Headphones', 1, 1, 25000.00, 15, 5, None, '2024-01-01'),
                ('PROD006', 'Logitech Mouse', 3, 1, 2500.00, 20, 10, None, '2024-01-01')
            ]
            for product in sample_products:
                cursor.execute("""
                    INSERT INTO products (product_id, name, category_id, supplier_id, price, 
                    current_stock, minimum_stock, expiry_date, date_added) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, product)
        
        # Sample coupons
        cursor.execute("SELECT COUNT(*) FROM coupons")
        if cursor.fetchone()[0] == 0:
            future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            sample_coupons = [
                ('WELCOME10', 'percentage', 10.00, 1000.00, 5000.00, 50, 0, future_date),
                ('SAVE500', 'fixed', 500.00, 2000.00, 500.00, 20, 0, future_date)
            ]
            for coupon in sample_coupons:
                cursor.execute("""
                    INSERT INTO coupons (code, discount_type, discount_value, min_amount, 
                    max_discount, usage_limit, used_count, valid_until) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, coupon)
        
        conn.commit()
    except Exception as e:
        print(f"Warning: Error inserting sample data: {e}")

# AI Analytics Engine
class InventoryAI:
    def __init__(self):
        self.conn = get_db_connection()

    def analyze_inventory(self):
        recommendations = []
        cursor = self.conn.cursor(dictionary=True)
        
        cursor.execute("DELETE FROM ai_recommendations WHERE status = 'active'")
        self.conn.commit()

        recommendations.extend(self._analyze_low_stock())
        recommendations.extend(self._analyze_non_movable_stock())
        recommendations.extend(self._analyze_expiry_warnings())

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
            WHERE p.current_stock <= p.minimum_stock AND p.current_stock > 0 AND p.status = 'Active'
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
            AND p.status = 'Active'
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
                        'message': f"📦 {product['name']} hasn't moved for {days_in_stock} days. Consider promotion.",
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
            AND p.status = 'Active'
        """, (warning_date.date(),))
        results = cursor.fetchall()
        cursor.close()

        recommendations = []
        for product in results:
            expiry_date = product['expiry_date']
            days_to_expiry = (expiry_date - datetime.now().date()).days

            if days_to_expiry <= 0:
                priority = 5
                message = f"🚨 {product['name']} has EXPIRED! Remove immediately."
            elif days_to_expiry <= 7:
                priority = 4
                message = f"⏰ {product['name']} expires in {days_to_expiry} days. Urgent clearance!"
            else:
                priority = 3
                message = f"📅 {product['name']} expires in {days_to_expiry} days. Plan clearance."

            recommendations.append({
                'type': 'EXPIRY_WARNING',
                'product_id': product['id'],
                'message': message,
                'priority': priority
            })

        return recommendations

# ================= ROUTE HANDLERS =================

# ============= LOGIN & MAIN ROUTES =============
@app.route('/')
def home():
    # Check if user is already logged in
    if 'userRole' in session:
        if session['userRole'] == 'administrator':
            return redirect('/admin')
        elif session['userRole'] == 'billing':
            return redirect('/billing')
    
    # If not logged in, show login page
    return send_from_directory('.', 'login.html')

@app.route('/login')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ============= ADMIN PANEL ROUTES =============
@app.route('/admin')
def admin_home():
    # Optional: Add session validation
    # if 'userRole' not in session or session['userRole'] != 'administrator':
    #     return redirect(url_for('login_page'))
    
    # Look for dashboard file in admin folder
    try:
        return send_from_directory('admin', 'dashboard.html')
    except:
        return send_from_directory('admin', 'index.html')

# Serve all admin files from admin folder
@app.route('/admin/<path:filename>')
def admin_files(filename):
    return send_from_directory('admin', filename)

@app.route('/dashboard.html')
def dashboard():
    return send_from_directory('admin', 'dashboard.html')

@app.route('/category.html')
def categories():
    return send_from_directory('admin', 'category.html')

@app.route('/supplier.html')
def suppliers():
    return send_from_directory('admin', 'supplier.html')

@app.route('/addproducts.html')
def add_products():
    return send_from_directory('admin', 'addproducts.html')

@app.route('/aianalytics.html')
def ai_analytics():
    return send_from_directory('admin', 'aianalytics.html')

@app.route('/billing.html')
def billing():
    return send_from_directory('admin', 'billing.html')

# ============= BILLING PANEL ROUTES =============
@app.route('/billing')
@app.route('/billing/')
def billing_home():
    # Optional: Add session validation
    # if 'userRole' not in session or session['userRole'] != 'billing':
    #     return redirect(url_for('login_page'))
    
    # This will render billing/templates/index.html
    return render_template('index.html')

@app.route('/pos')
def pos():
    return render_template('pos.html')

@app.route('/bill-history')
def bill_history():
    return render_template('bill_history.html')

@app.route('/coupon-manager')
def coupon_manager():
    return render_template('coupon_manager.html')

# ============= AUTHENTICATION API =============
@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    try:
        data = request.json
        section = data.get('section', '').lower()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Demo users (replace with database lookup in production)
        users = {
            'administrator': {'username': 'admin', 'password': 'admin123'},
            'billing': {'username': 'billing', 'password': 'billing123'}
        }
        
        if section in users:
            user = users[section]
            if username == user['username'] and password == user['password']:
                session['userRole'] = section
                session['username'] = username
                
                redirect_url = '/admin' if section == 'administrator' else '/billing'
                
                return jsonify({
                    'success': True,
                    'message': f'Welcome! Redirecting to {section} panel...',
                    'redirect': redirect_url
                })
        
        return jsonify({
            'success': False,
            'message': f'Incorrect username or password for {section}.'
        }), 401
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Authentication failed. Please try again.'
        }), 500

# ============= UNIFIED API ROUTES =============

# Stats API (used by both admin and billing)
@app.route('/api/stats')
def get_stats():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Admin stats
        c.execute("SELECT COUNT(*) FROM suppliers")
        suppliers_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM categories")
        categories_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM products WHERE status = 'Active'")
        products_count = c.fetchone()[0]

        c.execute("SELECT SUM(current_stock) FROM products WHERE status = 'Active'")
        total_stock = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM products WHERE current_stock <= minimum_stock AND status = 'Active'")
        low_stock_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM ai_recommendations WHERE status = 'active'")
        active_recommendations = c.fetchone()[0]

        # Billing stats
        c.execute("SELECT COUNT(*) FROM customers")
        total_customers = c.fetchone()[0]
        
        # Today's sales
        c.execute("SELECT COUNT(*), COALESCE(SUM(net_amount), 0) FROM sales WHERE DATE(created_at) = CURDATE()")
        today_sales_data = c.fetchone()
        today_transactions = today_sales_data[0]
        today_revenue = float(today_sales_data[1])

        c.close()
        conn.close()
        
        return jsonify({
            'suppliers': suppliers_count,
            'categories': categories_count,
            'products': products_count,
            'total_stock': total_stock,
            'low_stock_alerts': low_stock_count,
            'ai_recommendations': active_recommendations,
            'total_customers': total_customers,
            'today_transactions': today_transactions,
            'today_revenue': today_revenue
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# AI Analysis APIs
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

# Unified Products API (works for both admin and billing)
# Unified Products API (works for both admin and billing) - FIXED VERSION
# Unified Products API (works for both admin and billing) - FIXED VERSION
@app.route('/api/products', methods=['GET', 'POST'])
def products_api():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        try:
            # Check if it's for billing (return billing-compatible format)
            billing_mode = request.args.get('billing', 'false').lower() == 'true'
            
            if billing_mode:
                # Return products in billing format with quantity field
                cursor.execute("""
                    SELECT id, name, price, current_stock, status
                    FROM products 
                    WHERE status = 'Active' AND current_stock > 0
                    ORDER BY name
                """)
                products = cursor.fetchall()
                
                # FIX: Properly transform for billing compatibility
                billing_products = []
                for product in products:
                    # THE KEY FIX - ensure proper data conversion
                    current_stock = product.get('current_stock', 0)
                    if current_stock is None:
                        current_stock = 0
                    
                    
                    billing_products.append({
                                'id': product['id'],
                                'name': product['name'],
                                'price': float(product['price']) if product['price'] else 0.0,
                                'quantity': int(current_stock),
                                'current_stock': int(current_stock),
                                'stock': int(current_stock),   # ✅ Added for compatibility
                                'status': product['status']
                            })

                
                cursor.close()
                conn.close()
                return jsonify(billing_products)
            else:
                # Return products in admin format (unchanged)
                cursor.execute("""
                    SELECT p.*, c.name as category_name, s.name as supplier_name
                    FROM products p
                    LEFT JOIN categories c ON p.category_id = c.id
                    LEFT JOIN suppliers s ON p.supplier_id = s.id
                    WHERE p.status = 'Active'
                    ORDER BY p.date_added DESC, p.name
                """)
                products = cursor.fetchall()
                
                # Convert Decimal to float for JSON
                for product in products:
                    if product.get('price'):
                        product['price'] = float(product['price'])
                
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

            # Trigger AI analysis after adding product
            try:
                ai_engine = InventoryAI()
                ai_engine.analyze_inventory()
            except Exception as ai_error:
                print(f"⚠️ AI analysis failed: {ai_error}")

            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Product added successfully'})

        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': f'Database error: {str(e)}'}), 500



# Products search API (for billing)
# Products search API (for billing) - FIXED VERSION
# Products search API (for billing) - FIXED VERSION
@app.route('/api/products/search')
def search_products():
    query = request.args.get('q', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id, name, price, current_stock, status 
        FROM products 
        WHERE name LIKE %s AND status = 'Active' AND current_stock > 0
        ORDER BY name
    """, (f'%{query}%',))
    
    products = cursor.fetchall()
    
    # FIX: Transform for billing compatibility
    billing_products = []
    for product in products:
        # Ensure proper data conversion
        current_stock = product.get('current_stock', 0)
        if current_stock is None:
            current_stock = 0
            
        billing_products.append({
                    'id': product['id'],
                    'name': product['name'],
                    'price': float(product['price']) if product['price'] else 0.0,
                    'quantity': int(current_stock),
                    'current_stock': int(current_stock),
                    'stock': int(current_stock),  # ✅ Added this line
                    'status': product['status']
})

    
    cursor.close()
    conn.close()
    return jsonify(billing_products)


# Customer APIs
@app.route('/api/customers/<contact>')
def get_customer(contact):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM customers WHERE contact = %s', (contact,))
    customer = cursor.fetchone()
    
    if customer and customer.get('total_purchases'):
        customer['total_purchases'] = float(customer['total_purchases'])
    
    cursor.close()
    conn.close()
    
    if customer:
        return jsonify(customer)
    return jsonify({'error': 'Customer not found'}), 404

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO customers (name, email, contact) VALUES (%s, %s, %s)',
                      (data['name'], data.get('email'), data['contact']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Customer added successfully'})
    except mysql.connector.IntegrityError:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Customer with this contact already exists'}), 400

# Coupon APIs
@app.route('/api/coupons/validate', methods=['POST'])
def validate_coupon():
    data = request.json
    coupon_code = data.get('code', '').upper()
    bill_amount = data.get('amount', 0)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('''SELECT * FROM coupons WHERE code = %s AND is_active = 1 AND 
                     used_count < usage_limit AND CURDATE() BETWEEN valid_from AND valid_until''', 
                  (coupon_code,))
    coupon = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not coupon:
        return jsonify({'error': 'Invalid or expired coupon code'}), 400
    
    if bill_amount < coupon['min_amount']:
        return jsonify({'error': f'Minimum bill amount required: ₹{coupon["min_amount"]}'}), 400
    
    if coupon['discount_type'] == 'percentage':
        discount = (bill_amount * float(coupon['discount_value'])) / 100
        if coupon['max_discount'] > 0:
            discount = min(discount, float(coupon['max_discount']))
    else:
        discount = float(coupon['discount_value'])
    
    return jsonify({
        'discount': discount,
        'coupon_id': coupon['id'],
        'message': f'Coupon applied! Discount: ₹{discount:.2f}'
    })

@app.route('/api/coupons', methods=['GET', 'POST'])
def coupons_api():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM coupons ORDER BY id DESC')
        coupons = cursor.fetchall()
        
        # Convert Decimal to float
        for coupon in coupons:
            for field in ['discount_value', 'min_amount', 'max_discount']:
                if coupon.get(field):
                    coupon[field] = float(coupon[field])
        
        cursor.close()
        conn.close()
        return jsonify(coupons)
    
    elif request.method == 'POST':
        try:
            data = request.json
            valid_until = (datetime.now() + timedelta(days=int(data['valid_days']))).strftime("%Y-%m-%d")
            cursor.execute('''INSERT INTO coupons (code, discount_type, discount_value, min_amount, 
                             max_discount, usage_limit, valid_until) VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                          (data['code'].upper(), data['discount_type'], float(data['discount_value']),
                           float(data['min_amount']), float(data['max_discount']), 
                           int(data['usage_limit']), valid_until))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Coupon added successfully'})
        except mysql.connector.IntegrityError:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Coupon code already exists'}), 400

# Sales API
@app.route('/api/sales', methods=['GET', 'POST'])
def sales_api():
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM sales ORDER BY created_at DESC LIMIT 100')
        sales = cursor.fetchall()
        
        # Convert Decimal to float
        for sale in sales:
            for field in ['bill_amount', 'discount_amount', 'coupon_discount', 'net_amount']:
                if sale.get(field):
                    sale[field] = float(sale[field])
        
        cursor.close()
        conn.close()
        return jsonify(sales)
    
    elif request.method == 'POST':
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate invoice number
        invoice_no = str(int(time.time()))
        
        # Calculate points
        points_used = data.get('points_used', 0)
        points_earned = max(0, int(float(data['net_amount']) / 100))
        
        # Insert sale record
        cursor.execute('''INSERT INTO sales (invoice_no, customer_name, customer_contact, customer_email,
                         bill_amount, discount_amount, coupon_discount, points_used, net_amount, 
                         points_earned, items_json) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                      (invoice_no, data['customer_name'], data['customer_contact'], data.get('customer_email', ''),
                       float(data['bill_amount']), float(data['discount_amount']), float(data.get('coupon_discount', 0)),
                       points_used, float(data['net_amount']), points_earned, json.dumps(data['items'])))
        
        # Update customer loyalty points
        cursor.execute('''INSERT INTO customers (name, email, contact, loyalty_points, total_purchases)
                         VALUES (%s, %s, %s, %s, %s)
                         ON DUPLICATE KEY UPDATE
                             loyalty_points = loyalty_points - %s + %s,
                             total_purchases = total_purchases + %s''',
                      (data['customer_name'], data.get('customer_email', ''), data['customer_contact'],
                       points_earned, float(data['net_amount']),
                       points_used, points_earned, float(data['net_amount'])))
        
        # Update product quantities and record sales history
        for item in data['items']:
            # Update product stock
            cursor.execute('UPDATE products SET current_stock = current_stock - %s, total_sold = total_sold + %s WHERE id = %s',
                          (item['quantity'], item['quantity'], item['id']))
            
            # Mark as inactive if quantity becomes 0
            cursor.execute('UPDATE products SET status = "Inactive" WHERE current_stock <= 0 AND id = %s', (item['id'],))
            
            # Record in sales history
            cursor.execute('INSERT INTO sales_history (product_id, quantity_sold, amount) VALUES (%s, %s, %s)',
                          (item['id'], item['quantity'], float(item.get('price', 0)) * item['quantity']))
        
        # Update coupon usage if applied
        if data.get('coupon_id'):
            cursor.execute('UPDATE coupons SET used_count = used_count + 1 WHERE id = %s',
                          (data['coupon_id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'invoice_no': invoice_no,
            'points_earned': points_earned,
            'message': 'Sale completed successfully'
        })

@app.route('/api/sales/search')
def search_sales():
    search_type = request.args.get('type', 'invoice_no')
    query = request.args.get('q', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if search_type == 'invoice_no':
        cursor.execute('SELECT * FROM sales WHERE invoice_no LIKE %s ORDER BY created_at DESC', (f'%{query}%',))
    elif search_type == 'customer_name':
        cursor.execute('SELECT * FROM sales WHERE customer_name LIKE %s ORDER BY created_at DESC', (f'%{query}%',))
    else:  # customer_contact
        cursor.execute('SELECT * FROM sales WHERE customer_contact LIKE %s ORDER BY created_at DESC', (f'%{query}%',))
    
    sales = cursor.fetchall()
    
    # Convert Decimal to float
    for sale in sales:
        for field in ['bill_amount', 'discount_amount', 'coupon_discount', 'net_amount']:
            if sale.get(field):
                sale[field] = float(sale[field])
    
    cursor.close()
    conn.close()
    return jsonify(sales)

# ============= ADMIN SPECIFIC APIs =============

# Suppliers API
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

# Categories API
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
                if product.get('price'):
                    product['price'] = float(product['price'])
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
            cursor.execute("UPDATE products SET status='Deleted' WHERE id=%s", (product_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    init_db()

    print("🚀 UNIFIED INVENTORY & BILLING MANAGEMENT SYSTEM")
    print("=" * 80)
    print("🔐 Login: http://localhost:5000")
    print("🏠 Admin Dashboard: http://localhost:5000/admin")
    print("📝 Add Products: http://localhost:5000/addproducts.html")
    print("📊 AI Analytics: http://localhost:5000/aianalytics.html")
    print("🏷️ Categories: http://localhost:5000/category.html")
    print("🚚 Suppliers: http://localhost:5000/supplier.html")
    print("💳 Billing System: http://localhost:5000/billing")
    print("🛒 POS System: http://localhost:5000/pos")
    print("📈 Bill History: http://localhost:5000/bill-history")
    print("🎟️ Coupon Manager: http://localhost:5000/coupon-manager")
    print("💾 Database: MySQL (inventory_ai)")
    print("🤖 AI Engine: Active with Enhanced Analytics")
    print("🔄 Features: Fully Synchronized Admin + Billing System")
    print("🔑 Login Credentials:")
    print("   Admin: admin / admin123")
    print("   Billing: billing / billing123")
    print("=" * 80)

    app.run(debug=True, port=5000)
