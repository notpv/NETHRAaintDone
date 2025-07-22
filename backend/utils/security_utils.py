import secrets
import string
import hashlib
from typing import Optional, Dict
import re
import logging

logger = logging.getLogger(__name__)

class SecurityUtils:
    """Security utilities for NETHRA backend"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters long")
        
        # Uppercase check
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("Password should contain uppercase letters")
        
        # Lowercase check
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("Password should contain lowercase letters")
        
        # Number check
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("Password should contain numbers")
        
        # Special character check
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("Password should contain special characters")
        
        strength_levels = {
            0: "very_weak",
            1: "weak", 
            2: "fair",
            3: "good",
            4: "strong",
            5: "very_strong"
        }
        
        return {
            "score": score,
            "max_score": 5,
            "strength": strength_levels[score],
            "is_strong": score >= 4,
            "feedback": feedback
        }
    
    @staticmethod
    def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
        """Hash sensitive data with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        combined = f"{data}{salt}"
        hashed = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        
        return f"{salt}:{hashed}"
    
    @staticmethod
    def verify_hashed_data(data: str, hashed_data: str) -> bool:
        """Verify data against hash"""
        try:
            salt, hash_value = hashed_data.split(':', 1)
            combined = f"{data}{salt}"
            calculated_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
            
            return calculated_hash == hash_value
            
        except Exception as e:
            logger.error(f"Hash verification failed: {str(e)}")
            return False

# Global security utils instance
security_utils = SecurityUtils()
