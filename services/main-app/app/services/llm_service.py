"""
LLM service for managing language model interactions
"""

import logging
from typing import Optional, List, Dict, Any
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for managing LLM operations"""
    
    def __init__(self):
        self.llm = None
        self._initialized = False
        self.api_base = settings.LLM_BASE_URL or "http://localhost:8001/v1"
        self.api_key = settings.LLM_API_KEY or "not-required"
    
    async def initialize(self):
        """Initialize the LLM service"""
        if not self._initialized:
            logger.info(f"LLM service initialized with base URL: {self.api_base}")
            self._initialized = True
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate text from prompt using the Qwen model"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    json={
                        "model": settings.LLM_MODEL,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
                        "temperature": temperature or settings.LLM_TEMPERATURE
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"LLM API error: {response.status_code} - {response.text}")
                    return f"Error: LLM service returned status {response.status_code}"
                    
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get LLM service statistics"""
        return {
            "status": "operational",
            "model": settings.LLM_MODEL,
            "provider": settings.LLM_PROVIDER
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the LLM service"""
        return {
            "status": "healthy" if self._initialized else "not_initialized",
            "model": settings.LLM_MODEL,
            "provider": settings.LLM_PROVIDER
        }
    
    async def close(self):
        """Close the LLM service"""
        logger.info("Closing LLM service")
        self._initialized = False


# Singleton instance
llm_service = LLMService()