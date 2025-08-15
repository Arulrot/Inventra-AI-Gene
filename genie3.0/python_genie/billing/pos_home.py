import tkinter as tk
from tkinter import ttk, messagebox
import subprocess, sys

class POSHome(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inventa AI Gene - POS Home")
        self.geometry("900x600")
        self.configure(bg="#f4f6f9")

        self.create_ui()

    def open_module(self, filename):
        try:
            subprocess.Popen([sys.executable, filename])
        except FileNotFoundError:
            messagebox.showerror("Error", f"Module {filename} not found")

    def create_ui(self):
        # === Header ===
        header = tk.Frame(self, bg="#007bff", pady=20)
        header.pack(fill="x")
        tk.Label(header, text="🏪 Inventa AI Gene", fg="white", bg="#007bff",
                 font=("Segoe UI", 24, "bold")).pack()
        tk.Label(header, text="Advanced Point of Sale System with Loyalty & Coupons",
                 fg="white", bg="#007bff", font=("Segoe UI", 12)).pack(pady=(5,0))
        tk.Label(header, text="Complete inventory management and billing solution for modern businesses",
                 fg="white", bg="#007bff", font=("Segoe UI", 10)).pack()

        # === Menu Buttons (like Bootstrap cards) ===
        menu_frame = tk.Frame(self, bg="#f4f6f9", pady=20)
        menu_frame.pack(fill="x")

        self.create_card(menu_frame, "🖥 Point of Sale",
                         "Complete POS with cart, billing, and loyalty features.",
                         lambda: self.open_module("billing/billing_module.py"), "#007bff").grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        self.create_card(menu_frame, "📊 Sales History",
                         "View your past transactions and detailed reports.",
                         lambda: self.open_module("billing/sales_history.py"), "#17a2b8").grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        self.create_card(menu_frame, "🏷 Coupon Management",
                         "Create and manage discount coupons.",
                         lambda: self.open_module("billing/coupon_manager.py"), "#28a745").grid(row=0, column=2, padx=15, pady=10, sticky="nsew")

        menu_frame.columnconfigure((0,1,2), weight=1)

        # === Features List ===
        features_frame = ttk.LabelFrame(self, text="Features", padding=10)
        features_frame.pack(fill="both", expand=True, padx=20, pady=10)

        left_features = [
            "Real-time inventory management",
            "Customer loyalty points system",
            "Discount coupon management",
            "Comprehensive sales reporting"
        ]

        right_features = [
            "Customer database management",
            "Multi-level discount system",
            "Print-ready bill generation",
            "Desktop-based responsive interface"
        ]

        # Two columns
        lf = tk.Frame(features_frame)
        rf = tk.Frame(features_frame)
        lf.pack(side="left", expand=True, fill="both")
        rf.pack(side="right", expand=True, fill="both")

        for feat in left_features:
            tk.Label(lf, text="✔ " + feat, anchor="w",
                     font=("Segoe UI", 10)).pack(anchor="w", pady=2)
        for feat in right_features:
            tk.Label(rf, text="✔ " + feat, anchor="w",
                     font=("Segoe UI", 10)).pack(anchor="w", pady=2)

    def create_card(self, parent, title, desc, command, color):
        frame = tk.Frame(parent, bg="white", bd=1, relief="solid", padx=15, pady=15)
        tk.Label(frame, text=title, font=("Segoe UI", 14, "bold"), fg=color, bg="white").pack(anchor="center")
        tk.Label(frame, text=desc, wraplength=200, bg="white", font=("Segoe UI", 9)).pack(anchor="center", pady=5)
        ttk.Button(frame, text="Open", command=command).pack(pady=5)
        return frame

if __name__ == "__main__":
    app = POSHome()
    app.mainloop()
