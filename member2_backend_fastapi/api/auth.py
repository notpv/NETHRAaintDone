from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from database.database import get_db
from database.crud import UserCRUD, SessionCRUD, SystemLogCRUD
from database.models import User
from schemas.auth_schemas import (
    UserCreate, UserLogin, Token, TokenData, 
    UserResponse, LoginResponse, PasswordChange
)
from services.auth_service import AuthService
from utils.jwt_utils import JWTHandler
from middleware.rate_limit import rate_limit
from services.security_service import SecurityService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)
jwt_handler = JWTHandler()
auth_service = AuthService()
security_service = SecurityService()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(max_requests=5, window_seconds=300)  # 5 registrations per 5 minutes
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    try:
        # Check if user already exists
        existing_user = UserCRUD.get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered"
            )
        
        existing_email = UserCRUD.get_user_by_email(db, user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Validate password strength
        if not security_service.validate_password_strength(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet security requirements"
            )
        
        # Create new user
        new_user = UserCRUD.create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            device_id=user_data.device_id,
            device_model=user_data.device_model,
            os_version=user_data.os_version,
            app_version=user_data.app_version
        )
        
        # Log successful registration
        SystemLogCRUD.create_log(
            db=db,
            level="INFO",
            message=f"New user registered: {user_data.username}",
            module="auth",
            user_id=new_user.id,
            additional_data=f'{{"ip_address": "{request.client.host}"}}'
        )
        
        logger.info(f"✅ New user registered: {user_data.username} (ID: {new_user.id})")
        
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            is_active=new_user.is_active,
            created_at=new_user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error"
        )

@router.post("/login", response_model=LoginResponse)
@rate_limit(max_requests=10, window_seconds=60)  # 10 login attempts per minute
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token"""
    try:
        # Authenticate user credentials
        user = UserCRUD.authenticate_user(db, login_data.username, login_data.password)
        
        if not user:
            # Log failed login attempt
            SystemLogCRUD.create_log(
                db=db,
                level="WARNING",
                message=f"Failed login attempt: {login_data.username}",
                module="auth",
                additional_data=f'{{"ip_address": "{request.client.host}"}}'
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Create new session
        session = SessionCRUD.create_session(
            db=db,
            user_id=user.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            device_fingerprint=login_data.device_fingerprint
        )
        
        # Generate JWT tokens
        access_token = jwt_handler.create_access_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "session_id": session.id,
                "device_id": user.device_id
            }
        )
        
        refresh_token = jwt_handler.create_refresh_token(
            data={"sub": str(user.id), "session_id": session.id}
        )
        
        # Update user last login
        UserCRUD.update_user(db, user.id, last_login=datetime.utcnow())
        
        # Log successful login
        SystemLogCRUD.create_log(
            db=db,
            level="INFO",
            message=f"User logged in: {user.username}",
            module="auth",
            user_id=user.id,
            session_id=str(session.session_uuid),
            additional_data=f'{{"ip_address": "{request.client.host}"}}'
        )
        
        logger.info(f"✅ User logged in: {user.username} (Session: {session.session_uuid})")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600,  # 1 hour
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at
            ),
            session_id=session.session_uuid
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )

@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Logout user and invalidate session"""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Verify token and get user info
        token_data = jwt_handler.verify_token(credentials.credentials)
        user_id = int(token_data.sub)
        session_id = token_data.session_id
        
        # End the session
        SessionCRUD.end_session(db, session_id, reason="user_logout")
        
        # Log logout
        SystemLogCRUD.create_log(
            db=db,
            level="INFO",
            message="User logged out",
            module="auth",
            user_id=user_id,
            session_id=str(session_id)
        )
        
        logger.info(f"✅ User logged out: ID {user_id}")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"❌ Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        token_data = jwt_handler.verify_refresh_token(refresh_token)
        user_id = int(token_data.sub)
        
        # Get user
        user = UserCRUD.get_user(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token = jwt_handler.create_access_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "session_id": token_data.session_id,
                "device_id": user.device_id
            }
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600
        )
        
    except Exception as e:
        logger.error(f"❌ Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        if not UserCRUD.authenticate_user(db, current_user.username, password_data.current_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        if not security_service.validate_password_strength(password_data.new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password does not meet security requirements"
            )
        
        # Update password
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(password_data.new_password)
        
        UserCRUD.update_user(db, current_user.id, hashed_password=hashed_password)
        
        # Log password change
        SystemLogCRUD.create_log(
            db=db,
            level="INFO",
            message="Password changed",
            module="auth",
            user_id=current_user.id
        )
        
        logger.info(f"✅ Password changed for user: {current_user.username}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's active sessions"""
    try:
        sessions = SessionCRUD.get_active_sessions(db, current_user.id)
        
        return {
            "active_sessions": len(sessions),
            "sessions": [
                {
                    "session_id": session.session_uuid,
                    "created_at": session.session_start,
                    "last_activity": session.last_activity,
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent[:100] if session.user_agent else None
                }
                for session in sessions
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )

@router.post("/validate-token")
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Validate JWT token"""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token required"
            )
        
        token_data = jwt_handler.verify_token(credentials.credentials)
        
        return {
            "valid": True,
            "user_id": token_data.sub,
            "username": token_data.username,
            "expires_at": datetime.fromtimestamp(token_data.exp).isoformat()
        }
        
    except Exception:
        return {"valid": False}

@router.post("/revoke-session/{session_uuid}")
async def revoke_session(
    session_uuid: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a specific session"""
    try:
        # Find the session
        session = db.query(SessionCRUD.get_session.__annotations__['return'].__args__[0]).filter(
            SessionCRUD.get_session.__annotations__['return'].__args__[0].session_uuid == session_uuid,
            SessionCRUD.get_session.__annotations__['return'].__args__[0].user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        SessionCRUD.end_session(db, session.id, reason="user_revoked")
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Session revocation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session revocation failed"
        )

