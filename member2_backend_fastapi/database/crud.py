from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from datetime import datetime, timedelta
import logging
from .models import User, Session as UserSession, TrustProfile, TrustScore, TamperEvent, MirageEvent, SystemLog
from passlib.context import CryptContext
import statistics

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCRUD:
    """CRUD operations for User model"""
    
    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str, **kwargs) -> User:
        """Create a new user"""
        hashed_password = pwd_context.hash(password)
        
        db_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            **kwargs
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create initial trust profile
        TrustProfileCRUD.create_trust_profile(db, db_user.id)
        
        logger.info(f"Created new user: {username} (ID: {db_user.id})")
        return db_user
    
    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/password"""
        user = UserCRUD.get_user_by_username(db, username)
        
        if not user:
            return None
        
        if user.is_locked():
            logger.warning(f"Login attempt for locked user: {username}")
            return None
        
        if not pwd_context.verify(password, user.hashed_password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                logger.warning(f"User account locked due to failed login attempts: {username}")
            
            db.commit()
            return None
        
        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        user.locked_until = None
        db.commit()
        
        return user
    
    @staticmethod
    def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
        """Update user information"""
        user = UserCRUD.get_user(db, user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_stats(db: Session, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        user = UserCRUD.get_user(db, user_id)
        if not user:
            return {}
        
        # Get session stats
        total_sessions = db.query(UserSession).filter(UserSession.user_id == user_id).count()
        active_sessions = db.query(UserSession).filter(
            and_(UserSession.user_id == user_id, UserSession.is_active == True)
        ).count()
        
        # Get trust score stats
        trust_scores = db.query(TrustScore).filter(TrustScore.user_id == user_id).all()
        avg_trust_score = statistics.mean([ts.trust_score for ts in trust_scores]) if trust_scores else 0
        
        # Get security events
        tamper_events = db.query(TamperEvent).filter(TamperEvent.user_id == user_id).count()
        mirage_events = db.query(MirageEvent).filter(MirageEvent.user_id == user_id).count()
        
        return {
            "user_id": user_id,
            "username": user.username,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "avg_trust_score": round(avg_trust_score, 2),
            "total_trust_scores": len(trust_scores),
            "tamper_events": tamper_events,
            "mirage_events": mirage_events,
            "account_age_days": (datetime.utcnow() - user.created_at).days,
            "last_login": user.last_login
        }

class SessionCRUD:
    """CRUD operations for Session model"""
    
    @staticmethod
    def create_session(db: Session, user_id: int, **kwargs) -> UserSession:
        """Create a new user session"""
        session = UserSession(
            user_id=user_id,
            **kwargs
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Created new session for user {user_id}: {session.session_uuid}")
        return session
    
    @staticmethod
    def get_session(db: Session, session_id: int) -> Optional[UserSession]:
        """Get session by ID"""
        return db.query(UserSession).filter(UserSession.id == session_id).first()
    
    @staticmethod
    def get_active_sessions(db: Session, user_id: int) -> List[UserSession]:
        """Get all active sessions for a user"""
        return db.query(UserSession).filter(
            and_(UserSession.user_id == user_id, UserSession.is_active == True)
        ).all()
    
    @staticmethod
    def update_session_activity(db: Session, session_id: int) -> Optional[UserSession]:
        """Update session last activity"""
        session = SessionCRUD.get_session(db, session_id)
        if session:
            session.update_activity()
            db.commit()
            db.refresh(session)
        return session
    
    @staticmethod
    def end_session(db: Session, session_id: int, reason: str = "user_logout") -> Optional[UserSession]:
        """End a user session"""
        session = SessionCRUD.get_session(db, session_id)
        if session:
            session.is_active = False
            session.session_end = datetime.utcnow()
            session.logout_reason = reason
            db.commit()
            db.refresh(session)
            logger.info(f"Ended session {session.session_uuid}: {reason}")
        return session
    
    @staticmethod
    def cleanup_expired_sessions(db: Session, timeout_minutes: int = 10) -> int:
        """Clean up expired sessions"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        expired_sessions = db.query(UserSession).filter(
            and_(
                UserSession.is_active == True,
                UserSession.last_activity < cutoff_time
            )
        ).all()
        
        count = 0
        for session in expired_sessions:
            session.is_active = False
            session.session_end = datetime.utcnow()
            session.logout_reason = "timeout"
            count += 1
        
        db.commit()
        logger.info(f"Cleaned up {count} expired sessions")
        return count

