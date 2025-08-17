import sqlite3
import sys
import os

def get_db_path():
    """Gets the correct path to the database file."""
    if getattr(sys, 'frozen', False):
        # Running as a bundled .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as a .py script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'hardware_store.db')

DB_PATH = get_db_path()

def get_db_connection():
    """Establishes and returns a database connection and cursor for SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        return conn, cursor
    except sqlite3.Error as err:
        print(f"Error connecting to database: {err}")
        return None, None