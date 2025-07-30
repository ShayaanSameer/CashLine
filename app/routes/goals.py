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

goals_bp = Blueprint("goals", __name__)

@goals_bp.route('/goals')
@login_required
def goals():
    goals = list(current_app.mongo.getCollectionEndpoint('Goal').find({"user_id":current_user._id}))
    for i in range(len(goals)):
        goals[i] = deserializeDoc.goal(goals[i])

    return render_template('goals.html', goals=goals)

@goals_bp.route('/goals/add', methods=['GET', 'POST'])
@login_required
def add_goal():
    form = GoalForm()
    if form.validate_on_submit():
        goal = Goal(
            user_id=current_user._id,
            name=form.name.data,
            target_amount=form.target_amount.data,
            current_amount=form.current_amount.data,
            target_date=datetime.combine(form.target_date.data, datetime.min.time())
        )

        doc = vars(goal)
        doc.pop("_id", None)
        current_app.mongo.getCollectionEndpoint('Goal').insert_one(doc)
        flash('Goal added successfully!', 'success')
        return redirect(url_for('goals'))
    
    return render_template('add_goal.html', form=form)

@goals_bp.route('/goals/edit/<goal_id>', methods=['GET', 'POST'])
@login_required
def edit_goal(goal_id):
    goal_doc = current_app.mongo.getCollectionEndpoint('Goal').find_one({"_id": ObjectId(goal_id)})
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
        goal.target_date = datetime.combine(form.target_date.data, datetime.min.time())
        
        current_app.mongo.getCollectionEndpoint('Goal').update_one(
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

@goals_bp.route('/goals/delete/<goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):
    goal_doc = current_app.mongo.getCollectionEndpoint('Goal').find_one({"_id": ObjectId(goal_id)})
    if not goal_doc:
        abort(404)
    goal = deserializeDoc.goal(goal_doc)
    if goal.user_id != current_user._id:
        flash('Access denied.', 'error')
        return redirect(url_for('goals'))
    
    current_app.mongo.getCollectionEndpoint('Goal').delete_one({"_id" : ObjectId(goal_id)})
    flash('Goal deleted successfully!', 'success')
    return redirect(url_for('goals'))
