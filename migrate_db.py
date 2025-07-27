#!/usr/bin/env python3
"""
Database Migration Script
Handles the target_date nullable change for the Goal model
"""

from app import create_app
from models import db, Goal
from sqlalchemy import text

def migrate_database():
    app = create_app('production')
    
    with app.app_context():
        try:
            # Check if we need to migrate
            result = db.session.execute(text("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='goal'
            """))
            table_sql = result.fetchone()
            
            if table_sql and 'target_date' in table_sql[0]:
                # Check if target_date is NOT NULL
                if 'target_date NOT NULL' in table_sql[0]:
                    print("🔄 Migrating database schema...")
                    
                    # Drop and recreate the goal table
                    db.session.execute(text("DROP TABLE IF EXISTS goal"))
                    db.create_all()
                    
                    print("✅ Database migration completed!")
                else:
                    print("✅ Database schema is already up to date!")
            else:
                print("✅ Creating new database with correct schema...")
                db.create_all()
                
        except Exception as e:
            print(f"❌ Migration error: {e}")
            # Fallback: just create tables
            db.create_all()
            print("✅ Database tables created!")

if __name__ == '__main__':
    migrate_database() 