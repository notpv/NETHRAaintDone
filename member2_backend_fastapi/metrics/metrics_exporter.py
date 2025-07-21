import time
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.multiprocess import MultiProcessCollector
from prometheus_client import CollectorRegistry
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class PrometheusMetrics:
    """
    Prometheus metrics collector for NETHRA backend
    
    Tracks API performance, trust scores, security events, and system health
    """
    
    def __init__(self):
        # API Metrics
        self.http_requests_total = Counter(
            'nethra_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.http_request_duration_seconds = Histogram(
            'nethra_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
        )
        
        # Trust Score Metrics
        self.trust_scores_total = Counter(
            'nethra_trust_scores_total',
            'Total trust score predictions',
            ['user_threshold_category']
        )
        
        self.trust_score_distribution = Histogram(
            'nethra_trust_score_distribution',
            'Distribution of trust scores',
            buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        )
        
        self.ai_inference_duration_seconds = Histogram(
            'nethra_ai_inference_duration_seconds',
            'AI model inference time in seconds',
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
        )
        
        # Security Metrics
        self.mirage_activations_total = Counter(
            'nethra_mirage_activations_total',
            'Total mirage interface activations',
            ['mirage_type', 'intensity']
        )
        
        self.authentication_attempts_total = Counter(
            'nethra_authentication_attempts_total',
            'Total authentication attempts',
            ['result']  # success, failed_password, user_not_found, account_locked
        )
        
        self.security_events_total = Counter(
            'nethra_security_events_total',
            'Total security events',
            ['event_type', 'severity']
        )
        
        # System Health Metrics
        self.active_sessions_gauge = Gauge(
            'nethra_active_sessions',
            'Number of active user sessions'
        )
        
        self.database_operations_total = Counter(
            'nethra_database_operations_total',
            'Total database operations',
            ['operation_type', 'table', 'result']
        )
        
        self.cache_operations_total = Counter(
            'nethra_cache_operations_total',
            'Total cache operations',
            ['operation', 'result']  # hit, miss, set, delete
        )
        
        # User Behavior Metrics
        self.threshold_breaches_total = Counter(
            'nethra_threshold_breaches_total',
            'Total threshold breaches',
            ['severity']  # low, medium, high, critical
        )
        
        self.session_duration_seconds = Histogram(
            'nethra_session_duration_seconds',
            'User session duration in seconds',
            buckets=[60, 300, 600, 1800, 3600, 7200, 14400, 28800]  # 1min to 8hours
        )

# Global metrics instance
metrics = PrometheusMetrics()

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect HTTP metrics
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get endpoint path (normalized)
        endpoint = self._normalize_endpoint(request.url.path)
        method = request.method
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Record metrics
            processing_time = time.time() - start_time
            
            metrics.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            metrics.http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(processing_time)
            
            return response
            
        except Exception as e:
            # Record error metrics
            metrics.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=500
            ).inc()
            
            processing_time = time.time() - start_time
            metrics.http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(processing_time)
            
            raise
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint paths for consistent metrics"""
        # Remove trailing slashes
        path = path.rstrip('/')
        
        # Replace path parameters with placeholders
        if '/user/' in path and path.count('/') > 2:
            return '/user/{id}'
        elif '/trust/' in path and path.count('/') > 2:
            return '/trust/{endpoint}'
        elif path.startswith('/static/'):
            return '/static/*'
        
        return path or '/'

def record_trust_score_metrics(trust_score: float, threshold: float, 
                             inference_time: float, user_id: int = None):
    """Record trust score related metrics"""
    try:
        # Record trust score distribution
        metrics.trust_score_distribution.observe(trust_score)
        
        # Record AI inference time
        metrics.ai_inference_duration_seconds.observe(inference_time)
        
        # Categorize threshold for metrics
        if threshold <= 30:
            threshold_category = "low"
        elif threshold <= 60:
            threshold_category = "medium" 
        else:
            threshold_category = "high"
        
        metrics.trust_scores_total.labels(
            user_threshold_category=threshold_category
        ).inc()
        
        # Record threshold breach if applicable
        if trust_score < threshold:
            breach_severity = _calculate_breach_severity(trust_score, threshold)
            metrics.threshold_breaches_total.labels(severity=breach_severity).inc()
        
    except Exception as e:
        logger.error(f"Failed to record trust score metrics: {e}")

def record_mirage_activation(mirage_type: str, intensity: str):
    """Record mirage interface activation metrics"""
    try:
        metrics.mirage_activations_total.labels(
            mirage_type=mirage_type,
            intensity=intensity
        ).inc()
        
    except Exception as e:
        logger.error(f"Failed to record mirage metrics: {e}")

def record_authentication_attempt(result: str):
    """Record authentication attempt metrics"""
    try:
        metrics.authentication_attempts_total.labels(result=result).inc()
        
    except Exception as e:
        logger.error(f"Failed to record auth metrics: {e}")

def record_security_event(event_type: str, severity: str = "medium"):
    """Record security event metrics"""
    try:
        metrics.security_events_total.labels(
            event_type=event_type,
            severity=severity
        ).inc()
        
    except Exception as e:
        logger.error(f"Failed to record security event metrics: {e}")

def update_active_sessions_count(count: int):
    """Update active sessions gauge"""
    try:
        metrics.active_sessions_gauge.set(count)
        
    except Exception as e:
        logger.error(f"Failed to update session count: {e}")

def record_database_operation(operation_type: str, table: str, success: bool):
    """Record database operation metrics"""
    try:
        result = "success" if success else "error"
        metrics.database_operations_total.labels(
            operation_type=operation_type,
            table=table,
            result=result
        ).inc()
        
    except Exception as e:
        logger.error(f"Failed to record database metrics: {e}")

def record_session_duration(duration_seconds: float):
    """Record user session duration"""
    try:
        metrics.session_duration_seconds.observe(duration_seconds)
        
    except Exception as e:
        logger.error(f"Failed to record session duration: {e}")

def _calculate_breach_severity(trust_score: float, threshold: float) -> str:
    """Calculate severity of threshold breach"""
    breach_gap = threshold - trust_score
    
    if breach_gap > 30:
        return "critical"
    elif breach_gap > 20:
        return "high"
    elif breach_gap > 10:
        return "medium"
    else:
        return "low"

def setup_metrics(app: FastAPI):
    """
    Setup Prometheus metrics for FastAPI app
    
    Adds metrics middleware and /metrics endpoint
    """
    # Add metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    # Add metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    async def get_metrics():
        """Prometheus metrics endpoint"""
        try:
            return Response(
                generate_latest(),
                media_type=CONTENT_TYPE_LATEST
            )
        except Exception as e:
            logger.error(f"Metrics generation failed: {e}")
            return Response(
                "# Metrics temporarily unavailable\n",
                media_type="text/plain"
            )
    
    logger.info("✅ Prometheus metrics configured")

def get_metrics_summary() -> Dict[str, Any]:
    """
    Get summary of current metrics for health checks
    
    Returns key metrics without full Prometheus format
    """
    try:
        from prometheus_client import REGISTRY
        
        # This would collect current metric values
        # In a real implementation, you'd iterate through metric families
        
        return {
            "metrics_enabled": True,
            "total_endpoints_tracked": 10,  # Estimated
            "collection_time": time.time(),
            "status": "healthy"
        }
        
    except Exception as e:
        logger.error(f"Metrics summary failed: {e}")
        return {
            "metrics_enabled": False,
            "error": str(e),
            "status": "error"
        }

# Custom metrics middleware function
def metrics_middleware(app: FastAPI):
    """Alternative setup function for metrics middleware"""
    return MetricsMiddleware(app)
