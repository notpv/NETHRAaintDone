from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import json

# Import models
from database.models import User, TrustProfile, UserSession, BehavioralData, MirageSession

logger = logging.getLogger(__name__)

# =============================================================================
# USER CRUD OPERATIONS
# =============================================================================

def create_user(db: Session, username: str, email: str, hashed_password: str) -> User:
    """Create a new user"""
    try:
        db_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create initial trust profile for the user
        create_trust_profile(db, db_user.id)
        
        logger.info(f"Created user {username} with ID {db_user.id}")
        return db_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create user {username}: {str(e)}")
        raise

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def update_user_login_attempt(db: Session, user_id: int, success: bool):
    """Update user login attempt tracking"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            if success:
                user.failed_login_attempts = 0
                user.locked_until = None
            else:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            
            db.commit()
            logger.info(f"Updated login attempt for user {user_id}: success={success}")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update login attempt for user {user_id}: {str(e)}")

# =============================================================================
# TRUST PROFILE CRUD OPERATIONS
# =============================================================================

def create_trust_profile(db: Session, user_id: int) -> TrustProfile:
    """Create initial trust profile for new user"""
    try:
        trust_profile = TrustProfile(
            user_id=user_id,
            session_count=0,
            average_trust_score=50.0,
            personal_threshold=40.0,
            score_history="[]",
            is_learning_phase=True
        )
        db.add(trust_profile)
        db.commit()
        db.refresh(trust_profile)
        
        logger.info(f"Created trust profile for user {user_id}")
        return trust_profile
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create trust profile for user {user_id}: {str(e)}")
        raise

def get_trust_profile(db: Session, user_id: int) -> Optional[TrustProfile]:
    """Get trust profile for user"""
    return db.query(TrustProfile).filter(TrustProfile.user_id == user_id).first()

def update_trust_profile(
    db: Session, 
    user_id: int, 
    trust_score: float,
    behavioral_data: Dict[str, float]
) -> TrustProfile:
    """Update user's trust profile with new trust score and behavioral data"""
    try:
        profile = get_trust_profile(db, user_id)
        if not profile:
            profile = create_trust_profile(db, user_id)
        
        # Update session count
        profile.session_count += 1
        
        # Update score history
        score_history = json.loads(profile.score_history or "[]")
        score_history.append({
            "score": trust_score,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 50 scores
        if len(score_history) > 50:
            score_history = score_history[-50:]
        
        profile.score_history = json.dumps(score_history)
        
        # Update average trust score
        scores = [entry["score"] for entry in score_history]
        profile.average_trust_score = sum(scores) / len(scores)
        
        # Update behavioral baselines
        profile.avg_pressure_baseline = behavioral_data.get("avg_pressure", 0.0)
        profile.avg_swipe_velocity_baseline = behavioral_data.get("avg_swipe_velocity", 0.0)
        profile.avg_swipe_duration_baseline = behavioral_data.get("avg_swipe_duration", 0.0)
        profile.accel_stability_baseline = behavioral_data.get("accel_stability", 0.0)
        profile.gyro_stability_baseline = behavioral_data.get("gyro_stability", 0.0)
        profile.touch_frequency_baseline = behavioral_data.get("touch_frequency", 0.0)
        
        # Update learning phase status (need 10+ sessions to establish baseline)
        profile.is_learning_phase = profile.session_count < 10
        
        # Update personal threshold based on user's behavioral patterns
        if profile.session_count >= 5:
            # Adjust threshold based on user's average score
            if profile.average_trust_score > 70:
                profile.personal_threshold = 50.0  # Higher threshold for consistent users
            elif profile.average_trust_score < 40:
                profile.personal_threshold = 25.0  # Lower threshold for inconsistent users
            else:
                profile.personal_threshold = 40.0  # Default threshold
        
        profile.last_updated = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Updated trust profile for user {user_id}")
        logger.info(f"  Session count: {profile.session_count}")
        logger.info(f"  Average score: {profile.average_trust_score:.2f}")
        logger.info(f"  Personal threshold: {profile.personal_threshold:.2f}")
        
        return profile
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update trust profile for user {user_id}: {str(e)}")
        raise

# =============================================================================
# BEHAVIORAL DATA CRUD OPERATIONS
# =============================================================================

def store_behavioral_data(
    db: Session,
    user_id: int,
    session_id: Optional[int],
    behavioral_data: Dict[str, float],
    trust_score: float,
    mirage_triggered: bool = False
):
    """Store behavioral data and trust score"""
    try:
        behavior_record = BehavioralData(
            user_id=user_id,
            session_id=session_id,
            avg_pressure=behavioral_data.get("avg_pressure", 0.0),
            avg_swipe_velocity=behavioral_data.get("avg_swipe_velocity", 0.0),
            avg_swipe_duration=behavioral_data.get("avg_swipe_duration", 0.0),
            accel_stability=behavioral_data.get("accel_stability", 0.0),
            gyro_stability=behavioral_data.get("gyro_stability", 0.0),
            touch_frequency=behavioral_data.get("touch_frequency", 0.0),
            trust_score=trust_score,
            mirage_triggered=mirage_triggered,
            timestamp=datetime.utcnow()
        )
        
        db.add(behavior_record)
        db.commit()
        db.refresh(behavior_record)
        
        logger.info(f"Stored behavioral data for user {user_id}")
        return behavior_record
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store behavioral data for user {user_id}: {str(e)}")
        raise

def get_user_trust_history(db: Session, user_id: int, limit: int = 20) -> List[BehavioralData]:
    """Get user's trust score history"""
    return db.query(BehavioralData)\
        .filter(BehavioralData.user_id == user_id)\
        .order_by(desc(BehavioralData.timestamp))\
        .limit(limit)\
        .all()

def get_behavioral_statistics(db: Session, user_id: int, days: int = 7) -> Dict[str, Any]:
    """Get behavioral statistics for user over specified days"""
    try:
        since_date = datetime.utcnow() - timedelta(days=days)
        
        records = db.query(BehavioralData)\
            .filter(
                BehavioralData.user_id == user_id,
                BehavioralData.timestamp >= since_date
            )\
            .all()
        
        if not records:
            return {"status": "no_data", "message": "No behavioral data found"}
        
        # Calculate statistics
        trust_scores = [r.trust_score for r in records if r.trust_score is not None]
        mirage_triggers = sum(1 for r in records if r.mirage_triggered)
        
        return {
            "total_sessions": len(records),
            "average_trust_score": sum(trust_scores) / len(trust_scores) if trust_scores else 0,
            "min_trust_score": min(trust_scores) if trust_scores else 0,
            "max_trust_score": max(trust_scores) if trust_scores else 0,
            "mirage_activation_rate": (mirage_triggers / len(records)) * 100 if records else 0,
            "days_analyzed": days
        }
        
    except Exception as e:
        logger.error(f"Failed to get behavioral statistics for user {user_id}: {str(e)}")
        return {"status": "error", "error": str(e)}

# =============================================================================
# MIRAGE SESSION CRUD OPERATIONS
# =============================================================================

def create_mirage_session(
    db: Session,
    user_id: int,
    session_id: Optional[int],
    trust_score_trigger: float,
    intensity_level: str = "moderate",  # RESTORED: Database column exists
    mirage_config: Optional[Dict[str, Any]] = None
) -> MirageSession:
    """Create a new mirage session record"""
    try:
        mirage_session = MirageSession(
            user_id=user_id,
            session_id=session_id,
            trust_score_trigger=trust_score_trigger,
            intensity_level=intensity_level,  # RESTORED: Database column exists
            activation_timestamp=datetime.utcnow(),
            fake_transactions_shown=0,
            attacker_interactions=0,
            is_active=True
        )
        
        # Store mirage configuration if provided
        if mirage_config:
            mirage_session.mirage_config = json.dumps(mirage_config)
        
        db.add(mirage_session)
        db.commit()
        db.refresh(mirage_session)
        
        logger.warning(f"🎭 Created mirage session {mirage_session.id} for user {user_id}")
        logger.info(f"   Trust score trigger: {trust_score_trigger}")
        logger.info(f"   Intensity level: {intensity_level}")  # RESTORED
        
        return mirage_session
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create mirage session for user {user_id}: {str(e)}")
        raise

def get_active_mirage_session(db: Session, user_id: int) -> Optional[MirageSession]:
    """Get active mirage session for user"""
    return db.query(MirageSession).filter(
        MirageSession.user_id == user_id,
        MirageSession.is_active == True
    ).first()

def update_mirage_interaction(db: Session, mirage_session_id: int, interaction_type: str = "view"):
    """Update mirage session interaction counters"""
    try:
        session = db.query(MirageSession).filter(MirageSession.id == mirage_session_id).first()
        if session:
            if interaction_type == "transaction":
                session.fake_transactions_shown += 1
            else:
                session.attacker_interactions += 1
            
            db.commit()
            logger.info(f"Updated mirage interaction for session {mirage_session_id}: {interaction_type}")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update mirage interaction: {str(e)}")

def deactivate_mirage_session(db: Session, user_id: int) -> Optional[MirageSession]:
    """Deactivate mirage session for user"""
    try:
        session = get_active_mirage_session(db, user_id)
        if session:
            session.is_active = False
            session.deactivation_timestamp = datetime.utcnow()
            
            # Calculate duration
            if session.activation_timestamp:
                duration = datetime.utcnow() - session.activation_timestamp
                session.duration_seconds = int(duration.total_seconds())
            
            db.commit()
            db.refresh(session)
            
            logger.info(f"🎭 Deactivated mirage session {session.id} for user {user_id}")
            return session
        
        return None
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to deactivate mirage session for user {user_id}: {str(e)}")
        return None

def get_mirage_session_history(db: Session, user_id: int, limit: int = 10) -> List[MirageSession]:
    """Get mirage session history for user"""
    return db.query(MirageSession)\
        .filter(MirageSession.user_id == user_id)\
        .order_by(desc(MirageSession.activation_timestamp))\
        .limit(limit)\
        .all()

def get_mirage_effectiveness_metrics(db: Session, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Get mirage effectiveness metrics - RESTORED intensity_level functionality"""
    try:
        query = db.query(MirageSession)
        if user_id:
            query = query.filter(MirageSession.user_id == user_id)
        
        sessions = query.all()
        
        if not sessions:
            return {"status": "no_data", "message": "No mirage sessions found"}
        
        total_sessions = len(sessions)
        avg_duration = sum(s.duration_seconds or 0 for s in sessions) / total_sessions
        avg_interactions = sum(s.attacker_interactions or 0 for s in sessions) / total_sessions
        avg_fake_transactions = sum(s.fake_transactions_shown or 0 for s in sessions) / total_sessions
        
        # RESTORED: intensity breakdown using database field
        intensity_breakdown = {}
        for session in sessions:
            intensity = session.intensity_level or "unknown"  # RESTORED: Now reads from database
            intensity_breakdown[intensity] = intensity_breakdown.get(intensity, 0) + 1
        
        return {
            "total_mirage_sessions": total_sessions,
            "average_duration_seconds": int(avg_duration),
            "average_attacker_interactions": avg_interactions,
            "average_fake_transactions_shown": avg_fake_transactions,
            "intensity_level_breakdown": intensity_breakdown,
            "effectiveness_score": min(avg_interactions * 10, 100)  # Simple effectiveness metric
        }
        
    except Exception as e:
        logger.error(f"Failed to get mirage effectiveness metrics: {str(e)}")
        return {"status": "error", "error": str(e)}

# =============================================================================
# USER SESSION CRUD OPERATIONS  
# =============================================================================

def create_user_session(
    db: Session,
    user_id: int,
    session_token: str,
    expires_at: datetime
) -> UserSession:
    """Create a new user session"""
    try:
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            is_active=True
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Created session {session_token} for user {user_id}")
        return session
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create session for user {user_id}: {str(e)}")
        raise

def create_session(
    db: Session, 
    user_id: int, 
    session_token: str, 
    expires_at: datetime,
    trust_score: Optional[float] = None
) -> UserSession:
    """Create a new user session - Alternative name for create_user_session"""
    return create_user_session(db, user_id, session_token, expires_at)

def get_user_session(db: Session, session_token: str) -> Optional[UserSession]:
    """Get user session by token"""
    return db.query(UserSession)\
        .filter(UserSession.session_token == session_token)\
        .first()

def get_active_session(db: Session, session_token: str) -> Optional[UserSession]:
    """Get active session by token - Alternative name for get_user_session"""
    session = get_user_session(db, session_token)
    if session and session.is_active and session.expires_at > datetime.utcnow():
        return session
    return None

def update_session_activity(db: Session, session_token: str, trust_score: Optional[float] = None):
    """Update session last activity timestamp"""
    try:
        session = get_user_session(db, session_token)
        if session:
            session.last_activity = datetime.utcnow()
            if trust_score is not None:
                session.trust_score = trust_score
            
            db.commit()
            logger.info(f"Updated activity for session {session_token}")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update session activity: {str(e)}")

def deactivate_user_session(db: Session, session_token: str):
    """Deactivate user session"""
    try:
        session = get_user_session(db, session_token)
        if session:
            session.is_active = False
            db.commit()
            logger.info(f"Deactivated session {session_token}")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to deactivate session: {str(e)}")

# =============================================================================
# CLEANUP AND MAINTENANCE
# =============================================================================

def cleanup_expired_sessions(db: Session):
    """Remove expired sessions"""
    try:
        expired_count = db.query(UserSession)\
            .filter(UserSession.expires_at < datetime.utcnow())\
            .delete()
        
        db.commit()
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired sessions")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cleanup expired sessions: {str(e)}")

def get_system_statistics(db: Session) -> Dict[str, Any]:
    """Get overall system statistics"""
    try:
        total_users = db.query(User).count()
        active_sessions = db.query(UserSession)\
            .filter(UserSession.is_active == True)\
            .count()
        total_behavioral_records = db.query(BehavioralData).count()
        active_mirage_sessions = db.query(MirageSession)\
            .filter(MirageSession.is_active == True)\
            .count()
        
        return {
            "total_users": total_users,
            "active_sessions": active_sessions,
            "behavioral_records": total_behavioral_records,
            "active_mirage_sessions": active_mirage_sessions,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system statistics: {str(e)}")
        return {"status": "error", "error": str(e)}
