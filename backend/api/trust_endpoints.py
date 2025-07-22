from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

# Database imports
from database.database import get_db
from database.crud import get_trust_profile, update_trust_profile, store_behavioral_data

# AI model imports
from services.ai_interface import get_trust_predictor

# Mirage controller imports
from services.mirage_controller import get_mirage_controller

# Auth imports
from api.auth_endpoints import get_current_user
from database.models import User

router = APIRouter()
logger = logging.getLogger(__name__)

# =============================================================================
# PYDANTIC REQUEST/RESPONSE MODELS
# =============================================================================

class BehavioralDataRequest(BaseModel):
    """Request model for behavioral data analysis"""
    user_id: int
    avg_pressure: float = Field(..., description="Average touch pressure (0.0-2.0)")
    avg_swipe_velocity: float = Field(..., description="Average swipe velocity (0.0-10.0)")
    avg_swipe_duration: float = Field(..., description="Average swipe duration in seconds")
    accel_stability: float = Field(..., description="Accelerometer stability (0.0-1.0)")
    gyro_stability: float = Field(..., description="Gyroscope stability (0.0-1.0)")
    touch_frequency: float = Field(..., description="Touch frequency per minute")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device metadata")

class TrustPredictionResponse(BaseModel):
    """Response model for trust prediction"""
    success: bool
    trust_score: float
    trust_category: str
    personal_threshold: float
    is_below_threshold: bool
    mirage_activated: bool
    mirage_intensity: Optional[str]
    security_action: str
    user_message: str
    session_count: int
    learning_phase: bool
    session_id: Optional[int] = None

class ThresholdAnalysisResponse(BaseModel):
    """Response model for threshold analysis"""
    user_id: int
    current_threshold: float
    recommended_threshold: float
    adjustment_reason: str
    confidence: float
    threshold_history: list

# =============================================================================
# MAIN TRUST PREDICTION ENDPOINT
# =============================================================================

