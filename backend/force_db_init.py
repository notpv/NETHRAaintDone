import sqlite3
import logging
from database.database import engine, Base
from database.models import User, TrustProfile, UserSession, BehavioralData, MirageSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_create_database():
    """Force create all NETHRA database tables manually"""
    try:
        # Method 1: Use SQLAlchemy
        logger.info("🔧 Creating tables using SQLAlchemy...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # Method 2: Verify with direct SQLite connection
        logger.info("🔍 Verifying tables with direct SQLite connection...")
        conn = sqlite3.connect('nethra.db')
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        logger.info(f"✅ Tables created: {[table[0] for table in tables]}")
        
        # Create tables manually if SQLAlchemy failed
        if len(tables) == 0:
            logger.info("⚠️ SQLAlchemy failed, creating tables manually...")
            
            # Create users table manually
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until DATETIME
                )
            ''')
            
            # Create trust_profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trust_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    session_count INTEGER DEFAULT 0,
                    average_trust_score REAL DEFAULT 50.0,
                    personal_threshold REAL DEFAULT 40.0,
                    score_history TEXT DEFAULT '[]',
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_learning_phase BOOLEAN DEFAULT 1,
                    avg_pressure_baseline REAL DEFAULT 0.0,
                    avg_swipe_velocity_baseline REAL DEFAULT 0.0,
                    avg_swipe_duration_baseline REAL DEFAULT 0.0,
                    accel_stability_baseline REAL DEFAULT 0.0,
                    gyro_stability_baseline REAL DEFAULT 0.0,
                    touch_frequency_baseline REAL DEFAULT 0.0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create other required tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    trust_score REAL,
                    is_mirage_active BOOLEAN DEFAULT 0,
                    mirage_activation_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS behavioral_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id INTEGER,
                    avg_pressure REAL NOT NULL,
                    avg_swipe_velocity REAL NOT NULL,
                    avg_swipe_duration REAL NOT NULL,
                    accel_stability REAL NOT NULL,
                    gyro_stability REAL NOT NULL,
                    touch_frequency REAL NOT NULL,
                    trust_score REAL,
                    personal_threshold REAL,
                    mirage_triggered BOOLEAN DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (session_id) REFERENCES user_sessions (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mirage_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id INTEGER,
                    trust_score_trigger REAL NOT NULL,
                    activation_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    deactivation_timestamp DATETIME,
                    duration_seconds INTEGER,
                    fake_transactions_shown INTEGER DEFAULT 0,
                    attacker_interactions INTEGER DEFAULT 0,
                    mirage_effectiveness REAL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (session_id) REFERENCES user_sessions (id)
                )
            ''')
            
            conn.commit()
            
            # Verify manual creation
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            logger.info(f"✅ Manual tables created: {[table[0] for table in tables]}")
        
        conn.close()
        
        # Final verification with SQLAlchemy
        from sqlalchemy import text
        with engine.connect() as sqlalchemy_conn:
            result = sqlalchemy_conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            final_tables = [row[0] for row in result.fetchall()]
            logger.info(f"🎯 Final verification - Available tables: {final_tables}")
        
        if 'users' in final_tables:
            logger.info("🎉 SUCCESS: Database initialized with users table!")
            return True
        else:
            logger.error("❌ FAILED: users table still not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = force_create_database()
    if success:
        print("🎯 NETHRA database successfully initialized!")
        print("✅ Ready to start your backend with: python main.py")
    else:
        print("❌ Database initialization failed!")
