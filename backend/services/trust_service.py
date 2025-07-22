import asyncio
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import statistics
import logging

from services.ai_interface import get_trust_predictor
from services.threshold_manager import ThresholdManager
from services.mirage_controller import get_mirage_controller
from services.behavioral_analyzer import get_behavioral_analyzer
from database.crud import store_behavioral_data, get_user_trust_history
from database.models import User, TrustProfile, BehavioralData

logger = logging.getLogger(__name__)

class TrustService:
    """
    Comprehensive Trust Processing Service for NETHRA
    Orchestrates AI predictions, threshold management, and security decisions
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.trust_predictor = get_trust_predictor()
        self.threshold_manager = ThresholdManager(db)
        self.mirage_controller = get_mirage_controller()
        self.behavioral_analyzer = get_behavioral_analyzer()
    
    async def process_trust_request(self, user_id: int, behavioral_data: Dict, session_id: Optional[int] = None) -> Dict:
        """
        Main trust processing pipeline - your core NETHRA functionality
        """
        try:
            logger.info(f"🎯 Processing trust request for user {user_id}")
            
            # Step 1: Validate behavioral data
            is_valid, validation_issues = self.behavioral_analyzer.validate_behavioral_features(behavioral_data)
            
            if not is_valid:
                logger.warning(f"Invalid behavioral data for user {user_id}: {validation_issues}")
                return {
                    "success": False,
                    "error": "Invalid behavioral data",
                    "validation_issues": validation_issues
                }
            
            # Step 2: Get AI trust score from Member 1's model
            trust_score = await self.trust_predictor.predict_trust_score(behavioral_data)
            trust_category = self.trust_predictor.get_trust_category(trust_score)
            
            # Step 3: Get user's personal threshold
            personal_threshold = self.threshold_manager.get_personal_threshold(user_id)
            
            # Step 4: Update user's behavioral profile
            trust_profile = self.threshold_manager.update_user_profile(
                user_id, trust_score, behavioral_data
            )
            
            # Step 5: Determine security action needed
            security_decision = await self._make_security_decision(
                user_id, trust_score, personal_threshold, session_id
            )
            
            # Step 6: Store behavioral data for analytics
            await self._store_behavioral_record(
                user_id, session_id, behavioral_data, trust_score, security_decision
            )
            
            # Step 7: Generate comprehensive response
            response = await self._generate_trust_response(
                user_id, trust_score, trust_category, personal_threshold,
                security_decision, trust_profile
            )
            
            logger.info(f"✅ Trust processing completed for user {user_id}")
            logger.info(f"   Trust Score: {trust_score:.2f}")
            logger.info(f"   Security Action: {security_decision['action']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Trust processing failed for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "trust_score": 30.0,  # Conservative fallback
                "security_action": "maximum_security"
            }
    
    async def _make_security_decision(self, user_id: int, trust_score: float, personal_threshold: float, session_id: Optional[int]) -> Dict:
        """Make security decision based on trust score and personal threshold"""
        
        # Primary decision: Compare to personal threshold
        is_below_threshold = trust_score < personal_threshold
        
        # Security action determination
        if trust_score >= 85:
            action = "allow_full_access"
            message = "Full access granted - highly trusted behavior"
            mirage_needed = False
            
        elif trust_score >= personal_threshold + 10:
            action = "allow_normal_access"
            message = "Normal access with standard monitoring"
            mirage_needed = False
            
        elif trust_score >= personal_threshold:
            action = "allow_with_monitoring"
            message = "Access granted with enhanced monitoring"
            mirage_needed = False
            
        elif trust_score >= 25:
            action = "activate_mirage"
            message = "Security measures activated"
            mirage_needed = True
            
        else:
            action = "maximum_security"
            message = "High security response initiated"
            mirage_needed = True
        
        # Activate mirage if needed
        mirage_result = None
        if mirage_needed:
            mirage_result = await self.mirage_controller.activate_mirage(
                user_id, trust_score, session_id
            )
        
        return {
            "action": action,
            "message": message,
            "is_below_threshold": is_below_threshold,
            "mirage_activated": mirage_needed,
            "mirage_result": mirage_result,
            "confidence": self._calculate_decision_confidence(trust_score, personal_threshold)
        }
    
    def _calculate_decision_confidence(self, trust_score: float, personal_threshold: float) -> float:
        """Calculate confidence in security decision"""
        # Distance from threshold indicates confidence
        distance = abs(trust_score - personal_threshold)
        
        # Normalize to 0-100 scale
        confidence = min(distance * 2, 100)
        
        return round(confidence, 2)
    
    async def _store_behavioral_record(self, user_id: int, session_id: Optional[int], 
                                     behavioral_data: Dict, trust_score: float, 
                                     security_decision: Dict):
        """Store behavioral data record asynchronously"""
        try:
            await asyncio.create_task(
                asyncio.to_thread(
                    store_behavioral_data,
                    self.db, user_id, session_id or 0,
                    behavioral_data, trust_score, 
                    security_decision["mirage_activated"]
                )
            )
        except Exception as e:
            logger.error(f"Failed to store behavioral record: {str(e)}")
    
    async def _generate_trust_response(self, user_id: int, trust_score: float, 
                                     trust_category: str, personal_threshold: float,
                                     security_decision: Dict, trust_profile: TrustProfile) -> Dict:
        """Generate comprehensive trust response"""
        
        return {
            "success": True,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            
            # Trust Score Information
            "trust_score": round(trust_score, 2),
            "trust_category": trust_category,
            "personal_threshold": personal_threshold,
            "is_below_threshold": security_decision["is_below_threshold"],
            
            # Security Decision
            "security_action": security_decision["action"],
            "user_message": security_decision["message"],
            "decision_confidence": security_decision["confidence"],
            
            # Mirage Interface
            "mirage_activated": security_decision["mirage_activated"],
            "mirage_intensity": security_decision.get("mirage_result", {}).get("mirage_config", {}).get("intensity_level"),
            
            # User Profile Information
            "session_count": trust_profile.session_count,
            "learning_phase": trust_profile.is_learning_phase,
            "average_trust_score": trust_profile.average_trust_score,
            
            # Recommendations
            "recommendations": self._generate_security_recommendations(trust_score, personal_threshold),
        }
    
    def _generate_security_recommendations(self, trust_score: float, personal_threshold: float) -> List[str]:
        """Generate security recommendations based on trust score"""
        recommendations = []
        
        if trust_score < personal_threshold - 20:
            recommendations.extend([
                "Consider re-authenticating with biometrics",
                "Review recent account activity",
                "Enable additional security notifications"
            ])
        elif trust_score < personal_threshold:
            recommendations.extend([
                "Monitor account activity closely",
                "Consider additional verification for sensitive operations"
            ])
        elif trust_score < 70:
            recommendations.append("Continue with normal security monitoring")
        else:
            recommendations.append("Trusted session - normal operations allowed")
        
        return recommendations
    
    async def get_user_trust_analytics(self, user_id: int, days: int = 7) -> Dict:
        """Get comprehensive trust analytics for user"""
        try:
            # Get trust history
            history = get_user_trust_history(self.db, user_id, limit=days * 10)
            
            if not history:
                return {
                    "user_id": user_id,
                    "message": "No trust history available",
                    "recommendations": ["Complete more sessions to establish baseline"]
                }
            
            # Calculate analytics
            trust_scores = [record.trust_score for record in history if record.trust_score]
            mirage_activations = sum(1 for record in history if record.mirage_triggered)
            
            analytics = {
                "user_id": user_id,
                "analysis_period_days": days,
                "total_sessions": len(history),
                "mirage_activations": mirage_activations,
                "mirage_rate_percent": round((mirage_activations / len(history)) * 100, 2) if history else 0,
                
                "trust_score_stats": {
                    "average": round(statistics.mean(trust_scores), 2) if trust_scores else 0,
                    "median": round(statistics.median(trust_scores), 2) if trust_scores else 0,
                    "min": min(trust_scores) if trust_scores else 0,
                    "max": max(trust_scores) if trust_scores else 0,
                    "std_dev": round(statistics.stdev(trust_scores), 2) if len(trust_scores) > 1 else 0
                },
                
                "behavioral_stability": self.behavioral_analyzer.calculate_feature_stability([
                    {
                        "avg_pressure": record.avg_pressure,
                        "avg_swipe_velocity": record.avg_swipe_velocity,
                        "avg_swipe_duration": record.avg_swipe_duration,
                        "accel_stability": record.accel_stability,
                        "gyro_stability": record.gyro_stability,
                        "touch_frequency": record.touch_frequency
                    } for record in history
                ]),
                
                "recent_trend": self._analyze_recent_trend(trust_scores[-10:] if trust_scores else []),
                "security_assessment": self._assess_user_security_posture(trust_scores, mirage_activations)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get trust analytics for user {user_id}: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_recent_trend(self, recent_scores: List[float]) -> Dict:
        """Analyze recent trust score trend"""
        if len(recent_scores) < 3:
            return {"trend": "insufficient_data"}
        
        # Simple trend analysis
        first_half = recent_scores[:len(recent_scores)//2]
        second_half = recent_scores[len(recent_scores)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        change = second_avg - first_avg
        change_percent = (change / first_avg) * 100 if first_avg != 0 else 0
        
        if abs(change_percent) < 5:
            trend = "stable"
        elif change_percent > 5:
            trend = "improving"
        else:
            trend = "declining"
        
        return {
            "trend": trend,
            "change_percent": round(change_percent, 2),
            "recent_average": round(second_avg, 2),
            "previous_average": round(first_avg, 2)
        }
    
    def _assess_user_security_posture(self, trust_scores: List[float], mirage_activations: int) -> Dict:
        """Assess overall security posture for user"""
        if not trust_scores:
            return {"assessment": "unknown", "reason": "No data available"}
        
        avg_score = statistics.mean(trust_scores)
        mirage_rate = mirage_activations / len(trust_scores) if trust_scores else 0
        
        if avg_score >= 80 and mirage_rate < 0.1:
            assessment = "excellent"
            reason = "Consistently high trust scores with minimal security interventions"
        elif avg_score >= 65 and mirage_rate < 0.2:
            assessment = "good" 
            reason = "Generally trustworthy behavior with occasional monitoring"
        elif avg_score >= 50 and mirage_rate < 0.3:
            assessment = "moderate"
            reason = "Mixed behavior patterns requiring regular security measures"
        elif avg_score >= 35:
            assessment = "concerning"
            reason = "Frequent low trust scores with regular security interventions"
        else:
            assessment = "high_risk"
            reason = "Consistently low trust scores indicating potential security issues"
        
        return {
            "assessment": assessment,
            "reason": reason,
            "average_trust_score": round(avg_score, 2),
            "mirage_activation_rate": round(mirage_rate * 100, 2)
        }
    
    async def compare_user_behavior(self, user_id: int, current_behavioral_data: Dict) -> Dict:
        """Compare current behavior to user's established baseline"""
        try:
            trust_profile = self.threshold_manager.db.query(TrustProfile).filter(
                TrustProfile.user_id == user_id
            ).first()
            
            if not trust_profile or trust_profile.is_learning_phase:
                return {
                    "comparison": "baseline_not_established",
                    "message": "User still in learning phase - no stable baseline available"
                }
            
            # Get baseline behavioral features
            baseline_features = {
                "avg_pressure": trust_profile.avg_pressure_baseline,
                "avg_swipe_velocity": trust_profile.avg_swipe_velocity_baseline,
                "avg_swipe_duration": trust_profile.avg_swipe_duration_baseline,
                "accel_stability": trust_profile.accel_stability_baseline,
                "gyro_stability": trust_profile.gyro_stability_baseline,
                "touch_frequency": trust_profile.touch_frequency_baseline
            }
            
            # Detect behavioral shifts
            shift_analysis = self.behavioral_analyzer.detect_behavioral_shift(
                current_behavioral_data, baseline_features
            )
            
            # Generate comparison summary
            comparison_result = {
                "user_id": user_id,
                "comparison": "available",
                "baseline_established": True,
                "sessions_in_baseline": trust_profile.session_count,
                "shift_detected": shift_analysis["shifts_detected"],
                "shift_severity": shift_analysis["overall_severity"],
                "feature_deviations": shift_analysis["feature_shifts"],
                "recommendation": self._get_shift_recommendation(shift_analysis)
            }
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"Failed to compare user behavior for user {user_id}: {str(e)}")
            return {"error": str(e)}
    
    def _get_shift_recommendation(self, shift_analysis: Dict) -> str:
        """Get recommendation based on behavioral shift analysis"""
        severity = shift_analysis["overall_severity"]
        
        if severity == "high":
            return "Significant behavioral changes detected - consider additional authentication"
        elif severity == "moderate":
            return "Some behavioral changes detected - monitor closely"
        else:
            return "Behavior within normal range - continue standard monitoring"

# Convenience function for easy access
def get_trust_service(db: Session) -> TrustService:
    """Get Trust Service instance with database session"""
    return TrustService(db)
