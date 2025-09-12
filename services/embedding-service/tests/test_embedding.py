"""
Tests for enhanced embedding service
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import numpy as np
import time

from cache.lru_cache import LRUEmbeddingCache
from cache.redis_cache import RedisEmbeddingCache
from batch_processor import BatchProcessor, DynamicBatchProcessor


class TestLRUCache:
    """Test LRU cache implementation"""
    
    def test_cache_basic_operations(self):
        """Test basic cache operations"""
        cache = LRUEmbeddingCache(max_size=3, ttl=3600)
        
        # Test set and get
        embedding = [0.1, 0.2, 0.3]
        cache.set_embedding("test text", "model1", embedding)
        
        retrieved = cache.get_embedding("test text", "model1")
        assert retrieved == embedding
        
        # Test cache miss
        assert cache.get_embedding("unknown text", "model1") is None
        
        # Test statistics
        assert cache.hits == 1
        assert cache.misses == 1
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction policy"""
        cache = LRUEmbeddingCache(max_size=2, ttl=3600)
        
        cache.set_embedding("text1", "model", [1])
        cache.set_embedding("text2", "model", [2])
        cache.set_embedding("text3", "model", [3])  # Should evict text1
        
        assert cache.get_embedding("text1", "model") is None
        assert cache.get_embedding("text2", "model") == [2]
        assert cache.get_embedding("text3", "model") == [3]
    
    def test_cache_ttl_expiration(self):
        """Test TTL expiration"""
        cache = LRUEmbeddingCache(max_size=10, ttl=0.1)  # 100ms TTL
        
        cache.set_embedding("text", "model", [1, 2, 3])
        assert cache.get_embedding("text", "model") == [1, 2, 3]
        
        time.sleep(0.2)  # Wait for expiration
        assert cache.get_embedding("text", "model") is None
    
    def test_batch_operations(self):
        """Test batch cache operations"""
        cache = LRUEmbeddingCache(max_size=10, ttl=3600)
        
        texts = ["text1", "text2", "text3"]
        embeddings = [[1], [2], [3]]
        
        cache.set_batch(texts, "model", embeddings)
        
        cached = cache.get_batch(texts + ["text4"], "model")
        assert 0 in cached and cached[0] == [1]
        assert 1 in cached and cached[1] == [2]
        assert 2 in cached and cached[2] == [3]
        assert 3 not in cached
    
    def test_cache_stats(self):
        """Test cache statistics"""
        cache = LRUEmbeddingCache(max_size=10, ttl=3600)
        
        # Generate some hits and misses
        cache.set_embedding("text1", "model", [1])
        cache.get_embedding("text1", "model")  # Hit
        cache.get_embedding("text2", "model")  # Miss
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["current_size"] == 1


@pytest.mark.asyncio
class TestRedisCache:
    """Test Redis cache implementation"""
    
    @patch('redis.asyncio.from_url')
    async def test_cache_initialization(self, mock_redis):
        """Test Redis cache initialization"""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis.return_value = mock_client
        
        cache = RedisEmbeddingCache("redis://localhost:6379", ttl=3600)
        await cache.initialize()
        
        assert cache.enabled
        mock_client.ping.assert_called_once()
    
    @patch('redis.asyncio.from_url')
    async def test_cache_operations(self, mock_redis):
        """Test Redis cache operations"""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.get = AsyncMock(return_value='[1, 2, 3]')
        mock_client.setex = AsyncMock()
        mock_redis.return_value = mock_client
        
        cache = RedisEmbeddingCache()
        await cache.initialize()
        
        # Test get
        embedding = await cache.get_embedding("test", "model")
        assert embedding == [1, 2, 3]
        
        # Test set
        await cache.set_embedding("test", "model", [4, 5, 6])
        mock_client.setex.assert_called()
    
    @patch('redis.asyncio.from_url')
    async def test_batch_operations(self, mock_redis):
        """Test Redis batch operations"""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis.return_value = mock_client
        
        # Mock pipeline
        mock_pipeline = AsyncMock()
        mock_pipeline.get = MagicMock()
        mock_pipeline.setex = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=['[1]', None, '[3]'])
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)
        
        cache = RedisEmbeddingCache()
        await cache.initialize()
        
        # Test batch get
        cached = await cache.get_batch(["text1", "text2", "text3"], "model")
        assert 0 in cached and cached[0] == [1]
        assert 1 not in cached
        assert 2 in cached and cached[2] == [3]


