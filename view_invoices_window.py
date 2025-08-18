import customtkinter as ctk
from db_connector import get_db_connection
from tkinter import filedialog, messagebox
import sqlite3
import os
import csv
import tempfile
import sys
from pdf_generator import generate_professional_pdf

class ViewInvoicesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_invoice_details = None
        self.current_invoices_data = [] # To store data for CSV export

        # --- Top Bar ---
        top_bar = ctk.CTkFrame(self)
        top_bar.pack(side="top", fill="x", padx=10, pady=10)
        back_button = ctk.CTkButton(top_bar, text="< Back to Menu", command=lambda: controller.show_frame("MainMenuFrame"))
        back_button.pack(side="left")
        ctk.CTkLabel(top_bar, text="View Past Invoices", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", expand=True)

        # --- Main Content Frame ---
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # --- Left Panel (Filters, List & Summary) ---
        self.list_frame = ctk.CTkFrame(content_frame, width=450)
        self.list_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        filter_frame = ctk.CTkFrame(self.list_frame)
        filter_frame.pack(fill="x", padx=5, pady=5)
        self.start_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="Start Date (YYYY-MM-DD)")
        self.start_date_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.end_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="End Date (YYYY-MM-DD)")
        self.end_date_entry.pack(side="left", fill="x", expand=True)
        filter_button = ctk.CTkButton(filter_frame, text="Filter", width=50, command=self.filter_invoices)
        filter_button.pack(side="left", padx=5)

        self.search_frame = ctk.CTkFrame(self.list_frame)
        self.search_frame.pack(fill="x", padx=5, pady=5)
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search by customer name...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", lambda event: self.filter_invoices())
        
        self.clear_button = ctk.CTkButton(self.list_frame, text="Clear Filters / Show All", command=self.clear_search)
        self.clear_button.pack(fill="x", padx=5, pady=(0, 10))
        
        self.invoice_list_frame = ctk.CTkScrollableFrame(self.list_frame)
        self.invoice_list_frame.pack(fill="both", expand=True)

        summary_frame = ctk.CTkFrame(self.list_frame)
        summary_frame.pack(fill="x", padx=5, pady=5)
        self.total_sales_label = ctk.CTkLabel(summary_frame, text="Total Sales: ₹0.00", font=ctk.CTkFont(weight="bold"))
        self.total_sales_label.pack(anchor="w")
        self.invoice_count_label = ctk.CTkLabel(summary_frame, text="Invoices Shown: 0")
        self.invoice_count_label.pack(anchor="w")
        export_button = ctk.CTkButton(summary_frame, text="Export List to CSV", command=self.export_to_csv)
        export_button.pack(fill="x", pady=5)

        # --- Right Panel (Details) ---
        self.details_frame = ctk.CTkFrame(content_frame)
        self.details_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.details_textbox = ctk.CTkTextbox(self.details_frame, font=("Courier", 12))
        self.details_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.details_textbox.configure(state="disabled")
        
        button_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        button_frame.pack(pady=10)
        self.open_pdf_button = ctk.CTkButton(button_frame, text="Open PDF", command=self.open_pdf, state="disabled")
        self.open_pdf_button.pack(side="left", padx=5)
        self.pdf_button = ctk.CTkButton(button_frame, text="Save to PDF", command=self.generate_pdf, state="disabled")
        self.pdf_button.pack(side="left", padx=5)

    def filter_invoices(self):
        self.load_invoice_list()

    def load_data(self):
        self.clear_search()

    def clear_search(self):
        self.search_entry.delete(0, 'end')
        self.start_date_entry.delete(0, 'end')
        self.end_date_entry.delete(0, 'end')
        self.load_invoice_list()
        self.details_textbox.configure(state="normal")
        self.details_textbox.delete("1.0", "end")
        self.details_textbox.configure(state="disabled")
        self.pdf_button.configure(state="disabled")
        self.open_pdf_button.configure(state="disabled")
        self.current_invoice_details = None

    def load_invoice_list(self):
        for widget in self.invoice_list_frame.winfo_children():
            widget.destroy()
        conn, cursor = get_db_connection()
        if not conn: return
        
        query = "SELECT i.id, i.invoice_date, i.total_amount, i.status, c.name FROM invoices i JOIN customers c ON i.customer_id = c.id WHERE 1=1"
        params = []
        
        search_term = self.search_entry.get()
        if search_term:
            query += " AND c.name LIKE ?"
            params.append(f"%{search_term}%")
        
        start_date = self.start_date_entry.get()
        if start_date:
            query += " AND i.invoice_date >= ?"
            params.append(start_date)
            
        end_date = self.end_date_entry.get()
        if end_date:
            query += " AND i.invoice_date <= ?"
            params.append(end_date)
            
        query += " ORDER BY i.id DESC"
        
        cursor.execute(query, tuple(params))
        invoices = cursor.fetchall()
        cursor.close()
        conn.close()
        
        self.current_invoices_data = [dict(row) for row in invoices]
        self.update_summary_panel()

        if not invoices:
            ctk.CTkLabel(self.invoice_list_frame, text="No invoices found.").pack()
            return

        for invoice in self.current_invoices_data:
            row_frame = ctk.CTkFrame(self.invoice_list_frame)
            row_frame.pack(fill="x", padx=2, pady=2)
            
            row_frame.grid_columnconfigure(1, weight=1)

            status_color = "green" if invoice['status'] == 'Paid' else "orange"
            status_indicator = ctk.CTkLabel(row_frame, text="●", text_color=status_color, width=10)
            status_indicator.grid(row=0, column=0, padx=(5,0))

            button_text = f"Inv #{invoice['id']} - {invoice['name']} - ₹{invoice['total_amount']:.2f}"
            btn = ctk.CTkButton(row_frame, text=button_text, fg_color="transparent", hover=False, anchor="w",
                                command=lambda inv_id=invoice['id']: self.display_invoice_details(inv_id))
            btn.grid(row=0, column=1, sticky="ew")

            toggle_status_btn = ctk.CTkButton(row_frame, text="Paid/Unpaid", width=80,
                                              command=lambda inv_id=invoice['id'], status=invoice['status']: self.toggle_status(inv_id, status))
            toggle_status_btn.grid(row=0, column=2, padx=2)

            delete_btn = ctk.CTkButton(row_frame, text="Del", width=40, fg_color="#D32F2F", hover_color="#B71C1C",
                                       command=lambda inv_id=invoice['id']: self.delete_invoice(inv_id))
            delete_btn.grid(row=0, column=3, padx=(0,2))

    def update_summary_panel(self):
        total_sales = sum(inv['total_amount'] for inv in self.current_invoices_data)
        count = len(self.current_invoices_data)
        self.total_sales_label.configure(text=f"Total Sales (Filtered): ₹{total_sales:.2f}")
        self.invoice_count_label.configure(text=f"Invoices Shown: {count}")

    def display_invoice_details(self, invoice_id):
        conn, cursor = get_db_connection()
        if not conn: return
        query_main = "SELECT * FROM invoices i JOIN customers c ON i.customer_id = c.id WHERE i.id = ?"
        cursor.execute(query_main, (invoice_id,))
        main_details = cursor.fetchone()
        query_items = "SELECT ii.quantity, ii.price_per_unit, p.name FROM invoice_items ii JOIN products p ON ii.product_id = p.id WHERE ii.invoice_id = ?"
        cursor.execute(query_items, (invoice_id,))
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        if not main_details: return
        
        # --- FIXED: Added missing tax keys to the dictionary ---
        invoice_data = {
            "id": main_details['id'], "date": main_details['invoice_date'],
            "customer_name": main_details['name'], "customer_phone": main_details['phone'],
            "items": [dict(item) for item in items], "subtotal": main_details['subtotal_amount'],
            "discount_percent": main_details['discount_percent'],
            "discount_amount": (main_details['subtotal_amount'] * main_details['discount_percent']) / 100,
            "cgst_percent": main_details['cgst_percent'],
            "sgst_percent": main_details['sgst_percent'],
            "total": main_details['total_amount']
        }
        
        details_text = (
            f"Invoice #: {invoice_data['id']}\nDate: {invoice_data['date']}\n\n"
            f"Bill To:\n  {invoice_data['customer_name']}\n"
        )
        if invoice_data['customer_phone']: details_text += f"  {invoice_data['customer_phone']}\n"
        details_text += "="*50 + "\n\n"
        details_text += f"{'Product':<30}{'Qty':<10}{'Price':<15}{'Total':<15}\n" + "-"*70 + "\n"
        for item in invoice_data['items']:
            price_formatted = f"₹{item['price_per_unit']:.2f}"
            total_formatted = f"₹{item['quantity'] * item['price_per_unit']:.2f}"
            details_text += f"{item['name']:<30}{item['quantity']:<10}{price_formatted:<15}{total_formatted:<15}\n"
        
        taxable_amount = invoice_data['subtotal'] - invoice_data['discount_amount']
        cgst_amount = (taxable_amount * invoice_data['cgst_percent']) / 100
        sgst_amount = (taxable_amount * invoice_data['sgst_percent']) / 100
        
        details_text += "\n" + "-"*70 + "\n"
        details_text += f"{'SUBTOTAL:':>55} ₹{invoice_data['subtotal']:.2f}\n"
        details_text += f"{f'DISCOUNT ({invoice_data['discount_percent']}%):':>55} -₹{invoice_data['discount_amount']:.2f}\n"
        details_text += f"{f'CGST ({invoice_data['cgst_percent']}%):':>55} +₹{cgst_amount:.2f}\n"
        details_text += f"{f'SGST ({invoice_data['sgst_percent']}%):':>55} +₹{sgst_amount:.2f}\n"
        details_text += "="*50 + "\n"
        details_text += f"{'GRAND TOTAL:':>55} ₹{invoice_data['total']:.2f}\n"
        
        self.details_textbox.configure(state="normal")
        self.details_textbox.delete("1.0", "end")
        self.details_textbox.insert("1.0", details_text)
        self.details_textbox.configure(state="disabled")
        self.current_invoice_details = invoice_data
        self.pdf_button.configure(state="normal")
        self.open_pdf_button.configure(state="normal")

    def generate_pdf(self):
        if not self.current_invoice_details: return
        try:
            pdf = generate_professional_pdf(self.current_invoice_details)
            if pdf:
                filepath = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF Documents", "*.pdf")],
                    initialfile=f"Invoice_{self.current_invoice_details['id']}.pdf",
                    title="Save Invoice as PDF"
                )
                if not filepath: return
                pdf.output(filepath)
                if os.path.exists(filepath):
                    messagebox.showinfo("Success", f"PDF saved successfully to:\n{filepath}", parent=self.controller)
                else:
                    messagebox.showerror("Save Error", "Failed to save the PDF file.", parent=self.controller)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF: {e}", parent=self.controller)

    def open_pdf(self):
        if not self.current_invoice_details: return
        try:
            pdf = generate_professional_pdf(self.current_invoice_details)
            if pdf:
                temp_pdf_path = os.path.join(tempfile.gettempdir(), f"invoice_{self.current_invoice_details['id']}.pdf")
                pdf.output(temp_pdf_path)
                
                if sys.platform == "win32":
                    os.startfile(temp_pdf_path)
                elif sys.platform == "darwin":
                    import subprocess
                    subprocess.call(["open", temp_pdf_path])
                else:
                    import subprocess
                    subprocess.call(["xdg-open", temp_pdf_path])
        except Exception as e:
            messagebox.showerror("File Open Error", f"Could not open the PDF file: {e}", parent=self.controller)

    def toggle_status(self, invoice_id, current_status):
        new_status = "Paid" if current_status == "Unpaid" else "Unpaid"
        conn, cursor = get_db_connection()
        if not conn: return
        try:
            cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (new_status, invoice_id))
            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not update status: {e}", parent=self.controller)
        finally:
            conn.close()
            self.load_invoice_list()

    def delete_invoice(self, invoice_id):
        if not messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete Invoice #{invoice_id}?\nThis will also add the stock back to inventory.", parent=self):
            return
        
        conn, cursor = get_db_connection()
        if not conn: return
        try:
            cursor.execute("SELECT product_id, quantity FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            items_to_restore = cursor.fetchall()
            
            for item in items_to_restore:
                cursor.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (item['quantity'], item['product_id']))
            
            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            
            conn.commit()
            self.clear_search()

        except sqlite3.Error as e:
            conn.rollback()
            messagebox.showerror("Database Error", f"Could not delete invoice: {e}", parent=self.controller)
        finally:
            conn.close()
            self.load_invoice_list()

    def export_to_csv(self):
        if not self.current_invoices_data:
            messagebox.showinfo("Export Info", "There are no invoices to export.", parent=self)
            return
        
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile="invoice_export.csv",
                title="Export Invoices to CSV"
            )
            if not filepath: return

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "invoice_date", "name", "total_amount", "status"])
                writer.writeheader()
                writer.writerows(self.current_invoices_data)
            
            messagebox.showinfo("Success", f"Data exported successfully to:\n{filepath}", parent=self.controller)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export to CSV: {e}", parent=self.controller)
