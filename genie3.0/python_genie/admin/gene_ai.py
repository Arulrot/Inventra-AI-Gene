# gene_ai.py
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "inventory.db"

def run_analysis():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Clear old recommendations (optional - keep if you want all history)
    cur.execute("DELETE FROM ai_recommendations")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # === Low Stock Alerts ===
    cur.execute("SELECT product_id, name, current_stock FROM products WHERE current_stock <= minimum_stock AND current_stock > 0")
    for pid, name, stock in cur.fetchall():
        cur.execute("""INSERT INTO ai_recommendations (message, created_date, priority, type, product_name, product_id, current_stock)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (f"Restock {name} soon – low stock warning.",
                     now_str, 4, "LOW_STOCK", name, pid, stock))

    # === Expiry Alerts ===
    warning_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    cur.execute("""SELECT product_id, name, expiry_date, current_stock
                   FROM products
                   WHERE expiry_date IS NOT NULL AND expiry_date != ''
                   AND DATE(expiry_date) <= DATE(?) AND current_stock > 0""",
                   (warning_date,))
    for pid, name, exp_date, stock in cur.fetchall():
        days_to_expiry = (datetime.strptime(exp_date, "%Y-%m-%d") - datetime.now()).days
        if days_to_expiry <= 0:
            msg = f"{name} has expired!"
            prio = 5
        elif days_to_expiry <= 7:
            msg = f"{name} is expiring in {days_to_expiry} days!"
            prio = 5
        else:
            msg = f"Consider promoting {name} – expiring within {days_to_expiry} days."
            prio = 3
        cur.execute("""INSERT INTO ai_recommendations (message, created_date, priority, type, product_name, product_id, current_stock)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (msg, now_str, prio, "EXPIRY_WARNING", name, pid, stock))

    # === Non-Movable Stock ===
    non_mov_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    cur.execute("""SELECT product_id, name, current_stock FROM products
                   WHERE date_added <= ? AND total_sold = 0 AND current_stock > 0""",
                   (non_mov_date,))
    for pid, name, stock in cur.fetchall():
        cur.execute("""INSERT INTO ai_recommendations (message, created_date, priority, type, product_name, product_id, current_stock)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (f"{name} is stagnant; review pricing or create bundle offers.",
                     now_str, 2, "NON_MOVABLE", name, pid, stock))

    conn.commit()
    conn.close()
    print("✅ Gene AI analysis completed and recommendations updated.")

if __name__ == "__main__":
    run_analysis()
