import customtkinter as ctk
import os
import sys
from database_setup import setup_database
from PIL import Image

from products_window import ProductsFrame
from customers_window import CustomersFrame
from invoice_window import InvoiceFrame
from view_invoices_window import ViewInvoicesFrame
from return_window import ReturnInvoiceFrame
from statement_window import StatementFrame # Import the new frame

def get_asset_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hardware Store")
        self.geometry("1100x700")
        self.minsize(800, 600)
        try:
            self.iconbitmap(get_asset_path("logo.ico"))
        except Exception as e:
            print(f"Error setting icon: {e}")
        container = ctk.CTkFrame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (MainMenuFrame, ProductsFrame, CustomersFrame, InvoiceFrame, ViewInvoicesFrame, ReturnInvoiceFrame, StatementFrame):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("MainMenuFrame")

    # --- UPDATED: show_frame now accepts an optional customer_id ---
    def show_frame(self, page_name, customer_id=None):
        frame = self.frames[page_name]
        if hasattr(frame, 'load_data'):
            # Pass the customer_id if the method accepts it
            if customer_id and page_name == "StatementFrame":
                frame.load_data(customer_id=customer_id)
            else:
                frame.load_data()
        frame.tkraise()

class MainMenuFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=5)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=1, column=0, columnspan=3, sticky="nsew")
        # try:
        #     logo_path = get_asset_path("logo.ico")
        #     logo_image = ctk.CTkImage(Image.open(logo_path), size=(64, 64))
        #     logo_label = ctk.CTkLabel(title_frame, image=logo_image, text="")
        #     logo_label.pack(pady=(0, 10))
        # except Exception as e:
        #     print(f"Error loading logo for main menu: {e}")
        shop_title = ctk.CTkLabel(title_frame, text="Hardware Store", font=ctk.CTkFont(size=32, weight="bold"))
        shop_title.pack(pady=(0,5))
        #shop_subtitle = ctk.CTkLabel(title_frame, text="Invoice & Inventory Management", font=ctk.CTkFont(size=14, slant="italic"))
        #shop_subtitle.pack()
        button_grid = ctk.CTkFrame(self, fg_color="transparent")
        button_grid.grid(row=2, column=0, columnspan=3, padx=100, pady=20, sticky="nsew")
        button_grid.grid_columnconfigure((0, 1, 2), weight=1)
        button_grid.grid_rowconfigure((0, 1), weight=1)
        def create_menu_button(parent, title, command, row, col, columnspan=1):
            fg_color = ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
            hover_color = ctk.ThemeManager.theme["CTkButton"]["hover_color"]
            button_frame = ctk.CTkFrame(parent, corner_radius=15, fg_color=fg_color, cursor="hand2", border_width=2)
            button_frame.grid(row=row, column=col, columnspan=columnspan, padx=20, pady=20, sticky="nsew")
            button_frame.grid_rowconfigure(0, weight=1)
            button_frame.grid_columnconfigure(0, weight=1)
            button_title = ctk.CTkLabel(button_frame, text=title, font=ctk.CTkFont(size=18, weight="bold"), anchor="center")
            button_title.grid(row=0, column=0, sticky="nsew")
            def on_enter(event): button_frame.configure(fg_color=hover_color)
            def on_leave(event): button_frame.configure(fg_color=fg_color)
            for child in [button_frame, button_title]:
                child.bind("<Enter>", on_enter)
                child.bind("<Leave>", on_leave)
                child.bind("<Button-1>", lambda event: command())
            return button_frame
        create_menu_button(button_grid, "Create New Invoice", lambda: controller.show_frame("InvoiceFrame"), 0, 0)
        create_menu_button(button_grid, "Manage Products", lambda: controller.show_frame("ProductsFrame"), 0, 1)
        create_menu_button(button_grid, "Manage Customers", lambda: controller.show_frame("CustomersFrame"), 0, 2)
        create_menu_button(button_grid, "View Past Invoices", lambda: controller.show_frame("ViewInvoicesFrame"), 1, 0)
        create_menu_button(button_grid, "Process Return", lambda: controller.show_frame("ReturnInvoiceFrame"), 1, 1)

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    db_path = get_asset_path('hardware_store.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Creating a new one...")
        setup_database()
        print("Database created successfully.")
    app = App()
    app.mainloop()
