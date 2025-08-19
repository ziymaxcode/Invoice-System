import os
import sys
import qrcode
from fpdf import FPDF
from tkinter import messagebox
from datetime import datetime

def get_asset_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

def generate_professional_pdf(invoice_details):
    # ... (This function is unchanged)
    pdf = FPDF()
    shop_details = {
        "name": "Ziyan's Hardware Store",
        "address": "123 Main Street, City, State - 12345",
        "gstin": "GSTIN: 29ABCDE1234F1Z5",
        "contact": "9876543210",
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
    def draw_page_header(pdf, invoice_details, shop_details):
        pdf.add_page()
        pdf.set_font("DejaVu", "B", size=20)
        pdf.cell(0, 10, shop_details['name'], ln=True, align='C')
        pdf.set_font("DejaVu", "", size=10)
        pdf.cell(0, 5, shop_details['address'], ln=True, align='C')
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
    draw_page_header(pdf, invoice_details, shop_details)
    pdf.set_font("DejaVu", "", size=10)
    for item in invoice_details['items']:
        if pdf.get_y() > 250:
            draw_page_header(pdf, invoice_details, shop_details)
            pdf.set_font("DejaVu", "", size=10)
        pdf.cell(100, 8, item['name'], border=1)
        pdf.cell(20, 8, str(item['quantity']), border=1, align='C')
        pdf.cell(35, 8, f"₹{item['price_per_unit']:.2f}", border=1, align='R')
        pdf.cell(35, 8, f"₹{item['quantity'] * item['price_per_unit']:.2f}", border=1, align='R', ln=True)
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

def generate_return_note_pdf(return_details):
    # ... (This function is unchanged)
    pdf = FPDF()
    pdf.add_page()
    shop_details = {
        "name": "Ziyan's Hardware Store",
        "address": "123 Main Street, City, State - 12345",
        "gstin": "GSTIN: 29ABCDE1234F1Z5",
        "contact": "9876543210"
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
    pdf.set_font("DejaVu", "B", size=20)
    pdf.cell(0, 10, "Credit Note / Return Receipt", ln=True, align='C')
    pdf.set_font("DejaVu", "", size=10)
    pdf.cell(0, 5, shop_details['name'], ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", size=12)
    pdf.cell(100, 8, f"Return ID: {return_details['id']}")
    pdf.cell(90, 8, f"Return Date: {return_details['date']}", align='R', ln=True)
    pdf.set_font("DejaVu", "", size=10)
    pdf.cell(0, 8, f"Original Invoice #: {return_details['original_invoice_id']}", ln=True)
    pdf.cell(0, 8, f"Customer: {return_details['customer_name']}", ln=True)
    pdf.ln(5)
    pdf.set_font("DejaVu", "B", size=10)
    pdf.cell(120, 8, "Returned Product", border=1)
    pdf.cell(30, 8, "Qty", border=1, align='C')
    pdf.cell(40, 8, "Refund Amount", border=1, align='R', ln=True)
    pdf.set_font("DejaVu", "", size=10)
    for item in return_details['items']:
        pdf.cell(120, 8, item['name'], border=1)
        pdf.cell(30, 8, str(item['quantity']), border=1, align='C')
        pdf.cell(40, 8, f"₹{item['quantity'] * item['price_per_unit']:.2f}", border=1, align='R', ln=True)
    pdf.ln(5)
    pdf.set_font("DejaVu", "B", size=12)
    pdf.cell(150, 8, "Total Refund Amount:", align='R')
    pdf.cell(40, 8, f"₹{return_details['total_refund']:.2f}", align='R', ln=True)
    return pdf

# --- UPDATED: Renamed from generate_ledger_pdf to generate_statement_pdf ---
def generate_statement_pdf(statement_data):
    # ... (This function is unchanged, but renamed for clarity)
    pdf = FPDF()
    pdf.add_page()
    try:
        font_path = get_asset_path("DejaVuSans.ttf")
        if not os.path.exists(font_path):
            raise FileNotFoundError("DejaVuSans.ttf not found.")
        pdf.add_font("DejaVu", "", font_path)
        pdf.add_font("DejaVu", "B", font_path)
    except Exception as e:
        messagebox.showerror("Font Error", f"Could not load font: {e}")
        return None
    pdf.set_font("DejaVu", "B", size=16)
    pdf.cell(0, 10, f"Statement: {statement_data['customer']['name']}", ln=True)
    pdf.set_font("DejaVu", "", size=10)
    if statement_data['customer']['phone']:
        pdf.cell(0, 5, f"Contact: {statement_data['customer']['phone']}", ln=True)
    pdf.cell(0, 5, f"Report Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", ln=True)
    pdf.ln(5)
    summary_box_y = pdf.get_y()
    pdf.set_font("DejaVu", "", size=10)
    pdf.rect(x=10, y=summary_box_y, w=190, h=30)
    pdf.set_xy(15, summary_box_y + 5)
    pdf.cell(60, 8, "Total Debit(-)")
    pdf.set_font("DejaVu", "B", size=12)
    pdf.set_xy(15, summary_box_y + 15)
    pdf.cell(60, 8, f"₹{statement_data['total_debit']:.2f}")
    pdf.set_xy(75, summary_box_y + 5)
    pdf.set_font("DejaVu", "", size=10)
    pdf.cell(60, 8, "Total Credit(+)")
    pdf.set_font("DejaVu", "B", size=12)
    pdf.set_xy(75, summary_box_y + 15)
    pdf.cell(60, 8, f"₹{statement_data['total_credit']:.2f}")
    pdf.set_xy(135, summary_box_y + 5)
    pdf.set_font("DejaVu", "", size=10)
    pdf.cell(60, 8, "Net Balance")
    pdf.set_font("DejaVu", "B", size=12)
    pdf.set_xy(135, summary_box_y + 15)
    balance_status = "Dr" if statement_data['customer']['balance'] > 0 else "Cr"
    pdf.cell(60, 8, f"₹{abs(statement_data['customer']['balance']):.2f} {balance_status}")
    pdf.ln(35)
    pdf.set_font("DejaVu", "B", size=10)
    pdf.cell(30, 8, "Date", border=1)
    pdf.cell(80, 8, "Details", border=1)
    pdf.cell(25, 8, "Debit", border=1, align='R')
    pdf.cell(25, 8, "Credit", border=1, align='R')
    pdf.cell(30, 8, "Balance", border=1, align='R', ln=True)
    pdf.set_font("DejaVu", "", size=9)
    for trans in statement_data['transactions']:
        if pdf.get_y() > 260:
            pdf.add_page()
        pdf.cell(30, 8, trans['transaction_date'], border=1)
        pdf.multi_cell(80, 8, trans['details'], border=1, align='L')
        current_y = pdf.get_y()
        pdf.set_xy(120, current_y - 8)
        pdf.cell(25, 8, f"₹{trans['debit']:.2f}" if trans['debit'] > 0 else "", border=1, align='R')
        pdf.cell(25, 8, f"₹{trans['credit']:.2f}" if trans['credit'] > 0 else "", border=1, align='R')
        balance_status = "Dr" if trans['balance_after'] > 0 else "Cr"
        pdf.cell(30, 8, f"₹{abs(trans['balance_after']):.2f} {balance_status}", border=1, align='R', ln=True)
    return pdf

# --- NEW: Function to generate a Sales Ledger PDF ---
def generate_sales_ledger_pdf(ledger_data):
    pdf = FPDF()
    pdf.add_page()
    
    try:
        font_path = get_asset_path("DejaVuSans.ttf")
        if not os.path.exists(font_path):
            raise FileNotFoundError("DejaVuSans.ttf not found.")
        pdf.add_font("DejaVu", "", font_path)
        pdf.add_font("DejaVu", "B", font_path)
    except Exception as e:
        messagebox.showerror("Font Error", f"Could not load font: {e}")
        return None

    # --- Header ---
    pdf.set_font("DejaVu", "B", size=16)
    pdf.cell(0, 10, "Sales Ledger Report", ln=True)
    pdf.set_font("DejaVu", "", size=10)
    pdf.cell(0, 5, f"Period: {ledger_data['start_date']} to {ledger_data['end_date']}", ln=True)
    pdf.ln(5)

    # --- Transactions Table ---
    pdf.set_font("DejaVu", "B", size=10)
    pdf.cell(25, 8, "Date", border=1)
    pdf.cell(45, 8, "Customer", border=1)
    pdf.cell(85, 8, "Narration (Products)", border=1)
    pdf.cell(35, 8, "Amount", border=1, align='R', ln=True)

    pdf.set_font("DejaVu", "", size=9)
    total_sales = 0
    for invoice in ledger_data['invoices']:
        if pdf.get_y() > 260: # New page check
            pdf.add_page()
        
        narration = ", ".join([item['name'] for item in invoice['items']])
        
        pdf.cell(25, 8, invoice['invoice_date'], border=1)
        pdf.cell(45, 8, invoice['name'], border=1)
        
        # Store Y position before multi_cell
        pre_multi_cell_y = pdf.get_y()
        pdf.multi_cell(85, 8, narration, border=1, align='L')
        post_multi_cell_y = pdf.get_y()
        
        # Calculate height of multi_cell and draw other cells
        cell_height = post_multi_cell_y - pre_multi_cell_y
        pdf.set_xy(165, pre_multi_cell_y)
        pdf.cell(35, cell_height, f"₹{invoice['total_amount']:.2f}", border=1, align='R', ln=True)
        
        total_sales += invoice['total_amount']

    # --- Totals ---
    pdf.ln(5)
    pdf.set_font("DejaVu", "B", size=10)
    pdf.cell(155, 8, "Grand Total:", border=1, align='R')
    pdf.cell(35, 8, f"₹{total_sales:.2f}", border=1, align='R', ln=True)

    return pdf
