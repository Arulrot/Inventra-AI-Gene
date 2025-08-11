import mysql.connector
from mysql.connector import Error, errorcode
import time
import threading

# MySQL connection config
MYSQL_CONFIG = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'inventory_ai',
    'connection_timeout': 10,  # Add timeout
    'autocommit': True,        # Add autocommit
    'auth_plugin': 'mysql_native_password'  # Specify auth plugin
}

class AdvancedDescriptiveAnalytics:
    def __init__(self):
        """Initialize with enhanced connection verification"""
        print("🔍 Verifying MySQL connection...")
        self.conn = None
        
        # Test connection first
        if self._test_connection():
            self.conn = self._establish_connection()
            print("✅ Database connection established")
        else:
            raise ConnectionError("❌ Could not establish database connection")
            
        self.df_products = None
        self.df_sales = None
        self.df_suppliers = None
        self.df_categories = None
        self.load_and_prepare_data()
    
    def _test_connection(self):
        """Test connection with timeout protection"""
        try:
            # Test basic connection
            test_conn = mysql.connector.connect(
                user=MYSQL_CONFIG['user'],
                password=MYSQL_CONFIG['password'],
                host=MYSQL_CONFIG['host'],
                connection_timeout=5
            )
            
            if test_conn.is_connected():
                print("✅ Basic MySQL server connection successful")
                test_conn.close()
                
                # Test database-specific connection
                db_conn = mysql.connector.connect(**MYSQL_CONFIG)
                if db_conn.is_connected():
                    print("✅ Database 'inventory_ai' connection successful")
                    db_conn.close()
                    return True
                    
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("❌ Access denied - check username/password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("❌ Database 'inventory_ai' does not exist")
            elif err.errno == 2003:
                print("❌ Can't connect to MySQL server - check if MySQL service is running")
            else:
                print(f"❌ MySQL Error: {err}")
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
        
        return False
    
    def _establish_connection(self):
        """Establish connection with retry mechanism"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Connection attempt {attempt + 1}/{max_retries}")
                conn = mysql.connector.connect(**MYSQL_CONFIG)
                
                if conn.is_connected():
                    return conn
                    
            except mysql.connector.Error as err:
                print(f"❌ Attempt {attempt + 1} failed: {err}")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    
        raise ConnectionError("Failed to establish connection after all retries")

    def load_and_prepare_data(self):
        """Load and preprocess data with enhanced error handling"""
        print("📊 Loading data from database...")
        
        try:
            # Verify connection is still active
            if not self.conn.is_connected():
                print("⚠️ Connection lost, reconnecting...")
                self.conn = self._establish_connection()
            
            # Load products with timeout protection
            print("   Loading products...")
            products_query = """
            SELECT p.*, c.name as category_name, s.name as supplier_name 
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            LIMIT 1000
            """
            
            cursor = self.conn.cursor()
            cursor.execute(products_query)
            
            # Check if query returned results
            if cursor.description:
                import pandas as pd
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                self.df_products = pd.DataFrame(data, columns=columns)
                print(f"   ✅ Loaded {len(self.df_products)} products")
            else:
                print("   ⚠️ No product data found")
                self.df_products = pd.DataFrame()
            
            cursor.close()
            
            # Continue with other data loading...
            self._load_remaining_data()
            
            # Data preprocessing
            self._preprocess_data()
            print("✅ Data loaded and preprocessed successfully!")
            
        except mysql.connector.Error as err:
            print(f"❌ MySQL error during data loading: {err}")
            raise
        except Exception as e:
            print(f"❌ Data loading error: {e}")
            raise
    
    def _load_remaining_data(self):
        """Load remaining data tables"""
        try:
            cursor = self.conn.cursor()
            
            # Load sales data
            print("   Loading sales history...")
            sales_query = """
            SELECT sh.*, p.name as product_name, p.price, c.name as category_name
            FROM sales_history sh
            JOIN products p ON sh.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            LIMIT 1000
            """
            cursor.execute(sales_query)
            
            if cursor.description:
                import pandas as pd
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                self.df_sales = pd.DataFrame(data, columns=columns)
                print(f"   ✅ Loaded {len(self.df_sales)} sales records")
            else:
                self.df_sales = pd.DataFrame()
            
            # Load suppliers and categories
            cursor.execute("SELECT * FROM suppliers")
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                self.df_suppliers = pd.DataFrame(data, columns=columns)
                print(f"   ✅ Loaded {len(self.df_suppliers)} suppliers")
            
            cursor.execute("SELECT * FROM categories")
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                self.df_categories = pd.DataFrame(data, columns=columns)
                print(f"   ✅ Loaded {len(self.df_categories)} categories")
            
            cursor.close()
            
        except mysql.connector.Error as err:
            print(f"❌ Error loading remaining data: {err}")
            raise

    # ... rest of your existing methods remain the same ...

# Enhanced main function with better error handling
def main():
    """Enhanced main execution function"""
    print("🎨 ADVANCED DESCRIPTIVE ANALYTICS FOR INVENTORY MANAGEMENT")
    print("=" * 80)
    
    try:
        # Pre-flight checks
        print("🔍 Running pre-flight checks...")
        
        # Check MySQL service (Windows)
        import subprocess
        try:
            result = subprocess.run(['sc', 'query', 'mysql80'], 
                                  capture_output=True, text=True, timeout=5)
            if 'RUNNING' in result.stdout:
                print("✅ MySQL service is running")
            else:
                print("❌ MySQL service is not running")
                print("💡 Start MySQL service: net start mysql80")
                return
        except Exception:
            print("⚠️ Could not check MySQL service status")
        
        # Initialize analytics system
        print("\n🚀 Initializing analytics system...")
        analytics = AdvancedDescriptiveAnalytics()
        
        # Run complete analysis
        analytics.run_complete_analysis()
        
    except ConnectionError as ce:
        print(f"\n❌ Connection Error: {ce}")
        print("\n💡 TROUBLESHOOTING STEPS:")
        print("1. Check if MySQL service is running: net start mysql80")
        print("2. Verify credentials (root/root)")
        print("3. Ensure database 'inventory_ai' exists")
        print("4. Check if port 3306 is open")
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
