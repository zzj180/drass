"""
Pydantic models for deployment configuration validation
"""
from typing import Dict, List, Optional, Union, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator
import re


class DeploymentType(str, Enum):
    """Deployment target types"""
    DOCKER_COMPOSE = "docker-compose"
    LOCAL_GPU = "local-gpu"
    AWS = "aws"
    KUBERNETES = "kubernetes"


class Environment(str, Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProvider(str, Enum):
    """LLM service providers"""
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    LOCAL_MLX = "local-mlx"
    VLLM = "vllm"
    OLLAMA = "ollama"
    AZURE = "azure"


class EmbeddingProvider(str, Enum):
    """Embedding service providers"""
    OPENAI = "openai"
    COHERE = "cohere"
    LOCAL = "local"
    SENTENCE_TRANSFORMERS = "sentence-transformers"


class VectorStoreProvider(str, Enum):
    """Vector store providers"""
    CHROMADB = "chromadb"
    WEAVIATE = "weaviate"
    PINECONE = "pinecone"
    QDRANT = "qdrant"
    MILVUS = "milvus"


class DatabaseProvider(str, Enum):
    """Database providers"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"


class CacheProvider(str, Enum):
    """Cache providers"""
    REDIS = "redis"
    MEMCACHED = "memcached"
    DYNAMODB = "dynamodb"


class ResourceSpec(BaseModel):
    """Resource specification"""
    request: Optional[str] = Field(None, description="Minimum required resources")
    limit: Optional[str] = Field(None, description="Maximum allowed resources")


class GPUSpec(BaseModel):
    """GPU specification"""
    enabled: bool = Field(False, description="Enable GPU support")
    type: Optional[Literal["nvidia", "amd", "apple-silicon", "intel"]] = None
    count: int = Field(1, ge=0, description="Number of GPUs")
    memory: Optional[str] = Field(None, pattern=r"^\d+(G|Gi)$", description="GPU memory")


class StorageSpec(BaseModel):
    """Storage specification"""
    size: str = Field(..., pattern=r"^\d+(G|Gi|T|Ti)$", description="Storage size")
    type: Literal["ssd", "hdd", "nvme", "efs", "ebs"] = "ssd"
    iops: Optional[int] = Field(None, description="IOPS for cloud storage")
    encryption: bool = True


class HealthCheck(BaseModel):
    """Health check configuration"""
    enabled: bool = True
    path: str = "/health"
    interval: int = Field(30, ge=1, description="Check interval in seconds")
    timeout: int = Field(5, ge=1, description="Check timeout in seconds")
    retries: int = Field(3, ge=1, description="Number of retries")


class ServiceResources(BaseModel):
    """Service resource allocation"""
    cpu: Optional[str] = Field(None, pattern=r"^\d+(\.\d+)?$", description="CPU cores")
    memory: Optional[str] = Field(None, pattern=r"^\d+(M|G|Mi|Gi)$", description="Memory allocation")


class BaseService(BaseModel):
    """Base service configuration"""
    enabled: bool = True
    image: Optional[str] = None
    version: str = "latest"
    replicas: int = Field(1, ge=0)
    port: Optional[int] = Field(None, ge=1, le=65535)
    environment: Dict[str, str] = Field(default_factory=dict)
    resources: Optional[ServiceResources] = None
    health_check: Optional[HealthCheck] = None


class LLMService(BaseService):
    """LLM service configuration"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(2048, ge=1)
    gpu_layers: Optional[int] = Field(None, ge=0, description="Layers to offload to GPU")
    quantization: Optional[Literal["none", "int8", "int4", "fp16", "bf16"]] = None

    @validator("api_key")
    def validate_api_key(cls, v, values):
        """Validate API key requirement based on provider"""
        provider = values.get("provider")
        if provider in [LLMProvider.OPENROUTER, LLMProvider.OPENAI, LLMProvider.AZURE]:
            if not v:
                raise ValueError(f"API key required for {provider}")
        return v


class EmbeddingService(BaseService):
    """Embedding service configuration"""
    provider: EmbeddingProvider
    model: str = "text-embedding-ada-002"
    api_key: Optional[str] = None
    batch_size: int = Field(100, ge=1)
    dimensions: Optional[int] = Field(None, ge=1)


class RerankingService(BaseService):
    """Reranking service configuration"""
    provider: Literal["cohere", "local", "cross-encoder"]
    model: Optional[str] = None
    api_key: Optional[str] = None
    top_k: int = Field(10, ge=1)


class ConnectionConfig(BaseModel):
    """Database/service connection configuration"""
    host: str
    port: int = Field(..., ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    api_key: Optional[str] = None
    index_name: Optional[str] = None


class VectorStoreService(BaseService):
    """Vector store service configuration"""
    provider: VectorStoreProvider
    connection: Optional[ConnectionConfig] = None
    persistence: Optional[Dict] = Field(
        default_factory=lambda: {"enabled": True, "path": "./data/vector_store"}
    )


class PoolConfig(BaseModel):
    """Database connection pool configuration"""
    min_connections: int = Field(2, ge=1)
    max_connections: int = Field(10, ge=1)

    @validator("max_connections")
    def validate_max_connections(cls, v, values):
        """Ensure max >= min connections"""
        min_conn = values.get("min_connections", 2)
        if v < min_conn:
            raise ValueError(f"max_connections ({v}) must be >= min_connections ({min_conn})")
        return v


class DatabaseService(BaseService):
    """Database service configuration"""
    provider: DatabaseProvider
    connection: ConnectionConfig
    pool: Optional[PoolConfig] = None


class CacheService(BaseService):
    """Cache service configuration"""
    provider: CacheProvider
    connection: Optional[ConnectionConfig] = None
    ttl: int = Field(3600, ge=1, description="Default TTL in seconds")


class Services(BaseModel):
    """All service configurations"""
    api: Optional[BaseService] = None
    frontend: Optional[BaseService] = None
    llm: Optional[LLMService] = None
    embedding: Optional[EmbeddingService] = None
    reranking: Optional[RerankingService] = None
    vector_store: Optional[VectorStoreService] = None
    database: Optional[DatabaseService] = None
    cache: Optional[CacheService] = None


class DeploymentConfig(BaseModel):
    """Deployment target configuration"""
    type: DeploymentType
    name: str = Field(..., pattern=r"^[a-z0-9-]+$", description="Deployment name")
    environment: Environment = Environment.DEVELOPMENT
    region: Optional[str] = None
    profile: Optional[str] = None


class EnvironmentConfig(BaseModel):
    """Environment variables and secrets configuration"""
    variables: Dict[str, str] = Field(default_factory=dict)
    secrets: Dict[str, str] = Field(default_factory=dict)
    files: List[str] = Field(default_factory=list, description="Additional .env files")


class ResourcesConfig(BaseModel):
    """Resource allocation configuration"""
    cpu: Optional[ResourceSpec] = None
    memory: Optional[ResourceSpec] = None
    gpu: Optional[GPUSpec] = None
    storage: Optional[StorageSpec] = None


class LoadBalancerConfig(BaseModel):
    """Load balancer configuration"""
    enabled: bool = False
    type: Optional[Literal["alb", "nlb", "nginx", "traefik"]] = None


class NetworkingConfig(BaseModel):
    """Network configuration"""
    ports: Dict[str, int] = Field(default_factory=dict)
    domain: Optional[str] = None
    ssl: bool = False
    load_balancer: Optional[LoadBalancerConfig] = None


class ScalingConfig(BaseModel):
    """Auto-scaling configuration"""
    enabled: bool = False
    min_instances: int = Field(1, ge=1)
    max_instances: int = Field(10, ge=1)
    target_cpu: float = Field(70, ge=0, le=100)

    @validator("max_instances")
    def validate_max_instances(cls, v, values):
        """Ensure max >= min instances"""
        min_inst = values.get("min_instances", 1)
        if v < min_inst:
            raise ValueError(f"max_instances ({v}) must be >= min_instances ({min_inst})")
        return v


class MonitoringConfig(BaseModel):
    """Monitoring and logging configuration"""
    enabled: bool = True
    providers: List[Literal["prometheus", "grafana", "cloudwatch", "datadog", "newrelic"]] = Field(
        default_factory=list
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


class FirewallRule(BaseModel):
    """Firewall rule configuration"""
    port: int = Field(..., ge=1, le=65535)
    protocol: Literal["tcp", "udp"] = "tcp"
    source: str = "0.0.0.0/0"


class SecurityConfig(BaseModel):
    """Security configuration"""
    encryption: bool = True
    secrets_manager: Optional[Literal["aws-secrets", "vault", "local", "kubernetes"]] = "local"
    firewall_rules: List[FirewallRule] = Field(default_factory=list)


class DeploymentConfiguration(BaseModel):
    """Complete deployment configuration"""
    deployment: DeploymentConfig
    services: Services
    environment: EnvironmentConfig
    resources: Optional[ResourcesConfig] = None
    networking: Optional[NetworkingConfig] = None
    scaling: Optional[ScalingConfig] = None
    monitoring: Optional[MonitoringConfig] = None
    security: Optional[SecurityConfig] = None

    @root_validator
    def validate_deployment_requirements(cls, values):
        """Validate deployment-specific requirements"""
        deployment = values.get("deployment")
        if not deployment:
            return values

        deployment_type = deployment.type
        services = values.get("services", Services())

        # AWS deployment requires certain configurations
        if deployment_type == DeploymentType.AWS:
            if not deployment.region:
                raise ValueError("AWS deployment requires 'region' to be specified")

        # Local GPU deployment requires GPU configuration
        if deployment_type == DeploymentType.LOCAL_GPU:
            resources = values.get("resources")
            if not resources or not resources.gpu or not resources.gpu.enabled:
                raise ValueError("Local GPU deployment requires GPU to be enabled in resources")

        # Kubernetes deployment requires scaling configuration
        if deployment_type == DeploymentType.KUBERNETES:
            if not values.get("scaling"):
                values["scaling"] = ScalingConfig(enabled=True)

        return values

    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"

    def to_yaml(self) -> str:
        """Convert configuration to YAML string"""
        import yaml
        return yaml.dump(
            self.dict(exclude_none=True, exclude_unset=True),
            default_flow_style=False,
            sort_keys=False
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "DeploymentConfiguration":
        """Create configuration from YAML string"""
        import yaml
        data = yaml.safe_load(yaml_str)
        return cls(**data)

    @classmethod
    def from_file(cls, file_path: str) -> "DeploymentConfiguration":
        """Load configuration from YAML file"""
        with open(file_path, "r") as f:
            return cls.from_yaml(f.read())

    def save(self, file_path: str) -> None:
        """Save configuration to YAML file"""
        with open(file_path, "w") as f:
            f.write(self.to_yaml())

    def validate_completeness(self) -> List[str]:
        """Check if all required services are configured"""
        warnings = []

        if not self.services.llm:
            warnings.append("LLM service not configured")

        if not self.services.database:
            warnings.append("Database service not configured")

        if not self.services.vector_store:
            warnings.append("Vector store service not configured")

        if self.deployment.environment == Environment.PRODUCTION:
            if not self.monitoring or not self.monitoring.enabled:
                warnings.append("Monitoring not enabled for production environment")

            if not self.security or not self.security.encryption:
                warnings.append("Encryption not enabled for production environment")

            if not self.scaling or not self.scaling.enabled:
                warnings.append("Auto-scaling not enabled for production environment")

        return warnings