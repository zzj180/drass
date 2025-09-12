"""
Redis cache implementation for embedding service
"""

import json
import hashlib
import logging
from typing import Optional, List, Dict, Any
import redis.asyncio as redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisEmbeddingCache:
    """Redis-based cache for embeddings"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", ttl: int = 3600):
        self.redis_url = redis_url
        self.ttl = ttl  # Time to live in seconds
        self.client = None
        self.enabled = False
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False  # We'll handle encoding/decoding
            )
            await self.client.ping()
            self.enabled = True
            logger.info("Redis cache initialized successfully")
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Redis cache initialization failed: {e}. Cache disabled.")
            self.enabled = False
            
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            
    def _generate_key(self, text: str, model: str) -> str:
        """Generate cache key from text and model"""
        content = f"{model}:{text}"
        return f"emb:{hashlib.sha256(content.encode()).hexdigest()}"
    
    async def get_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """Get cached embedding for text"""
        if not self.enabled or not self.client:
            return None
            
        try:
            key = self._generate_key(text, model)
            cached = await self.client.get(key)
            
            if cached:
                embedding = json.loads(cached)
                logger.debug(f"Cache hit for text (length: {len(text)})")
                return embedding
                
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            
        return None
    
    async def set_embedding(self, text: str, model: str, embedding: List[float]):
        """Cache embedding for text"""
        if not self.enabled or not self.client:
            return
            
        try:
            key = self._generate_key(text, model)
            value = json.dumps(embedding)
            await self.client.setex(key, self.ttl, value)
            logger.debug(f"Cached embedding for text (length: {len(text)})")
            
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    async def get_batch(self, texts: List[str], model: str) -> Dict[int, List[float]]:
        """Get cached embeddings for multiple texts"""
        if not self.enabled or not self.client:
            return {}
            
        cached_embeddings = {}
        
        try:
            # Create pipeline for batch get
            pipe = self.client.pipeline()
            keys = []
            
            for i, text in enumerate(texts):
                key = self._generate_key(text, model)
                keys.append((i, key))
                pipe.get(key)
            
            # Execute pipeline
            results = await pipe.execute()
            
            # Process results
            for (idx, key), result in zip(keys, results):
                if result:
                    embedding = json.loads(result)
                    cached_embeddings[idx] = embedding
                    
            if cached_embeddings:
                logger.debug(f"Cache hits: {len(cached_embeddings)}/{len(texts)}")
                
        except Exception as e:
            logger.warning(f"Batch cache get error: {e}")
            
        return cached_embeddings
    
    async def set_batch(self, texts: List[str], model: str, embeddings: List[List[float]]):
        """Cache multiple embeddings"""
        if not self.enabled or not self.client:
            return
            
        try:
            # Create pipeline for batch set
            pipe = self.client.pipeline()
            
            for text, embedding in zip(texts, embeddings):
                key = self._generate_key(text, model)
                value = json.dumps(embedding)
                pipe.setex(key, self.ttl, value)
            
            # Execute pipeline
            await pipe.execute()
            logger.debug(f"Cached {len(texts)} embeddings")
            
        except Exception as e:
            logger.warning(f"Batch cache set error: {e}")
    
    async def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries"""
        if not self.enabled or not self.client:
            return
            
        try:
            if pattern:
                keys = await self.client.keys(f"emb:*{pattern}*")
            else:
                keys = await self.client.keys("emb:*")
                
            if keys:
                await self.client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
                
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled or not self.client:
            return {"enabled": False}
            
        try:
            info = await self.client.info("stats")
            keys_count = await self.client.dbsize()
            
            return {
                "enabled": True,
                "total_keys": keys_count,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                ) if info.get("keyspace_hits", 0) > 0 else 0,
                "memory_used": info.get("used_memory_human", "0B")
            }
            
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}