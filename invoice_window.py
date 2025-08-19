import customtkinter as ctk
from db_connector import get_db_connection
from datetime import date
import sqlite3
from tkinter import messagebox
import os
import sys
import tempfile
from pdf_generator import generate_professional_pdf

class InvoiceFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._customer_search_job = None
        self._product_search_job = None
        self.last_saved_invoice_id = None
        self.invoice_items = []
        top_bar = ctk.CTkFrame(self)
        top_bar.pack(side="top", fill="x", padx=10, pady=10)
        back_button = ctk.CTkButton(top_bar, text="< Back to Menu", command=self.go_back)
        back_button.pack(side="left")
        new_invoice_button = ctk.CTkButton(top_bar, text="Create New Invoice", command=self.reset_form)
        new_invoice_button.pack(side="left", padx=10)
        ctk.CTkLabel(top_bar, text="Create Invoice", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", expand=True)
        self.details_frame = ctk.CTkFrame(self)
        self.details_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(self.details_frame, text="Customer:").pack(side="left", padx=5)
        self.customer_menu = ctk.CTkComboBox(self.details_frame, values=["Select Customer"], command=self.customer_selected)
        self.customer_menu.pack(side="left", padx=5, expand=True, fill="x")
        self.customer_menu.bind("<KeyRelease>", self.search_customers)
        self.new_customer_button = ctk.CTkButton(self.details_frame, text="+ New", width=50, command=self.toggle_new_customer_form)
        self.new_customer_button.pack(side="left", padx=5)
        today = date.today().strftime("%Y-%m-%d")
        ctk.CTkLabel(self.details_frame, text=f"Date: {today}").pack(side="right", padx=10)
        self.new_customer_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkLabel(self.new_customer_frame, text="New Customer Name:").pack(side="left", padx=(10, 5))
        self.new_customer_name_entry = ctk.CTkEntry(self.new_customer_frame, placeholder_text="Name")
        self.new_customer_name_entry.pack(side="left", padx=5)
        ctk.CTkLabel(self.new_customer_frame, text="Phone:").pack(side="left", padx=5)
        self.new_customer_phone_entry = ctk.CTkEntry(self.new_customer_frame, placeholder_text="Phone (Optional)")
        self.new_customer_phone_entry.pack(side="left", padx=5)
        self.save_customer_button = ctk.CTkButton(self.new_customer_frame, text="Save Customer", command=self.save_new_customer)
        self.save_customer_button.pack(side="left", padx=5)
        self.new_customer_frame_visible = False
        self.add_item_frame = ctk.CTkFrame(self)
        self.add_item_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(self.add_item_frame, text="Product:").pack(side="left", padx=5)
        self.product_menu = ctk.CTkComboBox(self.add_item_frame, values=["Select Product"])
        self.product_menu.pack(side="left", padx=5, expand=True, fill="x")
        self.product_menu.bind("<KeyRelease>", self.search_products)
        ctk.CTkLabel(self.add_item_frame, text="Quantity:").pack(side="left", padx=5)
        self.quantity_entry = ctk.CTkEntry(self.add_item_frame, width=80)
        self.quantity_entry.pack(side="left", padx=5)
        add_button = ctk.CTkButton(self.add_item_frame, text="Add to Invoice", command=self.add_item_to_invoice)
        add_button.pack(side="left", padx=10)
        self.status_label = ctk.CTkLabel(self.add_item_frame, text="")
        self.status_label.pack(side="left", padx=10)
        self.items_display_frame = ctk.CTkScrollableFrame(self)
        self.items_display_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.pack(fill="x", padx=10, pady=10)
        self.calculation_frame = ctk.CTkFrame(self.bottom_frame)
        self.calculation_frame.pack(side="left", padx=10)
        ctk.CTkLabel(self.calculation_frame, text="Discount (%):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.discount_entry = ctk.CTkEntry(self.calculation_frame, width=60)
        self.discount_entry.grid(row=0, column=1, padx=5, pady=2)
        self.discount_entry.bind("<KeyRelease>", lambda event: self.update_invoice_display())
        ctk.CTkLabel(self.calculation_frame, text="CGST (%):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.cgst_entry = ctk.CTkEntry(self.calculation_frame, width=60)
        self.cgst_entry.grid(row=1, column=1, padx=5, pady=2)
        self.cgst_entry.bind("<KeyRelease>", lambda event: self.update_invoice_display())
        ctk.CTkLabel(self.calculation_frame, text="SGST (%):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.sgst_entry = ctk.CTkEntry(self.calculation_frame, width=60)
        self.sgst_entry.grid(row=2, column=1, padx=5, pady=2)
        self.sgst_entry.bind("<KeyRelease>", lambda event: self.update_invoice_display())
        self.totals_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.totals_frame.pack(side="left", padx=20)
        self.subtotal_label = ctk.CTkLabel(self.totals_frame, text="Subtotal: ₹0.00")
        self.subtotal_label.pack(anchor="w")
        self.discount_amount_label = ctk.CTkLabel(self.totals_frame, text="Discount: -₹0.00", text_color="green")
        self.discount_amount_label.pack(anchor="w")
        self.cgst_amount_label = ctk.CTkLabel(self.totals_frame, text="CGST: +₹0.00")
        self.cgst_amount_label.pack(anchor="w")
        self.sgst_amount_label = ctk.CTkLabel(self.totals_frame, text="SGST: +₹0.00")
        self.sgst_amount_label.pack(anchor="w")
        self.total_label = ctk.CTkLabel(self.totals_frame, text="Grand Total: ₹0.00", font=ctk.CTkFont(size=16, weight="bold"))
        self.total_label.pack(anchor="w", pady=(5,0))
        self.print_button = ctk.CTkButton(self.bottom_frame, text="Open PDF", command=self.print_invoice, state="disabled")
        self.print_button.pack(side="right", padx=5)
        self.save_button = ctk.CTkButton(self.bottom_frame, text="Save Invoice", command=self.save_invoice)
        self.save_button.pack(side="right", padx=5)

    def save_invoice(self):
        selected_customer = self.customer_menu.get()
        if "No customers found" in selected_customer or selected_customer not in self.customer_data:
            self.status_label.configure(text="Please select a valid customer.", text_color="red")
            return
        if not self.invoice_items:
            self.status_label.configure(text="Cannot save an empty invoice.", text_color="red")
            return
        
        customer_id = self.customer_data[selected_customer]
        invoice_date = date.today().strftime("%Y-%m-%d")
        subtotal = sum(item['line_total'] for item in self.invoice_items)
        try: discount_percent = float(self.discount_entry.get() or 0)
        except ValueError: discount_percent = 0
        try: cgst_percent = float(self.cgst_entry.get() or 0)
        except ValueError: cgst_percent = 0
        try: sgst_percent = float(self.sgst_entry.get() or 0)
        except ValueError: sgst_percent = 0
        
        discount_amount = (subtotal * discount_percent) / 100
        taxable_amount = subtotal - discount_amount
        cgst_amount = (taxable_amount * cgst_percent) / 100
        sgst_amount = (taxable_amount * sgst_percent) / 100
        total_amount = taxable_amount + cgst_amount + sgst_amount

        conn, cursor = get_db_connection()
        if not conn: return
        try:
            sql_invoice = "INSERT INTO invoices (customer_id, invoice_date, subtotal_amount, discount_percent, cgst_percent, sgst_percent, total_amount) VALUES (?, ?, ?, ?, ?, ?, ?)"
            cursor.execute(sql_invoice, (customer_id, invoice_date, subtotal, discount_percent, cgst_percent, sgst_percent, total_amount))
            invoice_id = cursor.lastrowid
            
            sql_items = "INSERT INTO invoice_items (invoice_id, product_id, quantity, price_per_unit) VALUES (?, ?, ?, ?)"
            items_to_insert = [(invoice_id, item['product_id'], item['quantity'], item['price_per_unit']) for item in self.invoice_items]
            cursor.executemany(sql_items, items_to_insert)
            
            sql_update_stock = "UPDATE products SET stock = stock - ? WHERE id = ?"
            for item in self.invoice_items:
                cursor.execute(sql_update_stock, (item['quantity'], item['product_id']))
            
            # --- UPDATED: Create descriptive transaction details ---
            product_names = [item['name'] for item in self.invoice_items]
            details_summary = "Sale: " + ", ".join(product_names[:2])
            if len(product_names) > 2:
                details_summary += ", ..."

            cursor.execute("SELECT balance FROM customers WHERE id = ?", (customer_id,))
            current_balance = cursor.fetchone()['balance']
            new_balance = current_balance + total_amount
            
            cursor.execute("INSERT INTO transactions (customer_id, transaction_date, details, debit, balance_after) VALUES (?, ?, ?, ?, ?)",
                           (customer_id, invoice_date, details_summary, total_amount, new_balance))
            
            cursor.execute("UPDATE customers SET balance = ? WHERE id = ?", (new_balance, customer_id))

            conn.commit()
            messagebox.showinfo("Success", f"Invoice #{invoice_id} saved successfully!", parent=self.controller)
            self.save_button.configure(state="disabled")
            self.last_saved_invoice_id = invoice_id
            self.print_button.configure(state="normal")
            self.load_products()
        except sqlite3.Error as err:
            conn.rollback()
            messagebox.showerror("Database Error", f"Failed to save invoice: {err}", parent=self.controller)
        finally:
            cursor.close()
            conn.close()
    
    # ... (rest of the file is unchanged)
    def delete_invoice_item(self, item_to_delete):
        self.invoice_items.remove(item_to_delete)
        self.update_invoice_display()
    def update_item_quantity(self, item, new_quantity_str):
        try:
            new_quantity = int(new_quantity_str)
            if new_quantity <= 0:
                self.delete_invoice_item(item)
                return
        except ValueError:
            messagebox.showwarning("Input Error", "Quantity must be a valid number.", parent=self)
            self.update_invoice_display()
            return
        product_info = self.product_data[item['name']]
        available_stock = product_info['stock']
        quantity_of_other_items_in_cart = sum(i['quantity'] for i in self.invoice_items if i['product_id'] == item['product_id'] and i is not item)
        if (new_quantity + quantity_of_other_items_in_cart) > available_stock:
            messagebox.showwarning("Stock Error", f"Cannot set quantity to {new_quantity}.\nOnly {available_stock - quantity_of_other_items_in_cart} available in stock.", parent=self)
            self.update_invoice_display()
            return
        item['quantity'] = new_quantity
        item['line_total'] = new_quantity * item['price_per_unit']
        self.update_invoice_display()
    def add_item_to_invoice(self):
        selected_product = self.product_menu.get()
        quantity_str = self.quantity_entry.get()
        if "No products found" in selected_product or selected_product not in self.product_data:
            self.status_label.configure(text="Please select a valid product.", text_color="red")
            return
        try:
            quantity = int(quantity_str)
            if quantity <= 0: raise ValueError("Quantity must be positive")
        except ValueError:
            self.status_label.configure(text="Invalid quantity.", text_color="red")
            return
        product_info = self.product_data[selected_product]
        available_stock = product_info['stock']
        quantity_in_cart = sum(item['quantity'] for item in self.invoice_items if item['product_id'] == product_info['id'])
        if (quantity + quantity_in_cart) > available_stock:
            messagebox.showwarning("Stock Error", f"Cannot add {quantity} of {selected_product}.\nOnly {available_stock - quantity_in_cart} left in stock.", parent=self)
            return
        for item in self.invoice_items:
            if item['product_id'] == product_info['id']:
                item['quantity'] += quantity
                item['line_total'] = item['quantity'] * item['price_per_unit']
                self.status_label.configure(text=f"Updated quantity for {selected_product}", text_color="green")
                self.quantity_entry.delete(0, 'end')
                self.update_invoice_display()
                return
        item = {"product_id": product_info['id'], "name": selected_product, "quantity": quantity, "price_per_unit": product_info['price'], "line_total": quantity * product_info['price']}
        self.invoice_items.append(item)
        self.status_label.configure(text=f"Added {selected_product}", text_color="green")
        self.quantity_entry.delete(0, 'end')
        self.update_invoice_display()
    def update_invoice_display(self):
        for widget in self.items_display_frame.winfo_children():
            widget.destroy()
        header_frame = ctk.CTkFrame(self.items_display_frame)
        header_frame.pack(fill="x", pady=(0,5))
        header_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header_frame, text="Product", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(header_frame, text="Qty", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=5)
        ctk.CTkLabel(header_frame, text="Price", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=5)
        ctk.CTkLabel(header_frame, text="Total", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, padx=5)
        ctk.CTkLabel(header_frame, text="Action", font=ctk.CTkFont(weight="bold")).grid(row=0, column=4, padx=5)
        subtotal = 0.0
        for item in self.invoice_items:
            row_frame = ctk.CTkFrame(self.items_display_frame)
            row_frame.pack(fill="x", pady=2, padx=2)
            row_frame.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row_frame, text=item['name'], anchor="w").grid(row=0, column=0, sticky="ew", padx=5)
            qty_entry = ctk.CTkEntry(row_frame, width=60)
            qty_entry.insert(0, str(item['quantity']))
            qty_entry.grid(row=0, column=1, padx=5)
            qty_entry.bind("<Return>", lambda event, current_item=item, entry=qty_entry: self.update_item_quantity(current_item, entry.get()))
            ctk.CTkLabel(row_frame, text=f"₹{item['price_per_unit']:.2f}").grid(row=0, column=2, padx=5)
            ctk.CTkLabel(row_frame, text=f"₹{item['line_total']:.2f}").grid(row=0, column=3, padx=5)
            delete_button = ctk.CTkButton(row_frame, text="Delete", width=60, fg_color="#D32F2F", hover_color="#B71C1C", command=lambda current_item=item: self.delete_invoice_item(current_item))
            delete_button.grid(row=0, column=4, padx=5)
            subtotal += item['line_total']
        try: discount_percent = float(self.discount_entry.get() or 0)
        except ValueError: discount_percent = 0
        try: cgst_percent = float(self.cgst_entry.get() or 0)
        except ValueError: cgst_percent = 0
        try: sgst_percent = float(self.sgst_entry.get() or 0)
        except ValueError: sgst_percent = 0
        discount_amount = (subtotal * discount_percent) / 100
        taxable_amount = subtotal - discount_amount
        cgst_amount = (taxable_amount * cgst_percent) / 100
        sgst_amount = (taxable_amount * sgst_percent) / 100
        grand_total = taxable_amount + cgst_amount + sgst_amount
        self.subtotal_label.configure(text=f"Subtotal: ₹{subtotal:.2f}")
        self.discount_amount_label.configure(text=f"Discount ({discount_percent}%): -₹{discount_amount:.2f}")
        self.cgst_amount_label.configure(text=f"CGST ({cgst_percent}%): +₹{cgst_amount:.2f}")
        self.sgst_amount_label.configure(text=f"SGST ({sgst_percent}%): +₹{sgst_amount:.2f}")
        self.total_label.configure(text=f"Grand Total: ₹{grand_total:.2f}")
    def go_back(self):
        self.reset_form()
        self.controller.show_frame("MainMenuFrame")
    def load_data(self):
        self.reset_form()
        self.load_customers()
        self.load_products()
    def reset_form(self):
        self.invoice_items = []
        self.status_label.configure(text="")
        self.save_button.configure(state="normal")
        self.print_button.configure(state="disabled")
        self.last_saved_invoice_id = None
        if self.new_customer_frame_visible:
            self.toggle_new_customer_form()
        self.customer_menu.set("")
        self.product_menu.set("")
        self.discount_entry.delete(0, 'end')
        self.cgst_entry.delete(0, 'end')
        self.sgst_entry.delete(0, 'end')
        self.load_customers()
        self.load_products()
        self.update_invoice_display()
    def toggle_new_customer_form(self):
        if self.new_customer_frame_visible:
            self.new_customer_frame.pack_forget()
            self.new_customer_frame_visible = False
        else:
            self.new_customer_frame.pack(fill="x", padx=10, pady=(0, 10), after=self.details_frame)
            self.new_customer_frame_visible = True
    def save_new_customer(self):
        name = self.new_customer_name_entry.get()
        phone = self.new_customer_phone_entry.get()
        if not name:
            messagebox.showwarning("Input Error", "Customer name cannot be empty.", parent=self)
            return
        conn, cursor = get_db_connection()
        if not conn: return
        try:
            sql = "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)"
            cursor.execute(sql, (name, phone, ""))
            conn.commit()
            self.new_customer_name_entry.delete(0, 'end')
            self.new_customer_phone_entry.delete(0, 'end')
            self.load_customers()
            self.customer_menu.set(name)
            self.toggle_new_customer_form()
        except sqlite3.Error as err:
            messagebox.showerror("Database Error", f"Failed to save new customer: {err}", parent=self)
        finally:
            cursor.close()
            conn.close()
    def load_customers(self, search_term=""):
        conn, cursor = get_db_connection()
        if not conn: return
        query = "SELECT id, name FROM customers WHERE name LIKE ? ORDER BY name"
        cursor.execute(query, (f"%{search_term}%",))
        customers = cursor.fetchall()
        cursor.close()
        conn.close()
        self.customer_data = {row['name']: row['id'] for row in customers}
        customer_names = list(self.customer_data.keys())
        if not customer_names:
            customer_names = []
        current_text = self.customer_menu.get()
        self.customer_menu.configure(values=customer_names)
        self.customer_menu.set(current_text)
    def load_products(self, search_term=""):
        conn, cursor = get_db_connection()
        if not conn: return
        query = "SELECT id, name, price, stock FROM products WHERE name LIKE ? ORDER BY name"
        cursor.execute(query, (f"%{search_term}%",))
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        self.product_data = {row['name']: {'id': row['id'], 'price': row['price'], 'stock': row['stock']} for row in products}
        product_names = list(self.product_data.keys())
        if not product_names:
            product_names = []
        current_text = self.product_menu.get()
        self.product_menu.configure(values=product_names)
        self.product_menu.set(current_text)
    def search_customers(self, event=None):
        self.after(5, self._perform_customer_search)
    def _perform_customer_search(self):
        search_term = self.customer_menu.get()
        self.load_customers(search_term)
        self.customer_menu._open_dropdown_menu()
    def customer_selected(self, selected_customer):
        pass
    def search_products(self, event=None):
        self.after(5, self._perform_product_search)
    def _perform_product_search(self):
        search_term = self.product_menu.get()
        self.load_products(search_term)
        self.product_menu._open_dropdown_menu()
    def print_invoice(self):
        if self.last_saved_invoice_id is None: return
        conn, cursor = get_db_connection()
        if not conn: return
        query_main = "SELECT * FROM invoices i JOIN customers c ON i.customer_id = c.id WHERE i.id = ?"
        cursor.execute(query_main, (self.last_saved_invoice_id,))
        main_details = cursor.fetchone()
        query_items = "SELECT ii.quantity, ii.price_per_unit, p.name FROM invoice_items ii JOIN products p ON ii.product_id = p.id WHERE ii.invoice_id = ?"
        cursor.execute(query_items, (self.last_saved_invoice_id,))
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        if not main_details: return
        invoice_data = {
            "id": main_details['id'], "date": main_details['invoice_date'],
            "customer_name": main_details['name'], "customer_phone": main_details['phone'],
            "items": [dict(item) for item in items], "subtotal": main_details['subtotal_amount'],
            "discount_percent": main_details['discount_percent'],
            "discount_amount": (main_details['subtotal_amount'] * main_details['discount_percent']) / 100,
            "cgst_percent": main_details['cgst_percent'], "sgst_percent": main_details['sgst_percent'],
            "total": main_details['total_amount']
        }
        pdf = generate_professional_pdf(invoice_data)
        if pdf:
            try:
                temp_pdf_path = os.path.join(tempfile.gettempdir(), f"invoice_{self.last_saved_invoice_id}.pdf")
                pdf.output(temp_pdf_path)
                if os.name == 'nt': os.startfile(temp_pdf_path)
                else:
                    import subprocess
                    if sys.platform == "darwin": subprocess.call(["open", temp_pdf_path])
                    else: subprocess.call(["xdg-open", temp_pdf_path])
            except Exception as e:
                messagebox.showerror("File Open Error", f"Could not open the PDF file: {e}", parent=self.controller)