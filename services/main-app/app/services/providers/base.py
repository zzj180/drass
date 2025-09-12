"""
Base LLM Provider interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
import time


@dataclass
class LLMResponse:
    """Standard LLM response format"""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    response_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TokenUsage:
    """Token usage tracking"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float = 0.0


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
        self._initialized = False
        self.metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "average_response_time": 0.0
        }
    
    @abstractmethod
    async def initialize(self):
        """Initialize the provider"""
        pass
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Generate completion from messages"""
        pass
    
    @abstractmethod
    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generation from messages"""
        pass
    
    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings for texts"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health"""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        pass
    
    def estimate_cost(self, usage: TokenUsage, model: str) -> float:
        """Estimate cost based on token usage"""
        # Default implementation with generic pricing
        price_per_1k_prompt = 0.001
        price_per_1k_completion = 0.002
        
        if model in self.config.get("pricing", {}):
            pricing = self.config["pricing"][model]
            price_per_1k_prompt = pricing.get("prompt", price_per_1k_prompt)
            price_per_1k_completion = pricing.get("completion", price_per_1k_completion)
        
        prompt_cost = (usage.prompt_tokens / 1000) * price_per_1k_prompt
        completion_cost = (usage.completion_tokens / 1000) * price_per_1k_completion
        
        return prompt_cost + completion_cost
    
    def update_metrics(self, response: LLMResponse, error: bool = False):
        """Update provider metrics"""
        self.metrics["total_requests"] += 1
        
        if error:
            self.metrics["total_errors"] += 1
        elif response.usage:
            self.metrics["total_tokens"] += response.usage.get("total_tokens", 0)
            if hasattr(response, "response_time"):
                # Update average response time
                current_avg = self.metrics["average_response_time"]
                total_requests = self.metrics["total_requests"]
                new_avg = ((current_avg * (total_requests - 1)) + response.response_time) / total_requests
                self.metrics["average_response_time"] = new_avg
    
    async def close(self):
        """Clean up provider resources"""
        self._initialized = False