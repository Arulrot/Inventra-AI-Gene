# dashboard.py
# Admin-only dashboard for the Inventor AI Gene application (Corrected)

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import time
import sqlite3
import os

# --- Assuming these are your other class files ---
# Make sure these files exist and are correctly named.
from supplier import supplierClass
from category import categoryClass
from product import productClass
from sales import salesClass

# --- Constants for Professional UI Configuration ---
BG_COLOR = "#f0f0f0"
TITLE_BG_COLOR = "#2c3e50"
TITLE_FG_COLOR = "white"
FOOTER_BG_COLOR = "#34495e"
MENU_FRAME_BG_COLOR = "#ffffff"
MENU_ACTIVE_BG_COLOR = "#e0e0e0"
MENU_LBL_BG_COLOR = "#3498db"

FONT_TITLE = ("Segoe UI", 30, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_MENU = ("Segoe UI", 16, "bold")
FONT_FOOTER = ("Segoe UI", 10)
FONT_STATS = ("Segoe UI", 18, "bold")

class LoginWindow:
    """Login window that appears before the main application."""
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Login")
        self.root.geometry("400x200+500+250")
        self.root.resizable(False, False)
        self.root.config(bg=BG_COLOR)

        login_frame = tk.Frame(self.root, bg=BG_COLOR)
        login_frame.pack(expand=True)

        tk.Label(login_frame, text="Administrator Password", font=("Segoe UI", 14, "bold"), bg=BG_COLOR).pack(pady=(0, 10))

        self.password_var = tk.StringVar()
        password_entry = tk.Entry(login_frame, textvariable=self.password_var, show="*", font=("Segoe UI", 12), width=30)
        password_entry.pack()
        password_entry.focus()
        
        # --- THIS IS THE CORRECTED LINE ---
        # The event is now correctly specified as "<Return>" for the Enter key.
        password_entry.bind("<Return>", self.login) 

        login_button = tk.Button(login_frame, text="Login", command=self.login, font=("Segoe UI", 12, "bold"), bg="#27ae60", fg="white", cursor="hand2", width=15)
        login_button.pack(pady=20)

    def login(self, event=None):
        """Validates the password and launches the main dashboard."""
        if self.password_var.get() == "root":
            self.root.destroy()
            launch_dashboard()
        else:
            messagebox.showerror("Error", "Invalid Password", parent=self.root)
            self.password_var.set("")

class InventorAI:
    """Main Admin Dashboard for Inventory Management."""
    def __init__(self, root):
        self.root = root
        self.setup_main_window()
        self.db_conn = self.initialize_database()

        self.check_resources()
        self.load_images()

        self._create_header()
        self._create_left_menu()
        self._create_dashboard_content()
        self._create_footer()

        self.update_dashboard_stats()
        self.update_clock()

    def setup_main_window(self):
        self.root.title("Inventor AI Gene | Admin Dashboard")
        self.root.geometry("1350x700+110+80")
        self.root.resizable(False, False)
        self.root.config(bg=BG_COLOR)
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

    def initialize_database(self):
        try:
            return sqlite3.connect(database=r'ims.db')
        except Exception as ex:
            messagebox.showerror("Database Error", f"Error connecting to database: {str(ex)}", parent=self.root)
            self.root.destroy()
            return None

    def check_resources(self):
        if not os.path.exists("./bill"):
            os.makedirs("./bill")

    def load_images(self):
        try:
            self.icon_title_img = tk.PhotoImage(file="images/logo1.png")
            self.icon_side_img = tk.PhotoImage(file="images/side.png")
            menu_logo_pil = Image.open("images/menu_im.png").resize((200, 200))
            self.MenuLogo = ImageTk.PhotoImage(menu_logo_pil)
        except Exception as ex:
            messagebox.showwarning("Image Warning", f"Could not load images: {str(ex)}", parent=self.root)
            self.icon_title_img = tk.PhotoImage()
            self.icon_side_img = tk.PhotoImage()
            self.MenuLogo = tk.PhotoImage()

    def _create_header(self):
        title_label = tk.Label(self.root, text="Inventor AI Gene", image=self.icon_title_img, compound=tk.LEFT,
                               font=FONT_TITLE, bg=TITLE_BG_COLOR, fg=TITLE_FG_COLOR, anchor="w", padx=20)
        title_label.place(x=0, y=0, relwidth=1, height=70)

        btn_logout = tk.Button(self.root, text="Logout", command=self.logout, font=FONT_BODY, bg="#e74c3c", fg="white", cursor="hand2")
        btn_logout.place(x=1200, y=15, height=40, width=120)

        self.lbl_clock = tk.Label(self.root, text="Welcome!\t\t Date: DD-MM-YYYY\t\t Time: HH:MM:SS",
                                  font=FONT_BODY, bg=FOOTER_BG_COLOR, fg=TITLE_FG_COLOR)
        self.lbl_clock.place(x=0, y=70, relwidth=1, height=30)

    def _create_left_menu(self):
        LeftMenu = tk.Frame(self.root, bd=2, relief=tk.RIDGE, bg=MENU_FRAME_BG_COLOR)
        LeftMenu.place(x=0, y=102, width=220, height=565)

        lbl_menuLogo = tk.Label(LeftMenu, image=self.MenuLogo, bg=MENU_FRAME_BG_COLOR)
        lbl_menuLogo.pack(side=tk.TOP, pady=10)

        tk.Label(LeftMenu, text="Menu", font=("Segoe UI", 18, "bold"), bg=MENU_LBL_BG_COLOR, fg="white").pack(side=tk.TOP, fill=tk.X, pady=10)

        menu_items = {
            "Supplier": self.open_supplier_window,
            "Category": self.open_category_window,
            "Products": self.open_product_window,
            "Sales": self.open_sales_window,
            "Exit": self.on_exit
        }

        for text, command in menu_items.items():
            btn = tk.Button(LeftMenu, text=text, command=command, image=self.icon_side_img, compound=tk.LEFT,
                            padx=10, anchor="w", font=FONT_MENU, bg=MENU_FRAME_BG_COLOR, bd=0, cursor="hand2")
            btn.pack(side=tk.TOP, fill=tk.X, pady=5)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=MENU_ACTIVE_BG_COLOR))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=MENU_FRAME_BG_COLOR))

    def _create_dashboard_content(self):
        self.lbl_supplier = self.create_stat_box("Total Suppliers\n[ 0 ]", "#1abc9c", 300, 120)
        self.lbl_category = self.create_stat_box("Total Categories\n[ 0 ]", "#3498db", 650, 120)
        self.lbl_product = self.create_stat_box("Total Products\n[ 0 ]", "#9b59b6", 300, 300)
        self.lbl_sales = self.create_stat_box("Total Sales\n[ 0 ]", "#e67e22", 650, 300)

    def create_stat_box(self, text, color, x, y):
        lbl = tk.Label(self.root, text=text, bd=5, relief=tk.RIDGE, bg=color, fg="white", font=FONT_STATS)
        lbl.place(x=x, y=y, height=150, width=300)
        return lbl

    def _create_footer(self):
        footer_text = "Inventor AI Gene | Admin Panel"
        lbl_footer = tk.Label(self.root, text=footer_text, font=FONT_FOOTER, bg=FOOTER_BG_COLOR, fg=TITLE_FG_COLOR)
        lbl_footer.pack(side=tk.BOTTOM, fill=tk.X)

    def open_window(self, window_class):
        new_win = tk.Toplevel(self.root)
        new_obj = window_class(new_win)

    def open_supplier_window(self): self.open_window(supplierClass)
    def open_category_window(self): self.open_window(categoryClass)
    def open_product_window(self): self.open_window(productClass)
    def open_sales_window(self): self.open_window(salesClass)

    def update_clock(self):
        time_str = time.strftime("%I:%M:%S %p")
        date_str = time.strftime("%d-%m-%Y")
        self.lbl_clock.config(text=f"Welcome, Admin!\t\t Date: {date_str}\t\t Time: {time_str}")
        self.lbl_clock.after(1000, self.update_clock)

    def update_dashboard_stats(self):
        if not self.db_conn: return
        try:
            cur = self.db_conn.cursor()
            def get_count(table_name):
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                return cur.fetchone()[0]

            self.lbl_product.config(text=f"Total Products\n[ {get_count('product')} ]")
            self.lbl_category.config(text=f"Total Categories\n[ {get_count('category')} ]")
            self.lbl_supplier.config(text=f"Total Suppliers\n[ {get_count('supplier')} ]")
            
            bill_count = len(os.listdir("bill"))
            self.lbl_sales.config(text=f"Total Sales\n[ {bill_count} ]")
        except Exception as ex:
            messagebox.showerror("Error", f"Error updating stats: {str(ex)}", parent=self.root)

    def logout(self):
        self.on_exit()

    def on_exit(self):
        if messagebox.askokcancel("Exit", "Do you want to exit the application?", parent=self.root):
            if self.db_conn:
                self.db_conn.close()
            self.root.destroy()

def launch_dashboard():
    root = tk.Tk()
    app = InventorAI(root)
    root.mainloop()

if __name__ == "__main__":
    login_root = tk.Tk()
    login_app = LoginWindow(login_root)
    login_root.mainloop()
