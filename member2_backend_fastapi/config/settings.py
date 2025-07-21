import os
import secrets
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
from cryptography.fernet import Fernet

class Settings(BaseSettings):
    """
    NETHRA Auto-Configuration - Zero Setup Required!
    
    Smart defaults that work out of the box for hackathons
    """
    
    # Application Info
    APP_NAME: str = "NETHRA Guardian AI Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True  # Auto-enable for development
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database - Auto SQLite
    DATABASE_URL: str = "sqlite:///./nethra.db"
    DATABASE_ECHO: bool = False
    
    # JWT - Auto-generate secure keys
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Encryption - Auto-generate
    ENCRYPTION_KEY: str = Field(default_factory=lambda: Fernet.generate_key().decode())
    BCRYPT_ROUNDS: int = 12
    
    # AI Model - Auto-detect
    MODEL_PATH: str = "./models/trust_model.h5"
    DEFAULT_TRUST_THRESHOLD: float = 40.0
    MIN_SESSIONS_FOR_PERSONAL_THRESHOLD: int = 5
    
    # Session - Hackathon optimized
    SESSION_TIMEOUT_MINUTES: int = 10  # As required
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    # Security - Dev-friendly defaults
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]  # Permissive for demo
    CORS_ORIGINS: List[str] = ["*"]  # Allow all origins for hackathon
    SECURE_COOKIES: bool = False  # Disable for local testing
    
    # Rate Limiting - Lenient for demo
    RATE_LIMIT_REQUESTS: int = 1000  # High limit
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # Monitoring - Auto-enable
    PROMETHEUS_METRICS_PORT: int = 9090
    ENABLE_METRICS: bool = True
    
    # Logging - Optimized for demo
    LOG_LEVEL: str = "INFO"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
        self._log_startup_info()
    
    def _ensure_directories(self):
        """Auto-create required directories"""
        import pathlib
        
        # Create models directory
        pathlib.Path("models").mkdir(exist_ok=True)
        pathlib.Path("logs").mkdir(exist_ok=True)
        pathlib.Path("static").mkdir(exist_ok=True)
        
    def _log_startup_info(self):
        """Show configuration info on startup"""
        print(f"🚀 {self.APP_NAME} v{self.APP_VERSION}")
        print(f"🔧 Auto-configuration enabled")
        print(f"🗄️  Database: {self.DATABASE_URL}")
        print(f"🔐 JWT Secret: {'*' * 20}...{self.JWT_SECRET_KEY[-10:]}")
        print(f"⏱️  Session timeout: {self.SESSION_TIMEOUT_MINUTES} minutes")
        print(f"🤖 Model path: {self.MODEL_PATH}")
    
    @property
    def is_model_available(self) -> bool:
        """Check if AI model file exists"""
        import pathlib
        return pathlib.Path(self.MODEL_PATH).exists()
    
    @property
    def demo_mode(self) -> bool:
        """Enable demo-friendly settings"""
        return True  # Always true for hackathon
    
    class Config:
        # Only load .env if it exists (optional)
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Ignore missing .env file
        env_ignore_empty = True

# Global settings instance with auto-configuration
settings = Settings()

def get_settings() -> Settings:
    """Get auto-configured settings"""
    return settings
