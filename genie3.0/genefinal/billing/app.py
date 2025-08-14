from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import time
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

def get_db_connection():
    conn = sqlite3.connect('pos_system.db')
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    conn = get_db_connection()
    
    # Products table
    conn.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        status TEXT DEFAULT 'Active'
    )''')
    
    # Customers table
    conn.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        contact TEXT UNIQUE NOT NULL,
        loyalty_points INTEGER DEFAULT 0,
        total_purchases REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Sales history table
    conn.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_contact TEXT NOT NULL,
        customer_email TEXT,
        bill_amount REAL NOT NULL,
        discount_amount REAL DEFAULT 0,
        coupon_discount REAL DEFAULT 0,
        points_used INTEGER DEFAULT 0,
        net_amount REAL NOT NULL,
        points_earned INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        items_json TEXT NOT NULL
    )''')
    
    # Coupons table
    conn.execute('''CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_type TEXT NOT NULL,
        discount_value REAL NOT NULL,
        min_amount REAL DEFAULT 0,
        max_discount REAL DEFAULT 0,
        usage_limit INTEGER DEFAULT 1,
        used_count INTEGER DEFAULT 0,
        valid_from TEXT DEFAULT CURRENT_TIMESTAMP,
        valid_until TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    )''')
    
    # Insert sample data if tables are empty
    if conn.execute('SELECT COUNT(*) FROM products').fetchone()[0] == 0:
        sample_products = [
            ('Laptop Dell XPS', 85000.00, 10, 'Active'),
            ('iPhone 14 Pro', 125000.00, 5, 'Active'),
            ('Samsung Galaxy S23', 95000.00, 8, 'Active'),
            ('MacBook Air M2', 115000.00, 3, 'Active'),
            ('Sony Headphones', 25000.00, 15, 'Active'),
            ('Logitech Mouse', 2500.00, 20, 'Active'),
            ('Mechanical Keyboard', 8500.00, 12, 'Active'),
            ('4K Monitor', 45000.00, 6, 'Active'),
            ('USB-C Hub', 3500.00, 25, 'Active'),
            ('Webcam HD', 7500.00, 18, 'Active')
        ]
        conn.executemany('INSERT INTO products (name, price, quantity, status) VALUES (?, ?, ?, ?)', sample_products)
    
    # Insert sample coupons
    if conn.execute('SELECT COUNT(*) FROM coupons').fetchone()[0] == 0:
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        sample_coupons = [
            ('WELCOME10', 'percentage', 10.0, 1000.0, 5000.0, 10, 0, datetime.now().strftime("%Y-%m-%d"), future_date, 1),
            ('SAVE500', 'fixed', 500.0, 2000.0, 500.0, 5, 0, datetime.now().strftime("%Y-%m-%d"), future_date, 1),
            ('BIGDEAL', 'percentage', 15.0, 10000.0, 10000.0, 3, 0, datetime.now().strftime("%Y-%m-%d"), future_date, 1)
        ]
        conn.executemany('''INSERT INTO coupons (code, discount_type, discount_value, min_amount, 
                           max_discount, usage_limit, used_count, valid_from, valid_until, is_active) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', sample_coupons)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
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

# API Routes
@app.route('/api/products')
def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE status = "Active"').fetchall()
    conn.close()
    return jsonify([dict(product) for product in products])

@app.route('/api/products/search')
def search_products():
    query = request.args.get('q', '')
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE name LIKE ? AND status = "Active"', 
                           (f'%{query}%',)).fetchall()
    conn.close()
    return jsonify([dict(product) for product in products])

@app.route('/api/customers/<contact>')
def get_customer(contact):
    conn = get_db_connection()
    customer = conn.execute('SELECT * FROM customers WHERE contact = ?', (contact,)).fetchone()
    conn.close()
    if customer:
        return jsonify(dict(customer))
    return jsonify({'error': 'Customer not found'}), 404

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO customers (name, email, contact) VALUES (?, ?, ?)',
                    (data['name'], data['email'], data['contact']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Customer added successfully'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Customer with this contact already exists'}), 400

@app.route('/api/coupons/validate', methods=['POST'])
def validate_coupon():
    data = request.json
    coupon_code = data.get('code', '').upper()
    bill_amount = data.get('amount', 0)
    
    conn = get_db_connection()
    coupon = conn.execute('''SELECT * FROM coupons WHERE code = ? AND is_active = 1 AND 
                            used_count < usage_limit AND date('now') BETWEEN valid_from AND valid_until''', 
                         (coupon_code,)).fetchone()
    conn.close()
    
    if not coupon:
        return jsonify({'error': 'Invalid or expired coupon code'}), 400
    
    if bill_amount < coupon['min_amount']:
        return jsonify({'error': f'Minimum bill amount required: ₹{coupon["min_amount"]}'}), 400
    
    if coupon['discount_type'] == 'percentage':
        discount = (bill_amount * coupon['discount_value']) / 100
        if coupon['max_discount'] > 0:
            discount = min(discount, coupon['max_discount'])
    else:
        discount = coupon['discount_value']
    
    return jsonify({
        'discount': discount,
        'coupon_id': coupon['id'],
        'message': f'Coupon applied! Discount: ₹{discount:.2f}'
    })

@app.route('/api/coupons', methods=['GET'])
def get_coupons():
    conn = get_db_connection()
    coupons = conn.execute('SELECT * FROM coupons ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(coupon) for coupon in coupons])

@app.route('/api/coupons', methods=['POST'])
def add_coupon():
    data = request.json
    conn = get_db_connection()
    try:
        valid_until = (datetime.now() + timedelta(days=int(data['valid_days']))).strftime("%Y-%m-%d")
        conn.execute('''INSERT INTO coupons (code, discount_type, discount_value, min_amount, 
                       max_discount, usage_limit, valid_until) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (data['code'].upper(), data['discount_type'], float(data['discount_value']),
                     float(data['min_amount']), float(data['max_discount']), 
                     int(data['usage_limit']), valid_until))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Coupon added successfully'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Coupon code already exists'}), 400

