from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

def generate_invoice(invoice_no, customer_name, items, output_file='pdf_invoice_gen\pdf_inf_cpy\invoice.pdf'):
    c = canvas.Canvas(output_file, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "INVOICE")

    # Company Info
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, "Your Company Name")
    c.drawString(50, height - 100, "123, Your Street, Your City")
    c.drawString(50, height - 120, "Email: youremail@example.com")

    # Invoice Details
    c.drawString(400, height - 80, f"Invoice #: {invoice_no}")
    c.drawString(400, height - 100, f"Date: {datetime.today().strftime('%d-%m-%Y')}")

    # Customer Info
    c.drawString(50, height - 160, f"Billed To: {customer_name}")

    # Table Headers
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 200, "Item")
    c.drawString(300, height - 200, "Qty")
    c.drawString(400, height - 200, "Price")
    c.drawString(500, height - 200, "Total")

    # Table Content
    c.setFont("Helvetica", 12)
    y = height - 220
    grand_total = 0
    for item in items:
        name, qty, price = item
        total = qty * price
        grand_total += total

        c.drawString(50, y, name)
        c.drawString(300, y, str(qty))
        c.drawString(400, y, f"{price:.2f}")
        c.drawString(500, y, f"{total:.2f}")
        y -= 20

    # Grand Total
    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, y - 10, "Grand Total:")
    c.drawString(500, y - 10, f"{grand_total:.2f}")

    c.showPage()
    c.save()
    print(f"Invoice saved as '{output_file}'.")

# Example usage
items = [
    ("Product A", 2, 100.00),
    ("Product B", 1, 250.00),
    ("Service C", 3, 150.00)
]
generate_invoice("INV001", "John Doe", items)
