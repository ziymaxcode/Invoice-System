import sqlite3
import sys
import os

def get_db_path():
    """Gets the correct path to the database file."""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'hardware_store.db')

def setup_database():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # --- Create tables ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
        price REAL NOT NULL, stock INTEGER DEFAULT 0 )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        phone TEXT, address TEXT )
    ''')
    # --- UPDATED: Added subtotal and discount columns ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER,
        invoice_date TEXT NOT NULL, 
        subtotal_amount REAL NOT NULL,
        discount_percent REAL DEFAULT 0,
        total_amount REAL NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (id) )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL, quantity INTEGER NOT NULL,
        price_per_unit REAL NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices (id),
        FOREIGN KEY (product_id) REFERENCES products (id) )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    setup_database()
    print(f"Database setup complete at: {get_db_path()}")