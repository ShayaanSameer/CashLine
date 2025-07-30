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
from app.operations import mongoDBClient, deserializeDoc, summarize_user_financial_context

advice_bp = Blueprint("advice", __name__)

@advice_bp.route('/advice', methods=['GET', 'POST'])
@login_required
def advice():
    GEMINI_API_KEY = current_app.config["GEMINI_API_KEY"]

    if request.method == 'POST':
        question = request.form.get('question', '')
        if question:
            try:
                # Get comprehensive financial context
                budget_context = summarize_user_financial_context()
                
                # Use Gemini API for financial advice
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
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

                print(response.json())
                
                if response.status_code == 200:
                    result = response.json()
                    print(result)
                    candidates = result.get("candidates", [])
                    if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
                        parts = candidates[0]["content"]["parts"]
                        if parts and "text" in parts[0]:
                            advice = parts[0]["text"]
                        else:
                            advice = "No advice text returned from Gemini."
                    else:
                        advice = "No candidates returned from Gemini."
                    return render_template('advice.html', advice=advice, question=question)
                
            except Exception as e:
                error = f"Error connecting to Gemini API: {e}"
                return render_template('advice.html', error=error, question=question)
    
    return render_template('advice.html')

@advice_bp.route('/advice/chat', methods=['POST'])
@login_required
def advice_chat():
    GEMINI_API_KEY = current_app.config["GEMINI_API_KEY"]
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
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
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
            print(result)
            candidates = result.get("candidates", [])
            if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
                parts = candidates[0]["content"]["parts"]
                if parts and "text" in parts[0]:
                    ai_response = parts[0]["text"]
                else:
                    ai_response = "No response text returned."
            else:
                ai_response = "No candidates returned from Gemini."
            return jsonify({'ai_response': ai_response})
            
    except Exception as e:
        return jsonify({'error': f'Error connecting to Gemini API: {e}'}), 500
