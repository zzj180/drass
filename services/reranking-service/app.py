"""
FastAPI Reranking Service with Enhanced Architecture
Implements async/await, multi-provider support, graceful degradation, and monitoring
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import asyncio
import logging
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response
import json

from config import settings, RerankingProvider
from providers.provider_factory import ProviderFactory
from cache.cache_manager import CacheManager
from models.health import HealthResponse, ModelInfoResponse
from models.requests import RerankRequest, RerankResponse, BatchRerankRequest

# Configure structured logging
def setup_logging():
    """Configure structured JSON logging"""
    if settings.LOG_FORMAT == "json":
        import structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        return structlog.get_logger()
    else:
        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

logger = setup_logging()

# Prometheus metrics
if settings.ENABLE_METRICS:
    rerank_requests = Counter(
        'rerank_requests_total',
        'Total number of rerank requests',
        ['status', 'provider']
    )
    rerank_duration = Histogram(
        'rerank_duration_seconds',
        'Time spent processing rerank requests',
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
    )
    documents_processed = Counter(
        'documents_processed_total',
        'Total number of documents processed'
    )
    model_load_time = Gauge(
        'model_load_time_seconds',
        'Time taken to load the model'
    )
    cache_hit_rate = Gauge(
        'cache_hit_rate',
        'Cache hit rate percentage'
    )
    active_requests = Gauge(
        'active_requests',
        'Number of active requests being processed'
    )
    fallback_triggers = Counter(
        'fallback_triggers_total',
        'Number of times fallback was triggered'
    )

# Global components
reranking_provider = None
cache_manager = None
provider_factory = None
is_fallback_active = False
current_model_name = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle with proper initialization and cleanup
    """
    global reranking_provider, cache_manager, provider_factory
    global is_fallback_active, current_model_name

    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME}",
               provider=settings.RERANKING_PROVIDER,
               model=settings.MODEL_NAME)

    start_time = time.time()

    try:
        # Initialize cache manager
        logger.info("Initializing cache manager")
        cache_manager = CacheManager(
            cache_type=settings.CACHE_TYPE,
            cache_size=settings.CACHE_SIZE,
            ttl=settings.CACHE_TTL,
            redis_url=settings.REDIS_URL
        )
        await cache_manager.initialize()

        # Initialize provider factory
        provider_factory = ProviderFactory()

        # Try to load primary model
        try:
            logger.info(f"Loading primary model: {settings.MODEL_NAME}")
            reranking_provider = await provider_factory.create_provider(
                provider_type=settings.RERANKING_PROVIDER,
                model_name=settings.MODEL_NAME,
                device=settings.DEVICE
            )
            current_model_name = settings.MODEL_NAME
            is_fallback_active = False

        except Exception as e:
            logger.error(f"Failed to load primary model: {e}")

            if settings.FALLBACK_ENABLED:
                # Try fallback models
                logger.info("Attempting to load fallback models")
                for fallback_model in settings.FALLBACK_MODELS:
                    try:
                        logger.info(f"Trying fallback model: {fallback_model}")
                        reranking_provider = await provider_factory.create_provider(
                            provider_type=RerankingProvider.SENTENCE_TRANSFORMERS,
                            model_name=fallback_model,
                            device=settings.DEVICE
                        )
                        current_model_name = fallback_model
                        is_fallback_active = True

                        if settings.ENABLE_METRICS:
                            fallback_triggers.inc()

                        logger.warning(f"Using fallback model: {fallback_model}")
                        break

                    except Exception as fallback_error:
                        logger.error(f"Fallback model {fallback_model} failed: {fallback_error}")
                        continue

                if not reranking_provider:
                    raise RuntimeError("All models failed to load")
            else:
                raise

        load_time = time.time() - start_time

        if settings.ENABLE_METRICS:
            model_load_time.set(load_time)

        logger.info(f"Service initialized successfully in {load_time:.2f} seconds",
                   model=current_model_name,
                   is_fallback=is_fallback_active)

    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        logger.warning("Service will start in degraded mode")
        # Service continues without reranking capabilities

    yield

    # Shutdown
    logger.info("Shutting down service")

    if cache_manager:
        await cache_manager.close()

    if reranking_provider:
        await reranking_provider.close()

