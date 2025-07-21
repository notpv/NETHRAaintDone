import os
import logging
from typing import Generator
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nethra.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# SQLite specific configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        poolclass=StaticPool,
        echo=DATABASE_ECHO
    )
else:
    engine = create_engine(DATABASE_URL, echo=DATABASE_ECHO)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Base class for ORM models
Base = declarative_base()

# SQLite optimization
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Optimize SQLite performance"""
    if 'sqlite' in DATABASE_URL:
        cursor = dbapi_connection.cursor()
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Optimize SQLite settings
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=memory")
        cursor.close()

def init_db() -> None:
    """Initialize database and create all tables"""
    try:
        # Import all models to ensure they're registered
        from . import models
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Database tables created successfully")
        
        # Create indexes for better performance
        create_indexes()
        
        # Create initial admin user if needed
        create_default_data()
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

def create_indexes():
    """Create database indexes for better performance"""
    try:
        with engine.connect() as connection:
            # Indexes for users table
            connection.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            
            # Indexes for trust_scores table
            connection.execute("CREATE INDEX IF NOT EXISTS idx_trust_scores_user_timestamp ON trust_scores(user_id, timestamp)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_trust_scores_session ON trust_scores(session_id)")
            
            # Indexes for sessions table
            connection.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_active ON sessions(user_id, is_active)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity)")
            
            connection.commit()
            logger.info("✅ Database indexes created successfully")
            
    except Exception as e:
        logger.warning(f"⚠️ Index creation warning: {e}")

def create_default_data():
    """Create default users and data for testing"""
    try:
        from .crud import UserCRUD
        
        db = SessionLocal()
        
        # Check if admin user exists
        admin_user = UserCRUD.get_user_by_username(db, "admin")
        
        if not admin_user:
            # Create default admin user
            admin_user = UserCRUD.create_user(
                db=db,
                username="admin",
                email="admin@nethra.ai",
                password="NethraAdmin2025!",
                full_name="NETHRA Administrator",
                device_id="admin_device"
            )
            logger.info("✅ Default admin user created")
        
        # Create test user for demo
        test_user = UserCRUD.get_user_by_username(db, "testuser")
        if not test_user:
            test_user = UserCRUD.create_user(
                db=db,
                username="testuser",
                email="test@nethra.ai", 
                password="TestUser123!",
                full_name="Test User",
                device_id="test_device"
            )
            logger.info("✅ Test user created")
        
        db.close()
        
    except Exception as e:
        logger.error(f"❌ Default data creation failed: {e}")

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


from contextlib import contextmanager

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

class DatabaseManager:
    """Database manager class for advanced operations"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_table_stats(self) -> dict:
        """Get statistics about database tables"""
        try:
            with self.engine.connect() as connection:
                stats = {}
                
                # Get row counts for each table
                tables = ['users', 'sessions', 'trust_profiles', 'trust_scores', 'tamper_events', 'mirage_events']
                
                for table in tables:
                    try:
                        result = connection.execute(f"SELECT COUNT(*) FROM {table}")
                        stats[table] = result.scalar()
                    except:
                        stats[table] = 0
                
                return stats
        except Exception as e:
            logger.error(f"Failed to get table stats: {e}")
            return {}
    
    def cleanup_old_sessions(self, days_old: int = 30):
        """Clean up old inactive sessions"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(
                    f"""
                    DELETE FROM sessions 
                    WHERE is_active = 0 
                    AND session_end < datetime('now', '-{days_old} days')
                    """
                )
                connection.commit()
                logger.info(f"Cleaned up {result.rowcount} old sessions")
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")

    def backup_database(self, backup_path: str = None):
        """Create database backup"""
        try:
            import shutil
            from datetime import datetime
            
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"nethra_backup_{timestamp}.db"
            
            if DATABASE_URL.startswith("sqlite"):
                db_file = DATABASE_URL.replace("sqlite:///", "")
                shutil.copy2(db_file, backup_path)
                logger.info(f"Database backed up to: {backup_path}")
                return backup_path
            else:
                logger.warning("Backup only supported for SQLite databases")
                return None
                
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return None

# Global database manager instance
db_manager = DatabaseManager()
