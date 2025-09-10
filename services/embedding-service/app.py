"""
Embedding Service for Drass LangChain Compliance Assistant
Provides text embedding functionality using various models
"""

import os
import time
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model cache
embedding_model = None
model_lock = None

class EmbeddingRequest(BaseModel):
    """Request model for embedding generation"""
    texts: List[str] = Field(..., description="List of texts to embed")
    model: Optional[str] = Field(None, description="Specific model to use")
    
class EmbeddingResponse(BaseModel):
    """Response model for embedding generation"""
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    model: str = Field(..., description="Model used for embedding")
    usage: Dict[str, Any] = Field(..., description="Usage statistics")
    
class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    model_loaded: bool = False
    model_name: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize model on startup"""
    global embedding_model
    logger.info("Initializing embedding model...")
    embedding_model = EmbeddingModel()
    await embedding_model.initialize()
    logger.info(f"Model {embedding_model.model_name} loaded successfully")
    yield
    # Cleanup
    logger.info("Shutting down embedding service...")

# Create FastAPI app
app = FastAPI(
    title="Embedding Service",
    description="Text embedding service for Drass Compliance Assistant",
    version="1.0.0",
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

class EmbeddingModel:
    """Embedding model wrapper supporting multiple providers"""
    
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
            from openai import OpenAI
            
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("EMBEDDING_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found in environment")
                
            self.model = OpenAI(api_key=api_key)
            
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
                
            self.model = cohere.Client(api_key)
            self.dimension = 1024  # Cohere embed dimension
            
            logger.info(f"Cohere embedding initialized with model: {self.model_name}")
            
        except ImportError:
            raise ImportError("Please install cohere: pip install cohere")
            
    async def embed_texts(self, texts: List[str]) -> Dict[str, Any]:
        """Generate embeddings for texts"""
        start_time = time.time()
        
        if self.provider == "sentence-transformers":
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            embeddings_list = embeddings.tolist()
            
        elif self.provider == "openai":
            response = self.model.embeddings.create(
                model=self.model_name,
                input=texts
            )
            embeddings_list = [item.embedding for item in response.data]
            
        elif self.provider == "cohere":
            response = self.model.embed(
                texts=texts,
                model=self.model_name
            )
            embeddings_list = response.embeddings
            
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
            
        elapsed_time = time.time() - start_time
        
        return {
            "embeddings": embeddings_list,
            "model": self.model_name,
            "usage": {
                "texts_count": len(texts),
                "total_tokens": sum(len(text.split()) for text in texts),  # Approximate
                "elapsed_time": elapsed_time,
                "dimension": self.dimension
            }
        }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        model_loaded=embedding_model is not None,
        model_name=embedding_model.model_name if embedding_model else None
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
        result = await embedding_model.embed_texts(request.texts)
        return EmbeddingResponse(**result)
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embeddings/batch")
async def create_batch_embeddings(requests: List[EmbeddingRequest]):
    """Batch processing for multiple embedding requests"""
    if not embedding_model:
        raise HTTPException(status_code=503, detail="Model not initialized")
        
    results = []
    for request in requests:
        try:
            result = await embedding_model.embed_texts(request.texts)
            results.append(result)
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            results.append({"error": str(e)})
            
    return {"results": results}

@app.get("/models")
async def list_models():
    """List available embedding models"""
    models = {
        "sentence-transformers": [
            "BAAI/bge-large-zh-v1.5",
            "BAAI/bge-large-en-v1.5",
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2"
        ],
        "openai": [
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002"
        ],
        "cohere": [
            "embed-english-v3.0",
            "embed-multilingual-v3.0"
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("EMBEDDING_SERVICE_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)