"""
Enhanced Embedding Service with caching and batch processing
"""

import os
import time
import asyncio
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
from dotenv import load_dotenv
import logging

# Import cache implementations
from cache.redis_cache import RedisEmbeddingCache
from cache.lru_cache import LRUEmbeddingCache
from batch_processor import create_batch_processor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
embedding_model = None
cache_service = None
batch_processor = None


class EmbeddingRequest(BaseModel):
    """Request model for embedding generation"""
    texts: List[str] = Field(..., description="List of texts to embed")
    model: Optional[str] = Field(None, description="Specific model to use")
    use_cache: bool = Field(default=True, description="Whether to use cache")
    batch_process: bool = Field(default=False, description="Use batch processing")


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation"""
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    model: str = Field(..., description="Model used for embedding")
    usage: Dict[str, Any] = Field(..., description="Usage statistics")
    cached: List[bool] = Field(default_factory=list, description="Which embeddings were cached")


class BatchEmbeddingRequest(BaseModel):
    """Batch embedding request"""
    batches: List[EmbeddingRequest] = Field(..., description="List of embedding requests")
    parallel: bool = Field(default=True, description="Process batches in parallel")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    model_loaded: bool = False
    model_name: Optional[str] = None
    cache_enabled: bool = False
    batch_processor_enabled: bool = False
    stats: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingModel:
    """Enhanced embedding model with caching support"""
    
    def __init__(self):
        self.provider = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
        self.model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
        self.model = None
        self.dimension = None
        
    async def initialize(self):
        """Initialize the embedding model based on provider"""
        if self.provider == "sentence-transformers":
            await self._init_sentence_transformers()
        elif self.provider == "openai":
            await self._init_openai()
        elif self.provider == "cohere":
            await self._init_cohere()
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")
            
    async def _init_sentence_transformers(self):
        """Initialize Sentence Transformers model"""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading Sentence Transformers model: {self.model_name}")
            
            # Use cache directory
            cache_dir = os.getenv("MODEL_CACHE_DIR", "./models")
            os.makedirs(cache_dir, exist_ok=True)
            
            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=cache_dir
            )
            
            # Enable multi-process for better performance
            if hasattr(self.model, 'max_seq_length'):
                self.model.max_seq_length = 512
            
            # Get embedding dimension
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded with dimension: {self.dimension}")
            
        except ImportError:
            raise ImportError("Please install sentence-transformers: pip install sentence-transformers")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
            
    async def _init_openai(self):
        """Initialize OpenAI embedding model"""
        try:
            from openai import AsyncOpenAI
            
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("EMBEDDING_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found in environment")
                
            self.model = AsyncOpenAI(api_key=api_key)
            
            # Set dimension based on model
            if "text-embedding-3" in self.model_name:
                self.dimension = 1536  # Default for text-embedding-3-small
            else:
                self.dimension = 1536  # Default for ada-002
                
            logger.info(f"OpenAI embedding initialized with model: {self.model_name}")
            
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
            
    async def _init_cohere(self):
        """Initialize Cohere embedding model"""
        try:
            import cohere
            
            api_key = os.getenv("COHERE_API_KEY") or os.getenv("EMBEDDING_API_KEY")
            if not api_key:
                raise ValueError("Cohere API key not found in environment")
                
            self.model = cohere.AsyncClient(api_key)
            self.dimension = 1024  # Cohere embed dimension
            
            logger.info(f"Cohere embedding initialized with model: {self.model_name}")
            
        except ImportError:
            raise ImportError("Please install cohere: pip install cohere")
            
    async def embed_texts(
        self,
        texts: List[str],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Generate embeddings with cache support"""
        start_time = time.time()
        
        # Check cache first
        cached_embeddings = {}
        texts_to_process = []
        text_indices = []
        
        if use_cache and cache_service:
            cached_embeddings = await cache_service.get_batch(texts, self.model_name)
            
            for i, text in enumerate(texts):
                if i not in cached_embeddings:
                    texts_to_process.append(text)
                    text_indices.append(i)
        else:
            texts_to_process = texts
            text_indices = list(range(len(texts)))
        
        # Process uncached texts
        new_embeddings = []
        if texts_to_process:
            if self.provider == "sentence-transformers":
                # Batch processing for sentence transformers
                embeddings = self.model.encode(
                    texts_to_process,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                    batch_size=min(32, len(texts_to_process))
                )
                new_embeddings = embeddings.tolist()
                
            elif self.provider == "openai":
                # Async processing for OpenAI
                response = await self.model.embeddings.create(
                    model=self.model_name,
                    input=texts_to_process
                )
                new_embeddings = [item.embedding for item in response.data]
                
            elif self.provider == "cohere":
                # Async processing for Cohere
                response = await self.model.embed(
                    texts=texts_to_process,
                    model=self.model_name
                )
                new_embeddings = response.embeddings
            
            # Cache new embeddings
            if use_cache and cache_service and new_embeddings:
                await cache_service.set_batch(texts_to_process, self.model_name, new_embeddings)
        
        # Combine cached and new embeddings in correct order
        final_embeddings = []
        cached_flags = []
        new_idx = 0
        
        for i in range(len(texts)):
            if i in cached_embeddings:
                final_embeddings.append(cached_embeddings[i])
                cached_flags.append(True)
            else:
                final_embeddings.append(new_embeddings[new_idx])
                cached_flags.append(False)
                new_idx += 1
        
        elapsed_time = time.time() - start_time
        
        return {
            "embeddings": final_embeddings,
            "model": self.model_name,
            "cached": cached_flags,
            "usage": {
                "texts_count": len(texts),
                "cached_count": len(cached_embeddings),
                "processed_count": len(texts_to_process),
                "total_tokens": sum(len(text.split()) for text in texts),  # Approximate
                "elapsed_time": elapsed_time,
                "dimension": self.dimension,
                "cache_hit_rate": len(cached_embeddings) / len(texts) if texts else 0
            }
        }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global embedding_model, cache_service, batch_processor
    
    # Initialize embedding model
    logger.info("Initializing embedding model...")
    embedding_model = EmbeddingModel()
    await embedding_model.initialize()
    logger.info(f"Model {embedding_model.model_name} loaded successfully")
    
    # Initialize cache
    cache_type = os.getenv("CACHE_TYPE", "lru")  # lru or redis
    
    if cache_type == "redis":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        cache_ttl = int(os.getenv("CACHE_TTL", 3600))
        cache_service = RedisEmbeddingCache(redis_url, cache_ttl)
        await cache_service.initialize()
    else:
        cache_size = int(os.getenv("CACHE_SIZE", 1000))
        cache_ttl = int(os.getenv("CACHE_TTL", 3600))
        cache_service = LRUEmbeddingCache(cache_size, cache_ttl)
    
    logger.info(f"Cache service initialized: {cache_type}")
    
    # Initialize batch processor
    batch_processor_type = os.getenv("BATCH_PROCESSOR", "static")
    if batch_processor_type == "dynamic":
        batch_processor = create_batch_processor(
            processor_type="dynamic",
            min_batch_size=int(os.getenv("MIN_BATCH_SIZE", 8)),
            max_batch_size=int(os.getenv("MAX_BATCH_SIZE", 64)),
            target_latency=float(os.getenv("TARGET_LATENCY", 0.5))
        )
    else:
        batch_processor = create_batch_processor(
            processor_type="static",
            batch_size=int(os.getenv("BATCH_SIZE", 32)),
            max_wait_time=float(os.getenv("MAX_WAIT_TIME", 0.1))
        )
    
    await batch_processor.start()
    logger.info(f"Batch processor started: {batch_processor_type}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down embedding service...")
    await batch_processor.stop()
    
    if hasattr(cache_service, 'close'):
        await cache_service.close()


