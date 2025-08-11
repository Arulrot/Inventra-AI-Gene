from flask import Flask, jsonify, request, send_from_directory, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Database initialization
def init_db():
    conn = sqlite3.connect('ims.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS supplier (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT,
        address TEXT,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS category (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS product (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER,
        supplier_id INTEGER,
        price REAL,
        stock INTEGER,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES category(id),
        FOREIGN KEY (supplier_id) REFERENCES supplier(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_no TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_contact TEXT,
        total_amount REAL NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sales_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_no TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        total REAL NOT NULL,
        FOREIGN KEY (bill_no) REFERENCES sales(bill_no),
        FOREIGN KEY (product_id) REFERENCES product(id)
    )''')
    
    conn.commit()
    conn.close()

# Root redirect to admindash.html
@app.route('/')
def redirect_to_admin():
    return redirect('/admindash.html')

# Serve HTML files
@app.route('/admindash.html')
def serve_admin_dash():
    return send_from_directory('.', 'admindash.html')

@app.route('/category.html')
def serve_category():
    return send_from_directory('.', 'category.html')

@app.route('/images/<path:path>')
def send_img(path):
    return send_from_directory('images', path)

# Stats API
@app.route('/api/stats')
def api_stats():
    try:
        conn = sqlite3.connect('ims.db')
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM supplier")
        suppliers_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM category")
        categories_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM product")
        products_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM sales")
        sales_count = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "suppliers": suppliers_count,
            "categories": categories_count,
            "products": products_count,
            "sales": sales_count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Category APIs
@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        conn = sqlite3.connect('ims.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM category ORDER BY name")
        categories = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(categories)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    try:
        conn = sqlite3.connect('ims.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM category WHERE id = ?", (category_id,))
        category = c.fetchone()
        conn.close()
        if category:
            return jsonify(dict(category))
        return jsonify({"error": "Category not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories', methods=['POST'])
def add_category():
    try:
        data = request.json
        conn = sqlite3.connect('ims.db')
        c = conn.cursor()
        c.execute("INSERT INTO category (name) VALUES (?)", (data['name'],))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    try:
        data = request.json
        conn = sqlite3.connect('ims.db')
        c = conn.cursor()
        c.execute("UPDATE category SET name=? WHERE id=?", (data['name'], category_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    try:
        conn = sqlite3.connect('ims.db')
        c = conn.cursor()
        c.execute("DELETE FROM category WHERE id=?", (category_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories/counts', methods=['GET'])
def get_category_counts():
    try:
        conn = sqlite3.connect('ims.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT category_id, COUNT(*) as count 
            FROM product 
            WHERE category_id IS NOT NULL 
            GROUP BY category_id
        """)
        counts = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(counts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    print("=" * 60)
    print("🚀 Inventra AI Gene Server Starting...")
    print("=" * 60)
    print("📊 Main Dashboard: http://localhost:5000")
    print("📝 Categories: http://localhost:5000/category.html")
    print("💾 Database: SQLite (ims.db)")
    print("=" * 60)
    
    app.run(debug=True, port=5000, host='127.0.0.1')
