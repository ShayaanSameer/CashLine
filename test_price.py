#!/usr/bin/env python3

import os
import requests

def test_stock_price():
    """Test the stock price functionality"""
    
    # Set the API key for testing
    os.environ['STOCK_API_KEY'] = 'd23c50hr01qgiro31ghgd23c50hr01qgiro31gi0'
    
    test_symbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'VOO']
    
    print("Testing Stock Price Functionality")
    print("=" * 50)
    
    for symbol in test_symbols:
        print(f"\nGetting price for: {symbol}")
        try:
            finnhub_key = os.environ.get('STOCK_API_KEY')
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={finnhub_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if 'c' in data and data['c'] is not None:
                print(f"Current Price: ${data['c']:.2f}")
                print(f"Change: ${data.get('d', 0):.2f} ({data.get('dp', 0):.2f}%)")
                print(f"High: ${data.get('h', 0):.2f}")
                print(f"Low: ${data.get('l', 0):.2f}")
                print(f"Open: ${data.get('o', 0):.2f}")
                print(f"Previous Close: ${data.get('pc', 0):.2f}")
            else:
                print("No price data available")
                
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_stock_price() 