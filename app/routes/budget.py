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

budget_bp = Blueprint("budget", __name__)

@budget_bp.route('/budget', methods=['GET', 'POST'])
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
        doc = vars(budget)
        doc.pop("_id", None)
        current_app.mongo.getCollectionEndpoint('Budget').insert_one(doc)

        flash('Budget added successfully!', 'success')
        return redirect(url_for('budget'))
    
    budgets = list(current_app.mongo.getCollectionEndpoint('Budget').find({"user_id" : current_user._id}))
    for i in range(len(budgets)):
        budgets[i] = deserializeDoc.budget(budgets[i])

    return render_template('budget.html', form=form, budgets=budgets)

@budget_bp.route('/edit_budget/<budget_id>', methods=['GET', 'POST'])
@login_required
def edit_budget(budget_id):
    budget_doc = current_app.mongo.getCollectionEndpoint('Budget').find_one({"_id": ObjectId(budget_id)})
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
        
        current_app.mongo.getCollectionEndpoint('Budget').update_one(
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

@budget_bp.route('/delete_budget/<budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id):
    budget_doc = current_app.mongo.getCollectionEndpoint('Budget').find_one({"_id": ObjectId(budget_id)})
    if not budget_doc:
        abort(404)
    budget = deserializeDoc.budget(budget_doc)

    if budget.user_id != current_user._id:
        flash('Access denied.', 'error')
        return redirect(url_for('budget'))
    
    current_app.mongo.getCollectionEndpoint('Budget').delete_one({"_id" : ObjectId(budget_id)})
    flash('Budget deleted successfully!', 'success')
    return redirect(url_for('budget'))
