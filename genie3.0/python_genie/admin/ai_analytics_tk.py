import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from collections import Counter

# Matplotlib for charts
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

DB_PATH = "inventory.db"

class AIAnalyticsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Analytics - Inventor AI Genie")
        self.geometry("1100x700")

        self.create_ui()
        self.load_analytics()

    def db_connect(self):
        return sqlite3.connect(DB_PATH)

    def create_ui(self):
        # Summary Frame
        summary_frame = ttk.Frame(self, padding=10)
        summary_frame.pack(fill="x")

        self.critical_var = tk.StringVar(value="0")
        self.warning_var = tk.StringVar(value="0")
        self.info_var = tk.StringVar(value="0")
        self.completed_var = tk.StringVar(value="0")  # Placeholder

        stats = [
            ("Critical Alerts", self.critical_var, "red"),
            ("Warnings", self.warning_var, "orange"),
            ("Recommendations", self.info_var, "blue"),
            ("Actions Taken", self.completed_var, "green"),
        ]
        for i, (label, var, color) in enumerate(stats):
            lf = ttk.LabelFrame(summary_frame, text=label, padding=10)
            lf.grid(row=0, column=i, padx=5, sticky="nsew")
            ttk.Label(lf, textvariable=var, foreground=color,
                      font=("Segoe UI", 20, "bold")).pack()
        for i in range(len(stats)):
            summary_frame.columnconfigure(i, weight=1)

        # Charts Frame (Matplotlib)
        charts_frame = ttk.Frame(self, padding=10)
        charts_frame.pack(fill="x")

        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(8, 4))
        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=charts_frame)
        self.canvas.get_tk_widget().pack(fill="x")

        # Table Frame
        table_frame = ttk.Frame(self, padding=10)
        table_frame.pack(fill="both", expand=True)

        ttk.Label(table_frame, text="Detailed AI Recommendations",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w")

        self.tree = ttk.Treeview(table_frame, columns=("Priority","Type","Product","Message","Date"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill="both", expand=True)

        # Refresh button
        ttk.Button(self, text="Refresh Analytics", command=self.refresh_analytics).pack(pady=5)

    def load_analytics(self):
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute("SELECT message, created_date, priority, type, product_name, current_stock, product_id FROM ai_recommendations")
        rows = cur.fetchall()
        conn.close()

        # Update summary counts
        critical_count = len([r for r in rows if r[2] >= 4])
        warning_count = len([r for r in rows if r[2] == 3])
        info_count = len([r for r in rows if r[2] <= 2])
        completed_count = 0  # Placeholder

        self.critical_var.set(critical_count)
        self.warning_var.set(warning_count)
        self.info_var.set(info_count)
        self.completed_var.set(completed_count)

        # Update charts
        self.update_charts(rows)

        # Update table
        self.tree.delete(*self.tree.get_children())
        for msg, created, priority, rtype, prod_name, stock, pid in rows:
            self.tree.insert("", "end", values=(
                f"{priority}/5",
                rtype or "N/A",
                prod_name or "System",
                msg,
                created
            ))

    def update_charts(self, rows):
        # Recommendation Types Pie/Doughnut
        type_counts = Counter(r[3] for r in rows if r[3])
        self.ax1.clear()
        if type_counts:
            self.ax1.pie(type_counts.values(), labels=type_counts.keys(), autopct="%1.0f%%")
        self.ax1.set_title("Recommendation Types")

        # Priority Bar Chart
        priority_counts = Counter(r[2] for r in rows if r[2])
        self.ax2.clear()
        self.ax2.bar(priority_counts.keys(), priority_counts.values(), color=["#78909c","#26a69a","#ffa726","#ff6b4a","#ff4757"])
        self.ax2.set_title("Priority Distribution")
        self.ax2.set_xlabel("Priority")
        self.ax2.set_ylabel("Count")

        self.canvas.draw()

    def refresh_analytics(self):
        # Simulate AI Analysis process
        messagebox.showinfo("AI Analysis", "Running AI Analysis... (placeholder)\nData will be refreshed.")
        self.load_analytics()

if __name__ == "__main__":
    AIAnalyticsApp().mainloop()
