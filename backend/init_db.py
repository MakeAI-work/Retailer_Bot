#!/usr/bin/env python3
"""
Database initialization script for WhatsApp Retailer Bots
This script creates all database tables and optionally adds sample data
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import our app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import User, Item, Sale, WhatsAppSession
from app.config import settings
from app.utils.security import get_password_hash


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    return engine


def add_sample_data(engine):
    """Add sample data for testing"""
    print("Adding sample data...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(User).first():
            print("⚠️  Sample data already exists, skipping...")
            return
        
        # Create sample user
        sample_user = User(
            name="Test Retailer",
            whatsapp_number="1234567890",
            password_hash=get_password_hash("password123"),
            is_active=True
        )
        db.add(sample_user)
        db.commit()
        db.refresh(sample_user)
        
        # Create sample items
        sample_items = [
            Item(name="Natraj Pencils", quantity=100, price=5.0, description="HB pencils pack of 10"),
            Item(name="Notebook A4", quantity=50, price=25.0, description="200 pages ruled notebook"),
            Item(name="Ball Pen", quantity=200, price=10.0, description="Blue ink ball pen"),
            Item(name="Eraser", quantity=75, price=2.0, description="White eraser"),
            Item(name="Ruler", quantity=30, price=8.0, description="30cm plastic ruler"),
        ]
        
        for item in sample_items:
            db.add(item)
        
        db.commit()
        print("✅ Sample data added successfully!")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main function"""
    print("🚀 Initializing WhatsApp Retailer Bots Database...")
    
    try:
        # Create tables
        engine = create_tables()
        
        # Ask user if they want sample data
        add_samples = input("\nDo you want to add sample data? (y/N): ").lower().strip()
        if add_samples in ['y', 'yes']:
            add_sample_data(engine)
        
        print("\n✅ Database initialization complete!")
        print("\nNext steps:")
        print("1. Update your .env file with correct database credentials")
        print("2. Run: alembic revision --autogenerate -m 'Initial migration'")
        print("3. Run: alembic upgrade head")
        print("4. Start the FastAPI server: uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. Database exists (createdb whatsapp_retailer_db)")
        print("3. Database credentials in .env are correct")
        sys.exit(1)


if __name__ == "__main__":
    main()
