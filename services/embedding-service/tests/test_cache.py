"""
Cache performance tests
"""

import pytest
import asyncio
import time
import random
import string
from unittest.mock import patch, AsyncMock

from cache.lru_cache import LRUEmbeddingCache
from cache.redis_cache import RedisEmbeddingCache


def generate_random_text(length: int = 100) -> str:
    """Generate random text for testing"""
    return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))


def generate_random_embedding(dimension: int = 768) -> list:
    """Generate random embedding vector"""
    return [random.random() for _ in range(dimension)]


class TestCachePerformance:
    """Performance tests for cache implementations"""
    
    def test_lru_cache_performance(self):
        """Test LRU cache performance"""
        cache = LRUEmbeddingCache(max_size=1000, ttl=3600)
        
        # Generate test data
        texts = [generate_random_text() for _ in range(1000)]
        embeddings = [generate_random_embedding(768) for _ in range(1000)]
        model = "test-model"
        
        # Test write performance
        start_time = time.time()
        for text, embedding in zip(texts, embeddings):
            cache.set_embedding(text, model, embedding)
        write_time = time.time() - start_time
        
        print(f"\nLRU Cache Write Performance:")
        print(f"  - Wrote 1000 embeddings in {write_time:.3f}s")
        print(f"  - Average write time: {write_time/1000*1000:.3f}ms")
        
        # Test read performance (all hits)
        start_time = time.time()
        for text in texts:
            _ = cache.get_embedding(text, model)
        read_hit_time = time.time() - start_time
        
        print(f"LRU Cache Read Performance (hits):")
        print(f"  - Read 1000 embeddings in {read_hit_time:.3f}s")
        print(f"  - Average read time: {read_hit_time/1000*1000:.3f}ms")
        
        # Test read performance (all misses)
        miss_texts = [generate_random_text() for _ in range(1000)]
        start_time = time.time()
        for text in miss_texts:
            _ = cache.get_embedding(text, model)
        read_miss_time = time.time() - start_time
        
        print(f"LRU Cache Read Performance (misses):")
        print(f"  - Read 1000 misses in {read_miss_time:.3f}s")
        print(f"  - Average miss time: {read_miss_time/1000*1000:.3f}ms")
        
        # Test mixed read pattern (50% hits)
        mixed_texts = texts[:500] + miss_texts[:500]
        random.shuffle(mixed_texts)
        
        start_time = time.time()
        for text in mixed_texts:
            _ = cache.get_embedding(text, model)
        mixed_time = time.time() - start_time
        
        print(f"LRU Cache Mixed Performance (50% hits):")
        print(f"  - Read 1000 embeddings in {mixed_time:.3f}s")
        print(f"  - Average read time: {mixed_time/1000*1000:.3f}ms")
        
        # Assert performance requirements
        assert write_time < 1.0  # Should write 1000 items in < 1s
        assert read_hit_time < 0.5  # Should read 1000 hits in < 0.5s
        assert read_miss_time < 0.1  # Should handle 1000 misses in < 0.1s
    
    def test_batch_performance(self):
        """Test batch operation performance"""
        cache = LRUEmbeddingCache(max_size=1000, ttl=3600)
        
        # Generate test data
        batch_size = 100
        num_batches = 10
        model = "test-model"
        
        batches = []
        for _ in range(num_batches):
            texts = [generate_random_text() for _ in range(batch_size)]
            embeddings = [generate_random_embedding(768) for _ in range(batch_size)]
            batches.append((texts, embeddings))
        
        # Test batch write performance
        start_time = time.time()
        for texts, embeddings in batches:
            cache.set_batch(texts, model, embeddings)
        batch_write_time = time.time() - start_time
        
        print(f"\nBatch Write Performance:")
        print(f"  - Wrote {num_batches} batches ({num_batches * batch_size} items) in {batch_write_time:.3f}s")
        print(f"  - Average batch write time: {batch_write_time/num_batches*1000:.3f}ms")
        
        # Test batch read performance
        start_time = time.time()
        for texts, _ in batches:
            _ = cache.get_batch(texts, model)
        batch_read_time = time.time() - start_time
        
        print(f"Batch Read Performance:")
        print(f"  - Read {num_batches} batches in {batch_read_time:.3f}s")
        print(f"  - Average batch read time: {batch_read_time/num_batches*1000:.3f}ms")
        
        assert batch_write_time < 2.0  # Should handle batch writes efficiently
        assert batch_read_time < 1.0  # Should handle batch reads efficiently
    
    def test_cache_memory_usage(self):
        """Test cache memory usage"""
        import sys
        
        cache = LRUEmbeddingCache(max_size=1000, ttl=3600)
        
        # Measure initial memory
        initial_size = sys.getsizeof(cache.cache) + sys.getsizeof(cache.timestamps)
        
        # Fill cache
        for i in range(1000):
            text = f"text_{i}"
            embedding = generate_random_embedding(768)
            cache.set_embedding(text, "model", embedding)
        
        # Measure final memory
        final_size = sys.getsizeof(cache.cache) + sys.getsizeof(cache.timestamps)
        
        # Estimate per-item memory
        memory_per_item = (final_size - initial_size) / 1000
        
        print(f"\nMemory Usage:")
        print(f"  - Initial size: {initial_size:,} bytes")
        print(f"  - Final size: {final_size:,} bytes")
        print(f"  - Per-item memory: ~{memory_per_item:.0f} bytes")
        print(f"  - Total for 1000 items: {(final_size - initial_size) / 1024 / 1024:.2f} MB")
        
        # Rough estimate: each item should use < 10KB
        assert memory_per_item < 10000


