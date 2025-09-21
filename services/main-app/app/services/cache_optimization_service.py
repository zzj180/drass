"""
Cache Optimization Service
Handles cache strategy optimization and management
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json
import hashlib
from dataclasses import dataclass
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheStrategy(Enum):
    """Cache strategies"""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"


@dataclass
class CacheEntry:
    """Cache entry data structure"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    hit_rate_percent: float = 0.0
    average_access_time_ms: float = 0.0


class LRUCache:
    """LRU Cache implementation"""
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.metrics = CacheMetrics()
    
    def _update_access_order(self, key: str):
        """Update access order for LRU"""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if self.access_order:
            lru_key = self.access_order[0]
            if lru_key in self.cache:
                entry = self.cache[lru_key]
                self.metrics.total_size_bytes -= entry.size_bytes
                del self.cache[lru_key]
                self.access_order.remove(lru_key)
                self.metrics.evictions += 1
                logger.debug(f"Evicted LRU entry: {lru_key}")
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired"""
        if entry.ttl_seconds is None:
            return False
        
        age = (datetime.now() - entry.created_at).total_seconds()
        return age > entry.ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        start_time = time.time()
        
        if key not in self.cache:
            self.metrics.misses += 1
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if self._is_expired(entry):
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            self.metrics.misses += 1
            self.metrics.total_size_bytes -= entry.size_bytes
            return None
        
        # Update access information
        entry.last_accessed = datetime.now()
        entry.access_count += 1
        self._update_access_order(key)
        
        # Update metrics
        self.metrics.hits += 1
        access_time = (time.time() - start_time) * 1000
        self.metrics.average_access_time_ms = (
            (self.metrics.average_access_time_ms * (self.metrics.hits - 1) + access_time) / 
            self.metrics.hits
        )
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache"""
        # Calculate size
        try:
            size_bytes = len(json.dumps(value, default=str).encode('utf-8'))
        except:
            size_bytes = 1000  # Default estimate
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=ttl_seconds or self.default_ttl,
            size_bytes=size_bytes
        )
        
        # Remove existing entry if present
        if key in self.cache:
            old_entry = self.cache[key]
            self.metrics.total_size_bytes -= old_entry.size_bytes
            if key in self.access_order:
                self.access_order.remove(key)
        
        # Add new entry
        self.cache[key] = entry
        self._update_access_order(key)
        self.metrics.total_size_bytes += size_bytes
        
        # Evict if necessary
        while len(self.cache) > self.max_size:
            self._evict_lru()
        
        self.metrics.entry_count = len(self.cache)
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        if key in self.cache:
            entry = self.cache[key]
            self.metrics.total_size_bytes -= entry.size_bytes
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            self.metrics.entry_count = len(self.cache)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_order.clear()
        self.metrics = CacheMetrics()
    
    def get_metrics(self) -> CacheMetrics:
        """Get cache metrics"""
        total_requests = self.metrics.hits + self.metrics.misses
        self.metrics.hit_rate_percent = (
            (self.metrics.hits / total_requests * 100) if total_requests > 0 else 0
        )
        return self.metrics
    
    def cleanup_expired(self) -> int:
        """Clean up expired entries"""
        expired_keys = []
        for key, entry in self.cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            entry = self.cache[key]
            self.metrics.total_size_bytes -= entry.size_bytes
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
        
        self.metrics.entry_count = len(self.cache)
        return len(expired_keys)


