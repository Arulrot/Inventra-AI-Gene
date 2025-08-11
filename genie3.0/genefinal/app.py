from flask import Flask, jsonify, request, send_from_directory
import mysql.connector
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# AI Engine Configuration
AI_CONFIG = {
    'LOW_STOCK_THRESHOLD': 10,
    'NON_MOVABLE_DAYS': 90,
    'EXPIRY_WARNING_DAYS': 30,
    'REORDER_MULTIPLIER': 1.5
}

# MySQL connection config
MYSQL_CONFIG = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'inventory_ai'
}

def get_db_connection():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    return conn

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
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT,
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

# Initialize AI engine
ai_engine = InventoryAI()

# Routes and APIs remain mostly unchanged except DB calls are updated accordingly.

@app.route('/')
def home():
    return send_from_directory('.', 'dashboard.html')

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

@app.route('/aianalytics.html')
def ai_analytics():
    return send_from_directory('.', 'aianalytics.html')

@app.route('/billing.html')
def billing():
    return send_from_directory('.', 'billing.html')

# API Routes
@app.route('/api/stats')
def get_stats():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM suppliers")
        suppliers_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM categories")
        categories_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM products")
        products_count = c.fetchone()[0]

        c.execute("SELECT SUM(current_stock) FROM products")
        total_stock = c.fetchone()[0]
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

# Products API
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

            # Trigger AI analysis after adding product
            try:
                ai_engine.analyze_inventory()
            except Exception as ai_error:
                print(f"⚠️ AI analysis failed: {ai_error}")

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

    print("🤖 Inventor AI Genie - AI Inventory Management System")
    print("=" * 60)
    print("🏠 Dashboard: http://localhost:5000")
    print("📝 Add Products: http://localhost:5000/addproducts.html")
    print("📊 AI Analytics: http://localhost:5000/aianalytics.html")
    print("💾 Database: MySQL (inventory_ai)")
    print("🤖 AI Engine: Active with Date Tracking")
    print("=" * 60)

    app.run(debug=True, port=5000)
