import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
from datetime import datetime

DB_PATH = "inventory.db"

class BillingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("POS Billing - Inventa AI Genie")
        self.geometry("1350x750")
        self.configure(bg="#f7f9fc")

        # State
        self.cart_list = []
        self.current_customer = None
        self.applied_coupon = None

        # Tk vars
        self.var_search = tk.StringVar()
        self.var_cname = tk.StringVar()
        self.var_contact = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_pid = tk.StringVar()
        self.var_pname = tk.StringVar()
        self.var_price = tk.DoubleVar()
        self.var_qty = tk.StringVar()
        self.var_stock = tk.IntVar()

        self.var_discount = tk.DoubleVar(value=5.0)
        self.var_coupon_code = tk.StringVar()
        self.var_coupon_discount = tk.DoubleVar(value=0.0)
        self.var_points_use = tk.IntVar(value=0)
        self.var_loyalty_points = tk.IntVar(value=0)

        self.bill_amount = 0.0
        self.discount_amount = 0.0
        self.net_pay = 0.0

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.create_ui()
        self.load_products()

    def db_connect(self):
        return sqlite3.connect(DB_PATH)

    # ============ UI ============
    def create_ui(self):
        # Left Column - Products
        left_frame = tk.LabelFrame(self, text="Products", font=("Segoe UI", 12, "bold"), bg="white")
        left_frame.place(x=10, y=10, width=400, height=730)

        sf = tk.Frame(left_frame, bg="white")
        sf.pack(fill="x", pady=5)
        tk.Entry(sf, textvariable=self.var_search, font=("Segoe UI", 12)).pack(side="left", fill="x", expand=True)
        ttk.Button(sf, text="Search", command=self.search_products).pack(side="left", padx=3)
        ttk.Button(sf, text="All", command=self.load_products).pack(side="left")

        columns = ("pid", "name", "price", "stock")
        self.product_table = ttk.Treeview(left_frame, columns=columns, show="headings", height=29)
        for col in columns:
            self.product_table.heading(col, text=col.capitalize())
            width = 80 if col != "name" else 160
            self.product_table.column(col, width=width, anchor="center")
        self.product_table.pack(fill="both", expand=True)
        self.product_table.bind("<Double-1>", self.on_product_select)

        # Middle - Customer and Cart
        middle_frame = tk.LabelFrame(self, text="Customer & Cart", font=("Segoe UI", 12, "bold"), bg="white")
        middle_frame.place(x=420, y=10, width=580, height=730)

        # Customer section
        cust_frame = tk.Frame(middle_frame, bg="white")
        cust_frame.pack(fill="x", pady=5)

        tk.Label(cust_frame, text="Name:", font=("Segoe UI", 10), bg="white").grid(row=0, column=0)
        tk.Entry(cust_frame, textvariable=self.var_cname, font=("Segoe UI", 10), width=18).grid(row=0, column=1)
        tk.Label(cust_frame, text="Mobile:", font=("Segoe UI", 10), bg="white").grid(row=0, column=2)
        contact_entry = tk.Entry(cust_frame, textvariable=self.var_contact, font=("Segoe UI", 10), width=15)
        contact_entry.grid(row=0, column=3)
        contact_entry.bind("<KeyRelease>", lambda e: self.lookup_customer())

        tk.Label(cust_frame, text="Email:", font=("Segoe UI", 10), bg="white").grid(row=1, column=0)
        tk.Entry(cust_frame, textvariable=self.var_email, font=("Segoe UI", 10), width=18).grid(row=1, column=1)
        ttk.Button(cust_frame, text="Save Customer", command=self.add_customer).grid(row=1, column=3)

        self.loyalty_label = tk.Label(cust_frame, text="Points: 0", font=("Segoe UI", 10, "bold"), fg="#007bff", bg="white")
        self.loyalty_label.grid(row=2, column=0, columnspan=2)
        tk.Label(cust_frame, text="Use (pts):", font=("Segoe UI", 10), bg="white").grid(row=2, column=2)
        tk.Entry(cust_frame, textvariable=self.var_points_use, width=10).grid(row=2, column=3)

        # Cart Table
        cart_columns = ("pid", "name", "price", "qty", "total")
        self.cart_table = ttk.Treeview(middle_frame, columns=cart_columns, show="headings", height=20)
        for col in cart_columns:
            self.cart_table.heading(col, text=col.capitalize())
            self.cart_table.column(col, width=100 if col != "name" else 180, anchor="center")
        self.cart_table.pack(fill="both", pady=5)
        self.cart_table.bind("<ButtonRelease-1>", self.get_cart_data)

        # Cart buttons
        btn_frame = tk.Frame(middle_frame, bg="white")
        btn_frame.pack(fill="x")
        tk.Label(btn_frame, text="Qty:", font=("Segoe UI", 10), bg="white").pack(side="left")
        tk.Entry(btn_frame, textvariable=self.var_qty, width=7).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Add/Update", command=self.add_update_cart).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove", command=self.remove_cart_item).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear Cart", command=self.clear_cart).pack(side="left", padx=5)

        # Right - Summary
        right_frame = tk.LabelFrame(self, text="Bill Summary", font=("Segoe UI", 12, "bold"), bg="white")
        right_frame.place(x=1010, y=10, width=330, height=730)

        tk.Label(right_frame, text="Coupon Code:", font=("Segoe UI", 10), bg="white").pack(anchor="w", padx=5, pady=(5, 0))
        tk.Entry(right_frame, textvariable=self.var_coupon_code).pack(fill="x", padx=5)
        ttk.Button(right_frame, text="Apply Coupon", command=self.apply_coupon).pack(padx=5, pady=3, fill="x")

        tk.Label(right_frame, text="Discount %:", font=("Segoe UI", 10), bg="white").pack(anchor="w", padx=5)
        tk.Entry(right_frame, textvariable=self.var_discount).pack(fill="x", padx=5)
        self.var_discount.trace_add("write", lambda *args: self.update_bill_summary())

        self.summary_labels = {}
        for label in ["Bill Amount", "Discount", "Coupon Discount", "Points Used", "Net Pay"]:
            f = tk.Frame(right_frame, bg="white")
            f.pack(fill="x", pady=2)
            tk.Label(f, text=label + ":", font=("Segoe UI", 10), bg="white").pack(side="left", padx=5)
            lbl = tk.Label(f, text="₹0.00", font=("Segoe UI", 10, "bold"), bg="white")
            lbl.pack(side="right", padx=5)
            self.summary_labels[label] = lbl

        ttk.Button(right_frame, text="Generate Bill", command=self.generate_bill).pack(pady=8, fill="x")
        ttk.Button(right_frame, text="Clear All", command=self.clear_all).pack(pady=2, fill="x")

        self.txt_bill_area = scrolledtext.ScrolledText(right_frame, font=("Consolas", 9), height=20)
        self.txt_bill_area.pack(fill="both", expand=True, padx=5, pady=5)

    # ========= Product DB ==========
    def load_products(self):
        con = self.db_connect()
        cur = con.cursor()
        cur.execute("SELECT product_id, name, price, current_stock FROM products WHERE current_stock>0")
        rows = cur.fetchall()
        self.product_table.delete(*self.product_table.get_children())
        for r in rows:
            self.product_table.insert("", "end", values=(r[0], r[1], round(float(r[2]), 2), int(r[3])))
        con.close()

    def search_products(self):
        q = self.var_search.get().strip()
        con = self.db_connect()
        cur = con.cursor()
        cur.execute("SELECT product_id, name, price, current_stock FROM products WHERE name LIKE ?", (f"%{q}%",))
        rows = cur.fetchall()
        self.product_table.delete(*self.product_table.get_children())
        for r in rows:
            self.product_table.insert("", "end", values=(r[0], r[1], round(float(r[2]), 2), int(r[3])))
        con.close()

    # ========= Cart Actions =========
    def on_product_select(self, e):
        sel = self.product_table.selection()
        if not sel: return
        pid, pname, price, stock = self.product_table.item(sel[0])["values"]
        self.var_pid.set(pid); self.var_pname.set(pname)
        self.var_price.set(price); self.var_stock.set(stock)
        self.var_qty.set("1")

    def get_cart_data(self, e):
        sel = self.cart_table.selection()
        if not sel: return
        pid, pname, price, qty, total = self.cart_table.item(sel[0])["values"]
        for it in self.cart_list:
            if it[0] == pid:
                self.var_pid.set(it[0]); self.var_pname.set(it[1])
                self.var_price.set(it[2]); self.var_qty.set(it[3])
                self.var_stock.set(it[4])
                break

    def add_update_cart(self):
        if not self.var_pid.get() or not self.var_qty.get().isdigit(): return
        qty = int(self.var_qty.get())
        stock = int(self.var_stock.get()); price = float(self.var_price.get())
        if qty > stock:
            messagebox.showerror("Error", "Quantity exceeds stock."); return
        for i, it in enumerate(self.cart_list):
            if it[0] == self.var_pid.get():
                new_qty = it[3] + qty
                if new_qty > stock:
                    messagebox.showerror("Error", "Total qty exceeds stock."); return
                self.cart_list[i][3] = new_qty
                break
        else:
            self.cart_list.append([self.var_pid.get(), self.var_pname.get(), price, qty, stock])
        self.show_cart(); self.update_bill_summary()

    def show_cart(self):
        self.cart_table.delete(*self.cart_table.get_children())
        for it in self.cart_list:
            self.cart_table.insert("", "end", values=(it[0], it[1], it[2], it[3], round(it[2]*it[3], 2)))

    def remove_cart_item(self):
        sel = self.cart_table.selection()
        if not sel: return
        pid = self.cart_table.item(sel[0])["values"][0]
        self.cart_list = [x for x in self.cart_list if x[0] != pid]
        self.show_cart(); self.update_bill_summary()

    def clear_cart(self):
        self.cart_list.clear(); self.show_cart(); self.update_bill_summary()

    # ========= Customer =========
    def lookup_customer(self):
        phone = self.var_contact.get().strip()
        if len(phone) < 4:
            self.var_cname.set(""); self.var_email.set(""); self.var_loyalty_points.set(0)
            self.loyalty_label.config(text="Points: 0"); return
        con = self.db_connect()
        cur = con.cursor()
        cur.execute("SELECT customer_id, name, email, loyalty_points FROM customers WHERE contact=?", (phone,))
        row = cur.fetchone()
        con.close()
        if row:
            self.current_customer = row[0]
            self.var_cname.set(row[1]); self.var_email.set(row[2] or "")
            self.var_loyalty_points.set(row[3]); self.loyalty_label.config(text=f"Points: {row[3]}")
        else:
            self.current_customer = None
            self.var_loyalty_points.set(0)
            self.loyalty_label.config(text="Points: 0")

    def add_customer(self):
        name = self.var_cname.get(); contact = self.var_contact.get(); email = self.var_email.get()
        if not name or not contact: return
        con = self.db_connect(); cur = con.cursor()
        cur.execute("SELECT customer_id FROM customers WHERE contact=?", (contact,))
        if cur.fetchone():
            cur.execute("UPDATE customers SET name=?, email=? WHERE contact=?", (name, email, contact))
        else:
            cur.execute("INSERT INTO customers (name, contact, email, loyalty_points) VALUES (?,?,?,0)", (name, contact, email))
        con.commit(); con.close()
        self.lookup_customer()

    # ========= Coupon =========
    def apply_coupon(self):
        code = self.var_coupon_code.get().strip()
        if not code: return
        con = self.db_connect(); cur = con.cursor()
        cur.execute("SELECT discount_type, discount_value, min_amount, max_discount, usage_limit, used_count, valid_until FROM coupons WHERE code=?", (code,))
        row = cur.fetchone(); con.close()
        if not row: return messagebox.showerror("Error", "Invalid coupon")
        dtype, dval, minamt, maxdisc, limit, used, valid_until = row
        subtotal = sum(i[2]*i[3] for i in self.cart_list)
        if subtotal < minamt: return messagebox.showerror("Error", f"Bill must be ≥ ₹{minamt}")
        disc_val = (subtotal * dval / 100) if dtype == "percentage" else dval
        if maxdisc > 0 and disc_val > maxdisc: disc_val = maxdisc
        if used >= limit: return messagebox.showerror("Error", "Usage limit reached")
        self.var_coupon_discount.set(disc_val); self.applied_coupon = code
        self.update_bill_summary()

    # ========= Billing =========
    def update_bill_summary(self):
        self.bill_amount = sum(i[2]*i[3] for i in self.cart_list)
        self.discount_amount = (self.bill_amount * self.var_discount.get() / 100)
        coupon_amt = self.var_coupon_discount.get()
        pts_used = min(self.var_points_use.get(), self.var_loyalty_points.get())
        self.net_pay = max(0, self.bill_amount - self.discount_amount - coupon_amt - pts_used)
        self.summary_labels["Bill Amount"].config(text=f"₹{self.bill_amount:.2f}")
        self.summary_labels["Discount"].config(text=f"₹{self.discount_amount:.2f}")
        self.summary_labels["Coupon Discount"].config(text=f"₹{coupon_amt:.2f}")
        self.summary_labels["Points Used"].config(text=f"₹{pts_used:.2f}")
        self.summary_labels["Net Pay"].config(text=f"₹{self.net_pay:.2f}")
        self.update_bill_preview()

    def update_bill_preview(self):
        self.txt_bill_area.delete("1.0", "end")
        self.txt_bill_area.insert("end", f"INVENTA AI GENE STORE\n")
        self.txt_bill_area.insert("end", f"Customer: {self.var_cname.get()}  Ph: {self.var_contact.get()}\n")
        self.txt_bill_area.insert("end", "-"*40 + "\n")
        for it in self.cart_list:
            self.txt_bill_area.insert("end", f"{it[1]:15} {it[3]:>3} x ₹{it[2]:.2f} = ₹{it[2]*it[3]:.2f}\n")
        self.txt_bill_area.insert("end", "-"*40 + f"\nNet Pay ₹{self.net_pay:.2f}\n")

    def generate_bill(self):
        if not self.cart_list or not self.var_contact.get() or not self.var_cname.get():
            return messagebox.showerror("Error", "Incomplete details")
        con = self.db_connect(); cur = con.cursor()
        if not self.current_customer:
            cur.execute("INSERT INTO customers (name, contact, email, loyalty_points) VALUES (?,?,?,0)", (self.var_cname.get(), self.var_contact.get(), self.var_email.get()))
            cid = cur.lastrowid; pts_avail = 0
        else:
            cid = self.current_customer; pts_avail = self.var_loyalty_points.get()
        pts_used = min(self.var_points_use.get(), pts_avail)
        pts_earned = int(self.net_pay // 100)
        # Insert into sales
        cur.execute("""INSERT INTO sales (customer_id, customer_name, customer_contact, customer_email, bill_amount, discount_amount, coupon_discount, points_used, net_amount, points_earned, created_date) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (cid, self.var_cname.get(), self.var_contact.get(), self.var_email.get(), self.bill_amount, self.discount_amount, self.var_coupon_discount.get(), pts_used, self.net_pay, pts_earned, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        sale_id = cur.lastrowid
        # Items and stock update
        for it in self.cart_list:
            cur.execute("INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (?,?,?,?)", (sale_id, it[0], it[3], it[2]))
            cur.execute("UPDATE products SET current_stock = current_stock - ? WHERE product_id=?", (it[3], it[0]))
        # Update customer points
        cur.execute("UPDATE customers SET loyalty_points = loyalty_points - ? + ? WHERE customer_id=?", (pts_used, pts_earned, cid))
        if self.applied_coupon:
            cur.execute("UPDATE coupons SET used_count = used_count + 1 WHERE code=?", (self.applied_coupon,))
        con.commit(); con.close()
        self.var_loyalty_points.set(self.var_loyalty_points.get() - pts_used + pts_earned)
        self.loyalty_label.config(text=f"Points: {self.var_loyalty_points.get()}")
        messagebox.showinfo("Saved", f"Bill #{sale_id} saved.")
        self.clear_all(); self.load_products()

    def clear_all(self):
        self.cart_list.clear(); self.show_cart()
        self.var_cname.set(""); self.var_contact.set(""); self.var_email.set("")
        self.var_discount.set(5.0); self.var_coupon_discount.set(0.0)
        self.var_points_use.set(0); self.var_loyalty_points.set(0); self.var_coupon_code.set("")
        self.txt_bill_area.delete("1.0", "end"); self.update_bill_summary()


if __name__ == "__main__":
    BillingApp().mainloop()
