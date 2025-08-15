import tkinter as tk
from tkinter import ttk, messagebox
import subprocess, sys, os, datetime

# --- DEBUG LOG FILE ---
LOG_FILE = os.path.abspath("launcher_debug.log")

def debug_log(message):
    """Append debug messages to the log file."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()} - {message}\n")

# --- USER LOGIN DATA ---
users = {
    "Administrator Panel": {
        "username": "admin",
        "password": "admin123",
        "file": os.path.join("admin", "mainpannel.py")  # Path to your admin panel file
    },
    "Billing & POS": {
        "username": "billing",
        "password": "billing123",
        "file": os.path.join("billing", "pos_home.py")
    }
}

def authenticate():
    section = section_var.get()
    username = username_var.get().strip()
    password = password_var.get().strip()

    debug_log(f"Attempting login: section='{section}', user='{username}'")

    if not username or not password:
        messagebox.showerror("Error", "Please enter both username and password.")
        debug_log("Login failed - missing username or password")
        return

    user = users.get(section)
    if user and username == user["username"] and password == user["password"]:
        messagebox.showinfo("Login Successful", f"Welcome! Opening {section}...")
        debug_log(f"Login successful for {section}")

        root.destroy()

        # Resolve full path
        script_path = os.path.abspath(user["file"])
        debug_log(f"Resolved script path: {script_path}")

        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"File not found:\n{script_path}")
            debug_log("ERROR - file not found.")
            return

        try:
            python_exe = sys.executable
            debug_log(f"Launching subprocess: {python_exe} {script_path}")
            # Capture stdout/stderr into a log file for debugging
            with open(LOG_FILE, "a", encoding="utf-8") as logf:
                logf.write(f"\n---- NEW LAUNCH: {datetime.datetime.now()} ----\n")
                subprocess.Popen(
                    [python_exe, script_path],
                    cwd=os.path.dirname(script_path),
                    stdout=logf, stderr=logf
                )
        except Exception as e:
            messagebox.showerror("Launch Error", str(e))
            debug_log(f"Launch exception: {e}")
    else:
        messagebox.showerror("Login Failed", f"Incorrect username or password for {section}.")
        password_var.set("")
        debug_log("Login failed - incorrect credentials")

# ----------------- GUI -----------------
root = tk.Tk()
root.title("Retail AI Login - Inventa AI Gene")
root.geometry("400x400")
root.configure(bg="#f0f0f0")
root.resizable(False, False)

tk.Label(root, text="💻 InventaAI", font=("Segoe UI", 20, "bold"),
         fg="#5f2c82", bg="#f0f0f0").pack(pady=(20, 5))
tk.Label(root, text="AI-powered Inventory & Billing Management",
         font=("Segoe UI", 10), bg="#f0f0f0").pack(pady=(0, 15))

frame = tk.Frame(root, bg="white", bd=2, relief=tk.RIDGE)
frame.pack(padx=20, pady=10, fill="both", expand=True)

section_var = tk.StringVar(value="Administrator Panel")
ttk.Label(frame, text="Section:").pack(anchor="w", pady=(15, 3), padx=10)
ttk.Combobox(frame, textvariable=section_var, state="readonly",
             values=["Administrator Panel", "Billing & POS"]).pack(padx=10, fill="x")

username_var = tk.StringVar()
ttk.Label(frame, text="Username:").pack(anchor="w", pady=(10, 3), padx=10)
ttk.Entry(frame, textvariable=username_var).pack(padx=10, fill="x")

password_var = tk.StringVar()
ttk.Label(frame, text="Password:").pack(anchor="w", pady=(10, 3), padx=10)
ttk.Entry(frame, textvariable=password_var, show="*").pack(padx=10, fill="x")

tk.Button(frame, text="Login →", bg="#5f2c82", fg="white",
          font=("Segoe UI", 10, "bold"), command=authenticate)\
    .pack(pady=20, ipadx=10, ipady=5)

demo = tk.LabelFrame(frame, text="Demo Credentials", padx=10, pady=10)
demo.pack(fill="x", padx=10, pady=5)
tk.Label(demo, text="Admin: admin / admin123", anchor="w").pack(fill="x")
tk.Label(demo, text="Billing: billing / billing123", anchor="w").pack(fill="x")

root.mainloop()