@router.post("/predict-trust", response_model=TrustPredictionResponse)
async def predict_trust_score(
    request: BehavioralDataRequest,
    db: Session = Depends(get_db)
):
    """
    🎯 MAIN TRUST PREDICTION ENDPOINT
    This is the core API that Member 3's Flutter app calls!
    Integrates Member 1's AI model + your dynamic thresholds + mirage interface
    """
    try:
        logger.info(f"🎯 Trust prediction requested for user {request.user_id}")
        
        # 1. EXTRACT BEHAVIORAL FEATURES
        behavioral_data = {
            "avg_pressure": request.avg_pressure,
            "avg_swipe_velocity": request.avg_swipe_velocity,
            "avg_swipe_duration": request.avg_swipe_duration,
            "accel_stability": request.accel_stability,
            "gyro_stability": request.gyro_stability,
            "touch_frequency": request.touch_frequency
        }
        
        logger.info(f"   Behavioral features: {behavioral_data}")
        
        # 2. GET AI TRUST PREDICTION (FIXED - No await)
        trust_predictor = get_trust_predictor()
        trust_score = trust_predictor.predict_trust_score(behavioral_data)
        trust_category = trust_predictor.get_trust_category(trust_score)
        
        logger.info(f"   AI Trust Score: {trust_score:.2f}% ({trust_category})")
        
        # 3. GET USER'S PERSONAL THRESHOLD
        trust_profile = get_trust_profile(db, request.user_id)
        if not trust_profile:
            # Create initial profile for new user
            from database.crud import create_trust_profile
            trust_profile = create_trust_profile(db, request.user_id)
            logger.info(f"   Created new trust profile for user {request.user_id}")
        
        personal_threshold = trust_profile.personal_threshold
        session_count = trust_profile.session_count
        is_learning_phase = trust_profile.is_learning_phase
        
        logger.info(f"   Personal threshold: {personal_threshold}%")
        logger.info(f"   Session count: {session_count}")
        
        # 4. DETERMINE IF BELOW THRESHOLD (SUSPICIOUS)
        is_below_threshold = trust_score < personal_threshold
        
        # 5. GET SECURITY RECOMMENDATION
        security_rec = trust_predictor.get_security_recommendation(trust_score)
        security_action = security_rec["action"]
        user_message = security_rec["message"]
        
        # 6. INITIALIZE MIRAGE VARIABLES
        mirage_activated = False
        mirage_intensity = None
        session_id = None
        
        # 7. ACTIVATE MIRAGE IF NEEDED (FIXED - await only for async functions)
        if is_below_threshold:
            try:
                logger.warning(f"🚨 ACTIVATING MIRAGE - Trust Score: {trust_score:.2f}%, Threshold: {personal_threshold}%")
                
                # Get mirage controller
                mirage_controller = get_mirage_controller()
                
                # FIXED: activate_mirage is async, so we await it
                mirage_result = await mirage_controller.activate_mirage(
                    user_id=request.user_id,
                    trust_score=trust_score,
                    session_id=session_id,
                    intensity="high" if trust_score < 20 else "moderate"
                )
                
                # Set response based on actual activation
                if mirage_result.get("mirage_activated", False):
                    mirage_activated = True
                    mirage_intensity = mirage_result.get("intensity_level", "high")
                    security_action = "maximum_security"
                    user_message = "High security mode enabled."
                    logger.warning(f"✅ MIRAGE ACTIVATED for user {request.user_id}")
                else:
                    logger.error(f"❌ Mirage activation failed: {mirage_result}")
                    
            except Exception as e:
                logger.error(f"❌ Mirage activation exception: {str(e)}")
                mirage_activated = False
        
        # 8. UPDATE USER'S TRUST PROFILE
        updated_profile = update_trust_profile(
            db=db,
            user_id=request.user_id,
            trust_score=trust_score,
            behavioral_data=behavioral_data
        )
        
        # 9. STORE BEHAVIORAL DATA RECORD
        store_behavioral_data(
            db=db,
            user_id=request.user_id,
            session_id=session_id,
            behavioral_data=behavioral_data,
            trust_score=trust_score,
            mirage_triggered=mirage_activated
        )
        
        # 10. RETURN COMPREHENSIVE RESPONSE
        response = TrustPredictionResponse(
            success=True,
            trust_score=trust_score,
            trust_category=trust_category,
            personal_threshold=personal_threshold,
            is_below_threshold=is_below_threshold,
            mirage_activated=mirage_activated,
            mirage_intensity=mirage_intensity,
            security_action=security_action,
            user_message=user_message,
            session_count=updated_profile.session_count,
            learning_phase=updated_profile.is_learning_phase,
            session_id=session_id
        )
        
        logger.info(f"✅ Trust prediction completed for user {request.user_id}")
        logger.info(f"   Final result: {trust_score:.2f}% ({trust_category})")
        logger.info(f"   Mirage activated: {mirage_activated}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Trust prediction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Trust prediction failed: {str(e)}"
        )

# =============================================================================
# TRUST ANALYSIS ENDPOINTS
# =============================================================================

