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

# --- PDF Generation Function ---
def generate_professional_pdf(invoice_details):
    pdf = FPDF()
    pdf.add_page()
    
    # --- CUSTOMIZE YOUR SHOP DETAILS HERE ---
    shop_name = "ASHIQ HARDWARE"
    shop_address = "Near Paradise Ground, 6th Block, Krishnapura, Surathkal, Mangaluru, Karnataka 575014"
    shop_contact= "081059 06222"
    shop_gstin = "GSTIN: 29ABCDE1234F1Z5"
    upi_id = "your-upi-id@oksbi" # IMPORTANT: Replace with your actual UPI ID
    # -----------------------------------------

    # Add and set the font
    try:
        font_path = get_asset_path("DejaVuSans.ttf")
        if not os.path.exists(font_path):
            raise FileNotFoundError("DejaVuSans.ttf not found.")
        pdf.add_font("DejaVu", "", font_path)
        pdf.add_font("DejaVu", "B", font_path)
    except Exception as e:
        messagebox.showerror("Font Error", f"Could not load font: {e}")
        return None

    # --- PDF Header ---
    pdf.set_font("DejaVu", "B", size=20)
    pdf.cell(0, 10, shop_name, ln=True, align='C')
    pdf.set_font("DejaVu", "", size=10)
    pdf.cell(0, 5, shop_address, ln=True, align='C')
    pdf.cell(0, 5, shop_gstin, ln=True, align='C')
    pdf.cell(0, 5, shop_contact, ln=True, align='C')
    pdf.ln(10)

    # --- Invoice Info and Customer Details ---
    pdf.set_font("DejaVu", "B", size=12)
    pdf.cell(100, 8, f"Invoice #: {invoice_details['id']}")
    pdf.cell(90, 8, f"Date: {invoice_details['date']}", align='R', ln=True)
    pdf.set_font("DejaVu", "", size=10)
    pdf.cell(0, 8, f"Bill To: {invoice_details['customer_name']}", ln=True)
    if invoice_details['customer_phone']:
        pdf.cell(0, 5, f"Phone: {invoice_details['customer_phone']}", ln=True)
    pdf.ln(5)

    # --- Items Table Header ---
    pdf.set_font("DejaVu", "B", size=10)
    pdf.cell(100, 8, "Product", border=1)
    pdf.cell(20, 8, "Qty", border=1, align='C')
    pdf.cell(35, 8, "Price", border=1, align='R')
    pdf.cell(35, 8, "Total", border=1, align='R', ln=True)

    # --- Items Table Rows ---
    pdf.set_font("DejaVu", "", size=10)
    for item in invoice_details['items']:
        pdf.cell(100, 8, item['name'], border=1)
        pdf.cell(20, 8, str(item['quantity']), border=1, align='C')
        pdf.cell(35, 8, f"₹{item['price_per_unit']:.2f}", border=1, align='R')
        pdf.cell(35, 8, f"₹{item['quantity'] * item['price_per_unit']:.2f}", border=1, align='R', ln=True)
    
    # --- UPDATED: Totals Section with Taxes ---
    pdf.ln(5)
    totals_x_pos = 130
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
        upi_string = f"upi://pay?pa={upi_id}&pn={shop_name.replace(' ', '%20')}&am={invoice_details['total']:.2f}&cu=INR"
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