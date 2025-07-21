from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from database.database import get_db
from database.crud import UserCRUD, SessionCRUD, TrustScoreCRUD
from database.models import User
from schemas.user_schemas import UserProfile, UserUpdate, UserStats, UserSessionInfo, UserSecurityReport
from services.auth_service import AuthService, get_current_active_user
from services.security_service import SecurityService
from utils.performance_utils import async_cache

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
security_service = SecurityService()

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed user profile information"""
    try:
        return UserProfile(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            phone_number=current_user.phone_number,
            date_of_birth=current_user.date_of_birth,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
            device_model=current_user.device_model,
            os_version=current_user.os_version,
            app_version=current_user.app_version
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    user_updates: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    try:
        # Sanitize input data
        update_data = {}
        
        if user_updates.full_name:
            update_data["full_name"] = security_service.sanitize_input(user_updates.full_name)
        
        if user_updates.phone_number:
            update_data["phone_number"] = security_service.sanitize_input(user_updates.phone_number)
        
        if user_updates.date_of_birth:
            update_data["date_of_birth"] = user_updates.date_of_birth
        
        if user_updates.device_model:
            update_data["device_model"] = security_service.sanitize_input(user_updates.device_model)
        
        if user_updates.os_version:
            update_data["os_version"] = security_service.sanitize_input(user_updates.os_version)
        
        if user_updates.app_version:
            update_data["app_version"] = security_service.sanitize_input(user_updates.app_version)
        
        # Update user
        updated_user = UserCRUD.update_user(db, current_user.id, **update_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"✅ User profile updated: {current_user.username}")
        
        return UserProfile(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            full_name=updated_user.full_name,
            phone_number=updated_user.phone_number,
            date_of_birth=updated_user.date_of_birth,
            is_active=updated_user.is_active,
            is_verified=updated_user.is_verified,
            created_at=updated_user.created_at,
            last_login=updated_user.last_login,
            device_model=updated_user.device_model,
            os_version=updated_user.os_version,
            app_version=updated_user.app_version
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@router.get("/stats", response_model=UserStats)
@async_cache(ttl_seconds=300)  # Cache for 5 minutes
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive user statistics"""
    try:
        stats = UserCRUD.get_user_stats(db, current_user.id)
        
        return UserStats(
            user_id=stats["user_id"],
            username=stats["username"],
            total_sessions=stats["total_sessions"],
            active_sessions=stats["active_sessions"],
            avg_trust_score=stats["avg_trust_score"],
            total_trust_scores=stats["total_trust_scores"],
            tamper_events=stats["tamper_events"],
            mirage_events=stats["mirage_events"],
            account_age_days=stats["account_age_days"],
            last_login=stats["last_login"]
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )

@router.get("/sessions", response_model=List[UserSessionInfo])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get user's recent sessions"""
    try:
        sessions = db.query(SessionCRUD.get_session.__annotations__['return'].__args__[0]).filter(
            SessionCRUD.get_session.__annotations__['return'].__args__[0].user_id == current_user.id
        ).order_by(
            SessionCRUD.get_session.__annotations__['return'].__args__[0].session_start.desc()
        ).limit(limit).all()
        
        session_info_list = []
        
        for session in sessions:
            # Calculate session duration
            if session.session_end:
                duration_minutes = (session.session_end - session.session_start).total_seconds() / 60
            else:
                duration_minutes = (datetime.utcnow() - session.session_start).total_seconds() / 60
            
            session_info = UserSessionInfo(
                session_id=str(session.session_uuid),
                started_at=session.session_start,
                last_activity=session.last_activity,
                duration_minutes=round(duration_minutes, 2),
                ip_address=session.ip_address,
                user_agent=session.user_agent[:100] if session.user_agent else None,
                is_active=session.is_active
            )
            session_info_list.append(session_info)
        
        return session_info_list
        
    except Exception as e:
        logger.error(f"❌ Failed to get user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user sessions"
        )

@router.get("/security-report", response_model=UserSecurityReport)
async def get_user_security_report(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=90)
):
    """Get comprehensive security report for user"""
    try:
        # Get trust score analytics
        trust_analytics = TrustScoreCRUD.get_trust_score_analytics(db, current_user.id, days)
        
        # Calculate security score
        security_score = _calculate_user_security_score(trust_analytics)
        
        # Determine risk level
        if security_score >= 90:
            risk_level = "very_low"
        elif security_score >= 75:
            risk_level = "low"
        elif security_score >= 60:
            risk_level = "medium"
        elif security_score >= 40:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        # Generate recommendations
        recommendations = _generate_security_recommendations(trust_analytics, risk_level)
        
        # Get session data
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        total_logins = db.query(SessionCRUD.get_session.__annotations__['return'].__args__[0]).filter(
            SessionCRUD.get_session.__annotations__['return'].__args__[0].user_id == current_user.id,
            SessionCRUD.get_session.__annotations__['return'].__args__[0].session_start >= cutoff_date
        ).count()
        
        return UserSecurityReport(
            user_id=current_user.id,
            report_period_days=days,
            security_score=security_score,
            risk_level=risk_level,
            total_logins=total_logins,
            failed_login_attempts=current_user.failed_login_attempts,
            mirage_activations=trust_analytics.get("mirage_triggers", 0),
            trust_score_trend=trust_analytics.get("trend", "stable"),
            recommendations=recommendations,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to generate security report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate security report"
        )

