from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "sqlite:///./nethra.db"
    database_pool_size: int = 10
    
    # JWT Configuration
    jwt_secret_key: str = "nethra-super-secret-jwt-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Security Configuration
    encryption_key_path: str = "./encryption.key"
    bcrypt_rounds: int = 12
    
    # Session Configuration
    session_timeout_minutes: int = 10
    max_concurrent_sessions: int = 3
    
    # AI Model Configuration (Member 1's specifications)
    ai_model_path: str = "./models/nethra_neural_network.h5"
    ai_scaler_path: str = "./models/nethra_scaler.pkl"
    trust_score_threshold_default: float = 40.0
    mirage_activation_threshold: float = 40.0
    
    # Monitoring Configuration
    enable_metrics: bool = True
    metrics_port: int = 8000
    
    # Environment
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# JWT settings
ALGORITHM = settings.jwt_algorithm
SECRET_KEY = settings.jwt_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes

# Database settings
DATABASE_URL = settings.database_url

# AI Model settings (Member 1's model paths)
AI_MODEL_PATH = settings.ai_model_path
AI_SCALER_PATH = settings.ai_scaler_path
DEFAULT_THRESHOLD = settings.trust_score_threshold_default
MIRAGE_THRESHOLD = settings.mirage_activation_threshold

# Session settings
SESSION_TIMEOUT = settings.session_timeout_minutes
MAX_SESSIONS = settings.max_concurrent_sessions
