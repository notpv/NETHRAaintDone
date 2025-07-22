from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

class UserRegistrationRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool

class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: UserInfo

class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    expires: Optional[int] = None
    error: Optional[str] = None
