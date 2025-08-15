import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime

DB_PATH = "inventory.db"

class SupplierManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Supplier Management - Inventor AI Genie")
        self.geometry("900x600")
        self.editing_id = None

        self.create_tables()
        self.create_ui()
        self.load_stats()
        self.load_suppliers()

    def db_connect(self):
        return sqlite3.connect(DB_PATH)

    def create_tables(self):
        conn = self.db_connect()
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS suppliers(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        supplier_id TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        phone TEXT,
                        email TEXT,
                        address TEXT
                    )""")
        conn.commit()
        conn.close()

    def create_ui(self):
        # Stats cards
        stats_frame = ttk.Frame(self, padding=10)
        stats_frame.pack(fill="x")

        self.total_suppliers = tk.StringVar(value="0")
        self.active_suppliers = tk.StringVar(value="0")
        self.total_products = tk.StringVar(value="0")
        self.recent_orders = tk.StringVar(value="0")

        stats = [
            ("Total Suppliers", self.total_suppliers),
            ("Active Suppliers", self.active_suppliers),
            ("Products Supplied", self.total_products),
            ("Recent Orders", self.recent_orders)
        ]
        for i, (label, var) in enumerate(stats):
            lf = ttk.LabelFrame(stats_frame, text=label, padding=10)
            lf.grid(row=0, column=i, padx=5, sticky="nsew")
            ttk.Label(lf, textvariable=var, font=("Segoe UI", 18, "bold")).pack()
        for i in range(len(stats)):
            stats_frame.columnconfigure(i, weight=1)

        # Search + Buttons
        control_frame = ttk.Frame(self, padding=10)
        control_frame.pack(fill="x")

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.filter_suppliers())
        ttk.Entry(control_frame, textvariable=self.search_var, width=40).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Refresh", command=self.load_suppliers).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Add Supplier", command=self.show_add_modal).pack(side="right", padx=5)

        # Table
        self.tree = ttk.Treeview(self, columns=("ID","SuppID","Name","Phone","Email","Address"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, minwidth=50, width=120)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.on_edit)

        # Right-click menu for Delete
        self.rc_menu = tk.Menu(self, tearoff=0)
        self.rc_menu.add_command(label="Edit", command=self.rc_edit)
        self.rc_menu.add_command(label="Delete", command=self.rc_delete)
        self.tree.bind("<Button-3>", self.show_rc_menu)

    def load_stats(self):
        conn = self.db_connect()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM suppliers")
        count = c.fetchone()[0]
        self.total_suppliers.set(count)
        self.active_suppliers.set(count)  # no active/inactive tracking here

        # Dummy product & recent orders count for UI consistency
        self.total_products.set("0")
        self.recent_orders.set("0")
        conn.close()

    def load_suppliers(self):
        conn = self.db_connect()
        c = conn.cursor()
        c.execute("SELECT id, supplier_id, name, phone, email, address FROM suppliers ORDER BY id DESC")
        self.suppliers_data = c.fetchall()
        conn.close()
        self.display_suppliers(self.suppliers_data)
        self.load_stats()

    def display_suppliers(self, rows):
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", values=r)

    def filter_suppliers(self):
        term = self.search_var.get().lower()
        filtered = []
        for r in self.suppliers_data:
            if any(term in (str(field).lower() if field else "") for field in r):
                filtered.append(r)
        self.display_suppliers(filtered)

    def show_add_modal(self):
        self.editing_id = None
        self.show_modal("Add Supplier")

    def show_modal(self, title):
        modal = tk.Toplevel(self)
        modal.title(title)
        modal.geometry("400x400")
        modal.transient(self)
        modal.grab_set()

        ttk.Label(modal, text="Supplier ID:*").pack(anchor="w", padx=10, pady=2)
        self.ent_suppid = ttk.Entry(modal)
        self.ent_suppid.pack(fill="x", padx=10)
        if not self.editing_id:
            self.ent_suppid.insert(0, f"SUP{datetime.now().strftime('%H%M%S')}")

        ttk.Label(modal, text="Supplier Name:*").pack(anchor="w", padx=10, pady=2)
        self.ent_name = ttk.Entry(modal)
        self.ent_name.pack(fill="x", padx=10)

        ttk.Label(modal, text="Phone:").pack(anchor="w", padx=10, pady=2)
        self.ent_phone = ttk.Entry(modal)
        self.ent_phone.pack(fill="x", padx=10)

        ttk.Label(modal, text="Email:").pack(anchor="w", padx=10, pady=2)
        self.ent_email = ttk.Entry(modal)
        self.ent_email.pack(fill="x", padx=10)

        ttk.Label(modal, text="Address:").pack(anchor="w", padx=10, pady=2)
        self.txt_address = tk.Text(modal, height=3)
        self.txt_address.pack(fill="x", padx=10)

        btn_frame = ttk.Frame(modal)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Cancel", command=modal.destroy).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Save", command=lambda: self.save_supplier(modal)).pack(side="left", padx=5)

        if self.editing_id:
            # prefill form for edit
            for r in self.suppliers_data:
                if r[0] == self.editing_id:
                    self.ent_suppid.delete(0, tk.END)
                    self.ent_suppid.insert(0, r[1])
                    self.ent_name.insert(0, r[2])
                    if r[3]: self.ent_phone.insert(0, r[3])
                    if r[4]: self.ent_email.insert(0, r[4])
                    if r[5]: self.txt_address.insert("1.0", r[5])

    def save_supplier(self, modal):
        suppid = self.ent_suppid.get().strip()
        name = self.ent_name.get().strip()
        phone = self.ent_phone.get().strip()
        email = self.ent_email.get().strip()
        address = self.txt_address.get("1.0", tk.END).strip()

        if not suppid or not name:
            messagebox.showerror("Error", "Supplier ID and Name are required.")
            return

        conn = self.db_connect()
        c = conn.cursor()
        try:
            if self.editing_id is None:
                c.execute("INSERT INTO suppliers (supplier_id, name, phone, email, address) VALUES (?,?,?,?,?)",
                          (suppid, name, phone, email, address))
            else:
                c.execute("UPDATE suppliers SET supplier_id=?, name=?, phone=?, email=?, address=? WHERE id=?",
                          (suppid, name, phone, email, address, self.editing_id))
            conn.commit()
            modal.destroy()
            self.load_suppliers()
            msg = "added" if self.editing_id is None else "updated"
            messagebox.showinfo("Success", f"Supplier {msg} successfully.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Supplier ID already exists.")
        finally:
            conn.close()

    def on_edit(self, event):
        selected = self.tree.focus()
        if selected:
            values = self.tree.item(selected)["values"]
            self.editing_id = values[0]
            self.show_modal("Edit Supplier")

    def rc_edit(self):
        self.on_edit(None)

    def rc_delete(self):
        selected = self.tree.focus()
        if selected:
            values = self.tree.item(selected)["values"]
            cid = values[0]
            name = values[2]
            if messagebox.askyesno("Confirm", f"Delete supplier '{name}'?"):
                conn = self.db_connect()
                c = conn.cursor()
                c.execute("DELETE FROM suppliers WHERE id=?", (cid,))
                conn.commit()
                conn.close()
                self.load_suppliers()
                messagebox.showinfo("Deleted", "Supplier deleted successfully.")

    def show_rc_menu(self, event):
        try:
            self.tree.selection_set(self.tree.identify_row(event.y))
            self.rc_menu.post(event.x_root, event.y_root)
        finally:
            self.rc_menu.grab_release()

if __name__ == "__main__":
    SupplierManager().mainloop()