@app.route('/api/sales', methods=['POST'])
def create_sale():
    data = request.json
    conn = get_db_connection()
    
    # Generate invoice number
    invoice_no = str(int(time.time()))
    
    # Calculate points
    points_used = data.get('points_used', 0)
    points_earned = max(0, int(data['net_amount'] / 100))
    
    # Insert sale record
    conn.execute('''INSERT INTO sales (invoice_no, customer_name, customer_contact, customer_email,
                   bill_amount, discount_amount, coupon_discount, points_used, net_amount, 
                   points_earned, items_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (invoice_no, data['customer_name'], data['customer_contact'], data.get('customer_email', ''),
                 data['bill_amount'], data['discount_amount'], data.get('coupon_discount', 0),
                 points_used, data['net_amount'], points_earned, json.dumps(data['items'])))
    
    # Update customer loyalty points
    conn.execute('''INSERT OR REPLACE INTO customers (name, email, contact, loyalty_points, total_purchases)
                   VALUES (?, ?, ?, 
                   COALESCE((SELECT loyalty_points FROM customers WHERE contact=?), 0) - ? + ?,
                   COALESCE((SELECT total_purchases FROM customers WHERE contact=?), 0) + ?)''',
                (data['customer_name'], data.get('customer_email', ''), data['customer_contact'],
                 data['customer_contact'], points_used, points_earned, data['customer_contact'], data['net_amount']))
    
    # Update product quantities
    for item in data['items']:
        conn.execute('UPDATE products SET quantity = quantity - ? WHERE id = ?',
                    (item['quantity'], item['id']))
        # Mark as inactive if quantity becomes 0
        conn.execute('UPDATE products SET status = "Inactive" WHERE quantity <= 0')
    
    # Update coupon usage if applied
    if data.get('coupon_id'):
        conn.execute('UPDATE coupons SET used_count = used_count + 1 WHERE id = ?',
                    (data['coupon_id'],))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'invoice_no': invoice_no,
        'points_earned': points_earned,
        'message': 'Sale completed successfully'
    })

@app.route('/api/sales')
def get_sales():
    conn = get_db_connection()
    sales = conn.execute('SELECT * FROM sales ORDER BY created_at DESC LIMIT 100').fetchall()
    conn.close()
    return jsonify([dict(sale) for sale in sales])

@app.route('/api/sales/search')
def search_sales():
    search_type = request.args.get('type', 'invoice_no')
    query = request.args.get('q', '')
    
    conn = get_db_connection()
    if search_type == 'invoice_no':
        sales = conn.execute('SELECT * FROM sales WHERE invoice_no LIKE ? ORDER BY created_at DESC',
                           (f'%{query}%',)).fetchall()
    elif search_type == 'customer_name':
        sales = conn.execute('SELECT * FROM sales WHERE customer_name LIKE ? ORDER BY created_at DESC',
                           (f'%{query}%',)).fetchall()
    else:  # customer_contact
        sales = conn.execute('SELECT * FROM sales WHERE customer_contact LIKE ? ORDER BY created_at DESC',
                           (f'%{query}%',)).fetchall()
    
    conn.close()
    return jsonify([dict(sale) for sale in sales])

if __name__ == '__main__':
    setup_database()
    app.run(debug=True)
