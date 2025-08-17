# Hardware Store Invoice System

A simple, modern, and local-first desktop application for managing products, customers, and invoices. Built with Python and CustomTkinter, this system is designed to be easy to use for small business owners without requiring any technical expertise or internet connection.

![Main Menu Screenshot](https://i.imgur.com/your-screenshot-url.png) <!-- It's a good idea to add a screenshot of your app here -->

## ✨ Features

- **Single Window Interface:** All actions happen within a single, clean window with a frame-based navigation system for a smooth user experience.
- **Product Management:**
  - Add, edit, and delete products (name, price, stock).
  - View a real-time list of all available products.
- **Customer Management:**
  - Add, edit, and delete customer details (name, phone, address).
  - View a complete list of all customers.
- **Invoice Creation:**
  - Searchable dropdowns to quickly find existing customers and products.
  - "Quick Add" feature to create new customers on the fly without leaving the invoice screen.
  - Automatic stock control: prevents selling more items than available and deducts stock upon saving an invoice.
- **Invoice Viewing & Exporting:**
  - View a list of all past invoices.
  - Search for invoices by customer name.
  - Generate and save any invoice as a PDF file, ready for printing or emailing.
  - "Print" option that opens the generated PDF in the system's default viewer.
- **Customization:**
  - Supports custom application icons (`.ico`).
  - Uses a custom font to correctly display currency symbols like the Indian Rupee (₹).

## 🛠️ Technologies Used

- **Backend:** Python 3
- **GUI:** CustomTkinter
- **Database:** SQLite 3 (file-based, no server required)
- **PDF Generation:** FPDF2
- **Executable Bundler:** PyInstaller

## 🚀 Setup and Installation (For Developers)

To run this project from the source code, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/ziymaxcode/Invoice-System.git](https://github.com/ziymaxcode/Invoice-System.git)
    cd Invoice-System
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```
    - On Windows: `venv\Scripts\activate`
    - On macOS/Linux: `source venv/bin/activate`

3.  **Install the required libraries:**
    A `requirements.txt` file is included for convenience.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python main_app.py
    ```
    The first time you run it, a `hardware_store.db` file will be created automatically.

## 📦 Building the Executable (`.exe`)

To package the application into a single executable file for distribution:

1.  Make sure you have all the necessary asset files in the project's root directory:
    - `logo.ico` (your application icon)
    - `DejaVuSans.ttf` (the font for PDF generation)

2.  Run the PyInstaller command from your terminal:
    ```bash
    pyinstaller --onefile --windowed --add-data "DejaVuSans.ttf;." --add-data "logo.ico;." main_app.py
    ```

3.  The final executable will be located in the `dist` folder.

## Usage

To run the application, simply double-click the `.exe` file.

**Important:** For the application to work correctly, the following files must be kept together in the same folder:
- `YourAppName.exe` (the main application)
- `hardware_store.db` (the database file, created on first run)
- `DejaVuSans.ttf` (the font for PDFs)
- `logo.ico` (the application icon)

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
