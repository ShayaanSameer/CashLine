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
from app.operations import mongoDBClient, deserializeDoc, fetch_exchange_rate, get_stock_price, get_currency_symbol

main_bp = Blueprint("main", __name__)

@main_bp.route('/onboarding', methods=['GET', 'POST'], endpoint="onboarding")
@login_required
def onboarding():
    GEMINI_API_KEY = current_app.app["GEMINI_API_KEY"]
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

@main_bp.route('/test-onboarding', endpoint="test_onboarding")
def test_onboarding():
    return "Onboarding route is working!"

@main_bp.route('/onboarding/confirm', methods=['POST'], endpoint="onboarding_confirm")
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
                doc = vars(budget)
                doc.pop("_id", None)
                current_app.mongo.getCollectionEndpoint("Budget").insert_one(doc)
    
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
                doc = vars(goal)
                doc.pop("_id", None)
                current_app.mongo.getCollectionEndpoint("Goal").insert_one(doc)
    
    try:
        flash('Welcome! Your personalized budget has been set up.', 'success')
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        flash('An error occurred while setting up your budget.', 'error')
        return redirect(url_for('main.dashboard'))
    
@main_bp.route('/set_currency', methods=['POST', 'GET'], endpoint="set_currency")
def set_currency():
    code = request.values.get('currency', 'USD').upper()
    CURRENCY_LIST = [
        ('USD', '$'), ('EUR', '€'), ('GBP', '£'), ('INR', '₹'),
        ('CAD', 'C$'), ('AUD', 'A$'), ('JPY', '¥'), ('CNY', '¥'),
        ('CHF', 'Fr'), ('SGD', 'S$'), ('ZAR', 'R'),
    ]
    
    if code not in [c[0] for c in CURRENCY_LIST]:
        code = 'USD'
    session['currency'] = code
    rate = fetch_exchange_rate(code, 'USD', current_app.config["EXCHANGE_RATE_API_KEY"])
    session['exchange_rate'] = rate
    session['currency_rate'] = rate
    return redirect(request.referrer or url_for('main.dashboard'))
    
@main_bp.route('/', endpoint="dashboard")
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
    budgets = list(current_app.mongo.getCollectionEndpoint('Budget').find({"user_id":current_user._id}))
    for i in range(0, len(budgets)):
        budgets[i] = deserializeDoc.budget(budgets[i])
    # budgets = Budget.query.filter_by(user_id=current_user.id).all()
    expenses = list(current_app.mongo.getCollectionEndpoint('Expense').find({"user_id":current_user._id}))
    for i in range(0, len(expenses)):
        expenses[i] = deserializeDoc.expense(expenses[i])
    # expenses = Expense.query.filter_by(user_id=current_user.id).all()
    investments = list(current_app.mongo.getCollectionEndpoint('Investment').find({"user_id":current_user._id}))
    for i in range(0, len(investments)):
        investments[i] = deserializeDoc.investment(investments[i])
    # investments = Investment.query.filter_by(user_id=current_user.id).all()
    goals = list(current_app.mongo.getCollectionEndpoint('Goal').find({"user_id":current_user._id}))
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
        price_data = get_stock_price(inv.symbol, current_app.config["FINNHUB_API_KEY"])
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

    CURRENCY_LIST = [
        ('USD', '$'), ('EUR', '€'), ('GBP', '£'), ('INR', '₹'),
        ('CAD', 'C$'), ('AUD', 'A$'), ('JPY', '¥'), ('CNY', '¥'),
        ('CHF', 'Fr'), ('SGD', 'S$'), ('ZAR', 'R'),
    ]
    
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