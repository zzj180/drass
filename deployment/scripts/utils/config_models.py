"""Configuration models using Pydantic for validation and type safety."""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from pathlib import Path


class Metadata(BaseModel):
    """Configuration metadata."""
    name: str = Field(..., description="Configuration name")
    version: str = Field(default="1.0", description="Configuration version")
    created_at: datetime = Field(default_factory=datetime.now)
    description: Optional[str] = None
    author: Optional[str] = None


class AWSConfig(BaseModel):
    """AWS infrastructure configuration."""
    region: str = Field(default="us-west-2")
    vpc_id: Optional[str] = None
    subnet_ids: List[str] = Field(default_factory=list)
    security_group_ids: List[str] = Field(default_factory=list)
    instance_types: Dict[str, str] = Field(default_factory=dict)
    ecs_cluster: Optional[str] = None
    ecr_registry: Optional[str] = None
    s3_bucket: Optional[str] = None


class DockerConfig(BaseModel):
    """Docker configuration."""
    compose_file: str = Field(default="docker-compose.yml")
    network: str = Field(default="drass-network")
    registry: Optional[str] = None
    build_args: Dict[str, str] = Field(default_factory=dict)
    volumes: Dict[str, str] = Field(default_factory=dict)


class LocalGPUConfig(BaseModel):
    """Local GPU configuration."""
    gpu_type: Literal["nvidia", "apple_silicon", "amd"] = "nvidia"
    cuda_version: Optional[str] = None
    gpu_memory: Optional[str] = None
    gpu_count: int = 1
    metal_enabled: bool = False
    mlx_enabled: bool = False


class Infrastructure(BaseModel):
    """Infrastructure configuration."""
    aws: Optional[AWSConfig] = None
    docker: Optional[DockerConfig] = None
    local_gpu: Optional[LocalGPUConfig] = None


class LLMConfig(BaseModel):
    """LLM service configuration."""
    provider: Literal["openrouter", "openai", "azure", "local-mlx", "vllm", "ollama", "llamacpp"]
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, gt=0)
    timeout: int = Field(default=60, gt=0)
    context_length: int = Field(default=32768, gt=0)

    # Provider-specific settings
    # OpenRouter
    openrouter_site_url: Optional[str] = None
    openrouter_app_name: Optional[str] = None

    # Azure
    azure_deployment_name: Optional[str] = None
    azure_api_version: Optional[str] = None

    # Local MLX
    mlx_model_path: Optional[str] = None
    mlx_precision: Literal["float16", "bfloat16", "int8", "int4"] = "bfloat16"

    # vLLM
    vllm_gpu_memory_utilization: float = Field(default=0.9, ge=0.0, le=1.0)
    vllm_max_model_len: Optional[int] = None

    # Ollama
    ollama_num_predict: Optional[int] = None
    ollama_num_ctx: Optional[int] = None


class EmbeddingConfig(BaseModel):
    """Embedding service configuration."""
    provider: Literal["openai", "local", "huggingface", "cohere"]
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    batch_size: int = Field(default=100, gt=0)
    dimensions: Optional[int] = None

    # Local settings
    local_model_path: Optional[str] = None
    device: Literal["cpu", "cuda", "mps"] = "cpu"


class RerankingConfig(BaseModel):
    """Reranking service configuration."""
    enabled: bool = True
    provider: Literal["cohere", "local", "cross-encoder"]
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    top_k: int = Field(default=10, gt=0)

    # Local settings
    local_model_path: Optional[str] = None
    device: Literal["cpu", "cuda", "mps"] = "cpu"


class DocumentProcessorConfig(BaseModel):
    """Document processor configuration."""
    enabled: bool = True
    api_base: str = Field(default="http://localhost:8003")
    max_file_size: str = Field(default="100MB")
    supported_formats: List[str] = Field(
        default=["pdf", "docx", "xlsx", "pptx", "txt", "md", "html", "csv"]
    )
    ocr_enabled: bool = True
    ocr_language: str = Field(default="eng")


