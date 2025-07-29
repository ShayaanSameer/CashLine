#!/usr/bin/env python3
"""
Database Reset Script
Use this in production emergencies to reset the database schema
"""

from app import create_app
from temp.models import db
from sqlalchemy import text

def reset_database():
    app = create_app('production')
    
    with app.app_context():
        try:
            print("Resetting database schema...")
            
            # Drop all tables
            db.drop_all()
            print("Dropped all tables")
            
            # Recreate all tables with correct schema
            db.create_all()
            print("Recreated all tables with updated schema")
            
            print("Database reset completed successfully!")
            
        except Exception as e:
            print(f"Reset error: {e}")

if __name__ == '__main__':
    reset_database() 