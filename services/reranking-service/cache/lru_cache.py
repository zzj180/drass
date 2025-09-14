"""
LRU cache implementation for reranking results
"""
from typing import Any, Optional, Dict
import time
import asyncio
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

class LRUCache:
    """
    Thread-safe LRU cache implementation with TTL support
    """

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize LRU cache

        Args:
            max_size: Maximum number of items in cache
            ttl: Time-to-live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.lock = asyncio.Lock()
        self.hits = 0
        self.misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self.lock:
            if key in self.cache:
                # Check if expired
                item = self.cache[key]
                if time.time() - item["timestamp"] > self.ttl:
                    # Expired, remove it
                    del self.cache[key]
                    self.misses += 1
                    return None

                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return item["value"]

            self.misses += 1
            return None

    async def set(self, key: str, value: Any) -> None:
        """
        Set item in cache

        Args:
            key: Cache key
            value: Value to cache
        """
        async with self.lock:
            # Remove oldest items if at capacity
            while len(self.cache) >= self.max_size:
                # Remove least recently used (first item)
                self.cache.popitem(last=False)

            # Add new item
            self.cache[key] = {
                "value": value,
                "timestamp": time.time()
            }

    async def clear(self) -> None:
        """
        Clear all items from cache
        """
        async with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            logger.info("LRU cache cleared")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        async with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "type": "lru",
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "ttl": self.ttl
            }

    async def remove_expired(self) -> int:
        """
        Remove expired items from cache

        Returns:
            Number of items removed
        """
        async with self.lock:
            current_time = time.time()
            expired_keys = []

            for key, item in self.cache.items():
                if current_time - item["timestamp"] > self.ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]

            if expired_keys:
                logger.debug(f"Removed {len(expired_keys)} expired items from cache")

            return len(expired_keys)