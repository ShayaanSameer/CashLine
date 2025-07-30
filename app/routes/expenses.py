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
from app.operations import mongoDBClient, deserializeDoc, fetch_exchange_rate

expenses_bp = Blueprint("expenses", __name__)

@expenses_bp.route('/expenses', methods=['GET', 'POST'], endpoint='expenses')
@login_required
def expenses():
    form = ExpenseForm()
    
    # Get categories from existing budgets
    budgets = list(current_app.mongo.getCollectionEndpoint('Budget').find({"user_id":current_user._id}))
    for i in range(len(budgets)):
        budgets[i] = deserializeDoc.budget(budgets[i])

    categories = [budget.category for budget in budgets]
    form.category.choices = [(cat, cat) for cat in categories]
    
    if form.validate_on_submit():
        # Convert amount to USD
        amount_usd = form.amount.data
        if form.currency.data != 'USD':
            rate = fetch_exchange_rate(form.currency.data, 'USD', current_app.config["EXCHANGE_RATE_API_KEY"])
            amount_usd = form.amount.data * rate
        
        expense = Expense(
            user_id=current_user._id,
            amount=form.amount.data,
            category=form.category.data,
            description=form.description.data,
            date=datetime.combine(form.date.data, datetime.min.time()),
            currency=form.currency.data,
            converted_amount_usd=amount_usd
        )
        doc = vars(expense)
        doc.pop("_id", None)
        current_app.mongo.getCollectionEndpoint('Expense').insert_one(doc)
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses.expenses'))
    

    expenses = list(current_app.mongo.getCollectionEndpoint('Expense').find({"user_id":current_user._id}).sort({"date" : -1}))
    for i in range(len(expenses)):
        expenses[i] = deserializeDoc.expense(expenses[i])

    return render_template('expenses.html', form=form, expenses=expenses)

@expenses_bp.route('/edit_expense/<expense_id>', methods=['GET', 'POST'], endpoint='edit_expense')
@login_required
def edit_expense(expense_id):
    expense_doc = current_app.mongo.getCollectionEndpoint('Expense').find_one({"_id": ObjectId(expense_id)})
    if not expense_doc:
        abort(404)
    expense = deserializeDoc.expense(expense_doc)

    if expense.user_id != current_user._id:
        flash('Access denied.', 'error')
        return redirect(url_for('expenses.expenses'))
    
    form = ExpenseForm()
    
    # Get categories from existing budgets
    budgets = list(current_app.mongo.getCollectionEndpoint('Budget').find({"user_id":current_user._id}))
    for i in range(len(budgets)):
        budgets[i] = deserializeDoc.budget(budgets[i])

    categories = [budget.category for budget in budgets]
    form.category.choices = [(cat, cat) for cat in categories]
    
    if form.validate_on_submit():
        # Convert amount to USD
        amount_usd = form.amount.data
        if form.currency.data != 'USD':
            rate = fetch_exchange_rate(form.currency.data, 'USD', current_app.config["EXCHANGE_RATE_API_KEY"])
            amount_usd = form.amount.data * rate
        
        expense.amount = form.amount.data
        expense.category = form.category.data
        expense.description = form.description.data
        expense.date = datetime.combine(form.date.data, datetime.min.time())
        expense.currency = form.currency.data
        expense.converted_amount_usd = amount_usd
        
        current_app.mongo.getCollectionEndpoint('Expense').update_one(
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
        return redirect(url_for('expenses.expenses'))
    elif request.method == 'GET':
        form.amount.data = expense.amount
        form.category.data = expense.category
        form.description.data = expense.description
        form.date.data = expense.date
        form.currency.data = expense.currency
    
    return render_template('edit_expense.html', form=form, expense=expense)

@expenses_bp.route('/delete_expense/<expense_id>', methods=['POST'], endpoint='delete_expense')
@login_required
def delete_expense(expense_id):
    expense_doc = current_app.mongo.getCollectionEndpoint('Expense').find_one({"_id": ObjectId(expense_id)})
    if not expense_doc:
        abort(404)
    expense = deserializeDoc.expense(expense_doc)

    if expense.user_id != current_user._id:
        flash('Access denied.', 'error')
        return redirect(url_for('expenses.expenses'))
    
    current_app.mongo.getCollectionEndpoint('Expense').delete_one({"_id" : ObjectId(expense_id)})
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expenses.expenses'))
