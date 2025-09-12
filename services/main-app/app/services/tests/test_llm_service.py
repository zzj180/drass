"""
Tests for Unified LLM Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from app.services.llm_service_enhanced import (
    UnifiedLLMService,
    LLMProvider,
    CacheStrategy,
    LRUCache
)
from app.services.providers.base import LLMResponse, TokenUsage


class TestLRUCache:
    """Test LRU cache implementation"""
    
    def test_cache_basic_operations(self):
        cache = LRUCache(max_size=3)
        
        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None
        
        # Test LRU eviction
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    def test_cache_lru_ordering(self):
        cache = LRUCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it most recently used
        cache.get("key1")
        
        # Add new item, should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key2") is None
        assert cache.get("key1") == "value1"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"


@pytest.mark.asyncio
class TestUnifiedLLMService:
    """Test Unified LLM Service"""
    
    async def test_service_initialization(self):
        """Test service initialization"""
        service = UnifiedLLMService()
        
        with patch('app.services.llm_service_enhanced.LocalMLXProvider') as mock_mlx:
            mock_provider = AsyncMock()
            mock_provider.initialize = AsyncMock()
            mock_mlx.return_value = mock_provider
            
            await service.initialize()
            
            assert service._initialized
            assert service.primary_provider is not None
    
    async def test_generate_with_cache(self):
        """Test generation with caching"""
        service = UnifiedLLMService()
        service.cache_strategy = CacheStrategy.MEMORY
        service._initialized = True
        
        # Mock provider
        mock_provider = AsyncMock()
        mock_response = LLMResponse(
            content="Test response",
            model="test-model",
            provider="test",
            usage={"total_tokens": 100},
            response_time=0.5
        )
        mock_provider.generate = AsyncMock(return_value=mock_response)
        
        service.providers = {"test": mock_provider}
        service.primary_provider = "test"
        
        # First call should hit provider
        messages = [{"role": "user", "content": "Hello"}]
        response1 = await service.generate(messages, use_cache=True)
        assert response1.content == "Test response"
        mock_provider.generate.assert_called_once()
        
        # Second call should hit cache
        response2 = await service.generate(messages, use_cache=True)
        assert response2.content == "Test response"
        assert response2.metadata.get("cached") is True
        # Provider should not be called again
        mock_provider.generate.assert_called_once()
    
    async def test_generate_without_cache(self):
        """Test generation without caching"""
        service = UnifiedLLMService()
        service._initialized = True
        
        # Mock provider
        mock_provider = AsyncMock()
        mock_response = LLMResponse(
            content="Test response",
            model="test-model",
            provider="test"
        )
        mock_provider.generate = AsyncMock(return_value=mock_response)
        
        service.providers = {"test": mock_provider}
        service.primary_provider = "test"
        
        messages = [{"role": "user", "content": "Hello"}]
        
        # Multiple calls without cache should all hit provider
        await service.generate(messages, use_cache=False)
        await service.generate(messages, use_cache=False)
        
        assert mock_provider.generate.call_count == 2
    
    async def test_failover_mechanism(self):
        """Test automatic failover to backup provider"""
        service = UnifiedLLMService()
        service._initialized = True
        
        # Mock primary provider that fails
        mock_primary = AsyncMock()
        mock_primary.generate = AsyncMock(side_effect=Exception("Primary failed"))
        
        # Mock backup provider that succeeds
        mock_backup = AsyncMock()
        mock_response = LLMResponse(
            content="Backup response",
            model="backup-model",
            provider="backup"
        )
        mock_backup.generate = AsyncMock(return_value=mock_response)
        
        service.providers = {
            "primary": mock_primary,
            "backup": mock_backup
        }
        service.primary_provider = "primary"
        service.fallback_providers = ["backup"]
        service.max_retries = 2  # Reduce retries for test
        
        messages = [{"role": "user", "content": "Hello"}]
        response = await service.generate(messages, use_cache=False)
        
        assert response.content == "Backup response"
        assert mock_primary.generate.call_count == 2  # Tried with retries
        assert mock_backup.generate.call_count == 1  # Succeeded on first try
    
    async def test_retry_mechanism(self):
        """Test retry mechanism with eventual success"""
        service = UnifiedLLMService()
        service._initialized = True
        
        # Mock provider that fails twice then succeeds
        mock_provider = AsyncMock()
        mock_response = LLMResponse(
            content="Success after retries",
            model="test-model",
            provider="test"
        )
        mock_provider.generate = AsyncMock(
            side_effect=[
                Exception("First attempt failed"),
                Exception("Second attempt failed"),
                mock_response
            ]
        )
        
        service.providers = {"test": mock_provider}
        service.primary_provider = "test"
        service.max_retries = 3
        service.retry_delay = 0.01  # Short delay for testing
        
        messages = [{"role": "user", "content": "Hello"}]
        response = await service.generate(messages, use_cache=False)
        
        assert response.content == "Success after retries"
        assert mock_provider.generate.call_count == 3
    
    async def test_cost_tracking(self):
        """Test cost tracking across providers"""
        service = UnifiedLLMService()
        service._initialized = True
        
        # Mock provider with usage information
        mock_provider = AsyncMock()
        mock_response = LLMResponse(
            content="Test response",
            model="test-model",
            provider="test",
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        )
        mock_provider.generate = AsyncMock(return_value=mock_response)
        mock_provider.estimate_cost = MagicMock(return_value=0.001)
        
        service.providers = {"test": mock_provider}
        service.primary_provider = "test"
        
        messages = [{"role": "user", "content": "Hello"}]
        
        # Generate multiple responses
        await service.generate(messages, use_cache=False)
        await service.generate(messages, use_cache=False)
        
        assert service.total_cost == 0.002
        assert service.cost_by_provider["test"] == 0.002
    
    async def test_streaming_generation(self):
        """Test streaming generation"""
        service = UnifiedLLMService()
        service._initialized = True
        
        # Mock provider with streaming
        mock_provider = AsyncMock()
        
        async def mock_stream():
            for chunk in ["Hello", " ", "world", "!"]:
                yield chunk
        
        mock_provider.stream_generate = mock_stream
        
        service.providers = {"test": mock_provider}
        service.primary_provider = "test"
        
        messages = [{"role": "user", "content": "Hello"}]
        
        chunks = []
        async for chunk in service.stream_generate(messages):
            chunks.append(chunk)
        
        assert "".join(chunks) == "Hello world!"
    
    async def test_health_check(self):
        """Test health check aggregation"""
        service = UnifiedLLMService()
        service._initialized = True
        
        # Mock providers with different health states
        mock_healthy = AsyncMock()
        mock_healthy.health_check = AsyncMock(return_value={"status": "healthy"})
        
        mock_unhealthy = AsyncMock()
        mock_unhealthy.health_check = AsyncMock(return_value={"status": "unhealthy"})
        
        service.providers = {
            "healthy": mock_healthy,
            "unhealthy": mock_unhealthy
        }
        
        health = await service.health_check()
        
        assert health["status"] == "degraded"  # One healthy, one unhealthy
        assert "healthy" in health["providers"]
        assert "unhealthy" in health["providers"]
    
    async def test_token_counting(self):
        """Test token counting"""
        service = UnifiedLLMService()
        service._initialized = True
        
        # Mock provider with token counting
        mock_provider = AsyncMock()
        mock_provider.count_tokens = MagicMock(return_value=25)
        
        service.providers = {"test": mock_provider}
        service.primary_provider = "test"
        
        count = service.count_tokens("This is a test message")
        assert count == 25
        mock_provider.count_tokens.assert_called_once_with("This is a test message")
    
    async def test_stats_collection(self):
        """Test statistics collection"""
        service = UnifiedLLMService()
        service._initialized = True
        
        # Mock provider with metrics
        mock_provider = AsyncMock()
        mock_provider._initialized = True
        mock_provider.metrics = {
            "total_requests": 10,
            "total_errors": 2,
            "average_response_time": 0.5
        }
        
        service.providers = {"test": mock_provider}
        service.primary_provider = "test"
        service.total_cost = 0.05
        service.cost_by_provider = {"test": 0.05}
        
        stats = await service.get_stats()
        
        assert stats["initialized"] is True
        assert stats["primary_provider"] == "test"
        assert stats["total_cost"] == 0.05
        assert stats["providers"]["test"]["metrics"]["total_requests"] == 10


@pytest.mark.asyncio
class TestProviderIntegration:
    """Test provider integration (requires mock servers)"""
    
    @pytest.mark.skip(reason="Requires running LLM servers")
    async def test_local_mlx_integration(self):
        """Test integration with local MLX server"""
        from app.services.providers.local_mlx import LocalMLXProvider
        
        provider = LocalMLXProvider({
            "base_url": "http://localhost:8001/v1",
            "model_name": "qwen3-8b-mlx"
        })
        
        await provider.initialize()
        
        response = await provider.generate(
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        
        assert response.content
        assert response.provider == "local_mlx"
    
    @pytest.mark.skip(reason="Requires API key")
    async def test_openrouter_integration(self):
        """Test integration with OpenRouter"""
        from app.services.providers.openrouter import OpenRouterProvider
        
        provider = OpenRouterProvider({
            "api_key": "test-key",
            "default_model": "meta-llama/llama-3-8b-instruct"
        })
        
        await provider.initialize()
        
        response = await provider.generate(
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        
        assert response.content
        assert response.provider == "openrouter"