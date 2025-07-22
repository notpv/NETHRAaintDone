import time
from collections import defaultdict, deque
from typing import Dict, Tuple
import asyncio
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Advanced rate limiting service"""
    
    def __init__(self, default_limit: int = 60, window_seconds: int = 60):
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, float] = {}  # IP -> block_until_timestamp
    
    async def is_allowed(self, identifier: str, limit: int = None) -> Tuple[bool, Dict]:
        """Check if request is allowed"""
        limit = limit or self.default_limit
        current_time = time.time()
        
        # Check if IP is currently blocked
        if identifier in self.blocked_ips:
            if current_time < self.blocked_ips[identifier]:
                return False, {
                    "allowed": False,
                    "reason": "temporarily_blocked",
                    "retry_after": int(self.blocked_ips[identifier] - current_time)
                }
            else:
                # Remove expired block
                del self.blocked_ips[identifier]
        
        # Clean old requests
        await self._clean_old_requests(identifier, current_time)
        
        # Check rate limit
        request_count = len(self.requests[identifier])
        
        if request_count >= limit:
            # Block IP for 5 minutes if they exceed limit significantly
            if request_count > limit * 1.5:
                self.blocked_ips[identifier] = current_time + 300  # 5 minutes
                logger.warning(f"IP {identifier} blocked for 5 minutes due to excessive requests")
            
            return False, {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "limit": limit,
                "current_count": request_count,
                "window_seconds": self.window_seconds,
                "retry_after": self.window_seconds
            }
        
        # Record this request
        self.requests[identifier].append(current_time)
        
        return True, {
            "allowed": True,
            "limit": limit,
            "remaining": limit - request_count - 1,
            "reset_time": int(current_time + self.window_seconds)
        }
    
    async def _clean_old_requests(self, identifier: str, current_time: float):
        """Remove requests older than window"""
        window_start = current_time - self.window_seconds
        
        while (self.requests[identifier] and 
               self.requests[identifier][0] < window_start):
            self.requests[identifier].popleft()
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics"""
        current_time = time.time()
        
        return {
            "active_identifiers": len(self.requests),
            "blocked_identifiers": len(self.blocked_ips),
            "total_requests": sum(len(requests) for requests in self.requests.values()),
            "blocked_ips": list(self.blocked_ips.keys()),
            "timestamp": current_time
        }

# Global rate limiter
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