@router.get("/threshold-analysis/{user_id}", response_model=ThresholdAnalysisResponse)
async def analyze_user_threshold(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Analyze and recommend optimal threshold for user"""
    try:
        trust_profile = get_trust_profile(db, user_id)
        if not trust_profile:
            raise HTTPException(status_code=404, detail="User trust profile not found")
        
        # Parse score history
        import json
        score_history = json.loads(trust_profile.score_history or "[]")
        
        if len(score_history) < 3:
            return ThresholdAnalysisResponse(
                user_id=user_id,
                current_threshold=trust_profile.personal_threshold,
                recommended_threshold=trust_profile.personal_threshold,
                adjustment_reason="Insufficient data for analysis (need 3+ sessions)",
                confidence=0.3,
                threshold_history=score_history
            )
        
        # Calculate statistics
        recent_scores = [entry["score"] for entry in score_history[-10:]]
        avg_score = sum(recent_scores) / len(recent_scores)
        min_score = min(recent_scores)
        score_variance = sum((s - avg_score) ** 2 for s in recent_scores) / len(recent_scores)
        
        # Determine recommended threshold
        if avg_score > 80 and min_score > 70:
            recommended_threshold = 60.0  # User is very consistent, can use higher threshold
            reason = "Consistent high trust scores - threshold can be increased"
        elif avg_score < 50 or min_score < 30:
            recommended_threshold = 25.0  # User has low scores, lower threshold needed
            reason = "Low trust scores detected - threshold should be decreased"
        elif score_variance > 400:
            recommended_threshold = 35.0  # High variance, use conservative threshold
            reason = "High variance in trust scores - conservative threshold recommended"
        else:
            recommended_threshold = trust_profile.personal_threshold
            reason = "Current threshold is optimal for user's behavioral patterns"
        
        confidence = min(1.0, len(score_history) / 20.0)  # Higher confidence with more data
        
        return ThresholdAnalysisResponse(
            user_id=user_id,
            current_threshold=trust_profile.personal_threshold,
            recommended_threshold=recommended_threshold,
            adjustment_reason=reason,
            confidence=confidence,
            threshold_history=score_history[-20:]  # Last 20 sessions
        )
        
    except Exception as e:
        logger.error(f"Threshold analysis failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Threshold analysis failed: {str(e)}")

@router.get("/user-trust-history/{user_id}")
async def get_user_trust_history(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's trust score history"""
    try:
        from database.crud import get_user_trust_history
        history = get_user_trust_history(db, user_id, limit)
        
        trust_data = []
        for record in history:
            trust_data.append({
                "timestamp": record.timestamp.isoformat(),
                "trust_score": record.trust_score,
                "avg_pressure": record.avg_pressure,
                "avg_swipe_velocity": record.avg_swipe_velocity,
                "avg_swipe_duration": record.avg_swipe_duration,
                "accel_stability": record.accel_stability,
                "gyro_stability": record.gyro_stability,
                "touch_frequency": record.touch_frequency,
                "mirage_triggered": record.mirage_triggered
            })
        
        return {
            "user_id": user_id,
            "total_records": len(trust_data),
            "trust_history": trust_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get trust history for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get trust history: {str(e)}")

@router.post("/compare-baseline/{user_id}")
async def compare_to_baseline(
    user_id: int,
    current_score: float,
    db: Session = Depends(get_db)
):
    """Compare current trust score to user's baseline"""
    try:
        trust_profile = get_trust_profile(db, user_id)
        if not trust_profile:
            raise HTTPException(status_code=404, detail="User trust profile not found")
        
        baseline_score = trust_profile.average_trust_score
        difference = current_score - baseline_score
        
        if abs(difference) < 10:
            deviation_level = "normal"
            message = "Trust score is within normal range for this user"
        elif abs(difference) < 25:
            deviation_level = "moderate"
            message = f"Trust score deviates moderately from baseline ({'higher' if difference > 0 else 'lower'})"
        else:
            deviation_level = "significant"
            message = f"Significant deviation from baseline ({'much higher' if difference > 0 else 'much lower'})"
        
        return {
            "user_id": user_id,
            "current_score": current_score,
            "baseline_score": baseline_score,
            "difference": difference,
            "deviation_level": deviation_level,
            "message": message,
            "session_count": trust_profile.session_count
        }
        
    except Exception as e:
        logger.error(f"Baseline comparison failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Baseline comparison failed: {str(e)}")

# =============================================================================
# PROTECTED TRUST ENDPOINTS
# =============================================================================

@router.get("/my-trust-stats")
async def get_my_trust_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trust statistics for authenticated user"""
    return await get_user_trust_history(current_user.id, 10, db)

@router.get("/my-threshold-analysis")
async def get_my_threshold_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get threshold analysis for authenticated user"""
    return await analyze_user_threshold(current_user.id, db)
