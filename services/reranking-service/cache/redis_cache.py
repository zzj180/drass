"""
Redis cache implementation for distributed caching
"""
from typing import Any, Optional, Dict
import json
import asyncio
import logging
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Redis-based cache implementation for distributed scenarios
    """

    def __init__(self, redis_url: str, ttl: int = 3600, prefix: str = "rerank:"):
        """
        Initialize Redis cache

        Args:
            redis_url: Redis connection URL
            ttl: Time-to-live in seconds
            prefix: Key prefix for namespacing
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis package not installed. Install with: pip install redis")

        self.redis_url = redis_url
        self.ttl = ttl
        self.prefix = prefix
        self.client = None
        self.hits = 0
        self.misses = 0

    async def initialize(self) -> None:
        """
        Initialize Redis connection
        """
        try:
            self.client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.client:
            return None

        try:
            full_key = f"{self.prefix}{key}"
            value = await self.client.get(full_key)

            if value:
                self.hits += 1
                return json.loads(value)
            else:
                self.misses += 1
                return None

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.misses += 1
            return None

    async def set(self, key: str, value: Any) -> None:
        """
        Set item in cache

        Args:
            key: Cache key
            value: Value to cache
        """
        if not self.client:
            return

        try:
            full_key = f"{self.prefix}{key}"
            json_value = json.dumps(value)
            await self.client.setex(full_key, self.ttl, json_value)

        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def clear(self) -> None:
        """
        Clear all items with our prefix from cache
        """
        if not self.client:
            return

        try:
            # Get all keys with our prefix
            pattern = f"{self.prefix}*"
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)

            # Delete all keys
            if keys:
                await self.client.delete(*keys)

            self.hits = 0
            self.misses = 0
            logger.info(f"Cleared {len(keys)} items from Redis cache")

        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        try:
            # Count keys with our prefix
            pattern = f"{self.prefix}*"
            count = 0
            async for _ in self.client.scan_iter(match=pattern):
                count += 1

            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

            # Get Redis info
            info = await self.client.info()

            return {
                "type": "redis",
                "size": count,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "ttl": self.ttl,
                "redis_memory": info.get("used_memory_human", "unknown"),
                "redis_connected_clients": info.get("connected_clients", 0)
            }

        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {
                "type": "redis",
                "error": str(e)
            }

    async def close(self) -> None:
        """
        Close Redis connection
        """
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")