# Create FastAPI app
app = FastAPI(
    title=settings.SERVICE_NAME,
    description="High-performance document reranking service with multi-provider support",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request tracking middleware
@app.middleware("http")
async def track_requests(request, call_next):
    """Track active requests for monitoring"""
    if settings.ENABLE_METRICS:
        active_requests.inc()

    try:
        response = await call_next(request)
        return response
    finally:
        if settings.ENABLE_METRICS:
            active_requests.dec()

@app.post("/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest):
    """
    Rerank documents based on relevance to query

    Uses the configured provider (sentence-transformers, openai, cohere)
    with automatic caching and fallback support.
    """
    if not reranking_provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reranking service is not available"
        )

    start_time = time.time()

    try:
        # Check cache first
        cache_key = cache_manager.generate_key(request.query, request.documents)
        cached_result = await cache_manager.get(cache_key)

        if cached_result:
            logger.debug("Cache hit", query=request.query[:50])
            if settings.ENABLE_METRICS:
                cache_hit_rate.inc()

            processing_time = (time.time() - start_time) * 1000
            return RerankResponse(
                reranked_documents=cached_result["documents"],
                scores=cached_result["scores"],
                indices=cached_result["indices"],
                processing_time_ms=processing_time,
                model_used=current_model_name,
                is_cached=True
            )

        # Perform reranking
        logger.debug(f"Reranking {len(request.documents)} documents")

        result = await reranking_provider.rerank(
            query=request.query,
            documents=request.documents,
            top_k=request.top_k,
            normalize_scores=request.normalize_scores
        )

        # Cache the result
        await cache_manager.set(cache_key, {
            "documents": result["documents"],
            "scores": result["scores"],
            "indices": result["indices"]
        })

        processing_time = (time.time() - start_time) * 1000

        # Update metrics
        if settings.ENABLE_METRICS:
            rerank_requests.labels(
                status='success',
                provider=settings.RERANKING_PROVIDER
            ).inc()
            rerank_duration.observe(processing_time / 1000)
            documents_processed.inc(len(request.documents))

        return RerankResponse(
            reranked_documents=result["documents"],
            scores=result["scores"],
            indices=result["indices"],
            processing_time_ms=processing_time,
            model_used=current_model_name,
            is_cached=False
        )

    except Exception as e:
        if settings.ENABLE_METRICS:
            rerank_requests.labels(
                status='error',
                provider=settings.RERANKING_PROVIDER
            ).inc()

        logger.error(f"Reranking failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reranking failed: {str(e)}"
        )

@app.post("/batch_rerank")
async def batch_rerank_documents(request: BatchRerankRequest):
    """
    Rerank multiple queries with their respective documents

    Processes multiple query-documents pairs efficiently with batching
    and parallel processing where possible.
    """
    if not reranking_provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reranking service is not available"
        )

    start_time = time.time()

    try:
        # Process in parallel if provider supports it
        tasks = []
        for query, documents in zip(request.queries, request.documents_list):
            task = reranking_provider.rerank(
                query=query,
                documents=documents,
                top_k=request.top_k,
                normalize_scores=request.normalize_scores
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        processing_time = (time.time() - start_time) * 1000

        # Update metrics
        if settings.ENABLE_METRICS:
            rerank_requests.labels(
                status='success',
                provider=settings.RERANKING_PROVIDER
            ).inc(len(request.queries))

            total_docs = sum(len(docs) for docs in request.documents_list)
            documents_processed.inc(total_docs)

        return {
            "results": results,
            "processing_time_ms": processing_time,
            "queries_processed": len(request.queries),
            "model_used": current_model_name
        }

    except Exception as e:
        if settings.ENABLE_METRICS:
            rerank_requests.labels(
                status='error',
                provider=settings.RERANKING_PROVIDER
            ).inc()

        logger.error(f"Batch reranking failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch reranking failed: {str(e)}"
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint with detailed status information
    """
    health_status = {
        "status": "healthy" if reranking_provider else "degraded",
        "model_loaded": reranking_provider is not None,
        "model_name": current_model_name,
        "provider": settings.RERANKING_PROVIDER,
        "fallback_enabled": settings.FALLBACK_ENABLED,
        "is_fallback_active": is_fallback_active,
        "cache_enabled": cache_manager is not None,
        "cache_type": settings.CACHE_TYPE if cache_manager else None
    }

    # Add cache statistics if available
    if cache_manager:
        cache_stats = await cache_manager.get_stats()
        health_status.update({
            "cache_hits": cache_stats.get("hits", 0),
            "cache_misses": cache_stats.get("misses", 0),
            "cache_size": cache_stats.get("size", 0),
            "cache_hit_rate": cache_stats.get("hit_rate", 0.0)
        })

    # Add provider-specific info
    if reranking_provider:
        provider_info = await reranking_provider.get_info()
        health_status["provider_info"] = provider_info

    # Set appropriate status code
    if not reranking_provider:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )

    return health_status

@app.get("/models")
async def get_models():
    """
    Get information about available models and providers
    """
    if not provider_factory:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider factory not initialized"
        )

    return {
        "current_provider": settings.RERANKING_PROVIDER,
        "current_model": current_model_name,
        "is_fallback": is_fallback_active,
        "available_providers": provider_factory.get_available_providers(),
        "fallback_models": settings.FALLBACK_MODELS,
        "supported_devices": ["cpu", "cuda", "mps"]
    }

@app.post("/clear_cache")
async def clear_cache():
    """
    Clear the reranking cache
    """
    if not cache_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache manager not initialized"
        )

    await cache_manager.clear()

    return {
        "status": "success",
        "message": "Cache cleared successfully"
    }

@app.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint
    """
    if settings.ENABLE_METRICS:
        return Response(
            content=generate_latest(),
            media_type="text/plain"
        )
    else:
        return {"message": "Metrics disabled"}

@app.get("/")
async def root():
    """
    Root endpoint with service information
    """
    return {
        "service": settings.SERVICE_NAME,
        "version": "2.0.0",
        "status": "running" if reranking_provider else "degraded",
        "provider": settings.RERANKING_PROVIDER,
        "model": current_model_name,
        "is_fallback": is_fallback_active,
        "endpoints": {
            "rerank": "/rerank",
            "batch_rerank": "/batch_rerank",
            "health": "/health",
            "models": "/models",
            "metrics": "/metrics",
            "clear_cache": "/clear_cache",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn

    # Direct startup without complex scripts
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )