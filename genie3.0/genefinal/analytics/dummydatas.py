import mysql.connector
import random
from datetime import datetime, timedelta
import uuid

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

def clear_existing_data():
    """Clear existing data from all tables (optional - for clean start)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("🧹 Clearing existing data...")
        
        # Disable foreign key checks temporarily
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Clear tables in reverse order to avoid foreign key conflicts
        tables = ['ai_recommendations', 'sales_history', 'products', 'categories', 'suppliers']
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
            print(f"   Cleared {table}")
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        conn.commit()
        print("✅ Data cleared successfully!")
        
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def generate_suppliers_data():
    """Generate 15 supplier records"""
    print("🏭 Generating suppliers data...")
    
    suppliers_data = [
        ('SUPP001', 'TechWorld Electronics Ltd', '555-0101', 'orders@techworld.com', '123 Tech Street, Silicon Valley, CA 94025'),
        ('SUPP002', 'Global Fashion Distributors', '555-0102', 'sales@globalfashion.com', '456 Style Avenue, New York, NY 10001'),
        ('SUPP003', 'Fresh Foods Wholesale Inc', '555-0103', 'procurement@freshfoods.com', '789 Market Lane, Chicago, IL 60601'),
        ('SUPP004', 'BookMasters Publishing', '555-0104', 'wholesale@bookmasters.com', '321 Literature Blvd, Boston, MA 02101'),
        ('SUPP005', 'HomeCore Solutions Ltd', '555-0105', 'orders@homecore.com', '654 Garden Way, Portland, OR 97201'),
        ('SUPP006', 'SportZone Equipment Co', '555-0106', 'bulk@sportzone.com', '987 Athletic Drive, Denver, CO 80201'),
        ('SUPP007', 'Beauty Essentials Supply', '555-0107', 'sales@beautyessentials.com', '147 Glamour Street, Los Angeles, CA 90001'),
        ('SUPP008', 'AutoParts Direct LLC', '555-0108', 'orders@autopartsdirect.com', '258 Motor Avenue, Detroit, MI 48201'),
        ('SUPP009', 'Premium Electronics Corp', '555-0109', 'contact@premiumelectronics.com', '369 Innovation Park, Austin, TX 78701'),
        ('SUPP010', 'Organic Health Products', '555-0110', 'info@organichealth.com', '741 Wellness Road, Seattle, WA 98101'),
        ('SUPP011', 'Industrial Tools & More', '555-0111', 'sales@industrialtools.com', '852 Workshop Street, Cleveland, OH 44101'),
        ('SUPP012', 'Kids & Toys Paradise', '555-0112', 'orders@kidstoysparadise.com', '963 Playground Ave, Orlando, FL 32801'),
        ('SUPP013', 'Office Supplies Central', '555-0113', 'wholesale@officesupplies.com', '159 Business Plaza, Phoenix, AZ 85001'),
        ('SUPP014', 'Outdoor Adventure Gear', '555-0114', 'gear@outdooradventure.com', '357 Mountain Trail, Salt Lake City, UT 84101'),
        ('SUPP015', 'Digital Solutions Provider', '555-0115', 'support@digitalsolutions.com', '468 Software Park, San Francisco, CA 94102')
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for supplier in suppliers_data:
            cursor.execute("""
                INSERT INTO suppliers (supplier_id, name, phone, email, address) 
                VALUES (%s, %s, %s, %s, %s)
            """, supplier)
        
        conn.commit()
        print(f"   ✅ Inserted {len(suppliers_data)} suppliers")
        
    except Exception as e:
        print(f"   ❌ Error inserting suppliers: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def generate_categories_data():
    """Generate 15 category records"""
    print("📂 Generating categories data...")
    
    categories_data = [
        ('Electronics', 'Electronic devices, gadgets, and accessories'),
        ('Clothing & Fashion', 'Apparel, shoes, and fashion accessories'),
        ('Food & Beverages', 'Fresh food, packaged goods, and drinks'),
        ('Books & Media', 'Books, magazines, DVDs, and digital media'),
        ('Home & Garden', 'Furniture, decor, and gardening supplies'),
        ('Sports & Fitness', 'Exercise equipment and sports gear'),
        ('Beauty & Personal Care', 'Cosmetics, skincare, and hygiene products'),
        ('Automotive', 'Car parts, accessories, and maintenance items'),
        ('Health & Wellness', 'Vitamins, supplements, and health products'),
        ('Tools & Hardware', 'Hand tools, power tools, and hardware supplies'),
        ('Toys & Games', 'Children toys, board games, and puzzles'),
        ('Office Supplies', 'Stationery, office equipment, and supplies'),
        ('Outdoor & Recreation', 'Camping gear, outdoor equipment, and recreation items'),
        ('Pet Supplies', 'Pet food, toys, and care products'),
        ('Arts & Crafts', 'Art supplies, craft materials, and hobby items')
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for category in categories_data:
            cursor.execute("""
                INSERT INTO categories (name, description) 
                VALUES (%s, %s)
            """, category)
        
        conn.commit()
        print(f"   ✅ Inserted {len(categories_data)} categories")
        
    except Exception as e:
        print(f"   ❌ Error inserting categories: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def generate_products_data():
    """Generate 15 product records"""
    print("🏷️ Generating products data...")
    
    # Realistic product data with category mapping
    products_data = [
        ('PROD001', 'iPhone 15 Pro Max 256GB', 1, 1, 1299.99, 25, 5, 730),
        ('PROD002', 'Samsung 65" 4K Smart TV', 1, 1, 899.99, 12, 3, 1095),
        ('PROD003', 'Nike Air Max Running Shoes', 2, 2, 129.99, 45, 10, 365),
        ('PROD004', 'Organic Quinoa 2lb Bag', 3, 3, 12.99, 180, 20, 90),
        ('PROD005', 'The Psychology of Money Book', 4, 4, 16.99, 75, 15, 1825),
        ('PROD006', 'IKEA Office Chair Ergonomic', 5, 5, 199.99, 18, 4, 1095),
        ('PROD007', 'Adidas Gym Dumbbell Set', 6, 6, 89.99, 32, 8, 1825),
        ('PROD008', 'L\'Oreal Anti-Aging Serum', 7, 7, 24.99, 95, 12, 180),
        ('PROD009', 'Bosch Car Battery 12V', 8, 8, 149.99, 22, 5, 1095),
        ('PROD010', 'Whey Protein Powder 5lb', 9, 10, 49.99, 67, 10, 365),
        ('PROD011', 'DeWalt Cordless Drill Kit', 10, 11, 179.99, 15, 3, 1825),
        ('PROD012', 'LEGO Creator Expert Set', 11, 12, 299.99, 8, 2, 1825),
        ('PROD013', 'HP LaserJet Printer Toner', 12, 13, 89.99, 55, 10, 1095),
        ('PROD014', 'Coleman Camping Tent 4-Person', 13, 14, 159.99, 28, 6, 1095),
        ('PROD015', 'Acrylic Paint Set Professional', 15, 15, 34.99, 42, 8, 1095)
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for i, product_base in enumerate(products_data):
            product_id, name, category_id, supplier_id, price, stock, min_stock, shelf_life_days = product_base
            
            # Generate realistic dates and sales data
            date_added = datetime.now() - timedelta(days=random.randint(30, 365))
            expiry_date = datetime.now() + timedelta(days=shelf_life_days + random.randint(-30, 60))
            total_sold = random.randint(10, 500)
            current_stock = stock + random.randint(-10, 20)  # Some variation
            current_stock = max(0, current_stock)  # Ensure non-negative
            
            cursor.execute("""
                INSERT INTO products 
                (product_id, name, category_id, supplier_id, price, current_stock, 
                 minimum_stock, expiry_date, date_added, total_sold) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (product_id, name, category_id, supplier_id, price, current_stock, 
                  min_stock, expiry_date, date_added, total_sold))
        
        conn.commit()
        print(f"   ✅ Inserted {len(products_data)} products")
        
    except Exception as e:
        print(f"   ❌ Error inserting products: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def generate_sales_history_data():
    """Generate 15 sales history records"""
    print("💰 Generating sales history data...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get product IDs and prices for realistic sales data
        cursor.execute("SELECT id, price FROM products")
        products = cursor.fetchall()
        
        sales_data = []
        
        for i in range(15):
            product = random.choice(products)
            product_id, product_price = product
            
            # Generate realistic sales data
            quantity_sold = random.randint(1, 10)
            sale_date = datetime.now() - timedelta(
                days=random.randint(1, 180),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Add some price variation (discounts/premiums)
            price_variation = random.uniform(0.8, 1.2)
            amount = product_price * quantity_sold * price_variation
            
            sales_data.append((product_id, quantity_sold, sale_date, amount))
        
        # Insert sales data
        for sale in sales_data:
            cursor.execute("""
                INSERT INTO sales_history (product_id, quantity_sold, sale_date, amount) 
                VALUES (%s, %s, %s, %s)
            """, sale)
        
        conn.commit()
        print(f"   ✅ Inserted {len(sales_data)} sales records")
        
    except Exception as e:
        print(f"   ❌ Error inserting sales history: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def generate_ai_recommendations_data():
    """Generate 15 AI recommendation records"""
    print("🤖 Generating AI recommendations data...")
    
    # Realistic AI recommendation types and messages
    recommendation_templates = [
        ('RESTOCK', 'Product is running low on stock. Consider reordering {} units.', [2, 3, 4, 5]),
        ('LOW_STOCK', 'Stock level critical for {}. Immediate restock recommended.', [4, 5]),
        ('EXPIRY_WARNING', 'Product {} expires soon. Consider promotion or discount.', [3, 4, 5]),
        ('PRICE_OPTIMIZATION', 'Price adjustment recommended for {} to increase sales.', [2, 3]),
        ('PROMOTION', 'High-demand product {}. Consider featuring in promotions.', [1, 2, 3]),
        ('SLOW_MOVING', 'Product {} has slow sales. Review pricing or marketing strategy.', [2, 3, 4]),
        ('OVERSTOCK', 'Excess inventory detected for {}. Reduce future orders.', [1, 2]),
        ('SEASONAL_TREND', 'Seasonal demand pattern detected for {}. Adjust inventory accordingly.', [2, 3]),
        ('SUPPLIER_PERFORMANCE', 'Supplier reliability issue detected for {}. Consider alternative suppliers.', [3, 4]),
        ('CATEGORY_ANALYSIS', 'Category performance analysis suggests optimizing {} product mix.', [2, 3]),
        ('CUSTOMER_PREFERENCE', 'Customer demand trending upward for {}. Increase stock levels.', [2, 3, 4]),
        ('PROFIT_MARGIN', 'Profit margin optimization opportunity identified for {}.', [2, 3]),
        ('INVENTORY_TURNOVER', 'Low inventory turnover for {}. Consider bundling or discounts.', [2, 3, 4]),
        ('QUALITY_ALERT', 'Quality concern pattern detected for {}. Review with supplier.', [4, 5]),
        ('DEMAND_FORECAST', 'Predictive analytics suggests increased demand for {} next quarter.', [1, 2, 3])
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get product IDs and names for realistic recommendations
        cursor.execute("SELECT id, name FROM products")
        products = cursor.fetchall()
        
        recommendations_data = []
        
        for i in range(15):
            product = random.choice(products)
            product_id, product_name = product
            
            # Choose random recommendation template
            rec_type, message_template, priorities = random.choice(recommendation_templates)
            priority = random.choice(priorities)
            
            # Format message with product name
            message = message_template.format(product_name)
            
            # Random status
            status = random.choice(['active', 'pending', 'completed', 'dismissed'])
            
            # Random creation date (within last 30 days)
            created_date = datetime.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            recommendations_data.append((rec_type, product_id, message, priority, status, created_date))
        
        # Insert recommendations
        for rec in recommendations_data:
            cursor.execute("""
                INSERT INTO ai_recommendations 
                (type, product_id, message, priority, status, created_date) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, rec)
        
        conn.commit()
        print(f"   ✅ Inserted {len(recommendations_data)} AI recommendations")
        
    except Exception as e:
        print(f"   ❌ Error inserting AI recommendations: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def verify_data():
    """Verify the inserted data"""
    print("\n📊 Verifying inserted data...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        tables = ['suppliers', 'categories', 'products', 'sales_history', 'ai_recommendations']
        
        print("\n" + "="*50)
        print("📋 DATA INSERTION SUMMARY")
        print("="*50)
        
        total_records = 0
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_records += count
            print(f"   {table:20} : {count:3d} records")
        
        print("-"*50)
        print(f"   {'TOTAL RECORDS':20} : {total_records:3d}")
        print("="*50)
        
        # Show sample data from each table
        print("\n🔍 SAMPLE DATA PREVIEW:")
        print("-"*50)
        
        # Sample products
        cursor.execute("""
            SELECT p.name, c.name as category, s.name as supplier, p.price, p.current_stock
            FROM products p 
            JOIN categories c ON p.category_id = c.id 
            JOIN suppliers s ON p.supplier_id = s.id 
            LIMIT 3
        """)
        products_sample = cursor.fetchall()
        
        print("\n📦 Sample Products:")
        for product in products_sample:
            name, category, supplier, price, stock = product
            print(f"   • {name[:25]:25} | {category[:15]:15} | ${price:7.2f} | Stock: {stock}")
        
        # Sample sales
        cursor.execute("""
            SELECT p.name, sh.quantity_sold, sh.amount, DATE(sh.sale_date)
            FROM sales_history sh
            JOIN products p ON sh.product_id = p.id
            ORDER BY sh.sale_date DESC
            LIMIT 3
        """)
        sales_sample = cursor.fetchall()
        
        print("\n💰 Sample Sales:")
        for sale in sales_sample:
            product, qty, amount, date = sale
            print(f"   • {product[:25]:25} | Qty: {qty:2d} | ${amount:7.2f} | {date}")
        
        # Sample recommendations
        cursor.execute("""
            SELECT type, message, priority, status
            FROM ai_recommendations
            ORDER BY priority DESC, created_date DESC
            LIMIT 3
        """)
        recommendations_sample = cursor.fetchall()
        
        print("\n🤖 Sample AI Recommendations:")
        for rec in recommendations_sample:
            rec_type, message, priority, status = rec
            print(f"   • {rec_type:15} | Priority: {priority} | {status:10} | {message[:40]}...")
        
        print("\n✅ Data verification completed!")
        
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to generate all dummy data"""
    print("🚀 INVENTORY DATABASE DUMMY DATA GENERATOR")
    print("=" * 60)
    print("📊 Generating 15 records for each table...")
    print("=" * 60)
    
    try:
        # Ask user if they want to clear existing data
        clear_data = input("\n🧹 Clear existing data first? (y/N): ").lower().strip()
        if clear_data == 'y':
            clear_existing_data()
        
        print(f"\n⚡ Starting data generation process...")
        print("-" * 40)
        
        # Generate data for all tables in correct order (respecting foreign keys)
        generate_suppliers_data()
        generate_categories_data()
        generate_products_data()
        generate_sales_history_data()
        generate_ai_recommendations_data()
        
        print("\n" + "="*60)
        print("🎉 DUMMY DATA GENERATION COMPLETED!")
        print("="*60)
        
        # Verify the data
        verify_data()
        
        print(f"\n💡 Your database is now populated with realistic dummy data!")
        print(f"   • 15 suppliers with contact information")
        print(f"   • 15 categories across different industries") 
        print(f"   • 15 products with pricing and inventory data")
        print(f"   • 15 sales transactions with realistic dates")
        print(f"   • 15 AI recommendations with various priorities")
        
        print(f"\n🚀 Ready for analytics! Run your inventory analysis now.")
        
    except KeyboardInterrupt:
        print("\n\n❌ Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