@pytest.mark.asyncio
class TestBatchProcessor:
    """Test batch processor"""
    
    async def test_batch_processor_initialization(self):
        """Test batch processor initialization"""
        processor = BatchProcessor(batch_size=16, max_wait_time=0.05)
        await processor.start()
        
        assert processor.processing
        assert processor.batch_size == 16
        
        await processor.stop()
        assert not processor.processing
    
    async def test_batch_collection(self):
        """Test batch collection and processing"""
        processor = BatchProcessor(batch_size=3, max_wait_time=0.1)
        
        # Mock embedding model
        with patch('app.embedding_model') as mock_model:
            mock_model.embed_texts = AsyncMock(return_value={
                "embeddings": [[1], [2], [3], [4]],
                "model": "test",
                "usage": {}
            })
            
            await processor.start()
            
            # Add requests
            futures = []
            for i in range(4):
                future = await processor.add_request([f"text{i}"], f"req{i}")
                futures.append(future)
            
            # Wait for processing
            results = await asyncio.gather(*futures)
            
            assert len(results) == 4
            for result in results:
                assert "embeddings" in result
            
            await processor.stop()
    
    async def test_dynamic_batch_processor(self):
        """Test dynamic batch processor"""
        processor = DynamicBatchProcessor(
            min_batch_size=2,
            max_batch_size=8,
            target_latency=0.1
        )
        
        assert processor.current_batch_size == 2
        
        # Simulate low latency - should increase batch size
        processor.latency_history = [0.05] * 10
        processor._adjust_batch_size()
        assert processor.current_batch_size > 2
        
        # Simulate high latency - should decrease batch size
        processor.latency_history = [0.2] * 10
        processor._adjust_batch_size()
        assert processor.current_batch_size == 2  # Min size


class TestEmbeddingModel:
    """Test embedding model functionality"""
    
    @pytest.mark.asyncio
    @patch('sentence_transformers.SentenceTransformer')
    async def test_sentence_transformer_init(self, mock_st):
        """Test Sentence Transformer initialization"""
        from app_enhanced import EmbeddingModel
        
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension = MagicMock(return_value=768)
        mock_st.return_value = mock_model
        
        model = EmbeddingModel()
        model.provider = "sentence-transformers"
        await model.initialize()
        
        assert model.dimension == 768
        assert model.model is not None
    
    @pytest.mark.asyncio
    async def test_embedding_with_cache(self):
        """Test embedding generation with cache"""
        from app_enhanced import EmbeddingModel
        
        with patch('sentence_transformers.SentenceTransformer') as mock_st:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension = MagicMock(return_value=768)
            mock_model.encode = MagicMock(return_value=np.array([[1, 2], [3, 4]]))
            mock_st.return_value = mock_model
            
            model = EmbeddingModel()
            model.provider = "sentence-transformers"
            await model.initialize()
            
            # Create mock cache
            mock_cache = MagicMock()
            mock_cache.get_batch = AsyncMock(return_value={0: [1, 2]})  # First text cached
            mock_cache.set_batch = AsyncMock()
            
            # Test with cache
            with patch('app_enhanced.cache_service', mock_cache):
                result = await model.embed_texts(["cached", "not_cached"], use_cache=True)
                
                assert len(result["embeddings"]) == 2
                assert result["cached"] == [True, False]
                assert result["usage"]["cached_count"] == 1
                assert result["usage"]["processed_count"] == 1
                
                # Verify only uncached text was processed
                mock_model.encode.assert_called_once()
                call_args = mock_model.encode.call_args[0][0]
                assert len(call_args) == 1
                assert call_args[0] == "not_cached"


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests"""
    
    async def test_end_to_end_embedding(self):
        """Test end-to-end embedding generation"""
        from app_enhanced import EmbeddingModel
        
        # This would require actual model loading
        # Skipped in unit tests, run separately with real models
        pass
    
    async def test_concurrent_requests(self):
        """Test handling concurrent embedding requests"""
        from app_enhanced import EmbeddingModel
        
        with patch('sentence_transformers.SentenceTransformer') as mock_st:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension = MagicMock(return_value=768)
            mock_model.encode = MagicMock(return_value=np.array([[1], [2]]))
            mock_st.return_value = mock_model
            
            model = EmbeddingModel()
            model.provider = "sentence-transformers"
            await model.initialize()
            
            # Simulate concurrent requests
            tasks = []
            for i in range(10):
                task = model.embed_texts([f"text{i}"], use_cache=False)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 10
            for result in results:
                assert "embeddings" in result
                assert len(result["embeddings"]) == 1