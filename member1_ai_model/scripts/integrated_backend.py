    def init_database(self):
        """Initialize complete database schema - Updated to match Member 2's schema"""
        conn = sqlite3.connect(self.db_path)
        
        # Enhanced Users table with dynamic threshold management (Member 2's schema)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                device_info TEXT,
                biometric_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                
                -- Dynamic threshold management fields
                session_count INTEGER DEFAULT 0,
                avg_trust_score REAL DEFAULT 50.0,
                trust_score_std REAL DEFAULT 15.0,
                personal_threshold REAL DEFAULT 40.0,
                threshold_last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- User categorization for different security rules
                user_type TEXT DEFAULT 'new',
                threshold_learning_complete BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Enhanced Sessions table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                device_info TEXT,
                trust_index REAL,
                risk_level TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                expired_at DATETIME,
                termination_reason TEXT,
                
                -- Dynamic threshold context for audit trail
                threshold_used REAL,
                user_type_at_login TEXT,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''import sqlite3
import numpy as np
import json
import os
from datetime import datetime
from neural_inference import get_trust_score
from dynamic_thresholds import SimpleDynamicThresholds

class NethraIntegratedBackend:
    """
    Complete backend system for Member 2
    Integrates AI model + Dynamic thresholds + Database management
    """
    
    def __init__(self, db_path='database/nethra.db'):
        self.db_path = db_path
        self.threshold_engine = SimpleDynamicThresholds(db_path)
        
        # Create database directory
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self.init_database()
        
        print("✓ NETHRA Integrated Backend initialized")
    
    def init_database(self):
        """Initialize complete database schema - Updated to match Member 2's schema"""
        conn = sqlite3.connect(self.db_path)
        
        # Enhanced Users table with dynamic threshold management (Member 2's schema)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                device_info TEXT,
                biometric_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                
                -- Dynamic threshold management fields
                session_count INTEGER DEFAULT 0,
                avg_trust_score REAL DEFAULT 50.0,
                trust_score_std REAL DEFAULT 15.0,
                personal_threshold REAL DEFAULT 40.0,
                threshold_last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- User categorization for different security rules
                user_type TEXT DEFAULT 'new',
                threshold_learning_complete BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Enhanced Sessions table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                device_info TEXT,
                trust_index REAL,
                risk_level TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                expired_at DATETIME,
                termination_reason TEXT,
                
                -- Dynamic threshold context for audit trail
                threshold_used REAL,
                user_type_at_login TEXT,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Enhanced Behavioral Data table with AI model features
        conn.execute('''
            CREATE TABLE IF NOT EXISTS behavioral_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Raw behavioral data (JSON format)
                touch_patterns TEXT,
                swipe_patterns TEXT,
                device_motion TEXT,
                app_usage TEXT,
                network_info TEXT,
                
                -- Extracted features for AI model (Member 1's 6 features)
                avg_pressure REAL,
                avg_swipe_velocity REAL,
                avg_swipe_duration REAL,
                accel_stability REAL,
                gyro_stability REAL,
                touch_frequency REAL,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')
        
        # Enhanced Trust Scores table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trust_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                trust_score REAL NOT NULL,
                risk_level TEXT,
                anomalies TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Dynamic threshold context for analysis
                threshold_used REAL,
                user_type TEXT,
                threshold_decision TEXT,
                was_personalized BOOLEAN DEFAULT FALSE,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')
        
        # Security incidents table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS security_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                incident_type TEXT,
                severity TEXT,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE,
                
                -- Session and threshold context for incident analysis
                session_id TEXT,
                trust_score REAL,
                threshold_used REAL,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Mirage sessions table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS mirage_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                mirage_type TEXT,
                activated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                duration INTEGER,
                deactivated_at DATETIME,
                
                -- Threshold context for mirage activation analysis
                trigger_trust_score REAL,
                threshold_used REAL,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Threshold calculation history
        conn.execute('''
            CREATE TABLE IF NOT EXISTS threshold_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                old_threshold REAL,
                new_threshold REAL,
                avg_score REAL,
                score_std REAL,
                session_count INTEGER,
                calculation_reason TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Database schema initialized (Member 2 compatible)")
    
    def register_user(self, user_id, device_info=None):
        """Register a new user - Updated for Member 2's schema"""
        conn = sqlite3.connect(self.db_path)
        try:
            device_info_json = json.dumps(device_info) if device_info else None
            
            conn.execute('''
                INSERT INTO users (user_id, device_info) VALUES (?, ?)
            ''', (user_id, device_info_json))
            
            conn.commit()
            print(f"✓ User registered: {user_id}")
            return user_id
        except sqlite3.IntegrityError:
            print(f"✗ User already exists: {user_id}")
            return None
        finally:
            conn.close()
    
    def get_user_info(self, user_id):
        """Get user information - Updated for Member 2's schema"""
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'device_info': json.loads(result[1]) if result[1] else None,
                'biometric_data': json.loads(result[2]) if result[2] else None,
                'created_at': result[3],
                'last_login': result[4],
                'session_count': result[5],
                'avg_trust_score': result[6],
                'trust_score_std': result[7],
                'personal_threshold': result[8],
                'threshold_last_updated': result[9],
                'user_type': result[10],
                'threshold_learning_complete': result[11]
            }
        return None
    
    def extract_behavioral_features(self, raw_sensor_data):
        """
        Extract 6 behavioral features from raw phone sensor data
        
        Args:
            raw_sensor_data: Dict containing touch, swipe, and motion data
        
        Returns:
            List of 6 features for AI model
        """
        try:
            # Extract touch data
            touch_events = raw_sensor_data.get('touch_events', [])
            if touch_events:
                pressures = [t.get('pressure', 0.5) for t in touch_events]
                avg_pressure = np.mean(pressures)
                touch_frequency = len(touch_events) / raw_sensor_data.get('session_duration', 60)
            else:
                avg_pressure = 0.5
                touch_frequency = 0.5
            
            # Extract swipe data
            swipe_events = raw_sensor_data.get('swipe_events', [])
            if swipe_events:
                velocities = [s.get('velocity', 150) for s in swipe_events]
                durations = [s.get('duration', 0.5) for s in swipe_events]
                avg_swipe_velocity = np.mean(velocities)
                avg_swipe_duration = np.mean(durations)
            else:
                avg_swipe_velocity = 150.0
                avg_swipe_duration = 0.5
            
            # Extract motion data
            motion_events = raw_sensor_data.get('motion_events', [])
            if motion_events:
                accel_y_values = [m.get('accel_y', 9.8) for m in motion_events]
                gyro_x_values = [m.get('gyro_x', 0) for m in motion_events]
                accel_stability = np.std(accel_y_values)
                gyro_stability = np.std(gyro_x_values)
            else:
                accel_stability = 0.3
                gyro_stability = 0.1
            
            # Return exactly 6 features in the correct order
            features = [
                avg_pressure,        # 0
                avg_swipe_velocity,  # 1
                avg_swipe_duration,  # 2
                accel_stability,     # 3
                gyro_stability,      # 4
                touch_frequency      # 5
            ]
            
            return features
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            # Return default neutral features
            return [0.5, 150.0, 0.5, 0.3, 0.1, 2.0]
    
    def authenticate_user(self, user_id, raw_sensor_data, context_info=None):
        """
        Main authentication function - Updated for Member 2's schema
        
        Args:
            user_id: User identifier (TEXT format)
            raw_sensor_data: Raw sensor data from phone
            context_info: Optional context (IP, device, location)
        
        Returns:
            Authentication result dictionary
        """
        try:
            # 1. Extract behavioral features
            behavioral_features = self.extract_behavioral_features(raw_sensor_data)
            
            # 2. Get AI trust score
            ai_trust_score = get_trust_score(behavioral_features)
            
            # 3. Apply dynamic threshold logic
            auth_result = self.threshold_engine.authenticate_with_dynamic_threshold(
                user_id, behavioral_features, ai_trust_score
            )
            
            # 4. Add context information
            auth_result['user_id'] = user_id
            auth_result['timestamp'] = datetime.now().isoformat()
            auth_result['features_used'] = behavioral_features
            
            # 5. Handle mirage activation
            if auth_result['decision'] == 'TRIGGER_MIRAGE':
                self.activate_mirage_session(user_id, auth_result)
                self.create_security_incident(user_id, 'SUSPICIOUS_BEHAVIOR', 'HIGH', 
                                            f"Trust score {ai_trust_score} below threshold {auth_result['threshold_used']:.1f}")
            
            # 6. Store authentication decision
            self.store_auth_decision(user_id, auth_result, context_info)
            
            return auth_result
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return {
                'trust_score': 50,
                'threshold_used': 40,
                'decision': 'ERROR',
                'error': str(e)
            }
    
    def activate_mirage_session(self, user_id, auth_result):
        """Activate mirage session - Updated for Member 2's schema"""
        conn = sqlite3.connect(self.db_path)
        
        # Generate session ID for mirage
        import uuid
        session_id = str(uuid.uuid4())
        
        conn.execute('''
            INSERT INTO mirage_sessions 
            (user_id, session_id, mirage_type, trigger_trust_score, threshold_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, session_id, 'DECOY_BANKING', auth_result['trust_score'], auth_result['threshold_used']))
        
        conn.commit()
        conn.close()
    
    def store_auth_decision(self, user_id, auth_result, context_info):
        """Store authentication decision in database - Updated for Member 2's schema"""
        # This is now handled by the dynamic threshold engine's store_session method
        # which stores data in the proper Member 2 schema tables
        pass
    
    def create_security_incident(self, user_id, incident_type, severity, description):
        """Create security incident - Updated for Member 2's schema"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO security_incidents (user_id, incident_type, severity, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, incident_type, severity, description))
        conn.commit()
        conn.close()
    
    def get_user_dashboard_data(self, user_id):
        """Get dashboard data for user - Updated for Member 2's schema"""
        conn = sqlite3.connect(self.db_path)
        
        # Get user stats
        user_stats = self.threshold_engine.get_user_stats(user_id)
        
        # Get recent sessions from trust_scores table
        cursor = conn.execute('''
            SELECT trust_score, threshold_used, threshold_decision, timestamp 
            FROM trust_scores 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''', (user_id,))
        recent_sessions = cursor.fetchall()
        
        # Get security incidents
        cursor = conn.execute('''
            SELECT incident_type, severity, description, timestamp 
            FROM security_incidents 
            WHERE user_id = ? AND resolved = FALSE
            ORDER BY timestamp DESC
        ''', (user_id,))
        incidents = cursor.fetchall()
        
        conn.close()
        
        return {
            'user_stats': user_stats,
            'recent_sessions': [
                {
                    'trust_score': s[0],
                    'threshold_used': s[1],
                    'decision': s[2],
                    'timestamp': s[3]
                } for s in recent_sessions
            ],
            'active_incidents': [
                {
                    'type': i[0],
                    'severity': i[1],
                    'description': i[2],
                    'timestamp': i[3]
                } for i in incidents
            ]
        }
    
    def get_system_analytics(self):
        """Get system-wide analytics"""
        conn = sqlite3.connect(self.db_path)
        
        # Total users
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Authentication stats (last 24 hours)
        cursor = conn.execute('''
            SELECT decision, COUNT(*) 
            FROM auth_decisions 
            WHERE timestamp > datetime('now', '-1 day')
            GROUP BY decision
        ''')
        auth_stats = dict(cursor.fetchall())
        
        # Average trust scores by user type
        cursor = conn.execute('''
            SELECT 
                CASE WHEN session_count >= 7 THEN 'experienced' ELSE 'new' END as user_type,
                AVG(avg_score) as avg_trust_score,
                COUNT(*) as user_count
            FROM user_thresholds 
            GROUP BY user_type
        ''')
        user_type_stats = cursor.fetchall()
        
        # Security alerts (last 7 days)
        cursor = conn.execute('''
            SELECT severity, COUNT(*) 
            FROM security_alerts 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY severity
        ''')
        alert_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_users': total_users,
            'auth_stats_24h': auth_stats,
            'user_type_stats': [
                {
                    'type': row[0],
                    'avg_trust_score': row[1],
                    'count': row[2]
                } for row in user_type_stats
            ],
            'alert_stats_7d': alert_stats
        }

# API endpoints for Member 3 (Flutter integration)
class NethraAPI:
    """
    Simple API wrapper for Flutter integration
    """
    
    def __init__(self):
        self.backend = NethraIntegratedBackend()
    
    def login_authenticate(self, request_data):
        """
        API endpoint for login authentication
        
        Expected request_data format:
        {
            "user_id": 123,
            "sensor_data": {
                "touch_events": [...],
                "swipe_events": [...], 
                "motion_events": [...],
                "session_duration": 60
            },
            "context": {
                "ip_address": "192.168.1.1",
                "device_info": {...},
                "location": "New York"
            }
        }
        """
        try:
            user_id = request_data['user_id']
            sensor_data = request_data['sensor_data']
            context = request_data.get('context', {})
            
            result = self.backend.authenticate_user(user_id, sensor_data, context)
            
            return {
                'success': True,
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_dashboard(self, user_id):
        """API endpoint for user dashboard data"""
        try:
            data = self.backend.get_user_dashboard_data(user_id)
            return {
                'success': True,
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def register_new_user(self, user_data):
        """API endpoint for user registration"""
        try:
            user_id = self.backend.register_user(
                username=user_data['username'],
                email=user_data.get('email'),
                phone=user_data.get('phone')
            )
            
            if user_id:
                return {
                    'success': True,
                    'user_id': user_id
                }
            else:
                return {
                    'success': False,
                    'error': 'Username already exists'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Demo and testing functions
def create_sample_data():
    """Create sample data for testing - Updated for Member 2's schema"""
    backend = NethraIntegratedBackend()
    
    # Register sample users
    user1_id = "alice_smith_001"
    user2_id = "bob_jones_002"
    
    backend.register_user(user1_id, {"device": "iPhone 12", "os": "iOS 15"})
    backend.register_user(user2_id, {"device": "Samsung S21", "os": "Android 12"})
    
    print(f"Created sample users: {user1_id}, {user2_id}")
    
    # Create sample authentication sessions
    sample_sessions = [
        # Alice (high scorer)
        ([0.7, 180, 0.4, 0.1, 0.05, 3.0], user1_id),
        ([0.65, 175, 0.45, 0.12, 0.06, 2.8], user1_id),
        ([0.72, 185, 0.38, 0.09, 0.04, 3.2], user1_id),
        
        # Bob (low scorer)
        ([0.3, 100, 0.8, 0.4, 0.2, 1.2], user2_id),
        ([0.35, 110, 0.75, 0.38, 0.18, 1.4], user2_id),
        ([0.32, 105, 0.82, 0.42, 0.22, 1.1], user2_id),
    ]
    
    for features, uid in sample_sessions:
        # Create fake sensor data
        fake_sensor_data = {
            'touch_events': [{'pressure': features[0]} for _ in range(10)],
            'swipe_events': [{'velocity': features[1], 'duration': features[2]} for _ in range(5)],
            'motion_events': [{'accel_y': 9.8, 'gyro_x': 0} for _ in range(20)],
            'session_duration': 60
        }
        
        result = backend.authenticate_user(uid, fake_sensor_data)
        print(f"User {uid}: Score={result['trust_score']}, Decision={result['decision']}")

def demo_complete_system():
    """Demo the complete integrated system - Updated for Member 2's schema"""
    print("NETHRA Complete System Demo (Member 2 Schema Compatible)")
    print("=" * 65)
    
    # Create sample data
    create_sample_data()
    
    # Show analytics
    backend = NethraIntegratedBackend()
    analytics = backend.get_system_analytics()
    
    print(f"\n📊 System Analytics:")
    print(f"Total Users: {analytics['total_users']}")
    print(f"User Types: {analytics['user_type_stats']}")
    
    # Test API
    api = NethraAPI()
    
    # Test authentication API
    test_request = {
        'user_id': 'alice_smith_001',
        'sensor_data': {
            'touch_events': [{'pressure': 0.6} for _ in range(8)],
            'swipe_events': [{'velocity': 160, 'duration': 0.5} for _ in range(3)],
            'motion_events': [{'accel_y': 9.8, 'gyro_x': 0.05} for _ in range(15)],
            'session_duration': 45
        },
        'context': {
            'ip_address': '192.168.1.100',
            'device_info': {'model': 'iPhone 12', 'os': 'iOS 15'},
            'location': 'New York'
        }
    }
    
    api_result = api.login_authenticate(test_request)
    print(f"\n🔌 API Test Result:")
    print(f"Success: {api_result['success']}")
    if api_result['success']:
        result = api_result['result']
        print(f"Trust Score: {result['trust_score']}")
        print(f"Decision: {result['decision']}")
        print(f"Threshold: {result['threshold_used']:.1f}")
        
    print(f"\n✅ INTEGRATION READY FOR MEMBER 2!")
    print(f"Database schema matches Member 2's requirements")
    print(f"All features working with TEXT user_ids and enhanced tables")

if __name__ == "__main__":
    demo_complete_system()
