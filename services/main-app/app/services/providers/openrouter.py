"""
OpenRouter LLM Provider implementation
"""

import logging
import time
from typing import Optional, List, Dict, Any, AsyncGenerator
import httpx
import json

from .base import BaseLLMProvider, LLMResponse, TokenUsage

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter API provider for accessing multiple LLM models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://openrouter.ai/api/v1")
        self.default_model = config.get("default_model", "meta-llama/llama-3-8b-instruct")
        self.site_url = config.get("site_url", "https://drass.ai")
        self.site_name = config.get("site_name", "Drass Compliance Assistant")
        self.client = None
    
    async def initialize(self):
        """Initialize OpenRouter provider"""
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": self.site_url,
                "X-Title": self.site_name,
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
        
        # Test connection
        try:
            response = await self.client.get("/models")
            if response.status_code == 200:
                self._initialized = True
                logger.info("OpenRouter provider initialized successfully")
            else:
                raise Exception(f"Failed to connect to OpenRouter: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter provider: {e}")
            raise
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using OpenRouter"""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        model = model or self.default_model
        
        try:
            request_data = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens or 1000,
                "temperature": temperature or 0.7,
                "stream": stream,
                **kwargs
            }
            
            if stream:
                return await self._handle_streaming(request_data, start_time)
            
            response = await self.client.post(
                "/chat/completions",
                json=request_data
            )
            
            if response.status_code != 200:
                error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            response_time = time.time() - start_time
            
            # Extract usage information
            usage = None
            if "usage" in data:
                usage = {
                    "prompt_tokens": data["usage"].get("prompt_tokens", 0),
                    "completion_tokens": data["usage"].get("completion_tokens", 0),
                    "total_tokens": data["usage"].get("total_tokens", 0)
                }
            
            llm_response = LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=model,
                provider="openrouter",
                usage=usage,
                response_time=response_time,
                metadata={"finish_reason": data["choices"][0].get("finish_reason")}
            )
            
            self.update_metrics(llm_response)
            return llm_response
            
        except Exception as e:
            logger.error(f"Error generating response with OpenRouter: {e}")
            self.update_metrics(None, error=True)
            raise
    
    async def _handle_streaming(self, request_data: Dict, start_time: float) -> LLMResponse:
        """Handle streaming response"""
        response = await self.client.post(
            "/chat/completions",
            json=request_data,
            headers={"Accept": "text/event-stream"}
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter streaming error: {response.status_code}")
        
        content_chunks = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            content_chunks.append(delta["content"])
                except json.JSONDecodeError:
                    continue
        
        response_time = time.time() - start_time
        content = "".join(content_chunks)
        
        return LLMResponse(
            content=content,
            model=request_data["model"],
            provider="openrouter",
            response_time=response_time
        )
    
    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generation from OpenRouter"""
        if not self._initialized:
            await self.initialize()
        
        model = model or self.default_model
        
        request_data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens or 1000,
            "temperature": temperature or 0.7,
            "stream": True,
            **kwargs
        }
        
        async with self.client.stream(
            "POST",
            "/chat/completions",
            json=request_data
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue
    
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings using OpenRouter"""
        # OpenRouter doesn't directly support embeddings
        # This would need to use a different service or model
        raise NotImplementedError("OpenRouter doesn't directly support embeddings. Use a dedicated embedding service.")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenRouter provider health"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Try to get models list as health check
            response = await self.client.get("/models")
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "provider": "openrouter",
                "base_url": self.base_url,
                "metrics": self.metrics
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "openrouter",
                "error": str(e),
                "metrics": self.metrics
            }
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Simple approximation: ~4 characters per token
        # For more accurate counting, use tiktoken library
        return len(text) // 4
    
    async def close(self):
        """Close the client connection"""
        if self.client:
            await self.client.aclose()
        await super().close()