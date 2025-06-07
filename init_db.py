#!/usr/bin/env python3
"""
Database initialization script for StatementSense
"""
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.config import settings
from app.db.base import Base
from app.models.statement import BankStatement, Transaction, CategoryRule, ProcessingLog  # noqa


def create_database():
    """Create the database if it doesn't exist"""
    # Extract database name from URL
    db_name = settings.DB_NAME
    
    # Create connection to PostgreSQL without specifying database
    admin_url = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/postgres"
    
    try:
        admin_engine = create_engine(admin_url)
        
        with admin_engine.connect() as conn:
            # Set isolation level to autocommit to allow database creation
            conn.execute(text("commit"))
            
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if not result.fetchone():
                # Database doesn't exist, create it
                print(f"Creating database: {db_name}")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database {db_name} created successfully")
            else:
                print(f"Database {db_name} already exists")
                
    except Exception as e:
        print(f"Error creating database: {e}")
        return False
    
    return True


def create_tables():
    """Create all tables using SQLAlchemy"""
    try:
        engine = create_engine(str(settings.DATABASE_URL))
        
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully")
        
        return True
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False


def create_sample_category_rules():
    """Create some sample category rules"""
    from sqlalchemy.orm import sessionmaker
    from app.models.statement import CategoryRule
    
    try:
        engine = create_engine(str(settings.DATABASE_URL))
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            # Check if rules already exist
            existing_count = db.query(CategoryRule).count()
            if existing_count > 0:
                print(f"Category rules already exist ({existing_count} rules)")
                return True
            
            print("Creating sample category rules...")
            
            sample_rules = [
                {
                    "rule_name": "OXXO Convenience Store",
                    "rule_type": "exact_match",
                    "pattern": "oxxo",
                    "category": "alimentacion",
                    "priority": 10
                },
                {
                    "rule_name": "Walmart Supermarket", 
                    "rule_type": "exact_match",
                    "pattern": "walmart",
                    "category": "alimentacion",
                    "priority": 10
                },
                {
                    "rule_name": "PEMEX Gas Station",
                    "rule_type": "exact_match", 
                    "pattern": "pemex",
                    "category": "gasolineras",
                    "priority": 10
                },
                {
                    "rule_name": "Restaurant Pattern",
                    "rule_type": "pattern_match",
                    "pattern": r"\b(rest|restaurant|restaurante)\b",
                    "category": "alimentacion",
                    "priority": 5
                },
                {
                    "rule_name": "Doctor Visits",
                    "rule_type": "pattern_match", 
                    "pattern": r"\bdr\s+[a-z]+",
                    "category": "salud",
                    "priority": 8
                },
                {
                    "rule_name": "Gas Station Pattern",
                    "rule_type": "pattern_match",
                    "pattern": r"\bgas\s+",
                    "category": "gasolineras", 
                    "priority": 7
                },
                {
                    "rule_name": "Netflix Subscription",
                    "rule_type": "exact_match",
                    "pattern": "netflix",
                    "category": "servicios",
                    "priority": 10
                },
                {
                    "rule_name": "Uber Transportation",
                    "rule_type": "pattern_match",
                    "pattern": r"\buber\s+(trip|eats)",
                    "category": "transporte",
                    "priority": 8
                }
            ]
            
            for rule_data in sample_rules:
                rule = CategoryRule(**rule_data)
                db.add(rule)
            
            db.commit()
            print(f"Created {len(sample_rules)} sample category rules")
            
        return True
        
    except Exception as e:
        print(f"Error creating sample rules: {e}")
        return False


def main():
    """Main initialization function"""
    print("=" * 50)
    print("StatementSense Database Initialization")
    print("=" * 50)
    
    # Step 1: Create database
    print("\n1. Creating database...")
    if not create_database():
        print("❌ Failed to create database")
        sys.exit(1)
    
    # Step 2: Create tables
    print("\n2. Creating tables...")
    if not create_tables():
        print("❌ Failed to create tables")
        sys.exit(1)
    
    # Step 3: Create sample data
    print("\n3. Creating sample category rules...")
    if not create_sample_category_rules():
        print("❌ Failed to create sample rules")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Database initialization completed successfully!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Start the API server: uvicorn app.main:app --reload")
    print("2. Upload a PDF statement via POST /api/v1/statements/upload")
    print("3. Process it via POST /api/v1/statements/{id}/process")
    print("4. View results at /docs for API documentation")


if __name__ == "__main__":
    main()
