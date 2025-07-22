from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import logging
from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Create engine with proper SQLite configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
    connect_args={
        "check_same_thread": False,
        "timeout": 20
    } if "sqlite" in DATABASE_URL else {}
)

# Create SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def check_database_health():
    """Check database connection health - FIXED with text() wrapper"""
    try:
        with engine.connect() as conn:
            # FIXED: Properly wrapped SQL in text() - this was causing your error!
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database health check successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database health check failed: {str(e)}")
        return False

def get_database_info():
    """Get database information with proper text() wrappers"""
    try:
        with engine.connect() as conn:
            # FIXED: All SQL queries properly wrapped in text()
            user_result = conn.execute(text("SELECT COUNT(*) FROM users"))
            session_result = conn.execute(text("SELECT COUNT(*) FROM user_sessions WHERE is_active = 1"))
            behavioral_result = conn.execute(text("SELECT COUNT(*) FROM behavioral_data"))
            mirage_result = conn.execute(text("SELECT COUNT(*) FROM mirage_sessions WHERE is_active = 1"))
            
            return {
                "total_users": user_result.scalar(),
                "active_sessions": session_result.scalar(),
                "behavioral_records": behavioral_result.scalar(),
                "active_mirage_sessions": mirage_result.scalar(),
                "status": "connected",
                "database_type": "sqlite" if "sqlite" in DATABASE_URL else "postgresql"
            }
    except Exception as e:
        logger.error(f"❌ Failed to get database info: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

def test_database_operations():
    """Test basic database operations with proper text() usage"""
    try:
        with engine.connect() as conn:
            # Test table existence
            tables_result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in tables_result.fetchall()]
            
            # Test basic queries on each table
            test_results = {}
            for table in tables:
                try:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    test_results[table] = count_result.scalar()
                except Exception as table_error:
                    test_results[table] = f"Error: {str(table_error)}"
            
            return {
                "status": "success",
                "tables": tables,
                "table_counts": test_results
            }
    except Exception as e:
        logger.error(f"❌ Database operations test failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

def initialize_database_connection():
    """Initialize and verify database connection on startup"""
    try:
        with engine.connect() as conn:
            # Verify connection with proper text() wrapper
            conn.execute(text("SELECT 1"))
            
            # Get basic info
            user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            
        logger.info(f"✅ Database connection initialized successfully")
        logger.info(f"   Current users: {user_count}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection initialization failed: {str(e)}")
        return False
