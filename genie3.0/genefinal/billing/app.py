from flask import Flask, jsonify, request, send_from_directory, render_template_string
import mysql.connector
import os
from datetime import datetime, timedelta
import json
from decimal import Decimal
import uuid
import hashlib

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
    """Initialize database with comprehensive enhanced schema"""
    conn = get_db_connection()
    c = conn.cursor()

    # Enhanced Suppliers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            supplier_id VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            contact_person VARCHAR(255),
            phone VARCHAR(50),
            email VARCHAR(255),
            address TEXT,
            gst_number VARCHAR(50),
            payment_terms VARCHAR(255),
            status ENUM('active', 'inactive') DEFAULT 'active',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    ''')

    # Enhanced Categories table
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            parent_id INT,
            tax_rate DECIMAL(5,2) DEFAULT 18.00,
            image_url VARCHAR(500),
            sort_order INT DEFAULT 0,
            status ENUM('active', 'inactive') DEFAULT 'active',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    ''')

    # Enhanced Products table with comprehensive fields
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(255) UNIQUE NOT NULL,
            sku VARCHAR(255) UNIQUE,
            barcode VARCHAR(255) UNIQUE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            category_id INT,
            supplier_id INT,
            brand VARCHAR(255),
            model VARCHAR(255),
            cost_price DECIMAL(12,2),
            selling_price DECIMAL(12,2),
            mrp DECIMAL(12,2),
            discount_percent DECIMAL(5,2) DEFAULT 0.00,
            discount_price DECIMAL(12,2),
            current_stock INT DEFAULT 0,
            minimum_stock INT DEFAULT 5,
            maximum_stock INT DEFAULT 1000,
            unit VARCHAR(50) DEFAULT 'pcs',
            weight DECIMAL(8,2),
            dimensions VARCHAR(255),
            expiry_date DATE,
            batch_number VARCHAR(255),
            manufacturing_date DATE,
            date_added DATE NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            total_sold INT DEFAULT 0,
            total_purchased INT DEFAULT 0,
            low_stock_alert BOOLEAN DEFAULT TRUE,
            track_inventory BOOLEAN DEFAULT TRUE,
            is_active BOOLEAN DEFAULT TRUE,
            tax_inclusive BOOLEAN DEFAULT FALSE,
            hsn_code VARCHAR(50),
            image_url VARCHAR(500),
            tags TEXT,
            warranty_period INT DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
            INDEX idx_product_id (product_id),
            INDEX idx_sku (sku),
            INDEX idx_barcode (barcode),
            INDEX idx_category (category_id),
            INDEX idx_active (is_active)
        )
    ''')

    # Enhanced Customers table with loyalty system
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(20) UNIQUE NOT NULL,
            email VARCHAR(255),
            address TEXT,
            city VARCHAR(100),
            state VARCHAR(100),
            pincode VARCHAR(10),
            date_of_birth DATE,
            anniversary_date DATE,
            gender ENUM('male', 'female', 'other'),
            occupation VARCHAR(255),
            loyalty_points INT DEFAULT 0,
            total_spent DECIMAL(15,2) DEFAULT 0.00,
            total_orders INT DEFAULT 0,
            total_savings DECIMAL(15,2) DEFAULT 0.00,
            tier ENUM('bronze', 'silver', 'gold', 'platinum', 'diamond') DEFAULT 'bronze',
            tier_achieved_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            referral_code VARCHAR(20) UNIQUE,
            referred_by VARCHAR(50),
            notes TEXT,
            tags VARCHAR(255),
            status ENUM('active', 'inactive', 'blocked') DEFAULT 'active',
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_visit TIMESTAMP NULL,
            is_vip BOOLEAN DEFAULT FALSE,
            credit_limit DECIMAL(15,2) DEFAULT 0.00,
            INDEX idx_phone (phone),
            INDEX idx_customer_id (customer_id),
            INDEX idx_tier (tier),
            INDEX idx_status (status)
        )
    ''')

    # Enhanced Bills/Sales table
    c.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bill_number VARCHAR(50) UNIQUE NOT NULL,
            customer_id INT,
            cashier_name VARCHAR(100) DEFAULT 'System',
            bill_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bill_type ENUM('sale', 'return', 'exchange') DEFAULT 'sale',
            subtotal DECIMAL(15,2) NOT NULL,
            total_discount DECIMAL(12,2) DEFAULT 0.00,
            loyalty_points_used INT DEFAULT 0,
            loyalty_discount DECIMAL(12,2) DEFAULT 0.00,
            coupon_discount DECIMAL(12,2) DEFAULT 0.00,
            tax_amount DECIMAL(12,2) DEFAULT 0.00,
            round_off DECIMAL(5,2) DEFAULT 0.00,
            net_amount DECIMAL(15,2) NOT NULL,
            paid_amount DECIMAL(15,2) DEFAULT 0.00,
            change_amount DECIMAL(12,2) DEFAULT 0.00,
            payment_method ENUM('cash', 'card', 'upi', 'wallet', 'credit', 'mixed') DEFAULT 'cash',
            payment_status ENUM('pending', 'completed', 'partial', 'refunded') DEFAULT 'completed',
            payment_reference VARCHAR(255),
            coupon_code VARCHAR(50),
            loyalty_points_earned INT DEFAULT 0,
            delivery_address TEXT,
            delivery_charges DECIMAL(8,2) DEFAULT 0.00,
            notes TEXT,
            special_instructions TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
            INDEX idx_bill_number (bill_number),
            INDEX idx_customer (customer_id),
            INDEX idx_date (bill_date),
            INDEX idx_status (payment_status)
        )
    ''')

    # Enhanced Bill Items table
    c.execute('''
        CREATE TABLE IF NOT EXISTS bill_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bill_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity DECIMAL(10,3) NOT NULL,
            unit_price DECIMAL(12,2) NOT NULL,
            discount_percent DECIMAL(5,2) DEFAULT 0.00,
            discount_amount DECIMAL(12,2) DEFAULT 0.00,
            tax_rate DECIMAL(5,2) DEFAULT 18.00,
            tax_amount DECIMAL(12,2) DEFAULT 0.00,
            line_total DECIMAL(15,2) NOT NULL,
            cost_price DECIMAL(12,2),
            profit_amount DECIMAL(12,2),
            serial_numbers TEXT,
            batch_number VARCHAR(255),
            expiry_date DATE,
            returned_quantity DECIMAL(10,3) DEFAULT 0.00,
            FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            INDEX idx_bill (bill_id),
            INDEX idx_product (product_id)
        )
    ''')

    # Enhanced Coupons table
    c.execute('''
        CREATE TABLE IF NOT EXISTS coupons (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            discount_type ENUM('percentage', 'fixed', 'bogo', 'buy_x_get_y') DEFAULT 'percentage',
            discount_value DECIMAL(12,2) NOT NULL,
            min_purchase_amount DECIMAL(12,2) DEFAULT 0.00,
            max_discount_amount DECIMAL(12,2) DEFAULT 999999.99,
            usage_limit INT DEFAULT 1000,
            usage_limit_per_customer INT DEFAULT 10,
            used_count INT DEFAULT 0,
            valid_from DATETIME NOT NULL,
            valid_until DATETIME NOT NULL,
            applicable_days VARCHAR(20) DEFAULT 'all',
            applicable_categories TEXT,
            applicable_products TEXT,
            applicable_customer_tiers TEXT,
            exclude_sale_items BOOLEAN DEFAULT FALSE,
            is_stackable BOOLEAN DEFAULT FALSE,
            auto_apply BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_by VARCHAR(100) DEFAULT 'System',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_code (code),
            INDEX idx_active (is_active),
            INDEX idx_dates (valid_from, valid_until)
        )
    ''')

    # Loyalty Transactions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS loyalty_transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            bill_id INT NULL,
            transaction_type ENUM('earned', 'redeemed', 'expired', 'adjusted', 'bonus') NOT NULL,
            points INT NOT NULL,
            description TEXT,
            reference_number VARCHAR(100),
            expiry_date DATE,
            balance_before INT DEFAULT 0,
            balance_after INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(100) DEFAULT 'System',
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE SET NULL,
            INDEX idx_customer (customer_id),
            INDEX idx_type (transaction_type),
            INDEX idx_date (created_at)
        )
    ''')

    # Sales history table (enhanced)
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT,
            bill_id INT,
            quantity_sold DECIMAL(10,3),
            sale_price DECIMAL(12,2),
            cost_price DECIMAL(12,2),
            profit_amount DECIMAL(12,2),
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            customer_id INT,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
            FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE SET NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
            INDEX idx_product (product_id),
            INDEX idx_date (sale_date),
            INDEX idx_customer (customer_id)
        )
    ''')

    # AI Recommendations table (enhanced)
    c.execute('''
        CREATE TABLE IF NOT EXISTS ai_recommendations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            type VARCHAR(50) NOT NULL,
            product_id INT,
            customer_id INT,
            message TEXT NOT NULL,
            action_required TEXT,
            priority INT DEFAULT 1,
            status VARCHAR(50) DEFAULT 'active',
            data JSON,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_date TIMESTAMP NULL,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
            INDEX idx_type (type),
            INDEX idx_priority (priority),
            INDEX idx_status (status)
        )
    ''')

    # System Settings table
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            setting_key VARCHAR(100) UNIQUE NOT NULL,
            setting_value TEXT,
            setting_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
            description TEXT,
            category VARCHAR(100) DEFAULT 'general',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            updated_by VARCHAR(100) DEFAULT 'System'
        )
    ''')

    # Payment Methods table
    c.execute('''
        CREATE TABLE IF NOT EXISTS payment_methods (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bill_id INT NOT NULL,
            method ENUM('cash', 'card', 'upi', 'wallet', 'cheque', 'credit') NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            reference_number VARCHAR(255),
            status ENUM('pending', 'completed', 'failed') DEFAULT 'completed',
            notes TEXT,
            FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE
        )
    ''')

    # Insert sample data
    insert_sample_data(c)
    
    conn.commit()
    c.close()
    conn.close()
    print("✅ Enhanced database initialized successfully")

