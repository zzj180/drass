"""
Configuration management for Reranking Service
Enhanced with multi-provider support and improved configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List
from enum import Enum
import os

class RerankingProvider(str, Enum):
    """Available reranking providers"""
    SENTENCE_TRANSFORMERS = "sentence-transformers"
    OPENAI = "openai"
    COHERE = "cohere"
    LOCAL = "local"

class Settings(BaseSettings):
    """
    Service configuration with environment variable support
    Enhanced with multi-provider and fallback support
    """
    # Service settings
    SERVICE_NAME: str = "Reranking Service"
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8002, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Provider settings
    RERANKING_PROVIDER: RerankingProvider = Field(
        default=RerankingProvider.SENTENCE_TRANSFORMERS,
        env="RERANKING_PROVIDER",
        description="Reranking provider to use"
    )

    # Model settings
    MODEL_NAME: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-12-v2",
        env="RERANKING_MODEL",
        description="Cross-encoder model for reranking"
    )

    # Fallback models (from smallest to largest)
    FALLBACK_MODELS: List[str] = Field(
        default=[
            "cross-encoder/ms-marco-MiniLM-L-12-v2",  # 140MB
            "BAAI/bge-reranker-base",  # 400MB
            "BAAI/bge-reranker-large"  # 1.1GB
        ],
        description="Fallback models to try if primary fails"
    )

    MODEL_CACHE_DIR: str = Field(
        default="./model_cache",
        env="MODEL_CACHE_DIR",
        description="Directory to cache downloaded models"
    )

    DEVICE: str = Field(
        default="cpu",
        env="RERANKING_DEVICE",
        description="Device to run model on (cuda/cpu/mps)"
    )

    # Performance settings
    MAX_LENGTH: int = Field(
        default=512,
        env="RERANKING_MAX_LENGTH",
        description="Maximum sequence length for model input"
    )

    BATCH_SIZE: int = Field(
        default=32,
        env="RERANKING_BATCH_SIZE",
        description="Batch size for reranking"
    )

    DEFAULT_TOP_K: int = Field(
        default=10,
        env="DEFAULT_TOP_K",
        description="Default number of top documents to return"
    )

    MAX_DOCUMENTS: int = Field(
        default=100,
        env="RERANKING_MAX_DOCUMENTS",
        description="Maximum number of documents to rerank in one request"
    )

    # Cache settings
    CACHE_ENABLED: bool = Field(
        default=True,
        env="CACHE_ENABLED",
        description="Enable result caching"
    )

    CACHE_TYPE: str = Field(
        default="lru",
        env="CACHE_TYPE",
        description="Cache type (lru/redis)"
    )

    CACHE_SIZE: int = Field(
        default=1000,
        env="CACHE_SIZE",
        description="Maximum cache size for LRU cache"
    )

    CACHE_TTL: int = Field(
        default=3600,
        env="CACHE_TTL",
        description="Cache time-to-live in seconds"
    )

    REDIS_URL: Optional[str] = Field(
        default=None,
        env="REDIS_URL",
        description="Redis URL for distributed caching"
    )

    # API Keys (for external providers)
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        env="OPENAI_API_KEY",
        description="OpenAI API key for reranking"
    )

    COHERE_API_KEY: Optional[str] = Field(
        default=None,
        env="COHERE_API_KEY",
        description="Cohere API key for reranking"
    )

    # Monitoring
    ENABLE_METRICS: bool = Field(
        default=True,
        env="ENABLE_METRICS",
        description="Enable Prometheus metrics"
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )

    LOG_FORMAT: str = Field(
        default="json",
        env="LOG_FORMAT",
        description="Log format (json/text)"
    )

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS",
        description="Allowed CORS origins"
    )

    # Graceful degradation
    FALLBACK_ENABLED: bool = Field(
        default=True,
        env="FALLBACK_ENABLED",
        description="Enable fallback to simpler models on failure"
    )

    # Connection pooling
    CONNECTION_POOL_SIZE: int = Field(
        default=10,
        env="CONNECTION_POOL_SIZE",
        description="Size of connection pool for external APIs"
    )

    REQUEST_TIMEOUT: int = Field(
        default=30,
        env="REQUEST_TIMEOUT",
        description="Timeout for external API requests in seconds"
    )

    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @validator('MODEL_CACHE_DIR')
    def ensure_cache_dir(cls, v):
        # Only create directory if it's a relative path and not in Docker
        if not v.startswith('/') and not os.environ.get('DOCKER_CONTAINER'):
            os.makedirs(v, exist_ok=True)
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create global settings instance
settings = Settings()