import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
from datetime import datetime

DB_PATH = "inventory.db"

class SalesHistoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sales History - Inventa AI Genie")
        self.geometry("1000x600")
        self.create_ui()
        self.load_sales()

    def db_connect(self):
        return sqlite3.connect(DB_PATH)

    def create_ui(self):
        # === Search Bar ===
        search_frame = ttk.Frame(self, padding=5)
        search_frame.pack(fill="x")

        self.search_type = tk.StringVar(value="invoice_no")
        self.search_query = tk.StringVar()

        ttk.Label(search_frame, text="Search by:").pack(side="left", padx=2)
        ttk.Combobox(search_frame, textvariable=self.search_type, state="readonly",
                     values=["invoice_no", "customer_name", "customer_contact"], width=18).pack(side="left", padx=2)
        ttk.Entry(search_frame, textvariable=self.search_query, width=40).pack(side="left", padx=2)

        ttk.Button(search_frame, text="Search", command=self.search_sales).pack(side="left", padx=2)
        ttk.Button(search_frame, text="Show All", command=self.load_sales).pack(side="left", padx=2)

        # === Sales Table ===
        columns = ("Invoice", "Customer", "Contact", "Bill Amt", "Net Amt", "Points Earned", "Date")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=20)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree.bind("<Double-1>", self.view_bill_details)

    def load_sales(self):
        self.tree.delete(*self.tree.get_children())
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT rowid, sale_id, customer_name, customer_contact, bill_amount,
                   net_amount, 0 as points_earned, created_date
            FROM sales ORDER BY created_date DESC
        """)
        rows = cur.fetchall()
        conn.close()

        for r in rows:
            sale_id, cust, contact, bill_amt, net_amt, points, date_str = r[1], r[2], r[3], r[4], r[5], r[6], r[7]
            try:
                date_disp = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
            except:
                date_disp = date_str
            self.tree.insert("", "end", iid=r[0], values=(
                sale_id, cust, contact, f"₹{bill_amt:.2f}", f"₹{net_amt:.2f}", points, date_disp
            ))

    def search_sales(self):
        query = self.search_query.get().strip()
        stype = self.search_type.get()

        if not query:
            self.load_sales()
            return

        self.tree.delete(*self.tree.get_children())
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute(f"""
            SELECT rowid, sale_id, customer_name, customer_contact, bill_amount,
                   net_amount, 0 as points_earned, created_date
            FROM sales
            WHERE {stype} LIKE ?
            ORDER BY created_date DESC
        """, (f"%{query}%",))
        rows = cur.fetchall()
        conn.close()

        for r in rows:
            sale_id, cust, contact, bill_amt, net_amt, points, date_str = r[1], r[2], r[3], r[4], r[5], r[6], r[7]
            try:
                date_disp = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
            except:
                date_disp = date_str
            self.tree.insert("", "end", iid=r[0], values=(
                sale_id, cust, contact, f"₹{bill_amt:.2f}", f"₹{net_amt:.2f}", points, date_disp
            ))

    def view_bill_details(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        rowid = selected[0]
        sale_id = self.tree.item(rowid)["values"][0]

        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT customer_name, customer_contact, customer_email,
                   bill_amount, discount_amount, coupon_discount, points_used,
                   net_amount, 0 as points_earned, created_date
            FROM sales WHERE sale_id = ?
        """, (sale_id,))
        sale = cur.fetchone()

        cur.execute("""
            SELECT p.name, si.quantity, si.price
            FROM sale_items si
            LEFT JOIN products p ON si.product_id = p.product_id
            WHERE sale_id = ?
        """, (sale_id,))
        items = cur.fetchall()
        conn.close()

        if not sale:
            messagebox.showerror("Error", "Sale not found.")
            return

        # Build bill text
        cust_name, cust_contact, cust_email, bill_amt, disc_amt, coup_amt, pts_used, net_amt, pts_earned, created = sale
        try:
            created_disp = datetime.strptime(created, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
        except:
            created_disp = created

        bill_text = []
        bill_text.append("INVENTA AI GENE STORE")
        bill_text.append("Phone: 9899459288, Delhi-110053\n")
        bill_text.append(f"Invoice No: {sale_id}")
        bill_text.append(f"Date: {created_disp}")
        bill_text.append(f"Customer: {cust_name}")
        bill_text.append(f"Mobile: {cust_contact}")
        bill_text.append(f"Email: {cust_email or 'N/A'}\n")
        bill_text.append("="*50)
        bill_text.append(f"{'Item':20} {'Qty':>5} {'Price':>10} {'Total':>10}")
        bill_text.append("="*50)

        for name, qty, price in items:
            total_line = qty * price
            bill_text.append(f"{name:20} {qty:>5} {price:>10.2f} {total_line:>10.2f}")

        bill_text.append("="*50)
        bill_text.append(f"Subtotal: {bill_amt:.2f}")
        bill_text.append(f"Discount: {disc_amt:.2f}")
        bill_text.append(f"Coupon Discount: {coup_amt:.2f}")
        bill_text.append(f"Points Used: {pts_used:.2f}")
        bill_text.append("-"*50)
        bill_text.append(f"NET TOTAL: {net_amt:.2f}")
        bill_text.append(f"Points Earned: {pts_earned}")
        bill_text.append("="*50)
        bill_text.append("Thank you for shopping with us!")

        # Show modal-like window
        win = tk.Toplevel(self)
        win.title(f"Bill Details - Invoice {sale_id}")
        win.geometry("650x500")
        text_box = scrolledtext.ScrolledText(win, font=("Courier New", 10))
        text_box.pack(fill="both", expand=True)
        text_box.insert("1.0", "\n".join(bill_text))
        text_box.config(state="disabled")

if __name__ == "__main__":
    SalesHistoryApp().mainloop()
