import sqlite3
from .database import get_db_path
import datetime

try:
    import yfinance as yf
except ImportError:
    yf = None

DB_PATH = get_db_path()

def add_investment(symbol, shares, purchase_price, purchase_date):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                shares REAL NOT NULL,
                purchase_price REAL NOT NULL,
                purchase_date TEXT
            )
            """
        )
        c.execute(
            "INSERT INTO investments (symbol, shares, purchase_price, purchase_date) VALUES (?, ?, ?, ?)",
            (symbol.upper(), shares, purchase_price, purchase_date)
        )
        conn.commit()

def get_all_investments():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, symbol, shares, purchase_price, purchase_date FROM investments")
        return c.fetchall()

def get_current_price(symbol):
    if yf is None:
        return None
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[0])
    except Exception:
        pass
    return None

def calculate_portfolio(investments):
    details = []
    total_value = 0
    for inv in investments:
        id, symbol, shares, purchase_price, purchase_date = inv
        current_price = get_current_price(symbol)
        if current_price:
            value = current_price * shares
            gain = value - (purchase_price * shares)
            details.append({
                "id": id,
                "symbol": symbol,
                "shares": shares,
                "purchase_price": purchase_price,
                "current_price": current_price,
                "value": value,
                "gain": gain,
                "purchase_date": purchase_date
            })
            total_value += value
    return total_value, details 