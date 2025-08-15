import sqlite3
from datetime import datetime, timedelta

DB_PATH = "inventory.db"

def create_and_seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ===== ADMIN TABLES =====
    cur.execute("""
    CREATE TABLE IF NOT EXISTS suppliers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories(
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products(
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT UNIQUE,
        name TEXT NOT NULL,
        category_id INTEGER,
        supplier_id INTEGER,
        price REAL NOT NULL,
        current_stock INTEGER DEFAULT 0,
        minimum_stock INTEGER DEFAULT 0,
        expiry_date TEXT,
        date_added TEXT DEFAULT (DATE('now')),
        total_sold INTEGER DEFAULT 0,
        FOREIGN KEY (category_id) REFERENCES categories(category_id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bills(
        bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        total_amount REAL NOT NULL,
        created_date TEXT NOT NULL
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ai_recommendations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        created_date TEXT NOT NULL,
        priority INTEGER DEFAULT 1,
        type TEXT,
        product_name TEXT,
        product_id INTEGER,
        current_stock INTEGER
    )""")

    # ===== BILLING / POS TABLES =====
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT UNIQUE NOT NULL,
        email TEXT,
        loyalty_points INTEGER DEFAULT 0
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS coupons(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_type TEXT NOT NULL CHECK(discount_type IN ('percentage', 'fixed')),
        discount_value REAL NOT NULL,
        min_amount REAL DEFAULT 0,
        max_discount REAL DEFAULT 0,
        usage_limit INTEGER DEFAULT 1,
        used_count INTEGER DEFAULT 0,
        valid_until TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales(
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE,
        customer_id INTEGER,
        customer_name TEXT,
        customer_contact TEXT,
        customer_email TEXT,
        bill_amount REAL,
        discount_amount REAL,
        coupon_discount REAL,
        points_used REAL,
        net_amount REAL,
        points_earned INTEGER,
        created_date TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sale_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price REAL,
        FOREIGN KEY(sale_id) REFERENCES sales(sale_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )""")

    # ===== SEED SAMPLE DATA =====
    cur.execute("DELETE FROM suppliers")
    cur.execute("DELETE FROM categories")
    cur.execute("DELETE FROM products")
    cur.execute("DELETE FROM bills")
    cur.execute("DELETE FROM ai_recommendations")
    cur.execute("DELETE FROM customers")
    cur.execute("DELETE FROM coupons")
    cur.execute("DELETE FROM sales")
    cur.execute("DELETE FROM sale_items")

    suppliers = [
        ("SUP1001", "Fresh Farms Ltd", "9876543210", "contact@freshfarms.com", "123 Market Street"),
        ("SUP1002", "Tech Parts Co", "9123456780", "sales@techparts.com", "456 Industrial Ave"),
        ("SUP1003", "Bakers Hub", "9998887770", "hello@bakershub.com", "789 Baker Lane"),
    ]
    cur.executemany("INSERT INTO suppliers (supplier_id, name, phone, email, address) VALUES (?, ?, ?, ?, ?)", suppliers)

    categories = [
        ("Fruits", "Fresh and seasonal fruits"),
        ("Electronics", "Electronic components and gadgets"),
        ("Bakery", "Baked goods and confectionery"),
    ]
    cur.executemany("INSERT INTO categories (name, description) VALUES (?, ?)", categories)

    products = [
        ("P1001", "Apples", 1, 1, 120.0, 50, 10, (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d")),
        ("P1002", "Bananas", 1, 1, 60.0, 8, 15, (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")),
        ("P2001", "Resistor Pack", 2, 2, 5.0, 500, 50, None),
        ("P2002", "Capacitor Kit", 2, 2, 20.0, 5, 20, None),
        ("P3001", "Chocolate Cake", 3, 3, 350.0, 2, 5, (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")),
    ]
    cur.executemany("""
        INSERT INTO products (product_code, name, category_id, supplier_id, price, current_stock, minimum_stock, expiry_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, products)

    bills = [
        ("John Doe", 500.0, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Sarah Lee", 150.0, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    ]
    cur.executemany("INSERT INTO bills (customer_name, total_amount, created_date) VALUES (?, ?, ?)", bills)

    ai_recs = [
        ("Restock bananas soon – low stock warning.", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 4, "LOW_STOCK", "Bananas", 2, 8),
        ("Chocolate Cake is near expiry!", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 5, "EXPIRY_WARNING", "Chocolate Cake", 5, 2),
        ("Consider promoting Apples – expiring within 30 days.", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 3, "EXPIRY_WARNING", "Apples", 1, 50),
        ("Resistor Pack is stagnant; review pricing or bundle.", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 2, "NON_MOVABLE", "Resistor Pack", 3, 500),
    ]
    cur.executemany("""
        INSERT INTO ai_recommendations (message, created_date, priority, type, product_name, product_id, current_stock)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ai_recs)

    # Sample customers
    customers = [
        ("John Doe", "9999990000", "john@example.com", 10),
        ("Mary Smith", "8888880000", "mary@example.com", 5)
    ]
    cur.executemany("""INSERT INTO customers (name, contact, email, loyalty_points)
                       VALUES (?, ?, ?, ?)""", customers)

    # Sample coupon
    cur.execute("""INSERT INTO coupons (code, discount_type, discount_value, min_amount, max_discount, usage_limit, used_count, valid_until)
                   VALUES ('WELCOME10', 'percentage', 10, 100, 50, 100, 0, ?)""",
                ((datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),))

    # Sample sale and items
    sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""INSERT INTO sales (invoice_no, customer_id, customer_name, customer_contact, customer_email,
                                      bill_amount, discount_amount, coupon_discount, points_used, net_amount, points_earned, created_date)
                   VALUES ('INV1001', 1, 'John Doe', '9999990000', 'john@example.com',
                           500, 25, 10, 5, 460, 4, ?)""", (sale_date,))
    sale_id = cur.lastrowid
    # Sale items
    cur.execute("INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (sale_id, 1, 2, 120))
    cur.execute("INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (sale_id, 2, 5, 60))

    conn.commit()
    conn.close()
    print("✅ inventory.db created with admin + billing tables and sample data.")

if __name__ == "__main__":
    create_and_seed()
