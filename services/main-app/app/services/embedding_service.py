"""
Embedding service for managing text embeddings
"""

import logging
from typing import List, Optional, Dict, Any
import requests
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for managing embedding operations"""
    
    def __init__(self):
        self._initialized = False
        self.api_base = getattr(settings, 'EMBEDDING_API_BASE', 'http://localhost:8002')
    
    async def initialize(self):
        """Initialize the embedding service"""
        if not self._initialized:
            logger.info(f"Embedding service initialized with base URL: {self.api_base}")
            self._initialized = True
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        try:
            response = requests.post(
                f"{self.api_base}/embeddings",
                json={"texts": texts}
            )
            if response.status_code == 200:
                return response.json()["embeddings"]
            else:
                logger.error(f"Embedding service error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    async def embed_query(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single query"""
        embeddings = await self.embed_texts([text])
        return embeddings[0] if embeddings else None
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get embedding service statistics"""
        try:
            response = requests.get(f"{self.api_base}/health")
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "code": response.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the embedding service"""
        return await self.get_stats()
    
    async def close(self):
        """Close the embedding service"""
        logger.info("Closing embedding service")
        self._initialized = False


# Singleton instance
embedding_service = EmbeddingService()