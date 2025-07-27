from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from datetime import datetime
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
        return User.query.get(int(user_id))
    
    # Register blueprints or routes here
    register_routes(app)
    
    return app

def register_routes(app):
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
            url = f"https://v6.exchangerate-api.com/v6/41f126546f9e601c9de74e2c/latest/{base}"
            resp = requests.get(url, timeout=5)
            data = resp.json()
            return data['conversion_rates'][target]
        except Exception:
            return 1.0
    
    @app.route('/set_currency', methods=['POST', 'GET'])
    def set_currency():
        code = request.values.get('currency', 'USD').upper()
        if code not in [c[0] for c in CURRENCY_LIST]:
            code = 'USD'
        session['currency'] = code
        rate = fetch_exchange_rate(code, 'USD')
        session['exchange_rate'] = rate
        return redirect(request.referrer or url_for('dashboard'))
    
    @app.route('/')
    @login_required
    def dashboard():
        # Always ensure currency and rate are set and up to date
        if 'currency' not in session:
            session['currency'] = 'USD'
        if 'exchange_rate' not in session:
            session['exchange_rate'] = 1.0
        
        # Get user's data
        budgets = Budget.query.filter_by(user_id=current_user.id).all()
        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        investments = Investment.query.filter_by(user_id=current_user.id).all()
        goals = Goal.query.filter_by(user_id=current_user.id).all()
        
        # Calculate totals
        total_budget = sum(b.limit_amount for b in budgets)
        total_expenses = sum(e.converted_amount_usd for e in expenses)
        total_investments = sum(i.shares * i.purchase_price for i in investments)
        total_goals = sum(g.target_amount for g in goals)
        
        return render_template('dashboard.html',
                             budgets=budgets,
                             expenses=expenses,
                             investments=investments,
                             goals=goals,
                             total_budget=total_budget,
                             total_expenses=total_expenses,
                             total_investments=total_investments,
                             total_goals=total_goals,
                             currency_list=CURRENCY_LIST)
    
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
            budget = Budget(
                user_id=current_user.id,
                category=form.category.data,
                limit_amount=form.limit_amount.data,
                month=form.month.data,
                year=form.year.data
            )
            db.session.add(budget)
            db.session.commit()
            flash('Budget added successfully!', 'success')
            return redirect(url_for('budget'))
        
        budgets = Budget.query.filter_by(user_id=current_user.id).all()
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
            goal = Goal(
                user_id=current_user.id,
                name=form.name.data,
                target_amount=form.target_amount.data,
                current_amount=form.current_amount.data,
                target_date=form.target_date.data
            )
            db.session.add(goal)
            db.session.commit()
            flash('Goal added successfully!', 'success')
            return redirect(url_for('goals'))
        
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
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)