class VectorStoreConfig(BaseModel):
    """Vector store configuration."""
    type: Literal["chromadb", "weaviate", "pinecone", "qdrant", "milvus"]
    host: str = Field(default="localhost")
    port: int = Field(default=8000, gt=0)
    collection_name: str = Field(default="drass_docs")

    # Auth
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

    # Provider-specific
    # Pinecone
    pinecone_environment: Optional[str] = None
    pinecone_index_name: Optional[str] = None

    # Weaviate
    weaviate_scheme: Literal["http", "https"] = "http"
    weaviate_class_name: Optional[str] = None

    # Qdrant
    qdrant_grpc_port: Optional[int] = None
    qdrant_prefer_grpc: bool = False


class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: Literal["postgresql", "mysql", "sqlite"]
    host: str = Field(default="localhost")
    port: int = Field(default=5432, gt=0)
    database: str
    user: Optional[str] = None
    password: Optional[str] = None

    # Connection pool
    pool_size: int = Field(default=20, gt=0)
    max_overflow: int = Field(default=0, ge=0)
    pool_timeout: int = Field(default=30, gt=0)

    # SQLite specific
    sqlite_path: Optional[str] = None


class CacheConfig(BaseModel):
    """Cache configuration."""
    type: Literal["redis", "memcached", "memory"]
    host: str = Field(default="localhost")
    port: int = Field(default=6379, gt=0)
    password: Optional[str] = None
    ttl: int = Field(default=3600, gt=0)
    db: int = Field(default=0, ge=0)

    # Redis specific
    redis_ssl: bool = False
    redis_cluster_mode: bool = False


class Services(BaseModel):
    """All services configuration."""
    llm: LLMConfig
    embedding: EmbeddingConfig
    reranking: Optional[RerankingConfig] = None
    document_processor: Optional[DocumentProcessorConfig] = None
    vector_store: VectorStoreConfig
    database: DatabaseConfig
    cache: Optional[CacheConfig] = None


class MainAppConfig(BaseModel):
    """Main application configuration."""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, gt=0)
    workers: int = Field(default=4, gt=0)
    enable_docs: bool = True
    cors_origins: List[str] = Field(default=["http://localhost:5173"])

    # Features
    enable_streaming: bool = True
    enable_agent: bool = True
    enable_memory: bool = True

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = Field(default=60, gt=0)

    # Security
    jwt_enabled: bool = True
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, gt=0)
    refresh_token_expire_days: int = Field(default=7, gt=0)


class FrontendConfig(BaseModel):
    """Frontend configuration."""
    port: int = Field(default=5173, gt=0)
    build_mode: Literal["development", "production"] = "production"
    api_base: str = Field(default="http://localhost:8000")
    websocket_url: Optional[str] = None

    # Build settings
    source_map: bool = False
    minify: bool = True
    bundle_analyze: bool = False


class Application(BaseModel):
    """Application configuration."""
    main_app: MainAppConfig = Field(default_factory=MainAppConfig)
    frontend: FrontendConfig = Field(default_factory=FrontendConfig)


class PrometheusConfig(BaseModel):
    """Prometheus configuration."""
    enabled: bool = True
    port: int = Field(default=9090, gt=0)
    scrape_interval: str = Field(default="15s")
    retention: str = Field(default="15d")


class GrafanaConfig(BaseModel):
    """Grafana configuration."""
    enabled: bool = True
    port: int = Field(default=3000, gt=0)
    admin_user: str = Field(default="admin")
    admin_password: str = Field(default="admin")


class Monitoring(BaseModel):
    """Monitoring configuration."""
    enabled: bool = True
    prometheus: Optional[PrometheusConfig] = None
    grafana: Optional[GrafanaConfig] = None

    # Logging
    log_aggregator: Optional[Literal["elasticsearch", "loki", "cloudwatch"]] = None
    metrics_exporter: Optional[Literal["prometheus", "datadog", "newrelic"]] = None


class Logging(BaseModel):
    """Logging configuration."""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: Literal["json", "text"] = "json"
    outputs: List[Dict[str, Any]] = Field(default_factory=lambda: [{"type": "console"}])

    # File output
    file_path: Optional[str] = None
    file_rotation: bool = True
    file_max_bytes: int = Field(default=10485760, gt=0)  # 10MB
    file_backup_count: int = Field(default=5, gt=0)


