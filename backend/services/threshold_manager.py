import json
import statistics
from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from database.models import TrustProfile, User
from database.crud import get_trust_profile, update_trust_profile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ThresholdManager:
    """
    NETHRA Dynamic Personal Threshold Manager
    Creates personalized security baselines for each user
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.min_sessions_for_learning = 5  # Minimum sessions to establish personal baseline
        self.default_threshold = 40.0  # Member 1's baseline recommendation
        self.safety_margin = 1.5  # Standard deviations below mean for threshold
        self.min_threshold = 15.0  # Absolute minimum threshold
        self.max_threshold = 70.0  # Maximum threshold for safety
    
    def get_personal_threshold(self, user_id: int) -> float:
        """Get user's current personal threshold"""
        try:
            trust_profile = get_trust_profile(self.db, user_id)
            
            if not trust_profile:
                logger.info(f"No trust profile found for user {user_id}, using default threshold")
                return self.default_threshold
            
            # If still in learning phase, use default
            if trust_profile.is_learning_phase or trust_profile.session_count < self.min_sessions_for_learning:
                logger.info(f"User {user_id} still in learning phase ({trust_profile.session_count} sessions)")
                return self.default_threshold
            
            return trust_profile.personal_threshold
            
        except Exception as e:
            logger.error(f"Failed to get personal threshold for user {user_id}: {str(e)}")
            return self.default_threshold
    
    def calculate_personal_threshold(self, user_id: int) -> float:
        """Calculate personalized threshold based on user's behavioral history"""
        try:
            trust_profile = get_trust_profile(self.db, user_id)
            
            if not trust_profile or trust_profile.session_count < self.min_sessions_for_learning:
                return self.default_threshold
            
            # Parse score history
            score_history = json.loads(trust_profile.score_history or "[]")
            
            if len(score_history) < self.min_sessions_for_learning:
                return self.default_threshold
            
            # Statistical analysis of user's normal behavior
            mean_score = statistics.mean(score_history)
            
            if len(score_history) > 1:
                std_dev = statistics.stdev(score_history)
            else:
                std_dev = 5.0  # Default standard deviation
            
            # Set threshold based on statistical analysis
            # Threshold = mean - (safety_margin * std_dev)
            calculated_threshold = mean_score - (self.safety_margin * std_dev)
            
            # Apply bounds for safety
            personal_threshold = max(self.min_threshold, min(calculated_threshold, self.max_threshold))
            
            logger.info(f"📊 User {user_id} threshold calculation:")
            logger.info(f"   Mean score: {mean_score:.2f}")
            logger.info(f"   Std deviation: {std_dev:.2f}")
            logger.info(f"   Calculated threshold: {calculated_threshold:.2f}")
            logger.info(f"   Final threshold: {personal_threshold:.2f}")
            
            return round(personal_threshold, 2)
            
        except Exception as e:
            logger.error(f"Failed to calculate personal threshold for user {user_id}: {str(e)}")
            return self.default_threshold
    
    def update_user_profile(self, user_id: int, new_trust_score: float, behavioral_features: Dict) -> TrustProfile:
        """Update user's trust profile with new score and recalculate threshold"""
        try:
            # Update trust profile with new data
            trust_profile = update_trust_profile(self.db, user_id, new_trust_score, behavioral_features)
            
            # Recalculate personal threshold if enough sessions
            if trust_profile.session_count >= self.min_sessions_for_learning:
                new_threshold = self.calculate_personal_threshold(user_id)
                
                # Update threshold if it has changed significantly
                if abs(trust_profile.personal_threshold - new_threshold) > 2.0:
                    trust_profile.personal_threshold = new_threshold
                    trust_profile.is_learning_phase = False
                    self.db.commit()
                    
                    logger.info(f"🎯 Updated personal threshold for user {user_id}: {new_threshold:.2f}")
            
            return trust_profile
            
        except Exception as e:
            logger.error(f"Failed to update user profile for user {user_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def get_threshold_analysis(self, user_id: int) -> Dict:
        """Get detailed threshold analysis for user"""
        try:
            trust_profile = get_trust_profile(self.db, user_id)
            
            if not trust_profile:
                return {
                    "user_id": user_id,
                    "status": "no_profile",
                    "current_threshold": self.default_threshold,
                    "is_learning_phase": True,
                    "sessions_completed": 0,
                    "sessions_needed": self.min_sessions_for_learning
                }
            
            score_history = json.loads(trust_profile.score_history or "[]")
            
            analysis = {
                "user_id": user_id,
                "status": "learning" if trust_profile.is_learning_phase else "established",
                "current_threshold": trust_profile.personal_threshold,
                "is_learning_phase": trust_profile.is_learning_phase,
                "sessions_completed": trust_profile.session_count,
                "sessions_needed": max(0, self.min_sessions_for_learning - trust_profile.session_count),
                "average_trust_score": trust_profile.average_trust_score,
                "score_history": score_history[-10:],  # Last 10 scores
                "last_updated": trust_profile.last_updated.isoformat() if trust_profile.last_updated else None
            }
            
            if len(score_history) > 1:
                analysis["score_variance"] = round(statistics.stdev(score_history), 2)
                analysis["score_range"] = {
                    "min": min(score_history),
                    "max": max(score_history)
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to get threshold analysis for user {user_id}: {str(e)}")
            return {"error": str(e)}
    
    def compare_to_baseline(self, user_id: int, current_score: float) -> Dict:
        """Compare current score to user's personal baseline"""
        try:
            trust_profile = get_trust_profile(self.db, user_id)
            personal_threshold = self.get_personal_threshold(user_id)
            
            if not trust_profile:
                return {
                    "comparison": "no_baseline",
                    "current_score": current_score,
                    "personal_threshold": personal_threshold,
                    "deviation_from_baseline": None,
                    "risk_level": "unknown"
                }
            
            avg_score = trust_profile.average_trust_score
            deviation = current_score - avg_score
            
            # Determine risk level
            if current_score >= personal_threshold + 10:
                risk_level = "very_low"
            elif current_score >= personal_threshold:
                risk_level = "low"
            elif current_score >= personal_threshold - 10:
                risk_level = "moderate"
            else:
                risk_level = "high"
            
            return {
                "comparison": "available",
                "current_score": current_score,
                "average_baseline": avg_score,
                "personal_threshold": personal_threshold,
                "deviation_from_baseline": round(deviation, 2),
                "risk_level": risk_level,
                "sessions_analyzed": trust_profile.session_count
            }
            
        except Exception as e:
            logger.error(f"Failed to compare score to baseline for user {user_id}: {str(e)}")
            return {"error": str(e)}
