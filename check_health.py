#!/usr/bin/env python3
"""Quick health check script - run this before starting the server"""
import sys
import os

def check_health():
    errors = []
    warnings = []
    
    # Check Python version
    if sys.version_info < (3, 10):
        errors.append(f"Python 3.10+ required, got {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check if virtual env is activated (rough check)
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        warnings.append("Virtual environment may not be activated")
    
    # Check if required files exist
    required_files = [
        "app.py",
        "city_config.json",
        "db/models.py",
        "connectors/csv_seed.py",
        "data/seeds/boston_childcare_providers.csv",
        "data/seeds/boston_health_providers.csv"
    ]
    for f in required_files:
        if not os.path.exists(f):
            errors.append(f"Missing required file: {f}")
    
    # Try to import the app
    try:
        import app
        print("✅ App imports successfully")
    except Exception as e:
        errors.append(f"Failed to import app: {e}")
    
    # Check if port is free
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8000))
    sock.close()
    if result == 0:
        warnings.append("Port 8000 is already in use - kill existing processes first")
    
    # Report
    if errors:
        print("\n❌ ERRORS:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    
    print("\n✅ All checks passed! Ready to start server.")
    return 0

if __name__ == "__main__":
    sys.exit(check_health())

