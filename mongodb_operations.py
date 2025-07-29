from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from mongoModels import User, Budget, Expense, Investment, Goal, UserProfile, Asset, RetirementPlan

class mongoDBClient:
    def __init__(self, uri):
        self.uri = uri
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))

    def getCollectionEndpoint(self, name):
        return self.client.get_database("cashline").get_collection(name)
    
    def __del__(self):
        self.client.close()

class deserializeDoc:
    @staticmethod
    def user(doc):
        if not doc:
            return None
        return User(
            _id=doc.get('_id'),
            username=doc.get('username'),
            email=doc.get('email'),
            password_hash=doc.get('password_hash'),
            created_at=doc.get('created_at')
        )

    @staticmethod
    def user_profile(doc):
        if not doc:
            return None
        return UserProfile(
            user_id=doc.get('user_id'),
            age=doc.get('age'),
            ra=doc.get('retirement_age'),
            cs=doc.get('current_salary'),
            eri=doc.get('expected_retirement_income'),
            csave=doc.get('current_savings'),
            mc=doc.get('monthly_contribution'),
            rt=doc.get('risk_tolerance'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at'),
            _id=doc.get('_id')
        )

    @staticmethod
    def asset(doc):
        if not doc:
            return None
        return Asset(
            user_id=doc.get('user_id'),
            symbol=doc.get('symbol'),
            name=doc.get('name'),
            asset_type=doc.get('asset_type'),
            expected_return=doc.get('expected_return'),
            weight=doc.get('weight'),
            risk_level=doc.get('risk_level'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at'),
            _id=doc.get('_id')
        )

    @staticmethod
    def retirement_plan(doc):
        if not doc:
            return None
        return RetirementPlan(
            user_id=doc.get('user_id'),
            name=doc.get('name'),
            target_amount=doc.get('target_amount'),
            ytr=doc.get('years_to_retirment'),
            err=doc.get('expected_return_rate'),
            mcn=doc.get('monthly_contribution_needed'),
            pa=doc.get('projected_amount'),
            c_at=doc.get('created_at'),
            u_at=doc.get('updated_at'),
            _id=doc.get('_id')
        )

    @staticmethod
    def budget(doc):
        if not doc:
            return None
        return Budget(
            user_id=doc.get('user_id'),
            category=doc.get('category'),
            limit_amount=doc.get('limit_amount'),
            month=doc.get('month'),
            year=doc.get('year'),
            created_at=doc.get('created_at'),
            _id=doc.get('_id')
        )

    @staticmethod
    def expense(doc):
        if not doc:
            return None
        return Expense(
            user_id=doc.get('user_id'),
            amount=doc.get('amount'),
            category=doc.get('category'),
            description=doc.get('description'),
            date=doc.get('date'),
            currency=doc.get('currency'),
            converted_amount_usd=doc.get('converted_amount_usd'),
            created_at=doc.get('created_at'),
            _id=doc.get('_id')
        )

    @staticmethod
    def investment(doc):
        if not doc:
            return None
        return Investment(
            user_id=doc.get('user_id'),
            symbol=doc.get('symbol'),
            shares=doc.get('shares'),
            purchase_price=doc.get('purchase_price'),
            purchase_date=doc.get('purchase_date'),
            created_at=doc.get('created_at'),
            _id=doc.get('_id')
        )

    @staticmethod
    def goal(doc):
        if not doc:
            return None
        return Goal(
            user_id=doc.get('user_id'),
            name=doc.get('name'),
            target_amount=doc.get('target_amount'),
            current_amount=doc.get('current_amount'),
            target_date=doc.get('target_date'),
            created_at=doc.get('created_at'),
            _id=doc.get('_id')
        )