from tkinter import *
from PIL import Image, ImageTk
from tkinter import ttk, messagebox
import sqlite3
import time
import os
import tempfile

# ---------- Global Variables ----------
cart_list = []
chk_print = 0

# Tkinter variables
root = Tk()
root.geometry("1350x700+110+80")
root.title("Inventory Management System ")
root.resizable(False, False)
root.config(bg="white")

var_search = StringVar()
var_cname = StringVar()
var_contact = StringVar()
var_pid = StringVar()
var_pname = StringVar()
var_price = StringVar()
var_qty = StringVar()
var_stock = StringVar()
var_discount = StringVar(value="5")  # Default 5%

def setup_database():
    try:
        con = sqlite3.connect('ims.db')
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS product (
            pid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            qty INTEGER NOT NULL,
            status TEXT DEFAULT 'Active'
        )''')
        cur.execute("SELECT COUNT(*) FROM product")
        count = cur.fetchone()[0]
        if count == 0:
            sample_products = [
                ('Laptop Dell XPS', 85000.00, 10, 'Active'),
                ('iPhone 14 Pro', 125000.00, 5, 'Active'),
                ('Samsung Galaxy S23', 95000.00, 8, 'Active'),
                ('MacBook Air M2', 115000.00, 3, 'Active'),
                ('Sony Headphones', 25000.00, 15, 'Active'),
                ('Logitech Mouse', 2500.00, 20, 'Active'),
                ('Mechanical Keyboard', 8500.00, 12, 'Active'),
                ('4K Monitor', 45000.00, 6, 'Active'),
                ('USB-C Hub', 3500.00, 25, 'Active'),
                ('Webcam HD', 7500.00, 18, 'Active')
            ]
            cur.executemany("INSERT INTO product (name, price, qty, status) VALUES (?, ?, ?, ?)", sample_products)
            con.commit()
        con.close()
    except Exception as e:
        messagebox.showerror("Database Error", f"Error setting up database: {str(e)}")

# ------------- GUI Layout -------------
try:
    icon_title = PhotoImage(file="images/logo1.png")
except:
    icon_title = None

title = Label(root, text="Inventory Management System", image=icon_title, compound=LEFT,
              font=("times new roman", 40, "bold"), bg="#010c48", fg="white", anchor="w", padx=20)
title.place(x=0, y=0, relwidth=1, height=70)

btn_logout = Button(root, text="Logout", command=lambda: logout(), font=("times new roman", 15, "bold"),
                   bg="yellow", cursor="hand2")
btn_logout.place(x=1150, y=10, height=50, width=150)

lbl_clock = Label(root,
                  text="Welcome to Inventory Management System\t\t Date: DD:MM:YYYY\t\t Time: HH:MM:SS",
                  font=("times new roman", 15), bg="#4d636d", fg="white")
lbl_clock.place(x=0, y=70, relwidth=1, height=30)

lbl_footer = Label(root,
                   text="IMS-Inventory Management System ",
                   font=("times new roman", 10), bg="#4d636d", fg="white")
lbl_footer.pack(side=BOTTOM, fill=X)

ProductFrame1 = Frame(root, bd=4, relief=RIDGE, bg="white")
ProductFrame1.place(x=6, y=110, width=410, height=550)

pTitle = Label(ProductFrame1, text="All Products", font=("goudy old style", 20, "bold"), bg="#262626", fg="white")
pTitle.pack(side=TOP, fill=X)

ProductFrame2 = Frame(ProductFrame1, bd=2, relief=RIDGE, bg="white")
ProductFrame2.place(x=2, y=42, width=398, height=90)

lbl_search_1 = Label(ProductFrame2, text="Search Product | By Name", font=("times new roman", 15, "bold"),
                     bg="white", fg="green").place(x=2, y=5)
lbl_search_2 = Label(ProductFrame2, text="Product Name", font=("times new roman", 15, "bold"),
                     bg="white").place(x=2, y=45)
txt_search = Entry(ProductFrame2, textvariable=var_search,
                   font=("times new roman", 15), bg="lightyellow")
txt_search.place(x=128, y=47, width=150, height=22)
btn_search = Button(ProductFrame2, text="Search", command=lambda: search(),
                    font=("goudy old style", 15), bg="#2196f3", fg="white", cursor="hand2")
btn_search.place(x=285, y=45, width=100, height=25)
btn_show_all = Button(ProductFrame2, text="Show All", command=lambda: show(),
                      font=("goudy old style", 15), bg="#083531", fg="white", cursor="hand2")
btn_show_all.place(x=285, y=10, width=100, height=25)

ProductFrame3 = Frame(ProductFrame1, bd=3, relief=RIDGE)
ProductFrame3.place(x=2, y=140, width=398, height=375)
scrolly_pro = Scrollbar(ProductFrame3, orient=VERTICAL)
scrollx_pro = Scrollbar(ProductFrame3, orient=HORIZONTAL)

product_Table = ttk.Treeview(ProductFrame3,
                            columns=("pid", "name", "price", "qty", "status"),
                            yscrollcommand=scrolly_pro.set,
                            xscrollcommand=scrollx_pro.set)
scrollx_pro.pack(side=BOTTOM, fill=X)
scrolly_pro.pack(side=RIGHT, fill=Y)
scrollx_pro.config(command=product_Table.xview)
scrolly_pro.config(command=product_Table.yview)
product_Table.heading("pid", text="P ID")
product_Table.heading("name", text="Name")
product_Table.heading("price", text="Price")
product_Table.heading("qty", text="Quantity")
product_Table.heading("status", text="Status")
product_Table["show"] = "headings"
product_Table.column("pid", width=40)
product_Table.column("name", width=100)
product_Table.column("price", width=100)
product_Table.column("qty", width=40)
product_Table.column("status", width=90)
product_Table.pack(fill=BOTH, expand=1)
product_Table.bind("<ButtonRelease-1>", lambda ev: get_data(ev))

lbl_note = Label(ProductFrame1,
                 text="Note: 'Enter 0 Quantity to remove product from the Cart'",
                 font=("goudy old style", 12), anchor="w", bg="white", fg="red")
lbl_note.pack(side=BOTTOM, fill=X)

# ---- Customer & Cart Areas ----
CustomerFrame = Frame(root, bd=4, relief=RIDGE, bg="white")
CustomerFrame.place(x=420, y=110, width=530, height=70)
cTitle = Label(CustomerFrame, text="Customer Details", font=("goudy old style", 15), bg="lightgray")
cTitle.pack(side=TOP, fill=X)
lbl_name = Label(CustomerFrame, text="Name", font=("times new roman", 15), bg="white")
lbl_name.place(x=5, y=35)
txt_name = Entry(CustomerFrame, textvariable=var_cname, font=("times new roman", 13), bg="lightyellow")
txt_name.place(x=80, y=35, width=180)
lbl_contact = Label(CustomerFrame, text="Contact No.", font=("times new roman", 15), bg="white")
lbl_contact.place(x=270, y=35)
txt_contact = Entry(CustomerFrame, textvariable=var_contact, font=("times new roman", 15), bg="lightyellow")
txt_contact.place(x=380, y=35, width=140)

Cal_Cart_Frame = Frame(root, bd=2, relief=RIDGE, bg="white")
Cal_Cart_Frame.place(x=420, y=190, width=530, height=360)
Cart_Frame = Frame(Cal_Cart_Frame, bd=3, relief=RIDGE)
Cart_Frame.place(x=5, y=5, width=520, height=350)

cartTitle = Label(Cart_Frame, text="Cart \t Total Products: [0]", font=("goudy old style", 15), bg="lightgray")
cartTitle.pack(side=TOP, fill=X)
scrolly_cart = Scrollbar(Cart_Frame, orient=VERTICAL)
scrollx_cart = Scrollbar(Cart_Frame, orient=HORIZONTAL)
CartTable = ttk.Treeview(Cart_Frame, columns=("pid", "name", "price", "qty"),
                         yscrollcommand=scrolly_cart.set, xscrollcommand=scrollx_cart.set)
scrollx_cart.pack(side=BOTTOM, fill=X)
scrolly_cart.pack(side=RIGHT, fill=Y)
scrollx_cart.config(command=CartTable.xview)
scrolly_cart.config(command=CartTable.yview)
CartTable.heading("pid", text="P ID")
CartTable.heading("name", text="Name")
CartTable.heading("price", text="Price")
CartTable.heading("qty", text="Quantity")
CartTable["show"] = "headings"
CartTable.column("pid", width=40)
CartTable.column("name", width=100)
CartTable.column("price", width=90)
CartTable.column("qty", width=30)
CartTable.pack(fill=BOTH, expand=1)
CartTable.bind("<ButtonRelease-1>", lambda ev: get_data_cart(ev))

# Add Cart Widgets
Add_CartWidgets_Frame = Frame(root, bd=2, relief=RIDGE, bg="white")
Add_CartWidgets_Frame.place(x=420, y=550, width=530, height=110)

lbl_p_name = Label(Add_CartWidgets_Frame, text="Product Name", font=("times new roman", 15), bg="white")
lbl_p_name.place(x=5, y=5)
txt_p_name = Entry(Add_CartWidgets_Frame, textvariable=var_pname, font=("times new roman", 15), bg="lightyellow", state='readonly')
txt_p_name.place(x=5, y=35, width=190, height=22)
lbl_p_price = Label(Add_CartWidgets_Frame, text="Price Per Qty", font=("times new roman", 15), bg="white")
lbl_p_price.place(x=230, y=5)
txt_p_price = Entry(Add_CartWidgets_Frame, textvariable=var_price, font=("times new roman", 15), bg="lightyellow", state='readonly')
txt_p_price.place(x=230, y=35, width=150, height=22)
lbl_p_qty = Label(Add_CartWidgets_Frame, text="Quantity", font=("times new roman", 15), bg="white")
lbl_p_qty.place(x=390, y=5)
txt_p_qty = Entry(Add_CartWidgets_Frame, textvariable=var_qty, font=("times new roman", 15), bg="lightyellow")
txt_p_qty.place(x=390, y=35, width=120, height=22)
lbl_inStock = Label(Add_CartWidgets_Frame, text="In Stock", font=("times new roman", 15), bg="white")
lbl_inStock.place(x=5, y=70)
txt_p_qty.bind('<Return>', lambda event: add_update_cart())

btn_clear_cart = Button(Add_CartWidgets_Frame, command=lambda: clear_cart(),
                        text="Clear", font=("times new roman", 15, "bold"), bg="lightgray", cursor="hand2")
btn_clear_cart.place(x=180, y=70, width=150, height=30)
btn_add_cart = Button(Add_CartWidgets_Frame, command=lambda: add_update_cart(),
                      text="Add | Update", font=("times new roman", 15, "bold"), bg="orange", cursor="hand2")
btn_add_cart.place(x=340, y=70, width=180, height=30)

# Billing Area
billFrame = Frame(root, bd=2, relief=RIDGE, bg="white")
billFrame.place(x=953, y=110, width=400, height=410)
BTitle = Label(billFrame, text="Customer Bill Area", font=("goudy old style", 20, "bold"), bg="#262626", fg="white")
BTitle.pack(side=TOP, fill=X)
scrolly_bill = Scrollbar(billFrame, orient=VERTICAL)
scrolly_bill.pack(side=RIGHT, fill=Y)
txt_bill_area = Text(billFrame, yscrollcommand=scrolly_bill.set)
txt_bill_area.pack(fill=BOTH, expand=1)
scrolly_bill.config(command=txt_bill_area.yview)

# Billing Buttons
billMenuFrame = Frame(root, bd=2, relief=RIDGE, bg="white")
billMenuFrame.place(x=953, y=520, width=400, height=140)

lbl_amnt = Label(billMenuFrame, text="Bill Amount\n[0]", font=("goudy old style", 15, "bold"), bg="#3f51b5", fg="white")
lbl_amnt.place(x=2, y=5, width=120, height=70)
lbl_discount = Label(billMenuFrame, text="Discount (%)", font=("goudy old style", 12, "bold"), bg="#8bc34a", fg="white")
lbl_discount.place(x=124, y=5, width=120, height=25)
txt_discount = Entry(billMenuFrame, textvariable=var_discount, font=("goudy old style", 12), justify='center', bg="lightyellow")
txt_discount.place(x=124, y=35, width=120, height=25)
lbl_discount_amount = Label(billMenuFrame, text="Discount\n[0]", font=("goudy old style", 10, "bold"), bg="#8bc34a", fg="white")
lbl_discount_amount.place(x=124, y=65, width=120, height=30)
lbl_net_pay = Label(billMenuFrame, text="Net Pay\n[0]", font=("goudy old style", 15, "bold"), bg="#607d8b", fg="white")
lbl_net_pay.place(x=246, y=5, width=160, height=70)
btn_print = Button(billMenuFrame, text="Print", command=lambda: print_bill(), cursor="hand2",
                   font=("goudy old style", 15, "bold"), bg="lightgreen", fg="white")
btn_print.place(x=2, y=80, width=120, height=50)
btn_clear_all = Button(billMenuFrame, text="Clear All", command=lambda: clear_all(),
                       cursor="hand2", font=("goudy old style", 15, "bold"), bg="gray", fg="white")
btn_clear_all.place(x=124, y=80, width=120, height=50)
btn_generate = Button(billMenuFrame, text="Generate Bill", command=lambda: generate_bill(),
                      cursor="hand2", font=("goudy old style", 15, "bold"), bg="#009688", fg="white")
btn_generate.place(x=246, y=80, width=160, height=50)
txt_discount.bind('<KeyRelease>', lambda event: bill_update())

# --------------------- FUNCTIONS --------------------------

def show():
    con = sqlite3.connect('ims.db')
    cur = con.cursor()
    try:
        cur.execute("select pid,name,price,qty,status from product where status='Active'")
        rows = cur.fetchall()
        product_Table.delete(*product_Table.get_children())
        for row in rows:
            product_Table.insert('', END, values=row)
    except Exception as ex:
        messagebox.showerror("Error", f"Error due to : {str(ex)}")
    finally:
        con.close()

def search():
    con = sqlite3.connect('ims.db')
    cur = con.cursor()
    try:
        if var_search.get() == "":
            messagebox.showerror("Error", "Search input should be required", parent=root)
        else:
            cur.execute("select pid,name,price,qty,status from product where name LIKE '%" + var_search.get() +
                        "%' and status='Active'")
            rows = cur.fetchall()
            if len(rows) != 0:
                product_Table.delete(*product_Table.get_children())
                for row in rows:
                    product_Table.insert('', END, values=row)
            else:
                messagebox.showerror("Error", "No record found!!!", parent=root)
    except Exception as ex:
        messagebox.showerror("Error", f"Error due to : {str(ex)}")
    finally:
        con.close()

def get_data(ev):
    f = product_Table.focus()
    content = (product_Table.item(f))
    row = content['values']
    if row:
        var_pid.set(row[0])
        var_pname.set(row[1])
        var_price.set(row[2])
        lbl_inStock.config(text=f"In Stock [{str(row[3])}]")
        var_stock.set(row[3])
        var_qty.set('1')
        txt_p_qty.focus_set()

def get_data_cart(ev):
    f = CartTable.focus()
    content = (CartTable.item(f))
    row = content['values']
    if row:
        for cart_item in cart_list:
            if cart_item[0] == row[0]:
                var_pid.set(row[0])
                var_pname.set(row[1])
                var_price.set(row[2])
                var_qty.set(row[3])
                lbl_inStock.config(text=f"In Stock [{str(cart_item[4])}]")
                var_stock.set(cart_item[4])
                break

def add_update_cart():
    global cart_list
    if var_pid.get() == "":
        messagebox.showerror("Error", "Please select product from the list", parent=root)
    elif var_qty.get() == "":
        messagebox.showerror("Error", "Quantity is required", parent=root)
    else:
        try:
            qty = int(var_qty.get())
            stock = int(var_stock.get())
            if qty > stock:
                messagebox.showerror("Error", "Invalid Quantity - Exceeds Stock", parent=root)
                return
            price_cal = var_price.get()
            cart_data = [var_pid.get(), var_pname.get(), price_cal, var_qty.get(), var_stock.get()]
            present = "no"
            index_ = 0
            for row in cart_list:
                if var_pid.get() == row[0]:
                    present = "yes"
                    break
                index_ += 1
            if present == "yes":
                op = messagebox.askyesno("Confirm",
                                         "Product already present\nDo you want to Update|Remove from the Cart List", parent=root)
                if op == True:
                    if var_qty.get() == "0":
                        cart_list.pop(index_)
                    else:
                        cart_list[index_][3] = var_qty.get()
            else:
                if qty > 0:
                    cart_list.append(cart_data)
            show_cart()
            bill_update()
            clear_cart()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid quantity", parent=root)

def bill_update():
    global bill_amnt, net_pay, discount
    bill_amnt = 0
    net_pay = 0
    discount = 0
    for row in cart_list:
        bill_amnt = bill_amnt + (float(row[2]) * int(row[3]))
    try:
        discount_percent = float(var_discount.get())
    except:
        discount_percent = 0
    discount = (bill_amnt * discount_percent) / 100
    net_pay = bill_amnt - discount
    lbl_amnt.config(text=f"Bill Amount\n₹{bill_amnt:.2f}")
    lbl_discount_amount.config(text=f"Discount\n₹{discount:.2f}")
    lbl_net_pay.config(text=f"Net Pay\n₹{net_pay:.2f}")
    cartTitle.config(text=f"Cart \t Total Products: [{str(len(cart_list))}]")

def show_cart():
    CartTable.delete(*CartTable.get_children())
    for row in cart_list:
        CartTable.insert('', END, values=row)

def generate_bill():
    global chk_print, invoice
    if var_cname.get() == "" or var_contact.get() == "":
        messagebox.showerror("Error", f"Customer Details are required", parent=root)
    elif len(cart_list) == 0:
        messagebox.showerror("Error", f"Please Add product to the Cart!!!", parent=root)
    else:
        os.makedirs("bill", exist_ok=True)
        bill_top()
        bill_middle()
        bill_bottom()
        fp = open(f'bill/{str(invoice)}.txt', 'w')
        fp.write(txt_bill_area.get('1.0', END))
        fp.close()
        messagebox.showinfo("Saved", "Bill has been generated", parent=root)
        chk_print = 1

def bill_top():
    global invoice
    invoice = int(time.strftime("%H%M%S")) + int(time.strftime("%d%m%Y"))
    bill_top_temp = f'''