@router.delete("/account")
async def delete_user_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    confirmation: str = Query(..., description="Type 'DELETE' to confirm")
):
    """Delete user account (soft delete)"""
    try:
        if confirmation != "DELETE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account deletion not confirmed. Type 'DELETE' to confirm."
            )
        
        # Soft delete - deactivate user instead of removing data
        UserCRUD.update_user(
            db, 
            current_user.id, 
            is_active=False,
            email=f"deleted_{current_user.id}@deleted.nethra"
        )
        
        # End all active sessions
        SessionCRUD.cleanup_expired_sessions(db, timeout_minutes=0)
        
        logger.warning(f"🗑️ User account deleted: {current_user.username}")
        
        return {
            "message": "Account successfully deleted",
            "deleted_at": datetime.utcnow().isoformat(),
            "data_retention": "Personal data will be anonymized after 30 days"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Account deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account deletion failed"
        )

@router.post("/export-data")
async def export_user_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export user data (GDPR compliance)"""
    try:
        # Get user data
        user_data = {
            "user_profile": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "created_at": current_user.created_at.isoformat(),
                "last_login": current_user.last_login.isoformat() if current_user.last_login else None
            }
        }
        
        # Get sessions (last 100)
        sessions = SessionCRUD.get_active_sessions(db, current_user.id)
        user_data["sessions"] = [
            {
                "session_start": session.session_start.isoformat(),
                "session_end": session.session_end.isoformat() if session.session_end else None,
                "duration_minutes": (
                    (session.session_end or datetime.utcnow()) - session.session_start
                ).total_seconds() / 60
            }
            for session in sessions[:100]
        ]
        
        # Get trust scores (aggregated, no raw behavioral data)
        trust_scores = TrustScoreCRUD.get_user_trust_scores(db, current_user.id, limit=100)
        user_data["trust_analytics"] = {
            "total_evaluations": len(trust_scores),
            "average_trust_score": sum(ts.trust_score for ts in trust_scores) / len(trust_scores) if trust_scores else 0,
            "date_range": {
                "from": trust_scores[-1].timestamp.isoformat() if trust_scores else None,
                "to": trust_scores[0].timestamp.isoformat() if trust_scores else None
            }
        }
        
        user_data["export_metadata"] = {
            "exported_at": datetime.utcnow().isoformat(),
            "export_version": "1.0",
            "note": "Behavioral biometric data is not included for security reasons"
        }
        
        logger.info(f"📤 Data export generated for user: {current_user.username}")
        
        return user_data
        
    except Exception as e:
        logger.error(f"❌ Data export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data export failed"
        )

# Helper functions
def _calculate_user_security_score(trust_analytics: Dict[str, Any]) -> float:
    """Calculate overall security score for user"""
    base_score = 100.0
    
    try:
        # Deduct for threshold breaches
        if trust_analytics.get("total_scores", 0) > 0:
            breach_rate = trust_analytics.get("scores_below_threshold", 0) / trust_analytics["total_scores"]
            base_score -= (breach_rate * 40)
        
        # Deduct for mirage activations
        mirage_rate = trust_analytics.get("mirage_triggers", 0) / max(trust_analytics.get("total_scores", 1), 1)
        base_score -= (mirage_rate * 30)
        
        # Bonus for consistent behavior
        if trust_analytics.get("trend") == "improving":
            base_score += 10
        elif trust_analytics.get("trend") == "stable" and trust_analytics.get("avg_score", 0) > 70:
            base_score += 5
        
        return max(0, min(100, base_score))
        
    except Exception:
        return 50.0  # Neutral score on error

def _generate_security_recommendations(trust_analytics: Dict[str, Any], risk_level: str) -> List[str]:
    """Generate personalized security recommendations"""
    recommendations = []
    
    try:
        if risk_level in ["high", "critical"]:
            recommendations.append("Consider updating your device's security settings")
            recommendations.append("Review recent account activity for any suspicious behavior")
            recommendations.append("Ensure your device has the latest security updates")
        
        if trust_analytics.get("trend") == "declining":
            recommendations.append("Your behavioral patterns have been changing - this may indicate device issues")
            recommendations.append("Try using the app in a consistent environment")
        
        if trust_analytics.get("mirage_triggers", 0) > 0:
            recommendations.append("Recent security interventions were activated - review your usage patterns")
            recommendations.append("Consider re-training your behavioral profile if needed")
        
        # Always add general recommendations
        recommendations.extend([
            "Keep your app updated to the latest version",
            "Use the app regularly to maintain accurate behavioral patterns",
            "Contact support if you notice any unusual security alerts"
        ])
        
        return recommendations[:5]  # Limit to 5 recommendations
        
    except Exception:
        return ["Contact support for personalized security recommendations"]
