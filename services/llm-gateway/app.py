#!/usr/bin/env python3
"""
LLM Gateway Service - Unified interface for multiple LLM providers
Supports load balancing, failover, and request routing
"""

import os
import time
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import yaml
from cachetools import TTLCache
import redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LLM Gateway Service",
    description="Unified gateway for multiple LLM providers with load balancing and failover",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics
request_counter = Counter('llm_gateway_requests_total', 'Total LLM requests', ['provider', 'model', 'status'])
latency_histogram = Histogram('llm_gateway_latency_seconds', 'Request latency', ['provider', 'model'])
token_counter = Counter('llm_gateway_tokens_total', 'Total tokens processed', ['provider', 'model', 'type'])
active_connections = Gauge('llm_gateway_active_connections', 'Active connections', ['provider'])
error_counter = Counter('llm_gateway_errors_total', 'Total errors', ['provider', 'error_type'])

# Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY = float(os.getenv('RETRY_DELAY', '1.0'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))

# Initialize cache
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    cache_enabled = True
except:
    logger.warning("Redis not available, using in-memory cache")
    redis_client = None
    cache_enabled = False

memory_cache = TTLCache(maxsize=1000, ttl=CACHE_TTL)

# Request/Response Models
class CompletionRequest(BaseModel):
    model: str = Field(default="auto", description="Model name or 'auto' for automatic selection")
    prompt: Optional[str] = Field(None, description="Prompt for completion")
    messages: Optional[List[Dict[str, str]]] = Field(None, description="Messages for chat completion")
    max_tokens: int = Field(default=1000, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    top_p: float = Field(default=1.0, description="Top-p sampling")
    stream: bool = Field(default=False, description="Stream response")
    stop: Optional[List[str]] = Field(None, description="Stop sequences")
    n: int = Field(default=1, description="Number of completions")
    presence_penalty: float = Field(default=0.0, description="Presence penalty")
    frequency_penalty: float = Field(default=0.0, description="Frequency penalty")
    user: Optional[str] = Field(None, description="User identifier")

class EmbeddingRequest(BaseModel):
    model: str = Field(default="auto", description="Model name or 'auto'")
    input: List[str] = Field(..., description="Text to embed")
    encoding_format: str = Field(default="float", description="Encoding format")

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str
    permission: List[Dict] = []
    root: str
    parent: Optional[str] = None

# Provider Registry
class LLMProvider:
    """Base class for LLM providers."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.base_url = config.get('base_url', '')
        self.api_key = config.get('api_key', '')
        self.models = config.get('models', [])
        self.priority = config.get('priority', 100)
        self.max_requests_per_minute = config.get('max_rpm', 60)
        self.current_requests = 0
        self.last_reset = time.time()
        self.is_healthy = True
        self.last_health_check = datetime.now()
        
    async def check_health(self) -> bool:
        """Check provider health."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=5.0
                )
                self.is_healthy = response.status_code == 200
        except:
            self.is_healthy = False
        
        self.last_health_check = datetime.now()
        return self.is_healthy
    
    def can_handle_request(self) -> bool:
        """Check if provider can handle more requests."""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.last_reset > 60:
            self.current_requests = 0
            self.last_reset = current_time
        
        return self.current_requests < self.max_requests_per_minute and self.is_healthy
    
    async def make_request(self, endpoint: str, data: Dict[str, Any], stream: bool = False):
        """Make request to provider."""
        self.current_requests += 1
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            if stream:
                async with client.stream(
                    "POST",
                    f"{self.base_url}{endpoint}",
                    json=data,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            yield line
            else:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=data,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                yield response.json()

class ModelRouter:
    """Routes requests to appropriate providers."""
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.model_map: Dict[str, List[str]] = defaultdict(list)
        self.load_config()
        
    def load_config(self):
        """Load provider configuration."""
        config_path = os.getenv('GATEWAY_CONFIG', 'config/providers.yaml')
        
        # Default configuration if file doesn't exist
        default_config = {
            'providers': {
                'openrouter': {
                    'base_url': 'https://openrouter.ai/api/v1',
                    'api_key': os.getenv('OPENROUTER_API_KEY', ''),
                    'models': ['gpt-4', 'gpt-3.5-turbo', 'claude-3-opus', 'claude-3-sonnet'],
                    'priority': 1,
                    'max_rpm': 100
                },
                'local_mlx': {
                    'base_url': 'http://localhost:8001/v1',
                    'api_key': 'none',
                    'models': ['qwen3-8b-mlx'],
                    'priority': 2,
                    'max_rpm': 60
                },
                'ollama': {
                    'base_url': 'http://localhost:11434/api',
                    'api_key': 'none',
                    'models': ['qwen2.5:7b', 'llama3.2', 'mistral'],
                    'priority': 3,
                    'max_rpm': 30
                }
            },
            'routing_rules': {
                'default_model': 'gpt-3.5-turbo',
                'fallback_chain': ['openrouter', 'local_mlx', 'ollama'],
                'model_preferences': {
                    'fast': ['gpt-3.5-turbo', 'qwen2.5:7b'],
                    'quality': ['gpt-4', 'claude-3-opus'],
                    'local': ['qwen3-8b-mlx', 'qwen2.5:7b']
                }
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
            else:
                config = default_config
                
            # Initialize providers
            for name, provider_config in config.get('providers', {}).items():
                self.providers[name] = LLMProvider(name, provider_config)
                
                # Build model map
                for model in provider_config.get('models', []):
                    self.model_map[model].append(name)
                    
            self.routing_rules = config.get('routing_rules', default_config['routing_rules'])
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Use default config on error
            self.routing_rules = default_config['routing_rules']
    
    async def select_provider(self, model: str) -> Optional[LLMProvider]:
        """Select best available provider for model."""
        
        # Auto selection
        if model == "auto":
            model = self.routing_rules.get('default_model', 'gpt-3.5-turbo')
        
        # Get providers that support this model
        provider_names = self.model_map.get(model, [])
        
        # If no specific providers, use fallback chain
        if not provider_names:
            provider_names = self.routing_rules.get('fallback_chain', [])
        
        # Sort by priority and availability
        available_providers = []
        for name in provider_names:
            provider = self.providers.get(name)
            if provider and provider.can_handle_request():
                # Check health if not checked recently
                if datetime.now() - provider.last_health_check > timedelta(minutes=5):
                    await provider.check_health()
                
                if provider.is_healthy:
                    available_providers.append(provider)
        
        # Sort by priority (lower is better)
        available_providers.sort(key=lambda p: p.priority)
        
        return available_providers[0] if available_providers else None
    
    async def execute_with_fallback(self, request_data: Dict[str, Any], endpoint: str, stream: bool = False):
        """Execute request with automatic fallback."""
        model = request_data.get('model', 'auto')
        errors = []
        
        for attempt in range(MAX_RETRIES):
            provider = await self.select_provider(model)
            
            if not provider:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                continue
            
            try:
                # Record metrics
                active_connections.labels(provider=provider.name).inc()
                start_time = time.time()
                
                # Make request
                async for result in provider.make_request(endpoint, request_data, stream):
                    if stream:
                        yield result
                    else:
                        # Record success metrics
                        latency = time.time() - start_time
                        latency_histogram.labels(provider=provider.name, model=model).observe(latency)
                        request_counter.labels(provider=provider.name, model=model, status='success').inc()
                        
                        # Cache result if applicable
                        if not stream and cache_enabled:
                            cache_key = self._get_cache_key(request_data)
                            if redis_client:
                                redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
                            else:
                                memory_cache[cache_key] = result
                        
                        yield result
                        return
                
                # For streaming, record metrics after completion
                if stream:
                    latency = time.time() - start_time
                    latency_histogram.labels(provider=provider.name, model=model).observe(latency)
                    request_counter.labels(provider=provider.name, model=model, status='success').inc()
                
                active_connections.labels(provider=provider.name).dec()
                return
                
            except Exception as e:
                active_connections.labels(provider=provider.name).dec()
                error_counter.labels(provider=provider.name, error_type=type(e).__name__).inc()
                request_counter.labels(provider=provider.name, model=model, status='error').inc()
                
                errors.append(f"{provider.name}: {str(e)}")
                provider.is_healthy = False
                
                # Try next provider after delay
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        
        # All attempts failed
        raise HTTPException(
            status_code=503,
            detail=f"All providers failed. Errors: {'; '.join(errors)}"
        )
    
    def _get_cache_key(self, request_data: Dict[str, Any]) -> str:
        """Generate cache key for request."""
        # Create deterministic key from request
        key_data = json.dumps(request_data, sort_keys=True)
        return f"llm_gateway:{hashlib.md5(key_data.encode()).hexdigest()}"

# Initialize router
router = ModelRouter()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    healthy_providers = []
    unhealthy_providers = []
    
    for name, provider in router.providers.items():
        if provider.is_healthy:
            healthy_providers.append(name)
        else:
            unhealthy_providers.append(name)
    
    return {
        "status": "healthy" if healthy_providers else "unhealthy",
        "healthy_providers": healthy_providers,
        "unhealthy_providers": unhealthy_providers,
        "cache_enabled": cache_enabled
    }

@app.get("/v1/models")
async def list_models():
    """List available models."""
    models = []
    
    for model_name, provider_names in router.model_map.items():
        # Check if any provider is available
        available = any(
            router.providers.get(name, None) and router.providers[name].is_healthy
            for name in provider_names
        )
        
        if available:
            models.append(ModelInfo(
                id=model_name,
                created=int(time.time()),
                owned_by=provider_names[0] if provider_names else "unknown",
                root=model_name
            ))
    
    return {"data": models, "object": "list"}

@app.post("/v1/completions")
async def create_completion(request: CompletionRequest):
    """Create completion (OpenAI compatible)."""
    
    # Check cache first
    if not request.stream and cache_enabled:
        cache_key = router._get_cache_key(request.dict())
        
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return JSONResponse(json.loads(cached))
        elif cache_key in memory_cache:
            return JSONResponse(memory_cache[cache_key])
    
    # Prepare request data
    request_data = request.dict(exclude_none=True)
    
    # Route request
    if request.stream:
        async def stream_generator():
            async for line in router.execute_with_fallback(request_data, "/completions", stream=True):
                yield f"data: {line}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )
    else:
        result = None
        async for response in router.execute_with_fallback(request_data, "/completions"):
            result = response
        return JSONResponse(result)

@app.post("/v1/chat/completions")
async def create_chat_completion(request: CompletionRequest):
    """Create chat completion (OpenAI compatible)."""
    
    # Check cache first
    if not request.stream and cache_enabled:
        cache_key = router._get_cache_key(request.dict())
        
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return JSONResponse(json.loads(cached))
        elif cache_key in memory_cache:
            return JSONResponse(memory_cache[cache_key])
    
    # Prepare request data
    request_data = request.dict(exclude_none=True)
    
    # Route request
    if request.stream:
        async def stream_generator():
            async for line in router.execute_with_fallback(request_data, "/chat/completions", stream=True):
                yield f"data: {line}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )
    else:
        result = None
        async for response in router.execute_with_fallback(request_data, "/chat/completions"):
            result = response
        
        # Track token usage
        if result and 'usage' in result:
            usage = result['usage']
            model = request.model
            provider = next(iter(router.model_map.get(model, [])), 'unknown')
            
            token_counter.labels(provider=provider, model=model, type='prompt').inc(
                usage.get('prompt_tokens', 0)
            )
            token_counter.labels(provider=provider, model=model, type='completion').inc(
                usage.get('completion_tokens', 0)
            )
        
        return JSONResponse(result)

@app.post("/v1/embeddings")
async def create_embedding(request: EmbeddingRequest):
    """Create embeddings."""
    
    # Check cache
    if cache_enabled:
        cache_key = router._get_cache_key(request.dict())
        
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return JSONResponse(json.loads(cached))
        elif cache_key in memory_cache:
            return JSONResponse(memory_cache[cache_key])
    
    # Prepare request data
    request_data = request.dict(exclude_none=True)
    
    # Route request
    result = None
    async for response in router.execute_with_fallback(request_data, "/embeddings"):
        result = response
    
    return JSONResponse(result)

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/admin/reload")
async def reload_config():
    """Reload configuration."""
    try:
        router.load_config()
        return {"status": "success", "message": "Configuration reloaded"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/admin/health-check")
async def force_health_check():
    """Force health check on all providers."""
    results = {}
    
    for name, provider in router.providers.items():
        health = await provider.check_health()
        results[name] = {
            "healthy": health,
            "last_check": provider.last_health_check.isoformat()
        }
    
    return results

# Background tasks
@app.on_event("startup")
async def startup_event():
    """Run on startup."""
    logger.info("LLM Gateway starting up...")
    
    # Initial health check
    for provider in router.providers.values():
        await provider.check_health()
    
    logger.info(f"Loaded {len(router.providers)} providers")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on shutdown."""
    logger.info("LLM Gateway shutting down...")
    
    # Close Redis connection
    if redis_client:
        redis_client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)