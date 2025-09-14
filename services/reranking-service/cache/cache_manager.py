"""
Cache manager that handles both LRU and Redis caching
"""
from typing import Any, Optional, Dict
import hashlib
import json
import logging

from .lru_cache import LRUCache
from .redis_cache import RedisCache

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Unified cache manager supporting multiple cache backends
    """

    def __init__(
        self,
        cache_type: str = "lru",
        cache_size: int = 1000,
        ttl: int = 3600,
        redis_url: Optional[str] = None
    ):
        """
        Initialize cache manager

        Args:
            cache_type: Type of cache ("lru" or "redis")
            cache_size: Maximum size for LRU cache
            ttl: Time-to-live in seconds
            redis_url: Redis URL for Redis cache
        """
        self.cache_type = cache_type
        self.ttl = ttl
        self.cache = None

        if cache_type == "redis" and redis_url:
            self.cache = RedisCache(redis_url=redis_url, ttl=ttl)
        else:
            # Default to LRU cache
            self.cache = LRUCache(max_size=cache_size, ttl=ttl)
            if cache_type == "redis":
                logger.warning("Redis URL not provided, falling back to LRU cache")

    async def initialize(self) -> None:
        """
        Initialize the cache backend
        """
        if isinstance(self.cache, RedisCache):
            try:
                await self.cache.initialize()
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {e}")
                logger.info("Falling back to LRU cache")
                self.cache = LRUCache(max_size=1000, ttl=self.ttl)
        else:
            logger.info("LRU cache initialized")

    def generate_key(self, query: str, documents: list) -> str:
        """
        Generate a cache key from query and documents

        Args:
            query: Search query
            documents: List of documents

        Returns:
            Cache key string
        """
        # Create a deterministic key from query and documents
        content = {
            "query": query,
            "documents": documents
        }
        json_str = json.dumps(content, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.cache:
            return None

        return await self.cache.get(key)

    async def set(self, key: str, value: Any) -> None:
        """
        Set item in cache

        Args:
            key: Cache key
            value: Value to cache
        """
        if not self.cache:
            return

        await self.cache.set(key, value)

    async def clear(self) -> None:
        """
        Clear all items from cache
        """
        if self.cache:
            await self.cache.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        if self.cache:
            return await self.cache.get_stats()
        return {
            "type": "none",
            "message": "Cache not initialized"
        }

    async def close(self) -> None:
        """
        Close cache connections
        """
        if isinstance(self.cache, RedisCache):
            await self.cache.close()