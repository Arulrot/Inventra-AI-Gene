import tkinter as tk
from tkinter import ttk, messagebox
import subprocess, sys

class POSBase(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inventa AI Gene - POS System")
        self.geometry("1100x700")
        self.configure(bg="#f8f9fa")

        self.create_navbar()
        self.create_content_area()

    def create_navbar(self):
        navbar = tk.Frame(self, bg="#0d6efd", height=50)
        navbar.pack(fill="x")

        tk.Label(navbar, text="🏪 Inventa AI Gene", bg="#0d6efd", fg="white",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=10)

        button_style = dict(bg="#0d6efd", fg="white", activebackground="#0b5ed7",
                            activeforeground="white", font=("Segoe UI", 10, "bold"),
                            relief="flat", padx=15, pady=10)

        tk.Button(navbar, text="💰 POS", command=lambda: self.open_module("billing_module.py"), **button_style).pack(side="left")
        tk.Button(navbar, text="📜 History", command=lambda: self.open_module("sales_history.py"), **button_style).pack(side="left")
        tk.Button(navbar, text="🏷 Coupons", command=lambda: self.open_module("coupon_manager.py"), **button_style).pack(side="left")

    def create_content_area(self):
        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.pack(fill="both", expand=True)

        # Default content
        tk.Label(self.content_frame, text="Welcome to Inventa AI Gene POS System",
                 font=("Segoe UI", 16), bg="white").pack(pady=20)

    def open_module(self, filename):
        """Opens the respective module as a new process."""
        try:
            subprocess.Popen([sys.executable, filename])
        except FileNotFoundError:
            messagebox.showerror("Error", f"Module {filename} not found")

if __name__ == "__main__":
    POSBase().mainloop()
