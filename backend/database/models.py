from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import json

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # FIXED RELATIONSHIPS - All properly named:
    mirage_sessions = relationship("MirageSession", back_populates="user")
    trust_profile = relationship("TrustProfile", back_populates="user", uselist=False)
    behavioral_data = relationship("BehavioralData", back_populates="user")
    user_sessions = relationship("UserSession", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")  # Alias for compatibility

class TrustProfile(Base):
    __tablename__ = "trust_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    session_count = Column(Integer, default=0)
    average_trust_score = Column(Float, default=50.0)
    personal_threshold = Column(Float, default=40.0)
    score_history = Column(Text, default="[]")
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_learning_phase = Column(Boolean, default=True)
    
    # Behavioral statistics baselines
    avg_pressure_baseline = Column(Float, default=0.0)
    avg_swipe_velocity_baseline = Column(Float, default=0.0)
    avg_swipe_duration_baseline = Column(Float, default=0.0)
    accel_stability_baseline = Column(Float, default=0.0)
    gyro_stability_baseline = Column(Float, default=0.0)
    touch_frequency_baseline = Column(Float, default=0.0)
    
    user = relationship("User", back_populates="trust_profile")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String, unique=True, nullable=False)
    trust_score = Column(Float, nullable=True)
    is_mirage_active = Column(Boolean, default=False)
    mirage_activation_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=30))
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="user_sessions")

class BehavioralData(Base):
    __tablename__ = "behavioral_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("user_sessions.id"), nullable=True)
    
    # Member 1's 6 behavioral features
    avg_pressure = Column(Float, nullable=False)
    avg_swipe_velocity = Column(Float, nullable=False)
    avg_swipe_duration = Column(Float, nullable=False)
    accel_stability = Column(Float, nullable=False)
    gyro_stability = Column(Float, nullable=False)
    touch_frequency = Column(Float, nullable=False)
    
    # Computed trust analysis
    trust_score = Column(Float, nullable=True)
    personal_threshold = Column(Float, nullable=True)
    mirage_triggered = Column(Boolean, default=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="behavioral_data")

class MirageSession(Base):
    __tablename__ = "mirage_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, nullable=True)
    trust_score_trigger = Column(Float, nullable=False)
    intensity_level = Column(String(20), default="moderate")  # CRITICAL FIELD
    
    # Mirage session tracking
    activation_timestamp = Column(DateTime, default=datetime.utcnow)
    deactivation_timestamp = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    fake_transactions_shown = Column(Integer, default=0)
    attacker_interactions = Column(Integer, default=0)
    mirage_config = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    mirage_effectiveness = Column(Float, nullable=True)
    
    user = relationship("User", back_populates="mirage_sessions")

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    component = Column(String(50), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    request_id = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

class SecurityEvent(Base):
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    trust_score = Column(Float, nullable=True)
    behavioral_data = Column(Text, nullable=True)
    mirage_session_id = Column(Integer, ForeignKey("mirage_sessions.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    
    user = relationship("User")
    mirage_session = relationship("MirageSession")

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    component = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100), nullable=True)
    extra_data = Column(Text, nullable=True)  # FIXED: Changed from 'metadata' to avoid reserved keyword
