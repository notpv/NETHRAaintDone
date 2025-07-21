import time
import logging
from typing import Dict, Optional
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)

@dataclass
class RateLimitInfo:
    """Rate limiting information for a client"""
    requests: deque
    blocked_until: float = 0.0
    total_requests: int = 0
    total_blocked: int = 0

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced Rate Limiting Middleware for NETHRA Backend
    
    Protects against abuse, DoS attacks, and excessive API usage
    """
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60, 
                 block_duration: int = 300, burst_protection: bool = True):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_duration = block_duration
        self.burst_protection = burst_protection
        
        # In-memory storage for rate limiting (use Redis in production)
        self.clients: Dict[str, RateLimitInfo] = defaultdict(self._create_rate_limit_info)
        self.lock = threading.RLock()
        
        # Different limits for different endpoint types
        self.endpoint_limits = {
            "/auth/login": {"max_requests": 10, "window_seconds": 300},  # 10 login attempts per 5 min
            "/auth/register": {"max_requests": 5, "window_seconds": 300},  # 5 registrations per 5 min
            "/trust/predict": {"max_requests": 200, "window_seconds": 60},  # 200 predictions per min
            "/trust/batch-predict": {"max_requests": 10, "window_seconds": 60}  # 10 batch requests per min
        }
        
        # Cleanup old entries periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def _create_rate_limit_info(self) -> RateLimitInfo:
        """Create new rate limit info for a client"""
        return RateLimitInfo(requests=deque(), blocked_until=0.0)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting"""
        current_time = time.time()
        client_id = self._get_client_id(request)
        endpoint = self._normalize_endpoint(request.url.path)
        
        # Periodic cleanup
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(current_time)
        
        try:
            with self.lock:
                # Get client rate limit info
                client_info = self.clients[client_id]
                
                # Check if client is currently blocked
                if current_time < client_info.blocked_until:
                    client_info.total_blocked += 1
                    
                    remaining_block_time = int(client_info.blocked_until - current_time)
                    
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Blocked for {remaining_block_time} more seconds.",
                        headers={
                            "Retry-After": str(remaining_block_time),
                            "X-RateLimit-Limit": str(self.max_requests),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(client_info.blocked_until))
                        }
                    )
                
                # Get rate limit settings for this endpoint
                limits = self._get_endpoint_limits(endpoint)
                max_requests = limits["max_requests"]
                window_seconds = limits["window_seconds"]
                
                # Clean old requests outside the window
                cutoff_time = current_time - window_seconds
                while client_info.requests and client_info.requests[0] < cutoff_time:
                    client_info.requests.popleft()
                
                # Check if limit is exceeded
                if len(client_info.requests) >= max_requests:
                    # Block the client
                    client_info.blocked_until = current_time + self.block_duration
                    client_info.total_blocked += 1
                    
                    # Log rate limit violation
                    logger.warning(f"🚨 Rate limit exceeded for {client_id} on {endpoint}: "
                                 f"{len(client_info.requests)} requests in {window_seconds}s")
                    
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded: {max_requests} requests per {window_seconds} seconds",
                        headers={
                            "Retry-After": str(self.block_duration),
                            "X-RateLimit-Limit": str(max_requests),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(current_time + window_seconds))
                        }
                    )
                
                # Burst protection
                if self.burst_protection and self._detect_burst(client_info, current_time):
                    client_info.blocked_until = current_time + (self.block_duration // 2)
                    
                    logger.warning(f"🚨 Burst attack detected from {client_id}")
                    
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Burst rate limit exceeded",
                        headers={"Retry-After": str(self.block_duration // 2)}
                    )
                
                # Record this request
                client_info.requests.append(current_time)
                client_info.total_requests += 1
            
            # Process the request
            response = await call_next(request)
            
            # Add rate limit headers
            remaining_requests = max(0, max_requests - len(client_info.requests))
            reset_time = int(current_time + window_seconds)
            
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining_requests)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            response.headers["X-RateLimit-Window"] = str(window_seconds)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Rate limiting error: {e}")
            # Don't block requests due to rate limiting errors
            return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Try to get user ID from request state (if authenticated)
        if hasattr(request.state, "user_id"):
            return f"user_{request.state.user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host
        
        # Consider X-Forwarded-For for reverse proxy setups
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip_{client_ip}"
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for rate limiting"""
        # Remove trailing slashes
        path = path.rstrip("/")
        
        # Group similar endpoints
        if path.startswith("/user/"):
            return "/user/*"
        elif path.startswith("/trust/"):
            return "/trust/*"
        elif path.startswith("/auth/"):
            return "/auth/*"
        
        return path
    
    def _get_endpoint_limits(self, endpoint: str) -> Dict[str, int]:
        """Get rate limits for specific endpoint"""
        # Check for exact match
        if endpoint in self.endpoint_limits:
            return self.endpoint_limits[endpoint]
        
        # Check for pattern matches
        for pattern, limits in self.endpoint_limits.items():
            if pattern.endswith("*") and endpoint.startswith(pattern[:-1]):
                return limits
        
        # Return default limits
        return {"max_requests": self.max_requests, "window_seconds": self.window_seconds}
    
    def _detect_burst(self, client_info: RateLimitInfo, current_time: float) -> bool:
        """Detect burst/spike in requests"""
        if len(client_info.requests) < 10:
            return False
        
        # Check if last 10 requests happened within 10 seconds (burst)
        recent_requests = [req for req in client_info.requests if req > current_time - 10]
        return len(recent_requests) >= 10
    
    def _cleanup_old_entries(self, current_time: float):
        """Clean up old client entries to prevent memory leaks"""
        try:
            clients_to_remove = []
            
            for client_id, client_info in self.clients.items():
                # Remove clients that haven't made requests in the last hour
                # and are not currently blocked
                if (not client_info.requests or 
                    (client_info.requests[-1] < current_time - 3600 and 
                     current_time >= client_info.blocked_until)):
                    clients_to_remove.append(client_id)
            
            for client_id in clients_to_remove:
                del self.clients[client_id]
            
            self.last_cleanup = current_time
            
            if clients_to_remove:
                logger.info(f"🧹 Cleaned up {len(clients_to_remove)} old rate limit entries")
                
        except Exception as e:
            logger.error(f"❌ Rate limit cleanup failed: {e}")
    
    def get_rate_limit_stats(self) -> Dict[str, any]:
        """Get rate limiting statistics"""
        with self.lock:
            total_clients = len(self.clients)
            blocked_clients = sum(1 for info in self.clients.values() 
                                if time.time() < info.blocked_until)
            
            total_requests = sum(info.total_requests for info in self.clients.values())
            total_blocked_requests = sum(info.total_blocked for info in self.clients.values())
            
            return {
                "total_clients": total_clients,
                "blocked_clients": blocked_clients,
                "total_requests": total_requests,
                "total_blocked_requests": total_blocked_requests,
                "block_rate": (total_blocked_requests / max(total_requests, 1)) * 100,
                "current_time": time.time()
            }

# Decorator for applying rate limits to specific endpoints
def rate_limit(max_requests: int, window_seconds: int):
    """Decorator to apply rate limiting to specific endpoints"""
    def decorator(func):
        # This would be implemented to work with the middleware
        # For now, it's a placeholder that can be extended
        func._rate_limit_config = {
            "max_requests": max_requests,
            "window_seconds": window_seconds
        }
        return func
    return decorator
