import customtkinter as ctk
from db_connector import get_db_connection
from datetime import date
import sqlite3
from tkinter import messagebox
from fpdf import FPDF
import os
import sys
import tempfile

def get_asset_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

class InvoiceFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self._customer_search_job = None
        self._product_search_job = None
        self.last_saved_invoice_id = None

        # --- Top Bar ---
        top_bar = ctk.CTkFrame(self)
        top_bar.pack(side="top", fill="x", padx=10, pady=10)
        back_button = ctk.CTkButton(top_bar, text="< Back to Menu", command=self.go_back)
        back_button.pack(side="left")
        new_invoice_button = ctk.CTkButton(top_bar, text="Create New Invoice", command=self.reset_form)
        new_invoice_button.pack(side="left", padx=10)
        ctk.CTkLabel(top_bar, text="Create Invoice", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", expand=True)

        # --- Customer Selection & Product Adding Frames ---
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

        # --- Invoice Items Display ---
        self.items_display_frame = ctk.CTkFrame(self)
        self.items_display_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.items_list = ctk.CTkTextbox(self.items_display_frame, font=("Courier", 12))
        self.items_list.pack(fill="both", expand=True)
        self.items_list.configure(state="disabled")

        # --- UPDATED: Bottom Bar with Discount ---
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.pack(fill="x", padx=10, pady=10)
        self.discount_frame = ctk.CTkFrame(self.bottom_frame)
        self.discount_frame.pack(side="left", padx=10)
        ctk.CTkLabel(self.discount_frame, text="Discount (%):").pack(side="left")
        self.discount_entry = ctk.CTkEntry(self.discount_frame, width=60)
        self.discount_entry.pack(side="left", padx=5)
        self.discount_entry.bind("<KeyRelease>", lambda event: self.update_invoice_display())
        self.totals_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.totals_frame.pack(side="left", padx=20)
        self.subtotal_label = ctk.CTkLabel(self.totals_frame, text="Subtotal: ₹0.00")
        self.subtotal_label.pack(anchor="w")
        self.discount_amount_label = ctk.CTkLabel(self.totals_frame, text="Discount: -₹0.00", text_color="green")
        self.discount_amount_label.pack(anchor="w")
        self.total_label = ctk.CTkLabel(self.totals_frame, text="Grand Total: ₹0.00", font=ctk.CTkFont(size=16, weight="bold"))
        self.total_label.pack(anchor="w")
        self.print_button = ctk.CTkButton(self.bottom_frame, text="Open PDF", command=self.print_invoice, state="disabled")
        self.print_button.pack(side="right", padx=5)
        self.save_button = ctk.CTkButton(self.bottom_frame, text="Save Invoice", command=self.save_invoice)
        self.save_button.pack(side="right", padx=5)

    def update_invoice_display(self):
        self.items_list.configure(state="normal")
        self.items_list.delete("1.0", "end")
        header = f"{'Product':<30}{'Qty':<10}{'Price':<15}{'Total':<15}\n"
        separator = "-"*70 + "\n"
        self.items_list.insert("end", header)
        self.items_list.insert("end", separator)
        subtotal = 0.0
        for item in self.invoice_items:
            price_formatted = f"₹{item['price_per_unit']:.2f}"
            total_formatted = f"₹{item['line_total']:.2f}"
            line = f"{item['name']:<30}{item['quantity']:<10}{price_formatted:<15}{total_formatted:<15}\n"
            self.items_list.insert("end", line)
            subtotal += item['line_total']
        self.items_list.configure(state="disabled")
        try:
            discount_percent = float(self.discount_entry.get() or 0)
        except ValueError:
            discount_percent = 0
        discount_amount = (subtotal * discount_percent) / 100
        grand_total = subtotal - discount_amount
        self.subtotal_label.configure(text=f"Subtotal: ₹{subtotal:.2f}")
        self.discount_amount_label.configure(text=f"Discount ({discount_percent}%): -₹{discount_amount:.2f}")
        self.total_label.configure(text=f"Grand Total: ₹{grand_total:.2f}")

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
        try:
            discount_percent = float(self.discount_entry.get() or 0)
        except ValueError:
            discount_percent = 0
        discount_amount = (subtotal * discount_percent) / 100
        total_amount = subtotal - discount_amount
        conn, cursor = get_db_connection()
        if not conn: return
        try:
            sql_invoice = "INSERT INTO invoices (customer_id, invoice_date, subtotal_amount, discount_percent, total_amount) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(sql_invoice, (customer_id, invoice_date, subtotal, discount_percent, total_amount))
            invoice_id = cursor.lastrowid
            sql_items = "INSERT INTO invoice_items (invoice_id, product_id, quantity, price_per_unit) VALUES (?, ?, ?, ?)"
            items_to_insert = [(invoice_id, item['product_id'], item['quantity'], item['price_per_unit']) for item in self.invoice_items]
            cursor.executemany(sql_items, items_to_insert)
            sql_update_stock = "UPDATE products SET stock = stock - ? WHERE id = ?"
            for item in self.invoice_items:
                cursor.execute(sql_update_stock, (item['quantity'], item['product_id']))
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
            customer_names = ["No customers found"]
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
            product_names = ["No products found"]
        current_text = self.product_menu.get()
        self.product_menu.configure(values=product_names)
        self.product_menu.set(current_text)
    def search_customers(self, event=None):
        if self._customer_search_job:
            self.after_cancel(self._customer_search_job)
        self._customer_search_job = self.after(300, self._perform_customer_search)
    def _perform_customer_search(self):
        search_term = self.customer_menu.get()
        self.load_customers(search_term)
    def customer_selected(self, selected_customer):
        pass
    def search_products(self, event=None):
        if self._product_search_job:
            self.after_cancel(self._product_search_job)
        self._product_search_job = self.after(300, self._perform_product_search)
    def _perform_product_search(self):
        search_term = self.product_menu.get()
        self.load_products(search_term)
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
        item = {"product_id": product_info['id'], "name": selected_product, "quantity": quantity, "price_per_unit": product_info['price'], "line_total": quantity * product_info['price']}
        self.invoice_items.append(item)
        self.status_label.configure(text=f"Added {selected_product}", text_color="green")
        self.quantity_entry.delete(0, 'end')
        self.update_invoice_display()
    def print_invoice(self):
        if self.last_saved_invoice_id is None: return
        invoice_id = self.last_saved_invoice_id
        conn, cursor = get_db_connection()
        if not conn: return
        query_main = "SELECT i.invoice_date, i.subtotal_amount, i.discount_percent, i.total_amount, c.name, c.phone, c.address FROM invoices i JOIN customers c ON i.customer_id = c.id WHERE i.id = ?"
        cursor.execute(query_main, (invoice_id,))
        main_details = cursor.fetchone()
        query_items = "SELECT ii.quantity, ii.price_per_unit, p.name FROM invoice_items ii JOIN products p ON ii.product_id = p.id WHERE ii.invoice_id = ?"
        cursor.execute(query_items, (invoice_id,))
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        if not main_details:
            messagebox.showerror("Error", "Could not find the saved invoice to print.", parent=self.controller)
            return
        date, subtotal, discount_p, total, name, phone, address = main_details['invoice_date'], main_details['subtotal_amount'], main_details['discount_percent'], main_details['total_amount'], main_details['name'], main_details['phone'], main_details['address']
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
        details_text += "\n" + "-"*70 + "\n"
        details_text += f"{'SUBTOTAL:':>55} ₹{subtotal:.2f}\n"
        discount_amount = (subtotal * discount_p) / 100
        details_text += f"{f'DISCOUNT ({discount_p}%):':>55} -₹{discount_amount:.2f}\n"
        details_text += "="*50 + "\n"
        details_text += f"{'GRAND TOTAL:':>55} ₹{total:.2f}\n"
        pdf = FPDF()
        pdf.add_page()
        try:
            font_path = get_asset_path("DejaVuSans.ttf")
            if not os.path.exists(font_path):
                messagebox.showerror("Font Error", "DejaVuSans.ttf not found.", parent=self.controller)
                return
            pdf.add_font("DejaVu", "", font_path)
            pdf.set_font("DejaVu", size=10)
        except Exception as e:
            messagebox.showerror("Font Error", f"Could not load font: {e}", parent=self.controller)
            return
        pdf.multi_cell(0, 5, details_text)
        try:
            temp_pdf_path = os.path.join(tempfile.gettempdir(), f"invoice_{invoice_id}.pdf")
            pdf.output(temp_pdf_path)
            if os.name == 'nt':
                os.startfile(temp_pdf_path)
            else:
                import subprocess
                if sys.platform == "darwin": subprocess.call(["open", temp_pdf_path])
                else: subprocess.call(["xdg-open", temp_pdf_path])
        except Exception as e:
            messagebox.showerror("File Open Error", f"Could not open the PDF file: {e}", parent=self.controller)