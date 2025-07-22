import sqlite3
import os

# Remove any existing database
if os.path.exists('nethra.db'):
    os.remove('nethra.db')

# Create database connection
conn = sqlite3.connect('nethra.db')
cursor = conn.cursor()

# Create users table directly
cursor.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TEXT
);
''')

# Create trust_profiles table
cursor.execute('''
CREATE TABLE trust_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    session_count INTEGER DEFAULT 0,
    average_trust_score REAL DEFAULT 50.0,
    personal_threshold REAL DEFAULT 40.0,
    score_history TEXT DEFAULT '[]',
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
    is_learning_phase INTEGER DEFAULT 1,
    avg_pressure_baseline REAL DEFAULT 0.0,
    avg_swipe_velocity_baseline REAL DEFAULT 0.0,
    avg_swipe_duration_baseline REAL DEFAULT 0.0,
    accel_stability_baseline REAL DEFAULT 0.0,
    gyro_stability_baseline REAL DEFAULT 0.0,
    touch_frequency_baseline REAL DEFAULT 0.0,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
''')

# Create other tables
cursor.execute('''
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    trust_score REAL,
    is_mirage_active INTEGER DEFAULT 0,
    mirage_activation_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
''')

cursor.execute('''
CREATE TABLE behavioral_data (
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
    mirage_triggered INTEGER DEFAULT 0,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
''')

cursor.execute('''
CREATE TABLE mirage_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id INTEGER,
    trust_score_trigger REAL NOT NULL,
    activation_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    deactivation_timestamp TEXT,
    duration_seconds INTEGER,
    fake_transactions_shown INTEGER DEFAULT 0,
    attacker_interactions INTEGER DEFAULT 0,
    mirage_effectiveness REAL,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
''')

conn.commit()

# Verify tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("✅ CREATED TABLES:")
for table in tables:
    print(f"  - {table[0]}")

# Test inserting a user
cursor.execute("INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
               ("test", "test@test.com", "hashed_password_here"))
conn.commit()

cursor.execute("SELECT COUNT(*) FROM users")
count = cursor.fetchone()[0]
print(f"✅ Test user created, total users: {count}")

conn.close()
print("🎯 DATABASE CREATED SUCCESSFULLY!")
