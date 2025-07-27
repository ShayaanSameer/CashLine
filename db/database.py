"""
database.py
-----------
Database initialization and path management for the personal finance app.
Ensures the SQLite database and required tables exist. Provides a function to get the database path.
"""
import sqlite3
import os

# Get the absolute path to the database file in the db directory
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "personal_finance.db")

def get_db_path():
    """Return the absolute path to the SQLite database file.

    Returns the path to the SQLite database file used by the application. This is used by other modules to connect to the database.

    Returns:
        str: Absolute path to the SQLite database file.
    """
    return DB_PATH

# Ensure the database file exists and tables are created
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

"""
        ids to handle duplicates
 - database: personal_finance
    - Tables: 
        - 1.) budget (category, limit_amount, month, year)
        - 2.) expenses (amount, category, description, date, currency)
        
"""

# budget table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS budget (
               id INTEGER,
               category TEXT,
               limit_amount REAL,
               month TEXT,
               year INTEGER
                )''')

# expenses table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS expenses (
               id INTEGER,
               amount REAL,
               category TEXT,
               description TEXT,
               date DATE,
               currency TEXT )''')

# income table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS income (
    month TEXT,
    year INTEGER,
    amount REAL
)''')

# investments table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS investments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    shares REAL NOT NULL,
    purchase_price REAL NOT NULL,
    purchase_date TEXT
)''')

# categories table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    color TEXT NOT NULL
)''')

# goals table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    saved_amount REAL NOT NULL DEFAULT 0,
    deadline TEXT
)''')

# Insert default categories if table is empty
cursor.execute('SELECT COUNT(*) FROM categories')
if cursor.fetchone()[0] == 0:
    default_categories = [
        ("Dining", "#607D8B"),
        ("Groceries", "#4CAF50"),
        ("Shopping", "#E91E63"),
        ("Transit", "#FFEB3B"),
        ("Entertainment", "#2196F3"),
        ("Bills & Fees", "#009688"),
        ("Gifts", "#F44336"),
        ("Beauty", "#9C27B0"),
        ("Work", "#795548"),
        ("Travel", "#FF9800"),
        ("Income", "#7C4DFF")
    ]
    cursor.executemany('INSERT INTO categories (name, color) VALUES (?, ?)', default_categories)

# after making tables, commit changes
connection.commit()

# print table (budget)
# cursor.execute("SELECT * FROM budget")
# print(cursor.fetchall())

# close connection to database
connection.close()

# --- RESET DB: Drop and recreate tables ---
def reset_db():
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute('DROP TABLE IF EXISTS budget')
    cursor.execute('DROP TABLE IF EXISTS expenses')
    cursor.execute('DROP TABLE IF EXISTS income')
    cursor.execute('DROP TABLE IF EXISTS categories')
    cursor.execute('DROP TABLE IF EXISTS goals')
    cursor.execute('DROP TABLE IF EXISTS investments')  # <-- Add this line
    # Recreate tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS budget (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        limit_amount REAL NOT NULL,
        month TEXT NOT NULL,
        year INTEGER NOT NULL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL,
        currency TEXT NOT NULL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT NOT NULL,
        year INTEGER NOT NULL,
        amount REAL NOT NULL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        color TEXT NOT NULL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        target_amount REAL NOT NULL,
        saved_amount REAL NOT NULL DEFAULT 0,
        deadline TEXT
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS investments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        shares REAL NOT NULL,
        purchase_price REAL NOT NULL,
        purchase_date TEXT
    )''')
    # Insert default categories if table is empty
    cursor.execute('SELECT COUNT(*) FROM categories')
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ("Dining", "#607D8B"),
            ("Groceries", "#4CAF50"),
            ("Shopping", "#E91E63"),
            ("Transit", "#FFEB3B"),
            ("Entertainment", "#2196F3"),
            ("Bills & Fees", "#009688"),
            ("Gifts", "#F44336"),
            ("Beauty", "#9C27B0"),
            ("Work", "#795548"),
            ("Travel", "#FF9800")
        ]
        cursor.executemany('INSERT INTO categories (name, color) VALUES (?, ?)', default_categories)
    connection.commit()
    connection.close() 