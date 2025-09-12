# Unified LLM Service Migration Guide

## Overview
The enhanced Unified LLM Service (`llm_service_enhanced.py`) provides a robust, production-ready LLM abstraction layer with multiple provider support, automatic failover, caching, and comprehensive monitoring.

## Key Features

### 1. Multiple Provider Support
- **OpenRouter**: Access to 100+ models via unified API
- **Local MLX**: Apple Silicon optimized local models
- **LM Studio**: Local model serving with various backends
- **Extensible**: Easy to add new providers

### 2. Automatic Failover & Retry
- Configurable retry logic with exponential backoff
- Automatic failover to backup providers
- Graceful degradation on provider failures

### 3. Intelligent Caching
- Memory-based LRU cache
- Redis-based distributed cache
- Configurable TTL and cache strategies

### 4. Cost Tracking
- Per-provider cost tracking
- Token usage monitoring
- Cost estimation based on model pricing

### 5. Comprehensive Metrics
- Request/response times
- Error rates
- Token usage statistics
- Provider health monitoring

## Migration Steps

### 1. Update Environment Variables

```bash
# Provider Configuration
LLM_PROVIDER=auto  # auto | openrouter | local_mlx | lmstudio

# OpenRouter Configuration
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=meta-llama/llama-3-8b-instruct
SITE_URL=https://drass.ai
SITE_NAME=Drass Compliance Assistant

# Local MLX Configuration  
LLM_BASE_URL=http://localhost:8001/v1
LLM_MODEL=qwen3-8b-mlx

# LM Studio Configuration
LMSTUDIO_ENABLED=false
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_MODEL=local-model

# Caching Configuration
LLM_CACHE_STRATEGY=memory  # none | memory | redis
REDIS_URL=redis://localhost:6379
```

### 2. Update Import Statements

Replace old imports:
```python
# OLD
from app.services.llm_service import llm_service

# NEW
from app.services.llm_service_enhanced import unified_llm_service
```

### 3. Update Service Calls

The new service maintains backward compatibility while adding new features:

```python
# Basic generation (backward compatible)
response = await unified_llm_service.generate(
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=1000,
    temperature=0.7
)

# With provider selection
response = await unified_llm_service.generate(
    messages=[{"role": "user", "content": "Hello"}],
    provider="openrouter"  # Force specific provider
)

# Without caching (for dynamic content)
response = await unified_llm_service.generate(
    messages=[{"role": "user", "content": "Current time?"}],
    use_cache=False
)

# Streaming generation
async for chunk in unified_llm_service.stream_generate(messages):
    print(chunk, end="")
```

### 4. Access New Features

```python
# Get comprehensive statistics
stats = await unified_llm_service.get_stats()
print(f"Total cost: ${stats['total_cost']}")
print(f"Provider metrics: {stats['providers']}")

# Health check all providers
health = await unified_llm_service.health_check()
if health['status'] == 'degraded':
    logger.warning("Some LLM providers are unhealthy")

# Count tokens
token_count = unified_llm_service.count_tokens("Your text here")

# Clear cache
await unified_llm_service.clear_cache()
```

## Testing

### Unit Tests
```bash
cd services/main-app
pytest app/services/tests/test_llm_service.py -v
```

### Integration Tests
```bash
# Start local MLX server
python qwen3_api_server.py &

# Run integration tests
pytest app/services/tests/test_llm_service.py::TestProviderIntegration -v
```

### Performance Testing
```python
import asyncio
import time

async def performance_test():
    start = time.time()
    tasks = []
    
    # Test concurrent requests
    for i in range(10):
        task = unified_llm_service.generate(
            f"Test message {i}",
            use_cache=True
        )
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    print(f"Processed {len(responses)} requests in {elapsed:.2f}s")
    print(f"Average: {elapsed/len(responses):.3f}s per request")
```

## Monitoring & Debugging

### Enable Debug Logging
```python
import logging
logging.getLogger("app.services.llm_service_enhanced").setLevel(logging.DEBUG)
```

### Monitor Provider Health
```python
# Periodic health check
async def monitor_health():
    while True:
        health = await unified_llm_service.health_check()
        for provider, status in health['providers'].items():
            if status['status'] != 'healthy':
                logger.error(f"Provider {provider} is {status['status']}")
        await asyncio.sleep(60)  # Check every minute
```

### Track Costs
```python
# Cost tracking endpoint
@app.get("/api/v1/llm/costs")
async def get_llm_costs():
    stats = await unified_llm_service.get_stats()
    return {
        "total_cost": stats['total_cost'],
        "by_provider": stats['cost_by_provider']
    }
```

## Troubleshooting

### Provider Not Available
```python
# Check provider initialization
health = await unified_llm_service.health_check()
if "local_mlx" not in health['providers']:
    logger.error("Local MLX provider not initialized")
```

### Cache Issues
```python
# Clear cache if stale responses
await unified_llm_service.clear_cache()

# Disable cache for testing
response = await unified_llm_service.generate(
    messages,
    use_cache=False
)
```

### Failover Not Working
```python
# Check failover configuration
stats = await unified_llm_service.get_stats()
print(f"Primary: {stats['primary_provider']}")
print(f"Fallbacks: {stats['fallback_providers']}")
```

## Best Practices

1. **Use caching for static prompts**: Enable caching for prompts that don't change frequently
2. **Monitor costs**: Regularly check cost metrics, especially when using cloud providers
3. **Set appropriate timeouts**: Configure timeouts based on model size and complexity
4. **Implement graceful degradation**: Handle provider failures gracefully in your application
5. **Regular health checks**: Monitor provider health and switch providers if needed

## Provider-Specific Notes

### OpenRouter
- Requires API key from https://openrouter.ai
- Supports 100+ models with unified pricing
- Best for production workloads with model variety

### Local MLX
- Optimized for Apple Silicon (M1/M2/M3)
- No API costs, runs locally
- Best for development and privacy-sensitive applications

### LM Studio
- Supports various model formats (GGUF, GGML, etc.)
- GUI for model management
- Best for experimenting with different models

## Future Enhancements

- [ ] Add support for Anthropic Claude API
- [ ] Implement request queuing for rate limiting
- [ ] Add support for function calling
- [ ] Implement model-specific optimizations
- [ ] Add support for batch processing
- [ ] Implement cost budgets and alerts