# Create FastAPI app
app = FastAPI(
    title="Enhanced Embedding Service",
    description="Text embedding service with caching and batch processing",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    stats = {}
    
    if cache_service:
        if hasattr(cache_service, 'get_stats'):
            stats["cache"] = await cache_service.get_stats() if asyncio.iscoroutinefunction(cache_service.get_stats) else cache_service.get_stats()
    
    if batch_processor:
        stats["batch_processor"] = batch_processor.get_stats()
    
    return HealthResponse(
        status="healthy",
        model_loaded=embedding_model is not None,
        model_name=embedding_model.model_name if embedding_model else None,
        cache_enabled=cache_service is not None,
        batch_processor_enabled=batch_processor is not None,
        stats=stats
    )


@app.post("/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest):
    """Generate embeddings for input texts"""
    if not embedding_model:
        raise HTTPException(status_code=503, detail="Model not initialized")
        
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")
        
    if len(request.texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts per request")
    
    try:
        if request.batch_process and batch_processor:
            # Use batch processor
            request_id = str(uuid.uuid4())
            future = await batch_processor.add_request(request.texts, request_id)
            result = await future
        else:
            # Direct processing
            result = await embedding_model.embed_texts(
                request.texts,
                use_cache=request.use_cache
            )
        
        return EmbeddingResponse(**result)
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embeddings/batch")
async def create_batch_embeddings(request: BatchEmbeddingRequest):
    """Batch processing for multiple embedding requests"""
    if not embedding_model:
        raise HTTPException(status_code=503, detail="Model not initialized")
    
    results = []
    
    if request.parallel:
        # Process batches in parallel
        tasks = []
        for batch_request in request.batches:
            task = embedding_model.embed_texts(
                batch_request.texts,
                use_cache=batch_request.use_cache
            )
            tasks.append(task)
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in batch_results:
            if isinstance(result, Exception):
                results.append({"error": str(result)})
            else:
                results.append(result)
    else:
        # Process batches sequentially
        for batch_request in request.batches:
            try:
                result = await embedding_model.embed_texts(
                    batch_request.texts,
                    use_cache=batch_request.use_cache
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                results.append({"error": str(e)})
    
    return {"results": results}


@app.post("/cache/clear")
async def clear_cache(pattern: Optional[str] = None):
    """Clear cache entries"""
    if not cache_service:
        raise HTTPException(status_code=400, detail="Cache not enabled")
    
    if hasattr(cache_service, 'clear_cache'):
        if asyncio.iscoroutinefunction(cache_service.clear_cache):
            await cache_service.clear_cache(pattern)
        else:
            cache_service.clear_cache()
    
    return {"message": "Cache cleared successfully"}


@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    if not cache_service:
        raise HTTPException(status_code=400, detail="Cache not enabled")
    
    if hasattr(cache_service, 'get_stats'):
        stats = await cache_service.get_stats() if asyncio.iscoroutinefunction(cache_service.get_stats) else cache_service.get_stats()
        return stats
    
    return {"message": "Cache statistics not available"}


@app.get("/models")
async def list_models():
    """List available embedding models"""
    models = {
        "sentence-transformers": [
            "BAAI/bge-large-zh-v1.5",
            "BAAI/bge-large-en-v1.5",
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2",
            "intfloat/multilingual-e5-large"
        ],
        "openai": [
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002"
        ],
        "cohere": [
            "embed-english-v3.0",
            "embed-multilingual-v3.0",
            "embed-english-light-v3.0"
        ]
    }
    
    current_model = {
        "provider": embedding_model.provider if embedding_model else None,
        "model": embedding_model.model_name if embedding_model else None,
        "dimension": embedding_model.dimension if embedding_model else None
    }
    
    return {
        "current": current_model,
        "available": models
    }


@app.get("/batch/stats")
async def get_batch_stats():
    """Get batch processor statistics"""
    if not batch_processor:
        raise HTTPException(status_code=400, detail="Batch processor not enabled")
    
    return batch_processor.get_stats()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("EMBEDDING_SERVICE_PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)