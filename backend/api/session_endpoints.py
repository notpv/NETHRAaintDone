from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import secrets

# Database imports
from database.database import get_db
from database.models import User, UserSession

# Auth imports
from api.auth_endpoints import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class SessionCreateRequest(BaseModel):
    """Optional request model for session creation"""
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device metadata")

class SessionResponse(BaseModel):
    """Response model for session operations"""
    session_id: int
    session_token: str
    created_at: str
    expires_at: str
    last_activity: str
    is_active: bool
    user_id: int
    message: str

# =============================================================================
# DATABASE CRUD FUNCTIONS (FIXED)
# =============================================================================

def create_user_session_db(
    db: Session, 
    user_id: int, 
    session_token: str, 
    expires_at: datetime
) -> UserSession:
    """Create new user session in database - FIXED VERSION"""
    try:
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            expires_at=expires_at,  # FIXED: Now properly included
            is_active=True,
            trust_score=None,
            is_mirage_active=False,
            mirage_activation_count=0
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"✅ Session created successfully: {session_token} for user {user_id}")
        return session
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create session in database: {str(e)}")
        raise e

def get_session_by_token(db: Session, session_token: str) -> Optional[UserSession]:
    """Get active session by token"""
    try:
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        return session
        
    except Exception as e:
        logger.error(f"❌ Failed to get session: {str(e)}")
        return None

def update_session_activity(db: Session, session_token: str) -> bool:
    """Update session last activity timestamp"""
    try:
        session = get_session_by_token(db, session_token)
        if session:
            session.last_activity = datetime.utcnow()
            db.commit()
            return True
        return False
        
    except Exception as e:
        logger.error(f"❌ Failed to update session activity: {str(e)}")
        return False

# =============================================================================
# SESSION ENDPOINTS (FIXED)
# =============================================================================

@router.post("/create", response_model=SessionResponse)
async def create_user_session(
    request: Optional[SessionCreateRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new user session - COMPLETELY FIXED VERSION"""
    try:
        # Generate unique session token
        session_token = f"sess_{secrets.token_urlsafe(20)}"
        
        # Set session expiration (30 minutes from now)
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        
        # Create session with ALL required parameters
        session = create_user_session_db(
            db=db,
            user_id=current_user.id,
            session_token=session_token,
            expires_at=expires_at  # CRITICAL FIX: Now properly provided
        )
        
        # Log device info if provided
        if request and request.device_info:
            logger.info(f"   Device info recorded: {request.device_info}")
        
        logger.info(f"✅ Session created successfully for user {current_user.id}")
        
        return SessionResponse(
            session_id=session.id,
            session_token=session.session_token,
            created_at=session.created_at.isoformat(),
            expires_at=session.expires_at.isoformat(),
            last_activity=session.last_activity.isoformat(),
            is_active=session.is_active,
            user_id=session.user_id,
            message="Session created successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to create session for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/status/{session_token}")
async def get_session_status(
    session_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get session status by token"""
    try:
        session = get_session_by_token(db, session_token)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        time_remaining = (session.expires_at - datetime.utcnow()).total_seconds() / 60
        
        return {
            "session_id": session.id,
            "session_token": session.session_token,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "is_active": session.is_active,
            "trust_score": session.trust_score,
            "is_mirage_active": session.is_mirage_active,
            "time_remaining_minutes": max(0, int(time_remaining)),
            "status": "active" if time_remaining > 0 else "expired"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get session status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session status")

@router.post("/heartbeat/{session_token}")
async def session_heartbeat(
    session_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send session heartbeat to keep session active"""
    try:
        session = get_session_by_token(db, session_token)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        # Update last activity
        success = update_session_activity(db, session_token)
        
        if success:
            time_remaining = (session.expires_at - datetime.utcnow()).total_seconds() / 60
            return {
                "message": "Session heartbeat successful",
                "session_token": session_token,
                "last_activity": datetime.utcnow().isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "time_remaining_minutes": max(0, int(time_remaining))
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update session activity")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Session heartbeat failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Session heartbeat failed")

@router.get("/my-sessions")
async def get_my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active sessions for authenticated user"""
    try:
        sessions = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).order_by(UserSession.created_at.desc()).limit(10).all()
        
        session_list = []
        for session in sessions:
            time_remaining = (session.expires_at - datetime.utcnow()).total_seconds() / 60
            session_list.append({
                "session_id": session.id,
                "session_token": session.session_token[-8:] + "***",  # Partial token for security
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "is_active": time_remaining > 0,
                "time_remaining_minutes": max(0, int(time_remaining)),
                "trust_score": session.trust_score,
                "is_mirage_active": session.is_mirage_active
            })
        
        return {
            "user_id": current_user.id,
            "username": current_user.username,
            "total_sessions": len(session_list),
            "sessions": session_list
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get user sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user sessions")

@router.delete("/terminate/{session_token}")
async def terminate_session(
    session_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Terminate a specific session"""
    try:
        session = get_session_by_token(db, session_token)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        # Deactivate session
        session.is_active = False
        session.expires_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Session terminated: {session_token} for user {current_user.id}")
        
        return {
            "message": "Session terminated successfully",
            "session_token": session_token,
            "terminated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to terminate session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to terminate session")
