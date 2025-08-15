import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta

DB_PATH = 'inventory.db'

class ProductManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Product Management Center")
        self.geometry("1200x700")
        self.current_mode = 'add'
        self.editing_product_dbid = None

        self.create_widgets()
        self.load_categories()
        self.load_suppliers()
        self.load_products_table()
        self.reset_form()

    def db_connect(self):
        return sqlite3.connect(DB_PATH)

    def create_widgets(self):
        # Mode Switch buttons
        mode_frame = ttk.Frame(self, padding=5)
        mode_frame.pack(fill='x')

        self.btn_add_mode = ttk.Button(mode_frame, text="Add New Product", command=lambda: self.switch_mode('add'))
        self.btn_add_mode.pack(side='left', padx=5)

        self.btn_edit_mode = ttk.Button(mode_frame, text="Edit Product", command=lambda: self.switch_mode('edit'))
        self.btn_edit_mode.pack(side='left', padx=5)

        # Form Frame
        form_frame = ttk.LabelFrame(self, text="Product Form", padding=10)
        form_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        # Form fields
        self.ent_product_id = self.add_labeled_entry(form_frame, "Product ID")
        self.ent_name = self.add_labeled_entry(form_frame, "Product Name")
        self.cmb_category = self.add_labeled_combobox(form_frame, "Category")
        self.cmb_supplier = self.add_labeled_combobox(form_frame, "Supplier")
        self.ent_price = self.add_labeled_entry(form_frame, "Price (₹)")
        self.ent_stock = self.add_labeled_entry(form_frame, "Current Stock")
        self.ent_min_stock = self.add_labeled_entry(form_frame, "Min Stock")
        self.ent_date_added = self.add_labeled_entry(form_frame, "Date Added (YYYY-MM-DD)")
        self.ent_expiry = self.add_labeled_entry(form_frame, "Expiry Date (YYYY-MM-DD)")

        # AI Suggestions
        ttk.Label(form_frame, text="AI Suggestions:").pack(anchor='w', pady=(10,0))
        self.txt_ai = tk.Text(form_frame, height=6, wrap='word')
        self.txt_ai.pack(fill='x')

        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Reset", command=self.reset_form).pack(side='left', padx=5)
        self.btn_submit = ttk.Button(btn_frame, text="Add Product", command=self.submit_product)
        self.btn_submit.pack(side='left', padx=5)

        # Table Frame
        table_frame = ttk.LabelFrame(self, text="Current Products", padding=5)
        table_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Search bar
        search_frame = ttk.Frame(table_frame)
        search_frame.pack(fill='x')
        self.ent_search = ttk.Entry(search_frame)
        self.ent_search.pack(side='left', fill='x', expand=True)
        ttk.Button(search_frame, text="Search", command=self.filter_table).pack(side='left')

        # Treeview table
        self.tree = ttk.Treeview(table_frame, columns=("id","name","category","stock","price","status","added","expiry"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col.capitalize())
        self.tree.pack(fill='both', expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_table_select)

    def add_labeled_entry(self, parent, label):
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)
        ttk.Label(frame, text=label, width=20).pack(side='left')
        entry = ttk.Entry(frame)
        entry.pack(side='left', fill='x', expand=True)
        return entry

    def add_labeled_combobox(self, parent, label):
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)
        ttk.Label(frame, text=label, width=20).pack(side='left')
        cb = ttk.Combobox(frame, state='readonly')
        cb.pack(side='left', fill='x', expand=True)
        return cb

    def switch_mode(self, mode):
        self.current_mode = mode
        if mode == 'add':
            self.btn_submit.config(text="Add Product")
            self.reset_form()
        else:
            self.btn_submit.config(text="Update Product")

    def load_categories(self):
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute("SELECT category_id, name FROM categories")
        cats = cur.fetchall()
        conn.close()
        self.cmb_category['values'] = [f"{r[0]} - {r[1]}" for r in cats]

    def load_suppliers(self):
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute("SELECT supplier_id, name FROM suppliers")
        sups = cur.fetchall()
        conn.close()
        self.cmb_supplier['values'] = [f"{r[0]} - {r[1]}" for r in sups]

    def load_products_table(self, search_term=None):
        self.tree.delete(*self.tree.get_children())
        conn = self.db_connect()
        cur = conn.cursor()
        query = """SELECT product_id,name,(SELECT name FROM categories WHERE category_id=p.category_id),
                   current_stock,price,minimum_stock,date_added,expiry_date,rowid FROM products p"""
        cur.execute(query)
        products = cur.fetchall()
        conn.close()

        self.products_data = products
        for p in products:
            status = self.get_product_status(p)
            self.tree.insert('', 'end', values=(p[0], p[1], p[2], p[3], p[4], status, p[6], p[7]))

    def get_product_status(self, p):
        stock = p[3]
        min_stock = p[5]
        expiry = p[7]
        if stock == 0:
            return "Out of Stock"
        if stock <= min_stock:
            return "Low Stock"
        if expiry:
            try:
                days_left = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
                if days_left <= 0: return "Expired"
                if days_left <= 30: return "Expiring Soon"
            except:
                pass
        return "In Stock"

    def filter_table(self):
        term = self.ent_search.get().lower()
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute("""SELECT product_id,name,(SELECT name FROM categories WHERE category_id=p.category_id),
                        current_stock,price,minimum_stock,date_added,expiry_date,rowid
                       FROM products p
                       WHERE lower(name) LIKE ? OR lower(product_id) LIKE ?""",
                    (f"%{term}%", f"%{term}%"))
        results = cur.fetchall()
        conn.close()
        self.tree.delete(*self.tree.get_children())
        for p in results:
            status = self.get_product_status(p)
            self.tree.insert('', 'end', values=(p[0], p[1], p[2], p[3], p[4], status, p[6], p[7]))

    def on_table_select(self, event):
        if self.current_mode == 'edit':
            selected = self.tree.selection()
            if not selected: return
            values = self.tree.item(selected[0])['values']
            pid = values[0]

            conn = self.db_connect()
            cur = conn.cursor()
            cur.execute("SELECT rowid,* FROM products WHERE product_id=?", (pid,))
            row = cur.fetchone()
            conn.close()
            if row:
                self.editing_product_dbid = row[0]
                self.ent_product_id.delete(0, tk.END)
                self.ent_product_id.insert(0, row[1])
                self.ent_name.delete(0, tk.END)
                self.ent_name.insert(0, row[2])
                self.cmb_category.set(str(row[3]))
                self.cmb_supplier.set(str(row[4]))
                self.ent_price.delete(0, tk.END)
                self.ent_price.insert(0, row[5])
                self.ent_stock.delete(0, tk.END)
                self.ent_stock.insert(0, row[6])
                self.ent_min_stock.delete(0, tk.END)
                self.ent_min_stock.insert(0, row[7])
                self.ent_date_added.delete(0, tk.END)
                self.ent_date_added.insert(0, row[9])
                if row[8]:
                    self.ent_expiry.delete(0, tk.END)
                    self.ent_expiry.insert(0, row[8])
                self.update_ai_suggestions()

    def submit_product(self):
        pid = self.ent_product_id.get()
        name = self.ent_name.get()
        cat_id = int(self.cmb_category.get().split(" - ")[0]) if self.cmb_category.get() else None
        sup_id = int(self.cmb_supplier.get().split(" - ")[0]) if self.cmb_supplier.get() else None
        price = float(self.ent_price.get())
        stock = int(self.ent_stock.get())
        min_stock = int(self.ent_min_stock.get())
        date_added = self.ent_date_added.get()
        expiry = self.ent_expiry.get() or None

        conn = self.db_connect()
        cur = conn.cursor()
        if self.current_mode == 'add':
            cur.execute("""INSERT INTO products(product_id,name,category_id,supplier_id,price,current_stock,minimum_stock,expiry_date,date_added)
                           VALUES (?,?,?,?,?,?,?,?,?)""",
                           (pid,name,cat_id,sup_id,price,stock,min_stock,expiry,date_added))
        else:
            cur.execute("""UPDATE products SET product_id=?,name=?,category_id=?,supplier_id=?,price=?,current_stock=?,minimum_stock=?,expiry_date=?,date_added=?
                           WHERE rowid=?""",
                           (pid,name,cat_id,sup_id,price,stock,min_stock,expiry,date_added,self.editing_product_dbid))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", f"Product {'added' if self.current_mode=='add' else 'updated'} successfully")
        self.load_products_table()
        self.reset_form()

    def reset_form(self):
        self.editing_product_dbid = None
        self.ent_product_id.delete(0, tk.END)
        self.ent_product_id.insert(0, f"PRD{datetime.now().strftime('%H%M%S')}")
        self.ent_name.delete(0, tk.END)
        self.cmb_category.set('')
        self.cmb_supplier.set('')
        self.ent_price.delete(0, tk.END)
        self.ent_stock.delete(0, tk.END)
        self.ent_min_stock.delete(0, tk.END)
        self.ent_min_stock.insert(0, '5')
        self.ent_date_added.delete(0, tk.END)
        self.ent_date_added.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_expiry.delete(0, tk.END)
        self.txt_ai.delete(1.0, tk.END)
        self.update_ai_suggestions()

    def update_ai_suggestions(self):
        stock = int(self.ent_stock.get() or "0")
        expiry = self.ent_expiry.get()
        suggestions = []
        suggestions.append(f"🔍 Stock level: {stock} units")
        if stock == 0:
            suggestions.append("⚠️ Zero stock - restock soon")
        elif stock <= 10:
            suggestions.append("⚠️ Low stock - early alerts enabled")
        else:
            suggestions.append("✅ Good stock level")

        if expiry:
            try:
                days_to_exp = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
                if days_to_exp <= 0:
                    suggestions.append("🚨 Product expired!")
                elif days_to_exp <= 30:
                    suggestions.append(f"⏰ Expires in {days_to_exp} days")
                else:
                    suggestions.append(f"📅 {days_to_exp} days shelf life")
            except:
                pass

        self.txt_ai.config(state='normal')
        self.txt_ai.delete(1.0, tk.END)
        for s in suggestions:
            self.txt_ai.insert(tk.END, s + "\n")
        self.txt_ai.config(state='disabled')

if __name__ == "__main__":
    app = ProductManager()
    app.mainloop()
