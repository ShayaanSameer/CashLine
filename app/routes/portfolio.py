from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, abort, Blueprint, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import requests
import json
from functools import lru_cache
import re
from bson import ObjectId

from config import config
from app.forms import LoginForm, RegistrationForm, BudgetForm, ExpenseForm, InvestmentForm, GoalForm, UserProfileForm, AssetForm, RetirementPlanForm, AutomatedRetirementForm, RetirementProfileForm, RetirementCalculatorForm
from app.mongoModels import Investment, User, Budget, Expense, Goal, UserProfile, Asset, RetirementPlan
from app.operations import mongoDBClient, deserializeDoc
from app.operations import calculate_monthly_savings, search_stock_api, get_enhanced_expected_return, get_enhanced_risk_level, get_asset_categorization_from_finnhub, get_expected_return_for_asset, get_risk_level_for_asset, fetch_exchange_rate, get_stock_price

portfolio_bp = Blueprint("portfolio", __name__)

@portfolio_bp.route('/investments/retirement/assets/get_expected_return')
@login_required
def get_expected_return():
    """API endpoint to get expected return and risk level for asset type and symbol"""
    asset_type = request.args.get('asset_type', '')
    symbol = request.args.get('symbol', '')
    
    # Try to get enhanced data from Finnhub first
    if symbol:
        enhanced_return = get_enhanced_expected_return(symbol, current_app.config["FINNHUB_API_KEY"])
        enhanced_risk = get_enhanced_risk_level(symbol, current_app.config["FINNHUB_API_KEY"])
        enhanced_asset_type = get_asset_categorization_from_finnhub(symbol, current_app.config["FINNHUB_API_KEY"])
        
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

@portfolio_bp.route('/portfolio/allocation/get_expected_return')
@login_required
def get_allocation_expected_return():
    """API endpoint to get expected return and risk level for asset type and symbol"""
    asset_type = request.args.get('asset_type', '')
    symbol = request.args.get('symbol', '')
    
    # Try to get enhanced data from Finnhub first
    if symbol:
        enhanced_return = get_enhanced_expected_return(symbol, current_app.config["FINNHUB_API_KEY"])
        enhanced_risk = get_enhanced_risk_level(symbol, current_app.config["FINNHUB_API_KEY"])
        enhanced_asset_type = get_asset_categorization_from_finnhub(symbol, current_app.config["FINNHUB_API_KEY"])
        
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

# Unified Portfolio Management Routes
@portfolio_bp.route('/portfolio')
@login_required
def portfolio_overview():
    """Main portfolio dashboard - unified view of all investments and retirement planning"""
    # Get current investments
    current_investments = list(current_app.mongo.getCollectionEndpoint('Investment').find({"user_id":current_user._id}))
    for i in range(0, len(current_investments)):
        current_investments[i] = deserializeDoc.investment(current_investments[i])

    # Get retirement profile
    profile = deserializeDoc.user_profile(current_app.mongo.getCollectionEndpoint('UserProfile').find_one({"user_id":current_user._id}))
    
    # Get retirement assets (portfolio allocation)
    retirement_assets = list(current_app.mongo.getCollectionEndpoint('Asset').find({"user_id":current_user._id}))
    for i in range(0, len(retirement_assets)):
        retirement_assets[i] = deserializeDoc.asset(retirement_assets[i])

    # Get retirement plans
    retirement_plans = list(current_app.mongo.getCollectionEndpoint('RetirementPlan').find({"user_id":current_user._id}))
    for i in range(0, len(retirement_plans)):
        retirement_plans[i] = deserializeDoc.retirement_plan(retirement_plans[i])

    # Get real-time prices for current investments (limit to first 5 to avoid API limits)
    investment_prices = {}
    for investment in current_investments[:5]:
        price_data = get_stock_price(investment.symbol, current_app.config["FINNHUB_API_KEY"])
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
@portfolio_bp.route('/portfolio/holdings')
@login_required
def current_holdings():
    """Manage current investment holdings with real-time tracking"""
    investments = list(current_app.mongo.getCollectionEndpoint('Investment').find({"user_id":current_user._id}))
    for i in range(len(investments)):
        investments[i] = deserializeDoc.investment(investments[i])

    # Calculate portfolio summary values
    total_purchase_value = 0
    total_current_value = 0
    total_gain_loss = 0
    
    # Get real-time prices
    investment_prices = {}
    for investment in investments[:10]:  # Limit to avoid API rate limits
        price_data = get_stock_price(investment.symbol, current_app.config["FINNHUB_API_KEY"])
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

