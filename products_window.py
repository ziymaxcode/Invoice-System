import customtkinter as ctk
from db_connector import get_db_connection
import sqlite3
from tkinter import messagebox

# The class is now named ProductsFrame and inherits from CTkFrame
class ProductsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Main Layout ---
        # Add a top bar for title and back button
        top_bar = ctk.CTkFrame(self)
        top_bar.pack(side="top", fill="x", padx=10, pady=10)
        
        back_button = ctk.CTkButton(top_bar, text="< Back to Menu", command=lambda: controller.show_frame("MainMenuFrame"))
        back_button.pack(side="left")
        
        ctk.CTkLabel(top_bar, text="Manage Products", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", expand=True)

        # Main content frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # --- Left Frame for Adding/Editing Products ---
        self.form_frame = ctk.CTkFrame(content_frame, width=250)
        self.form_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.form_title = ctk.CTkLabel(self.form_frame, text="Add New Product", font=ctk.CTkFont(size=16, weight="bold"))
        self.form_title.pack(pady=10)

        self.name_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Product Name")
        self.name_entry.pack(pady=5, padx=10, fill="x")

        self.price_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Price (e.g., 12.99)")
        self.price_entry.pack(pady=5, padx=10, fill="x")

        self.stock_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Current Stock")
        self.stock_entry.pack(pady=5, padx=10, fill="x")

        self.action_button = ctk.CTkButton(self.form_frame, text="Add Product", command=self.add_product)
        self.action_button.pack(pady=10, padx=10, fill="x")
        
        self.clear_button = ctk.CTkButton(self.form_frame, text="Clear Form", command=self.clear_form, fg_color="gray")
        self.clear_button.pack(pady=5, padx=10, fill="x")
        
        self.status_label = ctk.CTkLabel(self.form_frame, text="", text_color="green")
        self.status_label.pack(pady=5)
        
        self.editing_product_id = None

        # --- Right Frame for Displaying Products ---
        self.display_frame = ctk.CTkFrame(content_frame)
        self.display_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self.display_frame)
        self.scrollable_frame.pack(fill="both", expand=True)

    def load_data(self):
        """This method will be called by the controller to refresh the data."""
        self.load_products()

    def clear_form(self, set_add_mode=True):
        self.name_entry.delete(0, 'end')
        self.price_entry.delete(0, 'end')
        self.stock_entry.delete(0, 'end')
        self.status_label.configure(text="")
        self.editing_product_id = None
        if set_add_mode:
            self.form_title.configure(text="Add New Product")
            self.action_button.configure(text="Add Product", command=self.add_product)

    def add_product(self):
        name = self.name_entry.get()
        price = self.price_entry.get()
        stock = self.stock_entry.get()
        if not name or not price or not stock:
            self.status_label.configure(text="All fields required.", text_color="red")
            return
        try:
            price_val = float(price)
            stock_val = int(stock)
        except ValueError:
            self.status_label.configure(text="Price/Stock must be numbers.", text_color="red")
            return
        conn, cursor = get_db_connection()
        if conn and cursor:
            try:
                sql = "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)"
                cursor.execute(sql, (name, price_val, stock_val))
                conn.commit()
                self.status_label.configure(text="Product added!", text_color="green")
                self.clear_form(set_add_mode=False)
                self.load_products()
            except sqlite3.Error as err:
                self.status_label.configure(text=f"Error: {err}", text_color="red")
            finally:
                cursor.close()
                conn.close()

    def setup_edit_form(self, product):
        self.clear_form(set_add_mode=False)
        self.editing_product_id = product['id']
        self.name_entry.insert(0, product['name'])
        self.price_entry.insert(0, str(product['price']))
        self.stock_entry.insert(0, str(product['stock']))
        self.form_title.configure(text=f"Editing: {product['name']}")
        self.action_button.configure(text="Save Changes", command=self.save_changes)

    def save_changes(self):
        if self.editing_product_id is None: return
        name = self.name_entry.get()
        price = self.price_entry.get()
        stock = self.stock_entry.get()
        if not name or not price or not stock:
            self.status_label.configure(text="All fields required.", text_color="red")
            return
        try:
            price_val = float(price)
            stock_val = int(stock)
        except ValueError:
            self.status_label.configure(text="Price/Stock must be numbers.", text_color="red")
            return
        conn, cursor = get_db_connection()
        if conn and cursor:
            try:
                sql = "UPDATE products SET name = ?, price = ?, stock = ? WHERE id = ?"
                cursor.execute(sql, (name, price_val, stock_val, self.editing_product_id))
                conn.commit()
                self.status_label.configure(text="Changes saved!", text_color="green")
                self.clear_form()
                self.load_products()
            except sqlite3.Error as err:
                self.status_label.configure(text=f"Error: {err}", text_color="red")
            finally:
                cursor.close()
                conn.close()

    def delete_product(self, product_id, product_name):
        answer = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{product_name}'?", parent=self.controller)
        if not answer: return
        conn, cursor = get_db_connection()
        if conn and cursor:
            try:
                sql = "DELETE FROM products WHERE id = ?"
                cursor.execute(sql, (product_id,))
                conn.commit()
                self.status_label.configure(text=f"Deleted '{product_name}'.", text_color="orange")
                self.load_products()
            except sqlite3.Error as err:
                self.status_label.configure(text=f"Error: {err}", text_color="red")
            finally:
                cursor.close()
                conn.close()

    def load_products(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        conn, cursor = get_db_connection()
        if not conn: return
        try:
            cursor.execute("SELECT id, name, price, stock FROM products ORDER BY name")
            products = cursor.fetchall()
            header_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(header_frame, text="Name", font=ctk.CTkFont(weight="bold"), width=200, anchor="w").pack(side="left", expand=True, fill="x")
            ctk.CTkLabel(header_frame, text="Price", font=ctk.CTkFont(weight="bold"), width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(header_frame, text="Stock", font=ctk.CTkFont(weight="bold"), width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(header_frame, text="Actions", font=ctk.CTkFont(weight="bold"), width=150, anchor="center").pack(side="left")
            for product in products:
                row_frame = ctk.CTkFrame(self.scrollable_frame)
                row_frame.pack(fill="x", padx=5, pady=2)
                product_dict = dict(product)
                ctk.CTkLabel(row_frame, text=product_dict['name'], width=200, anchor="w").pack(side="left", expand=True, fill="x")
                ctk.CTkLabel(row_frame, text=f"₹{product_dict['price']:.2f}", width=80, anchor="w").pack(side="left")
                ctk.CTkLabel(row_frame, text=product_dict['stock'], width=80, anchor="w").pack(side="left")
                actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                actions_frame.pack(side="left", padx=5)
                edit_button = ctk.CTkButton(actions_frame, text="Edit", width=60, command=lambda p=product_dict: self.setup_edit_form(p))
                edit_button.pack(side="left", padx=2)
                delete_button = ctk.CTkButton(actions_frame, text="Delete", width=60, fg_color="#D32F2F", hover_color="#B71C1C", command=lambda pid=product_dict['id'], pname=product_dict['name']: self.delete_product(pid, pname))
                delete_button.pack(side="left", padx=2)
        except sqlite3.Error as err:
            ctk.CTkLabel(self.scrollable_frame, text=f"Error loading products: {err}").pack()
        finally:
            if conn:
                cursor.close()
                conn.close()
