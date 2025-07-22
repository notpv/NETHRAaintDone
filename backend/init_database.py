from database.database import engine, Base
from database.models import User, TrustProfile, UserSession, BehavioralData, MirageSession
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize NETHRA database with all tables"""
    try:
        # Drop all existing tables (if any)
        Base.metadata.drop_all(bind=engine)
        logger.info("Dropped existing tables")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All database tables created successfully")
        
        # Verify tables were created
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Created tables: {tables}")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise

if __name__ == "__main__":
    init_database()
    print("🎯 NETHRA database initialized successfully!")