class TrustProfileCRUD:
    """CRUD operations for TrustProfile model"""
    
    @staticmethod
    def create_trust_profile(db: Session, user_id: int) -> TrustProfile:
        """Create initial trust profile for user"""
        trust_profile = TrustProfile(
            user_id=user_id,
            personal_threshold=40.0,  # Default threshold
            sessions_count=0,
            learning_complete=False,
            risk_level='low'
        )
        
        db.add(trust_profile)
        db.commit()
        db.refresh(trust_profile)
        
        logger.info(f"Created trust profile for user {user_id}")
        return trust_profile
    
    @staticmethod
    def get_trust_profile(db: Session, user_id: int) -> Optional[TrustProfile]:
        """Get trust profile for user"""
        return db.query(TrustProfile).filter(TrustProfile.user_id == user_id).first()
    
    @staticmethod
    def update_trust_profile(db: Session, user_id: int, trust_scores: List[float]) -> Optional[TrustProfile]:
        """Update trust profile with new statistics"""
        profile = TrustProfileCRUD.get_trust_profile(db, user_id)
        if not profile:
            return None
        
        if len(trust_scores) < 2:
            return profile
        
        # Calculate statistics
        profile.avg_trust_score = statistics.mean(trust_scores)
        profile.stddev_trust_score = statistics.stdev(trust_scores)
        profile.median_trust_score = statistics.median(trust_scores)
        profile.min_trust_score = min(trust_scores)
        profile.max_trust_score = max(trust_scores)
        
        # Calculate dynamic threshold (mean - 1.5 * std_dev)
        if profile.stddev_trust_score > 0:
            profile.personal_threshold = max(
                profile.avg_trust_score - (1.5 * profile.stddev_trust_score),
                10.0  # Minimum threshold
            )
        else:
            profile.personal_threshold = profile.avg_trust_score * 0.8
        
        # Update learning status
        profile.sessions_count = len(trust_scores)
        profile.learning_complete = len(trust_scores) >= 5
        profile.last_recalculated = datetime.utcnow()
        
        # Determine risk level
        if profile.stddev_trust_score > 15:
            profile.risk_level = 'high'
        elif profile.stddev_trust_score > 8:
            profile.risk_level = 'medium'
        else:
            profile.risk_level = 'low'
        
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Updated trust profile for user {user_id}: threshold={profile.personal_threshold:.2f}")
        return profile

class TrustScoreCRUD:
    """CRUD operations for TrustScore model"""
    
    @staticmethod
    def create_trust_score(db: Session, user_id: int, session_id: int, trust_score: float, **kwargs) -> TrustScore:
        """Create a new trust score record"""
        score_record = TrustScore(
            user_id=user_id,
            session_id=session_id,
            trust_score=trust_score,
            **kwargs
        )
        
        db.add(score_record)
        db.commit()
        db.refresh(score_record)
        
        return score_record
    
    @staticmethod
    def get_user_trust_scores(db: Session, user_id: int, limit: int = 100) -> List[TrustScore]:
        """Get recent trust scores for user"""
        return db.query(TrustScore).filter(
            TrustScore.user_id == user_id
        ).order_by(desc(TrustScore.timestamp)).limit(limit).all()
    
    @staticmethod
    def get_session_trust_scores(db: Session, session_id: int) -> List[TrustScore]:
        """Get all trust scores for a session"""
        return db.query(TrustScore).filter(
            TrustScore.session_id == session_id
        ).order_by(TrustScore.timestamp).all()
    
    @staticmethod
    def get_trust_score_analytics(db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get trust score analytics for user"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        scores = db.query(TrustScore).filter(
            and_(
                TrustScore.user_id == user_id,
                TrustScore.timestamp >= cutoff_date
            )
        ).all()
        
        if not scores:
            return {
                "total_scores": 0,
                "avg_score": 0,
                "trend": "insufficient_data"
            }
        
        score_values = [s.trust_score for s in scores]
        
        # Calculate trend (comparing first and last quarter)
        quarter_size = len(score_values) // 4
        if quarter_size > 0:
            early_avg = statistics.mean(score_values[:quarter_size])
            recent_avg = statistics.mean(score_values[-quarter_size:])
            
            if recent_avg > early_avg + 5:
                trend = "improving"
            elif recent_avg < early_avg - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "total_scores": len(scores),
            "avg_score": statistics.mean(score_values),
            "min_score": min(score_values),
            "max_score": max(score_values),
            "std_dev": statistics.stdev(score_values) if len(score_values) > 1 else 0,
            "trend": trend,
            "scores_below_threshold": len([s for s in scores if s.threshold_breached]),
            "mirage_triggers": len([s for s in scores if s.action_taken == 'mirage'])
        }

