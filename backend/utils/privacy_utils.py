import hashlib
import uuid
from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)

class PrivacyUtils:
    """Privacy compliance utilities for NETHRA"""
    
    @staticmethod
    def anonymize_data(data: Dict, sensitive_fields: List[str] = None) -> Dict:
        """Anonymize sensitive fields in data"""
        if sensitive_fields is None:
            sensitive_fields = ['email', 'username', 'phone', 'address']
        
        anonymized = data.copy()
        
        for field in sensitive_fields:
            if field in anonymized:
                # Replace with anonymized version
                original_value = str(anonymized[field])
                anonymized[field] = hashlib.sha256(original_value.encode()).hexdigest()[:8]
        
        return anonymized
    
    @staticmethod
    def generate_user_consent_record(user_id: int, consent_type: str) -> Dict:
        """Generate consent record for GDPR compliance"""
        return {
            "user_id": user_id,
            "consent_type": consent_type,
            "consent_given": True,
            "timestamp": "2025-07-21T21:25:00Z",
            "consent_id": str(uuid.uuid4()),
            "version": "1.0"
        }
    
    @staticmethod
    def export_user_data(user_data: Dict) -> Dict:
        """Export user data in GDPR-compliant format"""
        return {
            "export_timestamp": "2025-07-21T21:25:00Z",
            "data_controller": "NETHRA Security System",
            "user_data": user_data,
            "data_categories": [
                "behavioral_patterns",
                "trust_scores", 
                "session_data"
            ]
        }

# Global privacy utils instance
privacy_utils = PrivacyUtils()
