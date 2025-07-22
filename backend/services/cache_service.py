import asyncio
import json
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """Advanced caching service for NETHRA backend"""
    
    def __init__(self, default_ttl: int = 300):
        self.cache: Dict[str, Dict] = {}
        self.default_ttl = default_ttl
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            entry = self.cache[key]
            
            # Check expiration
            if datetime.utcnow() > entry["expires_at"]:
                del self.cache[key]
                self.stats["evictions"] += 1
                self.stats["misses"] += 1
                return None
            
            self.stats["hits"] += 1
            return entry["value"]
        
        self.stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
            
            self.cache[key] = {
                "value": value,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "access_count": 0
            }
            
            self.stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def clear(self) -> int:
        """Clear all cache entries"""
        count = len(self.cache)
        self.cache.clear()
        return count
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_keys": len(self.cache),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "sets": self.stats["sets"],
            "evictions": self.stats["evictions"]
        }

# Global cache service
_cache_service = None

def get_cache_service() -> CacheService:
    """Get or create global cache service"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
