"""
Local MLX Model Provider implementation
"""

import logging
import time
from typing import Optional, List, Dict, Any, AsyncGenerator
import httpx
import json

from .base import BaseLLMProvider, LLMResponse, TokenUsage

logger = logging.getLogger(__name__)


class LocalMLXProvider(BaseLLMProvider):
    """Local MLX model provider for Apple Silicon optimized inference"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:8001/v1")
        self.model_name = config.get("model_name", "qwen3-8b-mlx")
        self.client = None
    
    async def initialize(self):
        """Initialize local MLX provider"""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Content-Type": "application/json"
            },
            timeout=120.0  # Longer timeout for local models
        )
        
        # Test connection
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                self._initialized = True
                logger.info(f"Local MLX provider initialized at {self.base_url}")
            else:
                raise Exception(f"MLX server not responding: {response.status_code}")
        except httpx.ConnectError:
            logger.warning(f"MLX server not available at {self.base_url}")
            raise Exception(f"Cannot connect to MLX server at {self.base_url}")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using local MLX model"""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Convert messages to prompt if needed
            if len(messages) == 1 and messages[0]["role"] == "user":
                # Simple completion endpoint
                request_data = {
                    "model": self.model_name,
                    "prompt": messages[0]["content"],
                    "max_tokens": max_tokens or 1000,
                    "temperature": temperature or 0.7,
                    "stream": stream,
                    **kwargs
                }
                endpoint = "/completions"
            else:
                # Chat completion endpoint
                request_data = {
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": max_tokens or 1000,
                    "temperature": temperature or 0.7,
                    "stream": stream,
                    **kwargs
                }
                endpoint = "/chat/completions"
            
            if stream:
                return await self._handle_streaming(endpoint, request_data, start_time)
            
            response = await self.client.post(endpoint, json=request_data)
            
            if response.status_code != 200:
                error_msg = f"MLX API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            response_time = time.time() - start_time
            
            # Extract content based on endpoint
            if endpoint == "/completions":
                content = data["choices"][0]["text"]
            else:
                content = data["choices"][0]["message"]["content"]
            
            # MLX server may not provide token usage
            usage = None
            if "usage" in data:
                usage = {
                    "prompt_tokens": data["usage"].get("prompt_tokens", 0),
                    "completion_tokens": data["usage"].get("completion_tokens", 0),
                    "total_tokens": data["usage"].get("total_tokens", 0)
                }
            
            llm_response = LLMResponse(
                content=content,
                model=self.model_name,
                provider="local_mlx",
                usage=usage,
                response_time=response_time,
                metadata={
                    "finish_reason": data["choices"][0].get("finish_reason", "stop"),
                    "local": True
                }
            )
            
            self.update_metrics(llm_response)
            return llm_response
            
        except Exception as e:
            logger.error(f"Error generating response with MLX: {e}")
            self.update_metrics(None, error=True)
            raise
    
    async def _handle_streaming(self, endpoint: str, request_data: Dict, start_time: float) -> LLMResponse:
        """Handle streaming response from MLX server"""
        response = await self.client.post(
            endpoint,
            json=request_data,
            headers={"Accept": "text/event-stream"}
        )
        
        if response.status_code != 200:
            raise Exception(f"MLX streaming error: {response.status_code}")
        
        content_chunks = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    if "choices" in data and len(data["choices"]) > 0:
                        if endpoint == "/completions":
                            text = data["choices"][0].get("text", "")
                        else:
                            delta = data["choices"][0].get("delta", {})
                            text = delta.get("content", "")
                        if text:
                            content_chunks.append(text)
                except json.JSONDecodeError:
                    continue
        
        response_time = time.time() - start_time
        content = "".join(content_chunks)
        
        return LLMResponse(
            content=content,
            model=self.model_name,
            provider="local_mlx",
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
        """Stream generation from local MLX model"""
        if not self._initialized:
            await self.initialize()
        
        # Determine endpoint based on message format
        if len(messages) == 1 and messages[0]["role"] == "user":
            request_data = {
                "model": self.model_name,
                "prompt": messages[0]["content"],
                "max_tokens": max_tokens or 1000,
                "temperature": temperature or 0.7,
                "stream": True,
                **kwargs
            }
            endpoint = "/completions"
        else:
            request_data = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens or 1000,
                "temperature": temperature or 0.7,
                "stream": True,
                **kwargs
            }
            endpoint = "/chat/completions"
        
        async with self.client.stream("POST", endpoint, json=request_data) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            if endpoint == "/completions":
                                text = data["choices"][0].get("text", "")
                            else:
                                delta = data["choices"][0].get("delta", {})
                                text = delta.get("content", "")
                            if text:
                                yield text
                    except json.JSONDecodeError:
                        continue
    
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings - not supported by MLX server"""
        raise NotImplementedError("MLX server doesn't support embeddings. Use a dedicated embedding service.")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MLX provider health"""
        try:
            if not self.client:
                self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
            
            response = await self.client.get("/health")
            
            # Also try to get model info
            model_info = {}
            try:
                models_response = await self.client.get("/models")
                if models_response.status_code == 200:
                    model_info = models_response.json()
            except:
                pass
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "provider": "local_mlx",
                "base_url": self.base_url,
                "model": self.model_name,
                "models_available": model_info.get("data", []),
                "metrics": self.metrics
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "local_mlx",
                "base_url": self.base_url,
                "error": str(e),
                "metrics": self.metrics
            }
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # For Qwen models, approximately 2.5 characters per token for English
        # and 1.5 characters per token for Chinese
        # Using average of 2 characters per token
        return len(text) // 2
    
    async def close(self):
        """Close the client connection"""
        if self.client:
            await self.client.aclose()
        await super().close()