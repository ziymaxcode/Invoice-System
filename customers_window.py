import customtkinter as ctk
from db_connector import get_db_connection
import sqlite3
from tkinter import messagebox
import math

class CustomersFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.selected_customer_id = None

        # --- NEW: Pagination state ---
        self.current_page = 1
        self.customers_per_page = 20

        # --- Top Bar ---
        top_bar = ctk.CTkFrame(self)
        top_bar.pack(side="top", fill="x", padx=10, pady=10)
        back_button = ctk.CTkButton(top_bar, text="< Back to Menu", command=lambda: controller.show_frame("MainMenuFrame"))
        back_button.pack(side="left")
        ctk.CTkLabel(top_bar, text="Manage Customers", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", expand=True)

        # --- Main Content Frame ---
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # --- Left Panel (Add/Edit Form) ---
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

        # --- Right Panel (Customer List & Dashboard) ---
        self.display_frame = ctk.CTkFrame(content_frame)
        self.display_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.search_entry = ctk.CTkEntry(self.display_frame, placeholder_text="Search by name or phone...")
        self.search_entry.pack(fill="x", pady=(0, 5))
        self.search_entry.bind("<KeyRelease>", lambda event: self.load_customers(reset_page=True))

        self.scrollable_frame = ctk.CTkScrollableFrame(self.display_frame)
        self.scrollable_frame.pack(fill="both", expand=True)

        # --- NEW: Pagination Controls ---
        pagination_frame = ctk.CTkFrame(self.display_frame)
        pagination_frame.pack(fill="x", pady=5)
        self.prev_button = ctk.CTkButton(pagination_frame, text="<< Previous", command=self.prev_page)
        self.prev_button.pack(side="left", padx=5)
        self.page_label = ctk.CTkLabel(pagination_frame, text="Page 1 / 1")
        self.page_label.pack(side="left", expand=True)
        self.next_button = ctk.CTkButton(pagination_frame, text="Next >>", command=self.next_page)
        self.next_button.pack(side="right", padx=5)

        self.dashboard_frame = ctk.CTkFrame(self.display_frame, height=250)
        self.dashboard_frame.pack(fill="x", pady=5)
        self.dashboard_frame.pack_forget()

        stats_frame = ctk.CTkFrame(self.dashboard_frame)
        stats_frame.pack(side="left", fill="y", padx=10, pady=10)
        self.dashboard_title = ctk.CTkLabel(stats_frame, text="Customer Details", font=ctk.CTkFont(weight="bold"))
        self.dashboard_title.pack(anchor="w")
        self.total_spent_label = ctk.CTkLabel(stats_frame, text="Total Spent: ₹0.00")
        self.total_spent_label.pack(anchor="w")
        self.last_purchase_label = ctk.CTkLabel(stats_frame, text="Last Purchase: N/A")
        self.last_purchase_label.pack(anchor="w")
        notes_frame = ctk.CTkFrame(self.dashboard_frame)
        notes_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(notes_frame, text="Customer Notes:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.notes_textbox = ctk.CTkTextbox(notes_frame, height=80)
        self.notes_textbox.pack(fill="x", expand=True)
        save_notes_button = ctk.CTkButton(notes_frame, text="Save Notes", command=self.save_notes)
        save_notes_button.pack(anchor="e", pady=5)

    def load_data(self):
        self.load_customers(reset_page=True)

    def next_page(self):
        self.current_page += 1
        self.load_customers()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_customers()

    def load_customers(self, reset_page=False):
        if reset_page:
            self.current_page = 1
            
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.dashboard_frame.pack_forget()
        conn, cursor = get_db_connection()
        if not conn: return
        try:
            count_query = "SELECT COUNT(*) FROM customers WHERE 1=1"
            query = "SELECT * FROM customers WHERE 1=1"
            params = []
            search_term = self.search_entry.get()
            if search_term:
                filter_clause = " AND (name LIKE ? OR phone LIKE ?)"
                count_query += filter_clause
                query += filter_clause
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            
            cursor.execute(count_query, tuple(params))
            total_customers = cursor.fetchone()[0]
            total_pages = math.ceil(total_customers / self.customers_per_page)

            query += " ORDER BY name LIMIT ? OFFSET ?"
            offset = (self.current_page - 1) * self.customers_per_page
            params.extend([self.customers_per_page, offset])
            
            cursor.execute(query, tuple(params))
            customers = cursor.fetchall()

            self.page_label.configure(text=f"Page {self.current_page} / {total_pages}")
            self.prev_button.configure(state="normal" if self.current_page > 1 else "disabled")
            self.next_button.configure(state="normal" if self.current_page < total_pages else "disabled")

            for customer in customers:
                customer_dict = dict(customer)
                row_frame = ctk.CTkFrame(self.scrollable_frame)
                row_frame.pack(fill="x", padx=5, pady=2)
                
                info_button = ctk.CTkButton(row_frame, text=f"{customer_dict['name']} ({customer_dict['phone']})",
                                            fg_color="transparent", anchor="w",
                                            command=lambda c=customer_dict: self.display_customer_details(c))
                info_button.pack(side="left", expand=True, fill="x")
                
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
                conn.close()

    # ... (all other functions are unchanged)
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
                sql = "INSERT INTO customers (name, phone, address, notes) VALUES (?, ?, ?, ?)"
                cursor.execute(sql, (name, phone, address, ""))
                conn.commit()
                self.status_label.configure(text="Customer added!", text_color="green")
                self.clear_form(set_add_mode=False)
                self.load_customers(reset_page=True)
            except sqlite3.Error as err:
                self.status_label.configure(text=f"Error: {err}", text_color="red")
            finally:
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
                conn.close()
    def delete_customer(self, customer_id, customer_name):
        if not messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{customer_name}'?", parent=self.controller):
            return
        conn, cursor = get_db_connection()
        if conn and cursor:
            try:
                sql = "DELETE FROM customers WHERE id = ?"
                cursor.execute(sql, (customer_id,))
                conn.commit()
                self.status_label.configure(text=f"Deleted '{customer_name}'.", text_color="orange")
                self.load_customers(reset_page=True)
            except sqlite3.Error as err:
                self.status_label.configure(text=f"Error: {err}", text_color="red")
            finally:
                conn.close()
    def display_customer_details(self, customer):
        self.selected_customer_id = customer['id']
        self.dashboard_frame.pack(fill="x", pady=5)
        self.dashboard_title.configure(text=f"Dashboard for: {customer['name']}")
        self.notes_textbox.delete("1.0", "end")
        if customer['notes']:
            self.notes_textbox.insert("1.0", customer['notes'])
        conn, cursor = get_db_connection()
        if not conn: return
        try:
            cursor.execute("SELECT SUM(total_amount) as total FROM invoices WHERE customer_id = ?", (customer['id'],))
            total_spent = cursor.fetchone()['total'] or 0
            self.total_spent_label.configure(text=f"Total Spent: ₹{total_spent:.2f}")
            cursor.execute("SELECT MAX(invoice_date) as last_date FROM invoices WHERE customer_id = ?", (customer['id'],))
            last_date = cursor.fetchone()['last_date'] or "N/A"
            self.last_purchase_label.configure(text=f"Last Purchase: {last_date}")
        except sqlite3.Error as e:
            print(f"Error fetching dashboard data: {e}")
        finally:
            conn.close()
    def save_notes(self):
        if self.selected_customer_id is None: return
        notes = self.notes_textbox.get("1.0", "end-1c")
        conn, cursor = get_db_connection()
        if not conn: return
        try:
            cursor.execute("UPDATE customers SET notes = ? WHERE id = ?", (notes, self.selected_customer_id))
            conn.commit()
            messagebox.showinfo("Success", "Notes saved successfully.", parent=self)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not save notes: {e}", parent=self)
        finally:
            conn.close()
