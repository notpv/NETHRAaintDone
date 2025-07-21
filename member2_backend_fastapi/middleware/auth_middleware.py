import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import jwt

from config.settings import settings
from utils.jwt_utils import JWTHandler
from database.database import get_db_session
from database.crud import UserCRUD, SessionCRUD

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """
    NETHRA Authentication Middleware
    
    Handles JWT token validation and session management
    with proper exclusions for public endpoints
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.jwt_handler = JWTHandler()
        
        # PUBLIC ENDPOINTS - No authentication required
        self.public_paths = {
            "/health",
            "/ping", 
            "/version",
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/register",
            "/auth/login",
            "/auth/refresh",
            "/static/",
            "/favicon.ico"
        }
        
        # MONITORING ENDPOINTS - Always accessible
        self.monitoring_paths = {
            "/monitor/health",
            "/monitor/ping",
            "/monitor/status", 
            "/monitor/metrics",
            "/monitor/version"
        }
        
        # PROTECTED ENDPOINTS - Require authentication
        self.protected_prefixes = [
            "/trust/",
            "/user/",
            "/auth/logout",
            "/auth/validate-token",
            "/auth/change-password"
        ]
    
    def is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required)"""
        
        # Exact matches
        if path in self.public_paths:
            return True
        
        # Monitoring endpoints
        if path in self.monitoring_paths:
            return True
            
        # Path prefixes
        public_prefixes = ["/static/", "/docs", "/redoc"]
        if any(path.startswith(prefix) for prefix in public_prefixes):
            return True
            
        return False
    
    def requires_auth(self, path: str) -> bool:
        """Check if path requires authentication"""
        
        # Public paths don't require auth
        if self.is_public_path(path):
            return False
        
        # Protected prefixes require auth
        return any(path.startswith(prefix) for prefix in self.protected_prefixes)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request through authentication middleware
        """
        try:
            path = request.url.path
            method = request.method
            
            # Skip authentication for public endpoints
            if not self.requires_auth(path):
                logger.debug(f"🔓 Public endpoint: {method} {path}")
                return await call_next(request)
            
            # Extract and validate JWT token
            token = self.extract_token(request)
            
            if not token:
                logger.warning(f"🔒 Missing token for protected endpoint: {method} {path}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Validate token and get user info
            user_info = await self.validate_token(token)
            
            # Add user info to request state
            request.state.user_id = user_info["user_id"]
            request.state.username = user_info["username"] 
            request.state.session_id = user_info.get("session_id")
            
            logger.debug(f"✅ Authenticated request: {method} {path} - User: {user_info['username']}")
            
            # Continue to endpoint
            response = await call_next(request)
            
            # Add auth headers to response
            response.headers["X-Authenticated-User"] = user_info["username"]
            response.headers["X-Session-ID"] = str(user_info.get("session_id", ""))
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions (like 401 Unauthorized)
            raise
            
        except Exception as e:
            logger.error(f"❌ Auth middleware error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )
    
    def extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers"""
        try:
            # Check Authorization header
            auth_header = request.headers.get("Authorization")
            
            if auth_header and auth_header.startswith("Bearer "):
                return auth_header.split(" ", 1)[1]
            
            # Check for token in query parameters (for debugging)
            if settings.DEBUG:
                token = request.query_params.get("token")
                if token:
                    logger.debug("🔧 Using token from query parameter (debug mode)")
                    return token
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Token extraction failed: {e}")
            return None
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and return user information
        """
        try:
            # Decode and validate JWT token
            payload = self.jwt_handler.verify_token(token)
            
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            
            user_id = int(payload.sub)
            username = payload.username
            session_id = payload.session_id
            
            # Validate user exists and is active
            with get_db_session() as db:
                user = UserCRUD.get_user(db, user_id)
                
                if not user:
                    logger.warning(f"🔒 Token valid but user not found: {user_id}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User account not found"
                    )
                
                if not user.is_active:
                    logger.warning(f"🔒 Token valid but user inactive: {username}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User account is disabled"
                    )
                
                # Check session if session_id provided
                if session_id:
                    session = SessionCRUD.get_session(db, session_id)
                    if session and not session.is_active:
                        logger.warning(f"🔒 Session expired: {session_id}")
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Session has expired"
                        )
                    
                    # Update session activity
                    if session:
                        SessionCRUD.update_session_activity(db, session_id)
            
            return {
                "user_id": user_id,
                "username": username,
                "session_id": session_id,
                "is_active": user.is_active
            }
            
        except jwt.ExpiredSignatureError:
            logger.warning("🔒 Token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        except jwt.InvalidTokenError:
            logger.warning("🔒 Invalid token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
            
        except Exception as e:
            logger.error(f"❌ Token validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )
    
    def create_error_response(self, status_code: int, message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "error": "Authentication Error",
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "authentication_error"
        }

# Utility functions for manual auth checking
def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current authenticated user from request state"""
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return {
        "user_id": request.state.user_id,
        "username": request.state.username,
        "session_id": getattr(request.state, 'session_id', None)
    }

def require_auth(request: Request) -> int:
    """Require authentication and return user_id"""
    user_info = get_current_user(request)
    return user_info["user_id"]

# Optional: Session timeout checking
class SessionTimeoutChecker:
    """Check for session timeouts based on NETHRA's 10-minute requirement"""
    
    @staticmethod
    def is_session_expired(last_activity: datetime) -> bool:
        """Check if session has expired (10 minutes of inactivity)"""
        if not last_activity:
            return True
        
        timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        timeout_delta = timedelta(minutes=timeout_minutes)
        
        return datetime.utcnow() - last_activity > timeout_delta
    
    @staticmethod
    def get_session_remaining_time(last_activity: datetime) -> int:
        """Get remaining session time in seconds"""
        if not last_activity:
            return 0
        
        timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        timeout_delta = timedelta(minutes=timeout_minutes)
        elapsed = datetime.utcnow() - last_activity
        remaining = timeout_delta - elapsed
        
        return max(0, int(remaining.total_seconds()))
