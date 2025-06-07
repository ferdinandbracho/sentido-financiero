#!/usr/bin/env python3
"""
Test script to verify StatementSense configuration
Run with: uv run python test_config.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config():
    """Test configuration loading"""
    try:
        from app.config import settings
        print("✅ Configuration loaded successfully")
        print(f"   Project Name: {settings.PROJECT_NAME}")
        print(f"   Database URL: {str(settings.DATABASE_URL)[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False

def test_models():
    """Test model imports"""
    try:
        from app.models.statement import BankStatement, Transaction, CategoryRule, ProcessingLog
        print("✅ Models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False

def test_db_base():
    """Test database base"""
    try:
        from app.db.base import Base
        from app.models.statement import BankStatement
        
        # Check if models are registered
        tables = list(Base.metadata.tables.keys())
        print(f"✅ Database base configured with {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")
        return True
    except Exception as e:
        print(f"❌ Database base failed: {e}")
        return False

def test_categorizer():
    """Test smart categorizer"""
    try:
        from app.services.smart_categorizer import SmartCategorizer
        categorizer = SmartCategorizer()
        print("✅ Smart categorizer initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Smart categorizer failed: {e}")
        return False

def test_pdf_parser():
    """Test PDF parser"""
    try:
        from app.services.pdf_parser import PDFStatementParser
        parser = PDFStatementParser()
        print("✅ PDF parser initialized successfully")
        return True
    except Exception as e:
        print(f"❌ PDF parser failed: {e}")
        return False

def main():
    print("🧪 Testing StatementSense Configuration\n")
    
    tests = [
        ("Configuration", test_config),
        ("Models", test_models), 
        ("Database Base", test_db_base),
        ("Smart Categorizer", test_categorizer),
        ("PDF Parser", test_pdf_parser),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 Testing {name}...")
        results.append(test_func())
    
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("\n✅ StatementSense is ready for development!")
        print("\nNext steps:")
        print("1. Run: ./setup.sh  (to set up database and Ollama)")
        print("2. Run: make run     (to start the development server)")
    else:
        print(f"⚠️  Some tests failed ({passed}/{total})")
        print("\n❌ Please fix the issues above before proceeding")
        sys.exit(1)

if __name__ == "__main__":
    main()
