from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
import logging

from database.database import get_db
from database.crud import get_user_by_id, get_trust_profile
from api.auth_endpoints import get_current_user
from database.models import User

router = APIRouter()
logger = logging.getLogger(__name__)

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    created_at: str
    is_active: bool
    session_count: Optional[int] = 0
    average_trust_score: Optional[float] = 50.0
    personal_threshold: Optional[float] = 40.0
    is_learning_phase: Optional[bool] = True

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile with trust information"""
    try:
        # Get trust profile
        trust_profile = get_trust_profile(db, current_user.id)
        
        profile = UserProfile(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            created_at=current_user.created_at.isoformat(),
            is_active=current_user.is_active,
            session_count=trust_profile.session_count if trust_profile else 0,
            average_trust_score=trust_profile.average_trust_score if trust_profile else 50.0,
            personal_threshold=trust_profile.personal_threshold if trust_profile else 40.0,
            is_learning_phase=trust_profile.is_learning_phase if trust_profile else True
        )
        
        return profile
        
    except Exception as e:
        logger.error(f"Failed to get profile for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile")

@router.get("/trust-stats")
async def get_user_trust_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's trust statistics"""
    try:
        from services.threshold_manager import ThresholdManager
        
        threshold_manager = ThresholdManager(db)
        analysis = threshold_manager.get_threshold_analysis(current_user.id)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to get trust stats for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trust statistics")

@router.get("/behavioral-baseline")
async def get_behavioral_baseline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's behavioral baseline information"""
    try:
        trust_profile = get_trust_profile(db, current_user.id)
        
        if not trust_profile:
            return {
                "message": "No behavioral baseline established yet",
                "sessions_needed": 5
            }
        
        baseline = {
            "avg_pressure_baseline": trust_profile.avg_pressure_baseline,
            "avg_swipe_velocity_baseline": trust_profile.avg_swipe_velocity_baseline,
            "avg_swipe_duration_baseline": trust_profile.avg_swipe_duration_baseline,
            "accel_stability_baseline": trust_profile.accel_stability_baseline,
            "gyro_stability_baseline": trust_profile.gyro_stability_baseline,
            "touch_frequency_baseline": trust_profile.touch_frequency_baseline,
            "established_sessions": trust_profile.session_count,
            "is_baseline_ready": not trust_profile.is_learning_phase
        }
        
        return baseline
        
    except Exception as e:
        logger.error(f"Failed to get behavioral baseline for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve behavioral baseline")