@portfolio_bp.route('/portfolio/holdings/add', methods=['GET', 'POST'])
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
        doc = vars(investment)
        doc.pop("_id", None)
        current_app.mongo.getCollectionEndpoint('Investment').insert_one(doc)
        flash('Investment added successfully!', 'success')
        return redirect(url_for('current_holdings'))
    
    return render_template('add_holding.html', form=form)

@portfolio_bp.route('/portfolio/holdings/edit/<investment_id>', methods=['GET', 'POST'])
@login_required
def edit_holding(investment_id):
    investment_doc = current_app.mongo.getCollectionEndpoint('Investment').find_one({"_id": ObjectId(investment_id)})
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
        investment.purchase_date = datetime.combine(form.purchase_date.data, datetime.min.time())
        investment.updated_at = datetime.now()
        
        current_app.mongo.getCollectionEndpoint('Investment').update_one(
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

@portfolio_bp.route('/portfolio/holdings/delete/<investment_id>', methods=['POST'])
@login_required
def delete_holding(investment_id):
    investment_doc = current_app.mongo.getCollectionEndpoint('Investment').find_one({"_id": ObjectId(investment_id)})
    if not investment_doc:
        abort(404)
    investment = deserializeDoc.investment(investment_doc)

    if investment.user_id != current_user._id:
        flash('Access denied.', 'error')
        return redirect(url_for('current_holdings'))
    
    current_app.mongo.getCollectionEndpoint('Investment').delete_one({"_id" : ObjectId(investment_id)})
    flash('Investment deleted successfully!', 'success')
    return redirect(url_for('current_holdings'))

# Retirement Planning
@portfolio_bp.route('/portfolio/retirement')
@login_required
def retirement_planning():
    """Retirement planning dashboard"""
    profile_doc = current_app.mongo.getCollectionEndpoint('UserProfile').find_one({"user_id":current_user._id})
    profile = deserializeDoc.user_profile(profile_doc)
    
    retirement_plans = list(current_app.mongo.getCollectionEndpoint('RetirementPlan').find({"user_id":current_user._id}))
    for i in range(len(retirement_plans)):
        retirement_plans[i] = deserializeDoc.retirement_plan(retirement_plans[i])

    retirement_assets = list(current_app.mongo.getCollectionEndpoint('Asset').find({"user_id":current_user._id}))
    for i in range(len(retirement_assets)):
        retirement_assets[i] = deserializeDoc.asset(retirement_assets[i])
    
    return render_template('retirement_planning.html',
                            profile=profile,
                            retirement_plans=retirement_plans,
                            retirement_assets=retirement_assets)

@portfolio_bp.route('/portfolio/retirement/profile', methods=['GET', 'POST'])
@login_required
def retirement_profile():
    """Manage retirement profile and goals"""
    profile_doc = current_app.mongo.getCollectionEndpoint('UserProfile').find_one({"user_id":current_user._id})
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
                ra=form.retirement_age.data,
                cs=form.current_income.data,
                eri=form.expected_retirement_income.data,
                csave=form.current_savings.data
            )
            docs = vars(profile)
            docs.pop("_id", None)
            current_app.mongo.getCollectionEndpoint('UserProfile').insert_one(docs)
        
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
@portfolio_bp.route('/portfolio/allocation')
@login_required
def asset_allocation():
    """Manage retirement portfolio asset allocation"""
    assets = list(current_app.mongo.getCollectionEndpoint('Asset').find({"user_id":current_user._id}))
    for i in range(len(assets)):
        assets[i] = deserializeDoc.asset(assets[i])
    
    # Calculate portfolio summary
    total_weight = sum(asset.weight for asset in assets)
    weighted_return = sum(asset.expected_return * asset.weight / 100 for asset in assets)
    
    return render_template('asset_allocation.html', assets=assets, total_weight=total_weight, weighted_return=weighted_return)

