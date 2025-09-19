"""
Health check and monitoring response models
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(
        ...,
        description="Service health status (healthy/degraded/unhealthy)"
    )
    model_loaded: bool = Field(
        ...,
        description="Whether a model is loaded"
    )
    model_name: Optional[str] = Field(
        None,
        description="Name of the loaded model"
    )
    provider: str = Field(
        ...,
        description="Current reranking provider"
    )
    fallback_enabled: bool = Field(
        ...,
        description="Whether fallback mechanism is enabled"
    )
    is_fallback_active: bool = Field(
        ...,
        description="Whether currently using a fallback model"
    )
    cache_enabled: bool = Field(
        ...,
        description="Whether caching is enabled"
    )
    cache_type: Optional[str] = Field(
        None,
        description="Type of cache being used (lru/redis)"
    )
    cache_hits: Optional[int] = Field(
        None,
        description="Number of cache hits"
    )
    cache_misses: Optional[int] = Field(
        None,
        description="Number of cache misses"
    )
    cache_size: Optional[int] = Field(
        None,
        description="Current cache size"
    )
    cache_hit_rate: Optional[float] = Field(
        None,
        description="Cache hit rate percentage"
    )
    provider_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Provider-specific information"
    )

class ModelInfoResponse(BaseModel):
    """Model information response"""
    current_provider: str = Field(
        ...,
        description="Currently active provider"
    )
    current_model: str = Field(
        ...,
        description="Currently loaded model"
    )
    is_fallback: bool = Field(
        ...,
        description="Whether using a fallback model"
    )
    available_providers: Dict[str, Any] = Field(
        ...,
        description="List of available providers"
    )
    fallback_models: List[str] = Field(
        ...,
        description="List of configured fallback models"
    )
    supported_devices: List[str] = Field(
        ...,
        description="Supported compute devices"
    )

class MetricsResponse(BaseModel):
    """Metrics response model"""
    requests_total: int = Field(
        ...,
        description="Total number of requests"
    )
    requests_success: int = Field(
        ...,
        description="Number of successful requests"
    )
    requests_error: int = Field(
        ...,
        description="Number of failed requests"
    )
    average_latency_ms: float = Field(
        ...,
        description="Average request latency in milliseconds"
    )
    documents_processed_total: int = Field(
        ...,
        description="Total number of documents processed"
    )
    cache_hit_rate: float = Field(
        ...,
        description="Cache hit rate percentage"
    )
    model_load_time_seconds: float = Field(
        ...,
        description="Time taken to load the model"
    )
    active_requests: int = Field(
        ...,
        description="Number of currently active requests"
    )
    fallback_triggers: int = Field(
        ...,
        description="Number of times fallback was triggered"
    )