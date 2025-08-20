import customtkinter as ctk
from db_connector import get_db_connection
import sqlite3
from tkinter import messagebox, filedialog
import csv
import math

class ProductsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.current_page = 1
        self.products_per_page = 20

        # --- Top Bar ---
        top_bar = ctk.CTkFrame(self)
        top_bar.pack(side="top", fill="x", padx=10, pady=10)
        back_button = ctk.CTkButton(top_bar, text="< Back to Menu", command=lambda: controller.show_frame("MainMenuFrame"))
        back_button.pack(side="left")
        ctk.CTkLabel(top_bar, text="Manage Products", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", expand=True)

        # --- Main Content Frame ---
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # --- Left Panel (Add/Edit Form) ---
        self.form_frame = ctk.CTkFrame(content_frame, width=250)
        self.form_frame.pack(side="left", fill="y", padx=10, pady=10)
        self.form_title = ctk.CTkLabel(self.form_frame, text="Add New Product", font=ctk.CTkFont(size=16, weight="bold"))
        self.form_title.pack(pady=10)
        self.name_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Product Name")
        self.name_entry.pack(pady=5, padx=10, fill="x")
        self.price_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Price (e.g., 12.99)")
        self.price_entry.pack(pady=5, padx=10, fill="x")
        self.category_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Category (e.g., Tools)")
        self.category_entry.pack(pady=5, padx=10, fill="x")
        self.action_button = ctk.CTkButton(self.form_frame, text="Add Product", command=self.add_product)
        self.action_button.pack(pady=10, padx=10, fill="x")
        self.clear_button = ctk.CTkButton(self.form_frame, text="Clear Form", command=self.clear_form, fg_color="gray")
        self.clear_button.pack(pady=5, padx=10, fill="x")
        self.status_label = ctk.CTkLabel(self.form_frame, text="", text_color="green")
        self.status_label.pack(pady=5)
        self.editing_product_id = None

        # --- Right Panel (Product List & Filters) ---
        self.display_frame = ctk.CTkFrame(content_frame)
        self.display_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        filter_bar = ctk.CTkFrame(self.display_frame)
        filter_bar.pack(fill="x", pady=(0, 5))
        self.search_entry = ctk.CTkEntry(filter_bar, placeholder_text="Search by product name...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", lambda event: self.load_products(reset_page=True))
        self.category_filter_menu = ctk.CTkOptionMenu(filter_bar, values=["All Categories"], command=lambda choice: self.load_products(reset_page=True))
        self.category_filter_menu.pack(side="left")
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self.display_frame)
        self.scrollable_frame.pack(fill="both", expand=True)

        pagination_frame = ctk.CTkFrame(self.display_frame)
        pagination_frame.pack(fill="x", pady=5)
        self.prev_button = ctk.CTkButton(pagination_frame, text="<< Previous", command=self.prev_page)
        self.prev_button.pack(side="left", padx=5)
        self.page_label = ctk.CTkLabel(pagination_frame, text="Page 1 / 1")
        self.page_label.pack(side="left", expand=True)
        self.next_button = ctk.CTkButton(pagination_frame, text="Next >>", command=self.next_page)
        self.next_button.pack(side="right", padx=5)

        import_button = ctk.CTkButton(self.display_frame, text="Import Products from CSV", command=self.import_from_csv)
        import_button.pack(fill="x", pady=5)

    def load_data(self):
        self.load_products(reset_page=True)
        self.update_category_filter()
        
    def next_page(self):
        self.current_page += 1
        self.load_products()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_products()

    def load_products(self, reset_page=False):
        if reset_page:
            self.current_page = 1

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        conn, cursor = get_db_connection()
        if not conn: return
        
        try:
            count_query = "SELECT COUNT(*) FROM products WHERE 1=1"
            query = "SELECT * FROM products WHERE 1=1"
            params = []
            
            search_term = self.search_entry.get()
            if search_term:
                filter_clause = " AND name LIKE ?"
                count_query += filter_clause
                query += filter_clause
                params.append(f"%{search_term}%")
            
            category = self.category_filter_menu.get()
            if category and category != "All Categories":
                filter_clause = " AND category = ?"
                count_query += filter_clause
                query += filter_clause
                params.append(category)
            
            cursor.execute(count_query, tuple(params))
            total_products = cursor.fetchone()[0]
            total_pages = math.ceil(total_products / self.products_per_page)
            
            query += " ORDER BY name LIMIT ? OFFSET ?"
            offset = (self.current_page - 1) * self.products_per_page
            params.extend([self.products_per_page, offset])
            
            cursor.execute(query, tuple(params))
            products = cursor.fetchall()

            self.page_label.configure(text=f"Page {self.current_page} / {total_pages if total_pages > 0 else 1}")
            self.prev_button.configure(state="normal" if self.current_page > 1 else "disabled")
            self.next_button.configure(state="normal" if self.current_page < total_pages else "disabled")

            header_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(header_frame, text="Name", font=ctk.CTkFont(weight="bold"), width=200, anchor="w").pack(side="left", expand=True, fill="x")
            ctk.CTkLabel(header_frame, text="Category", font=ctk.CTkFont(weight="bold"), width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(header_frame, text="Price", font=ctk.CTkFont(weight="bold"), width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(header_frame, text="Actions", font=ctk.CTkFont(weight="bold"), width=150, anchor="center").pack(side="left")

            for product in products:
                product_dict = dict(product)
                row_frame = ctk.CTkFrame(self.scrollable_frame)
                row_frame.pack(fill="x", padx=5, pady=2)
                
                ctk.CTkLabel(row_frame, text=product_dict['name'], width=200, anchor="w").pack(side="left", expand=True, fill="x")
                ctk.CTkLabel(row_frame, text=product_dict['category'], width=100, anchor="w").pack(side="left")
                ctk.CTkLabel(row_frame, text=f"₹{product_dict['price']:.2f}", width=80, anchor="w").pack(side="left")
                
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
                conn.close()
    
    def update_category_filter(self):
        conn, cursor = get_db_connection()
        if not conn: return
        try:
            cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category")
            categories = [row['category'] for row in cursor.fetchall()]
            self.category_filter_menu.configure(values=["All Categories"] + categories)
        except sqlite3.Error as e:
            print(f"Error fetching categories: {e}")
        finally:
            conn.close()
    def clear_form(self, set_add_mode=True):
        self.name_entry.delete(0, 'end')
        self.price_entry.delete(0, 'end')
        self.category_entry.delete(0, 'end')
        self.status_label.configure(text="")
        self.editing_product_id = None
        if set_add_mode:
            self.form_title.configure(text="Add New Product")
            self.action_button.configure(text="Add Product", command=self.add_product)
    def add_product(self):
        name = self.name_entry.get()
        price = self.price_entry.get()
        category = self.category_entry.get()
        if not name or not price:
            self.status_label.configure(text="Name and Price are required.", text_color="red")
            return
        try:
            price_val = float(price)
        except ValueError:
            self.status_label.configure(text="Price must be a number.", text_color="red")
            return
        conn, cursor = get_db_connection()
        if conn and cursor:
            try:
                sql = "INSERT INTO products (name, price, category) VALUES (?, ?, ?)"
                cursor.execute(sql, (name, price_val, category))
                conn.commit()
                self.status_label.configure(text="Product added!", text_color="green")
                self.clear_form(set_add_mode=False)
                self.load_data()
            except sqlite3.Error as err:
                self.status_label.configure(text=f"Error: {err}", text_color="red")
            finally:
                conn.close()
    def setup_edit_form(self, product):
        self.clear_form(set_add_mode=False)
        self.editing_product_id = product['id']
        self.name_entry.insert(0, product['name'])
        self.price_entry.insert(0, str(product['price']))
        self.category_entry.insert(0, product['category'] or "")
        self.form_title.configure(text=f"Editing: {product['name']}")
        self.action_button.configure(text="Save Changes", command=self.save_changes)
    def save_changes(self):
        if self.editing_product_id is None: return
        name = self.name_entry.get()
        price = self.price_entry.get()
        category = self.category_entry.get()
        if not name or not price:
            self.status_label.configure(text="Name and Price are required.", text_color="red")
            return
        try:
            price_val = float(price)
        except ValueError:
            self.status_label.configure(text="Price must be a number.", text_color="red")
            return
        conn, cursor = get_db_connection()
        if conn and cursor:
            try:
                sql = "UPDATE products SET name = ?, price = ?, category = ? WHERE id = ?"
                cursor.execute(sql, (name, price_val, category, self.editing_product_id))
                conn.commit()
                self.status_label.configure(text="Changes saved!", text_color="green")
                self.clear_form()
                self.load_data()
            except sqlite3.Error as err:
                self.status_label.configure(text=f"Error: {err}", text_color="red")
            finally:
                conn.close()
    def delete_product(self, product_id, product_name):
        if not messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{product_name}'?", parent=self.controller):
            return
        conn, cursor = get_db_connection()
        if conn and cursor:
            try:
                sql = "DELETE FROM products WHERE id = ?"
                cursor.execute(sql, (product_id,))
                conn.commit()
                self.status_label.configure(text=f"Deleted '{product_name}'.", text_color="orange")
                self.load_data()
            except sqlite3.Error as err:
                self.status_label.configure(text=f"Error: {err}", text_color="red")
            finally:
                conn.close()
    def import_from_csv(self):
        try:
            filepath = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv")],
                title="Select a Product CSV file"
            )
            if not filepath: return
            conn, cursor = get_db_connection()
            if not conn: return
            imported_count = 0
            skipped_count = 0
            with open(filepath, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader) # Skip header row
                for row in reader:
                    try:
                        # --- UPDATED: CSV format is now name, price, category ---
                        name, price, category = row
                        sql = "INSERT INTO products (name, price, category) VALUES (?, ?, ?)"
                        cursor.execute(sql, (name, float(price), category))
                        imported_count += 1
                    except (sqlite3.IntegrityError, ValueError) as e:
                        print(f"Skipping row: {row} due to error: {e}")
                        skipped_count += 1
            conn.commit()
            conn.close()
            messagebox.showinfo("Import Complete", f"Successfully imported {imported_count} products.\nSkipped {skipped_count} duplicate or invalid rows.", parent=self)
            self.load_data()
        except Exception as e:
            messagebox.showerror("Import Error", f"An error occurred during CSV import: {e}", parent=self)