@portfolio_bp.route('/portfolio/allocation/add', methods=['GET', 'POST'])
@login_required
def add_asset():
    form = AssetForm()
    
    if form.validate_on_submit():
        # Auto-populate expected return and risk level if not provided or is 0
        if not form.expected_return.data or form.expected_return.data == 0:
            form.expected_return.data = get_enhanced_expected_return(form.symbol.data, current_app.config["FINNHUB_API_KEY"])
        
        # Auto-populate risk level if not provided
        if not form.risk_level.data:
            form.risk_level.data = get_enhanced_risk_level(form.symbol.data, current_app.config["FINNHUB_API_KEY"])
        
        # Check weight constraints
        assets = list(current_app.mongo.getCollectionEndpoint('Asset').find({"user_id":current_user._id}))
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

        doc = vars(asset)
        doc.pop("_id", None)
        current_app.mongo.getCollectionEndpoint('Asset').insert_one(doc)
        flash('Asset added successfully!', 'success')
        return redirect(url_for('asset_allocation'))
    
    return render_template('add_asset.html', form=form)

@portfolio_bp.route('/portfolio/allocation/search')
@login_required
def search_assets():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    results = search_stock_api(query, current_app.config["FINNHUB_API_KEY"])
    
    # Add price information to each result
    for result in results:
        price_data = get_stock_price(result['symbol'], current_app.config["FINNHUB_API_KEY"])
        if price_data:
            result['price'] = price_data
    
    return jsonify(results)

@portfolio_bp.route('/portfolio/holdings/search')
@login_required
def search_holdings():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': []})
    
    results = search_stock_api(query, current_app.config["FINNHUB_API_KEY"])
    
    # Add price information to each result
    for result in results:
        price_data = get_stock_price(result['symbol'], current_app.config["FINNHUB_API_KEY"])
        if price_data:
            result['price'] = price_data
    
    return jsonify({'results': results})

