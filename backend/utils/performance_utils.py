import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict
import logging

logger = logging.getLogger(__name__)

class SimpleCache:
    """Simple in-memory cache for NETHRA backend"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.cache: Dict[str, Dict] = {}
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
    
    def get(self, key: str) -> Any:
        """Get value from cache"""
        if key in self.cache:
            entry = self.cache[key]
            
            # Check if expired
            if time.time() - entry["timestamp"] > self.ttl:
                del self.cache[key]
                return None
            
            return entry["value"]
        
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache"""
        # Clean cache if too large
        if len(self.cache) >= self.max_size:
            self._cleanup_expired()
            
            # If still too large, remove oldest entries
            if len(self.cache) >= self.max_size:
                oldest_keys = sorted(
                    self.cache.keys(),
                    key=lambda k: self.cache[k]["timestamp"]
                )[:self.max_size // 4]
                
                for key in oldest_keys:
                    del self.cache[key]
        
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry["timestamp"] > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()

# Global cache instance
cache = SimpleCache()

def cached(ttl: int = 300):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def measure_time(func_name: str = None):
    """Decorator to measure function execution time"""
    def decorator(func: Callable) -> Callable:
        name = func_name or func.__name__
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(f"⏱️ {name} executed in {execution_time:.4f}s")
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(f"⏱️ {name} executed in {execution_time:.4f}s")
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
