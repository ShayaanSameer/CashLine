from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin):
    def __init__(self, 
                 _id = ObjectId(),
                 username = None,
                 email = None,
                 password_hash = None,
                 created_at = datetime.now()):
        self._id = _id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self._id)
    
class UserProfile():
    def __init__(self, user_id, age, ra, cs, eri, csave, mc, rt, created_at=datetime.now(), updated_at=datetime.now(), _id=ObjectId()):
        self._id=_id
        self.user_id = user_id
        self.age = age
        self.retirement_age = ra
        self.current_salary = cs
        self.expected_retirement_income = eri
        self.current_savings = csave
        self.monthly_contribution = mc
        self.risk_tolerance = rt
        self.created_at = created_at
        self.updated_at = updated_at

class Asset():
    def __init__(self, user_id, symbol, name, asset_type, expected_return, weight, risk_level, created_at=datetime.now(), updated_at=datetime.now(), _id=ObjectId()):
        self._id = _id
        self.user_id = user_id
        self.symbol = symbol
        self.name = name
        self.asset_type = asset_type
        self.expected_return = expected_return
        self.weight = weight
        self.risk_level = risk_level
        self.created_at = created_at
        self.updated = updated_at

class RetirementPlan():
    def __init__(self, user_id, name, target_amount, ytr, err, mcn, pa, c_at=datetime.now(), u_at=datetime.now(), _id=ObjectId()):
        self._id = _id
        self.user_id = user_id
        self.name = name
        self.target_amount = target_amount
        self.years_to_retirment = ytr
        self.expected_return_rate = err
        self.monthly_contribution_needed = mcn
        self.projected_amount = pa
        self.created_at = c_at
        self.updated_at = u_at

class Budget():
    def __init__(self, user_id, category, limit_amount, month, year, created_at=datetime.now(), _id=ObjectId()):
        self._id = _id
        self.user_id = user_id
        self.category = category
        self.limit_amount = limit_amount
        self.month = month
        self.year = year
        self.created_at = created_at

class Expense():
    def __init__(self, user_id, amount, category, description, date, currency, converted_amount_usd, created_at=datetime.now(), _id=ObjectId()):
        self._id = _id
        self.user_id = user_id
        self.category = category
        self.amount = amount
        self.description = description
        self.date = date
        self.currency = currency
        self.converted_amount_usd = converted_amount_usd
        self.created_at = created_at

class Investment():
    def __init__(self, user_id, symbol, shares, purchase_price, purchase_date, updated_at=datetime.now(), created_at=datetime.now(), _id=ObjectId()):
        self._id = _id
        self.user_id = user_id
        self.symbol = symbol
        self.shares = shares
        self.purchase_price = purchase_price
        self.purchase_date = purchase_date
        self.created_at = created_at
        self.updated_at = updated_at

class Goal():
    def __init__(self, user_id, name, target_amount, current_amount, target_date, created_at=datetime.now(), _id=ObjectId()):
        self._id = _id
        self.user_id = user_id
        self.name = name
        self.target_amount = target_amount
        self.current_amount = current_amount
        self.target_date = target_date
        self.created_at = created_at