import asyncio
import psutil
import time
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MonitoringService:
    """System monitoring service for NETHRA"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            "requests_total": 0,
            "requests_failed": 0,
            "trust_predictions": 0,
            "mirage_activations": 0,
            "average_response_time": 0.0
        }
    
    def record_request(self, success: bool = True, response_time: float = 0.0):
        """Record API request metrics"""
        self.metrics["requests_total"] += 1
        
        if not success:
            self.metrics["requests_failed"] += 1
        
        # Update average response time
        if response_time > 0:
            current_avg = self.metrics["average_response_time"]
            total_requests = self.metrics["requests_total"]
            
            self.metrics["average_response_time"] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )
    
    def record_trust_prediction(self, trust_score: float, mirage_activated: bool = False):
        """Record trust prediction metrics"""
        self.metrics["trust_predictions"] += 1
        
        if mirage_activated:
            self.metrics["mirage_activations"] += 1
    
    def get_system_metrics(self) -> Dict:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            uptime = time.time() - self.start_time
            
            return {
                "system": {
                    "cpu_usage_percent": cpu_percent,
                    "memory_usage_percent": memory.percent,
                    "memory_available_mb": memory.available // (1024 * 1024),
                    "uptime_seconds": int(uptime)
                },
                "application": self.metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            return {"error": str(e)}
    
    def get_health_status(self) -> Dict:
        """Get application health status"""
        try:
            # Check various components
            db_healthy = True  # Would check database connection
            ai_model_healthy = True  # Would check AI model status
            
            overall_status = "healthy" if all([db_healthy, ai_model_healthy]) else "degraded"
            
            return {
                "status": overall_status,
                "components": {
                    "database": "healthy" if db_healthy else "unhealthy",
                    "ai_model": "healthy" if ai_model_healthy else "unhealthy",
                    "mirage_controller": "healthy"
                },
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": int(time.time() - self.start_time)
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global monitoring service
_monitoring_service = None

def get_monitoring_service() -> MonitoringService:
    """Get or create global monitoring service"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service
