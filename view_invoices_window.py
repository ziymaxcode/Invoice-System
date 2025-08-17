import customtkinter as ctk
from db_connector import get_db_connection
from fpdf import FPDF
from tkinter import filedialog, messagebox
import sqlite3
import os
import sys # Import the 'sys' module

# --- NEW HELPER FUNCTION ---
def get_asset_path(filename):
    """Gets the correct path for asset files like fonts."""
    if getattr(sys, 'frozen', False):
        # Running as a bundled .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as a .py script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)


class ViewInvoicesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        top_bar = ctk.CTkFrame(self)
        top_bar.pack(side="top", fill="x", padx=10, pady=10)
        
        back_button = ctk.CTkButton(top_bar, text="< Back to Menu", command=lambda: controller.show_frame("MainMenuFrame"))
        back_button.pack(side="left")
        
        ctk.CTkLabel(top_bar, text="View Past Invoices", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", expand=True)

        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        self.list_frame = ctk.CTkFrame(content_frame, width=300)
        self.list_frame.pack(side="left", fill="y", padx=10, pady=10)
        self.search_frame = ctk.CTkFrame(self.list_frame)
        self.search_frame.pack(fill="x", padx=5, pady=5)
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search by customer name...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.search_button = ctk.CTkButton(self.search_frame, text="Go", width=40, command=self.search_invoices)
        self.search_button.pack(side="left")
        self.clear_button = ctk.CTkButton(self.list_frame, text="Clear Search / Show All", command=self.clear_search)
        self.clear_button.pack(fill="x", padx=5, pady=(0, 10))
        self.invoice_list_frame = ctk.CTkScrollableFrame(self.list_frame)
        self.invoice_list_frame.pack(fill="both", expand=True)

        self.details_frame = ctk.CTkFrame(content_frame)
        self.details_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.details_textbox = ctk.CTkTextbox(self.details_frame, font=("Courier", 12))
        self.details_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.details_textbox.configure(state="disabled")
        self.pdf_button = ctk.CTkButton(self.details_frame, text="Save to PDF", command=self.generate_pdf, state="disabled")
        self.pdf_button.pack(pady=10)

    def load_data(self):
        self.clear_search()
        self.details_textbox.configure(state="normal")
        self.details_textbox.delete("1.0", "end")
        self.details_textbox.configure(state="disabled")
        self.pdf_button.configure(state="disabled")

    def search_invoices(self):
        search_term = self.search_entry.get()
        if search_term: self.load_invoice_list(search_query=search_term)

    def clear_search(self):
        self.search_entry.delete(0, 'end')
        self.load_invoice_list()

    def load_invoice_list(self, search_query=None):
        for widget in self.invoice_list_frame.winfo_children():
            widget.destroy()
        conn, cursor = get_db_connection()
        if not conn: return
        query = "SELECT i.id, i.invoice_date, i.total_amount, c.name FROM invoices i JOIN customers c ON i.customer_id = c.id"
        params = []
        if search_query:
            query += " WHERE c.name LIKE ?"
            params.append(f"%{search_query}%")
        query += " ORDER BY i.id DESC"
        cursor.execute(query, params)
        invoices = cursor.fetchall()
        cursor.close()
        conn.close()
        if not invoices:
            ctk.CTkLabel(self.invoice_list_frame, text="No invoices found.").pack()
            return
        for invoice in invoices:
            inv_id, inv_date, inv_total, cust_name = invoice['id'], invoice['invoice_date'], invoice['total_amount'], invoice['name']
            # Make sure to use the Rupee symbol here if you changed it elsewhere
            button_text = f"Inv #{inv_id} - {cust_name} - ₹{inv_total:.2f}"
            btn = ctk.CTkButton(self.invoice_list_frame, text=button_text, command=lambda inv_id=inv_id: self.display_invoice_details(inv_id))
            btn.pack(fill="x", padx=5, pady=2)

    def display_invoice_details(self, invoice_id):
        conn, cursor = get_db_connection()
        if not conn: return
        query_main = "SELECT i.invoice_date, i.total_amount, c.name, c.phone, c.address FROM invoices i JOIN customers c ON i.customer_id = c.id WHERE i.id = ?"
        cursor.execute(query_main, (invoice_id,))
        main_details = cursor.fetchone()
        query_items = "SELECT ii.quantity, ii.price_per_unit, p.name FROM invoice_items ii JOIN products p ON ii.product_id = p.id WHERE ii.invoice_id = ?"
        cursor.execute(query_items, (invoice_id,))
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        if not main_details: return
        date, total, name, phone, address = main_details['invoice_date'], main_details['total_amount'], main_details['name'], main_details['phone'], main_details['address']
        details_text = f"Invoice #: {invoice_id}\nDate: {date}\n\nBill To:\n  {name}\n"
        if phone: details_text += f"  {phone}\n"
        if address: details_text += f"  {address}\n"
        details_text += "="*50 + "\n\n"
        details_text += f"{'Product':<30}{'Qty':<10}{'Price':<15}{'Total':<15}\n" + "-"*70 + "\n"
        for item in items:
            qty, price, prod_name = item['quantity'], item['price_per_unit'], item['name']
            line_total = qty * price
            price_formatted = f"₹{price:.2f}"
            total_formatted = f"₹{line_total:.2f}"
            details_text += f"{prod_name:<30}{qty:<10}{price_formatted:<15}{total_formatted:<15}\n"
        details_text += "\n" + "="*50 + "\n" + f"{'GRAND TOTAL:':>55} ₹{total:.2f}\n"
        self.details_textbox.configure(state="normal")
        self.details_textbox.delete("1.0", "end")
        self.details_textbox.insert("1.0", details_text)
        self.details_textbox.configure(state="disabled")
        self.current_invoice_details = details_text
        self.current_invoice_id = invoice_id
        self.pdf_button.configure(state="normal")

    def generate_pdf(self):
        if not self.current_invoice_details:
            return

        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Documents", "*.pdf")],
                initialfile=f"Invoice_{self.current_invoice_id}.pdf",
                title="Save Invoice as PDF"
            )
        except Exception:
            messagebox.showerror("Error", "Could not open file dialog.", parent=self.controller)
            return
        
        if not filepath:
            return

        pdf = FPDF()
        pdf.add_page()
        
        # --- FIX IS HERE ---
        # Add and set the new font that supports Unicode characters like '₹'
        try:
            font_path = get_asset_path("DejaVuSans.ttf")
            if not os.path.exists(font_path):
                messagebox.showerror("Font Error", "DejaVuSans.ttf not found. Please place it next to the application file.", parent=self.controller)
                return
            
            pdf.add_font("DejaVu", "", font_path)
            pdf.set_font("DejaVu", size=10)
        except Exception as e:
            messagebox.showerror("Font Error", f"Could not load the font: {e}", parent=self.controller)
            return
        
        # Now we can write the text directly without special encoding
        pdf.multi_cell(0, 5, self.current_invoice_details)
        
        try:
            pdf.output(filepath)
            if os.path.exists(filepath):
                messagebox.showinfo("Success", f"PDF saved successfully to:\n{filepath}", parent=self.controller)
            else:
                messagebox.showerror("Save Error", "Failed to save the PDF file for an unknown reason.", parent=self.controller)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF: {e}", parent=self.controller)
