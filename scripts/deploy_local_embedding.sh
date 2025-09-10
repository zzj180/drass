#!/bin/bash

# Local Embedding Service Deployment Script
# Deploys embedding service using Sentence Transformers locally

set -e

echo "========================================"
echo "Local Embedding Service Deployment"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
EMBEDDING_PORT=8001
EMBEDDING_MODEL="BAAI/bge-base-zh-v1.5"
SERVICE_DIR="services/embedding-service"

# Step 1: Check Python environment
echo -e "\n${YELLOW}Step 1: Checking Python environment...${NC}"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION is installed${NC}"
else
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

# Step 2: Create virtual environment
echo -e "\n${YELLOW}Step 2: Setting up Python environment...${NC}"
if [ ! -d "$SERVICE_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SERVICE_DIR/venv"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source "$SERVICE_DIR/venv/bin/activate"

# Step 3: Install dependencies
echo -e "\n${YELLOW}Step 3: Installing dependencies...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -q \
    fastapi \
    uvicorn \
    sentence-transformers \
    torch \
    numpy \
    pydantic \
    python-multipart \
    redis \
    httpx

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 4: Download embedding model
echo -e "\n${YELLOW}Step 4: Downloading embedding model...${NC}"
echo "Model: $EMBEDDING_MODEL"
python3 -c "
from sentence_transformers import SentenceTransformer
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
print('Downloading model...')
model = SentenceTransformer('$EMBEDDING_MODEL')
print('Model downloaded successfully!')
"
echo -e "${GREEN}✓ Model ready${NC}"

# Step 5: Update embedding service with local model support
echo -e "\n${YELLOW}Step 5: Updating embedding service...${NC}"
cat > "$SERVICE_DIR/local_app.py" << 'EOF'
"""
Local Embedding Service using Sentence Transformers
Optimized for Chinese and English text
"""

import os
import logging
import numpy as np
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
import torch
import uvicorn
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable tokenizers parallelism warning
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Configuration
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5")
CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "./models")
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "32"))
MAX_SEQUENCE_LENGTH = int(os.getenv("MAX_SEQUENCE_LENGTH", "512"))

# Initialize FastAPI app
app = FastAPI(
    title="Local Embedding Service",
    description="High-performance local embedding service for RAG applications",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
model = None
device = None

class EmbeddingRequest(BaseModel):
    """Request model for embedding generation"""
    texts: List[str] = Field(..., description="List of texts to embed")
    model: Optional[str] = Field(default=MODEL_NAME, description="Model name")
    instruction: Optional[str] = Field(default=None, description="Optional instruction for embedding")
    normalize: bool = Field(default=True, description="Normalize embeddings")
    
class EmbeddingResponse(BaseModel):
    """Response model for embedding generation"""
    embeddings: List[List[float]]
    model: str
    dimension: int
    usage: Dict[str, int]
    processing_time_ms: float

class ModelInfo(BaseModel):
    """Model information"""
    model_name: str
    dimension: int
    max_sequence_length: int
    device: str
    loaded: bool

@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    global model, device
    
    logger.info(f"Loading model: {MODEL_NAME}")
    
    # Detect device
    if torch.cuda.is_available():
        device = "cuda"
        logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
    elif torch.backends.mps.is_available():
        device = "mps"
        logger.info("Using Apple Silicon GPU")
    else:
        device = "cpu"
        logger.info("Using CPU")
    
    # Load model
    try:
        model = SentenceTransformer(
            MODEL_NAME,
            device=device,
            cache_folder=CACHE_DIR
        )
        model.max_seq_length = MAX_SEQUENCE_LENGTH
        logger.info(f"Model loaded successfully on {device}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Local Embedding Service",
        "model": MODEL_NAME,
        "device": device,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy" if model is not None else "unhealthy",
        "model_loaded": model is not None,
        "device": device,
        "available_memory_gb": torch.cuda.get_device_properties(0).total_memory / 1e9 if device == "cuda" else None
    }

@app.get("/models", response_model=List[ModelInfo])
async def list_models():
    """List available models"""
    return [
        ModelInfo(
            model_name=MODEL_NAME,
            dimension=model.get_sentence_embedding_dimension() if model else 0,
            max_sequence_length=MAX_SEQUENCE_LENGTH,
            device=device or "not loaded",
            loaded=model is not None
        )
    ]

@app.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    """Generate embeddings for input texts"""
    
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")
    
    if len(request.texts) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"Batch size {len(request.texts)} exceeds maximum {MAX_BATCH_SIZE}"
        )
    
    start_time = datetime.utcnow()
    
    try:
        # Add instruction if provided (for models like BGE)
        texts = request.texts
        if request.instruction and "bge" in MODEL_NAME.lower():
            texts = [f"{request.instruction}: {text}" for text in texts]
        
        # Generate embeddings
        with torch.no_grad():
            embeddings = model.encode(
                texts,
                normalize_embeddings=request.normalize,
                batch_size=min(len(texts), MAX_BATCH_SIZE),
                show_progress_bar=False,
                convert_to_numpy=True
            )
        
        # Convert to list
        if isinstance(embeddings, np.ndarray):
            embeddings_list = embeddings.tolist()
        else:
            embeddings_list = [emb.tolist() for emb in embeddings]
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Calculate token usage (approximate)
        total_tokens = sum(len(text.split()) * 1.3 for text in request.texts)
        
        return EmbeddingResponse(
            embeddings=embeddings_list,
            model=request.model or MODEL_NAME,
            dimension=len(embeddings_list[0]),
            usage={
                "prompt_tokens": int(total_tokens),
                "total_tokens": int(total_tokens)
            },
            processing_time_ms=processing_time
        )
    
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embeddings/batch")
async def generate_batch_embeddings(requests: List[EmbeddingRequest]):
    """Generate embeddings for multiple batches"""
    
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    results = []
    for req in requests:
        result = await generate_embeddings(req)
        results.append(result)
    
    return {"results": results}

