#!/usr/bin/env python3
"""Quick script to test database connection"""
import os
import sys

# Try to import database stuff
try:
    from db.models import Base, make_engine, make_session
    from sqlalchemy import text
    
    # Get database URL
    DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
    if DATABASE_URL:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        DB_URL = DATABASE_URL
    else:
        DB_URL = "sqlite:///./city_fraud_finder.db"
    
    print(f"🔌 Connecting to: {DB_URL.split('@')[1] if '@' in DB_URL else 'SQLite (local)'}")
    
    # Try to connect
    engine = make_engine(DB_URL)
    session = make_session(engine)
    
    # Test query
    result = session.execute(text("SELECT 1 as test"))
    test_value = result.scalar()
    
    if test_value == 1:
        print("✅ DATABASE CONNECTION WORKS!")
        print("✅ PostgreSQL is connected and responding")
        sys.exit(0)
    else:
        print("❌ Connection test failed")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

