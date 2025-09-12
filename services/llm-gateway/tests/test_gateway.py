"""Tests for LLM Gateway Service."""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, LLMProvider, ModelRouter, CompletionRequest

client = TestClient(app)


class TestLLMProvider:
    """Test LLM Provider functionality."""
    
    def test_provider_initialization(self):
        """Test provider initialization."""
        config = {
            'base_url': 'http://localhost:8000',
            'api_key': 'test-key',
            'models': ['model1', 'model2'],
            'priority': 1,
            'max_rpm': 60
        }
        
        provider = LLMProvider('test_provider', config)
        
        assert provider.name == 'test_provider'
        assert provider.base_url == 'http://localhost:8000'
        assert provider.api_key == 'test-key'
        assert provider.models == ['model1', 'model2']
        assert provider.priority == 1
        assert provider.max_requests_per_minute == 60
        assert provider.is_healthy is True
    
    def test_can_handle_request(self):
        """Test request handling capacity check."""
        config = {
            'base_url': 'http://localhost:8000',
            'api_key': 'test-key',
            'max_rpm': 2  # Very low for testing
        }
        
        provider = LLMProvider('test', config)
        
        # Should handle first requests
        assert provider.can_handle_request() is True
        provider.current_requests = 1
        assert provider.can_handle_request() is True
        
        # Should not handle when at limit
        provider.current_requests = 2
        assert provider.can_handle_request() is False
        
        # Should not handle when unhealthy
        provider.current_requests = 0
        provider.is_healthy = False
        assert provider.can_handle_request() is False
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality."""
        config = {
            'base_url': 'http://localhost:8000',
            'api_key': 'test-key'
        }
        
        provider = LLMProvider('test', config)
        
        # Mock httpx client
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await provider.check_health()
            assert result is True
            assert provider.is_healthy is True
            
        # Test unhealthy response
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await provider.check_health()
            assert result is False
            assert provider.is_healthy is False


class TestModelRouter:
    """Test Model Router functionality."""
    
    def test_router_initialization(self):
        """Test router initialization."""
        router = ModelRouter()
        
        assert router.providers is not None
        assert router.model_map is not None
        assert router.routing_rules is not None
    
    @pytest.mark.asyncio
    async def test_select_provider(self):
        """Test provider selection."""
        router = ModelRouter()
        
        # Add test providers
        router.providers['provider1'] = LLMProvider('provider1', {
            'base_url': 'http://localhost:8001',
            'api_key': 'key1',
            'models': ['model1'],
            'priority': 1,
            'max_rpm': 60
        })
        
        router.providers['provider2'] = LLMProvider('provider2', {
            'base_url': 'http://localhost:8002',
            'api_key': 'key2',
            'models': ['model1', 'model2'],
            'priority': 2,
            'max_rpm': 60
        })
        
        router.model_map = {
            'model1': ['provider1', 'provider2'],
            'model2': ['provider2']
        }
        
        # Should select provider1 for model1 (lower priority)
        provider = await router.select_provider('model1')
        assert provider is not None
        assert provider.name == 'provider1'
        
        # Should select provider2 for model2
        provider = await router.select_provider('model2')
        assert provider is not None
        assert provider.name == 'provider2'
        
        # Test with unhealthy provider
        router.providers['provider1'].is_healthy = False
        provider = await router.select_provider('model1')
        assert provider is not None
        assert provider.name == 'provider2'
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        router = ModelRouter()
        
        request_data = {
            'model': 'test-model',
            'prompt': 'test prompt',
            'temperature': 0.7
        }
        
        key1 = router._get_cache_key(request_data)
        key2 = router._get_cache_key(request_data)
        
        # Same input should generate same key
        assert key1 == key2
        
        # Different input should generate different key
        request_data['temperature'] = 0.8
        key3 = router._get_cache_key(request_data)
        assert key1 != key3


class TestAPIEndpoints:
    """Test API endpoints."""
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert 'status' in data
        assert 'healthy_providers' in data
        assert 'unhealthy_providers' in data
        assert 'cache_enabled' in data
    
    def test_list_models_endpoint(self):
        """Test model listing endpoint."""
        response = client.get("/v1/models")
        assert response.status_code == 200
        
        data = response.json()
        assert 'data' in data
        assert 'object' in data
        assert data['object'] == 'list'
    
    @patch('app.router.execute_with_fallback')
    def test_completion_endpoint(self, mock_execute):
        """Test completion endpoint."""
        # Mock the execute_with_fallback to return a generator
        async def mock_generator():
            yield {'choices': [{'text': 'Test response'}]}
        
        mock_execute.return_value = mock_generator()
        
        request_data = {
            'model': 'test-model',
            'prompt': 'Test prompt',
            'max_tokens': 100
        }
        
        response = client.post("/v1/completions", json=request_data)
        assert response.status_code == 200
    
    @patch('app.router.execute_with_fallback')
    def test_chat_completion_endpoint(self, mock_execute):
        """Test chat completion endpoint."""
        async def mock_generator():
            yield {
                'choices': [{
                    'message': {'role': 'assistant', 'content': 'Test response'}
                }],
                'usage': {
                    'prompt_tokens': 10,
                    'completion_tokens': 5,
                    'total_tokens': 15
                }
            }
        
        mock_execute.return_value = mock_generator()
        
        request_data = {
            'model': 'test-model',
            'messages': [
                {'role': 'user', 'content': 'Hello'}
            ],
            'max_tokens': 100
        }
        
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 200
    
    @patch('app.router.execute_with_fallback')
    def test_embedding_endpoint(self, mock_execute):
        """Test embedding endpoint."""
        async def mock_generator():
            yield {
                'data': [{
                    'embedding': [0.1, 0.2, 0.3],
                    'index': 0
                }],
                'model': 'test-embedding-model'
            }
        
        mock_execute.return_value = mock_generator()
        
        request_data = {
            'model': 'test-embedding',
            'input': ['Test text']
        }
        
        response = client.post("/v1/embeddings", json=request_data)
        assert response.status_code == 200
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert 'llm_gateway_requests_total' in response.text
    
    def test_admin_reload_endpoint(self):
        """Test configuration reload endpoint."""
        response = client.post("/admin/reload")
        assert response.status_code == 200
        
        data = response.json()
        assert 'status' in data
    
    @patch('app.router.providers')
    @pytest.mark.asyncio
    async def test_admin_health_check_endpoint(self, mock_providers):
        """Test forced health check endpoint."""
        # Create mock provider
        mock_provider = AsyncMock()
        mock_provider.check_health.return_value = True
        mock_provider.last_health_check = asyncio.Queue()
        
        mock_providers.items.return_value = [('test_provider', mock_provider)]
        
        response = client.post("/admin/health-check")
        assert response.status_code == 200


class TestCompletionRequest:
    """Test request models."""
    
    def test_completion_request_defaults(self):
        """Test CompletionRequest default values."""
        request = CompletionRequest(prompt="Test")
        
        assert request.model == "auto"
        assert request.prompt == "Test"
        assert request.max_tokens == 1000
        assert request.temperature == 0.7
        assert request.top_p == 1.0
        assert request.stream is False
        assert request.n == 1
    
    def test_completion_request_validation(self):
        """Test CompletionRequest validation."""
        # Valid request with all fields
        request = CompletionRequest(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=500,
            temperature=0.5,
            stream=True
        )
        
        assert request.model == "gpt-3.5-turbo"
        assert request.messages[0]["content"] == "Hello"
        assert request.max_tokens == 500
        assert request.temperature == 0.5
        assert request.stream is True


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('app.redis_client') as mock:
        mock.get.return_value = None
        mock.setex.return_value = True
        yield mock


def test_caching_with_redis(mock_redis):
    """Test caching with Redis."""
    request_data = {
        'model': 'test-model',
        'prompt': 'Test prompt'
    }
    
    # First request should miss cache
    response = client.post("/v1/completions", json=request_data)
    
    # Verify Redis was checked
    assert mock_redis.get.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])