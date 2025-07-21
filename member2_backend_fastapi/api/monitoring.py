from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text  # CRITICAL FIX for SQLAlchemy 2.x
from typing import Dict, Any
from datetime import datetime
import logging
import time

from database.database import get_db, SessionLocal
from utils.performance_utils import get_performance_stats
from scripts.integrated_backend import get_nethra_backend

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitor", tags=["monitoring"])

def check_database_health() -> Dict[str, Any]:
    """
    Proper database health check with SQLAlchemy 2.x compatibility
    """
    try:
        # Create direct database connection
        db = SessionLocal()
        
        # Test 1: Basic connection - FIXED with text()
        result = db.execute(text("SELECT 1 as test")).fetchone()
        
        if not result:
            db.close()
            return {"status": "unhealthy", "error": "No query result"}
        
        # Test 2: Table existence - FIXED with text()
        tables_result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('users', 'trust_profiles', 'trust_scores')
        """)).fetchall()
        
        table_names = [row[0] for row in tables_result]
        expected_tables = ['users', 'trust_profiles', 'trust_scores']
        missing_tables = [table for table in expected_tables if table not in table_names]
        
        # Test 3: User table access - FIXED with text()
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
        
        # Test 4: Database responsiveness - FIXED with text()
        start_time = time.time()
        db.execute(text("SELECT sqlite_version()")).fetchone()
        response_time = (time.time() - start_time) * 1000
        
        db.close()
        
        if missing_tables:
            return {
                "status": "unhealthy", 
                "error": f"Missing tables: {missing_tables}",
                "tables_found": table_names
            }
        
        # All tests passed
        return {
            "status": "healthy",
            "tables": table_names,
            "user_count": user_count,
            "connection_test": "passed",
            "response_time_ms": round(response_time, 2)
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__
        }

def check_ai_model_health() -> Dict[str, Any]:
    """
    Check AI model health status
    """
    try:
        backend = get_nethra_backend()
        health_info = backend.health_check()
        
        return {
            "status": "healthy" if health_info.get("model_loaded") else "degraded",
            "model_loaded": health_info.get("model_loaded", False),
            "model_version": health_info.get("model_version", "unknown"),
            "inference_count": health_info.get("inference_count", 0),
            "tensorflow_available": health_info.get("tensorflow_available", False)
        }
        
    except Exception as e:
        logger.error(f"AI model health check failed: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "model_loaded": False
        }

def get_system_stats() -> Dict[str, Any]:
    """
    Get system resource statistics (optional)
    """
    try:
        import psutil
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0
        }
    except ImportError:
        # psutil not available
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_usage": 0,
            "note": "System stats unavailable (psutil not installed)"
        }
    except Exception as e:
        logger.warning(f"System stats error: {e}")
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_usage": 0,
            "error": str(e)
        }

@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint - FIXED for SQLAlchemy 2.x
    """
    start_time = time.time()
    
    # Check database health
    db_health = check_database_health()
    
    # Check AI model health
    ai_health = check_ai_model_health()
    
    # Get system stats
    system_stats = get_system_stats()
    
    # Determine overall status
    overall_status = "healthy"
    if db_health["status"] == "unhealthy":
        overall_status = "unhealthy"
    elif db_health["status"] == "degraded" or ai_health["status"] == "degraded":
        overall_status = "degraded"
    
    health_response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_health["status"],
            "ai_model": ai_health["status"]
        },
        "details": {
            "database": db_health,
            "ai_model": ai_health,
            "system": system_stats
        },
        "version": "1.0.0",
        "response_time_ms": round((time.time() - start_time) * 1000, 2)
    }
    
    return health_response

@router.get("/status")
async def system_status():
    """
    Detailed system status endpoint
    """
    try:
        # Get performance stats
        perf_stats = get_performance_stats()
        
        # Get AI backend stats
        try:
            backend = get_nethra_backend()
            ai_stats = backend.get_performance_stats()
        except Exception as e:
            ai_stats = {"error": str(e)}
        
        # Database statistics - FIXED with text()
        db_stats = {}
        try:
            db = SessionLocal()
            
            # Get table row counts - FIXED with text()
            user_count = db.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
            session_count = db.execute(text("SELECT COUNT(*) FROM sessions")).fetchone()[0] if db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")).fetchone() else 0
            
            db_stats = {
                "user_count": user_count,
                "session_count": session_count,
                "database_size_kb": 0  # Could add file size check here
            }
            db.close()
            
        except Exception as e:
            db_stats = {"error": str(e)}
        
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "performance": perf_stats,
            "ai_backend": ai_stats,
            "database": db_stats,
            "system": get_system_stats()
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.get("/metrics")
async def get_metrics():
    """
    Prometheus-compatible metrics endpoint
    """
    try:
        db_health = check_database_health()
        ai_health = check_ai_model_health()
        system_stats = get_system_stats()
        
        metrics = []
        
        # Health metrics (0 or 1)
        metrics.append(f'nethra_database_healthy {1 if db_health["status"] == "healthy" else 0}')
        metrics.append(f'nethra_ai_model_healthy {1 if ai_health["status"] == "healthy" else 0}')
        
        # System metrics
        metrics.append(f'nethra_cpu_percent {system_stats.get("cpu_percent", 0)}')
        metrics.append(f'nethra_memory_percent {system_stats.get("memory_percent", 0)}')
        
        # Database metrics
        if db_health["status"] == "healthy":
            metrics.append(f'nethra_user_count {db_health.get("user_count", 0)}')
            metrics.append(f'nethra_db_response_time_ms {db_health.get("response_time_ms", 0)}')
        
        # AI metrics
        try:
            backend = get_nethra_backend()
            ai_stats = backend.get_performance_stats()
            metrics.append(f'nethra_total_predictions {ai_stats.get("total_predictions", 0)}')
            metrics.append(f'nethra_avg_inference_time_ms {ai_stats.get("avg_inference_time_ms", 0)}')
        except Exception:
            metrics.append(f'nethra_total_predictions 0')
            metrics.append(f'nethra_avg_inference_time_ms 0')
        
        # Uptime metric (in seconds)
        metrics.append(f'nethra_uptime_seconds {time.time()}')
        
        return "\n".join(metrics), {"Content-Type": "text/plain"}
        
    except Exception as e:
        logger.error(f"Metrics generation failed: {e}")
        # Return basic metrics even on error
        return f"nethra_status 0\nnethra_error 1\n# Error: {str(e)}", {"Content-Type": "text/plain"}

@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for load balancers
    """
    return {
        "status": "pong", 
        "timestamp": datetime.utcnow().isoformat(),
        "service": "NETHRA Guardian AI Backend",
        "version": "1.0.0"
    }

@router.get("/version")
async def version_info():
    """
    Version information endpoint
    """
    try:
        backend = get_nethra_backend()
        model_info = backend.get_model_info()
        
        return {
            "application": "NETHRA Guardian AI Backend",
            "version": "1.0.0",
            "model_version": model_info.get("model_version", "unknown"),
            "build_timestamp": datetime.utcnow().isoformat(),
            "features": [
                "JWT Authentication",
                "Behavioral Biometrics", 
                "Dynamic Thresholds",
                "Adaptive Mirage Interface",
                "Real-time Monitoring",
                "SQLAlchemy 2.x Compatible"
            ],
            "endpoints": {
                "health": "/monitor/health",
                "status": "/monitor/status", 
                "metrics": "/monitor/metrics",
                "ping": "/monitor/ping"
            }
        }
        
    except Exception as e:
        logger.error(f"Version info failed: {e}")
        return {
            "application": "NETHRA Guardian AI Backend",
            "version": "1.0.0",
            "error": "Model info unavailable",
            "features": [
                "JWT Authentication",
                "Behavioral Biometrics",
                "Dynamic Thresholds", 
                "Adaptive Mirage Interface",
                "Real-time Monitoring"
            ]
        }

@router.get("/ready")
async def readiness_check():
    """
    Kubernetes-style readiness check
    """
    db_health = check_database_health()
    ai_health = check_ai_model_health()
    
    ready = (db_health["status"] == "healthy" and 
             ai_health["status"] in ["healthy", "degraded"])
    
    if ready:
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": db_health["status"],
                "ai_model": ai_health["status"]
            }
        }
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "database": db_health["status"],
                    "ai_model": ai_health["status"]
                },
                "issues": [
                    service for service, status in {
                        "database": db_health["status"],
                        "ai_model": ai_health["status"]
                    }.items() if status == "unhealthy"
                ]
            }
        )

@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness check - simple ping
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_check": "passed"
    }
