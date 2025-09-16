from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional, Dict, Any
import os
from pathlib import Path

class Settings(BaseSettings):
    """
    Application settings using Pydantic BaseSettings for environment variable support
    """
    
    # Application settings
    APP_NAME: str = "LangChain Compliance Assistant"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    
    # API Documentation
    ENABLE_DOCS: bool = Field(default=True, env="ENABLE_DOCS")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost/compliance_assistant",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=0, env="DATABASE_MAX_OVERFLOW")
    
    # Redis (for caching and rate limiting)
    REDIS_ENABLED: bool = Field(default=False, env="REDIS_ENABLED")
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")
    
    # LLM Configuration (LM Studio with MLX-optimized model)
    LLM_PROVIDER: str = Field(default="openai", env="LLM_PROVIDER")  # LM Studio uses OpenAI API
    LLM_MODEL: str = Field(
        default="qwen3-8b-mlx-bf16",
        env="LLM_MODEL"
    )
    LLM_API_KEY: Optional[str] = Field(default="not-required", env="LLM_API_KEY")  # LM Studio doesn't need key
    LLM_BASE_URL: Optional[str] = Field(default="http://localhost:1234/v1", env="LLM_BASE_URL")
    LLM_TEMPERATURE: float = Field(default=0.7, env="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(default=4096, env="LLM_MAX_TOKENS")
    LLM_TIMEOUT: int = Field(default=60, env="LLM_TIMEOUT")
    LLM_CONTEXT_LENGTH: int = Field(default=32768, env="LLM_CONTEXT_LENGTH")
    
    # LM Studio with MLX settings
    LMSTUDIO_HOST: str = Field(default="localhost", env="LMSTUDIO_HOST")
    LMSTUDIO_PORT: int = Field(default=1234, env="LMSTUDIO_PORT")
    USE_MLX: bool = Field(default=True, env="USE_MLX")  # MLX optimization for Apple Silicon
    MODEL_PRECISION: str = Field(default="bfloat16", env="MODEL_PRECISION")  # bf16 precision
    
    # OpenRouter specific (kept as alternative)
    OPENROUTER_API_KEY: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = Field(
        default="https://openrouter.ai/api/v1",
        env="OPENROUTER_BASE_URL"
    )
    
    # Embedding Configuration
    EMBEDDING_PROVIDER: str = Field(default="openai", env="EMBEDDING_PROVIDER")
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        env="EMBEDDING_MODEL"
    )
    EMBEDDING_API_KEY: Optional[str] = Field(default=None, env="EMBEDDING_API_KEY")
    EMBEDDING_API_BASE: Optional[str] = Field(default="http://localhost:8002", env="EMBEDDING_API_BASE")
    EMBEDDING_DIMENSIONS: int = Field(default=1536, env="EMBEDDING_DIMENSIONS")
    EMBEDDING_BATCH_SIZE: int = Field(default=100, env="EMBEDDING_BATCH_SIZE")
    
    # Vector Store Configuration
    VECTOR_STORE_TYPE: str = Field(default="chromadb", env="VECTOR_STORE_TYPE")
    VECTOR_STORE_HOST: str = Field(default="localhost", env="VECTOR_STORE_HOST")
    VECTOR_STORE_PORT: int = Field(default=8000, env="VECTOR_STORE_PORT")
    VECTOR_STORE_COLLECTION: str = Field(
        default="compliance_documents",
        env="VECTOR_STORE_COLLECTION"
    )
    VECTOR_STORE_API_KEY: Optional[str] = Field(default=None, env="VECTOR_STORE_API_KEY")
    
    # ChromaDB specific
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default="./data/chroma",
        env="CHROMA_PERSIST_DIRECTORY"
    )
    CHROMA_SERVER_HOST: str = Field(default="localhost", env="CHROMA_SERVER_HOST")
    CHROMA_SERVER_PORT: int = Field(default=8000, env="CHROMA_SERVER_PORT")
    
    # Reranking Configuration
    RERANKING_ENABLED: bool = Field(default=False, env="RERANKING_ENABLED")
    RERANKING_PROVIDER: str = Field(default="cohere", env="RERANKING_PROVIDER")
    RERANKING_MODEL: str = Field(
        default="rerank-english-v2.0",
        env="RERANKING_MODEL"
    )
    RERANKING_API_KEY: Optional[str] = Field(default=None, env="RERANKING_API_KEY")
    RERANKING_TOP_K: int = Field(default=10, env="RERANKING_TOP_K")
    
    # Document Processing
    MAX_FILE_SIZE_MB: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[
            "pdf", "docx", "xlsx", "pptx", "txt", "md", "csv", "json",
            "png", "jpg", "jpeg", "gif", "bmp"
        ],
        env="ALLOWED_FILE_TYPES"
    )
    CHUNK_SIZE: int = Field(default=1000, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(default=200, env="CHUNK_OVERLAP")
    
    # Storage
    STORAGE_TYPE: str = Field(default="local", env="STORAGE_TYPE")
    STORAGE_PATH: str = Field(default="./data/uploads", env="STORAGE_PATH")
    
    # S3 Configuration (if using S3 storage)
    S3_BUCKET: Optional[str] = Field(default=None, env="S3_BUCKET")
    S3_REGION: str = Field(default="us-east-1", env="S3_REGION")
    S3_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="S3_SECRET_ACCESS_KEY")
    S3_ENDPOINT_URL: Optional[str] = Field(default=None, env="S3_ENDPOINT_URL")
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    WS_CONNECTION_TIMEOUT: int = Field(default=60, env="WS_CONNECTION_TIMEOUT")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # Feature Flags
    ENABLE_STREAMING: bool = Field(default=True, env="ENABLE_STREAMING")
    ENABLE_MEMORY: bool = Field(default=True, env="ENABLE_MEMORY")
    ENABLE_TOOLS: bool = Field(default=True, env="ENABLE_TOOLS")
    ENABLE_AGENT: bool = Field(default=True, env="ENABLE_AGENT")

    # Compliance Settings
    COMPLIANCE_MODE_ENABLED: bool = Field(default=True, env="COMPLIANCE_MODE_ENABLED")
    COMPLIANCE_MIN_WORD_COUNT: int = Field(default=5000, env="COMPLIANCE_MIN_WORD_COUNT")
    COMPLIANCE_ENABLE_EMOJI: bool = Field(default=True, env="COMPLIANCE_ENABLE_EMOJI")
    COMPLIANCE_ENABLE_MARKDOWN: bool = Field(default=True, env="COMPLIANCE_ENABLE_MARKDOWN")
    COMPLIANCE_MAX_EXPANSION_ATTEMPTS: int = Field(default=3, env="COMPLIANCE_MAX_EXPANSION_ATTEMPTS")
    
    # Lowercase properties for compatibility
    @property
    def vector_store_type(self):
        return self.VECTOR_STORE_TYPE
    
    @property
    def chroma_persist_directory(self):
        return self.CHROMA_PERSIST_DIRECTORY
    
    @property
    def openai_api_key(self):
        return self.LLM_API_KEY
    
    @property
    def openai_api_base(self):
        return self.LLM_BASE_URL
    
    @property
    def embedding_api_base(self):
        return self.EMBEDDING_API_BASE if hasattr(self, 'EMBEDDING_API_BASE') else "http://localhost:8002"
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ["development", "staging", "production", "testing"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v_upper
    
    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("ALLOWED_FILE_TYPES")
    @classmethod
    def validate_file_types(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [ft.strip().lower() for ft in v.split(",")]
        return [ft.lower() for ft in v]
    
    @property
    def database_url_async(self) -> str:
        """Convert database URL to async version"""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return self.DATABASE_URL
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Create settings instance
settings = Settings()

# Create necessary directories
Path(settings.STORAGE_PATH).mkdir(parents=True, exist_ok=True)
if settings.VECTOR_STORE_TYPE == "chromadb":
    Path(settings.CHROMA_PERSIST_DIRECTORY).mkdir(parents=True, exist_ok=True)