#!/usr/bin/env python3

import os
import requests

def test_finnhub_api():
    """Test the Finnhub API integration"""
    
    # Set the API key for testing
    os.environ['STOCK_API_KEY'] = 'd23c50hr01qgiro31ghgd23c50hr01qgiro31gi0'
    
    test_symbols = ['AAPL', 'TSLA', 'VOO', 'MSFT', 'GOOGL']
    
    print("Testing Finnhub API Integration")
    print("=" * 50)
    
    for symbol in test_symbols:
        print(f"\nSearching for: {symbol}")
        try:
            finnhub_key = os.environ.get('STOCK_API_KEY')
            url = f"https://finnhub.io/api/v1/search?q={symbol}&token={finnhub_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if 'result' in data and data['result']:
                print(f"Found {len(data['result'])} result(s):")
                for i, match in enumerate(data['result'][:3], 1):  # Show first 3 results
                    print(f"  {i}. {match.get('symbol', '')} - {match.get('description', '')} ({match.get('type', 'Stock')})")
            else:
                print("No results found")
                
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_finnhub_api() 