def insert_sample_data(cursor):
    """Insert comprehensive sample data"""
    
    # Sample suppliers
    suppliers = [
        ('SUP001', 'Tech Distributors Ltd', 'Raj Kumar', '+91-9876543210', 'raj@techdist.com', '123 Tech Street, Delhi', '07AAACT2727Q1ZZ', 'Net 30 days'),
        ('SUP002', 'Electronics Wholesale', 'Priya Sharma', '+91-8765432109', 'priya@elecwhole.com', '456 Electronics Park, Mumbai', '27AABCE5617R1ZX', 'Net 15 days'),
        ('SUP003', 'Mobile World Supplies', 'Amit Singh', '+91-7654321098', 'amit@mobworld.com', '789 Mobile Plaza, Bangalore', '29AABCM1234M1Z5', 'Cash on delivery'),
    ]
    
    cursor.execute("DELETE FROM suppliers")
    cursor.executemany('''
        INSERT INTO suppliers (supplier_id, name, contact_person, phone, email, address, gst_number, payment_terms)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', suppliers)
    
    # Sample categories
    categories = [
        ('Electronics', 'Electronic devices and gadgets', None, 18.00, '/images/electronics.jpg', 1),
        ('Mobile Phones', 'Smartphones and accessories', 1, 18.00, '/images/mobiles.jpg', 1),
        ('Laptops', 'Laptops and computers', 1, 18.00, '/images/laptops.jpg', 2),
        ('Accessories', 'Electronic accessories', 1, 18.00, '/images/accessories.jpg', 3),
        ('Home Appliances', 'Home and kitchen appliances', None, 18.00, '/images/appliances.jpg', 2),
    ]
    
    cursor.execute("DELETE FROM categories")
    cursor.executemany('''
        INSERT INTO categories (name, description, parent_id, tax_rate, image_url, sort_order)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', categories)
    
    # Sample products
    products = [
        ('PROD001', 'SKU001', 'IP15PM256', 'iPhone 15 Pro Max 256GB', 'Latest iPhone with advanced features', 2, 1, 'Apple', 'iPhone 15 Pro Max', 120000.00, 139900.00, 139900.00, 0.00, 139900.00, 5, 2, 50, 'pcs', 0.221, '160.7×77.6×7.85 mm', None, 'BATCH001', '2024-01-15', '2024-01-20', 0, 0, True, True, True, False, '85171800', '/images/iphone15pm.jpg', 'smartphone,premium,5g', 12),
        ('PROD002', 'SKU002', 'SAM24U512', 'Samsung Galaxy S24 Ultra 512GB', 'Premium Samsung flagship smartphone', 2, 1, 'Samsung', 'Galaxy S24 Ultra', 110000.00, 129900.00, 129900.00, 5.00, 123405.00, 8, 3, 30, 'pcs', 0.232, '162.3×79.0×8.6 mm', None, 'BATCH002', '2024-01-10', '2024-01-25', 0, 0, True, True, True, False, '85171800', '/images/galaxys24.jpg', 'smartphone,android,premium', 12),
        ('PROD003', 'SKU003', 'MBA13M3', 'MacBook Air 13" M3 Chip', 'Ultra-thin laptop with M3 processor', 3, 1, 'Apple', 'MacBook Air 13"', 95000.00, 114900.00, 114900.00, 0.00, 114900.00, 3, 1, 20, 'pcs', 1.24, '304×213×11.3 mm', None, 'BATCH003', '2024-01-05', '2024-01-30', 0, 0, True, True, True, False, '84713010', '/images/macbook-air.jpg', 'laptop,apple,ultrabook', 12),
        ('PROD004', 'SKU004', 'DELL-XPS13', 'Dell XPS 13 Plus Intel i7', 'Premium ultrabook with latest Intel processor', 3, 2, 'Dell', 'XPS 13 Plus', 85000.00, 109900.00, 119900.00, 8.34, 100900.00, 4, 1, 15, 'pcs', 1.26, '295.3×199.04×15.28 mm', None, 'BATCH004', '2024-01-12', '2024-02-01', 0, 0, True, True, True, False, '84713010', '/images/dell-xps.jpg', 'laptop,dell,business', 24),
        ('PROD005', 'SKU005', 'AIRPODS-PRO2', 'AirPods Pro 2nd Generation', 'Wireless earbuds with active noise cancellation', 4, 1, 'Apple', 'AirPods Pro', 20000.00, 24900.00, 24900.00, 0.00, 24900.00, 15, 5, 100, 'pcs', 0.061, '30.9×21.8×24.0 mm', None, 'BATCH005', '2024-01-18', '2024-02-05', 0, 0, True, True, True, False, '85183000', '/images/airpods-pro.jpg', 'earbuds,wireless,premium', 12),
    ]
    
    cursor.execute("DELETE FROM products")
    cursor.executemany('''
        INSERT INTO products (product_id, sku, barcode, name, description, category_id, supplier_id, brand, model, 
                             cost_price, selling_price, mrp, discount_percent, discount_price, current_stock, 
                             minimum_stock, maximum_stock, unit, weight, dimensions, expiry_date, batch_number, 
                             manufacturing_date, date_added, total_sold, total_purchased, low_stock_alert, 
                             track_inventory, is_active, tax_inclusive, hsn_code, image_url, tags, warranty_period)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', products)
    
    # Sample coupons
    coupons = [
        ('WELCOME10', 'Welcome Offer', 'Get 10% off on your first purchase', 'percentage', 10.00, 1000.00, 2000.00, 1000, 1, 0, '2024-01-01 00:00:00', '2024-12-31 23:59:59', 'all', '', '', 'bronze,silver,gold,platinum,diamond', False, False, False, True),
        ('SAVE500', 'Flat Savings', 'Flat ₹500 off on purchase above ₹5000', 'fixed', 500.00, 5000.00, 500.00, 500, 2, 0, '2024-01-01 00:00:00', '2024-06-30 23:59:59', 'all', '', '', 'silver,gold,platinum,diamond', False, False, False, True),
        ('PREMIUM20', 'Premium Discount', '20% off for premium members', 'percentage', 20.00, 2000.00, 5000.00, 200, 3, 0, '2024-01-01 00:00:00', '2024-12-31 23:59:59', 'all', '', '', 'gold,platinum,diamond', False, True, False, True),
        ('MOBILE15', 'Mobile Special', '15% off on mobile phones', 'percentage', 15.00, 1500.00, 3000.00, 300, 5, 0, '2024-01-01 00:00:00', '2024-03-31 23:59:59', 'all', '2', '', 'bronze,silver,gold,platinum,diamond', True, False, False, True),
    ]
    
    cursor.execute("DELETE FROM coupons")
    cursor.executemany('''
        INSERT INTO coupons (code, name, description, discount_type, discount_value, min_purchase_amount, 
                           max_discount_amount, usage_limit, usage_limit_per_customer, used_count, valid_from, 
                           valid_until, applicable_days, applicable_categories, applicable_products, 
                           applicable_customer_tiers, exclude_sale_items, is_stackable, auto_apply, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', coupons)
    
    # System settings
    settings = [
        ('store_name', 'Inventa AI Gene Store', 'string', 'Store name for billing'),
        ('store_address', 'Tech Plaza, Innovation Street, Delhi-110001', 'string', 'Store address'),
        ('store_phone', '+91-9899459288', 'string', 'Store contact number'),
        ('store_email', 'info@inventaaigene.com', 'string', 'Store email address'),
        ('gst_number', '07AAACI5482L1ZY', 'string', 'GST registration number'),
        ('default_tax_rate', '18.00', 'number', 'Default tax rate percentage'),
        ('loyalty_rate', '1', 'number', 'Points per rupee spent'),
        ('point_value', '1.00', 'number', 'Value of one loyalty point in rupees'),
        ('low_stock_alert', 'true', 'boolean', 'Enable low stock alerts'),
        ('auto_backup', 'true', 'boolean', 'Enable automatic backup'),
    ]
    
    cursor.execute("DELETE FROM system_settings")
    cursor.executemany('''
        INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
        VALUES (%s, %s, %s, %s)
    ''', settings)

# AI Analytics Engine (Enhanced)
class InventoryAI:
    def __init__(self):
        self.conn = get_db_connection()
        self.conn.autocommit = False

    def analyze_inventory(self):
        recommendations = []
        cursor = self.conn.cursor(dictionary=True)
        
        # Clear old recommendations
        cursor.execute("DELETE FROM ai_recommendations WHERE status = 'active'")
        self.conn.commit()

        # Run all analyses
        recommendations.extend(self._analyze_low_stock())
        recommendations.extend(self._analyze_non_movable_stock())
        recommendations.extend(self._analyze_expiry_warnings())
        recommendations.extend(self._analyze_reorder_suggestions())
        recommendations.extend(self._analyze_customer_behavior())
        recommendations.extend(self._analyze_profit_margins())

        # Save recommendations
        for rec in recommendations:
            cursor.execute("""
                INSERT INTO ai_recommendations (type, product_id, customer_id, message, action_required, priority, data)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (rec['type'], rec.get('product_id'), rec.get('customer_id'), rec['message'], 
                  rec.get('action_required'), rec['priority'], json.dumps(rec.get('data', {}))))

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
            WHERE p.current_stock <= p.minimum_stock AND p.current_stock > 0 AND p.is_active = TRUE
        """)
        results = cursor.fetchall()
        cursor.close()

        recommendations = []
        for product in results:
            recommendations.append({
                'type': 'LOW_STOCK',
                'product_id': product['id'],
                'message': f"⚠️ {product['name']} is running low (Stock: {product['current_stock']}, Min: {product['minimum_stock']})",
                'action_required': 'Reorder stock immediately',
                'priority': 4,
                'data': {
                    'current_stock': product['current_stock'],
                    'minimum_stock': product['minimum_stock'],
                    'suggested_order': max(product['minimum_stock'] * 2, 10)
                }
            })
        return recommendations

    def _analyze_non_movable_stock(self):
        ninety_days_ago = (datetime.now() - timedelta(days=AI_CONFIG['NON_MOVABLE_DAYS'])).date()
        cursor = self.conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.current_stock > 0 AND p.date_added <= %s AND p.total_sold = 0 AND p.is_active = TRUE
        """, (ninety_days_ago,))
        results = cursor.fetchall()
        cursor.close()

        recommendations = []
        for product in results:
            days_in_stock = (datetime.now().date() - product['date_added']).days
            if days_in_stock >= AI_CONFIG['NON_MOVABLE_DAYS']:
                recommendations.append({
                    'type': 'NON_MOVABLE',
                    'product_id': product['id'],
                    'message': f"📦 {product['name']} hasn't moved for {days_in_stock} days. Consider promotion or price reduction.",
                    'action_required': 'Create promotional offer',
                    'priority': 2,
                    'data': {
                        'days_in_stock': days_in_stock,
                        'current_price': float(product['selling_price']),
                        'suggested_discount': 15
                    }
                })
        return recommendations

    def _analyze_expiry_warnings(self):
        warning_date = datetime.now() + timedelta(days=AI_CONFIG['EXPIRY_WARNING_DAYS'])
        cursor = self.conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            WHERE p.expiry_date IS NOT NULL AND p.expiry_date <= %s AND p.current_stock > 0 AND p.is_active = TRUE
        """, (warning_date.date(),))
        results = cursor.fetchall()
        cursor.close()

        recommendations = []
        for product in results:
            days_to_expiry = (product['expiry_date'] - datetime.now().date()).days
            
            if days_to_expiry <= 0:
                priority = 5
                message = f"🚨 {product['name']} has EXPIRED! Remove from inventory immediately."
                action = "Remove expired stock"
            elif days_to_expiry <= 7:
                priority = 4
                message = f"⏰ {product['name']} expires in {days_to_expiry} days. Urgent clearance needed!"
                action = "Urgent clearance sale"
            else:
                priority = 3
                message = f"📅 {product['name']} expires in {days_to_expiry} days. Plan clearance sale."
                action = "Plan clearance promotion"

            recommendations.append({
                'type': 'EXPIRY_WARNING',
                'product_id': product['id'],
                'message': message,
                'action_required': action,
                'priority': priority,
                'data': {
                    'days_to_expiry': days_to_expiry,
                    'expiry_date': product['expiry_date'].isoformat(),
                    'current_stock': product['current_stock']
                }
            })
        return recommendations

    def _analyze_reorder_suggestions(self):
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, c.name as category_name, 
                   COALESCE(AVG(bi.quantity), 0) as avg_daily_sales
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN bill_items bi ON p.id = bi.product_id
            LEFT JOIN bills b ON bi.bill_id = b.id AND b.bill_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            WHERE p.current_stock <= p.minimum_stock AND p.is_active = TRUE
            GROUP BY p.id
        """)
        results = cursor.fetchall()
        cursor.close()

        recommendations = []
        for product in results:
            avg_sales = float(product['avg_daily_sales']) if product['avg_daily_sales'] else 0
            suggested_order = max(int(avg_sales * 30), product['minimum_stock'] * 2, 10)
            
            recommendations.append({
                'type': 'REORDER_SUGGESTION',
                'product_id': product['id'],
                'message': f"📈 {product['name']} needs restocking. Suggested order: {suggested_order} units based on sales trend.",
                'action_required': 'Place purchase order',
                'priority': 3,
                'data': {
                    'suggested_quantity': suggested_order,
                    'avg_daily_sales': avg_sales,
                    'supplier_id': product['supplier_id']
                }
            })
        return recommendations

    def _analyze_customer_behavior(self):
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.*, COUNT(b.id) as order_count, SUM(b.net_amount) as total_spent,
                   DATEDIFF(NOW(), MAX(b.bill_date)) as days_since_last_order
            FROM customers c
            LEFT JOIN bills b ON c.id = b.customer_id AND b.bill_date >= DATE_SUB(NOW(), INTERVAL 90 DAY)
            WHERE c.status = 'active' AND c.total_orders > 3
            GROUP BY c.id
            HAVING days_since_last_order > 30 OR days_since_last_order IS NULL
        """)
        results = cursor.fetchall()
        cursor.close()

        recommendations = []
        for customer in results:
            if customer['days_since_last_order']:
                recommendations.append({
                    'type': 'CUSTOMER_RETENTION',
                    'customer_id': customer['id'],
                    'message': f"👤 {customer['name']} hasn't visited for {customer['days_since_last_order']} days. Send retention offer.",
                    'action_required': 'Send personalized offer',
                    'priority': 2,
                    'data': {
                        'days_since_last_order': customer['days_since_last_order'],
                        'total_spent': float(customer['total_spent']) if customer['total_spent'] else 0,
                        'suggested_discount': 10
                    }
                })
        return recommendations

    def _analyze_profit_margins(self):
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, ((p.selling_price - p.cost_price) / p.cost_price * 100) as profit_margin
            FROM products p
            WHERE p.cost_price > 0 AND p.is_active = TRUE
            HAVING profit_margin < 20
        """)
        results = cursor.fetchall()
        cursor.close()

        recommendations = []
        for product in results:
            recommendations.append({
                'type': 'LOW_MARGIN',
                'product_id': product['id'],
                'message': f"💰 {product['name']} has low profit margin ({product['profit_margin']:.1f}%). Consider price adjustment.",
                'action_required': 'Review pricing strategy',
                'priority': 1,
                'data': {
                    'current_margin': float(product['profit_margin']),
                    'cost_price': float(product['cost_price']),
                    'selling_price': float(product['selling_price']),
                    'suggested_price': float(product['cost_price']) * 1.25
                }
            })
        return recommendations

# Routes
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

# Enhanced API Routes

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Today's stats
        cursor.execute("""
            SELECT COUNT(*) as today_bills, COALESCE(SUM(net_amount), 0) as today_revenue,
                   COALESCE(AVG(net_amount), 0) as avg_order_value
            FROM bills WHERE DATE(bill_date) = CURDATE() AND payment_status = 'completed'
        """)
        today_stats = cursor.fetchone()
        
        # Product stats
        cursor.execute("""
            SELECT COUNT(*) as total_products, 
                   COUNT(CASE WHEN current_stock <= minimum_stock THEN 1 END) as low_stock_count,
                   COUNT(CASE WHEN current_stock = 0 THEN 1 END) as out_of_stock_count,
                   SUM(current_stock) as total_stock_value
            FROM products WHERE is_active = TRUE
        """)
        product_stats = cursor.fetchone()
        
        # Customer stats
        cursor.execute("""
            SELECT COUNT(*) as total_customers,
                   COUNT(CASE WHEN DATE(registration_date) = CURDATE() THEN 1 END) as new_customers_today,
                   SUM(loyalty_points) as total_loyalty_points
            FROM customers WHERE status = 'active'
        """)
        customer_stats = cursor.fetchone()
        
        # AI recommendations
        cursor.execute("SELECT COUNT(*) as active_recommendations FROM ai_recommendations WHERE status = 'active'")
        ai_stats = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'today': today_stats,
            'products': product_stats,
            'customers': customer_stats,
            'ai': ai_stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['GET', 'POST'])
def products_api():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        try:
            # Get query parameters
            search = request.args.get('search', '')
            category_id = request.args.get('category_id')
            supplier_id = request.args.get('supplier_id')
            active_only = request.args.get('active_only', 'true').lower() == 'true'
            low_stock_only = request.args.get('low_stock_only', 'false').lower() == 'true'
            
            # Build query
            query = """
                SELECT p.*, c.name as category_name, s.name as supplier_name,
                       ((p.selling_price - p.cost_price) / p.cost_price * 100) as profit_margin
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                WHERE 1=1
            """
            params = []
            
            if active_only:
                query += " AND p.is_active = TRUE"
            
            if search:
                query += " AND (p.name LIKE %s OR p.product_id LIKE %s OR p.sku LIKE %s OR p.barcode LIKE %s)"
                search_param = f'%{search}%'
                params.extend([search_param, search_param, search_param, search_param])
            
            if category_id:
                query += " AND p.category_id = %s"
                params.append(category_id)
            
            if supplier_id:
                query += " AND p.supplier_id = %s"
                params.append(supplier_id)
            
            if low_stock_only:
                query += " AND p.current_stock <= p.minimum_stock"
            
            query += " ORDER BY p.name"
            
            cursor.execute(query, params)
            products = cursor.fetchall()
            
            # Convert Decimal to float for JSON serialization
            for product in products:
                for key, value in product.items():
                    if isinstance(value, Decimal):
                        product[key] = float(value)
            
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
            required_fields = ['product_id', 'name', 'category_id', 'supplier_id', 'cost_price', 'selling_price', 'current_stock']
            for field in required_fields:
                if field not in data or data[field] in [None, '']:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Generate SKU if not provided
            sku = data.get('sku') or f"SKU{data['product_id']}"
            
            # Calculate discount price if discount percent is provided
            discount_percent = float(data.get('discount_percent', 0))
            selling_price = float(data['selling_price'])
            discount_price = selling_price * (1 - discount_percent / 100) if discount_percent > 0 else selling_price
            
            cursor.execute("""
                INSERT INTO products (
                    product_id, sku, barcode, name, description, category_id, supplier_id, brand, model,
                    cost_price, selling_price, mrp, discount_percent, discount_price, current_stock,
                    minimum_stock, maximum_stock, unit, weight, dimensions, expiry_date, batch_number,
                    manufacturing_date, date_added, hsn_code, image_url, tags, warranty_period
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['product_id'], sku, data.get('barcode'), data['name'], data.get('description'),
                data['category_id'], data['supplier_id'], data.get('brand'), data.get('model'),
                data['cost_price'], data['selling_price'], data.get('mrp', selling_price),
                discount_percent, discount_price, data['current_stock'],
                data.get('minimum_stock', 5), data.get('maximum_stock', 1000), data.get('unit', 'pcs'),
                data.get('weight'), data.get('dimensions'), data.get('expiry_date'),
                data.get('batch_number'), data.get('manufacturing_date'), datetime.now().date(),
                data.get('hsn_code'), data.get('image_url'), data.get('tags'),
                data.get('warranty_period', 0)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Product added successfully'})
            
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

@app.route('/api/customers', methods=['GET', 'POST'])
def customers_api():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        try:
            search = request.args.get('search', '')
            phone = request.args.get('phone', '')
            
            if phone:
                cursor.execute("""
                    SELECT c.*, COUNT(b.id) as total_bills, COALESCE(SUM(b.net_amount), 0) as lifetime_value
                    FROM customers c
                    LEFT JOIN bills b ON c.id = b.customer_id
                    WHERE c.phone = %s AND c.status = 'active'
                    GROUP BY c.id
                """, (phone,))
                customer = cursor.fetchone()
                
                if customer:
                    # Convert Decimal to float
                    for key, value in customer.items():
                        if isinstance(value, Decimal):
                            customer[key] = float(value)
                
                cursor.close()
                conn.close()
                return jsonify(customer) if customer else jsonify({'error': 'Customer not found'}), 404
            
            else:
                query = "SELECT * FROM customers WHERE status = 'active'"
                params = []
                
                if search:
                    query += " AND (name LIKE %s OR phone LIKE %s OR email LIKE %s)"
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param, search_param])
                
                query += " ORDER BY name"
                cursor.execute(query, params)
                customers = cursor.fetchall()
                
                # Convert Decimal to float
                for customer in customers:
                    for key, value in customer.items():
                        if isinstance(value, Decimal):
                            customer[key] = float(value)
                
                cursor.close()
                conn.close()
                return jsonify(customers)
                
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        try:
            data = request.json
            
            # Validate required fields
            if not data.get('name') or not data.get('phone'):
                return jsonify({'error': 'Name and phone are required'}), 400
            
            # Generate customer ID
            customer_id = f"CUST{datetime.now().strftime('%Y%m%d%H%M%S')}"
            referral_code = str(uuid.uuid4())[:8].upper()
            
            cursor.execute("""
                INSERT INTO customers (customer_id, name, phone, email, address, city, state, pincode,
                                     date_of_birth, gender, occupation, referral_code, referred_by, notes, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                customer_id, data['name'], data['phone'], data.get('email'),
                data.get('address'), data.get('city'), data.get('state'), data.get('pincode'),
                data.get('date_of_birth'), data.get('gender'), data.get('occupation'),
                referral_code, data.get('referred_by'), data.get('notes'), data.get('tags')
            ))
            
            new_customer_id = cursor.lastrowid
            
            # Award welcome bonus points
            welcome_points = 100
            cursor.execute("""
                INSERT INTO loyalty_transactions (customer_id, transaction_type, points, description, balance_after)
                VALUES (%s, 'bonus', %s, 'Welcome bonus for new registration', %s)
            """, (new_customer_id, welcome_points, welcome_points))
            
            cursor.execute("UPDATE customers SET loyalty_points = %s WHERE id = %s", (welcome_points, new_customer_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'customer_id': customer_id,
                'referral_code': referral_code,
                'welcome_points': welcome_points
            })
            
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET', 'POST'])
def categories_api():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("""
            SELECT c.*, p.name as parent_name, 
                   COUNT(pr.id) as product_count
            FROM categories c
            LEFT JOIN categories p ON c.parent_id = p.id
            LEFT JOIN products pr ON c.id = pr.category_id AND pr.is_active = TRUE
            WHERE c.status = 'active'
            GROUP BY c.id
            ORDER BY c.sort_order, c.name
        """)
        categories = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(categories)

    elif request.method == 'POST':
        try:
            data = request.json
            cursor.execute("""
                INSERT INTO categories (name, description, parent_id, tax_rate, image_url, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                data['name'], data.get('description'), data.get('parent_id'),
                data.get('tax_rate', 18.00), data.get('image_url'), data.get('sort_order', 0)
            ))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

