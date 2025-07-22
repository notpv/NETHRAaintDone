import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import logging

from database.models import UserSession
from config import SESSION_TIMEOUT

logger = logging.getLogger(__name__)

class SessionService:
    """Service for managing user sessions and timeouts"""
    
    def __init__(self):
        self.session_timeout_minutes = SESSION_TIMEOUT
        self.cleanup_interval_seconds = 300  # 5 minutes
        self._cleanup_task = None
    
    async def start_cleanup_task(self):
        """Start background task for session cleanup"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("🧹 Session cleanup task started")
    
    async def stop_cleanup_task(self):
        """Stop background cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
            logger.info("🛑 Session cleanup task stopped")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired sessions"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                logger.info("Session cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {str(e)}")
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions from database"""
        try:
            from database.database import SessionLocal
            db = SessionLocal()
            
            expired_sessions = db.query(UserSession).filter(
                UserSession.expires_at < datetime.utcnow(),
                UserSession.is_active == True
            ).all()
            
            if expired_sessions:
                for session in expired_sessions:
                    session.is_active = False
                
                db.commit()
                logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {str(e)}")
    
    def is_session_expired(self, session: UserSession) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > session.expires_at
    
    def extend_session(self, session: UserSession, minutes: int = None) -> UserSession:
        """Extend session expiry time"""
        if minutes is None:
            minutes = self.session_timeout_minutes
        
        session.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        session.last_activity = datetime.utcnow()
        
        return session

# Global session service instance
_session_service = None

def get_session_service() -> SessionService:
    """Get or create global session service instance"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
