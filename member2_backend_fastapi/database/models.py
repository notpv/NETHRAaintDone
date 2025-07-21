from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import uuid
from .database import Base

class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    
    # Profile information
    full_name = Column(String(100))
    phone_number = Column(String(20))
    date_of_birth = Column(DateTime)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Device information
    device_id = Column(String(100))
    device_model = Column(String(50))
    os_version = Column(String(20))
    app_version = Column(String(20))
    
    # Privacy settings
    data_sharing_consent = Column(Boolean, default=False)
    analytics_consent = Column(Boolean, default=False)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    trust_profile = relationship("TrustProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    trust_scores = relationship("TrustScore", back_populates="user", cascade="all, delete-orphan")
    tamper_events = relationship("TamperEvent", back_populates="user", cascade="all, delete-orphan")
    mirage_events = relationship("MirageEvent", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
    
    def is_locked(self) -> bool:
        """Check if user account is locked"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

class Session(Base):
    """Session model for tracking user sessions"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session timing
    session_start = Column(DateTime, default=datetime.utcnow)
    session_end = Column(DateTime)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Session status
    is_active = Column(Boolean, default=True)
    logout_reason = Column(String(50))  # 'user_logout', 'timeout', 'security', 'tamper'
    
    # Session security
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    geolocation = Column(String(100))
    
    # Trust metrics for this session
    initial_trust_score = Column(Float)
    current_trust_score = Column(Float)
    min_trust_score = Column(Float)
    max_trust_score = Column(Float)
    trust_score_variance = Column(Float)
    
    # Behavioral flags
    mirage_triggered = Column(Boolean, default=False)
    mirage_trigger_count = Column(Integer, default=0)
    suspicious_activity_count = Column(Integer, default=0)
    
    # Device information
    device_fingerprint = Column(String(128))
    screen_resolution = Column(String(20))
    timezone = Column(String(50))
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    trust_scores = relationship("TrustScore", back_populates="session", cascade="all, delete-orphan")
    mirage_events = relationship("MirageEvent", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    def is_expired(self, timeout_minutes: int = 10) -> bool:
        """Check if session has expired due to inactivity"""
        if not self.last_activity:
            return True
        expire_time = self.last_activity + timedelta(minutes=timeout_minutes)
        return datetime.utcnow() > expire_time
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()

class TrustProfile(Base):
    """Trust profile model for storing user's behavioral baseline"""
    __tablename__ = "trust_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Statistical measures
    avg_trust_score = Column(Float)
    stddev_trust_score = Column(Float)
    median_trust_score = Column(Float)
    min_trust_score = Column(Float)
    max_trust_score = Column(Float)
    
    # Dynamic threshold
    personal_threshold = Column(Float)
    threshold_confidence = Column(Float)  # How confident we are in this threshold
    
    # Learning progress
    sessions_count = Column(Integer, default=0)
    total_trust_scores = Column(Integer, default=0)
    learning_complete = Column(Boolean, default=False)
    
    # Behavioral patterns
    dominant_interaction_pattern = Column(String(50))  # 'gentle', 'firm', 'erratic'
    preferred_hand = Column(String(10))  # 'left', 'right', 'both'
    avg_session_duration = Column(Float)  # in minutes
    typical_usage_hours = Column(String(100))  # JSON string of typical hours
    
    # Risk assessment
    risk_level = Column(String(20), default='low')  # 'low', 'medium', 'high'
    anomaly_sensitivity = Column(Float, default=0.8)  # 0-1, how sensitive to anomalies
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_recalculated = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="trust_profile")
    
    def __repr__(self):
        return f"<TrustProfile(user_id={self.user_id}, threshold={self.personal_threshold})>"
    
    def needs_recalculation(self) -> bool:
        """Check if trust profile needs recalculation"""
        if not self.last_recalculated:
            return True
        
        # Recalculate every 100 new scores or weekly
        time_threshold = self.last_recalculated + timedelta(days=7)
        return (self.sessions_count % 10 == 0) or (datetime.utcnow() > time_threshold)

class TrustScore(Base):
    """Trust score model for individual predictions"""
    __tablename__ = "trust_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    
    # Score details
    trust_score = Column(Float, nullable=False)
    confidence_score = Column(Float)  # Model's confidence in this prediction
    raw_prediction = Column(Float)  # Before any normalization
    
    # Model information
    model_version = Column(String(20), default="1.0.0")
    preprocessing_version = Column(String(20), default="1.0.0")
    inference_time_ms = Column(Float)
    
    # Input features summary (for debugging)
    feature_count = Column(Integer)
    feature_hash = Column(String(64))  # Hash of input features
    input_data_quality = Column(Float)  # 0-1, quality of input data
    
    # Context
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    timezone = Column(String(50))
    
    # Behavioral context
    interaction_type = Column(String(30))  # 'login', 'transaction', 'navigation'
    duration_since_last_score = Column(Float)  # seconds
    
    # Decision made
    threshold_used = Column(Float)
    threshold_breached = Column(Boolean)
    action_taken = Column(String(30))  # 'allow', 'challenge', 'deny', 'mirage'
    
    # Relationships
    user = relationship("User", back_populates="trust_scores")
    session = relationship("Session", back_populates="trust_scores")
    
    __table_args__ = (
        Index('idx_trust_scores_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_trust_scores_session', 'session_id'),
        Index('idx_trust_scores_threshold_breach', 'threshold_breached', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<TrustScore(id={self.id}, score={self.trust_score}, user_id={self.user_id})>"

class TamperEvent(Base):
    """Tamper event model for security incidents"""
    __tablename__ = "tamper_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # 'root_detection', 'debug_mode', 'emulator', etc.
    severity = Column(String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    description = Column(Text)
    
    # Technical details
    detection_method = Column(String(50))
    system_info = Column(Text)  # JSON string with system information
    stack_trace = Column(Text)
    
    # Response
    action_taken = Column(String(50))  # 'logged', 'session_terminated', 'account_locked'
    resolved = Column(Boolean, default=False)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Context
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="tamper_events")
    
    def __repr__(self):
        return f"<TamperEvent(id={self.id}, type='{self.event_type}', severity='{self.severity}')>"

class MirageEvent(Base):
    """Mirage event model for tracking deception interface usage"""
    __tablename__ = "mirage_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    
    # Trigger details
    trigger_reason = Column(String(100))  # 'low_trust_score', 'suspicious_pattern', 'tamper_detected'
    trust_score_at_trigger = Column(Float)
    threshold_at_trigger = Column(Float)
    
    # Mirage configuration
    mirage_type = Column(String(50))  # 'fake_balance', 'fake_transactions', 'slow_response'
    mirage_duration_seconds = Column(Float)
    mirage_intensity = Column(String(20))  # 'subtle', 'moderate', 'aggressive'
    
    # User interaction during mirage
    interactions_count = Column(Integer, default=0)
    failed_challenge_attempts = Column(Integer, default=0)
    time_to_exit = Column(Float)  # seconds until user gave up or left
    
    # Outcome
    mirage_successful = Column(Boolean)  # Did it successfully deter the attacker?
    user_frustrated = Column(Boolean)  # Signs of user frustration
    legitimate_user_affected = Column(Boolean)  # Was this a false positive?
    
    # Timestamps
    triggered_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    
    # Additional context
    cognitive_challenge_presented = Column(Boolean, default=False)
    challenge_type = Column(String(50))
    challenge_passed = Column(Boolean)
    
    # Relationships
    user = relationship("User", back_populates="mirage_events")
    session = relationship("Session", back_populates="mirage_events")
    
    def __repr__(self):
        return f"<MirageEvent(id={self.id}, type='{self.mirage_type}', successful={self.mirage_successful})>"

class SystemLog(Base):
    """System log model for general application logging"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Log details
    level = Column(String(20), nullable=False)  # 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    message = Column(Text, nullable=False)
    module = Column(String(50))  # Which module generated the log
    function = Column(String(50))  # Which function generated the log
    
    # Context
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String(36))
    request_id = Column(String(36))
    
    # Technical details
    exception_type = Column(String(100))
    stack_trace = Column(Text)
    additional_data = Column(Text)  # JSON string with additional context
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level='{self.level}', message='{self.message[:50]}...')>"

# Performance monitoring table
class PerformanceMetric(Base):
    """Performance metrics for monitoring system health"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Metric details
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))  # 'ms', 'seconds', 'count', 'percentage'
    
    # Context
    endpoint = Column(String(100))
    method = Column(String(10))  # HTTP method
    status_code = Column(Integer)
    user_id = Column(Integer)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_performance_metric_name_timestamp', 'metric_name', 'timestamp'),
        Index('idx_performance_endpoint', 'endpoint', 'timestamp'),
    )
