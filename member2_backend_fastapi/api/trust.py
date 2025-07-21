from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from database.database import get_db
from database.crud import TrustScoreCRUD, TrustProfileCRUD, SessionCRUD, MirageEventCRUD
from database.models import User
from schemas.trust_schemas import (
    TrustPredictionRequest, TrustPredictionResponse, 
    TrustProfileResponse, TrustAnalyticsResponse,
    MirageEventResponse, BatchTrustRequest
)
from services.auth_service import AuthService
from services.trust_service import TrustService
from services.threshold_manager import ThresholdManager
from services.mirage_service import MirageService
from scripts.integrated_backend import get_nethra_backend
from utils.performance_utils import async_cache
from middleware.rate_limit import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
trust_service = TrustService()
threshold_manager = ThresholdManager()
mirage_service = MirageService()

@router.post("/predict", response_model=TrustPredictionResponse)
@rate_limit(max_requests=100, window_seconds=60)
async def predict_trust_score(
    prediction_request: TrustPredictionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Predict trust score for user based on behavioral data
    
    This is the main endpoint that Flutter app will call for continuous authentication
    """
    try:
        start_time = datetime.utcnow()
        
        # Get NETHRA backend instance
        backend = get_nethra_backend()
        
        # Prepare context data
        context = {
            "ip_address": prediction_request.context.get("ip_address"),
            "device_info": prediction_request.context.get("device_info"),
            "app_version": prediction_request.context.get("app_version"),
            "critical_action": prediction_request.context.get("critical_action", False),
            "transaction_amount": prediction_request.context.get("transaction_amount"),
            "location": prediction_request.context.get("location")
        }
        
        # Get or create active session
        active_sessions = SessionCRUD.get_active_sessions(db, current_user.id)
        if active_sessions:
            session = active_sessions[0]
            SessionCRUD.update_session_activity(db, session.id)
        else:
            session = SessionCRUD.create_session(
                db=db,
                user_id=current_user.id,
                ip_address=context.get("ip_address"),
                user_agent=context.get("device_info", "")
            )
        
        # Perform trust prediction using integrated backend
        result = backend.authenticate_user(
            user_id=current_user.id,
            sensor_data=prediction_request.sensor_data,
            session_id=session.id,
            context=context
        )
        
        # Handle Mirage activation if needed
        mirage_details = None
        if result["trigger_mirage"]:
            mirage_event = await mirage_service.trigger_mirage(
                user_id=current_user.id,
                session_id=session.id,
                trust_score=result["trust_score"],
                threshold=result["user_threshold"],
                reason=result["reason"]
            )
            
            mirage_details = {
                "mirage_type": mirage_event.get("mirage_type"),
                "intensity": mirage_event.get("intensity"),
                "duration_estimate": mirage_event.get("duration_estimate"),
                "cognitive_challenge": mirage_event.get("cognitive_challenge")
            }
        
        # Prepare response
        response = TrustPredictionResponse(
            trust_score=result["trust_score"],
            confidence_score=result["confidence_score"],
            user_threshold=result["user_threshold"],
            status=result["status"],
            action=result["action"],
            trigger_mirage=result["trigger_mirage"],
            reason=result["reason"],
            session_id=str(session.session_uuid),
            timestamp=result["timestamp"],
            inference_time_ms=result["inference_time_ms"],
            model_version=result["model_version"],
            mirage_details=mirage_details
        )
        
        # Background task for analytics update
        background_tasks.add_task(
            update_session_analytics,
            session.id,
            result["trust_score"],
            result["trigger_mirage"]
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"🎯 Trust prediction completed for user {current_user.id}: "
                   f"score={result['trust_score']:.2f}, action={result['action']}, "
                   f"processing_time={processing_time:.2f}ms")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Trust prediction failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trust prediction failed: {str(e)}"
        )

@router.get("/profile", response_model=TrustProfileResponse)
@async_cache(ttl_seconds=300)  # Cache for 5 minutes
async def get_trust_profile(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's trust profile and learning status"""
    try:
        trust_profile = TrustProfileCRUD.get_trust_profile(db, current_user.id)
        
        if not trust_profile:
            trust_profile = TrustProfileCRUD.create_trust_profile(db, current_user.id)
        
        # Get recent trust scores for additional insights
        recent_scores = TrustScoreCRUD.get_user_trust_scores(db, current_user.id, limit=10)
        recent_score_values = [score.trust_score for score in recent_scores]
        
        return TrustProfileResponse(
            user_id=current_user.id,
            avg_trust_score=trust_profile.avg_trust_score,
            personal_threshold=trust_profile.personal_threshold,
            sessions_count=trust_profile.sessions_count,
            learning_complete=trust_profile.learning_complete,
            risk_level=trust_profile.risk_level,
            dominant_pattern=trust_profile.dominant_interaction_pattern,
            recent_scores=recent_score_values,
            last_updated=trust_profile.updated_at,
            threshold_confidence=trust_profile.threshold_confidence or 0.8
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get trust profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trust profile"
        )

@router.get("/analytics", response_model=TrustAnalyticsResponse)
async def get_trust_analytics(
    days: int = 30,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed trust analytics for user"""
    try:
        # Get trust score analytics
        analytics = TrustScoreCRUD.get_trust_score_analytics(db, current_user.id, days)
        
        # Get mirage analytics
        mirage_analytics = MirageEventCRUD.get_mirage_analytics(db, days)
        
        # Get session statistics
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        sessions = db.query(Session).filter(
            Session.user_id == current_user.id,
            Session.session_start >= cutoff_date
        ).all()
        
        avg_session_duration = 0
        if sessions:
            durations = []
            for session in sessions:
                if session.session_end:
                    duration = (session.session_end - session.session_start).total_seconds() / 60
                    durations.append(duration)
            
            if durations:
                avg_session_duration = sum(durations) / len(durations)
        
        return TrustAnalyticsResponse(
            period_days=days,
            total_trust_scores=analytics["total_scores"],
            average_trust_score=analytics["avg_score"],
            trust_trend=analytics["trend"],
            threshold_breaches=analytics["scores_below_threshold"],
            mirage_activations=analytics["mirage_triggers"],
            total_sessions=len(sessions),
            avg_session_duration_minutes=avg_session_duration,
            risk_incidents=mirage_analytics.get("total_events", 0),
            security_score=calculate_security_score(analytics, mirage_analytics)
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get analytics for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )

@router.post("/batch-predict")
@rate_limit(max_requests=10, window_seconds=60)
async def batch_predict_trust_scores(
    batch_request: BatchTrustRequest,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Batch prediction for multiple sensor data points (for testing/demo)"""
    try:
        backend = get_nethra_backend()
        results = []
        
        for i, sensor_data in enumerate(batch_request.sensor_data_list):
            try:
                result = backend.authenticate_user(
                    user_id=current_user.id,
                    sensor_data=sensor_data,
                    context={"batch_index": i}
                )
                results.append({
                    "index": i,
                    "trust_score": result["trust_score"],
                    "status": result["status"],
                    "trigger_mirage": result["trigger_mirage"]
                })
            except Exception as e:
                results.append({
                    "index": i,
                    "error": str(e),
                    "status": "ERROR"
                })
        
        return {
            "batch_id": f"batch_{datetime.utcnow().timestamp()}",
            "total_predictions": len(batch_request.sensor_data_list),
            "successful_predictions": len([r for r in results if "error" not in r]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Batch prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch prediction failed"
        )

@router.get("/mirage-events", response_model=List[MirageEventResponse])
async def get_mirage_events(
    limit: int = 50,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's mirage events history"""
    try:
        events = db.query(MirageEvent).filter(
            MirageEvent.user_id == current_user.id
        ).order_by(MirageEvent.triggered_at.desc()).limit(limit).all()
        
        return [
            MirageEventResponse(
                id=event.id,
                triggered_at=event.triggered_at,
                mirage_type=event.mirage_type,
                trigger_reason=event.trigger_reason,
                trust_score_at_trigger=event.trust_score_at_trigger,
                threshold_at_trigger=event.threshold_at_trigger,
                duration_seconds=event.mirage_duration_seconds,
                successful=event.mirage_successful,
                legitimate_user_affected=event.legitimate_user_affected
            )
            for event in events
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to get mirage events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve mirage events"
        )

@router.post("/threshold/update")
async def update_personal_threshold(
    new_threshold: float,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Manually update personal threshold (admin/testing feature)"""
    try:
        if not (0 <= new_threshold <= 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Threshold must be between 0 and 100"
            )
        
        trust_profile = TrustProfileCRUD.get_trust_profile(db, current_user.id)
        if not trust_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trust profile not found"
            )
        
        # Update threshold
        trust_profile.personal_threshold = new_threshold
        trust_profile.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Threshold updated for user {current_user.id}: {new_threshold}")
        
        return {
            "message": "Threshold updated successfully",
            "new_threshold": new_threshold,
            "previous_threshold": trust_profile.personal_threshold
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Threshold update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Threshold update failed"
        )

@router.get("/model-info")
async def get_model_info():
    """Get information about the AI model"""
    try:
        backend = get_nethra_backend()
        model_info = backend.get_model_info()
        performance_stats = backend.get_performance_stats()
        
        return {
            "model_info": model_info,
            "performance_stats": performance_stats,
            "health_status": backend.health_check()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model information"
        )

# Background task functions
async def update_session_analytics(session_id: int, trust_score: float, mirage_triggered: bool):
    """Background task to update session analytics"""
    try:
        with get_db_session() as db:
            session = SessionCRUD.get_session(db, session_id)
            if session:
                # Update session trust metrics
                if session.initial_trust_score is None:
                    session.initial_trust_score = trust_score
                
                session.current_trust_score = trust_score
                
                if session.min_trust_score is None or trust_score < session.min_trust_score:
                    session.min_trust_score = trust_score
                
                if session.max_trust_score is None or trust_score > session.max_trust_score:
                    session.max_trust_score = trust_score
                
                if mirage_triggered:
                    session.mirage_trigger_count += 1
                
                db.commit()
                
    except Exception as e:
        logger.error(f"❌ Session analytics update failed: {e}")

def calculate_security_score(trust_analytics: Dict, mirage_analytics: Dict) -> float:
    """Calculate overall security score for user"""
    try:
        base_score = 100.0
        
        # Deduct points for threshold breaches
        if trust_analytics["total_scores"] > 0:
            breach_rate = trust_analytics["scores_below_threshold"] / trust_analytics["total_scores"]
            base_score -= (breach_rate * 30)  # Up to 30 points deduction
        
        # Deduct points for mirage activations
        mirage_rate = mirage_analytics.get("total_events", 0) / max(trust_analytics["total_scores"], 1)
        base_score -= (mirage_rate * 20)  # Up to 20 points deduction
        
        # Bonus for consistent good behavior
        if trust_analytics["trend"] == "improving":
            base_score += 5
        elif trust_analytics["trend"] == "stable" and trust_analytics["avg_score"] > 70:
            base_score += 3
        
        return max(0, min(100, base_score))
        
    except Exception:
        return 50.0  # Default neutral score
