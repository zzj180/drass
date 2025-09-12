"""
FastAPI Reranking Service

Provides document reranking capabilities using cross-encoder models
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import logging
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response

from config import settings
from models.reranker import Reranker
from models.model_loader import ModelLoader

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
if settings.ENABLE_METRICS:
    rerank_requests = Counter(
        'rerank_requests_total',
        'Total number of rerank requests',
        ['status']
    )
    rerank_duration = Histogram(
        'rerank_duration_seconds',
        'Time spent processing rerank requests'
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

# Request/Response models
class RerankRequest(BaseModel):
    """Request model for reranking documents"""
    query: str = Field(..., description="The search query", min_length=1)
    documents: List[str] = Field(
        ...,
        description="List of documents to rerank",
        min_items=1,
        max_items=100
    )
    top_k: Optional[int] = Field(
        default=10,
        description="Number of top documents to return",
        ge=1,
        le=100
    )
    normalize_scores: bool = Field(
        default=False,
        description="Whether to normalize scores to [0, 1]"
    )
    
    @validator('documents')
    def validate_documents(cls, v):
        if len(v) > settings.MAX_DOCUMENTS:
            raise ValueError(f"Maximum {settings.MAX_DOCUMENTS} documents allowed")
        # Check for empty documents
        if any(not doc.strip() for doc in v):
            raise ValueError("Documents cannot be empty")
        return v

class RerankResponse(BaseModel):
    """Response model for reranked documents"""
    reranked_documents: List[str] = Field(
        ...,
        description="Documents ordered by relevance"
    )
    scores: List[float] = Field(
        ...,
        description="Relevance scores for each document"
    )
    indices: List[int] = Field(
        ...,
        description="Original indices of reranked documents"
    )
    processing_time_ms: float = Field(
        ...,
        description="Time taken to process the request in milliseconds"
    )

class BatchRerankRequest(BaseModel):
    """Request model for batch reranking"""
    queries: List[str] = Field(
        ...,
        description="List of queries",
        min_items=1,
        max_items=10
    )
    documents_list: List[List[str]] = Field(
        ...,
        description="List of document lists (one per query)",
        min_items=1,
        max_items=10
    )
    top_k: Optional[int] = Field(
        default=10,
        description="Number of top documents to return per query",
        ge=1,
        le=100
    )
    
    @validator('documents_list')
    def validate_batch_size(cls, v, values):
        if 'queries' in values and len(v) != len(values['queries']):
            raise ValueError("Number of document lists must match number of queries")
        return v

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model: str
    device: str
    cache_hits: int
    cache_misses: int
    cache_size: int

class ModelInfoResponse(BaseModel):
    """Model information response"""
    available_models: Dict[str, Dict[str, Any]]
    loaded_models: List[str]
    current_model: str
    device: str

# Global variables
reranker: Optional[Reranker] = None
model_loader: Optional[ModelLoader] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    """
    global reranker, model_loader
    
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME}")
    start_time = time.time()
    
    try:
        # Initialize model loader
        model_loader = ModelLoader(cache_dir=settings.MODEL_CACHE_DIR)
        
        # Initialize reranker
        reranker = Reranker(
            model_name=settings.MODEL_NAME,
            device=settings.DEVICE,
            max_length=settings.MAX_LENGTH,
            cache_dir=settings.MODEL_CACHE_DIR
        )
        
        load_time = time.time() - start_time
        if settings.ENABLE_METRICS:
            model_load_time.set(load_time)
        
        logger.info(f"Model loaded in {load_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Failed to initialize service: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down service")
    if reranker:
        reranker.clear_cache()

# Create FastAPI app
app = FastAPI(
    title=settings.SERVICE_NAME,
    description="Document reranking service using cross-encoder models",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest):
    """
    Rerank documents based on relevance to query
    
    Returns documents ordered by relevance with their scores
    """
    if not reranker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reranker not initialized"
        )
    
    start_time = time.time()
    
    try:
        # Perform reranking
        reranked_docs, scores, indices = reranker.rerank(
            query=request.query,
            documents=request.documents,
            top_k=request.top_k,
            batch_size=settings.BATCH_SIZE
        )
        
        # Normalize scores if requested
        if request.normalize_scores:
            import numpy as np
            scores = (1 / (1 + np.exp(-np.array(scores)))).tolist()
        
        processing_time = (time.time() - start_time) * 1000
        
        # Update metrics
        if settings.ENABLE_METRICS:
            rerank_requests.labels(status='success').inc()
            rerank_duration.observe(processing_time / 1000)
            documents_processed.inc(len(request.documents))
            
            # Update cache hit rate
            total_requests = reranker.cache_hits + reranker.cache_misses
            if total_requests > 0:
                hit_rate = (reranker.cache_hits / total_requests) * 100
                cache_hit_rate.set(hit_rate)
        
        return RerankResponse(
            reranked_documents=reranked_docs,
            scores=scores,
            indices=indices,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        if settings.ENABLE_METRICS:
            rerank_requests.labels(status='error').inc()
        logger.error(f"Reranking failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reranking failed: {str(e)}"
        )

@app.post("/batch_rerank")
async def batch_rerank_documents(request: BatchRerankRequest):
    """
    Rerank multiple queries with their respective documents
    
    Processes multiple query-documents pairs in a single request
    """
    if not reranker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reranker not initialized"
        )
    
    start_time = time.time()
    
    try:
        results = reranker.batch_rerank(
            queries=request.queries,
            documents_list=request.documents_list,
            top_k=request.top_k,
            batch_size=settings.BATCH_SIZE
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Format response
        batch_results = []
        for docs, scores, indices in results:
            batch_results.append({
                "reranked_documents": docs,
                "scores": scores,
                "indices": indices
            })
        
        # Update metrics
        if settings.ENABLE_METRICS:
            rerank_requests.labels(status='success').inc(len(request.queries))
            total_docs = sum(len(docs) for docs in request.documents_list)
            documents_processed.inc(total_docs)
        
        return {
            "results": batch_results,
            "processing_time_ms": processing_time,
            "queries_processed": len(request.queries)
        }
        
    except Exception as e:
        if settings.ENABLE_METRICS:
            rerank_requests.labels(status='error').inc()
        logger.error(f"Batch reranking failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch reranking failed: {str(e)}"
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns service health status and metrics
    """
    if not reranker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    
    model_info = reranker.get_model_info()
    
    return HealthResponse(
        status="healthy",
        model=model_info["model_name"],
        device=model_info["device"],
        cache_hits=model_info["cache_hits"],
        cache_misses=model_info["cache_misses"],
        cache_size=model_info["cache_size"]
    )

@app.get("/models", response_model=ModelInfoResponse)
async def get_model_info():
    """
    Get information about available and loaded models
    """
    if not model_loader or not reranker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    
    return ModelInfoResponse(
        available_models=model_loader.list_available_models(),
        loaded_models=model_loader.get_loaded_models(),
        current_model=reranker.model_name,
        device=reranker.device
    )

@app.post("/clear_cache")
async def clear_cache():
    """
    Clear the reranker cache
    
    Removes all cached scores from memory
    """
    if not reranker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reranker not initialized"
        )
    
    reranker.clear_cache()
    
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
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "rerank": "/rerank",
            "batch_rerank": "/batch_rerank",
            "health": "/health",
            "models": "/models",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="debug" if settings.DEBUG else "info"
    )