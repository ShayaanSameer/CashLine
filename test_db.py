#!/usr/bin/env python3

from app import app
from models import db, User, Budget, Expense, Investment, Goal
from datetime import datetime

def test_database():
    with app.app_context():
        # Create tables
        db.create_all()
        print("✅ Database tables created")
        
        # Test user creation
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        print("✅ User created successfully")
        
        # Test budget creation
        budget = Budget(
            user_id=user.id,
            category='Food',
            limit_amount=500.0,
            month='July',
            year='2025'
        )
        db.session.add(budget)
        db.session.commit()
        print("✅ Budget created successfully")
        
        # Test expense creation
        expense = Expense(
            user_id=user.id,
            amount=50.0,
            category='Food',
            description='Lunch',
            date=datetime.now().date(),
            currency='USD',
            converted_amount_usd=50.0
        )
        db.session.add(expense)
        db.session.commit()
        print("✅ Expense created successfully")
        
        # Test investment creation
        investment = Investment(
            user_id=user.id,
            symbol='AAPL',
            shares=10.0,
            purchase_price=150.0,
            purchase_date=datetime.now().date()
        )
        db.session.add(investment)
        db.session.commit()
        print("✅ Investment created successfully")
        
        # Test goal creation
        goal = Goal(
            user_id=user.id,
            name='Vacation',
            target_amount=5000.0,
            current_amount=1000.0,
            target_date=datetime.now().date()
        )
        db.session.add(goal)
        db.session.commit()
        print("✅ Goal created successfully")
        
        # Query and display data
        print("\n📊 Database Contents:")
        print(f"Users: {User.query.count()}")
        print(f"Budgets: {Budget.query.count()}")
        print(f"Expenses: {Expense.query.count()}")
        print(f"Investments: {Investment.query.count()}")
        print(f"Goals: {Goal.query.count()}")
        
        # Show user's data
        user_data = User.query.filter_by(username='testuser').first()
        if user_data:
            print(f"\n👤 User: {user_data.username}")
            print(f"Budgets: {[b.category for b in user_data.budgets]}")
            print(f"Expenses: {[e.description for e in user_data.expenses]}")
            print(f"Investments: {[i.symbol for i in user_data.investments]}")
            print(f"Goals: {[g.name for g in user_data.goals]}")

if __name__ == '__main__':
    test_database() 