import os
import sys
import qrcode
from fpdf import FPDF
from tkinter import messagebox

# --- Helper function to find asset files ---
def get_asset_path(filename):
    if getattr(sys, 'frozen', False):
        # Running as a bundled .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as a .py script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

# --- NEW: Helper function to draw headers on each page ---
def draw_page_header(pdf, invoice_details, shop_details):
    pdf.set_font("DejaVu", "B", size=20)
    pdf.cell(0, 10, shop_details['name'], ln=True, align='C')
    pdf.set_font("DejaVu", "", size=10)
    pdf.cell(0, 5, shop_details['address'], ln=True, align='C')
    # --- UPDATED: Added contact number to the header ---
    pdf.cell(0, 5, f"{shop_details['gstin']} | Contact: {shop_details['contact']}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", size=12)
    pdf.cell(100, 8, f"Invoice #: {invoice_details['id']}")
    pdf.cell(90, 8, f"Date: {invoice_details['date']}", align='R', ln=True)
    pdf.set_font("DejaVu", "", size=10)
    pdf.cell(0, 8, f"Bill To: {invoice_details['customer_name']}", ln=True)
    if invoice_details['customer_phone']:
        pdf.cell(0, 5, f"Phone: {invoice_details['customer_phone']}", ln=True)
    pdf.ln(5)
    pdf.set_font("DejaVu", "B", size=10)
    pdf.cell(100, 8, "Product", border=1)
    pdf.cell(20, 8, "Qty", border=1, align='C')
    pdf.cell(35, 8, "Price", border=1, align='R')
    pdf.cell(35, 8, "Total", border=1, align='R', ln=True)

# --- PDF Generation Function ---
def generate_professional_pdf(invoice_details):
    pdf = FPDF()
    
    shop_details = {
        "name": "ASHIQ HARDWARE",
        "address": "Near Paradise Ground, 6th Block, Krishnapura, Surathkal, Mangaluru, Karnataka 575014",
        "gstin": "GSTIN: 29ABCDE1234F1Z5",
        "contact": "081059 0622",
        "upi_id": "your-upi-id@oksbi"
    }

    try:
        font_path = get_asset_path("DejaVuSans.ttf")
        if not os.path.exists(font_path):
            raise FileNotFoundError("DejaVuSans.ttf not found.")
        pdf.add_font("DejaVu", "", font_path)
        pdf.add_font("DejaVu", "B", font_path)
    except Exception as e:
        messagebox.showerror("Font Error", f"Could not load font: {e}")
        return None

    # --- UPDATED: Multi-page logic ---
    pdf.add_page()
    draw_page_header(pdf, invoice_details, shop_details)
    
    pdf.set_font("DejaVu", "", size=10)
    for item in invoice_details['items']:
        # Check if there is enough space for the next item, otherwise create a new page
        if pdf.get_y() > 250: # 250 is a safe margin from the bottom
            pdf.add_page()
            draw_page_header(pdf, invoice_details, shop_details)
            pdf.set_font("DejaVu", "", size=10)

        pdf.cell(100, 8, item['name'], border=1)
        pdf.cell(20, 8, str(item['quantity']), border=1, align='C')
        pdf.cell(35, 8, f"₹{item['price_per_unit']:.2f}", border=1, align='R')
        pdf.cell(35, 8, f"₹{item['quantity'] * item['price_per_unit']:.2f}", border=1, align='R', ln=True)
    
    # --- Totals Section (always at the end) ---
    # If totals section is too close to the bottom, add a new page for it
    if pdf.get_y() > 220:
        pdf.add_page()

    pdf.ln(5)
    totals_x_pos = 130
    pdf.set_font("DejaVu", "", size=10)
    pdf.set_x(totals_x_pos)
    pdf.cell(35, 8, "Subtotal:", align='R')
    pdf.cell(35, 8, f"₹{invoice_details['subtotal']:.2f}", align='R', ln=True)
    pdf.set_x(totals_x_pos)
    pdf.cell(35, 8, f"Discount ({invoice_details['discount_percent']}%):", align='R')
    pdf.cell(35, 8, f"-₹{invoice_details['discount_amount']:.2f}", align='R', ln=True)
    
    taxable_amount = invoice_details['subtotal'] - invoice_details['discount_amount']
    cgst_amount = (taxable_amount * invoice_details['cgst_percent']) / 100
    sgst_amount = (taxable_amount * invoice_details['sgst_percent']) / 100
    
    pdf.set_x(totals_x_pos)
    pdf.cell(35, 8, f"CGST ({invoice_details['cgst_percent']}%):", align='R')
    pdf.cell(35, 8, f"+₹{cgst_amount:.2f}", align='R', ln=True)
    pdf.set_x(totals_x_pos)
    pdf.cell(35, 8, f"SGST ({invoice_details['sgst_percent']}%):", align='R')
    pdf.cell(35, 8, f"+₹{sgst_amount:.2f}", align='R', ln=True)

    pdf.set_font("DejaVu", "B", size=12)
    pdf.set_x(totals_x_pos)
    pdf.cell(35, 8, "Grand Total:", align='R')
    pdf.cell(35, 8, f"₹{invoice_details['total']:.2f}", align='R', ln=True)
    pdf.ln(10)

    # --- QR Code for Payment ---
    try:
        upi_string = f"upi://pay?pa={shop_details['upi_id']}&pn={shop_details['name'].replace(' ', '%20')}&am={invoice_details['total']:.2f}&cu=INR"
        qr_img = qrcode.make(upi_string)
        qr_path = get_asset_path("temp_qr.png")
        qr_img.save(qr_path)
        
        pdf.image(qr_path, x=10, y=pdf.get_y(), w=40)
        os.remove(qr_path)

        pdf.set_y(pdf.get_y() - 35)
        pdf.set_x(55)
        pdf.set_font("DejaVu", "B", size=12)
        pdf.cell(0, 10, "Scan to Pay", ln=True)
        pdf.set_x(55)
        pdf.set_font("DejaVu", "", size=10)
        pdf.cell(0, 8, "Thank you for your business!", ln=True)
    except Exception as e:
        print(f"Could not generate QR code: {e}")

    return pdf
