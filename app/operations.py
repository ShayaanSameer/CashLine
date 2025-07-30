from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, abort, Blueprint, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import requests
import json
from functools import lru_cache
import re
from bson import ObjectId

from .mongoModels import Investment, User, Budget, Expense, Goal, UserProfile, Asset, RetirementPlan

class mongoDBClient:
    def __init__(self, uri):
        self.uri = uri
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))

    def getCollectionEndpoint(self, name):
        return self.client.get_database("cashline").get_collection(name)
    
    def __del__(self):
        self.client.close()

class deserializeDoc:
    @staticmethod
    def user(doc):
        if not doc:
            return None
        return User(
            _id=doc.get('_id'),
            username=doc.get('username'),
            email=doc.get('email'),
            password_hash=doc.get('password_hash'),
            created_at=doc.get('created_at')
        )

    @staticmethod
    def user_profile(doc):
        if not doc:
            return None
        return UserProfile(
            user_id=doc.get('user_id'),
            age=doc.get('age'),
            ra=doc.get('retirement_age'),
            cs=doc.get('current_salary'),
            eri=doc.get('expected_retirement_income'),
            csave=doc.get('current_savings'),
            mc=doc.get('monthly_contribution'),
            rt=doc.get('risk_tolerance'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at'),
            _id=doc.get('_id')
        )

    @staticmethod
    def asset(doc):
        if not doc:
            return None
        return Asset(
            user_id=doc.get('user_id'),
            symbol=doc.get('symbol'),
            name=doc.get('name'),
            asset_type=doc.get('asset_type'),
            expected_return=doc.get('expected_return'),
            weight=doc.get('weight'),
            risk_level=doc.get('risk_level'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at'),
            _id=doc.get('_id')
        )

    @staticmethod
    def retirement_plan(doc):
        if not doc:
            return None
        return RetirementPlan(
            user_id=doc.get('user_id'),
            name=doc.get('name'),
            target_amount=doc.get('target_amount'),
            ytr=doc.get('years_to_retirment'),
            err=doc.get('expected_return_rate'),
            mcn=doc.get('monthly_contribution_needed'),
            pa=doc.get('projected_amount'),
            c_at=doc.get('created_at'),
            u_at=doc.get('updated_at'),
            _id=doc.get('_id')
        )

    @staticmethod
    def budget(doc):
        if not doc:
            return None
        return Budget(
            user_id=doc.get('user_id'),
            category=doc.get('category'),
            limit_amount=doc.get('limit_amount'),
            month=doc.get('month'),
            year=doc.get('year'),
            created_at=doc.get('created_at'),
            _id=doc.get('_id')
        )

    @staticmethod
    def expense(doc):
        if not doc:
            return None
        return Expense(
            user_id=doc.get('user_id'),
            amount=doc.get('amount'),
            category=doc.get('category'),
            description=doc.get('description'),
            date=doc.get('date'),
            currency=doc.get('currency'),
            converted_amount_usd=doc.get('converted_amount_usd'),
            created_at=doc.get('created_at'),
            _id=doc.get('_id')
        )

    @staticmethod
    def investment(doc):
        if not doc:
            return None
        return Investment(
            user_id=doc.get('user_id'),
            symbol=doc.get('symbol'),
            shares=doc.get('shares'),
            purchase_price=doc.get('purchase_price'),
            purchase_date=doc.get('purchase_date'),
            created_at=doc.get('created_at'),
            _id=doc.get('_id')
        )

    @staticmethod
    def goal(doc):
        if not doc:
            return None
        return Goal(
            user_id=doc.get('user_id'),
            name=doc.get('name'),
            target_amount=doc.get('target_amount'),
            current_amount=doc.get('current_amount'),
            target_date=doc.get('target_date'),
            created_at=doc.get('created_at'),
            _id=doc.get('_id')
        )
    
def get_currency_symbol(code):
    CURRENCY_LIST = [
        ('USD', '$'), ('EUR', '€'), ('GBP', '£'), ('INR', '₹'),
        ('CAD', 'C$'), ('AUD', 'A$'), ('JPY', '¥'), ('CNY', '¥'),
        ('CHF', 'Fr'), ('SGD', 'S$'), ('ZAR', 'R'),
    ]
    
    for c, s in CURRENCY_LIST:
        if c == code:
            return s
    return code

@lru_cache(maxsize=32)
def fetch_exchange_rate(base, target, api_key):
    if base == target:
        return 1.0
    try:
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        rate = data['conversion_rates'][target]
        print(f"DEBUG: Exchange rate {base}->{target}: {rate}")
        return rate
    except Exception as e:
        print(f"DEBUG: Exchange rate error for {base}->{target}: {e}")
        return 1.0

def search_stock_api(symbol, finnhub_key):
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
    
    # If no API results, return empty list
    return []

def get_stock_price(symbol, finnhub_key):
    """Get real-time stock price from Finnhub API with fallback to purchase price"""
    try:
        if finnhub_key and finnhub_key != 'your-finnhub-api-key-here':
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={finnhub_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if 'c' in data and data['c'] is not None:
                return {
                    'current_price': data['c'],
                    'change': data.get('d', 0),
                    'change_percent': data.get('dp', 0),
                    'high': data.get('h', 0),
                    'low': data.get('l', 0),
                    'open': data.get('o', 0),
                    'previous_close': data.get('pc', 0),
                    'timestamp': data.get('t', 0)
                }
        else:
            print(f"DEBUG: No valid STOCK_API_KEY found for {symbol}")
    except Exception as e:
        print(f"Error getting stock price for {symbol}: {e}")
    
    return None

def get_company_profile_from_finnhub(symbol, finnhub_key):
    """Get company profile data from Finnhub API for better categorization"""
    try:
        if finnhub_key and finnhub_key != 'your-finnhub-api-key-here':
            # Get company profile
            profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={finnhub_key}"
            profile_response = requests.get(profile_url, timeout=5)
            profile_data = profile_response.json()
            
            # Get company metrics for additional data
            metrics_url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={finnhub_key}"
            metrics_response = requests.get(metrics_url, timeout=5)
            metrics_data = metrics_response.json()
            
            if profile_data and 'ticker' in profile_data:
                return {
                    'symbol': profile_data.get('ticker', symbol),
                    'name': profile_data.get('name', ''),
                    'industry': profile_data.get('finnhubIndustry', ''),
                    'sector': profile_data.get('sector', ''),
                    'country': profile_data.get('country', ''),
                    'currency': profile_data.get('currency', 'USD'),
                    'market_cap': profile_data.get('marketCapitalization', 0),
                    'beta': metrics_data.get('beta', 1.0) if metrics_data else 1.0,
                    'volatility': metrics_data.get('volatility', 0) if metrics_data else 0
                }
    except Exception as e:
        print(f"Error getting company profile from Finnhub for {symbol}: {e}")
    
    return None

def get_expected_return_for_asset(asset_type, symbol=None):
    """Get expected annual return based on asset type and optionally symbol"""
    
    # Base expected returns by asset type (industry averages)
    base_returns = {
        'Stock': 8.0,  # S&P 500 historical average
        'Bond': 4.5,   # Investment grade bonds
        'ETF': 7.5,    # Market-weighted ETFs
        'Mutual Fund': 7.0,  # Actively managed funds
        'Real Estate': 6.0,  # REITs and real estate
        'Commodity': 5.0,    # Gold, oil, etc.
        'Other': 6.0   # Default for other assets
    }
    
    # Specific stock returns for popular companies (if available)
    specific_returns = {
        'AAPL': 9.5,   # Apple - tech growth
        'MSFT': 9.0,   # Microsoft - tech growth
        'GOOGL': 10.0, # Alphabet - tech growth
        'AMZN': 11.0,  # Amazon - high growth
        'TSLA': 12.0,  # Tesla - high growth, high risk
        'META': 9.5,   # Meta - tech growth
        'NVDA': 13.0,  # NVIDIA - AI growth
        'BRK.A': 8.5,  # Berkshire - diversified
        'JNJ': 6.5,    # Johnson & Johnson - stable
        'V': 8.0,      # Visa - financial services
        'JPM': 7.5,    # JPMorgan - banking
        'PG': 6.0,     # Procter & Gamble - consumer staples
        'UNH': 8.5,    # UnitedHealth - healthcare
        'HD': 7.5,     # Home Depot - retail
        'MA': 8.5,     # Mastercard - financial services
        'DIS': 7.0,    # Disney - entertainment
        'PYPL': 9.0,   # PayPal - fintech
    }
    
    # Return specific return if available, otherwise base return
    if symbol and symbol.upper() in specific_returns:
        return specific_returns[symbol.upper()]
    
    return base_returns.get(asset_type, 6.0)

def get_risk_level_for_asset(asset_type, symbol=None):
    """Get risk level based on asset type and optionally symbol"""
    
    # Base risk levels by asset type
    base_risk_levels = {
        'Stock': 'Medium',
        'Bond': 'Low',
        'ETF': 'Medium',
        'Mutual Fund': 'Medium',
        'Real Estate': 'Medium',
        'Commodity': 'High',
        'Other': 'Medium'
    }
    
    # Specific risk levels for popular companies
    specific_risk_levels = {
        # High Risk (Volatile/Growth)
        'TSLA': 'High',    # Tesla - highly volatile
        'NVDA': 'High',    # NVIDIA - AI boom
        'AMZN': 'High',    # Amazon - growth stock
        'META': 'High',    # Meta - tech volatility
        'NFLX': 'High',    # Netflix - streaming wars
        'CRM': 'High',     # Salesforce - tech growth
        
        # Medium Risk (Established Tech)
        'AAPL': 'Medium',  # Apple - stable tech
        'MSFT': 'Medium',  # Microsoft - established
        'GOOGL': 'Medium', # Alphabet - stable
        'PYPL': 'Medium',  # PayPal - fintech
        'V': 'Medium',     # Visa - financial services
        'MA': 'Medium',    # Mastercard - financial
        'HD': 'Medium',    # Home Depot - retail
        'DIS': 'Medium',   # Disney - entertainment
        
        # Low Risk (Defensive)
        'JNJ': 'Low',      # Johnson & Johnson - healthcare
        'PG': 'Low',       # Procter & Gamble - consumer staples
        'BRK.A': 'Low',    # Berkshire - diversified
        'JPM': 'Low',      # JPMorgan - banking
        'UNH': 'Low',      # UnitedHealth - healthcare
        
        # ETFs by risk level
        'VTI': 'Medium',   # Total market ETF
        'VOO': 'Medium',   # S&P 500 ETF
        'QQQ': 'High',     # NASDAQ ETF - tech heavy
        'SPY': 'Medium',   # S&P 500 ETF
        'BND': 'Low',      # Bond ETF
        'GLD': 'High',     # Gold ETF - commodity
        'TLT': 'Low',      # Treasury bonds
        'IEMG': 'High',    # Emerging markets
        'EFA': 'Medium',   # Developed markets
    }
    
    # Return specific risk level if available, otherwise base risk level
    if symbol and symbol.upper() in specific_risk_levels:
        return specific_risk_levels[symbol.upper()]
    
    return base_risk_levels.get(asset_type, 'Medium')

def get_asset_categorization_from_finnhub(symbol, finnhub_key):
    """Get asset categorization based on Finnhub company profile data"""
    profile = get_company_profile_from_finnhub(symbol, finnhub_key)
    
    if not profile:
        return None
    
    # Determine asset type based on industry/sector
    industry = profile.get('industry', '').lower()
    sector = profile.get('sector', '').lower()
    
    # ETF detection
    if any(keyword in profile.get('name', '').lower() for keyword in ['etf', 'fund', 'trust']):
        return 'ETF'
    
    # Bond detection
    if any(keyword in industry for keyword in ['bond', 'fixed income', 'treasury']):
        return 'Bond'
    
    # Real Estate detection
    if any(keyword in industry for keyword in ['real estate', 'reit', 'property']):
        return 'Real Estate'
    
    # Commodity detection
    if any(keyword in industry for keyword in ['commodity', 'gold', 'oil', 'mining']):
        return 'Commodity'
    
    # Mutual Fund detection
    if any(keyword in profile.get('name', '').lower() for keyword in ['fund', 'mutual']):
        return 'Mutual Fund'
    
    # Default to Stock for most companies
    return 'Stock'

def get_enhanced_expected_return(symbol, finnhub_key):
    """Get enhanced expected return using Finnhub data"""
    profile = get_company_profile_from_finnhub(symbol, finnhub_key)
    
    if not profile:
        return get_expected_return_for_asset('Stock', symbol)
    
    # Use beta and volatility to adjust expected returns
    beta = profile.get('beta', 1.0)
    volatility = profile.get('volatility', 0)
    sector = profile.get('sector', '').lower()
    industry = profile.get('industry', '').lower()
    
    # Base return by sector
    sector_returns = {
        'technology': 10.0,
        'healthcare': 8.5,
        'financial services': 7.5,
        'consumer defensive': 6.5,
        'consumer cyclical': 8.0,
        'industrials': 7.0,
        'energy': 6.0,
        'utilities': 5.5,
        'real estate': 6.0,
        'communication services': 8.5,
        'materials': 7.0
    }
    
    # Get base return from sector
    base_return = sector_returns.get(sector, 8.0)
    
    # Adjust based on beta (risk-adjusted return)
    if beta > 1.5:
        base_return += 2.0  # High beta = higher potential return
    elif beta < 0.8:
        base_return -= 1.0  # Low beta = lower potential return
    
    # Adjust based on volatility
    if volatility > 0.3:
        base_return += 1.5  # High volatility = higher potential return
    
    return round(base_return, 1)

def get_enhanced_risk_level(symbol, finnhub_key):
    """Get enhanced risk level using Finnhub data"""
    profile = get_company_profile_from_finnhub(symbol, finnhub_key)
    
    if not profile:
        return get_risk_level_for_asset('Stock', symbol)
    
    beta = profile.get('beta', 1.0)
    volatility = profile.get('volatility', 0)
    sector = profile.get('sector', '').lower()
    
    # Risk assessment based on beta and volatility
    if beta > 1.5 or volatility > 0.4:
        return 'High'
    elif beta < 0.8 and volatility < 0.2:
        return 'Low'
    else:
        return 'Medium'

def calculate_monthly_savings(target_amount, current_savings, years, expected_return):
    """Calculate required monthly savings to reach target"""
    try:
        if years <= 0:
            return 0
        
        future_value = target_amount
        present_value = current_savings
        rate = expected_return / 100
        n = years * 12  # monthly periods
        
        if rate > 0:
            # Avoid division by zero and handle edge cases
            if rate == 0:
                monthly_savings = (future_value - present_value) / n
            else:
                monthly_rate = rate / 12
                if monthly_rate == 0:
                    monthly_savings = (future_value - present_value) / n
                else:
                    monthly_savings = (future_value - present_value * (1 + monthly_rate)**n) / (((1 + monthly_rate)**n - 1) / monthly_rate)
        else:
            monthly_savings = (future_value - present_value) / n
        
        return max(0, monthly_savings)
    except Exception as e:
        print(f"Error in calculate_monthly_savings: {e}")
        return 0

def summarize_user_financial_context(client):
    """Summarize the user's current financial situation for AI context"""
    # Get user's data
    budgets = list(client.getCollectionEndpoint('Budget').find({"user_id":current_user._id}))
    for i in range(0, len(budgets)):
        budgets[i] = deserializeDoc.budget(budgets[i])
    # budgets = Budget.query.filter_by(user_id=current_user.id).all()
    expenses = list(client.getCollectionEndpoint('Expense').find({"user_id":current_user._id}))
    for i in range(0, len(expenses)):
        expenses[i] = deserializeDoc.expense(expenses[i])
    # expenses = Expense.query.filter_by(user_id=current_user.id).all()
    investments = list(client.getCollectionEndpoint('Investment').find({"user_id":current_user._id}))
    for i in range(0, len(investments)):
        investments[i] = deserializeDoc.investment(investments[i])
    # investments = Investment.query.filter_by(user_id=current_user.id).all()
    goals = list(client.getCollectionEndpoint('Goal').find({"user_id":current_user._id}))
    for i in range(0, len(goals)):
        goals[i] = deserializeDoc.goal(goals[i])
    # goals = Goal.query.filter_by(user_id=current_user.id).all()
    
    # Calculate totals
    total_budget = sum(b.limit_amount for b in budgets)
    total_expenses = sum(e.converted_amount_usd for e in expenses)
    total_investments = sum(i.shares * i.purchase_price for i in investments)
    total_goals = sum(g.target_amount for g in goals)
    current_income = session.get('monthly_income', 0)
    
    # Build context summary
    context_lines = [f"Current financial summary for {current_user.username}:"]
    
    # Income
    if current_income > 0:
        context_lines.append(f"Monthly income: ${current_income:.2f}")
    
    # Budget summary
    if budgets:
        context_lines.append(f"Total budget: ${total_budget:.2f}, Total spent: ${total_expenses:.2f}")
        context_lines.append("Budget Categories:")
        for budget in budgets:
            spent = sum(e.converted_amount_usd for e in expenses if e.category == budget.category)
            context_lines.append(f"- {budget.category}: limit ${budget.limit_amount:.2f}, spent ${spent:.2f}")
    else:
        context_lines.append(f"Total expenses: ${total_expenses:.2f}")
    
    # Recent expenses
    if expenses:
        context_lines.append("Recent expenses:")
        for expense in expenses[-5:]:  # Last 5 expenses
            context_lines.append(f"- ${expense.converted_amount_usd:.2f} on {expense.category} ({expense.description}) at {expense.date.strftime('%Y-%m-%d')}")
    
    # Goals
    if goals:
        context_lines.append("Financial goals:")
        for goal in goals:
            progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
            deadline = goal.target_date.strftime('%Y-%m-%d') if goal.target_date else 'No deadline'
            context_lines.append(f"- {goal.name}: target ${goal.target_amount:.2f}, saved ${goal.current_amount:.2f} ({progress:.1f}% complete), deadline {deadline}")
    
    # Investments
    if investments:
        context_lines.append("Investments:")
        for inv in investments:
            context_lines.append(f"- {inv.symbol}: {inv.shares} shares, purchase price ${inv.purchase_price:.2f}, purchase date {inv.purchase_date.strftime('%Y-%m-%d')}")
        context_lines.append(f"Total portfolio value: ${total_investments:.2f}")
    
    return "\n".join(context_lines)

