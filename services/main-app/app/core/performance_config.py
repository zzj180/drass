"""
Performance optimization configuration for VLLM and LLM services
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class PerformanceConfig(BaseModel):
    """Performance optimization configuration"""
    
    # Token limits for different use cases (optimized for speed)
    QUICK_RESPONSE_TOKENS: int = Field(default=128, description="Quick response token limit")
    STANDARD_RESPONSE_TOKENS: int = Field(default=256, description="Standard response token limit")
    DETAILED_RESPONSE_TOKENS: int = Field(default=512, description="Detailed response token limit")
    MAX_RESPONSE_TOKENS: int = Field(default=1024, description="Maximum response token limit")
    
    # Timeout settings (in seconds) - more aggressive
    QUICK_TIMEOUT: int = Field(default=10, description="Quick response timeout")
    STANDARD_TIMEOUT: int = Field(default=20, description="Standard response timeout")
    DETAILED_TIMEOUT: int = Field(default=40, description="Detailed response timeout")
    MAX_TIMEOUT: int = Field(default=80, description="Maximum timeout")
    
    # VLLM specific optimizations
    VLLM_TEMPERATURE: float = Field(default=0.7, description="VLLM temperature")
    VLLM_TOP_P: float = Field(default=0.9, description="VLLM top_p")
    VLLM_TOP_K: int = Field(default=50, description="VLLM top_k")
    VLLM_REPETITION_PENALTY: float = Field(default=1.1, description="VLLM repetition penalty")
    
    # Response type mappings (optimized for speed)
    RESPONSE_TYPE_CONFIGS: Dict[str, Dict[str, Any]] = Field(
        default={
            "quick": {
                "max_tokens": 128,
                "timeout": 10,
                "temperature": 0.7,
                "description": "快速回答，适合简单问题"
            },
            "standard": {
                "max_tokens": 256,
                "timeout": 20,
                "temperature": 0.7,
                "description": "标准回答，适合一般问题"
            },
            "detailed": {
                "max_tokens": 512,
                "timeout": 40,
                "temperature": 0.7,
                "description": "详细回答，适合复杂问题"
            },
            "analysis": {
                "max_tokens": 1024,
                "timeout": 80,
                "temperature": 0.7,
                "description": "深度分析，适合专业问题"
            }
        }
    )
    
    # RAG optimization settings
    RAG_QUICK_K: int = Field(default=2, description="Number of documents to retrieve for quick responses")
    RAG_STANDARD_K: int = Field(default=3, description="Number of documents to retrieve for standard responses")
    RAG_DETAILED_K: int = Field(default=4, description="Number of documents to retrieve for detailed responses")
    RAG_ANALYSIS_K: int = Field(default=5, description="Number of documents to retrieve for analysis responses")
    
    # Performance monitoring
    ENABLE_PERFORMANCE_MONITORING: bool = Field(default=True, description="Enable performance monitoring")
    LOG_SLOW_REQUESTS: bool = Field(default=True, description="Log requests slower than threshold")
    SLOW_REQUEST_THRESHOLD: float = Field(default=5.0, description="Slow request threshold in seconds")
    
    def get_config_for_type(self, response_type: str) -> Dict[str, Any]:
        """Get configuration for specific response type"""
        return self.RESPONSE_TYPE_CONFIGS.get(response_type, self.RESPONSE_TYPE_CONFIGS["standard"])
    
    def get_optimal_tokens(self, query_length: int, response_type: str = "standard") -> int:
        """Calculate optimal token count based on query length and response type"""
        config = self.get_config_for_type(response_type)
        base_tokens = config["max_tokens"]
        
        # Adjust based on query length
        if query_length > 200:
            return min(base_tokens * 1.5, self.MAX_RESPONSE_TOKENS)
        elif query_length > 100:
            return base_tokens
        else:
            return max(base_tokens * 0.7, self.QUICK_RESPONSE_TOKENS)
    
    def get_optimal_timeout(self, max_tokens: int) -> int:
        """Calculate optimal timeout based on token count"""
        if max_tokens <= 256:
            return self.QUICK_TIMEOUT
        elif max_tokens <= 512:
            return self.STANDARD_TIMEOUT
        elif max_tokens <= 1024:
            return self.DETAILED_TIMEOUT
        else:
            return self.MAX_TIMEOUT


# Global performance configuration instance
performance_config = PerformanceConfig()
