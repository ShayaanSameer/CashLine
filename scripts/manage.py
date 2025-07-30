#!/usr/bin/env python
import os
import sys
from flask.cli import FlaskGroup
from app import create_app, db
from temp.models import User, Budget, Expense, Investment, Goal

app = create_app()
cli = FlaskGroup(app)

@cli.command("create_db")
def create_db():
    """Create the database tables."""
    db.create_all()
    print("Database tables created!")

@cli.command("drop_db")
def drop_db():
    """Drop the database tables."""
    db.drop_all()
    print("Database tables dropped!")

@cli.command("init_db")
def init_db():
    """Initialize the database with sample data."""
    db.create_all()
    
    # Create a sample user
    user = User(username='demo', email='demo@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    print("Database initialized with sample data!")

if __name__ == "__main__":
    cli() 