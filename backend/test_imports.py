print("Testing NETHRA Backend imports...")

try:
    print("1. Testing basic imports...")
    import logging
    print("✅ logging imported")
    
    from datetime import datetime
    print("✅ datetime imported")
    
    import time
    print("✅ time imported")
    
    print("2. Testing FastAPI imports...")
    from fastapi import FastAPI
    print("✅ FastAPI imported")
    
    print("3. Testing SQLAlchemy imports...")
    from sqlalchemy import text
    print("✅ SQLAlchemy imported")
    
    print("4. Testing database imports...")
    from database.database import engine
    print("✅ Database engine imported")
    
    print("5. Testing API router imports...")
    from api import auth_endpoints
    print("✅ auth_endpoints imported")
    
    from api import trust_endpoints
    print("✅ trust_endpoints imported")
    
    from api import mirage_endpoints
    print("✅ mirage_endpoints imported")
    
    print("6. Testing service imports...")
    from services.ai_interface import get_trust_predictor
    print("✅ AI interface imported")
    
    from services.mirage_controller import get_mirage_controller
    print("✅ Mirage controller imported")
    
    print("7. Testing middleware imports...")
    from middleware.rate_limit_middleware import RateLimitMiddleware
    print("✅ Rate limit middleware imported")
    
    print("🎉 ALL IMPORTS SUCCESSFUL!")
    
except ImportError as e:
    print(f"❌ IMPORT ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print(f"❌ OTHER ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
