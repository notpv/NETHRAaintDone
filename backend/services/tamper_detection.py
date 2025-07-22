import hashlib
import hmac
import time
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class TamperDetectionService:
    """Tamper detection service for NETHRA security"""
    
    def __init__(self, secret_key: str = "nethra_tamper_detection_key"):
        self.secret_key = secret_key.encode('utf-8')
        self.suspicious_patterns = {
            "rapid_requests": 10,  # requests per second
            "invalid_user_agent": ["bot", "crawler", "scanner"],
            "suspicious_ips": set(),
            "unusual_behavioral_data": {}
        }
        
    def generate_integrity_hash(self, data: Dict) -> str:
        """Generate integrity hash for data"""
        try:
            # Sort keys for consistent hashing
            sorted_data = {k: data[k] for k in sorted(data.keys())}
            data_string = str(sorted_data)
            
            # Create HMAC hash
            hash_object = hmac.new(
                self.secret_key, 
                data_string.encode('utf-8'), 
                hashlib.sha256
            )
            
            return hash_object.hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to generate integrity hash: {str(e)}")
            return ""
    
    def verify_integrity(self, data: Dict, provided_hash: str) -> bool:
        """Verify data integrity"""
        try:
            calculated_hash = self.generate_integrity_hash(data)
            return hmac.compare_digest(calculated_hash, provided_hash)
            
        except Exception as e:
            logger.error(f"Integrity verification failed: {str(e)}")
            return False
    
    def detect_behavioral_tampering(self, behavioral_data: Dict) -> Tuple[bool, List[str]]:
        """Detect potential tampering in behavioral data"""
        suspicious_indicators = []
        
        # Check for impossible values
        impossible_values = {
            'avg_pressure': (0.0, 5.0),
            'avg_swipe_velocity': (0.0, 50.0),
            'avg_swipe_duration': (0.01, 10.0),
            'accel_stability': (0.0, 1.0),
            'gyro_stability': (0.0, 1.0),
            'touch_frequency': (0.0, 100.0)
        }
        
        for feature, (min_val, max_val) in impossible_values.items():
            if feature in behavioral_data:
                value = behavioral_data[feature]
                if not (min_val <= value <= max_val):
                    suspicious_indicators.append(f"Impossible {feature} value: {value}")
        
        # Check for patterns indicating synthetic data
        values = list(behavioral_data.values())
        
        # All identical values (suspicious)
        if len(set(values)) == 1 and len(values) > 1:
            suspicious_indicators.append("All behavioral values identical")
        
        # Perfect mathematical relationships (suspicious)
        if len(values) >= 2:
            ratios = []
            for i in range(1, len(values)):
                if values[i-1] != 0:
                    ratios.append(values[i] / values[i-1])
            
            # If all ratios are the same, data might be synthetic
            if len(set(f"{r:.3f}" for r in ratios)) == 1 and len(ratios) > 1:
                suspicious_indicators.append("Perfect mathematical relationships detected")
        
        return len(suspicious_indicators) > 0, suspicious_indicators
    
    def detect_request_tampering(self, request_data: Dict) -> Tuple[bool, List[str]]:
        """Detect request-level tampering"""
        suspicious_indicators = []
        
        # Check for missing timestamp
        if 'timestamp' not in request_data:
            suspicious_indicators.append("Missing timestamp")
        else:
            # Check timestamp validity (not too old/future)
            try:
                from datetime import datetime
                timestamp = datetime.fromisoformat(request_data['timestamp'].replace('Z', '+00:00'))
                now = datetime.utcnow()
                
                time_diff = abs((now - timestamp).total_seconds())
                
                if time_diff > 300:  # 5 minutes
                    suspicious_indicators.append(f"Timestamp too old/future: {time_diff}s")
                    
            except Exception:
                suspicious_indicators.append("Invalid timestamp format")
        
        # Check for unusual user_id patterns
        if 'user_id' in request_data:
            user_id = request_data['user_id']
            if user_id <= 0 or user_id > 1000000:
                suspicious_indicators.append("Suspicious user_id value")
        
        return len(suspicious_indicators) > 0, suspicious_indicators
    
    def assess_tamper_risk(self, behavioral_data: Dict, request_data: Dict) -> Dict:
        """Comprehensive tamper risk assessment"""
        try:
            behavioral_tampered, behavioral_issues = self.detect_behavioral_tampering(behavioral_data)
            request_tampered, request_issues = self.detect_request_tampering(request_data)
            
            total_issues = behavioral_issues + request_issues
            risk_score = len(total_issues) * 25  # 0-100 scale
            risk_score = min(risk_score, 100)
            
            # Risk level classification
            if risk_score >= 75:
                risk_level = "critical"
            elif risk_score >= 50:
                risk_level = "high"
            elif risk_score >= 25:
                risk_level = "moderate"
            else:
                risk_level = "low"
            
            return {
                "tamper_detected": behavioral_tampered or request_tampered,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "behavioral_issues": behavioral_issues,
                "request_issues": request_issues,
                "total_issues": len(total_issues),
                "recommended_action": self._get_recommended_action(risk_level)
            }
            
        except Exception as e:
            logger.error(f"Tamper risk assessment failed: {str(e)}")
            return {
                "tamper_detected": True,
                "risk_score": 100,
                "risk_level": "critical",
                "error": str(e),
                "recommended_action": "block_request"
            }
    
    def _get_recommended_action(self, risk_level: str) -> str:
        """Get recommended action based on risk level"""
        actions = {
            "low": "allow_request",
            "moderate": "additional_verification",
            "high": "activate_mirage",
            "critical": "block_request"
        }
        return actions.get(risk_level, "block_request")

# Global tamper detection service
_tamper_detection = None

def get_tamper_detection_service() -> TamperDetectionService:
    """Get or create global tamper detection service"""
    global _tamper_detection
    if _tamper_detection is None:
        _tamper_detection = TamperDetectionService()
    return _tamper_detection
