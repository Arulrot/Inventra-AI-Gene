import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

DB_PATH = "inventory.db"

class CategoryManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Category Management - Inventor AI Genie")
        self.geometry("900x600")

        self.editing_id = None
        
        self.create_tables()
        self.create_widgets()
        self.load_stats()
        self.load_categories()

    def db_connect(self):
        return sqlite3.connect(DB_PATH)

    def create_tables(self):
        conn = self.db_connect()
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS categories(
                        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )""")
        c.execute("""CREATE TABLE IF NOT EXISTS products(
                        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        category_id INTEGER,
                        FOREIGN KEY (category_id) REFERENCES categories(category_id)
                    )""")
        conn.commit()
        conn.close()

    def create_widgets(self):
        # --- Stats Frame ---
        stats_frame = ttk.Frame(self, padding=10)
        stats_frame.pack(fill="x")

        self.total_categories = tk.StringVar(value="0")
        self.total_products = tk.StringVar(value="0")
        self.active_categories = tk.StringVar(value="0")
        self.ai_insights = tk.StringVar(value="0")

        stats = [
            ("Total Categories", self.total_categories),
            ("Total Products", self.total_products),
            ("Active Categories", self.active_categories),
            ("AI Insights", self.ai_insights)
        ]
        for i, (label, var) in enumerate(stats):
            lf = ttk.LabelFrame(stats_frame, text=label, padding=10)
            lf.grid(row=0, column=i, padx=5, sticky="nsew")
            ttk.Label(lf, textvariable=var, font=("Segoe UI", 18, "bold")).pack()

        for i in range(len(stats)):
            stats_frame.columnconfigure(i, weight=1)

        # --- Search + Buttons ---
        control_frame = ttk.Frame(self, padding=10)
        control_frame.pack(fill="x")

        ttk.Button(control_frame, text="Add Category", command=self.show_add_modal).pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.search_var).pack(side="right")
        ttk.Label(control_frame, text="Search:").pack(side="right")
        self.search_var.trace("w", lambda *args: self.filter_categories())

        # --- Table ---
        table_frame = ttk.Frame(self, padding=10)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=("ID","Name","Description","Products","Created"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_edit)

        # --- Modal for Add/Edit ---
        self.modal = None

    def load_stats(self):
        conn = self.db_connect()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM categories")
        self.total_categories.set(c.fetchone()[0])

        c.execute("SELECT COUNT(*) FROM products")
        self.total_products.set(c.fetchone()[0])

        # Active categories = categories having products
        c.execute("""SELECT COUNT(DISTINCT category_id) FROM products WHERE category_id IS NOT NULL""")
        self.active_categories.set(c.fetchone()[0])

        # AI insights dummy
        self.ai_insights.set("0")

        conn.close()

    def load_categories(self):
        self.categories_data = []
        conn = self.db_connect()
        c = conn.cursor()
        c.execute("""SELECT c.category_id, c.name, c.description, 
                     COUNT(p.product_id) as product_count,
                     c.created_date
                     FROM categories c
                     LEFT JOIN products p ON c.category_id=p.category_id
                     GROUP BY c.category_id
                     ORDER BY c.category_id DESC""")
        rows = c.fetchall()
        conn.close()
        self.categories_data = rows
        self.display_categories(rows)

    def display_categories(self, rows):
        self.tree.delete(*self.tree.get_children())
        if not rows:
            return
        for r in rows:
            self.tree.insert("", "end", values=r)

    def filter_categories(self):
        term = self.search_var.get().lower()
        filtered = [row for row in self.categories_data if term in row[1].lower() or (row[2] and term in row[2].lower())]
        self.display_categories(filtered)

    def show_add_modal(self):
        self.editing_id = None
        self.show_modal("Add Category")

    def show_modal(self, title):
        if self.modal and tk.Toplevel.winfo_exists(self.modal):
            self.modal.destroy()
        self.modal = tk.Toplevel(self)
        self.modal.title(title)
        self.modal.geometry("400x250")
        self.modal.transient(self)
        self.modal.grab_set()

        ttk.Label(self.modal, text="Category Name:*").pack(pady=5)
        self.ent_name = ttk.Entry(self.modal)
        self.ent_name.pack(fill="x", padx=10)

        ttk.Label(self.modal, text="Description:").pack(pady=5)
        self.ent_desc = tk.Text(self.modal, height=5)
        self.ent_desc.pack(fill="x", padx=10)

        btn_frame = ttk.Frame(self.modal)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Cancel", command=self.modal.destroy).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Save", command=self.save_category).pack(side="left", padx=5)

    def save_category(self):
        name = self.ent_name.get().strip()
        desc = self.ent_desc.get("1.0", tk.END).strip()
        if not name:
            messagebox.showerror("Error", "Category name is required.")
            return
        
        conn = self.db_connect()
        c = conn.cursor()
        if self.editing_id is None:
            c.execute("INSERT INTO categories (name, description, created_date) VALUES (?, ?, ?)",
                      (name, desc, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        else:
            c.execute("UPDATE categories SET name=?, description=? WHERE category_id=?",
                      (name, desc, self.editing_id))
        conn.commit()
        conn.close()

        self.modal.destroy()
        self.load_categories()
        self.load_stats()
        messagebox.showinfo("Success", "Category saved successfully.")

    def on_edit(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])["values"]
        self.editing_id = item[0]
        self.show_modal("Edit Category")
        self.ent_name.insert(0, item[1])
        if item[2]:
            self.ent_desc.insert("1.0", item[2])

    def on_delete(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])["values"]
        cid = item[0]
        if messagebox.askyesno("Confirm", "Delete this category?"):
            conn = self.db_connect()
            c = conn.cursor()
            c.execute("DELETE FROM categories WHERE category_id=?", (cid,))
            conn.commit()
            conn.close()
            self.load_categories()
            self.load_stats()
            messagebox.showinfo("Deleted", "Category deleted successfully.")

if __name__ == "__main__":
    app = CategoryManager()
    app.mainloop()
