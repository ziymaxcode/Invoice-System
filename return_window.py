import customtkinter as ctk
from db_connector import get_db_connection
import sqlite3
from tkinter import messagebox
from datetime import date
import tempfile
import os
import sys
from pdf_generator import generate_return_note_pdf

class ReturnInvoiceFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.original_invoice_data = None
        self.return_items = {}
        self.last_return_id = None
        top_bar = ctk.CTkFrame(self)
        top_bar.pack(side="top", fill="x", padx=10, pady=10)
        back_button = ctk.CTkButton(top_bar, text="< Back to Menu", command=lambda: controller.show_frame("MainMenuFrame"))
        back_button.pack(side="left")
        ctk.CTkLabel(top_bar, text="Process a Return", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", expand=True)
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(search_frame, text="Enter Original Invoice ID:").pack(side="left", padx=5)
        self.invoice_id_entry = ctk.CTkEntry(search_frame, width=100)
        self.invoice_id_entry.pack(side="left", padx=5)
        load_button = ctk.CTkButton(search_frame, text="Load Invoice", command=self.load_invoice)
        load_button.pack(side="left", padx=5)
        self.invoice_status_label = ctk.CTkLabel(search_frame, text="")
        self.invoice_status_label.pack(side="left", padx=10)
        self.items_frame = ctk.CTkScrollableFrame(self)
        self.items_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(self.items_frame, text="No invoice loaded.").pack()
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=10, pady=10)
        self.refund_label = ctk.CTkLabel(bottom_frame, text="Total Refund: ₹0.00", font=ctk.CTkFont(size=16, weight="bold"))
        self.refund_label.pack(side="left", padx=10)
        self.print_return_button = ctk.CTkButton(bottom_frame, text="Print Return Note", state="disabled", command=self.print_return_note)
        self.print_return_button.pack(side="right", padx=5)
        self.process_return_button = ctk.CTkButton(bottom_frame, text="Process Return", state="disabled", command=self.process_return)
        self.process_return_button.pack(side="right", padx=5)

    def process_return(self):
        if not self.original_invoice_data: return

        items_to_return = []
        total_refund = 0.0
        
        for item in self.original_invoice_data['items']:
            try:
                return_qty = int(self.return_items[item['product_id']].get() or 0)
                if return_qty < 0:
                    messagebox.showerror("Invalid Quantity", "Return quantity cannot be negative.", parent=self)
                    return
                if return_qty > item['quantity']:
                    messagebox.showerror("Invalid Quantity", f"Cannot return more than {item['quantity']} for {item['name']}.", parent=self)
                    return
                if return_qty > 0:
                    items_to_return.append({
                        "product_id": item['product_id'], "quantity": return_qty,
                        "price_per_unit": item['price_per_unit'], "name": item['name']
                    })
                    total_refund += return_qty * item['price_per_unit']
            except ValueError:
                messagebox.showerror("Invalid Quantity", "Please enter valid numbers for return quantities.", parent=self)
                return

        if not items_to_return:
            messagebox.showinfo("No Items", "No items were marked for return.", parent=self)
            return

        conn, cursor = get_db_connection()
        if not conn: return
        try:
            return_date = date.today().strftime("%Y-%m-%d")
            cursor.execute("INSERT INTO returns (original_invoice_id, return_date, total_refund) VALUES (?, ?, ?)",
                           (self.original_invoice_data['invoice']['id'], return_date, total_refund))
            return_id = cursor.lastrowid
            
            for item in items_to_return:
                cursor.execute("INSERT INTO return_items (return_id, product_id, quantity, price_per_unit) VALUES (?, ?, ?, ?)",
                               (return_id, item['product_id'], item['quantity'], item['price_per_unit']))
                cursor.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (item['quantity'], item['product_id']))
            
            # --- UPDATED: Create descriptive transaction details ---
            product_names = [item['name'] for item in items_to_return]
            details_summary = "Return: " + ", ".join(product_names[:2])
            if len(product_names) > 2:
                details_summary += ", ..."

            customer_id = self.original_invoice_data['invoice']['customer_id']
            cursor.execute("SELECT balance FROM customers WHERE id = ?", (customer_id,))
            current_balance = cursor.fetchone()['balance']
            new_balance = current_balance - total_refund
            
            cursor.execute("INSERT INTO transactions (customer_id, transaction_date, details, credit, balance_after) VALUES (?, ?, ?, ?, ?)",
                           (customer_id, return_date, details_summary, total_refund, new_balance))
            
            cursor.execute("UPDATE customers SET balance = ? WHERE id = ?", (new_balance, customer_id))

            conn.commit()
            messagebox.showinfo("Success", f"Return processed successfully. Refund amount: ₹{total_refund:.2f}", parent=self)
            
            self.last_return_id = return_id
            self.print_return_button.configure(state="normal")
            self.process_return_button.configure(state="disabled")

        except sqlite3.Error as e:
            conn.rollback()
            messagebox.showerror("Database Error", f"Failed to process return: {e}", parent=self)
        finally:
            conn.close()

    # ... (rest of the file is unchanged)
    def load_data(self):
        self.invoice_id_entry.delete(0, 'end')
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.items_frame, text="Enter an Invoice ID to begin.").pack()
        self.invoice_status_label.configure(text="")
        self.refund_label.configure(text="Total Refund: ₹0.00")
        self.process_return_button.configure(state="disabled")
        self.print_return_button.configure(state="disabled")
        self.original_invoice_data = None
        self.return_items = {}
        self.last_return_id = None
    def load_invoice(self):
        try:
            invoice_id = int(self.invoice_id_entry.get())
        except ValueError:
            messagebox.showerror("Invalid ID", "Please enter a valid number for the Invoice ID.", parent=self)
            return
        conn, cursor = get_db_connection()
        if not conn: return
        try:
            cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
            invoice = cursor.fetchone()
            if not invoice:
                self.invoice_status_label.configure(text=f"Invoice #{invoice_id} not found.", text_color="red")
                return
            cursor.execute("SELECT p.name, p.id as product_id, ii.quantity, ii.price_per_unit FROM invoice_items ii JOIN products p ON ii.product_id = p.id WHERE ii.invoice_id = ?", (invoice_id,))
            items = cursor.fetchall()
            self.original_invoice_data = {"invoice": dict(invoice), "items": [dict(item) for item in items]}
            self.display_invoice_items()
            self.process_return_button.configure(state="normal")
            self.invoice_status_label.configure(text=f"Loaded Invoice #{invoice_id}", text_color="green")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error loading invoice: {e}", parent=self)
        finally:
            conn.close()
    def display_invoice_items(self):
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        self.return_items = {}
        header = ctk.CTkFrame(self.items_frame)
        header.pack(fill="x")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Product", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Purchased Qty", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=10)
        ctk.CTkLabel(header, text="Return Qty", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=10)
        for item in self.original_invoice_data['items']:
            row = ctk.CTkFrame(self.items_frame)
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=item['name']).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(row, text=str(item['quantity'])).grid(row=0, column=1, padx=10)
            return_qty_entry = ctk.CTkEntry(row, width=60)
            return_qty_entry.grid(row=0, column=2, padx=10)
            return_qty_entry.bind("<KeyRelease>", lambda event: self.calculate_refund())
            self.return_items[item['product_id']] = return_qty_entry
    def calculate_refund(self):
        total_refund = 0.0
        for item in self.original_invoice_data['items']:
            try:
                return_qty = int(self.return_items[item['product_id']].get() or 0)
                if return_qty > item['quantity']:
                    self.return_items[item['product_id']].configure(border_color="red")
                else:
                    self.return_items[item['product_id']].configure(border_color="gray50")
                    total_refund += return_qty * item['price_per_unit']
            except ValueError:
                pass
        self.refund_label.configure(text=f"Total Refund: ₹{total_refund:.2f}")
    def print_return_note(self):
        if self.last_return_id is None: return
        conn, cursor = get_db_connection()
        if not conn: return
        try:
            cursor.execute("SELECT r.id, r.return_date, r.total_refund, r.original_invoice_id, c.name as customer_name FROM returns r JOIN invoices i ON r.original_invoice_id = i.id JOIN customers c ON i.customer_id = c.id WHERE r.id = ?", (self.last_return_id,))
            return_details = cursor.fetchone()
            cursor.execute("SELECT ri.quantity, ri.price_per_unit, p.name FROM return_items ri JOIN products p ON ri.product_id = p.id WHERE ri.return_id = ?", (self.last_return_id,))
            items = cursor.fetchall()
            if not return_details: return
            return_data = {
                "id": return_details['id'], "date": return_details['return_date'],
                "original_invoice_id": return_details['original_invoice_id'],
                "customer_name": return_details['customer_name'],
                "total_refund": return_details['total_refund'],
                "items": [dict(item) for item in items]
            }
            pdf = generate_return_note_pdf(return_data)
            if pdf:
                temp_pdf_path = os.path.join(tempfile.gettempdir(), f"return_note_{self.last_return_id}.pdf")
                pdf.output(temp_pdf_path)
                if sys.platform == "win32":
                    os.startfile(temp_pdf_path)
                elif sys.platform == "darwin":
                    import subprocess
                    subprocess.call(["open", temp_pdf_path])
                else:
                    import subprocess
                    subprocess.call(["xdg-open", temp_pdf_path])
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not fetch return details: {e}", parent=self)
        finally:
            conn.close()