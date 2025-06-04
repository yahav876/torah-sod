#!/usr/bin/env python3
"""
Initialize database and create tables
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app_factory import create_app
from app.models.database import db

def init_database():
    """Initialize the database with all tables."""
    print("Initializing database...")
    
    # Create app context
    app = create_app('development')
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Show created tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\nCreated tables: {', '.join(tables)}")
        
        # Check if Torah verses need indexing
        from app.models.database import TorahVerse
        count = TorahVerse.query.count()
        if count > 0:
            print(f"\nTorah verses already indexed: {count} verses")
        else:
            print("\nTorah verses not indexed yet. Run the app to trigger automatic indexing.")

if __name__ == '__main__':
    init_database()
