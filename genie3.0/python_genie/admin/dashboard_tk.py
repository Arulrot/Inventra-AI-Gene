import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3, subprocess, sys
from datetime import datetime, timedelta

DB_PATH = "inventory.db"

class DashboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inventor AI Genie - Main Dashboard")
        self.geometry("1150x750")
        self.configure(bg="#f4f6f9")

        # Apply styling
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Card.TFrame", background="white", relief="flat")
        style.configure("Card.TLabel", background="white", font=("Segoe UI", 12))
        style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"), foreground="white")
        style.configure("StatValue.TLabel", font=("Segoe UI", 28, "bold"),
                        foreground="#4a6cff", background="white")

        self.stats_vars = {
            'suppliers': tk.StringVar(value="--"),
            'categories': tk.StringVar(value="--"),
            'products': tk.StringVar(value="--"),
            'total_stock': tk.StringVar(value="--"),
            'low_stock': tk.StringVar(value="--"),
            'expiry_stock': tk.StringVar(value="--"),
            'non_movable': tk.StringVar(value="--"),
            'ai_recommendations': tk.StringVar(value="--")
        }

        self.create_ui()
        self.update_clock()
        self.load_dashboard_stats()
        self.load_ai_recommendations()

        # Auto-refresh every 30 seconds
        self.after(30000, self.refresh_auto)

    def db_connect(self):
        return sqlite3.connect(DB_PATH)

    def create_ui(self):
        # ==== Navigation Bar ====
        nav_frame = tk.Frame(self, bg="#2f3542")
        nav_frame.pack(fill="x")
        buttons = [
            ("Dashboard", lambda: None),
            ("Categories", lambda: self.open_module("category_management.py")),
            ("Suppliers", lambda: self.open_module("supplier_management.py")),
            ("Products", lambda: self.open_module("product_management.py")),
            ("AI Analytics", lambda: self.open_module("ai_analytics_tk.py")),
            ("Billing", lambda: self.open_module("billing_module.py"))
        ]
        for label, cmd in buttons:
            btn = tk.Button(nav_frame, text=label, command=cmd,
                            fg="white", bg="#2f3542",
                            activebackground="#4a6cff", activeforeground="white",
                            relief="flat", font=("Segoe UI", 10, "bold"),
                            padx=15, pady=10)
            btn.pack(side="left", padx=2)

        # ==== Header ====
        header_frame = tk.Frame(self, bg="#4a6cff", height=60)
        header_frame.pack(fill="x")
        tk.Label(header_frame,
                 text="🤖 Inventor AI Genie - Dashboard",
                 bg="#4a6cff", fg="white",
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=20)
        self.clock_label = tk.Label(header_frame, bg="#4a6cff", fg="white",
                                    font=("Segoe UI", 11))
        self.clock_label.pack(side="right", padx=20)

        # ==== Stats Cards ====
        stats_frame = tk.Frame(self, bg="#f4f6f9")
        stats_frame.pack(fill="x", pady=20)

        stats_info = [
            ("Suppliers", 'suppliers', self.show_suppliers),
            ("Categories", 'categories', self.show_categories),
            ("Products", 'products', self.show_products),
            ("Total Stock", 'total_stock', self.show_stock_details),
            ("Low Stock", 'low_stock', self.show_low_stock),
            ("Expiry Alerts", 'expiry_stock', self.show_expiry_alerts),
            ("Non-Movable", 'non_movable', self.show_non_movable),
            ("AI Alerts", 'ai_recommendations', self.show_ai_alerts)
        ]
        for i, (title, key, cmd) in enumerate(stats_info):
            frame = ttk.Frame(stats_frame, style="Card.TFrame", padding=10)
            frame.grid(row=i // 4, column=i % 4, padx=10, pady=10, sticky="nsew")
            ttk.Label(frame, text=title, style="Card.TLabel").pack(anchor="center")
            ttk.Label(frame, textvariable=self.stats_vars[key], style="StatValue.TLabel").pack(anchor="center", pady=5)
            ttk.Button(frame, text="View Details", command=cmd).pack(pady=(5, 0))
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)

        # ==== AI Recommendations with Button ====
        ai_frame = ttk.LabelFrame(self, text="AI Recommendations", padding=10)
        ai_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Button row on top of AI frame
        btn_frame = tk.Frame(ai_frame, bg="white")
        btn_frame.pack(fill="x", pady=(0, 5))
        ttk.Button(btn_frame, text="🚀 Run Gene AI Analysis",
                   command=self.run_ai_analysis).pack(side="right")

        # Recommendations text area
        self.ai_text = scrolledtext.ScrolledText(
            ai_frame, state="disabled", wrap="word",
            font=("Segoe UI", 10), height=10
        )
        self.ai_text.pack(fill="both", expand=True)

    def open_module(self, filename):
        try:
            subprocess.Popen([sys.executable, filename])
        except FileNotFoundError:
            messagebox.showerror("Error", f"Could not find file: {filename}")

    def update_clock(self):
        now = datetime.now().strftime("%A, %d %B %Y %I:%M:%S %p")
        self.clock_label.config(text=now)
        self.after(1000, self.update_clock)

    def load_dashboard_stats(self):
        try:
            conn = self.db_connect()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM suppliers")
            self.stats_vars['suppliers'].set(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM categories")
            self.stats_vars['categories'].set(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM products")
            self.stats_vars['products'].set(cur.fetchone()[0])
            cur.execute("SELECT SUM(current_stock) FROM products")
            total_stock = cur.fetchone()[0] or 0
            self.stats_vars['total_stock'].set(total_stock)
            cur.execute("SELECT COUNT(*) FROM products WHERE current_stock <= minimum_stock AND current_stock > 0")
            self.stats_vars['low_stock'].set(cur.fetchone()[0])
            today = datetime.now()
            warning_date = today + timedelta(days=30)
            cur.execute("""SELECT COUNT(*) FROM products
                           WHERE expiry_date IS NOT NULL AND expiry_date != ''
                           AND DATE(expiry_date) <= DATE(?) AND current_stock > 0""",
                           (warning_date.strftime("%Y-%m-%d"),))
            self.stats_vars['expiry_stock'].set(cur.fetchone()[0])
            non_mov_date = today - timedelta(days=90)
            cur.execute("""SELECT COUNT(*) FROM products
                           WHERE date_added IS NOT NULL AND DATE(date_added) <= DATE(?)
                           AND total_sold = 0 AND current_stock > 0""",
                           (non_mov_date.strftime("%Y-%m-%d"),))
            self.stats_vars['non_movable'].set(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM ai_recommendations")
            self.stats_vars['ai_recommendations'].set(cur.fetchone()[0])
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_ai_recommendations(self):
        try:
            conn = self.db_connect()
            cur = conn.cursor()
            cur.execute("""SELECT message, created_date, priority
                           FROM ai_recommendations ORDER BY created_date DESC LIMIT 10""")
            rows = cur.fetchall()
            conn.close()
            self.ai_text.config(state="normal")
            self.ai_text.delete("1.0", tk.END)
            if not rows:
                self.ai_text.insert(tk.END, "No AI recommendations at this time.\n")
            else:
                for msg, created, prio in rows:
                    self.ai_text.insert(tk.END, f"[Priority {prio}] {created} - {msg}\n\n")
            self.ai_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # === Detail windows ===
    def show_suppliers(self):
        self.show_detail_window("Suppliers", "SELECT name, supplier_id, phone, email FROM suppliers")

    def show_categories(self):
        self.show_detail_window("Categories", "SELECT name, description FROM categories")

    def show_products(self):
        self.show_detail_window("Products", """SELECT p.name, c.name, s.name, p.price, p.current_stock, p.minimum_stock
                                               FROM products p
                                               LEFT JOIN categories c ON p.category_id = c.category_id
                                               LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id""")

    def show_stock_details(self):
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute("SELECT price, current_stock FROM products")
        rows = cur.fetchall()
        conn.close()
        total_value = sum(p * stock for p, stock in rows)
        avg_stock = round(sum(stock for _, stock in rows) / len(rows)) if rows else 0
        messagebox.showinfo("Stock Details", f"Total Stock Value: ₹{total_value:.2f}\nAverage Stock per Product: {avg_stock} units")

    def show_low_stock(self):
        self.show_detail_window("Low Stock Items", """SELECT name, current_stock, minimum_stock FROM products
                                                      WHERE current_stock <= minimum_stock AND current_stock > 0""")

    def show_expiry_alerts(self):
        warning_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        self.show_detail_window("Expiry Alerts", """SELECT name, current_stock, expiry_date FROM products
                                                    WHERE expiry_date <= ? AND current_stock > 0""",
                                                    (warning_date,))

    def show_non_movable(self):
        nonmov_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        self.show_detail_window("Non-Movable Stock", """SELECT name, current_stock, date_added FROM products
                                                        WHERE date_added <= ? AND total_sold = 0 AND current_stock > 0""",
                                                        (nonmov_date,))

    def show_ai_alerts(self):
        self.show_detail_window("AI Recommendations", "SELECT message, created_date, priority FROM ai_recommendations")

    def show_detail_window(self, title, query, params=()):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("650x450")
        text = scrolledtext.ScrolledText(win, font=("Segoe UI", 10))
        text.pack(fill="both", expand=True)
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        if not rows:
            text.insert(tk.END, "No data found.\n")
        else:
            for row in rows:
                text.insert(tk.END, " | ".join(str(r) for r in row) + "\n")

    def run_ai_analysis(self):
        try:
            subprocess.run([sys.executable, "gene_ai.py"], check=True)
            messagebox.showinfo("AI Analysis", "Gene AI analysis completed and recommendations updated.")
            self.load_ai_recommendations()
            self.load_dashboard_stats()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run Gene AI analysis:\n{e}")

    def refresh_auto(self):
        self.load_dashboard_stats()
        self.load_ai_recommendations()
        self.after(30000, self.refresh_auto)

if __name__ == "__main__":
    DashboardApp().mainloop()