@app.route('/api/suppliers', methods=['GET', 'POST'])
def suppliers_api():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("""
            SELECT s.*, COUNT(p.id) as product_count
            FROM suppliers s
            LEFT JOIN products p ON s.id = p.supplier_id AND p.is_active = TRUE
            WHERE s.status = 'active'
            GROUP BY s.id
            ORDER BY s.name
        """)
        suppliers = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(suppliers)

    elif request.method == 'POST':
        try:
            data = request.json
            supplier_id = f"SUP{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            cursor.execute("""
                INSERT INTO suppliers (supplier_id, name, contact_person, phone, email, address, 
                                     gst_number, payment_terms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                supplier_id, data['name'], data.get('contact_person'), data.get('phone'),
                data.get('email'), data.get('address'), data.get('gst_number'), data.get('payment_terms')
            ))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'supplier_id': supplier_id})
        except Exception as e:
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 500

@app.route('/api/coupons/validate', methods=['POST'])
def validate_coupon():
    try:
        data = request.json
        code = data.get('code', '').upper()
        amount = float(data.get('amount', 0))
        customer_tier = data.get('customer_tier', 'bronze')
        customer_id = data.get('customer_id')
        category_ids = data.get('category_ids', [])
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM coupons 
            WHERE code = %s AND is_active = TRUE 
            AND NOW() BETWEEN valid_from AND valid_until
            AND used_count < usage_limit
        """, (code,))
        
        coupon = cursor.fetchone()
        
        if not coupon:
            return jsonify({'valid': False, 'message': 'Invalid or expired coupon'})
        
        # Check minimum amount
        if amount < coupon['min_purchase_amount']:
            return jsonify({
                'valid': False, 
                'message': f'Minimum purchase amount: ₹{coupon["min_purchase_amount"]:.2f}'
            })
        
        # Check customer tier
        if coupon['applicable_customer_tiers']:
            eligible_tiers = coupon['applicable_customer_tiers'].split(',')
            if customer_tier not in eligible_tiers:
                return jsonify({
                    'valid': False, 
                    'message': f'Available for {", ".join(eligible_tiers).upper()} members only'
                })
        
        # Check category restrictions
        if coupon['applicable_categories'] and category_ids:
            applicable_cats = [int(x) for x in coupon['applicable_categories'].split(',')]
            if not any(cat_id in applicable_cats for cat_id in category_ids):
                return jsonify({
                    'valid': False, 
                    'message': 'Coupon not applicable for selected products'
                })
        
        # Check per-customer usage
        if customer_id:
            cursor.execute("""
                SELECT COUNT(*) as usage_count FROM bills 
                WHERE customer_id = %s AND coupon_code = %s
            """, (customer_id, code))
            usage = cursor.fetchone()
            if usage['usage_count'] >= coupon['usage_limit_per_customer']:
                return jsonify({'valid': False, 'message': 'Usage limit exceeded'})
        
        # Calculate discount
        if coupon['discount_type'] == 'percentage':
            discount = min((amount * coupon['discount_value']) / 100, coupon['max_discount_amount'])
        else:
            discount = min(coupon['discount_value'], amount)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'valid': True,
            'discount': float(discount),
            'coupon': {k: (float(v) if isinstance(v, Decimal) else v) for k, v in coupon.items()}
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bills', methods=['POST'])
def create_bill():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate bill number
        bill_number = f"BL{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate totals
        subtotal = sum(item['line_total'] for item in data['items'])
        tax_amount = data.get('tax_amount', subtotal * 0.18)
        net_amount = data.get('net_amount', subtotal + tax_amount)
        
        # Create bill
        cursor.execute("""
            INSERT INTO bills (
                bill_number, customer_id, cashier_name, subtotal, total_discount, 
                loyalty_points_used, loyalty_discount, coupon_discount, tax_amount, 
                round_off, net_amount, paid_amount, change_amount, payment_method, 
                coupon_code, loyalty_points_earned, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            bill_number, data.get('customer_id'), data.get('cashier_name', 'System'),
            subtotal, data.get('total_discount', 0), data.get('loyalty_points_used', 0),
            data.get('loyalty_discount', 0), data.get('coupon_discount', 0),
            tax_amount, data.get('round_off', 0), net_amount, data.get('paid_amount', net_amount),
            data.get('change_amount', 0), data.get('payment_method', 'cash'),
            data.get('coupon_code'), data.get('loyalty_points_earned', 0), data.get('notes')
        ))
        
        bill_id = cursor.lastrowid
        
        # Add bill items and update inventory
        for item in data['items']:
            cursor.execute("""
                INSERT INTO bill_items (
                    bill_id, product_id, quantity, unit_price, discount_percent, 
                    discount_amount, tax_rate, tax_amount, line_total, cost_price, 
                    profit_amount, batch_number, expiry_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                bill_id, item['product_id'], item['quantity'], item['unit_price'],
                item.get('discount_percent', 0), item.get('discount_amount', 0),
                item.get('tax_rate', 18), item.get('tax_amount', 0), item['line_total'],
                item.get('cost_price', 0), item.get('profit_amount', 0),
                item.get('batch_number'), item.get('expiry_date')
            ))
            
            # Update product stock
            cursor.execute("""
                UPDATE products SET 
                    current_stock = current_stock - %s,
                    total_sold = total_sold + %s,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (item['quantity'], item['quantity'], item['product_id']))
            
            # Add to sales history
            cursor.execute("""
                INSERT INTO sales_history (product_id, bill_id, quantity_sold, sale_price, 
                                         cost_price, profit_amount, customer_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                item['product_id'], bill_id, item['quantity'], item['unit_price'],
                item.get('cost_price', 0), item.get('profit_amount', 0), data.get('customer_id')
            ))
        
        # Update customer data
        if data.get('customer_id'):
            customer_id = data['customer_id']
            points_earned = data.get('loyalty_points_earned', 0)
            points_used = data.get('loyalty_points_used', 0)
            
            cursor.execute("""
                UPDATE customers SET 
                    loyalty_points = loyalty_points + %s - %s,
                    total_spent = total_spent + %s,
                    total_orders = total_orders + 1,
                    last_visit = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (points_earned, points_used, net_amount, customer_id))
            
            # Record loyalty transactions
            if points_earned > 0:
                cursor.execute("""
                    INSERT INTO loyalty_transactions (
                        customer_id, bill_id, transaction_type, points, description, 
                        reference_number, balance_after
                    ) SELECT %s, %s, 'earned', %s, 'Points earned from purchase', %s, loyalty_points
                    FROM customers WHERE id = %s
                """, (customer_id, bill_id, points_earned, bill_number, customer_id))
            
            if points_used > 0:
                cursor.execute("""
                    INSERT INTO loyalty_transactions (
                        customer_id, bill_id, transaction_type, points, description, 
                        reference_number, balance_after
                    ) SELECT %s, %s, 'redeemed', %s, 'Points redeemed for discount', %s, loyalty_points
                    FROM customers WHERE id = %s
                """, (customer_id, bill_id, -points_used, bill_number, customer_id))
        
        # Update coupon usage
        if data.get('coupon_code'):
            cursor.execute("UPDATE coupons SET used_count = used_count + 1 WHERE code = %s", 
                          (data['coupon_code'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'bill_number': bill_number,
            'bill_id': bill_id
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
            SELECT r.*, p.name as product_name, c.name as customer_name
            FROM ai_recommendations r
            LEFT JOIN products p ON r.product_id = p.id
            LEFT JOIN customers c ON r.customer_id = c.id
            WHERE r.status = 'active'
            ORDER BY r.priority DESC, r.created_date DESC
            LIMIT 50
        """)
        recommendations = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    
    print("🚀 Enhanced Retail Billing System")
    print("=" * 60)
    print("🏠 Application: http://localhost:5000")
    print("💾 Database: MySQL (inventory_ai)")
    print("🤖 AI Engine: Advanced Analytics")
    print("🛒 Features: Complete POS System")
    print("=" * 60)
    
    app.run(debug=True, port=5000, host='0.0.0.0')
