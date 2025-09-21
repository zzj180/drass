"""
OpenAI-compatible Provider implementation (works with vLLM, LM Studio, MLX, etc.)
"""

import logging
import time
from typing import Optional, List, Dict, Any, AsyncGenerator
import httpx
import json

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

from .base import BaseLLMProvider, LLMResponse, TokenUsage

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseLLMProvider):
    """OpenAI-compatible API provider for vLLM and other OpenAI-compatible services"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:8001/v1")
        self.model_name = config.get("model_name", "vllm")
        self.api_key = config.get("api_key", "123456")
        self.client = None

    async def initialize(self):
        """Initialize OpenAI-compatible provider"""
        # Check if we're connecting to localhost and disable proxy
        import os
        is_local = any(host in self.base_url.lower() for host in ['localhost', '127.0.0.1', '0.0.0.0'])

        client_kwargs = {
            "base_url": self.base_url,
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            "timeout": httpx.Timeout(300.0, connect=30.0)  # 5 minutes timeout for large models, 30s connect
        }

        # For local connections, explicitly disable proxy
        if is_local:
            client_kwargs["proxy"] = None
            # Also try to disable environment proxy temporarily
            old_http_proxy = os.environ.pop('HTTP_PROXY', None)
            old_https_proxy = os.environ.pop('HTTPS_PROXY', None)
            old_http_proxy_lower = os.environ.pop('http_proxy', None)
            old_https_proxy_lower = os.environ.pop('https_proxy', None)

        try:
            self.client = httpx.AsyncClient(**client_kwargs)
        finally:
            # Restore proxy settings if they were removed
            if is_local:
                if old_http_proxy:
                    os.environ['HTTP_PROXY'] = old_http_proxy
                if old_https_proxy:
                    os.environ['HTTPS_PROXY'] = old_https_proxy
                if old_http_proxy_lower:
                    os.environ['http_proxy'] = old_http_proxy_lower
                if old_https_proxy_lower:
                    os.environ['https_proxy'] = old_https_proxy_lower

        # Test connection by listing models
        try:
            logger.info(f"Testing OpenAI-compatible endpoint: {self.base_url}/models")
            response = await self.client.get("/models")
            if response.status_code == 200:
                self._initialized = True
                models_data = response.json()
                available_models = [m.get('id', 'unknown') for m in models_data.get('data', [])]
                logger.info(f"OpenAI-compatible provider initialized at {self.base_url}")
                logger.info(f"Available models: {available_models}")
            else:
                # Some services might not have /models endpoint, try a completion
                logger.info("Models endpoint not available, trying test completion")
                test_response = await self.client.post(
                    "/completions",
                    json={
                        "model": self.model_name,
                        "prompt": "Hello",
                        "max_tokens": 1,
                        "temperature": 0
                    }
                )
                if test_response.status_code in [200, 201]:
                    self._initialized = True
                    logger.info(f"OpenAI-compatible provider initialized at {self.base_url}")
                else:
                    raise Exception(f"Service not responding properly: {test_response.status_code}")
        except httpx.ConnectError as e:
            logger.warning(f"Service not available at {self.base_url}: {e}")
            raise Exception(f"Cannot connect to OpenAI-compatible service at {self.base_url}")
        except Exception as e:
            logger.warning(f"Failed to connect to service: {e}")
            # Don't fail completely - service might still work
            self._initialized = True
            logger.info(f"OpenAI-compatible provider initialized (with warnings) at {self.base_url}")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Generate response using OpenAI-compatible API"""
        if not self._initialized:
            raise Exception("Provider not initialized")

        start_time = time.time()

        # Prepare request
        request_data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.config.get("temperature", 0.7),
            "max_tokens": max_tokens or self.config.get("max_tokens", 2048),
            **kwargs
        }

        if stream:
            return await self._generate_stream(request_data, start_time)

        try:
            response = await self.client.post("/chat/completions", json=request_data)
            response.raise_for_status()

            data = response.json()
            choice = data["choices"][0]

            # Extract token usage
            usage = data.get("usage", {})
            token_usage = TokenUsage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0)
            )

            return LLMResponse(
                content=choice["message"]["content"],
                model=data.get("model", self.model_name),
                provider="openai_compatible",
                response_time=time.time() - start_time,
                usage=token_usage,
                metadata={"raw_response": data}
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during generation: {e}")
            raise Exception(f"Failed to generate response: {e}")
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            raise

    async def _generate_stream(
        self, request_data: Dict[str, Any], start_time: float
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        request_data["stream"] = True

        try:
            async with self.client.stream(
                "POST",
                "/chat/completions",
                json=request_data
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk_data = line[6:]
                        if chunk_data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(chunk_data)
                            if chunk["choices"][0].get("delta", {}).get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during streaming: {e}")
            raise Exception(f"Failed to generate streaming response: {e}")
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            raise

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generation from messages"""
        request_data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.config.get("temperature", 0.7),
            "max_tokens": max_tokens or self.config.get("max_tokens", 2048),
            "stream": True,
            **kwargs
        }

        async for chunk in self._generate_stream(request_data, time.time()):
            yield chunk

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings for texts"""
        # Most vLLM deployments don't include embedding models
        # This is a placeholder that should be overridden if needed
        raise NotImplementedError("Embedding not supported by this OpenAI-compatible provider")

    async def health_check(self) -> Dict[str, Any]:
        """Check provider health"""
        try:
            # Try models endpoint first
            response = await self.client.get("/models")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "provider": "openai_compatible",
                    "base_url": self.base_url,
                    "model": self.model_name
                }

            # Fallback to a test completion
            test_response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                    "temperature": 0
                }
            )

            if test_response.status_code == 200:
                return {
                    "status": "healthy",
                    "provider": "openai_compatible",
                    "base_url": self.base_url,
                    "model": self.model_name
                }
            else:
                return {
                    "status": "unhealthy",
                    "provider": "openai_compatible",
                    "error": f"Status code: {test_response.status_code}"
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "openai_compatible",
                "error": str(e)
            }

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if TIKTOKEN_AVAILABLE:
            # Try to use tiktoken for token counting
            try:
                # Try to get encoding for the model
                if "gpt" in self.model_name.lower():
                    encoding = tiktoken.encoding_for_model(self.model_name)
                else:
                    # Default to cl100k_base for non-GPT models
                    encoding = tiktoken.get_encoding("cl100k_base")

                return len(encoding.encode(text))
            except Exception:
                pass

        # Fallback to simple word-based estimation
        # Roughly 1 token per 4 characters
        return len(text) // 4

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
            self._initialized = False