class DeploymentConfig(BaseModel):
    """Deployment configuration."""
    type: Literal["aws", "docker-compose", "local-gpu", "local-cpu", "kubernetes"]
    environment: Literal["development", "staging", "production"] = "development"

    # Auto-scaling
    auto_scaling_enabled: bool = False
    min_replicas: int = Field(default=1, gt=0)
    max_replicas: int = Field(default=10, gt=0)
    target_cpu_percent: int = Field(default=70, gt=0, le=100)

    # Health checks
    health_check_enabled: bool = True
    health_check_interval: int = Field(default=30, gt=0)
    health_check_timeout: int = Field(default=10, gt=0)
    health_check_retries: int = Field(default=3, gt=0)


class Config(BaseModel):
    """Main configuration model."""
    version: str = Field(default="1.0")
    metadata: Metadata
    deployment: DeploymentConfig
    infrastructure: Infrastructure
    services: Services
    application: Application = Field(default_factory=Application)
    monitoring: Optional[Monitoring] = None
    logging: Logging = Field(default_factory=Logging)

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate configuration version."""
        supported_versions = ["1.0", "1.1"]
        if v not in supported_versions:
            raise ValueError(f"Unsupported version: {v}. Supported: {supported_versions}")
        return v

    def to_env(self) -> Dict[str, str]:
        """Convert configuration to environment variables."""
        env_vars = {}

        # LLM configuration
        llm = self.services.llm
        env_vars["LLM_PROVIDER"] = llm.provider
        env_vars["LLM_MODEL"] = llm.model
        if llm.api_key:
            env_vars["LLM_API_KEY"] = llm.api_key
        if llm.base_url:
            env_vars["LLM_BASE_URL"] = llm.base_url
        env_vars["LLM_TEMPERATURE"] = str(llm.temperature)
        env_vars["LLM_MAX_TOKENS"] = str(llm.max_tokens)

        # Embedding configuration
        emb = self.services.embedding
        env_vars["EMBEDDING_PROVIDER"] = emb.provider
        env_vars["EMBEDDING_MODEL"] = emb.model
        if emb.api_key:
            env_vars["EMBEDDING_API_KEY"] = emb.api_key
        if emb.api_base:
            env_vars["EMBEDDING_API_BASE"] = emb.api_base

        # Reranking configuration
        if self.services.reranking:
            rer = self.services.reranking
            env_vars["RERANKING_ENABLED"] = str(rer.enabled).lower()
            env_vars["RERANKING_PROVIDER"] = rer.provider
            env_vars["RERANKING_MODEL"] = rer.model
            if rer.api_key:
                env_vars["RERANKING_API_KEY"] = rer.api_key

        # Vector store configuration
        vec = self.services.vector_store
        env_vars["VECTOR_STORE_TYPE"] = vec.type
        env_vars["VECTOR_STORE_HOST"] = vec.host
        env_vars["VECTOR_STORE_PORT"] = str(vec.port)

        # Database configuration
        db = self.services.database
        env_vars["DATABASE_TYPE"] = db.type
        if db.type != "sqlite":
            env_vars["DATABASE_HOST"] = db.host
            env_vars["DATABASE_PORT"] = str(db.port)
            env_vars["DATABASE_NAME"] = db.database
            if db.user:
                env_vars["DATABASE_USER"] = db.user
            if db.password:
                env_vars["DATABASE_PASSWORD"] = db.password

        # Cache configuration
        if self.services.cache:
            cache = self.services.cache
            env_vars["CACHE_TYPE"] = cache.type
            if cache.type != "memory":
                env_vars["CACHE_HOST"] = cache.host
                env_vars["CACHE_PORT"] = str(cache.port)
                if cache.password:
                    env_vars["CACHE_PASSWORD"] = cache.password

        # Application configuration
        app = self.application.main_app
        env_vars["APP_HOST"] = app.host
        env_vars["APP_PORT"] = str(app.port)
        env_vars["APP_WORKERS"] = str(app.workers)
        env_vars["ENABLE_STREAMING"] = str(app.enable_streaming).lower()
        env_vars["ENABLE_AGENT"] = str(app.enable_agent).lower()

        # Frontend configuration
        frontend = self.application.frontend
        env_vars["FRONTEND_PORT"] = str(frontend.port)
        env_vars["VITE_API_BASE"] = frontend.api_base

        # Deployment
        env_vars["DEPLOYMENT_TYPE"] = self.deployment.type
        env_vars["ENVIRONMENT"] = self.deployment.environment

        # Logging
        env_vars["LOG_LEVEL"] = self.logging.level
        env_vars["LOG_FORMAT"] = self.logging.format

        return env_vars