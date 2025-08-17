import customtkinter as ctk
import os
import sys
from database_setup import setup_database

# Import the Frame classes from our other files
from products_window import ProductsFrame
from customers_window import CustomersFrame
from invoice_window import InvoiceFrame
from view_invoices_window import ViewInvoicesFrame

# --- NEW: A single function to find all external files ---
def get_asset_path(filename):
    """Gets the correct path for any asset file (db, icon, font)."""
    if getattr(sys, 'frozen', False):
        # Running as a bundled .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as a .py script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ASHIQ HARDWARE")
        self.geometry("1100x700")

        # --- UPDATED: Set the application icon ---
        try:
            self.iconbitmap(get_asset_path("logo.ico"))
        except Exception as e:
            # This will prevent a crash if the icon is missing
            print(f"Error setting icon: {e}")
        # -------------------------------------------

        # Create a container to hold all our frames
        container = ctk.CTkFrame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        # Create and store each page/frame
        for F in (MainMenuFrame, ProductsFrame, CustomersFrame, InvoiceFrame, ViewInvoicesFrame):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MainMenuFrame")

    def show_frame(self, page_name):
        """Shows a frame for the given page name."""
        frame = self.frames[page_name]
        if hasattr(frame, 'load_data'):
            frame.load_data()
        frame.tkraise()

class MainMenuFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        title_label = ctk.CTkLabel(self, text="Main Menu", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=40, padx=10)

        btn_new_invoice = ctk.CTkButton(self, text="Create New Invoice", font=ctk.CTkFont(size=14),
                                        command=lambda: controller.show_frame("InvoiceFrame"))
        btn_new_invoice.pack(pady=10, padx=200, fill="x")

        btn_manage_products = ctk.CTkButton(self, text="Manage Products", font=ctk.CTkFont(size=14),
                                            command=lambda: controller.show_frame("ProductsFrame"))
        btn_manage_products.pack(pady=10, padx=200, fill="x")

        btn_manage_customers = ctk.CTkButton(self, text="Manage Customers", font=ctk.CTkFont(size=14),
                                             command=lambda: controller.show_frame("CustomersFrame"))
        btn_manage_customers.pack(pady=10, padx=200, fill="x")
        
        btn_view_invoices = ctk.CTkButton(self, text="View Past Invoices", font=ctk.CTkFont(size=14),
                                          command=lambda: controller.show_frame("ViewInvoicesFrame"))
        btn_view_invoices.pack(pady=10, padx=200, fill="x")


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    # Use the new helper function to find the database
    db_path = get_asset_path('hardware_store.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Creating a new one...")
        setup_database()
        print("Database created successfully.")

    app = App()
    app.mainloop()
