from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime
import psutil
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    ai_model: str
    mirage_controller: str
    uptime: str
    version: str

class SystemMetrics(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_sessions: int
    total_users: int
    mirage_sessions_active: int

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check"""
    try:
        # Check database
        from database.database import check_database_health
        db_healthy = check_database_health()
        
        # Check AI model
        try:
            from services.ai_interface import get_trust_predictor
            predictor = get_trust_predictor()
            ai_healthy = predictor.model is not None
        except:
            ai_healthy = False
        
        # Check mirage controller
        try:
            from services.mirage_controller import get_mirage_controller
            mirage = get_mirage_controller()
            mirage_healthy = True
        except:
            mirage_healthy = False
        
        overall_status = "healthy" if all([db_healthy, ai_healthy, mirage_healthy]) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            database="connected" if db_healthy else "error",
            ai_model="loaded" if ai_healthy else "error",
            mirage_controller="active" if mirage_healthy else "error",
            uptime="active",
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Health check failed")

@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics():
    """Get system performance metrics"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application metrics (simplified for hackathon)
        active_sessions = 0  # Would query database in production
        total_users = 0      # Would query database in production
        mirage_sessions = 0  # Would query mirage controller
        
        return SystemMetrics(
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            active_sessions=active_sessions,
            total_users=total_users,
            mirage_sessions_active=mirage_sessions
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

@router.get("/trust-metrics")
async def get_trust_metrics():
    """Get NETHRA-specific trust metrics"""
    try:
        # This would be populated with real data in production
        metrics = {
            "total_trust_predictions": 0,
            "average_trust_score": 65.5,
            "mirage_activations_today": 0,
            "users_in_learning_phase": 0,
            "trust_score_distribution": {
                "0-25": 5,
                "26-50": 15,
                "51-75": 60,
                "76-100": 20
            },
            "mirage_effectiveness": 85.2,
            "false_positive_rate": 2.1
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get trust metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get trust metrics")

# Prometheus metrics endpoint (if you add monitoring later)
@router.get("/prometheus")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return "# NETHRA metrics endpoint - implement with prometheus_client library"
