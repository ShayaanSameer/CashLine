from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from datetime import datetime, date
from dotenv import load_dotenv
import requests
import json
from functools import lru_cache
import re

from config import config
from models import db, User, Budget, Expense, Investment, Goal
from forms import LoginForm, RegistrationForm, BudgetForm, ExpenseForm, InvestmentForm, GoalForm

# Load environment variables
load_dotenv()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # Register routes
    register_routes(app)
    
    return app

def register_routes(app):
    # Load environment variables
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
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
        budgets = Budget.query.filter_by(user_id=current_user.id).all()
        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        investments = Investment.query.filter_by(user_id=current_user.id).all()
        goals = Goal.query.filter_by(user_id=current_user.id).all()
        
        print(f"DEBUG: Dashboard - User {current_user.id} has {len(budgets)} budgets, {len(expenses)} expenses, {len(investments)} investments, {len(goals)} goals")
        
        # Calculate totals
        total_budget = sum(b.limit_amount for b in budgets)
        total_expenses = sum(e.converted_amount_usd for e in expenses)
        total_investments = sum(i.shares * i.purchase_price for i in investments)
        total_goals = sum(g.target_amount for g in goals)
        
        # Calculate data for dashboard
        data = {
            'total_budget': total_budget,
            'total_spent': total_expenses,
            'income': 0,  # We can add income tracking later
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
        
        # Get recent expenses (last 5)
        recent_expenses = expenses[-5:] if expenses else []
        
        # Calculate investments snapshot
        investments_snapshot = []
        for inv in investments:
            investments_snapshot.append({
                'symbol': inv.symbol,
                'shares': inv.shares,
                'purchase_price': inv.purchase_price,
                'current_price': inv.purchase_price,  # For now, use purchase price
                'value': inv.shares * inv.purchase_price,
                'gain': 0,
                'purchase_date': inv.purchase_date.strftime('%Y-%m-%d')
            })
        
        return render_template('dashboard.html',
                             data=data,
                             budgets=budgets,
                             expenses=expenses,
                             investments=investments,
                             goals=goals,
                             recent_expenses=recent_expenses,
                             investments_snapshot=investments_snapshot,
                             currency_list=CURRENCY_LIST,
                             get_currency_symbol=get_currency_symbol,
                             now=datetime.now())
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=True)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('login.html', form=form)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))
    
    @app.route('/budget', methods=['GET', 'POST'])
    @login_required
    def budget():
        form = BudgetForm()
        if form.validate_on_submit():
            print(f"DEBUG: Form submitted - Category: {form.category.data}, Amount: {form.limit_amount.data}")
            budget = Budget(
                user_id=current_user.id,
                category=form.category.data,
                limit_amount=form.limit_amount.data,
                month=form.month.data,
                year=form.year.data
            )
            db.session.add(budget)
            db.session.commit()
            print(f"DEBUG: Budget saved with ID: {budget.id}")
            flash('Budget added successfully!', 'success')
            return redirect(url_for('budget'))
        elif form.errors:
            print(f"DEBUG: Form errors: {form.errors}")
        
        budgets = Budget.query.filter_by(user_id=current_user.id).all()
        print(f"DEBUG: Found {len(budgets)} budgets for user {current_user.id}")
        return render_template('budget.html', form=form, budgets=budgets)
    
    @app.route('/edit_budget/<int:budget_id>', methods=['GET', 'POST'])
    @login_required
    def edit_budget(budget_id):
        budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
        form = BudgetForm(obj=budget)
        
        if form.validate_on_submit():
            budget.category = form.category.data
            budget.limit_amount = form.limit_amount.data
            budget.month = form.month.data
            budget.year = form.year.data
            db.session.commit()
            flash('Budget updated successfully!', 'success')
            return redirect(url_for('budget'))
        
        return render_template('edit_budget.html', form=form, budget=budget)
    
    @app.route('/delete_budget/<int:budget_id>', methods=['POST'])
    @login_required
    def delete_budget(budget_id):
        budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
        db.session.delete(budget)
        db.session.commit()
        flash('Budget deleted successfully!', 'success')
        return redirect(url_for('budget'))
    
    @app.route('/expenses', methods=['GET', 'POST'])
    @login_required
    def expenses():
        form = ExpenseForm()
        
        # Get user's budget categories for dropdown
        user_budgets = Budget.query.filter_by(user_id=current_user.id).all()
        category_choices = [(budget.category, budget.category) for budget in user_budgets]
        
        # Add a default option if no budgets exist
        if not category_choices:
            category_choices = [('Other', 'Other')]
        
        form.category.choices = category_choices
        
        if form.validate_on_submit():
            # Convert to USD if needed
            amount_usd = form.amount.data
            if form.currency.data != 'USD':
                rate = fetch_exchange_rate(form.currency.data, 'USD')
                amount_usd = form.amount.data * rate
            
            expense = Expense(
                user_id=current_user.id,
                amount=form.amount.data,
                category=form.category.data,
                description=form.description.data,
                date=form.date.data,
                currency=form.currency.data,
                converted_amount_usd=amount_usd
            )
            db.session.add(expense)
            db.session.commit()
            flash('Expense added successfully!', 'success')
            return redirect(url_for('expenses'))
        
        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        return render_template('expenses.html', form=form, expenses=expenses)
    
    @app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
    @login_required
    def edit_expense(expense_id):
        expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
        form = ExpenseForm(obj=expense)
        
        # Get user's budget categories for dropdown
        user_budgets = Budget.query.filter_by(user_id=current_user.id).all()
        category_choices = [(budget.category, budget.category) for budget in user_budgets]
        
        # Add a default option if no budgets exist
        if not category_choices:
            category_choices = [('Other', 'Other')]
        
        form.category.choices = category_choices
        
        if form.validate_on_submit():
            # Convert to USD if needed
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
            db.session.commit()
            flash('Expense updated successfully!', 'success')
            return redirect(url_for('expenses'))
        
        return render_template('edit_expense.html', form=form, expense=expense)
    
    @app.route('/delete_expense/<int:expense_id>', methods=['POST'])
    @login_required
    def delete_expense(expense_id):
        expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
        return redirect(url_for('expenses'))
    
    @app.route('/investments')
    @login_required
    def investments():
        investments = Investment.query.filter_by(user_id=current_user.id).all()
        return render_template('investments.html', investments=investments)
    
    @app.route('/investments/add', methods=['GET', 'POST'])
    @login_required
    def add_investment():
        form = InvestmentForm()
        if form.validate_on_submit():
            investment = Investment(
                user_id=current_user.id,
                symbol=form.symbol.data.upper(),
                shares=form.shares.data,
                purchase_price=form.purchase_price.data,
                purchase_date=form.purchase_date.data
            )
            db.session.add(investment)
            db.session.commit()
            flash('Investment added successfully!', 'success')
            return redirect(url_for('investments'))
        
        return render_template('add_investment.html', form=form)
    
    @app.route('/investments/edit/<int:investment_id>', methods=['GET', 'POST'])
    @login_required
    def edit_investment(investment_id):
        investment = Investment.query.filter_by(id=investment_id, user_id=current_user.id).first_or_404()
        form = InvestmentForm(obj=investment)
        
        if form.validate_on_submit():
            investment.symbol = form.symbol.data.upper()
            investment.shares = form.shares.data
            investment.purchase_price = form.purchase_price.data
            investment.purchase_date = form.purchase_date.data
            db.session.commit()
            flash('Investment updated successfully!', 'success')
            return redirect(url_for('investments'))
        
        return render_template('edit_investment.html', form=form, investment=investment)
    
    @app.route('/investments/delete/<int:investment_id>', methods=['POST'])
    @login_required
    def delete_investment(investment_id):
        investment = Investment.query.filter_by(id=investment_id, user_id=current_user.id).first_or_404()
        db.session.delete(investment)
        db.session.commit()
        flash('Investment deleted successfully!', 'success')
        return redirect(url_for('investments'))
    
    @app.route('/goals')
    @login_required
    def goals():
        goals = Goal.query.filter_by(user_id=current_user.id).all()
        return render_template('goals.html', goals=goals)
    
    @app.route('/goals/add', methods=['GET', 'POST'])
    @login_required
    def add_goal():
        form = GoalForm()
        if form.validate_on_submit():
            print(f"DEBUG: Goal form submitted - Name: {form.name.data}, Target: {form.target_amount.data}")
            goal = Goal(
                user_id=current_user.id,
                name=form.name.data,
                target_amount=form.target_amount.data,
                current_amount=form.current_amount.data,
                target_date=form.target_date.data
            )
            db.session.add(goal)
            db.session.commit()
            print(f"DEBUG: Goal saved with ID: {goal.id}")
            flash('Goal added successfully!', 'success')
            return redirect(url_for('goals'))
        elif form.errors:
            print(f"DEBUG: Goal form errors: {form.errors}")
        
        return render_template('add_goal.html', form=form)
    
    @app.route('/goals/edit/<int:goal_id>', methods=['GET', 'POST'])
    @login_required
    def edit_goal(goal_id):
        goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
        form = GoalForm(obj=goal)
        
        if form.validate_on_submit():
            goal.name = form.name.data
            goal.target_amount = form.target_amount.data
            goal.current_amount = form.current_amount.data
            goal.target_date = form.target_date.data
            db.session.commit()
            flash('Goal updated successfully!', 'success')
            return redirect(url_for('goals'))
        
        return render_template('edit_goal.html', form=form, goal=goal)
    
    @app.route('/goals/delete/<int:goal_id>', methods=['POST'])
    @login_required
    def delete_goal(goal_id):
        goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
        db.session.delete(goal)
        db.session.commit()
        flash('Goal deleted successfully!', 'success')
        return redirect(url_for('goals'))
    
    @app.route('/advice', methods=['GET', 'POST'])
    @login_required
    def advice():
        if request.method == 'POST':
            question = request.form.get('question', '')
            if question:
                # Simple advice logic - you can enhance this
                advice_text = f"Based on your question: '{question}', here's some general financial advice..."
                return render_template('advice.html', advice=advice_text, question=question)
        
        return render_template('advice.html')
    
    @app.route('/onboarding', methods=['GET', 'POST'])
    @login_required
    def onboarding():
        print(f"DEBUG: Onboarding - User: {current_user.username if current_user.is_authenticated else 'Not authenticated'}")
        message = None
        error = None
        ai_suggestion = None
        
        if request.method == 'GET':
            # Don't reset the database as it will delete the current user
            # Just ensure tables exist
            with app.app_context():
                db.create_all()
        
        if request.method == 'POST':
            print(f"DEBUG: Onboarding POST - User: {current_user.username if current_user.is_authenticated else 'Not authenticated'}")
            income = request.form.get('income')
            rent = request.form.get('rent')
            bills = request.form.getlist('bills[]')
            bill_amounts = request.form.getlist('bill_amounts[]')
            goals = request.form.getlist('goals')
            
            # Compose bills string for AI
            bills_str = ", ".join([f"{name} (${amt})" for name, amt in zip(bills, bill_amounts) if name and amt]) if bills and bill_amounts else "None"
            
            # Compose AI prompt
            if not GEMINI_API_KEY:
                # Create a simple default budget without AI
                default_budget = {
                    'budget_split': [
                        {'name': 'Housing', 'percent': 30, 'description': 'Rent, mortgage, utilities'},
                        {'name': 'Food & Dining', 'percent': 15, 'description': 'Groceries, restaurants, takeout'},
                        {'name': 'Transportation', 'percent': 10, 'description': 'Gas, public transit, car maintenance'},
                        {'name': 'Entertainment', 'percent': 10, 'description': 'Movies, hobbies, social activities'},
                        {'name': 'Shopping', 'percent': 10, 'description': 'Clothes, personal items, gifts'},
                        {'name': 'Healthcare', 'percent': 5, 'description': 'Medical expenses, insurance'},
                        {'name': 'Savings', 'percent': 20, 'description': 'Emergency fund and long-term savings'}
                    ],
                    'savings_goals': [
                        {'name': 'Emergency Fund', 'target_amount': 5000, 'deadline': '2025-12-31', 'description': '3-6 months of expenses'},
                        {'name': 'Vacation Fund', 'target_amount': 3000, 'deadline': '2025-10-15', 'description': 'Next vacation savings'}
                    ]
                }
                return render_template('onboarding_confirm.html', 
                                    income=income, rent=rent, 
                                    bills=zip(bills, bill_amounts), 
                                    goals=goals, ai_suggestion=default_budget)
            
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
                    
                    # Show confirmation page with AI suggestion
                    return render_template('onboarding_confirm.html', 
                                        income=income, rent=rent, 
                                        bills=zip(bills, bill_amounts), 
                                        goals=goals, ai_suggestion=ai_suggestion)
                else:
                    error = f"Gemini API error: {response.status_code}"
                    return render_template('onboarding.html', message=message, error=error)
                    
            except Exception as e:
                error = f"Error connecting to Gemini API: {e}"
                return render_template('onboarding.html', message=message, error=error)
        
        return render_template('onboarding.html', message=message, error=error)

    @app.route('/onboarding/confirm', methods=['POST'])
    @login_required
    def onboarding_confirm():
        income = request.form.get('income')
        rent = request.form.get('rent')
        bills = request.form.getlist('bills[]')
        bill_amounts = request.form.getlist('bill_amounts[]')
        goals = request.form.getlist('goals')
        budget_names = request.form.getlist('budget_name[]')
        budget_percents = request.form.getlist('budget_percent[]')
        goal_names = request.form.getlist('goal_name[]')
        goal_targets = request.form.getlist('goal_target[]')
        goal_deadlines = request.form.getlist('goal_deadline[]')
        
        # Get current user
        user = current_user
        
        # Save income (we'll add this to a new Income model later)
        # For now, we'll store it in session
        session['monthly_income'] = float(income) if income else 0
        
        # Add AI-suggested budget categories
        if income and budget_names and budget_percents:
            for name, percent in zip(budget_names, budget_percents):
                if name and percent:
                    limit = float(income) * float(percent) / 100.0
                    budget = Budget(
                        user_id=user.id,
                        category=name,
                        limit_amount=limit,
                        month=datetime.now().strftime('%B'),
                        year=datetime.now().year
                    )
                    db.session.add(budget)
        
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
                        user_id=user.id,
                        name=name,
                        target_amount=float(target),
                        current_amount=0,
                        target_date=target_date
                    )
                    db.session.add(goal)
        
        try:
            db.session.commit()
            flash('Welcome! Your personalized budget has been set up.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            # If it's a schema issue, try to recreate the database
            if 'NOT NULL constraint failed: goal.target_date' in str(e):
                try:
                    from sqlalchemy import text
                    db.session.execute(text("DROP TABLE IF EXISTS goal"))
                    db.create_all()
                    # Retry the commit
                    db.session.commit()
                    flash('Welcome! Your personalized budget has been set up.', 'success')
                    return redirect(url_for('dashboard'))
                except Exception as retry_error:
                    flash('Database schema issue. Please contact support.', 'error')
                    return redirect(url_for('dashboard'))
            else:
                flash('An error occurred while setting up your budget.', 'error')
                return redirect(url_for('dashboard'))
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

# Create the app instance
app = create_app('production' if os.environ.get('DATABASE_URL') else 'default')

if __name__ == '__main__':
    app.run(debug=True)