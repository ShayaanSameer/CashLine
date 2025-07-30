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
from app.operations import deserializeDoc

auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user_doc = current_app.mongo.getCollectionEndpoint('User').find_one({'username':form.username.data})
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

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm(current_app.mongo, request.form)
    if form.validate_on_submit():
        # Check if username already exists
        user_doc = current_app.mongo.getCollectionEndpoint('User').find_one({'username':form.username.data})
        existing_user = deserializeDoc.user(user_doc)

        if existing_user:
            flash('Username already exists. Please choose a different username.', 'error')
            return render_template('register.html', form=form)
        
        # Check if email already exists
        user_doc = current_app.mongo.getCollectionEndpoint('User').find_one({'email':form.email.data})
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

            doc = vars(user)
            doc.pop("_id", None)
            current_app.mongo.getCollectionEndpoint('User').insert_one(doc)

            flash('Registration successful! Please log in with your new account.', 'login_success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))