"""
LM Studio Provider implementation
"""

import logging
import time
from typing import Optional, List, Dict, Any, AsyncGenerator
import httpx
import json

from .base import BaseLLMProvider, LLMResponse, TokenUsage

logger = logging.getLogger(__name__)


class LMStudioProvider(BaseLLMProvider):
    """LM Studio provider for local model serving"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:1234/v1")
        self.model_name = config.get("model_name", "local-model")
        self.client = None
    
    async def initialize(self):
        """Initialize LM Studio provider"""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Content-Type": "application/json"
            },
            timeout=120.0  # Longer timeout for local models
        )
        
        # Test connection
        try:
            response = await self.client.get("/models")
            if response.status_code == 200:
                models = response.json()
                if models.get("data"):
                    # Use the first available model if not specified
                    if not self.model_name or self.model_name == "local-model":
                        self.model_name = models["data"][0]["id"]
                    logger.info(f"LM Studio provider initialized with model: {self.model_name}")
                self._initialized = True
            else:
                raise Exception(f"LM Studio not responding: {response.status_code}")
        except httpx.ConnectError:
            logger.warning(f"LM Studio not available at {self.base_url}")
            raise Exception(f"Cannot connect to LM Studio at {self.base_url}")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using LM Studio"""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            request_data = {
                "model": self.model_name,
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
                error_msg = f"LM Studio API error: {response.status_code} - {response.text}"
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
                model=self.model_name,
                provider="lmstudio",
                usage=usage,
                response_time=response_time,
                metadata={
                    "finish_reason": data["choices"][0].get("finish_reason", "stop"),
                    "local": True,
                    "lmstudio_version": data.get("system_fingerprint")
                }
            )
            
            self.update_metrics(llm_response)
            return llm_response
            
        except Exception as e:
            logger.error(f"Error generating response with LM Studio: {e}")
            self.update_metrics(None, error=True)
            raise
    
    async def _handle_streaming(self, request_data: Dict, start_time: float) -> LLMResponse:
        """Handle streaming response from LM Studio"""
        response = await self.client.post(
            "/chat/completions",
            json=request_data,
            headers={"Accept": "text/event-stream"}
        )
        
        if response.status_code != 200:
            raise Exception(f"LM Studio streaming error: {response.status_code}")
        
        content_chunks = []
        total_tokens = 0
        
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
                        # Some LM Studio versions include token count in streaming
                        if "usage" in data:
                            total_tokens = data["usage"].get("total_tokens", total_tokens)
                except json.JSONDecodeError:
                    continue
        
        response_time = time.time() - start_time
        content = "".join(content_chunks)
        
        usage = None
        if total_tokens > 0:
            # Estimate token distribution
            prompt_tokens = self.count_tokens("".join([m["content"] for m in request_data["messages"]]))
            completion_tokens = self.count_tokens(content)
            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        
        return LLMResponse(
            content=content,
            model=self.model_name,
            provider="lmstudio",
            usage=usage,
            response_time=response_time,
            metadata={"local": True, "streaming": True}
        )
    
    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generation from LM Studio"""
        if not self._initialized:
            await self.initialize()
        
        request_data = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens or 1000,
            "temperature": temperature or 0.7,
            "stream": True,
            **kwargs
        }
        
        async with self.client.stream("POST", "/chat/completions", json=request_data) as response:
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
        """Generate embeddings using LM Studio"""
        if not self._initialized:
            await self.initialize()
        
        # LM Studio supports embeddings endpoint
        try:
            embeddings = []
            for text in texts:
                response = await self.client.post(
                    "/embeddings",
                    json={
                        "model": model or self.model_name,
                        "input": text
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    embeddings.append(data["data"][0]["embedding"])
                else:
                    raise Exception(f"Embedding failed: {response.status_code}")
            
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings with LM Studio: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check LM Studio provider health"""
        try:
            if not self.client:
                self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
            
            response = await self.client.get("/models")
            
            models_list = []
            if response.status_code == 200:
                models_data = response.json()
                models_list = [m["id"] for m in models_data.get("data", [])]
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "provider": "lmstudio",
                "base_url": self.base_url,
                "current_model": self.model_name,
                "available_models": models_list,
                "metrics": self.metrics
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "lmstudio",
                "base_url": self.base_url,
                "error": str(e),
                "metrics": self.metrics
            }
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # General approximation for most models
        # ~4 characters per token for English text
        return len(text) // 4
    
    async def close(self):
        """Close the client connection"""
        if self.client:
            await self.client.aclose()
        await super().close()