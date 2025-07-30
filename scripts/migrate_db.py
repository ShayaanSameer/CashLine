#!/usr/bin/env python3
"""
Database Migration Script
Handles the target_date nullable change for the Goal model
"""

from app import app, db
from temp.models import User, Budget, Expense, Investment, Goal, UserProfile, Asset, RetirementPlan

def migrate_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database migration completed successfully!")

if __name__ == '__main__':
    migrate_database() 