# Drass Deployment Configuration System

A flexible deployment configuration system supporting multiple deployment scenarios including AWS, Docker Compose, and local GPU deployments.

## Quick Start

```bash
# Interactive configuration wizard
python deployment/scripts/configure.py

# Deploy with existing configuration
python deployment/scripts/deploy.py --config deployment/configs/user/my-config.yaml

# Validate configuration
python deployment/scripts/validate.py --config deployment/configs/user/my-config.yaml
```

## Supported Deployment Scenarios

### 1. Docker Compose (Local Development)
- Complete containerized environment
- All services in Docker containers
- Ideal for development and testing

### 2. Local GPU (Production with Hardware Acceleration)
- Utilizes local GPU resources (Apple Silicon MLX or NVIDIA CUDA)
- Native performance for AI models
- Optimized for edge deployments

### 3. AWS (Cloud Production)
- ECS/EC2 deployment
- Auto-scaling support
- Managed services integration (RDS, ElastiCache)

## Directory Structure

```
deployment/
├── configs/           # Configuration files
│   ├── templates/    # Base templates for different scenarios
│   ├── presets/      # Pre-configured scenarios
│   ├── user/         # User-specific configurations
│   └── examples/     # Example configurations
├── scripts/          # Deployment scripts
│   ├── configure.py  # Interactive configuration wizard
│   ├── deploy.py     # Unified deployment script
│   ├── validate.py   # Configuration validator
│   └── utils/        # Utility modules
├── schemas/          # YAML schemas for validation
└── docs/            # Documentation
```

## Configuration Workflow

1. **Generate Configuration**
   ```bash
   python deployment/scripts/configure.py
   ```
   - Interactive wizard guides through options
   - Hardware auto-detection and recommendations
   - Saves configuration to `configs/user/`

2. **Validate Configuration**
   ```bash
   python deployment/scripts/validate.py --config your-config.yaml
   ```
   - Schema validation
   - Dependency checking
   - Resource availability verification

3. **Deploy Application**
   ```bash
   python deployment/scripts/deploy.py --config your-config.yaml
   ```
   - Automated deployment based on configuration
   - Health checking
   - Rollback support

## Configuration Options

### Core Services
- **API Backend** - FastAPI application
- **Frontend** - React application
- **LLM Service** - Language model provider
- **Embedding Service** - Text embeddings
- **Reranking Service** - Document reranking
- **Vector Store** - Vector database
- **Database** - PostgreSQL
- **Cache** - Redis

### LLM Providers
- OpenRouter (Cloud)
- OpenAI API
- Local MLX (Apple Silicon)
- vLLM (NVIDIA GPU)
- Ollama (Multiple models)

### Storage Options
- **Vector Stores**: ChromaDB, Weaviate, Pinecone, Qdrant
- **Databases**: PostgreSQL, MySQL
- **Cache**: Redis, Memcached

## Environment Variables

The system automatically generates appropriate `.env` files based on your configuration:

```bash
# Generated .env example
LLM_PROVIDER=openrouter
LLM_MODEL=gpt-4
LLM_API_KEY=your-api-key
EMBEDDING_PROVIDER=local
VECTOR_STORE_TYPE=chromadb
DATABASE_URL=postgresql://user:pass@localhost/drass
REDIS_URL=redis://localhost:6379
```

## Examples

### Minimal Local Development
```bash
python deployment/scripts/configure.py --preset minimal
python deployment/scripts/deploy.py --config configs/user/minimal.yaml
```

### Production with Local GPU
```bash
python deployment/scripts/configure.py --preset local-gpu
python deployment/scripts/deploy.py --config configs/user/local-gpu.yaml
```

### AWS Deployment
```bash
python deployment/scripts/configure.py --preset aws
python deployment/scripts/deploy.py --config configs/user/aws.yaml --environment production
```

## Health Checking

All deployments include automatic health checking:

```bash
# Check service health
python deployment/scripts/health_check.py --config your-config.yaml

# Monitor deployment
python deployment/scripts/monitor.py --config your-config.yaml
```

## Rollback

If deployment fails, automatic rollback is triggered:

```bash
# Manual rollback
python deployment/scripts/rollback.py --config your-config.yaml --version previous
```

## Troubleshooting

See `deployment/docs/troubleshooting.md` for common issues and solutions.

## Contributing

1. Add new deployment scenarios in `configs/templates/`
2. Implement deployers in `scripts/deployers/`
3. Update schema in `schemas/config-schema.yaml`
4. Add tests in `tests/`

## License

See LICENSE file in the root directory.