class TamperEventCRUD:
    """CRUD operations for TamperEvent model"""
    
    @staticmethod
    def create_tamper_event(db: Session, user_id: int, event_type: str, **kwargs) -> TamperEvent:
        """Create a new tamper event"""
        event = TamperEvent(
            user_id=user_id,
            event_type=event_type,
            **kwargs
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        logger.warning(f"Tamper event detected for user {user_id}: {event_type}")
        return event
    
    @staticmethod
    def get_tamper_events(db: Session, user_id: int = None, limit: int = 100) -> List[TamperEvent]:
        """Get tamper events, optionally filtered by user"""
        query = db.query(TamperEvent)
        
        if user_id:
            query = query.filter(TamperEvent.user_id == user_id)
        
        return query.order_by(desc(TamperEvent.detected_at)).limit(limit).all()

class MirageEventCRUD:
    """CRUD operations for MirageEvent model"""
    
    @staticmethod
    def create_mirage_event(db: Session, user_id: int, session_id: int, **kwargs) -> MirageEvent:
        """Create a new mirage event"""
        event = MirageEvent(
            user_id=user_id,
            session_id=session_id,
            **kwargs
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        logger.info(f"Mirage event created for user {user_id}: {kwargs.get('mirage_type', 'unknown')}")
        return event
    
    @staticmethod
    def end_mirage_event(db: Session, event_id: int, successful: bool = False) -> Optional[MirageEvent]:
        """End a mirage event"""
        event = db.query(MirageEvent).filter(MirageEvent.id == event_id).first()
        
        if event:
            event.ended_at = datetime.utcnow()
            event.mirage_successful = successful
            
            if event.triggered_at:
                duration = (datetime.utcnow() - event.triggered_at).total_seconds()
                event.mirage_duration_seconds = duration
            
            db.commit()
            db.refresh(event)
        
        return event
    
    @staticmethod
    def get_mirage_analytics(db: Session, days: int = 30) -> Dict[str, Any]:
        """Get mirage system analytics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        events = db.query(MirageEvent).filter(
            MirageEvent.triggered_at >= cutoff_date
        ).all()
        
        if not events:
            return {"total_events": 0, "success_rate": 0}
        
        successful_events = [e for e in events if e.mirage_successful]
        false_positives = [e for e in events if e.legitimate_user_affected]
        
        return {
            "total_events": len(events),
            "successful_events": len(successful_events),
            "success_rate": len(successful_events) / len(events) * 100,
            "false_positive_rate": len(false_positives) / len(events) * 100,
            "avg_duration": statistics.mean([e.mirage_duration_seconds for e in events if e.mirage_duration_seconds]),
            "most_common_trigger": max(set([e.trigger_reason for e in events]), key=[e.trigger_reason for e in events].count) if events else None
        }

class SystemLogCRUD:
    """CRUD operations for SystemLog model"""
    
    @staticmethod
    def create_log(db: Session, level: str, message: str, **kwargs) -> SystemLog:
        """Create a system log entry"""
        log_entry = SystemLog(
            level=level,
            message=message,
            **kwargs
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        return log_entry
    
    @staticmethod
    def get_recent_logs(db: Session, level: str = None, hours: int = 24, limit: int = 1000) -> List[SystemLog]:
        """Get recent system logs"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = db.query(SystemLog).filter(SystemLog.timestamp >= cutoff_time)
        
        if level:
            query = query.filter(SystemLog.level == level)
        
        return query.order_by(desc(SystemLog.timestamp)).limit(limit).all()

# Utility functions for database analytics
def get_system_health(db: Session) -> Dict[str, Any]:
    """Get overall system health metrics"""
    # Active users in last 24 hours
    day_ago = datetime.utcnow() - timedelta(days=1)
    active_users = db.query(User).filter(User.last_login >= day_ago).count()
    
    # Active sessions
    active_sessions = db.query(UserSession).filter(UserSession.is_active == True).count()
    
    # Recent trust scores
    recent_scores = db.query(TrustScore).filter(TrustScore.timestamp >= day_ago).count()
    
    # Security events
    recent_tamper_events = db.query(TamperEvent).filter(TamperEvent.detected_at >= day_ago).count()
    recent_mirage_events = db.query(MirageEvent).filter(MirageEvent.triggered_at >= day_ago).count()
    
    # Error logs
    recent_errors = db.query(SystemLog).filter(
        and_(SystemLog.timestamp >= day_ago, SystemLog.level == 'ERROR')
    ).count()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "active_users_24h": active_users,
        "active_sessions": active_sessions,
        "trust_scores_24h": recent_scores,
        "tamper_events_24h": recent_tamper_events,
        "mirage_events_24h": recent_mirage_events,
        "error_logs_24h": recent_errors,
        "system_status": "healthy" if recent_errors < 10 else "warning"
    }
