#!/usr/bin/env python3

import os
import sys
import requests
from datetime import datetime

def search_stock_api(symbol):
    """Search for stock information using multiple fallback options"""
    symbol = symbol.upper().strip()
    
    # Curated list of popular stocks as fallback
    popular_stocks = {
        'AAPL': {'name': 'Apple Inc.', 'type': 'Stock', 'region': 'US'},
        'MSFT': {'name': 'Microsoft Corporation', 'type': 'Stock', 'region': 'US'},
        'GOOGL': {'name': 'Alphabet Inc.', 'type': 'Stock', 'region': 'US'},
        'AMZN': {'name': 'Amazon.com Inc.', 'type': 'Stock', 'region': 'US'},
        'TSLA': {'name': 'Tesla Inc.', 'type': 'Stock', 'region': 'US'},
        'META': {'name': 'Meta Platforms Inc.', 'type': 'Stock', 'region': 'US'},
        'NVDA': {'name': 'NVIDIA Corporation', 'type': 'Stock', 'region': 'US'},
        'BRK.A': {'name': 'Berkshire Hathaway Inc.', 'type': 'Stock', 'region': 'US'},
        'JNJ': {'name': 'Johnson & Johnson', 'type': 'Stock', 'region': 'US'},
        'V': {'name': 'Visa Inc.', 'type': 'Stock', 'region': 'US'},
        'JPM': {'name': 'JPMorgan Chase & Co.', 'type': 'Stock', 'region': 'US'},
        'PG': {'name': 'Procter & Gamble Co.', 'type': 'Stock', 'region': 'US'},
        'UNH': {'name': 'UnitedHealth Group Inc.', 'type': 'Stock', 'region': 'US'},
        'HD': {'name': 'Home Depot Inc.', 'type': 'Stock', 'region': 'US'},
        'MA': {'name': 'Mastercard Inc.', 'type': 'Stock', 'region': 'US'},
        'DIS': {'name': 'Walt Disney Co.', 'type': 'Stock', 'region': 'US'},
        'PYPL': {'name': 'PayPal Holdings Inc.', 'type': 'Stock', 'region': 'US'},
        'NFLX': {'name': 'Netflix Inc.', 'type': 'Stock', 'region': 'US'},
        'CRM': {'name': 'Salesforce Inc.', 'type': 'Stock', 'region': 'US'},
        'INTC': {'name': 'Intel Corporation', 'type': 'Stock', 'region': 'US'},
        'VTI': {'name': 'Vanguard Total Stock Market ETF', 'type': 'ETF', 'region': 'US'},
        'VOO': {'name': 'Vanguard S&P 500 ETF', 'type': 'ETF', 'region': 'US'},
        'QQQ': {'name': 'Invesco QQQ Trust', 'type': 'ETF', 'region': 'US'},
        'SPY': {'name': 'SPDR S&P 500 ETF Trust', 'type': 'ETF', 'region': 'US'},
        'BND': {'name': 'Vanguard Total Bond Market ETF', 'type': 'ETF', 'region': 'US'},
        'GLD': {'name': 'SPDR Gold Shares', 'type': 'ETF', 'region': 'US'},
        'TLT': {'name': 'iShares 20+ Year Treasury Bond ETF', 'type': 'ETF', 'region': 'US'},
        'IEMG': {'name': 'iShares Core MSCI Emerging Markets ETF', 'type': 'ETF', 'region': 'US'},
        'EFA': {'name': 'iShares MSCI EAFE ETF', 'type': 'ETF', 'region': 'US'}
    }
    
    # First, try exact match in popular stocks
    if symbol in popular_stocks:
        stock_info = popular_stocks[symbol]
        return [{
            'symbol': symbol,
            'name': stock_info['name'],
            'type': stock_info['type'],
            'region': stock_info['region']
        }]
    
    # Then, try partial matches in popular stocks
    matches = []
    for ticker, info in popular_stocks.items():
        if symbol in ticker or symbol in info['name'].upper():
            matches.append({
                'symbol': ticker,
                'name': info['name'],
                'type': info['type'],
                'region': info['region']
            })
            if len(matches) >= 5:
                break
    
    # If we found matches, return them
    if matches:
        return matches
    
            # Try Finnhub API (recommended - free tier with 60 calls/minute)
        try:
            finnhub_key = os.environ.get('STOCK_API_KEY')
            if finnhub_key:
                url = f"https://finnhub.io/api/v1/search?q={symbol}&token={finnhub_key}"
                response = requests.get(url, timeout=5)
                data = response.json()
                
                if 'result' in data and data['result']:
                    api_matches = []
                    for match in data['result'][:5]:
                        api_matches.append({
                            'symbol': match.get('symbol', ''),
                            'name': match.get('description', ''),
                            'type': match.get('type', 'Stock'),
                            'region': match.get('primaryExchange', 'US')
                        })
                    return api_matches
        except Exception as e:
            print(f"Finnhub API error: {e}")
    
    # Try IEX Cloud API as second fallback
    try:
        iex_key = os.environ.get('IEX_API_KEY')
        if iex_key:
            url = f"https://cloud.iexapis.com/stable/search/{symbol}?token={iex_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data:
                api_matches = []
                for match in data[:5]:
                    api_matches.append({
                        'symbol': match.get('symbol', ''),
                        'name': match.get('name', ''),
                        'type': 'Stock',
                        'region': 'US'
                    })
                return api_matches
    except Exception as e:
        print(f"IEX API error: {e}")
    
    # Try Alpha Vantage API as final fallback
    try:
        alpha_key = os.environ.get('ALPHA_VANTAGE_API_KEY', 'demo')
        url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={symbol}&apikey={alpha_key}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'bestMatches' in data and data['bestMatches']:
            api_matches = []
            for match in data['bestMatches'][:5]:
                api_matches.append({
                    'symbol': match['1. symbol'],
                    'name': match['2. name'],
                    'type': match['3. type'],
                    'region': match['4. region']
                })
            return api_matches
    except Exception as e:
        print(f"Alpha Vantage API error: {e}")
    
    # If no API results, return empty list
    return []

def test_stock_search():
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'VOO', 'SPY', 'BND', 'INVALID', 'APPLE', 'MICROSOFT']
    
    print("Testing Stock Search Function")
    print("=" * 50)
    
    for symbol in test_symbols:
        print(f"\nSearching for: {symbol}")
        results = search_stock_api(symbol)
        
        if results:
            print(f"Found {len(results)} result(s):")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['symbol']} - {result['name']} ({result['type']}, {result['region']})")
        else:
            print("No results found")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_stock_search() 