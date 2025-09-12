"""
Configuration management for Reranking Service
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Service configuration with environment variable support
    """
    # Service settings
    SERVICE_NAME: str = "Reranking Service"
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8002, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Model settings
    MODEL_NAME: str = Field(
        default="BAAI/bge-reranker-large",
        env="MODEL_NAME",
        description="Cross-encoder model for reranking"
    )
    MODEL_CACHE_DIR: str = Field(
        default="./models",
        env="MODEL_CACHE_DIR",
        description="Directory to cache downloaded models"
    )
    DEVICE: str = Field(
        default="cpu",
        env="DEVICE",
        description="Device to run model on (cuda/cpu/mps)"
    )
    
    # Performance settings
    MAX_LENGTH: int = Field(
        default=512,
        env="MAX_LENGTH",
        description="Maximum sequence length for model input"
    )
    BATCH_SIZE: int = Field(
        default=32,
        env="BATCH_SIZE",
        description="Batch size for reranking"
    )
    DEFAULT_TOP_K: int = Field(
        default=10,
        env="DEFAULT_TOP_K",
        description="Default number of top documents to return"
    )
    MAX_DOCUMENTS: int = Field(
        default=100,
        env="MAX_DOCUMENTS",
        description="Maximum number of documents to rerank in one request"
    )
    
    # Cache settings
    CACHE_ENABLED: bool = Field(
        default=True,
        env="CACHE_ENABLED",
        description="Enable result caching"
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
    
    # Monitoring
    ENABLE_METRICS: bool = Field(
        default=True,
        env="ENABLE_METRICS",
        description="Enable Prometheus metrics"
    )
    
    # CORS
    CORS_ORIGINS: list = Field(
        default=["*"],
        env="CORS_ORIGINS",
        description="Allowed CORS origins"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create global settings instance
settings = Settings()