@app.get("/benchmark")
async def benchmark():
    """Run a simple benchmark"""
    
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    test_texts = [
        "这是一个测试句子。",
        "This is a test sentence.",
        "机器学习是人工智能的一个分支。",
        "Machine learning is a branch of artificial intelligence."
    ]
    
    start_time = datetime.utcnow()
    
    with torch.no_grad():
        embeddings = model.encode(test_texts, show_progress_bar=False)
    
    processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    return {
        "num_texts": len(test_texts),
        "embedding_dimension": embeddings.shape[1],
        "processing_time_ms": processing_time,
        "texts_per_second": len(test_texts) / (processing_time / 1000),
        "device": device
    }

if __name__ == "__main__":
    uvicorn.run(
        "local_app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=False,
        log_level="info"
    )
EOF

echo -e "${GREEN}✓ Service updated${NC}"

# Step 6: Create systemd service file (for production)
echo -e "\n${YELLOW}Step 6: Creating service configuration...${NC}"
cat > "$SERVICE_DIR/embedding.service" << EOF
[Unit]
Description=Local Embedding Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD/$SERVICE_DIR
Environment="PATH=$PWD/$SERVICE_DIR/venv/bin"
Environment="EMBEDDING_MODEL=$EMBEDDING_MODEL"
Environment="PORT=$EMBEDDING_PORT"
ExecStart=$PWD/$SERVICE_DIR/venv/bin/python local_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Service configuration created${NC}"

# Step 7: Create Docker configuration
echo -e "\n${YELLOW}Step 7: Creating Docker configuration...${NC}"
cat > "$SERVICE_DIR/Dockerfile.local" << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY local_app.py .

# Download model at build time
ARG MODEL_NAME=BAAI/bge-base-zh-v1.5
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${MODEL_NAME}')"

# Expose port
EXPOSE 8001

# Run application
CMD ["uvicorn", "local_app:app", "--host", "0.0.0.0", "--port", "8001"]
EOF

# Create requirements file
cat > "$SERVICE_DIR/requirements.txt" << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
sentence-transformers==2.2.2
torch>=2.0.0
numpy==1.24.3
pydantic==2.5.0
python-multipart==0.0.6
redis==5.0.1
httpx==0.25.2
EOF

echo -e "${GREEN}✓ Docker configuration created${NC}"

# Step 8: Create test script
echo -e "\n${YELLOW}Step 8: Creating test script...${NC}"
cat > "$SERVICE_DIR/test_embedding.py" << 'EOF'
#!/usr/bin/env python3
"""Test script for local embedding service"""

import requests
import json
import time
import numpy as np
from typing import List

API_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{API_URL}/health")
    return response.json()

def test_embedding(texts: List[str]):
    """Test embedding generation"""
    payload = {
        "texts": texts,
        "normalize": True
    }
    response = requests.post(f"{API_URL}/embeddings", json=payload)
    return response.json()

def test_similarity(text1: str, text2: str):
    """Test semantic similarity"""
    response = test_embedding([text1, text2])
    if "embeddings" in response:
        emb1 = np.array(response["embeddings"][0])
        emb2 = np.array(response["embeddings"][1])
        similarity = np.dot(emb1, emb2)
        return similarity
    return None

