import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "inventory.db"

class CouponManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Coupon Manager - Inventa AI Genie")
        self.geometry("900x500")
        self.create_db()
        self.create_ui()
        self.load_coupons()

    def db_connect(self):
        return sqlite3.connect(DB_PATH)

    def create_db(self):
        conn = self.db_connect()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                discount_type TEXT NOT NULL CHECK(discount_type IN ('percentage', 'fixed')),
                discount_value REAL NOT NULL,
                min_amount REAL DEFAULT 0,
                max_discount REAL DEFAULT 0,
                usage_limit INTEGER DEFAULT 1,
                used_count INTEGER DEFAULT 0,
                valid_until TEXT
            )
        """)
        conn.commit()
        conn.close()

    def create_ui(self):
        main = tk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(main)
        left.pack(side="left", padx=10, fill="y")
        right = tk.Frame(main)
        right.pack(side="right", fill="both", expand=True, padx=10)

        # --- Coupon Form ---
        form_box = ttk.LabelFrame(left, text="Add New Coupon")
        form_box.pack(fill="y", expand=True)

        # Coupon Code
        ttk.Label(form_box, text="Coupon Code").grid(row=0, column=0, sticky="w")
        self.ent_code = ttk.Entry(form_box)
        self.ent_code.grid(row=0, column=1, pady=2, padx=4, sticky="ew")

        # Discount Type
        ttk.Label(form_box, text="Discount Type").grid(row=1, column=0, sticky="w")
        self.cmb_dtype = ttk.Combobox(form_box, values=["percentage", "fixed"], state="readonly")
        self.cmb_dtype.current(0)
        self.cmb_dtype.grid(row=1, column=1, pady=2, padx=4, sticky="ew")

        # Discount Value
        ttk.Label(form_box, text="Discount Value").grid(row=2, column=0, sticky="w")
        self.ent_value = ttk.Entry(form_box)
        self.ent_value.grid(row=2, column=1, pady=2, padx=4, sticky="ew")

        # Min Amount
        ttk.Label(form_box, text="Minimum Amount").grid(row=3, column=0, sticky="w")
        self.ent_min = ttk.Entry(form_box)
        self.ent_min.insert(0, "0")
        self.ent_min.grid(row=3, column=1, pady=2, padx=4, sticky="ew")

        # Max Discount
        ttk.Label(form_box, text="Max Discount").grid(row=4, column=0, sticky="w")
        self.ent_max = ttk.Entry(form_box)
        self.ent_max.insert(0, "0")
        self.ent_max.grid(row=4, column=1, pady=2, padx=4, sticky="ew")

        # Usage Limit
        ttk.Label(form_box, text="Usage Limit").grid(row=5, column=0, sticky="w")
        self.ent_limit = ttk.Entry(form_box)
        self.ent_limit.insert(0, "1")
        self.ent_limit.grid(row=5, column=1, pady=2, padx=4, sticky="ew")

        # Valid for Days
        ttk.Label(form_box, text="Valid for Days").grid(row=6, column=0, sticky="w")
        self.ent_days = ttk.Entry(form_box)
        self.ent_days.insert(0, "30")
        self.ent_days.grid(row=6, column=1, pady=2, padx=4, sticky="ew")

        ttk.Button(form_box, text="Add Coupon", command=self.add_coupon).grid(row=7, column=0, columnspan=2, pady=10)

        for i in range(2):
            form_box.columnconfigure(i, weight=1)

        # --- Coupons Table ---
        table_box = ttk.LabelFrame(right, text="Existing Coupons")
        table_box.pack(fill="both", expand=True)

        columns = ("Code", "Type", "Value", "Used/Limit", "Valid Until")
        self.tree = ttk.Treeview(table_box, columns=columns, show="headings", height=16)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=130, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=3)
        self.tree.tag_configure('expired', background="#fff3cd")  # light warning color

    def load_coupons(self):
        self.tree.delete(*self.tree.get_children())
        conn = self.db_connect()
        c = conn.cursor()
        c.execute("SELECT code, discount_type, discount_value, used_count, usage_limit, valid_until, max_discount FROM coupons ORDER BY valid_until DESC")
        rows = c.fetchall()
        conn.close()
        for row in rows:
            code, dtype, value, used, limit, until, maxdisc = row
            now = datetime.now()
            expired = False
            valid_until_disp = until
            try:
                if until:
                    d = datetime.strptime(until, "%Y-%m-%d")
                    expired = d < now
                    valid_until_disp = d.strftime("%Y-%m-%d")
            except:
                pass
            is_maxed = used >= (limit or 1)
            tag = 'expired' if expired or is_maxed else ''

            display_value = f"{value}%" if dtype == "percentage" else f"₹{value:.2f}"
            self.tree.insert("", "end", values=[
                code, dtype,
                display_value,
                f"{used}/{limit}",
                valid_until_disp
            ], tags=(tag,))

    def add_coupon(self):
        code = self.ent_code.get().strip()
        dtype = self.cmb_dtype.get()
        try:
            value = float(self.ent_value.get())
        except ValueError:
            messagebox.showerror("Error", "Discount value must be a number")
            return
        try:
            min_amount = float(self.ent_min.get())
        except ValueError:
            min_amount = 0
        try:
            max_discount = float(self.ent_max.get())
        except ValueError:
            max_discount = 0
        try:
            usage_limit = int(self.ent_limit.get())
        except ValueError:
            usage_limit = 1
        try:
            valid_days = int(self.ent_days.get())
        except ValueError:
            valid_days = 30

        if not code:
            messagebox.showerror("Error", "Coupon Code required")
            return

        valid_until = (datetime.now() + timedelta(days=valid_days)).strftime("%Y-%m-%d")
        try:
            conn = self.db_connect()
            c = conn.cursor()
            c.execute("""
                INSERT INTO coupons
                    (code, discount_type, discount_value, min_amount, max_discount,
                    usage_limit, used_count, valid_until)
                 VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """, (code, dtype, value, min_amount, max_discount, usage_limit, valid_until))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Coupon code already exists.")
            return

        messagebox.showinfo("Success", "Coupon added successfully!")
        # Clear form
        self.ent_code.delete(0, tk.END)
        self.cmb_dtype.current(0)
        self.ent_value.delete(0, tk.END)
        self.ent_min.delete(0, tk.END)
        self.ent_min.insert(0, "0")
        self.ent_max.delete(0, tk.END)
        self.ent_max.insert(0, "0")
        self.ent_limit.delete(0, tk.END)
        self.ent_limit.insert(0, "1")
        self.ent_days.delete(0, tk.END)
        self.ent_days.insert(0, "30")
        self.load_coupons()

if __name__ == "__main__":
    CouponManager().mainloop()
