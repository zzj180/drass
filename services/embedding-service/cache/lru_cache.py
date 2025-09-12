"""
Local LRU cache implementation for embedding service
"""

import hashlib
import logging
from typing import Optional, List, Dict, Any
from collections import OrderedDict
import time
import json

logger = logging.getLogger(__name__)


class LRUEmbeddingCache:
    """LRU cache for embeddings"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self.cache = OrderedDict()
        self.timestamps = {}
        self.hits = 0
        self.misses = 0
        
    def _generate_key(self, text: str, model: str) -> str:
        """Generate cache key from text and model"""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        return time.time() - self.timestamps[key] > self.ttl
    
    def _evict_expired(self):
        """Remove expired entries"""
        keys_to_remove = []
        current_time = time.time()
        
        for key in list(self.cache.keys()):
            if current_time - self.timestamps.get(key, 0) > self.ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
            del self.timestamps[key]
    
    def get_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """Get cached embedding for text"""
        key = self._generate_key(text, model)
        
        if key in self.cache and not self._is_expired(key):
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            logger.debug(f"Cache hit for text (length: {len(text)})")
            return self.cache[key]
        
        self.misses += 1
        return None
    
    def set_embedding(self, text: str, model: str, embedding: List[float]):
        """Cache embedding for text"""
        key = self._generate_key(text, model)
        
        # Add to cache
        self.cache[key] = embedding
        self.timestamps[key] = time.time()
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        
        # Evict LRU if cache is full
        if len(self.cache) > self.max_size:
            # Remove least recently used
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        logger.debug(f"Cached embedding for text (length: {len(text)})")
    
    def get_batch(self, texts: List[str], model: str) -> Dict[int, List[float]]:
        """Get cached embeddings for multiple texts"""
        cached_embeddings = {}
        
        for i, text in enumerate(texts):
            embedding = self.get_embedding(text, model)
            if embedding is not None:
                cached_embeddings[i] = embedding
        
        if cached_embeddings:
            logger.debug(f"Cache hits: {len(cached_embeddings)}/{len(texts)}")
        
        return cached_embeddings
    
    def set_batch(self, texts: List[str], model: str, embeddings: List[List[float]]):
        """Cache multiple embeddings"""
        for text, embedding in zip(texts, embeddings):
            self.set_embedding(text, model, embedding)
        
        logger.debug(f"Cached {len(texts)} embeddings")
    
    def clear_cache(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.timestamps.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self._evict_expired()
        
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "type": "LRU",
            "max_size": self.max_size,
            "current_size": len(self.cache),
            "ttl": self.ttl,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }
    
    def export_cache(self) -> Dict[str, Any]:
        """Export cache contents for persistence"""
        self._evict_expired()
        
        return {
            "cache": {k: v for k, v in self.cache.items()},
            "timestamps": self.timestamps,
            "stats": {
                "hits": self.hits,
                "misses": self.misses
            }
        }
    
    def import_cache(self, data: Dict[str, Any]):
        """Import cache contents from persistence"""
        if "cache" in data:
            self.cache = OrderedDict(data["cache"])
        if "timestamps" in data:
            self.timestamps = data["timestamps"]
        if "stats" in data:
            self.hits = data["stats"].get("hits", 0)
            self.misses = data["stats"].get("misses", 0)
        
        self._evict_expired()
        logger.info(f"Imported {len(self.cache)} cache entries")