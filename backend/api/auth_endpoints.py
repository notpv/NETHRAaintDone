from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
import logging

from database.database import get_db
from database.crud import create_user, get_user_by_username
from utils.jwt_utils import create_access_token, verify_token
from database.models import User
from schemas.auth_schemas import UserRegistrationRequest, TokenResponse, UserInfo

router = APIRouter()
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

@router.post("/register", response_model=TokenResponse)
async def register_user(
    user_data: UserRegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register new user"""
    try:
        # Check if username already exists
        existing_user = get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username already registered"
            )
        
        # Hash password and create user
        hashed_password = hash_password(user_data.password)
        db_user = create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        
        # Create access token
        access_token = create_access_token(data={"sub": db_user.username})
        
        # Convert SQLAlchemy model to Pydantic model using from_orm
        user_response = UserInfo.model_validate(db_user)
        
        logger.info(f"✅ User registered successfully: {user_data.username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=30 * 60,
            user_info=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration failed for {user_data.username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=TokenResponse)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token"""
    try:
        # Get user by username
        user = get_user_by_username(db, form_data.username)
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.username})
        
        user_response = UserInfo.model_validate(user)
        
        logger.info(f"✅ User logged in successfully: {form_data.username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=30 * 60,
            user_info=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login failed for {form_data.username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/validate-token")
async def validate_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Validate JWT token"""
    try:
        logger.info(f"🔍 Validating token: {token[:20]}...")
        
        payload = verify_token(token)
        username = payload.get("sub")
        
        if username is None:
            logger.error("❌ Token payload missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token - missing username"
            )
        
        user = get_user_by_username(db, username)
        if user is None:
            logger.error(f"❌ User not found for username: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        logger.info(f"✅ Token validation successful for user: {username}")
        
        return {
            "valid": True,
            "user_id": user.id,
            "username": user.username,
            "expires": payload.get("exp"),
            "message": "Token is valid"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

@router.post("/logout")
async def logout_user():
    """Logout user (token-based logout)"""
    return {"message": "Successfully logged out"}

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        payload = verify_token(token)
        username = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = get_user_by_username(db, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get current user failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