class CacheOptimizationService:
    """Service for cache optimization and management"""
    
    def __init__(self):
        # Cache instances
        self.caches: Dict[str, LRUCache] = {}
        
        # Cache configurations
        self.cache_configs = {
            "api_responses": {
                "max_size": 1000,
                "default_ttl": 300,  # 5 minutes
                "strategy": CacheStrategy.TTL
            },
            "user_sessions": {
                "max_size": 500,
                "default_ttl": 3600,  # 1 hour
                "strategy": CacheStrategy.TTL
            },
            "document_metadata": {
                "max_size": 2000,
                "default_ttl": 1800,  # 30 minutes
                "strategy": CacheStrategy.LRU
            },
            "compliance_results": {
                "max_size": 500,
                "default_ttl": 600,  # 10 minutes
                "strategy": CacheStrategy.TTL
            },
            "audit_logs": {
                "max_size": 100,
                "default_ttl": 60,  # 1 minute
                "strategy": CacheStrategy.LRU
            }
        }
        
        # Initialize caches
        self._initialize_caches()
        
        # Cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _initialize_caches(self):
        """Initialize cache instances"""
        for cache_name, config in self.cache_configs.items():
            self.caches[cache_name] = LRUCache(
                max_size=config["max_size"],
                default_ttl=config["default_ttl"]
            )
            logger.info(f"Initialized cache: {cache_name} (max_size={config['max_size']}, ttl={config['default_ttl']}s)")
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(60)  # Run every minute
                    await self.cleanup_expired_entries()
                except Exception as e:
                    logger.error(f"Cache cleanup error: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    def get_cache(self, cache_name: str) -> Optional[LRUCache]:
        """Get cache instance by name"""
        return self.caches.get(cache_name)
    
    def get(self, cache_name: str, key: str) -> Optional[Any]:
        """Get value from cache"""
        cache = self.get_cache(cache_name)
        if cache:
            return cache.get(key)
        return None
    
    def set(self, cache_name: str, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in cache"""
        cache = self.get_cache(cache_name)
        if cache:
            cache.set(key, value, ttl_seconds)
            return True
        return False
    
    def delete(self, cache_name: str, key: str) -> bool:
        """Delete value from cache"""
        cache = self.get_cache(cache_name)
        if cache:
            return cache.delete(key)
        return False
    
    def clear_cache(self, cache_name: str) -> bool:
        """Clear specific cache"""
        cache = self.get_cache(cache_name)
        if cache:
            cache.clear()
            return True
        return False
    
    def clear_all_caches(self) -> None:
        """Clear all caches"""
        for cache in self.caches.values():
            cache.clear()
        logger.info("All caches cleared")
    
    async def cleanup_expired_entries(self) -> Dict[str, int]:
        """Clean up expired entries from all caches"""
        cleanup_results = {}
        
        for cache_name, cache in self.caches.items():
            try:
                expired_count = cache.cleanup_expired()
                cleanup_results[cache_name] = expired_count
                if expired_count > 0:
                    logger.debug(f"Cleaned up {expired_count} expired entries from {cache_name}")
            except Exception as e:
                logger.error(f"Failed to cleanup {cache_name}: {e}")
                cleanup_results[cache_name] = -1
        
        return cleanup_results
    
    def get_cache_metrics(self, cache_name: Optional[str] = None) -> Dict[str, Any]:
        """Get cache metrics"""
        if cache_name:
            cache = self.get_cache(cache_name)
            if cache:
                metrics = cache.get_metrics()
                return {
                    cache_name: {
                        "hits": metrics.hits,
                        "misses": metrics.misses,
                        "evictions": metrics.evictions,
                        "hit_rate_percent": metrics.hit_rate_percent,
                        "entry_count": metrics.entry_count,
                        "total_size_bytes": metrics.total_size_bytes,
                        "average_access_time_ms": metrics.average_access_time_ms
                    }
                }
            return {}
        
        # Get metrics for all caches
        all_metrics = {}
        for name, cache in self.caches.items():
            metrics = cache.get_metrics()
            all_metrics[name] = {
                "hits": metrics.hits,
                "misses": metrics.misses,
                "evictions": metrics.evictions,
                "hit_rate_percent": metrics.hit_rate_percent,
                "entry_count": metrics.entry_count,
                "total_size_bytes": metrics.total_size_bytes,
                "average_access_time_ms": metrics.average_access_time_ms
            }
        
        return all_metrics
    
    def optimize_cache_config(self, cache_name: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize cache configuration based on metrics"""
        cache = self.get_cache(cache_name)
        if not cache:
            return {"error": f"Cache {cache_name} not found"}
        
        current_config = self.cache_configs.get(cache_name, {})
        recommendations = []
        
        # Analyze hit rate
        hit_rate = metrics.get("hit_rate_percent", 0)
        if hit_rate < 50:
            recommendations.append({
                "type": "increase_size",
                "description": "Low hit rate, consider increasing cache size",
                "current_size": current_config.get("max_size", 1000),
                "recommended_size": min(current_config.get("max_size", 1000) * 2, 5000)
            })
        elif hit_rate > 90 and metrics.get("evictions", 0) == 0:
            recommendations.append({
                "type": "decrease_size",
                "description": "High hit rate with no evictions, consider decreasing cache size",
                "current_size": current_config.get("max_size", 1000),
                "recommended_size": max(current_config.get("max_size", 1000) // 2, 100)
            })
        
        # Analyze TTL
        current_ttl = current_config.get("default_ttl", 300)
        if hit_rate < 30:
            recommendations.append({
                "type": "increase_ttl",
                "description": "Low hit rate, consider increasing TTL",
                "current_ttl": current_ttl,
                "recommended_ttl": min(current_ttl * 2, 3600)
            })
        
        # Analyze access time
        avg_access_time = metrics.get("average_access_time_ms", 0)
        if avg_access_time > 10:
            recommendations.append({
                "type": "optimize_structure",
                "description": "High access time, consider optimizing cache structure",
                "current_access_time_ms": avg_access_time
            })
        
        return {
            "cache_name": cache_name,
            "current_config": current_config,
            "current_metrics": metrics,
            "recommendations": recommendations,
            "optimization_score": self._calculate_optimization_score(metrics)
        }
    
    def _calculate_optimization_score(self, metrics: Dict[str, Any]) -> int:
        """Calculate cache optimization score (0-100)"""
        score = 100
        
        # Hit rate scoring (40% weight)
        hit_rate = metrics.get("hit_rate_percent", 0)
        if hit_rate < 50:
            score -= 40
        elif hit_rate < 70:
            score -= 20
        elif hit_rate < 90:
            score -= 10
        
        # Access time scoring (30% weight)
        avg_access_time = metrics.get("average_access_time_ms", 0)
        if avg_access_time > 10:
            score -= 30
        elif avg_access_time > 5:
            score -= 15
        elif avg_access_time > 1:
            score -= 5
        
        # Eviction rate scoring (20% weight)
        evictions = metrics.get("evictions", 0)
        total_requests = metrics.get("hits", 0) + metrics.get("misses", 0)
        if total_requests > 0:
            eviction_rate = (evictions / total_requests) * 100
            if eviction_rate > 20:
                score -= 20
            elif eviction_rate > 10:
                score -= 10
        
        # Size efficiency scoring (10% weight)
        entry_count = metrics.get("entry_count", 0)
        total_size = metrics.get("total_size_bytes", 0)
        if entry_count > 0:
            avg_entry_size = total_size / entry_count
            if avg_entry_size > 10000:  # 10KB per entry
                score -= 10
            elif avg_entry_size > 5000:  # 5KB per entry
                score -= 5
        
        return max(0, min(100, score))
    
    def generate_cache_key(self, prefix: str, *args) -> str:
        """Generate consistent cache key"""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def warm_cache(self, cache_name: str, warmup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Warm up cache with predefined data"""
        cache = self.get_cache(cache_name)
        if not cache:
            return {"error": f"Cache {cache_name} not found"}
        
        warmed_count = 0
        failed_count = 0
        
        for key, value in warmup_data.items():
            try:
                cache.set(key, value)
                warmed_count += 1
            except Exception as e:
                logger.error(f"Failed to warm cache entry {key}: {e}")
                failed_count += 1
        
        return {
            "cache_name": cache_name,
            "warmed_entries": warmed_count,
            "failed_entries": failed_count,
            "total_entries": len(warmup_data)
        }
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        all_metrics = self.get_cache_metrics()
        
        # Calculate totals
        total_hits = sum(m["hits"] for m in all_metrics.values())
        total_misses = sum(m["misses"] for m in all_metrics.values())
        total_evictions = sum(m["evictions"] for m in all_metrics.values())
        total_size = sum(m["total_size_bytes"] for m in all_metrics.values())
        total_entries = sum(m["entry_count"] for m in all_metrics.values())
        
        overall_hit_rate = (total_hits / (total_hits + total_misses) * 100) if (total_hits + total_misses) > 0 else 0
        
        return {
            "cache_count": len(self.caches),
            "total_metrics": {
                "hits": total_hits,
                "misses": total_misses,
                "evictions": total_evictions,
                "hit_rate_percent": round(overall_hit_rate, 2),
                "total_size_bytes": total_size,
                "total_entries": total_entries
            },
            "individual_caches": all_metrics,
            "configurations": self.cache_configs,
            "generated_at": datetime.now().isoformat()
        }


# Global instance
cache_optimization_service = CacheOptimizationService()