\t\tXYZ-Inventory
\t Phone No. 9899459288 , Delhi-110053
{str("="*46)}
 Customer Name: {var_cname.get()}
 Ph. no. : {var_contact.get()}
 Bill No. {str(invoice)}\t\t\tDate: {str(time.strftime("%d/%m/%Y"))}
{str("="*46)}
 Product Name\t\t\tQTY\tPrice
{str("="*46)}
'''
    txt_bill_area.delete('1.0', END)
    txt_bill_area.insert('1.0', bill_top_temp)

def bill_bottom():
    bill_bottom_temp = f'''
{str("="*46)}
 Bill Amount\t\t\t\tRs.{bill_amnt:.2f}
 Discount\t\t\t\tRs.{discount:.2f}
 Net Pay\t\t\t\tRs.{net_pay:.2f}
{str("="*46)}\n
'''
    txt_bill_area.insert(END, bill_bottom_temp)

def bill_middle():
    con = sqlite3.connect('ims.db')
    cur = con.cursor()
    try:
        for row in cart_list:
            pid = row[0]
            name = row[1]
            qty = int(row[4]) - int(row[3])
            if int(row[3]) == int(row[4]):
                status = "Inactive"
            else:
                status = "Active"
            price = float(row[2]) * int(row[3])
            txt_bill_area.insert(END, "\n " + name + "\t\t\t" + row[3] + "\tRs." + str(price))
            cur.execute("update product set qty=?,status=? where pid=?", (qty, status, pid))
            con.commit()
        con.close()
        show()
    except Exception as ex:
        messagebox.showerror("Error", f"Error due to : {str(ex)}", parent=root)

def clear_cart():
    var_pid.set("")
    var_pname.set("")
    var_price.set("")
    var_qty.set("")
    lbl_inStock.config(text=f"In Stock")
    var_stock.set("")

def clear_all():
    global cart_list, chk_print
    if messagebox.askyesno("Confirm", "Are you sure you want to clear all data?", parent=root):
        cart_list.clear()
        clear_cart()
        show()
        show_cart()
        var_cname.set("")
        var_contact.set("")
        var_discount.set("5")
        chk_print = 0
        txt_bill_area.delete('1.0', END)
        cartTitle.config(text="Cart \t Total Products: [0]")
        var_search.set("")
        bill_update()

def update_date_time():
    time_ = time.strftime("%I:%M:%S")
    date_ = time.strftime("%d-%m-%Y")
    lbl_clock.config(text=f"Welcome to Inventory Management System\t\t Date: {str(date_)}\t\t Time: {str(time_)}")
    lbl_clock.after(1000, update_date_time)

def print_bill():
    global chk_print
    if chk_print == 1:
        messagebox.showinfo("Print", "Please wait while printing", parent=root)
        try:
            new_file = tempfile.mktemp('.txt')
            with open(new_file, 'w') as f:
                f.write(txt_bill_area.get('1.0', END))
            os.startfile(new_file, 'print')
        except Exception as e:
            messagebox.showerror("Print Error", f"Error printing: {str(e)}", parent=root)
    else:
        messagebox.showinfo("Print", "Please generate bill to print the receipt", parent=root)

def logout():
    if messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?", parent=root):
        root.destroy()

# ------------------ INIT APP -------------------
setup_database()
show()
update_date_time()
root.mainloop()
