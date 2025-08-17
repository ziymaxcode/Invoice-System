import customtkinter as ctk
from db_connector import get_db_connection
import sqlite3
from tkinter import messagebox

class CustomersFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        top_bar = ctk.CTkFrame(self)
        top_bar.pack(side="top", fill="x", padx=10, pady=10)
        
        back_button = ctk.CTkButton(top_bar, text="< Back to Menu", command=lambda: controller.show_frame("MainMenuFrame"))
        back_button.pack(side="left")
        
        ctk.CTkLabel(top_bar, text="Manage Customers", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", expand=True)

        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        self.form_frame = ctk.CTkFrame(content_frame, width=250)
        self.form_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.form_title = ctk.CTkLabel(self.form_frame, text="Add New Customer", font=ctk.CTkFont(size=16, weight="bold"))
        self.form_title.pack(pady=10)

        self.name_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Customer Name")
        self.name_entry.pack(pady=5, padx=10, fill="x")

        self.phone_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Phone Number")
        self.phone_entry.pack(pady=5, padx=10, fill="x")

        self.address_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Address")
        self.address_entry.pack(pady=5, padx=10, fill="x")

        self.action_button = ctk.CTkButton(self.form_frame, text="Add Customer", command=self.add_customer)
        self.action_button.pack(pady=10, padx=10, fill="x")

        self.clear_button = ctk.CTkButton(self.form_frame, text="Clear Form", command=self.clear_form, fg_color="gray")
        self.clear_button.pack(pady=5, padx=10, fill="x")

        self.status_label = ctk.CTkLabel(self.form_frame, text="", text_color="green")
        self.status_label.pack(pady=5)

        self.editing_customer_id = None

        self.display_frame = ctk.CTkFrame(content_frame)
        self.display_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self.display_frame)
        self.scrollable_frame.pack(fill="both", expand=True)

    def load_data(self):
        self.load_customers()

    def clear_form(self, set_add_mode=True):
        self.name_entry.delete(0, 'end')
        self.phone_entry.delete(0, 'end')
        self.address_entry.delete(0, 'end')
        self.status_label.configure(text="")
        self.editing_customer_id = None
        if set_add_mode:
            self.form_title.configure(text="Add New Customer")
            self.action_button.configure(text="Add Customer", command=self.add_customer)

    def add_customer(self):
        name = self.name_entry.get()
        phone = self.phone_entry.get()
        address = self.address_entry.get()
        if not name:
            self.status_label.configure(text="Customer name is required.", text_color="red")
            return
        conn, cursor = get_db_connection()
        if conn and cursor:
            try:
                sql = "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)"
                cursor.execute(sql, (name, phone, address))
                conn.commit()
                self.status_label.configure(text="Customer added!", text_color="green")
                self.clear_form(set_add_mode=False)
                self.load_customers()
            except sqlite3.Error as err:
                self.status_label.configure(text=f"Error: {err}", text_color="red")
            finally:
                cursor.close()
                conn.close()

    def setup_edit_form(self, customer):
        self.clear_form(set_add_mode=False)
        self.editing_customer_id = customer['id']
        self.name_entry.insert(0, customer['name'])
        self.phone_entry.insert(0, customer['phone'])
        self.address_entry.insert(0, customer['address'])
        self.form_title.configure(text=f"Editing: {customer['name']}")
        self.action_button.configure(text="Save Changes", command=self.save_changes)

    def save_changes(self):
        if self.editing_customer_id is None: return
        name = self.name_entry.get()
        phone = self.phone_entry.get()
        address = self.address_entry.get()
        if not name:
            self.status_label.configure(text="Customer name is required.", text_color="red")
            return
        conn, cursor = get_db_connection()
        if conn and cursor:
            try:
                sql = "UPDATE customers SET name = ?, phone = ?, address = ? WHERE id = ?"
                cursor.execute(sql, (name, phone, address, self.editing_customer_id))
                conn.commit()
                self.status_label.configure(text="Changes saved!", text_color="green")
                self.clear_form()
                self.load_customers()
            except sqlite3.Error as err:
                self.status_label.configure(text=f"Error: {err}", text_color="red")
            finally:
                cursor.close()
                conn.close()

    def delete_customer(self, customer_id, customer_name):
        answer = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{customer_name}'?", parent=self.controller)
        if not answer: return
        conn, cursor = get_db_connection()
        if conn and cursor:
            try:
                sql = "DELETE FROM customers WHERE id = ?"
                cursor.execute(sql, (customer_id,))
                conn.commit()
                self.status_label.configure(text=f"Deleted '{customer_name}'.", text_color="orange")
                self.load_customers()
            except sqlite3.Error as err:
                self.status_label.configure(text=f"Error: {err}", text_color="red")
            finally:
                cursor.close()
                conn.close()

    def load_customers(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        conn, cursor = get_db_connection()
        if not conn: return
        try:
            cursor.execute("SELECT id, name, phone, address FROM customers ORDER BY name")
            customers = cursor.fetchall()
            header_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(header_frame, text="Name", font=ctk.CTkFont(weight="bold"), width=200, anchor="w").pack(side="left", expand=True, fill="x")
            ctk.CTkLabel(header_frame, text="Phone", font=ctk.CTkFont(weight="bold"), width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(header_frame, text="Actions", font=ctk.CTkFont(weight="bold"), width=150, anchor="center").pack(side="left")
            for customer in customers:
                row_frame = ctk.CTkFrame(self.scrollable_frame)
                row_frame.pack(fill="x", padx=5, pady=2)
                customer_dict = dict(customer)
                ctk.CTkLabel(row_frame, text=customer_dict['name'], width=200, anchor="w").pack(side="left", expand=True, fill="x")
                ctk.CTkLabel(row_frame, text=customer_dict['phone'], width=120, anchor="w").pack(side="left")
                actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                actions_frame.pack(side="left", padx=5)
                edit_button = ctk.CTkButton(actions_frame, text="Edit", width=60, command=lambda c=customer_dict: self.setup_edit_form(c))
                edit_button.pack(side="left", padx=2)
                delete_button = ctk.CTkButton(actions_frame, text="Delete", width=60, fg_color="#D32F2F", hover_color="#B71C1C", command=lambda cid=customer_dict['id'], cname=customer_dict['name']: self.delete_customer(cid, cname))
                delete_button.pack(side="left", padx=2)
        except sqlite3.Error as err:
            ctk.CTkLabel(self.scrollable_frame, text=f"Error loading customers: {err}").pack()
        finally:
            if conn:
                cursor.close()
                conn.close()