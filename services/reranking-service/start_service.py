#!/usr/bin/env python3
"""
Startup script for Reranking Service with improved error handling
"""
import os
import sys
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_model_availability():
    """Check if model files are available locally"""
    model_name = os.getenv("MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-12-v2")
    cache_dir = os.getenv("MODEL_CACHE_DIR", "/app/model_cache")
    
    # Check if it's a local path
    if os.path.exists(model_name):
        return True
    
    # Check if it's a HuggingFace model and files exist in cache
    if "/" in model_name:
        cache_path = Path(cache_dir) / f"models--{model_name.replace('/', '--')}"
        if cache_path.exists():
            logger.info(f"Found cached model at {cache_path}")
            return True
    
    return False

def preload_model():
    """Preload the model to check availability"""
    try:
        from sentence_transformers import CrossEncoder
        
        model_name = os.getenv("MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-12-v2")
        cache_dir = os.getenv("MODEL_CACHE_DIR", "/app/model_cache")
        
        logger.info(f"Preloading model: {model_name}")
        
        # Set environment variables for caching
        os.environ["TRANSFORMERS_CACHE"] = cache_dir
        os.environ["HF_HOME"] = cache_dir
        
        # Try to load the model
        model = CrossEncoder(model_name, cache_folder=cache_dir)
        logger.info("Model preloaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Model preload failed: {str(e)}")
        return False

def main():
    """Main startup function"""
    logger.info("Starting Reranking Service startup checks...")
    
    # Check if model is available
    if check_model_availability():
        logger.info("Model files found locally")
    else:
        logger.warning("Model files not found locally, will download on first use")
    
    # Try to preload the model
    if preload_model():
        logger.info("Model preload successful")
    else:
        logger.warning("Model preload failed, service will start anyway")
    
    # Start the actual service
    logger.info("Starting FastAPI service...")
    import uvicorn
    from app import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )

if __name__ == "__main__":
    main()
