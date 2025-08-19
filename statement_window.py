import customtkinter as ctk
from db_connector import get_db_connection
import sqlite3
from tkinter import messagebox, filedialog
import os
import sys
import tempfile
# --- UPDATED: Corrected the function name to import ---
from pdf_generator import generate_statement_pdf

class StatementFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.customer_id = None
        self.statement_data = {} # To store data for PDF

        # --- Top Bar ---
        top_bar = ctk.CTkFrame(self)
        top_bar.pack(side="top", fill="x", padx=10, pady=10)
        back_button = ctk.CTkButton(top_bar, text="< Back to Customers", command=lambda: controller.show_frame("CustomersFrame"))
        back_button.pack(side="left")
        self.title_label = ctk.CTkLabel(top_bar, text="Customer Statement", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(side="left", expand=True)

        # --- Summary Panel ---
        summary_frame = ctk.CTkFrame(self)
        summary_frame.pack(fill="x", padx=10, pady=5)
        self.net_balance_label = ctk.CTkLabel(summary_frame, text="Net Balance: ₹0.00", font=ctk.CTkFont(size=16, weight="bold"))
        self.net_balance_label.pack(pady=5)

        # --- PDF Buttons ---
        pdf_button_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
        pdf_button_frame.pack(pady=5)
        self.open_pdf_button = ctk.CTkButton(pdf_button_frame, text="Open Statement PDF", command=self.open_pdf)
        self.open_pdf_button.pack(side="left", padx=10)
        self.save_pdf_button = ctk.CTkButton(pdf_button_frame, text="Save Statement PDF", command=self.save_pdf)
        self.save_pdf_button.pack(side="left", padx=10)

        # --- Transactions List ---
        self.transactions_frame = ctk.CTkScrollableFrame(self)
        self.transactions_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def load_data(self, customer_id=None):
        if customer_id:
            self.customer_id = customer_id
        if not self.customer_id: return

        for widget in self.transactions_frame.winfo_children():
            widget.destroy()

        conn, cursor = get_db_connection()
        if not conn: return
        try:
            cursor.execute("SELECT * FROM customers WHERE id = ?", (self.customer_id,))
            customer = cursor.fetchone()
            if not customer: return

            self.title_label.configure(text=f"Statement for: {customer['name']}")
            balance_status = "Dr (Will give)" if customer['balance'] > 0 else "Cr (Will get)"
            self.net_balance_label.configure(text=f"Net Balance: ₹{abs(customer['balance']):.2f} {balance_status}")

            cursor.execute("SELECT * FROM transactions WHERE customer_id = ? ORDER BY transaction_date, id", (self.customer_id,))
            transactions = cursor.fetchall()

            self.statement_data = {
                "customer": dict(customer),
                "transactions": [dict(t) for t in transactions],
                "total_debit": sum(t['debit'] for t in transactions),
                "total_credit": sum(t['credit'] for t in transactions)
            }

            header = ctk.CTkFrame(self.transactions_frame)
            header.pack(fill="x")
            header.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(header, text="Date", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5)
            ctk.CTkLabel(header, text="Details", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=5, sticky="w")
            ctk.CTkLabel(header, text="Debit (-)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=10)
            ctk.CTkLabel(header, text="Credit (+)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, padx=10)
            ctk.CTkLabel(header, text="Balance", font=ctk.CTkFont(weight="bold")).grid(row=0, column=4, padx=10)

            for trans in transactions:
                row = ctk.CTkFrame(self.transactions_frame)
                row.pack(fill="x", pady=2)
                row.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(row, text=trans['transaction_date']).grid(row=0, column=0, padx=5)
                ctk.CTkLabel(row, text=trans['details'], anchor="w").grid(row=0, column=1, padx=5, sticky="ew")
                ctk.CTkLabel(row, text=f"₹{trans['debit']:.2f}" if trans['debit'] > 0 else "").grid(row=0, column=2, padx=10)
                ctk.CTkLabel(row, text=f"₹{trans['credit']:.2f}" if trans['credit'] > 0 else "").grid(row=0, column=3, padx=10)
                balance_status = "Dr" if trans['balance_after'] > 0 else "Cr"
                ctk.CTkLabel(row, text=f"₹{abs(trans['balance_after']):.2f} {balance_status}").grid(row=0, column=4, padx=10)

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error loading statement: {e}", parent=self)
        finally:
            conn.close()

    def save_pdf(self):
        if not self.statement_data: return
        # --- UPDATED: Corrected the function name to call ---
        pdf = generate_statement_pdf(self.statement_data)
        if pdf:
            try:
                filepath = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF Documents", "*.pdf")],
                    initialfile=f"Statement_{self.statement_data['customer']['name']}.pdf",
                    title="Save Statement as PDF"
                )
                if not filepath: return
                pdf.output(filepath)
                messagebox.showinfo("Success", f"Statement saved successfully to:\n{filepath}", parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save PDF: {e}", parent=self)

    def open_pdf(self):
        if not self.statement_data: return
        # --- UPDATED: Corrected the function name to call ---
        pdf = generate_statement_pdf(self.statement_data)
        if pdf:
            try:
                temp_pdf_path = os.path.join(tempfile.gettempdir(), f"statement_{self.customer_id}.pdf")
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
                messagebox.showerror("File Open Error", f"Could not open PDF: {e}", parent=self)