def run_tests():
    print("="*50)
    print("Local Embedding Service Test Suite")
    print("="*50)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        health = test_health()
        print(f"✓ Service is {health['status']}")
        print(f"  Model loaded: {health['model_loaded']}")
        print(f"  Device: {health['device']}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return
    
    # Test 2: Simple embedding
    print("\n2. Testing embedding generation...")
    test_texts = [
        "合规管理是企业管理的重要组成部分",
        "Compliance management is crucial for businesses",
        "机器学习可以提高工作效率"
    ]
    
    try:
        result = test_embedding(test_texts)
        print(f"✓ Generated {len(result['embeddings'])} embeddings")
        print(f"  Dimension: {result['dimension']}")
        print(f"  Processing time: {result['processing_time_ms']:.2f}ms")
    except Exception as e:
        print(f"✗ Embedding generation failed: {e}")
        return
    
    # Test 3: Semantic similarity
    print("\n3. Testing semantic similarity...")
    pairs = [
        ("合规管理", "合规性管理"),
        ("合规管理", "天气预报"),
        ("machine learning", "deep learning"),
        ("machine learning", "weather forecast")
    ]
    
    for text1, text2 in pairs:
        similarity = test_similarity(text1, text2)
        if similarity is not None:
            print(f"  '{text1}' vs '{text2}': {similarity:.3f}")
    
    # Test 4: Benchmark
    print("\n4. Running benchmark...")
    try:
        response = requests.get(f"{API_URL}/benchmark")
        benchmark = response.json()
        print(f"✓ Benchmark completed")
        print(f"  Texts per second: {benchmark['texts_per_second']:.2f}")
        print(f"  Processing time: {benchmark['processing_time_ms']:.2f}ms")
    except Exception as e:
        print(f"✗ Benchmark failed: {e}")
    
    print("\n" + "="*50)
    print("Test suite completed!")

if __name__ == "__main__":
    run_tests()
EOF

chmod +x "$SERVICE_DIR/test_embedding.py"
echo -e "${GREEN}✓ Test script created${NC}"

# Step 9: Create startup script
echo -e "\n${YELLOW}Step 9: Creating startup script...${NC}"
cat > "$SERVICE_DIR/start_service.sh" << EOF
#!/bin/bash
# Start local embedding service

cd "$(dirname "\$0")"
source venv/bin/activate
export EMBEDDING_MODEL="$EMBEDDING_MODEL"
export PORT=$EMBEDDING_PORT
echo "Starting embedding service on port $EMBEDDING_PORT..."
python local_app.py
EOF

chmod +x "$SERVICE_DIR/start_service.sh"
echo -e "${GREEN}✓ Startup script created${NC}"

# Step 10: Create configuration file
echo -e "\n${YELLOW}Step 10: Creating configuration file...${NC}"
CONFIG_FILE="config/embedding.env"
mkdir -p config

cat > "$CONFIG_FILE" << EOF
# Local Embedding Service Configuration
# Generated on $(date)

# Service Settings
EMBEDDING_SERVICE_URL=http://localhost:$EMBEDDING_PORT
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=$EMBEDDING_MODEL

# Model Configuration
EMBEDDING_DIMENSION=768
MAX_SEQUENCE_LENGTH=512
MAX_BATCH_SIZE=32

# Performance Settings
MODEL_CACHE_DIR=./models
TOKENIZERS_PARALLELISM=false

# For use with main application
VECTOR_STORE_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./data/chroma
CHROMA_COLLECTION_NAME=compliance_docs

# Alternative local models (uncomment to use)
# EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # English only, faster
# EMBEDDING_MODEL=shibing624/text2vec-base-chinese       # Chinese optimized
EOF

echo -e "${GREEN}✓ Configuration file created at $CONFIG_FILE${NC}"

# Display summary
echo -e "\n${GREEN}========================================"
echo "Local Embedding Service Setup Complete!"
echo "========================================${NC}"
echo ""
echo "Service Details:"
echo "  Model: $EMBEDDING_MODEL"
echo "  Port: $EMBEDDING_PORT"
echo "  Dimension: 768"
echo ""
echo "Files created:"
echo "  Service: $SERVICE_DIR/local_app.py"
echo "  Config: $CONFIG_FILE"
echo "  Startup: $SERVICE_DIR/start_service.sh"
echo "  Test: $SERVICE_DIR/test_embedding.py"
echo ""
echo "To start the service:"
echo "  cd $SERVICE_DIR && ./start_service.sh"
echo ""
echo "To test the service:"
echo "  python3 $SERVICE_DIR/test_embedding.py"
echo ""
echo "To use with Docker:"
echo "  cd $SERVICE_DIR"
echo "  docker build -f Dockerfile.local -t embedding-service ."
echo "  docker run -p $EMBEDDING_PORT:$EMBEDDING_PORT embedding-service"
echo ""
echo -e "${GREEN}✓ Ready to use!${NC}"