@portfolio_bp.route('/portfolio/allocation/edit/<asset_id>', methods=['GET', 'POST'])
@login_required
def edit_asset(asset_id):
    asset_doc = current_app.mongo.getCollectionEndpoint('Asset').find_one({"_id": ObjectId(asset_id)})
    if not asset_doc:
        abort(404)
    asset = deserializeDoc.asset(asset_doc)

    if asset.user_id != current_user._id:
        flash('Access denied.', 'error')
        return redirect(url_for('asset_allocation'))
    
    form = AssetForm()
    
    print("Form errors:", form.errors)
    if form.validate_on_submit():
        # Auto-populate expected return and risk level if not provided or is 0
        if not form.expected_return.data or form.expected_return.data == 0:
            form.expected_return.data = get_enhanced_expected_return(form.symbol.data, current_app.config["FINNHUB_API_KEY"])
        
        # Auto-populate risk level if not provided
        if not form.risk_level.data:
            form.risk_level.data = get_enhanced_risk_level(form.symbol.data, current_app.config["FINNHUB_API_KEY"])
        
        # Check weight constraints
        assets = list(current_app.mongo.getCollectionEndpoint('Asset').find({"user_id":current_user._id}))
        for i in range(len(assets)):
            assets[i] = deserializeDoc.asset(assets[i])

        existing_weight = sum(a.weight for a in assets) - asset.weight

        if existing_weight + form.weight.data > 100:
            print("hello123")
            flash('Total portfolio weight cannot exceed 100%. Current total: {:.1f}%'.format(existing_weight), 'error')
            return render_template('edit_asset.html', form=form, asset=asset)
        
        asset.symbol = form.symbol.data.upper()
        asset.name = form.name.data
        asset.asset_type = form.asset_type.data
        asset.expected_return = form.expected_return.data
        asset.weight = form.weight.data
        asset.risk_level = form.risk_level.data
        asset.updated_at = datetime.now()

        current_app.mongo.getCollectionEndpoint('Asset').update_one(
            {"_id": ObjectId(asset_id)},
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

@portfolio_bp.route('/portfolio/allocation/delete/<asset_id>', methods=['POST'])
@login_required
def delete_asset(asset_id):
    asset_doc = current_app.mongo.getCollectionEndpoint('Asset').find_one({"_id": ObjectId(asset_id)})
    if not asset_doc:
        abort(404)
    asset = deserializeDoc.asset(asset_doc)

    if asset.user_id != current_user._id:
        flash('Access denied.', 'error')
        return redirect(url_for('asset_allocation'))
    
    current_app.mongo.getCollectionEndpoint('Asset').delete_one({"_id" : ObjectId(asset_id)})
    flash('Asset deleted successfully!', 'success')
    return redirect(url_for('asset_allocation'))

# Retirement Plans Management
@portfolio_bp.route('/portfolio/retirement/plans')
@login_required
def retirement_plans():
    """Manage retirement plans"""
    plans = list(current_app.mongo.getCollectionEndpoint("RetirementPlan").find({"user_id":current_user._id}))

    for i in range(len(plans)):
        plans[i] = deserializeDoc.retirement_plan(plans[i])

    return render_template('retirement_plans.html', plans=plans)

@portfolio_bp.route('/portfolio/retirement/plans/add', methods=['GET', 'POST'])
@login_required
def add_retirement_plan():
    form = RetirementPlanForm()
    if form.validate_on_submit():
        plan = RetirementPlan(
            user_id=current_user._id,
            name=form.name.data,
            target_amount=form.target_amount.data,
            ytr=form.years_to_retirement.data,
            err=form.expected_return_rate.data,
            mcn=0,
            pa=0  # Will be calculated based on current savings and returns
        )
        docs = vars(plan)
        docs.pop("_id", None)
        current_app.mongo.getCollectionEndpoint('RetirementPlan').insert_one(docs)
        flash('Retirement plan added successfully!', 'success')
        return redirect(url_for('retirement_plans'))
    
    return render_template('add_retirement_plan.html', form=form)

@portfolio_bp.route('/portfolio/retirement/plans/delete/<plan_id>', methods=['POST'])
@login_required
def delete_retirement_plan(plan_id):
    plan_doc = current_app.mongo.getCollectionEndpoint('RetirementPlan').find_one({"_id": ObjectId(plan_id)})
    if not plan_doc:
        abort(404)
    plan = deserializeDoc.retirement_plan(plan_doc)

    if plan.user_id != current_user._id:
        flash('Access denied.', 'error')
        return redirect(url_for('retirement_plans'))
    
    current_app.mongo.getCollectionEndpoint('RetirementPlan').delete_one({"_id" : ObjectId(plan_id)})
    flash('Retirement plan deleted successfully!', 'success')
    return redirect(url_for('retirement_plans'))

# Automated Retirement Planning
@portfolio_bp.route('/portfolio/retirement/automated', methods=['GET', 'POST'])
@login_required
def automated_retirement_onboarding():
    """Automated retirement planning based on industry best practices"""
    form = AutomatedRetirementForm()
    
    if form.validate_on_submit():
        # Create or update retirement profile
        profile_doc = current_app.mongo.getCollectionEndpoint('UserProfile').find_one()
        profile = deserializeDoc.user_profile(profile_doc)
        if not profile:
            profile = UserProfile(user_id=current_user._id)
            current_app.mongo.getCollectionEndpoint('UserProfile').insert_one(vars(profile))
        
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

        current_app.mongo.getCollectionEndpoint('UserProfile').update_one(
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
            ytr=years_to_retirement,
            err=expected_return,
            mcn=monthly_savings,
            pa=current_savings * (1 + expected_return/100)**years_to_retirement
        )
        docs = vars(plan)
        docs.pop("_id", None)
        
        current_app.mongo.getCollectionEndpoint('RetirementPlan').insert_one(docs)

        flash(f'Automated retirement plan created! Target: ${target_amount:,.0f}, Monthly savings: ${monthly_savings:,.0f}', 'success')
        return redirect(url_for('retirement_planning'))
    
    return render_template('automated_retirement.html', form=form)

# Retirement Calculator
@portfolio_bp.route('/portfolio/retirement/calculator', methods=['GET', 'POST'])
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
