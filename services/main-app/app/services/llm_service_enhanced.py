"""
Enhanced Unified LLM Service with multiple providers, caching, and failover
"""

import logging
import hashlib
import json
import time
from typing import Optional, List, Dict, Any, AsyncGenerator, Union
from enum import Enum
import asyncio
from collections import OrderedDict
import redis.asyncio as redis

from app.core.config import settings
from .providers import (
    BaseLLMProvider,
    OpenRouterProvider,
    LocalMLXProvider,
    LMStudioProvider
)
from .providers.base import LLMResponse, TokenUsage

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENROUTER = "openrouter"
    LOCAL_MLX = "local_mlx"
    LMSTUDIO = "lmstudio"
    AUTO = "auto"  # Automatic selection based on availability


class CacheStrategy(Enum):
    """Cache strategies"""
    NONE = "none"
    MEMORY = "memory"
    REDIS = "redis"


class LRUCache:
    """Simple LRU cache implementation"""
    
    def __init__(self, max_size: int = 100):
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            # Remove least recently used
            self.cache.popitem(last=False)
    
    def clear(self):
        self.cache.clear()


class UnifiedLLMService:
    """
    Unified LLM Service with multiple provider support, caching, retry, and failover
    """
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.primary_provider = None
        self.fallback_providers = []
        self._initialized = False
        
        # Caching
        self.cache_strategy = CacheStrategy(
            settings.LLM_CACHE_STRATEGY if hasattr(settings, 'LLM_CACHE_STRATEGY') else "memory"
        )
        self.memory_cache = LRUCache(max_size=100)
        self.redis_client = None
        self.cache_ttl = 3600  # 1 hour default
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.retry_backoff = 2.0  # exponential backoff factor
        
        # Cost tracking
        self.total_cost = 0.0
        self.cost_by_provider = {}
    
    async def initialize(self):
        """Initialize the unified LLM service with configured providers"""
        if self._initialized:
            return
        
        logger.info("Initializing Unified LLM Service")
        
        # Initialize cache
        await self._initialize_cache()
        
        # Initialize providers based on configuration
        await self._initialize_providers()
        
        # Set primary and fallback providers
        self._set_provider_priority()
        
        self._initialized = True
        logger.info(f"Unified LLM Service initialized with providers: {list(self.providers.keys())}")
    
    async def _initialize_cache(self):
        """Initialize caching based on strategy"""
        if self.cache_strategy == CacheStrategy.REDIS:
            try:
                redis_url = settings.REDIS_URL if hasattr(settings, 'REDIS_URL') else "redis://localhost:6379"
                self.redis_client = await redis.from_url(redis_url, decode_responses=True)
                await self.redis_client.ping()
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}. Falling back to memory cache.")
                self.cache_strategy = CacheStrategy.MEMORY
    
    async def _initialize_providers(self):
        """Initialize all configured providers"""
        # OpenRouter provider
        if hasattr(settings, 'OPENROUTER_API_KEY') and settings.OPENROUTER_API_KEY:
            try:
                provider = OpenRouterProvider({
                    "api_key": settings.OPENROUTER_API_KEY,
                    "default_model": getattr(settings, 'OPENROUTER_MODEL', 'meta-llama/llama-3-8b-instruct'),
                    "site_url": getattr(settings, 'SITE_URL', 'https://drass.ai'),
                    "site_name": getattr(settings, 'SITE_NAME', 'Drass Compliance Assistant')
                })
                await provider.initialize()
                self.providers[LLMProvider.OPENROUTER.value] = provider
                logger.info("OpenRouter provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenRouter provider: {e}")
        
        # Local MLX provider
        try:
            mlx_config = {
                "base_url": getattr(settings, 'LLM_BASE_URL', 'http://localhost:8001/v1'),
                "model_name": getattr(settings, 'LLM_MODEL', 'qwen3-8b-mlx')
            }
            provider = LocalMLXProvider(mlx_config)
            await provider.initialize()
            self.providers[LLMProvider.LOCAL_MLX.value] = provider
            logger.info("Local MLX provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Local MLX provider: {e}")
        
        # LM Studio provider
        if hasattr(settings, 'LMSTUDIO_ENABLED') and settings.LMSTUDIO_ENABLED:
            try:
                lmstudio_config = {
                    "base_url": getattr(settings, 'LMSTUDIO_BASE_URL', 'http://localhost:1234/v1'),
                    "model_name": getattr(settings, 'LMSTUDIO_MODEL', 'local-model')
                }
                provider = LMStudioProvider(lmstudio_config)
                await provider.initialize()
                self.providers[LLMProvider.LMSTUDIO.value] = provider
                logger.info("LM Studio provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize LM Studio provider: {e}")
        
        if not self.providers:
            raise Exception("No LLM providers could be initialized")
    
    def _set_provider_priority(self):
        """Set primary and fallback providers based on configuration and availability"""
        provider_priority = [
            LLMProvider.LOCAL_MLX.value,
            LLMProvider.LMSTUDIO.value,
            LLMProvider.OPENROUTER.value
        ]
        
        # Override with configured provider
        if hasattr(settings, 'LLM_PROVIDER'):
            configured_provider = settings.LLM_PROVIDER.lower()
            if configured_provider in [p.value for p in LLMProvider if p != LLMProvider.AUTO]:
                provider_priority.insert(0, configured_provider)
        
        # Set primary and fallback providers
        for provider_name in provider_priority:
            if provider_name in self.providers:
                if not self.primary_provider:
                    self.primary_provider = provider_name
                else:
                    self.fallback_providers.append(provider_name)
        
        logger.info(f"Primary provider: {self.primary_provider}, Fallback providers: {self.fallback_providers}")
    
    def _get_cache_key(self, messages: List[Dict], **kwargs) -> str:
        """Generate cache key from messages and parameters"""
        cache_data = {
            "messages": messages,
            **kwargs
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    async def _get_from_cache(self, key: str) -> Optional[LLMResponse]:
        """Get response from cache"""
        if self.cache_strategy == CacheStrategy.NONE:
            return None
        
        if self.cache_strategy == CacheStrategy.REDIS and self.redis_client:
            try:
                cached = await self.redis_client.get(f"llm:{key}")
                if cached:
                    data = json.loads(cached)
                    return LLMResponse(**data)
            except Exception as e:
                logger.warning(f"Redis cache get error: {e}")
        
        # Fallback to memory cache
        cached = self.memory_cache.get(key)
        if cached:
            return cached
        
        return None
    
    async def _set_cache(self, key: str, response: LLMResponse):
        """Set response in cache"""
        if self.cache_strategy == CacheStrategy.NONE:
            return
        
        if self.cache_strategy == CacheStrategy.REDIS and self.redis_client:
            try:
                cache_data = {
                    "content": response.content,
                    "model": response.model,
                    "provider": response.provider,
                    "usage": response.usage,
                    "response_time": response.response_time,
                    "metadata": response.metadata
                }
                await self.redis_client.setex(
                    f"llm:{key}",
                    self.cache_ttl,
                    json.dumps(cache_data)
                )
                return
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")
        
        # Fallback to memory cache
        self.memory_cache.set(key, response)
    
    async def generate(
        self,
        messages: Union[str, List[Dict[str, str]]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        provider: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion with automatic retry and failover
        
        Args:
            messages: Either a string prompt or list of message dicts
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            provider: Specific provider to use (optional)
            use_cache: Whether to use caching
            **kwargs: Additional provider-specific parameters
        
        Returns:
            LLMResponse object with completion
        """
        if not self._initialized:
            await self.initialize()
        
        # Convert string to messages format
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(messages, max_tokens=max_tokens, temperature=temperature, **kwargs)
            cached_response = await self._get_from_cache(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for request")
                cached_response.metadata = cached_response.metadata or {}
                cached_response.metadata["cached"] = True
                return cached_response
        
        # Determine providers to try
        providers_to_try = []
        if provider and provider in self.providers:
            providers_to_try = [provider]
        else:
            providers_to_try = [self.primary_provider] + self.fallback_providers
        
        last_error = None
        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue
            
            provider_instance = self.providers[provider_name]
            
            # Retry logic for current provider
            for attempt in range(self.max_retries):
                try:
                    logger.debug(f"Attempting generation with {provider_name} (attempt {attempt + 1}/{self.max_retries})")
                    
                    response = await provider_instance.generate(
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs
                    )
                    
                    # Update cost tracking
                    if response.usage:
                        token_usage = TokenUsage(
                            prompt_tokens=response.usage.get("prompt_tokens", 0),
                            completion_tokens=response.usage.get("completion_tokens", 0),
                            total_tokens=response.usage.get("total_tokens", 0)
                        )
                        cost = provider_instance.estimate_cost(token_usage, response.model)
                        self.total_cost += cost
                        self.cost_by_provider[provider_name] = self.cost_by_provider.get(provider_name, 0) + cost
                        response.metadata = response.metadata or {}
                        response.metadata["estimated_cost"] = cost
                    
                    # Cache successful response
                    if use_cache:
                        await self._set_cache(cache_key, response)
                    
                    return response
                    
                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1} failed for {provider_name}: {e}")
                    
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (self.retry_backoff ** attempt)
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All retries exhausted for {provider_name}")
            
            # Try next provider if available
            if provider_name != providers_to_try[-1]:
                logger.info(f"Failing over from {provider_name} to next provider")
        
        # All providers failed
        error_msg = f"All providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def stream_generate(
        self,
        messages: Union[str, List[Dict[str, str]]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream generation with automatic failover
        
        Args:
            messages: Either a string prompt or list of message dicts
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            provider: Specific provider to use (optional)
            **kwargs: Additional provider-specific parameters
        
        Yields:
            String chunks of the generated response
        """
        if not self._initialized:
            await self.initialize()
        
        # Convert string to messages format
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        
        # Determine providers to try
        providers_to_try = []
        if provider and provider in self.providers:
            providers_to_try = [provider]
        else:
            providers_to_try = [self.primary_provider] + self.fallback_providers
        
        last_error = None
        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue
            
            provider_instance = self.providers[provider_name]
            
            try:
                logger.debug(f"Attempting streaming generation with {provider_name}")
                
                async for chunk in provider_instance.stream_generate(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                ):
                    yield chunk
                
                return  # Successful completion
                
            except Exception as e:
                last_error = e
                logger.warning(f"Streaming failed for {provider_name}: {e}")
                
                # Try next provider if available
                if provider_name != providers_to_try[-1]:
                    logger.info(f"Failing over from {provider_name} to next provider")
                    # Yield error message to indicate failover
                    yield f"\n[Switching to backup provider...]\n"
        
        # All providers failed
        error_msg = f"All providers failed for streaming. Last error: {last_error}"
        logger.error(error_msg)
        yield f"\n[Error: {error_msg}]\n"
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all providers"""
        stats = {
            "initialized": self._initialized,
            "primary_provider": self.primary_provider,
            "fallback_providers": self.fallback_providers,
            "total_cost": self.total_cost,
            "cost_by_provider": self.cost_by_provider,
            "cache_strategy": self.cache_strategy.value,
            "providers": {}
        }
        
        for name, provider in self.providers.items():
            stats["providers"][name] = {
                "initialized": provider._initialized,
                "metrics": provider.metrics
            }
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for all providers"""
        health = {
            "status": "healthy" if self._initialized else "not_initialized",
            "providers": {}
        }
        
        for name, provider in self.providers.items():
            provider_health = await provider.health_check()
            health["providers"][name] = provider_health
        
        # Overall health status
        healthy_count = sum(1 for p in health["providers"].values() if p.get("status") == "healthy")
        if healthy_count == 0:
            health["status"] = "unhealthy"
        elif healthy_count < len(self.providers):
            health["status"] = "degraded"
        
        return health
    
    def count_tokens(self, text: str, provider: Optional[str] = None) -> int:
        """Count tokens using specified or primary provider"""
        provider_name = provider or self.primary_provider
        if provider_name in self.providers:
            return self.providers[provider_name].count_tokens(text)
        # Fallback to simple estimation
        return len(text) // 4
    
    async def clear_cache(self):
        """Clear all cached responses"""
        self.memory_cache.clear()
        
        if self.cache_strategy == CacheStrategy.REDIS and self.redis_client:
            try:
                keys = await self.redis_client.keys("llm:*")
                if keys:
                    await self.redis_client.delete(*keys)
                logger.info("Redis cache cleared")
            except Exception as e:
                logger.warning(f"Failed to clear Redis cache: {e}")
    
    async def close(self):
        """Close all provider connections and cleanup"""
        logger.info("Closing Unified LLM Service")
        
        # Close all providers
        for provider in self.providers.values():
            await provider.close()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        self._initialized = False


# Singleton instance
unified_llm_service = UnifiedLLMService()