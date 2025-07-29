from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import requests
import json
from functools import lru_cache
import re
from bson import ObjectId

from config import config
from forms import LoginForm, RegistrationForm, BudgetForm, ExpenseForm, InvestmentForm, GoalForm, UserProfileForm, AssetForm, RetirementPlanForm, AutomatedRetirementForm, RetirementProfileForm, RetirementCalculatorForm

from mongoModels import Investment, User, Budget, Expense, Goal, UserProfile, Asset, RetirementPlan
from mongodb_operations import mongoDBClient, deserializeDoc

# Load environment variables
load_dotenv()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    dbClient = mongoDBClient(app.config["MONGO_URI"])
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        userDoc = dbClient.getCollectionEndpoint('User').find_one({"_id":ObjectId(user_id)})
        if userDoc:
            return deserializeDoc.user(userDoc)
        else:
            return None
    
    # Register routes
    register_routes(app, dbClient)
    
    return app

def register_routes(app, mongoClient):
    # Load environment variables
    GEMINI_API_KEY = app.config["GEMINI_API_KEY"]
    
    # Helper to get current month and year
    now = datetime.now()
    CURRENT_MONTH = now.strftime('%B')
    CURRENT_YEAR = now.year
    
    CURRENCY_LIST = [
        ('USD', '$'), ('EUR', '€'), ('GBP', '£'), ('INR', '₹'),
        ('CAD', 'C$'), ('AUD', 'A$'), ('JPY', '¥'), ('CNY', '¥'),
        ('CHF', 'Fr'), ('SGD', 'S$'), ('ZAR', 'R'),
    ]
    
    def get_currency_symbol(code):
        for c, s in CURRENCY_LIST:
            if c == code:
                return s
        return code
    
    @lru_cache(maxsize=32)
    def fetch_exchange_rate(base, target):
        if base == target:
            return 1.0
        try:
            # Get API key from environment or use free tier
            api_key = os.environ.get('EXCHANGE_RATE_API_KEY')
            url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}"
            resp = requests.get(url, timeout=5)
            data = resp.json()
            rate = data['conversion_rates'][target]
            print(f"DEBUG: Exchange rate {base}->{target}: {rate}")
            return rate
        except Exception as e:
            print(f"DEBUG: Exchange rate error for {base}->{target}: {e}")
            return 1.0
    
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

    def get_stock_price(symbol):
        """Get real-time stock price from Finnhub API with fallback to purchase price"""
        try:
            finnhub_key = os.environ.get('STOCK_API_KEY')
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
    
    def get_company_profile_from_finnhub(symbol):
        """Get company profile data from Finnhub API for better categorization"""
        try:
            finnhub_key = os.environ.get('STOCK_API_KEY')
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

    def get_asset_categorization_from_finnhub(symbol):
        """Get asset categorization based on Finnhub company profile data"""
        profile = get_company_profile_from_finnhub(symbol)
        
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

    def get_enhanced_expected_return(symbol):
        """Get enhanced expected return using Finnhub data"""
        profile = get_company_profile_from_finnhub(symbol)
        
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

    def get_enhanced_risk_level(symbol):
        """Get enhanced risk level using Finnhub data"""
        profile = get_company_profile_from_finnhub(symbol)
        
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

    @app.route('/investments/retirement/assets/get_expected_return')
    @login_required
    def get_expected_return():
        """API endpoint to get expected return and risk level for asset type and symbol"""
        asset_type = request.args.get('asset_type', '')
        symbol = request.args.get('symbol', '')
        
        # Try to get enhanced data from Finnhub first
        if symbol:
            enhanced_return = get_enhanced_expected_return(symbol)
            enhanced_risk = get_enhanced_risk_level(symbol)
            enhanced_asset_type = get_asset_categorization_from_finnhub(symbol)
            
            return jsonify({
                'expected_return': enhanced_return,
                'risk_level': enhanced_risk,
                'asset_type': enhanced_asset_type or asset_type,
                'symbol': symbol,
                'source': 'finnhub'
            })
        
        # Fallback to our curated data
        expected_return = get_expected_return_for_asset(asset_type, symbol)
        risk_level = get_risk_level_for_asset(asset_type, symbol)
        
        return jsonify({
            'expected_return': expected_return,
            'risk_level': risk_level,
            'asset_type': asset_type,
            'symbol': symbol,
            'source': 'curated'
        })

    @app.route('/portfolio/allocation/get_expected_return')
    @login_required
    def get_allocation_expected_return():
        """API endpoint to get expected return and risk level for asset type and symbol"""
        asset_type = request.args.get('asset_type', '')
        symbol = request.args.get('symbol', '')
        
        # Try to get enhanced data from Finnhub first
        if symbol:
            enhanced_return = get_enhanced_expected_return(symbol)
            enhanced_risk = get_enhanced_risk_level(symbol)
            enhanced_asset_type = get_asset_categorization_from_finnhub(symbol)
            
            return jsonify({
                'expected_return': enhanced_return,
                'risk_level': enhanced_risk,
                'asset_type': enhanced_asset_type or asset_type,
                'symbol': symbol,
                'source': 'finnhub'
            })
        
        # Fallback to our curated data
        expected_return = get_expected_return_for_asset(asset_type, symbol)
        risk_level = get_risk_level_for_asset(asset_type, symbol)
        
        return jsonify({
            'expected_return': expected_return,
            'risk_level': risk_level,
            'asset_type': asset_type,
            'symbol': symbol,
            'source': 'curated'
        })
    
    @app.route('/set_currency', methods=['POST', 'GET'])
    def set_currency():
        code = request.values.get('currency', 'USD').upper()
        if code not in [c[0] for c in CURRENCY_LIST]:
            code = 'USD'
        session['currency'] = code
        rate = fetch_exchange_rate(code, 'USD')
        session['exchange_rate'] = rate
        session['currency_rate'] = rate
        return redirect(request.referrer or url_for('dashboard'))
    
    # Unified Portfolio Management Routes
    @app.route('/portfolio')
    @login_required
    def portfolio_overview():
        """Main portfolio dashboard - unified view of all investments and retirement planning"""
        # Get current investments
        current_investments = list(mongoClient.getCollectionEndpoint('Investment').find({"user_id":current_user._id}))
        for i in range(0, len(current_investments)):
            current_investments[i] = deserializeDoc.investment(current_investments[i])

        # Get retirement profile
        profile = deserializeDoc.user_profile(mongoClient.getCollectionEndpoint('UserProfile').find_one({"user_id":current_user._id}))
        
        # Get retirement assets (portfolio allocation)
        retirement_assets = list(mongoClient.getCollectionEndpoint('Asset').find({"user_id":current_user._id}))
        for i in range(0, len(retirement_assets)):
            retirement_assets[i] = deserializeDoc.asset(retirement_assets[i])

        # Get retirement plans
        retirement_plans = list(mongoClient.getCollectionEndpoint('RetirementPlan').find({"user_id":current_user._id}))
        for i in range(0, len(retirement_plans)):
            retirement_plans[i] = deserializeDoc.retirement_plan(retirement_plans[i])

        # Get real-time prices for current investments (limit to first 5 to avoid API limits)
        investment_prices = {}
        for investment in current_investments[:5]:
            price_data = get_stock_price(investment.symbol)
            if price_data:
                investment_prices[investment.symbol] = price_data
            else:
                # Fallback: use purchase price as current price when API fails
                investment_prices[investment.symbol] = {
                    'current_price': investment.purchase_price,
                    'change': 0,
                    'change_percent': 0,
                    'high': investment.purchase_price,
                    'low': investment.purchase_price,
                    'open': investment.purchase_price,
                    'previous_close': investment.purchase_price,
                    'timestamp': 0
                }
        
        # Calculate portfolio summary
        total_purchase_value = sum(inv.shares * inv.purchase_price for inv in current_investments)
        total_current_value = 0
        total_gain_loss = 0
        total_gain_loss_percent = 0
        
        # Calculate current values and gains/losses
        for investment in current_investments:
            if investment.symbol in investment_prices:
                current_price = investment_prices[investment.symbol]['current_price']
                current_value = investment.shares * current_price
                purchase_value = investment.shares * investment.purchase_price
                gain_loss = current_value - purchase_value
                
                total_current_value += current_value
                total_gain_loss += gain_loss
            else:
                # Fallback to purchase price if no current price available
                total_current_value += investment.shares * investment.purchase_price
        
        # Calculate total gain/loss percentage
        if total_purchase_value > 0:
            total_gain_loss_percent = (total_gain_loss / total_purchase_value) * 100
        
        total_retirement_assets = len(retirement_assets)
        
        return render_template('portfolio_overview.html', 
                             current_investments=current_investments,
                             investment_prices=investment_prices,
                             profile=profile,
                             retirement_assets=retirement_assets,
                             retirement_plans=retirement_plans,
                             total_purchase_value=total_purchase_value,
                             total_current_value=total_current_value,
                             total_gain_loss=total_gain_loss,
                             total_gain_loss_percent=total_gain_loss_percent,
                             total_retirement_assets=total_retirement_assets)

    # Current Holdings Management
    @app.route('/portfolio/holdings')
    @login_required
    def current_holdings():
        """Manage current investment holdings with real-time tracking"""
        investments = list(mongoClient.getCollectionEndpoint('Investment').find({"user_id":current_user._id}))
        for i in range(len(investments)):
            investments[i] = deserializeDoc.investment(investments[i])

        # Calculate portfolio summary values
        total_purchase_value = 0
        total_current_value = 0
        total_gain_loss = 0
        
        # Get real-time prices
        investment_prices = {}
        for investment in investments[:10]:  # Limit to avoid API rate limits
            price_data = get_stock_price(investment.symbol)
            if price_data:
                investment_prices[investment.symbol] = price_data
                print(f"DEBUG: Got real-time price for {investment.symbol}: ${price_data['current_price']}")
            else:
                # Fallback: use purchase price as current price when API fails
                investment_prices[investment.symbol] = {
                    'current_price': investment.purchase_price,
                    'change': 0,
                    'change_percent': 0,
                    'high': investment.purchase_price,
                    'low': investment.purchase_price,
                    'open': investment.purchase_price,
                    'previous_close': investment.purchase_price,
                    'timestamp': 0
                }
                print(f"DEBUG: Using fallback price for {investment.symbol}: ${investment.purchase_price}")
            
            # Calculate values for this investment
            purchase_value = investment.shares * investment.purchase_price
            current_value = investment.shares * investment_prices[investment.symbol]['current_price']
            gain_loss = current_value - purchase_value
            
            total_purchase_value += purchase_value
            total_current_value += current_value
            total_gain_loss += gain_loss
            
            print(f"DEBUG: {investment.symbol} - Purchase: ${purchase_value:.2f}, Current: ${current_value:.2f}, Gain/Loss: ${gain_loss:.2f}")
        
        total_gain_loss_pct = (total_gain_loss / total_purchase_value) * 100 if total_purchase_value > 0 else 0
        
        print(f"DEBUG: Portfolio Summary - Purchase: ${total_purchase_value:.2f}, Current: ${total_current_value:.2f}, Gain/Loss: ${total_gain_loss:.2f}, Return: {total_gain_loss_pct:.1f}%")
        
        return render_template('current_holdings.html', 
                             investments=investments,
                             investment_prices=investment_prices,
                             total_purchase_value=total_purchase_value,
                             total_current_value=total_current_value,
                             total_gain_loss=total_gain_loss,
                             total_gain_loss_pct=total_gain_loss_pct)

    @app.route('/portfolio/holdings/add', methods=['GET', 'POST'])
    @login_required
    def add_holding():
        form = InvestmentForm()
        if form.validate_on_submit():
            investment = Investment(
                user_id=current_user._id,
                symbol=form.symbol.data.upper(),
                shares=form.shares.data,
                purchase_price=form.purchase_price.data,
                purchase_date=datetime.combine(form.purchase_date.data, datetime.min.time())
            )
            mongoClient.getCollectionEndpoint('Investment').insert_one(vars(investment))
            flash('Investment added successfully!', 'success')
            return redirect(url_for('current_holdings'))
        
        return render_template('add_holding.html', form=form)

    @app.route('/portfolio/holdings/edit/<investment_id>', methods=['GET', 'POST'])
    @login_required
    def edit_holding(investment_id):
        investment_doc = mongoClient.getCollectionEndpoint('Investment').find_one({"_id": ObjectId(investment_id)})
        if not investment_doc:
            abort(404)
        investment = deserializeDoc.investment(investment_doc)
        
        if investment.user_id != current_user._id:
            flash('Access denied.', 'error')
            return redirect(url_for('current_holdings'))
        
        form = InvestmentForm()
        if form.validate_on_submit():
            investment.symbol = form.symbol.data.upper()
            investment.shares = form.shares.data
            investment.purchase_price = form.purchase_price.data
            investment.purchase_date = form.purchase_date.data
            investment.updated_at = datetime.now()
            
            mongoClient.getCollectionEndpoint('Investment').update_one(
                {"_id": ObjectId(investment_id)},
                {"$set": {
                    "symbol": investment.symbol,
                    "shares": investment.shares,
                    "purchase_price": investment.purchase_price,
                    "purchase_date": investment.purchase_date,
                    "updated_at": investment.updated_at
                }})

            flash('Investment updated successfully!', 'success')
            return redirect(url_for('current_holdings'))
        
        elif request.method == 'GET':
            form.symbol.data = investment.symbol
            form.shares.data = investment.shares
            form.purchase_price.data = investment.purchase_price
            form.purchase_date.data = investment.purchase_date
        
        return render_template('edit_holding.html', form=form, investment=investment)

    @app.route('/portfolio/holdings/delete/<investment_id>', methods=['POST'])
    @login_required
    def delete_holding(investment_id):
        investment_doc = mongoClient.getCollectionEndpoint('Investment').find_one({"_id": ObjectId(investment_id)})
        if not investment_doc:
            abort(404)
        investment = deserializeDoc.investment(investment_doc)

        if investment.user_id != current_user._id:
            flash('Access denied.', 'error')
            return redirect(url_for('current_holdings'))
        
        mongoClient.getConnectionEndpoint('Investment').delete_one({"_id" : ObjectId(investment_id)})
        flash('Investment deleted successfully!', 'success')
        return redirect(url_for('current_holdings'))

    # Retirement Planning
    @app.route('/portfolio/retirement')
    @login_required
    def retirement_planning():
        """Retirement planning dashboard"""
        profile_doc = mongoClient.getCollectionEndpoint('UserProfile').find_one({"user_id":current_user._id})
        profile = deserializeDoc.user_profile(profile_doc)
        
        retirement_plans = list(mongoClient.getCollectionEndpoint('RetirementPlan').find({"user_id":current_user._id}))
        for i in range(retirement_plans):
            retirement_plans[i] = deserializeDoc.retirement_plan(retirement_plans[i])

        retirement_assets = list(mongoClient.getCollectionEndpoint('Asset').find({"user_id":current_user._id}))
        for i in range(retirement_assets):
            retirement_assets[i] = deserializeDoc.asset(retirement_assets[i])
        
        return render_template('retirement_planning.html',
                             profile=profile,
                             retirement_plans=retirement_plans,
                             retirement_assets=retirement_assets)

    @app.route('/portfolio/retirement/profile', methods=['GET', 'POST'])
    @login_required
    def retirement_profile():
        """Manage retirement profile and goals"""
        profile_doc = mongoClient.getCollectionEndpoint('UserProfile').find_one({"user_id":current_user._id})
        profile = deserializeDoc.user_profile(profile_doc)
        form = RetirementProfileForm()
        
        if form.validate_on_submit():
            if profile:
                profile.age = form.current_age.data
                profile.retirement_age = form.retirement_age.data
                profile.current_salary = form.current_income.data
                profile.expected_retirement_income = form.expected_retirement_income.data
                profile.current_savings = form.current_savings.data
                profile.updated_at = datetime.now()
            else:
                profile = UserProfile(
                    user_id=current_user._id,
                    age=form.current_age.data,
                    retirement_age=form.retirement_age.data,
                    current_salary=form.current_income.data,
                    expected_retirement_income=form.expected_retirement_income.data,
                    current_savings=form.current_savings.data
                )
                mongoClient.getCollectionEndpoint('UserProfile').insert_one(vars(profile))
            
            flash('Retirement profile updated successfully!', 'success')
            return redirect(url_for('retirement_planning'))
        
        elif request.method == 'GET' and profile:
            form.current_age.data = profile.age
            form.retirement_age.data = profile.retirement_age
            form.current_income.data = profile.current_salary
            form.expected_retirement_income.data = profile.expected_retirement_income
            form.current_savings.data = profile.current_savings
        
        return render_template('retirement_profile.html', form=form, profile=profile)

    # Asset Allocation Management
    @app.route('/portfolio/allocation')
    @login_required
    def asset_allocation():
        """Manage retirement portfolio asset allocation"""
        assets = list(mongoClient.getConnectionEndpoint('Asset').find({"user_id":current_user._id}))
        for i in range(len(assets)):
            assets[i] = deserializeDoc.asset(assets[i])
        
        # Calculate portfolio summary
        total_weight = sum(asset.weight for asset in assets)
        weighted_return = sum(asset.expected_return * asset.weight / 100 for asset in assets)
        
        return render_template('asset_allocation.html', assets=assets, total_weight=total_weight, weighted_return=weighted_return)

    @app.route('/portfolio/allocation/add', methods=['GET', 'POST'])
    @login_required
    def add_asset():
        form = AssetForm()
        
        if form.validate_on_submit():
            # Auto-populate expected return and risk level if not provided or is 0
            if not form.expected_return.data or form.expected_return.data == 0:
                form.expected_return.data = get_enhanced_expected_return(
                    form.symbol.data
                )
            
            # Auto-populate risk level if not provided
            if not form.risk_level.data:
                form.risk_level.data = get_enhanced_risk_level(
                    form.symbol.data
                )
            
            # Check weight constraints
            assets = list(mongoClient.getConnectionEndpoint('Asset').find({"user_id":current_user._id}))
            for i in range(len(assets)):
                assets[i] = deserializeDoc.asset(assets[i])

            existing_weight = sum(a.weight for a in assets)
            if existing_weight + form.weight.data > 100:
                flash('Total portfolio weight cannot exceed 100%. Current total: {:.1f}%'.format(existing_weight), 'error')
                return render_template('add_asset.html', form=form)
            
            asset = Asset(
                user_id=current_user._id,
                symbol=form.symbol.data.upper(),
                name=form.name.data,
                asset_type=form.asset_type.data,
                expected_return=form.expected_return.data,
                weight=form.weight.data,
                risk_level=form.risk_level.data
            )
            mongoClient.getConnectionEndpoint('Asset').insert_one(vars(asset))
            flash('Asset added successfully!', 'success')
            return redirect(url_for('asset_allocation'))
        
        return render_template('add_asset.html', form=form)

    @app.route('/portfolio/allocation/search')
    @login_required
    def search_assets():
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify([])
        
        results = search_stock_api(query)
        
        # Add price information to each result
        for result in results:
            price_data = get_stock_price(result['symbol'])
            if price_data:
                result['price'] = price_data
        
        return jsonify(results)

    @app.route('/portfolio/holdings/search')
    @login_required
    def search_holdings():
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'results': []})
        
        results = search_stock_api(query)
        
        # Add price information to each result
        for result in results:
            price_data = get_stock_price(result['symbol'])
            if price_data:
                result['price'] = price_data
        
        return jsonify({'results': results})

    @app.route('/portfolio/allocation/edit/<asset_id>', methods=['GET', 'POST'])
    @login_required
    def edit_asset(asset_id):
        asset_doc = mongoClient.getCollectionEndpoint('Asset').find_one({"_id": ObjectId(asset_id)})
        if not asset_doc:
            abort(404)
        asset = deserializeDoc.asset(asset_doc)

        if asset.user_id != current_user._id:
            flash('Access denied.', 'error')
            return redirect(url_for('asset_allocation'))
        
        form = AssetForm()
        
        if form.validate_on_submit():
            # Auto-populate expected return and risk level if not provided or is 0
            if not form.expected_return.data or form.expected_return.data == 0:
                form.expected_return.data = get_enhanced_expected_return(
                    form.symbol.data
                )
            
            # Auto-populate risk level if not provided
            if not form.risk_level.data:
                form.risk_level.data = get_enhanced_risk_level(
                    form.symbol.data
                )
            
            # Check weight constraints
            assets = list(mongoClient.getConnectionEndpoint('Asset').find({"user_id":current_user._id}))
            for i in range(len(assets)):
                assets[i] = deserializeDoc.asset(assets[i])

            existing_weight = sum(a.weight for a in assets)

            if existing_weight + form.weight.data > 100:
                flash('Total portfolio weight cannot exceed 100%. Current total: {:.1f}%'.format(existing_weight), 'error')
                return render_template('edit_asset.html', form=form, asset=asset)
            
            asset.symbol = form.symbol.data.upper()
            asset.name = form.name.data
            asset.asset_type = form.asset_type.data
            asset.expected_return = form.expected_return.data
            asset.weight = form.weight.data
            asset.risk_level = form.risk_level.data
            asset.updated_at = datetime.now()

            mongoClient.getCollectionEndpoint('Asset').update_one(
                {"_id":ObjectId(asset_id)},
                {"$set": {
                    "symbol" : asset.symbol,
                    "name" : asset.name,
                    "asset_type" : asset.asset_type,
                    "expected_return" : asset.expected_return,
                    "weight" : asset.weight,
                    "risk_level" : asset.risk_level,
                    "updated_at" : asset.updated_at
                }}
            )
            
            flash('Asset updated successfully!', 'success')
            return redirect(url_for('asset_allocation'))
        
        elif request.method == 'GET':
            form.symbol.data = asset.symbol
            form.name.data = asset.name
            form.asset_type.data = asset.asset_type
            form.expected_return.data = asset.expected_return
            form.weight.data = asset.weight
            form.risk_level.data = asset.risk_level
        
        return render_template('edit_asset.html', form=form, asset=asset)

    @app.route('/portfolio/allocation/delete/<asset_id>', methods=['POST'])
    @login_required
    def delete_asset(asset_id):
        asset_doc = mongoClient.getCollectionEndpoint('Asset').find_one({"_id": ObjectId(asset_id)})
        if not asset_doc:
            abort(404)
        asset = deserializeDoc.asset(asset_doc)

        if asset.user_id != current_user._id:
            flash('Access denied.', 'error')
            return redirect(url_for('asset_allocation'))
        
        mongoClient.getConnectionEndpoint('Asset').delete_one({"_id" : ObjectId(asset_id)})
        flash('Asset deleted successfully!', 'success')
        return redirect(url_for('asset_allocation'))

    # Retirement Plans Management
    @app.route('/portfolio/retirement/plans')
    @login_required
    def retirement_plans():
        """Manage retirement plans"""
        plans = mongoClient.getCollectionEndpoint("RetirementPlan").find({"user_id":current_user._id})
        for i in range(len(plans)):
            plans[i] = deserializeDoc.retirement_plan(plans[i])

        return render_template('retirement_plans.html', plans=plans)

    @app.route('/portfolio/retirement/plans/add', methods=['GET', 'POST'])
    @login_required
    def add_retirement_plan():
        form = RetirementPlanForm()
        if form.validate_on_submit():
            plan = RetirementPlan(
                user_id=current_user._id,
                name=form.name.data,
                target_amount=form.target_amount.data,
                years_to_retirement=form.years_to_retirement.data,
                expected_return_rate=form.expected_return_rate.data,
                monthly_contribution_needed=form.monthly_contribution.data,
                projected_amount=0  # Will be calculated based on current savings and returns
            )
            mongoClient.getConnectionEndpoint('RetirementPlan').insert_one(vars(plan))
            flash('Retirement plan added successfully!', 'success')
            return redirect(url_for('retirement_plans'))
        
        return render_template('add_retirement_plan.html', form=form)

    @app.route('/portfolio/retirement/plans/delete/<plan_id>', methods=['POST'])
    @login_required
    def delete_retirement_plan(plan_id):
        plan_doc = mongoClient.getCollectionEndpoint('RetirementPlan').find_one({"_id": ObjectId(plan_id)})
        if not plan_doc:
            abort(404)
        plan = deserializeDoc.retirement_plan(plan_doc)

        if plan.user_id != current_user._id:
            flash('Access denied.', 'error')
            return redirect(url_for('retirement_plans'))
        
        mongoClient.getConnectionEndpoint('RetirementPlan').delete_one({"_id" : ObjectId(plan_id)})
        flash('Retirement plan deleted successfully!', 'success')
        return redirect(url_for('retirement_plans'))

    # Automated Retirement Planning
    @app.route('/portfolio/retirement/automated', methods=['GET', 'POST'])
    @login_required
    def automated_retirement_onboarding():
        """Automated retirement planning based on industry best practices"""
        form = AutomatedRetirementForm()
        
        if form.validate_on_submit():
            # Create or update retirement profile
            profile_doc = mongoClient.getCollectionEndpoint('UserProfile').find_one()
            profile = deserializeDoc.user_profile(profile_doc)
            if not profile:
                profile = UserProfile(user_id=current_user._id)
                mongoClient.getCollectionEndpoint('UserProfile').insert_one(vars(profile))
            
            # Auto-calculate retirement parameters based on industry standards
            current_age = form.current_age.data
            current_income = form.current_income.data
            current_savings = form.current_savings.data
            risk_tolerance = form.risk_tolerance.data
            
            # Calculate retirement age (industry standard: 65, but can be adjusted)
            retirement_age = 65
            if risk_tolerance == 'Conservative':
                retirement_age = 67
            elif risk_tolerance == 'Aggressive':
                retirement_age = 62
            
            # Calculate target retirement income (80% of current income rule)
            target_income = current_income * 0.8
            
            # Calculate target retirement amount (4% rule)
            target_amount = target_income * 25  # 4% rule: 25x annual expenses
            
            # Calculate expected return based on risk tolerance
            expected_return = {
                'Conservative': 5.0,
                'Moderate': 7.0,
                'Aggressive': 9.0
            }.get(risk_tolerance, 7.0)
            
            # Calculate years to retirement
            years_to_retirement = retirement_age - current_age
            
            # Calculate required monthly savings
            if years_to_retirement > 0:
                # Future value calculation
                future_value = target_amount
                present_value = current_savings
                rate = expected_return / 100
                n = years_to_retirement * 12  # monthly periods
                
                # Monthly payment formula: PMT = (FV - PV*(1+r)^n) / (((1+r)^n - 1) / r)
                if rate > 0:
                    monthly_savings = (future_value - present_value * (1 + rate/12)**n) / (((1 + rate/12)**n - 1) / (rate/12))
                else:
                    monthly_savings = (future_value - present_value) / n
            else:
                monthly_savings = 0
            
            # Update profile
            profile.age = current_age
            profile.retirement_age = retirement_age
            profile.current_salary = current_income
            profile.expected_retirement_income = target_income
            profile.current_savings = current_savings

            mongoClient.getCollectionEndpoint('UserProfile').update_one(
                {"_id" : profile._id},
                {"$set": {
                    'age' : profile.age,
                    'retirement_age' : profile.retirement_age,
                    'current_salary' : profile.current_salary,
                    'expected_retirement_income' : profile.expected_retirement_income,
                    'current_savings' : profile.current_savings,
                }}
            )
            
            # Create automated retirement plan
            plan = RetirementPlan(
                user_id=current_user._id,
                name=f"Automated {risk_tolerance} Plan",
                target_amount=target_amount,
                years_to_retirement=years_to_retirement,
                expected_return_rate=expected_return,
                monthly_contribution_needed=monthly_savings,
                projected_amount=current_savings * (1 + expected_return/100)**years_to_retirement
            )
            
            mongoClient.getCollectionEndpoint('RetirementPlan').insert_one(vars(plan))

            flash(f'Automated retirement plan created! Target: ${target_amount:,.0f}, Monthly savings: ${monthly_savings:,.0f}', 'success')
            return redirect(url_for('retirement_planning'))
        
        return render_template('automated_retirement.html', form=form)

    # Retirement Calculator
    @app.route('/portfolio/retirement/calculator', methods=['GET', 'POST'])
    @login_required
    def retirement_calculator():
        """Multi-scenario retirement calculator"""
        try:
            form = RetirementCalculatorForm()
            
            if form.validate_on_submit():
                # Calculate multiple scenarios
                scenarios = []
                
                # Conservative scenario
                conservative = {
                    'name': 'Conservative',
                    'expected_return': 5.0,
                    'risk_level': 'Low',
                    'monthly_savings': calculate_monthly_savings(
                        form.target_amount.data,
                        form.current_savings.data,
                        form.years_to_retirement.data,
                        5.0
                    ),
                    'retirement_age': 65,
                    'years_to_retirement': form.years_to_retirement.data,
                    'target_amount': form.target_amount.data,
                    'retirement_income': form.target_amount.data * 0.04,  # 4% withdrawal rule
                    'monthly_contribution_needed': calculate_monthly_savings(
                        form.target_amount.data,
                        form.current_savings.data,
                        form.years_to_retirement.data,
                        5.0
                    ),
                    'description': 'Lower risk approach with conservative returns'
                }
                scenarios.append(conservative)
                
                # Moderate scenario
                moderate = {
                    'name': 'Moderate',
                    'expected_return': 7.0,
                    'risk_level': 'Medium',
                    'monthly_savings': calculate_monthly_savings(
                        form.target_amount.data,
                        form.current_savings.data,
                        form.years_to_retirement.data,
                        7.0
                    ),
                    'retirement_age': 65,
                    'years_to_retirement': form.years_to_retirement.data,
                    'target_amount': form.target_amount.data,
                    'retirement_income': form.target_amount.data * 0.04,  # 4% withdrawal rule
                    'monthly_contribution_needed': calculate_monthly_savings(
                        form.target_amount.data,
                        form.current_savings.data,
                        form.years_to_retirement.data,
                        7.0
                    ),
                    'description': 'Balanced approach with moderate risk and returns'
                }
                scenarios.append(moderate)
                
                # Aggressive scenario
                aggressive = {
                    'name': 'Aggressive',
                    'expected_return': 9.0,
                    'risk_level': 'High',
                    'monthly_savings': calculate_monthly_savings(
                        form.target_amount.data,
                        form.current_savings.data,
                        form.years_to_retirement.data,
                        9.0
                    ),
                    'retirement_age': 65,
                    'years_to_retirement': form.years_to_retirement.data,
                    'target_amount': form.target_amount.data,
                    'retirement_income': form.target_amount.data * 0.04,  # 4% withdrawal rule
                    'monthly_contribution_needed': calculate_monthly_savings(
                        form.target_amount.data,
                        form.current_savings.data,
                        form.years_to_retirement.data,
                        9.0
                    ),
                    'description': 'Higher risk approach with potential for higher returns'
                }
                scenarios.append(aggressive)
                
                # Custom scenario
                custom = {
                    'name': 'Custom',
                    'expected_return': form.expected_return.data,
                    'risk_level': 'Custom',
                    'monthly_savings': calculate_monthly_savings(
                        form.target_amount.data,
                        form.current_savings.data,
                        form.years_to_retirement.data,
                        form.expected_return.data
                    ),
                    'retirement_age': 65,
                    'years_to_retirement': form.years_to_retirement.data,
                    'target_amount': form.target_amount.data,
                    'retirement_income': form.target_amount.data * 0.04,  # 4% withdrawal rule
                    'monthly_contribution_needed': calculate_monthly_savings(
                        form.target_amount.data,
                        form.current_savings.data,
                        form.years_to_retirement.data,
                        form.expected_return.data
                    ),
                    'description': 'Custom scenario based on your input parameters'
                }
                scenarios.append(custom)
                
                return render_template('retirement_calculator.html', 
                                     form=form, 
                                     scenarios=scenarios,
                                     show_results=True)
            
            return render_template('retirement_calculator.html', form=form)
        except Exception as e:
            print(f"Error in retirement_calculator: {e}")
            flash(f'An error occurred: {str(e)}', 'error')
            return render_template('retirement_calculator.html', form=form)

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

    def summarize_user_financial_context():
        """Summarize the user's current financial situation for AI context"""
        # Get user's data
        budgets = list(mongoClient.getCollectionEndpoint('Budget').find({"user_id":current_user._id}))
        for i in range(0, len(budgets)):
            budgets[i] = deserializeDoc.budget(budgets[i])
        # budgets = Budget.query.filter_by(user_id=current_user.id).all()
        expenses = list(mongoClient.getCollectionEndpoint('Expense').find({"user_id":current_user._id}))
        for i in range(0, len(budgets)):
            expenses[i] = deserializeDoc.expense(expenses[i])
        # expenses = Expense.query.filter_by(user_id=current_user.id).all()
        investments = list(mongoClient.getCollectionEndpoint('Investment').find({"user_id":current_user._id}))
        for i in range(0, len(investments)):
            investments[i] = deserializeDoc.investment(investments[i])
        # investments = Investment.query.filter_by(user_id=current_user.id).all()
        goals = list(mongoClient.getCollectionEndpoint('Goal').find({"user_id":current_user._id}))
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

    @app.route('/')
    @login_required
    def dashboard():
        # Always ensure currency and rate are set
        if 'currency' not in session:
            session['currency'] = 'USD'
        if 'exchange_rate' not in session:
            session['exchange_rate'] = 1.0
        if 'currency_rate' not in session:
            session['currency_rate'] = 1.0
        
        # Get user's data
        budgets = list(mongoClient.getCollectionEndpoint('Budget').find({"user_id":current_user._id}))
        for i in range(0, len(budgets)):
            budgets[i] = deserializeDoc.budget(budgets[i])
        # budgets = Budget.query.filter_by(user_id=current_user.id).all()
        expenses = list(mongoClient.getCollectionEndpoint('Expense').find({"user_id":current_user._id}))
        for i in range(0, len(budgets)):
            expenses[i] = deserializeDoc.expense(expenses[i])
        # expenses = Expense.query.filter_by(user_id=current_user.id).all()
        investments = list(mongoClient.getCollectionEndpoint('Investment').find({"user_id":current_user._id}))
        for i in range(0, len(investments)):
            investments[i] = deserializeDoc.investment(investments[i])
        # investments = Investment.query.filter_by(user_id=current_user.id).all()
        goals = list(mongoClient.getCollectionEndpoint('Goal').find({"user_id":current_user._id}))
        for i in range(0, len(goals)):
            goals[i] = deserializeDoc.goal(goals[i])
        # goals = Goal.query.filter_by(user_id=current_user.id).all()
        
        print(f"DEBUG: Dashboard - User {current_user._id} has {len(budgets)} budgets, {len(expenses)} expenses, {len(investments)} investments, {len(goals)} goals")
        
        # Calculate totals
        total_budget = sum(b.limit_amount for b in budgets)
        total_expenses = sum(e.converted_amount_usd for e in expenses)
        total_investments = sum(i.shares * i.purchase_price for i in investments)
        total_goals = sum(g.target_amount for g in goals)
        
        # Calculate data for dashboard
        data = {
            'total_budget': total_budget,
            'total_spent': total_expenses,
            'income': session.get('monthly_income', 0),  # Get income from session
            'categories': []
        }
        
        # Calculate categories from budgets
        for budget in budgets:
            spent = sum(e.converted_amount_usd for e in expenses if e.category == budget.category)
            data['categories'].append({
                'name': budget.category,
                'budget': budget.limit_amount,
                'spent': spent
            })
        
        # If no budgets exist, create categories from expenses
        if not data['categories'] and expenses:
            # Group expenses by category
            category_totals = {}
            for expense in expenses:
                category = expense.category
                if category not in category_totals:
                    category_totals[category] = 0
                category_totals[category] += expense.converted_amount_usd
            
            # Create category data from expenses
            for category, spent in category_totals.items():
                data['categories'].append({
                    'name': category,
                    'budget': spent,  # Use spent amount as budget for now
                    'spent': spent
                })
        
        # Generate weekly spending data for the chart
        if expenses:
            # Group expenses by week
            weekly_spending = [0, 0, 0, 0]  # 4 weeks
            for expense in expenses:
                # Calculate which week this expense belongs to (simple logic)
                week_index = min(3, int((expense.date.day - 1) / 7))
                weekly_spending[week_index] += expense.converted_amount_usd
            
            data['weekly_spending'] = weekly_spending
        else:
            data['weekly_spending'] = [0, 0, 0, 0]
        
        # Set budget for chart (use income if available, otherwise use total spent)
        if data['income'] > 0:
            data['chart_budget'] = data['income']
        elif total_budget > 0:
            data['chart_budget'] = total_budget
        else:
            data['chart_budget'] = total_expenses if total_expenses > 0 else 1000  # Default
        
        # Get recent expenses (last 5)
        recent_expenses = expenses[-5:] if expenses else []
        
        # Calculate investments snapshot with real-time prices
        investments_snapshot = []
        for inv in investments:
            # Get current price from API
            price_data = get_stock_price(inv.symbol)
            if price_data and 'current_price' in price_data:
                current_price = price_data['current_price']
                current_value = inv.shares * current_price
                gain = current_value - (inv.shares * inv.purchase_price)
            else:
                # Fallback to purchase price if API fails
                current_price = inv.purchase_price
                current_value = inv.shares * inv.purchase_price
                gain = 0
            
            investments_snapshot.append({
                'symbol': inv.symbol,
                'shares': inv.shares,
                'purchase_price': inv.purchase_price,
                'current_price': current_price,
                'value': current_value,
                'gain': gain,
                'purchase_date': inv.purchase_date.strftime('%Y-%m-%d')
            })
        
        return render_template('dashboard.html',
                             data=data,
                             budgets=budgets,
                             expenses=recent_expenses,
                             recent_expenses=recent_expenses,
                             investments=investments_snapshot,
                             investments_snapshot=investments_snapshot,
                             goals=goals,
                             currency=session.get('currency', 'USD'),
                             currency_symbol=get_currency_symbol(session.get('currency', 'USD')),
                             exchange_rate=session.get('exchange_rate', 1.0),
                             currency_list=CURRENCY_LIST,
                             get_currency_symbol=get_currency_symbol,
                             now=datetime.now())

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user_doc = mongoClient.getCollectionEndpoint('User').find_one({'username':form.username.data})
            user = deserializeDoc.user(user_doc)
            if user and user.check_password(form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                print("Logging in user:", user.username, " Authenticated?", user.is_authenticated)
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                if not user:
                    flash('Username not found. Please check your username or create a new account.', 'error')
                else:
                    flash('Incorrect password. Please try again.', 'error')
        


        return render_template('login.html', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = RegistrationForm(mongoClient, request.form)
        if form.validate_on_submit():
            # Check if username already exists
            user_doc = mongoClient.getCollectionEndpoint('User').find_one({'username':form.username.data})
            existing_user = deserializeDoc.user(user_doc)

            if existing_user:
                flash('Username already exists. Please choose a different username.', 'error')
                return render_template('register.html', form=form)
            
            # Check if email already exists
            user_doc = mongoClient.getCollectionEndpoint('User').find_one({'email':form.email.data})
            existing_email = deserializeDoc.user(user_doc)

            if existing_email:
                flash('Email already registered. Please use a different email or try logging in.', 'error')
                return render_template('register.html', form=form)
            
            try:
                user = User(
                    username=form.username.data,
                    email=form.email.data
                )
                user.set_password(form.password.data)

                mongoClient.getCollectionEndpoint('User').insert_one(vars(user))

                flash('Registration successful! Please log in with your new account.', 'login_success')
                return redirect(url_for('login'))
            except Exception as e:
                flash('Registration failed. Please try again.', 'error')
        
        return render_template('register.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/budget', methods=['GET', 'POST'])
    @login_required
    def budget():
        form = BudgetForm()
        if form.validate_on_submit():
            budget = Budget(
                user_id=current_user._id,
                category=form.category.data,
                limit_amount=form.limit_amount.data,
                month=form.month.data,
                year=int(form.year.data)
            )
            mongoClient.getCollectionEndpoint('Budget').insert_one(vars(budget))

            flash('Budget added successfully!', 'success')
            return redirect(url_for('budget'))
        
        budgets = list(mongoClient.getCollectionEndpoint('Budget').find({"user_id" : current_user._id}))
        for i in range(len(budgets)):
            budgets[i] = deserializeDoc.budget(budgets[i])

        return render_template('budget.html', form=form, budgets=budgets)

    @app.route('/edit_budget/<budget_id>', methods=['GET', 'POST'])
    @login_required
    def edit_budget(budget_id):
        budget_doc = mongoClient.getCollectionEndpoint('Budget').find_one({"_id": ObjectId(budget_id)})
        if not budget_doc:
            abort(404)
        budget = deserializeDoc.budget(budget_doc)

        if budget.user_id != current_user._id:
            flash('Access denied.', 'error')
            return redirect(url_for('budget'))
        
        form = BudgetForm()
        if form.validate_on_submit():
            budget.category = form.category.data
            budget.limit_amount = form.limit_amount.data
            budget.month = form.month.data
            budget.year = int(form.year.data)
            
            mongoClient.getCollectionEndpoint('Budget').update_one(
                { "_id" : ObjectId(budget_id) },
                { "$set" : {
                    "category" : budget.category,
                    "limit_amount" : budget.limit_amount,
                    "month" : budget.month,
                    "year" : budget.year,
                }}
            )

            flash('Budget updated successfully!', 'success')
            return redirect(url_for('budget'))
        elif request.method == 'GET':
            form.category.data = budget.category
            form.limit_amount.data = budget.limit_amount
            form.month.data = budget.month
            form.year.data = str(budget.year)
        
        return render_template('edit_budget.html', form=form, budget=budget)

    @app.route('/delete_budget/<budget_id>', methods=['POST'])
    @login_required
    def delete_budget(budget_id):
        budget_doc = mongoClient.getCollectionEndpoint('Budget').find_one({"_id": ObjectId(budget_id)})
        if not budget_doc:
            abort(404)
        budget = deserializeDoc.budget(budget_doc)

        if budget.user_id != current_user._id:
            flash('Access denied.', 'error')
            return redirect(url_for('budget'))
        
        mongoClient.getConnectionEndpoint('Budget').delete_one({"_id" : ObjectId(budget_id)})
        flash('Budget deleted successfully!', 'success')
        return redirect(url_for('budget'))

    @app.route('/expenses', methods=['GET', 'POST'])
    @login_required
    def expenses():
        form = ExpenseForm()
        
        # Get categories from existing budgets
        budgets = list(mongoClient.getConnectionEndpoint('Budget').find({"user_id":current_user._id}))
        for i in range(len(budgets)):
            budgets[i] = deserializeDoc.budget(budgets[i])

        categories = [budget.category for budget in budgets]
        form.category.choices = [(cat, cat) for cat in categories]
        
        if form.validate_on_submit():
            # Convert amount to USD
            amount_usd = form.amount.data
            if form.currency.data != 'USD':
                rate = fetch_exchange_rate(form.currency.data, 'USD')
                amount_usd = form.amount.data * rate
            
            expense = Expense(
                user_id=current_user._id,
                amount=form.amount.data,
                category=form.category.data,
                description=form.description.data,
                date=form.date.data,
                currency=form.currency.data,
                converted_amount_usd=amount_usd
            )
            mongoClient.getCollectionEndpoint('Expense').insert_one(vars(expense))
            flash('Expense added successfully!', 'success')
            return redirect(url_for('expenses'))
        

        expenses = list(mongoClient.getCollectionEndpoint('Expense').find({"user_id":current_user._id}).sort({"date" : -1}))
        for i in range(len(expenses)):
            expenses[i] = deserializeDoc.expense(expenses[i])

        return render_template('expenses.html', form=form, expenses=expenses)

    @app.route('/edit_expense/<expense_id>', methods=['GET', 'POST'])
    @login_required
    def edit_expense(expense_id):
        expense_doc = mongoClient.getCollectionEndpoint('Expense').find_one({"_id": ObjectId(expense_id)})
        if not expense_doc:
            abort(404)
        expense = deserializeDoc.expense(expense_doc)

        if expense.user_id != current_user._id:
            flash('Access denied.', 'error')
            return redirect(url_for('expenses'))
        
        form = ExpenseForm()
        
        # Get categories from existing budgets
        budgets = list(mongoClient.getConnectionEndpoint('Budget').find({"user_id":current_user._id}))
        for i in range(len(budgets)):
            budgets[i] = deserializeDoc.budget(budgets[i])

        categories = [budget.category for budget in budgets]
        form.category.choices = [(cat, cat) for cat in categories]
        
        if form.validate_on_submit():
            # Convert amount to USD
            amount_usd = form.amount.data
            if form.currency.data != 'USD':
                rate = fetch_exchange_rate(form.currency.data, 'USD')
                amount_usd = form.amount.data * rate
            
            expense.amount = form.amount.data
            expense.category = form.category.data
            expense.description = form.description.data
            expense.date = form.date.data
            expense.currency = form.currency.data
            expense.converted_amount_usd = amount_usd
            
            mongoClient.getCollectionEndpoint('Expense').update_one(
                {"_id": ObjectId(expense_id)},
                {"$set": {
                    "amount":expense.amount,
                    "category":expense.category,
                    "description":expense.description,
                    "date":expense.date,
                    "currency":expense.currency,
                    "converted_amount_usd":expense.converted_amount_usd
                }})

            flash('Expense updated successfully!', 'success')
            return redirect(url_for('expenses'))
        elif request.method == 'GET':
            form.amount.data = expense.amount
            form.category.data = expense.category
            form.description.data = expense.description
            form.date.data = expense.date
            form.currency.data = expense.currency
        
        return render_template('edit_expense.html', form=form, expense=expense)

    @app.route('/delete_expense/<expense_id>', methods=['POST'])
    @login_required
    def delete_expense(expense_id):
        expense_doc = mongoClient.getCollectionEndpoint('Expense').find_one({"_id": ObjectId(expense_id)})
        if not expense_doc:
            abort(404)
        expense = deserializeDoc.expense(expense_doc)

        if expense.user_id != current_user._id:
            flash('Access denied.', 'error')
            return redirect(url_for('expenses'))
        
        mongoClient.getConnectionEndpoint('Expense').delete_one({"_id" : ObjectId(expense_id)})
        flash('Expense deleted successfully!', 'success')
        return redirect(url_for('expenses'))

    @app.route('/goals')
    @login_required
    def goals():
        goals = list(mongoClient.getCollectionEndpoint('Goal').find({"user_id":current_user._id}))
        for i in range(len(goals)):
            goals[i] = deserializeDoc.goal(goals[i])

        return render_template('goals.html', goals=goals)

    @app.route('/goals/add', methods=['GET', 'POST'])
    @login_required
    def add_goal():
        form = GoalForm()
        if form.validate_on_submit():
            goal = Goal(
                user_id=current_user._id,
                name=form.name.data,
                target_amount=form.target_amount.data,
                current_amount=form.current_amount.data,
                target_date=form.target_date.data
            )
            mongoClient.getConnectionEndpoint('Goal').insert_one(vars(goal))
            flash('Goal added successfully!', 'success')
            return redirect(url_for('goals'))
        
        return render_template('add_goal.html', form=form)

    @app.route('/goals/edit/<goal_id>', methods=['GET', 'POST'])
    @login_required
    def edit_goal(goal_id):
        goal_doc = mongoClient.getCollectionEndpoint('Goal').find_one({"_id": ObjectId(goal_id)})
        if not goal_doc:
            abort(404)
        goal = deserializeDoc.goal(goal_doc)

        if goal.user_id != current_user._id:
            flash('Access denied.', 'error')
            return redirect(url_for('goals'))
        
        form = GoalForm()
        if form.validate_on_submit():
            goal.name = form.name.data
            goal.target_amount = form.target_amount.data
            goal.current_amount = form.current_amount.data
            goal.target_date = form.target_date.data
            
            mongoClient.getCollectionEndpoint('Goal').update_one(
                {"_id": ObjectId(goal_id)},
                {"$set": {
                    "name": goal.name,
                    "target_amount": goal.target_amount,
                    "current_amount": goal.current_amount,
                    "target_date": goal.target_date,
                }})
            
            flash('Goal updated successfully!', 'success')
            return redirect(url_for('goals'))
        elif request.method == 'GET':
            form.name.data = goal.name
            form.target_amount.data = goal.target_amount
            form.current_amount.data = goal.current_amount
            form.target_date.data = goal.target_date
        
        return render_template('edit_goal.html', form=form, goal=goal)

    @app.route('/goals/delete/<goal_id>', methods=['POST'])
    @login_required
    def delete_goal(goal_id):
        goal_doc = mongoClient.getCollectionEndpoint('Goal').find_one({"_id": ObjectId(goal_id)})
        if not goal_doc:
            abort(404)
        goal = deserializeDoc.goal(goal_doc)
        if goal.user_id != current_user._id:
            flash('Access denied.', 'error')
            return redirect(url_for('goals'))
        
        mongoClient.getConnectionEndpoint('Goal').delete_one({"_id" : ObjectId(goal_id)})
        flash('Goal deleted successfully!', 'success')
        return redirect(url_for('goals'))

    @app.route('/advice', methods=['GET', 'POST'])
    @login_required
    def advice():
        if request.method == 'POST':
            question = request.form.get('question', '')
            if question:
                try:
                    # Get comprehensive financial context
                    budget_context = summarize_user_financial_context()
                    
                    # Use Gemini API for financial advice
                    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
                    headers = {
                        "Content-Type": "application/json",
                        "x-goog-api-key": GEMINI_API_KEY
                    }
                    
                    system_prompt = (
                        f"{budget_context}\n\n"
                        "You are a helpful, concise, and practical financial budgeting assistant. "
                        "Give actionable, friendly, and specific advice for personal budgeting and money management. "
                        "If the user asks a general question, provide a budgeting tip. "
                        "If the user asks about their own budget, give tailored suggestions based on their financial data. "
                        "Always be encouraging and clear. "
                        "Format your response as a short, clear paragraph followed by 2-3 concise, actionable bullet points. "
                        "Use plain text, not markdown."
                    )
                    
                    data = {
                        "contents": [{"parts": [{"text": f"{system_prompt}\n\n{question}"}]}]
                    }
                    
                    response = requests.post(
                        url,
                        headers=headers,
                        json=data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        advice = result['candidates'][0]['content']['parts'][0]['text']
                        return render_template('advice.html', advice=advice, question=question)
                    else:
                        error = f"Error: {response.status_code}"
                        return render_template('advice.html', error=error, question=question)
                    
                except Exception as e:
                    error = f"Error connecting to Gemini API: {e}"
                    return render_template('advice.html', error=error, question=question)
        
        return render_template('advice.html')

    @app.route('/advice/chat', methods=['POST'])
    @login_required
    def advice_chat():
        data = request.get_json()
        question = data.get('question')
        if not question:
            return jsonify({'error': 'No question provided.'}), 400
        if not GEMINI_API_KEY:
            return jsonify({'error': 'Gemini API key not set.'}), 500
        
        try:
            # Get comprehensive financial context
            budget_context = summarize_user_financial_context()
            
            # Use Gemini API for financial advice
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            }
            
            system_prompt = (
                f"{budget_context}\n\n"
                "You are a helpful, concise, and practical financial budgeting assistant. "
                "Give actionable, friendly, and specific advice for personal budgeting and money management. "
                "If the user asks a general question, provide a budgeting tip. "
                "If the user asks about their own budget, give tailored suggestions based on their financial data. "
                "Always be encouraging and clear. "
                "Format your response as a short, clear paragraph followed by 2-3 concise, actionable bullet points. "
                "Use plain text, not markdown."
            )
            
            data = {
                "contents": [{"parts": [{"text": f"{system_prompt}\n\n{question}"}]}]
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['candidates'][0]['content']['parts'][0]['text']
                return jsonify({'ai_response': ai_response})
            else:
                return jsonify({'error': f'Gemini API error: {response.status_code}'}), 500
                
        except Exception as e:
            return jsonify({'error': f'Error connecting to Gemini API: {e}'}), 500

    @app.route('/onboarding', methods=['GET', 'POST'])
    @login_required
    def onboarding():
        message = None
        error = None
        ai_suggestion = None
        
        if request.method == 'GET':
            # Reset database on GET request (like original)
            pass  # We'll implement reset_db() later if needed
        
        if request.method == 'POST':
            income = request.form.get('income')
            rent = request.form.get('rent')
            bills = request.form.getlist('bills[]')
            bill_amounts = request.form.getlist('bill_amounts[]')
            goals = request.form.getlist('goals')
            
            # Compose bills string for AI
            bills_str = ", ".join([f"{name} (${amt})" for name, amt in zip(bills, bill_amounts) if name and amt]) if bills and bill_amounts else "None"
            
            # Compose AI prompt (exactly like original)
            if not GEMINI_API_KEY:
                error = "Gemini API key not set. Please set GEMINI_API_KEY in your .env file."
                return render_template('onboarding.html', message=message, error=error)
            
            prompt = (
                "Given the following financial goals: " + ", ".join(goals) + ". "
                f"The user's monthly after-tax income is ${income}. "
                f"Their rent/mortgage is ${rent} per month. "
                f"Their fixed monthly bills/expenses are: {bills_str}. "
                "Suggest a practical budget split (categories, percentages, and a short description for each) that best helps achieve these goals and covers their fixed expenses. "
                "Also suggest 2-3 specific savings goals (with target amounts and deadlines if possible) based on the user's info and goals. "
                "Return the result as a JSON object with two keys: 'budget_split' (a list of objects with 'name', 'percent', 'description') and 'savings_goals' (a list of objects with 'name', 'target_amount', 'deadline', 'description'). "
                "Percentages should sum to 100 and be rounded to the nearest integer."
            )
            
            conversation = [
                {"role": "user", "parts": [{"text": prompt}]}
            ]
            
            try:
                response = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": GEMINI_API_KEY
                    },
                    json={"contents": conversation},
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', None)
                    
                    if answer:
                        # Try to extract JSON from the response
                        start = answer.find('{')
                        end = answer.rfind('}')
                        if start != -1 and end != -1:
                            json_str = answer[start:end+1]
                            try:
                                ai_suggestion = json.loads(json_str)
                            except Exception:
                                ai_suggestion = None
                    
                    if not ai_suggestion:
                        error = "Could not parse AI suggestion. Please try again."
                        return render_template('onboarding.html', message=message, error=error)
                    
                    # Show confirmation page with AI suggestion (exactly like original)
                    return render_template('onboarding_confirm.html', 
                                         income=income, 
                                         rent=rent, 
                                         bills=zip(bills, bill_amounts), 
                                         goals=goals, 
                                         ai_suggestion=ai_suggestion)
                else:
                    error = f"Gemini API error: {response.status_code}"
                    return render_template('onboarding.html', message=message, error=error)
                    
            except Exception as e:
                error = f"Error connecting to Gemini API: {e}"
                return render_template('onboarding.html', message=message, error=error)
        
        return render_template('onboarding.html', message=message, error=error)

    @app.route('/test-onboarding')
    def test_onboarding():
        return "Onboarding route is working!"
    
    @app.route('/onboarding/confirm', methods=['POST'])
    def onboarding_confirm():
        income = request.form.get('income')
        rent = request.form.get('rent')
        bills = request.form.getlist('bills[]')
        bill_amounts = request.form.getlist('bill_amounts[]')
        goals = request.form.getlist('goals')
        budget_names = request.form.getlist('budget_name[]')
        budget_percents = request.form.getlist('budget_percent[]')
        # budget_descs = request.form.getlist('budget_desc[]')  # Not used for DB
        goal_names = request.form.getlist('goal_name[]')
        goal_targets = request.form.getlist('goal_target[]')
        goal_deadlines = request.form.getlist('goal_deadline[]')
        # goal_descs = request.form.getlist('goal_desc[]')  # Not used for DB
        
        # Get current user
        user = current_user
        
        # Save income (we'll add this to a new Income model later)
        # For now, we'll store it in session
        session['monthly_income'] = float(income) if income else 0
        
        # Only add AI-suggested budget split as categories (proportional to income)
        if income and budget_names and budget_percents:
            for name, percent in zip(budget_names, budget_percents):
                if name and percent:
                    limit = float(income) * float(percent) / 100.0
                    budget = Budget(
                        user_id=user._id,
                        category=name,
                        limit_amount=limit,
                        month=datetime.now().strftime('%B'),
                        year=datetime.now().year
                    )
                    mongoClient.getCollectionEndpoint("Budget").insertOne(vars(budget))
        
        # Save AI-suggested savings goals
        if goal_names and goal_targets:
            for name, target, deadline in zip(goal_names, goal_targets, goal_deadlines):
                if name and target:
                    # Handle empty or invalid deadline
                    target_date = None
                    if deadline and deadline.strip():
                        try:
                            target_date = datetime.strptime(deadline, '%Y-%m-%d').date()
                        except ValueError:
                            target_date = None
                    
                    goal = Goal(
                        user_id=user._id,
                        name=name,
                        target_amount=float(target),
                        current_amount=0,
                        target_date=target_date
                    )
                    mongoClient.getCollectionEndpoint("Goal").insertOne(vars(goal))
        
        try:
            flash('Welcome! Your personalized budget has been set up.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash('An error occurred while setting up your budget.', 'error')
            return redirect(url_for('dashboard'))
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500

# Create the app instance
app = create_app('production' if os.environ.get('DATABASE_URL') else 'default')

if __name__ == '__main__':
    app.run(debug=True)