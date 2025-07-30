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
from .forms import LoginForm, RegistrationForm, BudgetForm, ExpenseForm, InvestmentForm, GoalForm, UserProfileForm, AssetForm, RetirementPlanForm, AutomatedRetirementForm, RetirementProfileForm, RetirementCalculatorForm

from .mongoModels import Investment, User, Budget, Expense, Goal, UserProfile, Asset, RetirementPlan
from .operations import mongoDBClient, deserializeDoc

from .routes.advice import advice_bp
from .routes.auth import auth_bp
from .routes.budget import budget_bp
from .routes.expenses import expenses_bp
from .routes.goals import goals_bp
from .routes.main import main_bp
from .routes.portfolio import portfolio_bp


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    dbClient = mongoDBClient(app.config["MONGO_URI"])
    app.mongo = dbClient
    
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
        
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("500.html"), 500
    
    app.register_blueprint(advice_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(portfolio_bp)

    return app