@pytest.mark.asyncio
class TestRedisCachePerformance:
    """Performance tests for Redis cache"""
    
    @patch('redis.asyncio.from_url')
    async def test_redis_batch_performance(self, mock_redis):
        """Test Redis batch operation performance"""
        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        
        # Mock pipeline
        mock_pipeline = AsyncMock()
        mock_pipeline.get = lambda key: None
        mock_pipeline.setex = lambda key, ttl, value: None
        mock_pipeline.execute = AsyncMock(return_value=[None] * 100)
        mock_client.pipeline = lambda: mock_pipeline
        
        mock_redis.return_value = mock_client
        
        cache = RedisEmbeddingCache()
        await cache.initialize()
        
        # Generate test data
        texts = [generate_random_text() for _ in range(100)]
        embeddings = [generate_random_embedding(768) for _ in range(100)]
        model = "test-model"
        
        # Test batch write
        start_time = time.time()
        await cache.set_batch(texts, model, embeddings)
        write_time = time.time() - start_time
        
        print(f"\nRedis Batch Write Performance (mocked):")
        print(f"  - Wrote 100 embeddings in {write_time:.3f}s")
        
        # Test batch read
        start_time = time.time()
        await cache.get_batch(texts, model)
        read_time = time.time() - start_time
        
        print(f"Redis Batch Read Performance (mocked):")
        print(f"  - Read 100 embeddings in {read_time:.3f}s")
        
        # With mocked Redis, operations should be very fast
        assert write_time < 0.1
        assert read_time < 0.1


class TestCacheComparison:
    """Compare different cache implementations"""
    
    def test_cache_comparison(self):
        """Compare LRU and mock Redis cache performance"""
        # Test parameters
        num_items = 500
        num_reads = 1000
        
        # Generate test data
        texts = [generate_random_text() for _ in range(num_items)]
        embeddings = [generate_random_embedding(768) for _ in range(num_items)]
        model = "test-model"
        
        # Test LRU Cache
        lru_cache = LRUEmbeddingCache(max_size=num_items, ttl=3600)
        
        # Populate LRU cache
        start_time = time.time()
        for text, embedding in zip(texts, embeddings):
            lru_cache.set_embedding(text, model, embedding)
        lru_write_time = time.time() - start_time
        
        # Random reads from LRU
        read_indices = [random.randint(0, num_items - 1) for _ in range(num_reads)]
        start_time = time.time()
        for idx in read_indices:
            _ = lru_cache.get_embedding(texts[idx], model)
        lru_read_time = time.time() - start_time
        
        print(f"\nCache Performance Comparison:")
        print(f"LRU Cache:")
        print(f"  - Write {num_items} items: {lru_write_time:.3f}s")
        print(f"  - Read {num_reads} items: {lru_read_time:.3f}s")
        print(f"  - Avg write: {lru_write_time/num_items*1000:.3f}ms")
        print(f"  - Avg read: {lru_read_time/num_reads*1000:.3f}ms")
        
        # Get final statistics
        lru_stats = lru_cache.get_stats()
        print(f"  - Hit rate: {lru_stats['hit_rate']:.2%}")
        print(f"  - Cache size: {lru_stats['current_size']}")
        
        # Performance assertions
        assert lru_write_time < 1.0  # Should be fast for in-memory
        assert lru_read_time < 0.5  # Should be very fast for reads