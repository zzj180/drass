# Local LLM and Embedding Services Setup

## Overview

This document describes the setup and configuration of local LLM and embedding services for the Drass project, completed on 2025-09-10.

## Services Deployed

### 1. Qwen3-8B-MLX LLM Service (Port 8001)

**Model**: Qwen3-8B-MLX-bf16 (optimized for Apple Silicon)
**Location**: `/Users/arthurren/projects/drass/mlx_qwen3_converted`
**API**: OpenAI-compatible REST API

#### Setup Process:
1. Downloaded Qwen3-8B model using LM Studio
2. Converted from PyTorch to MLX format using `mlx_lm.convert`
3. Created custom Flask API server (`qwen3_api_server.py`)

#### Available Endpoints:
- `GET /v1/models` - List available models
- `POST /v1/completions` - Text completion
- `POST /v1/chat/completions` - Chat completion
- `GET /health` - Health check

#### Start Command:
```bash
python qwen3_api_server.py
```

### 2. Embedding Service (Port 8002)

**Model**: sentence-transformers/all-MiniLM-L6-v2
**Dimension**: 384
**Provider**: Sentence Transformers (local)

#### Setup Process:
1. Created virtual environment in `services/embedding-service`
2. Installed dependencies including sentence-transformers v5.1.0
3. Configured for local model with MPS (Metal Performance Shaders) support

#### Available Endpoints:
- `GET /health` - Service health status
- `POST /embeddings` - Generate embeddings for texts
- `POST /embeddings/batch` - Batch embedding generation
- `GET /models` - List available models

#### Configuration (`services/embedding-service/.env`):
```env
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_SERVICE_PORT=8002
MODEL_CACHE_DIR=./models
```

#### Start Command:
```bash
cd services/embedding-service
source venv/bin/activate
python app.py
```

## Model Conversion Details

### MLX Conversion Process
The Qwen3-8B model was converted from PyTorch format to MLX format for optimal performance on Apple Silicon:

```bash
mlx_lm.convert \
  --hf-path local_model_qwen3 \
  --mlx-path mlx_qwen3_converted \
  --dtype bfloat16
```

This conversion:
- Reduces memory usage
- Improves inference speed on M-series chips
- Maintains model quality with bfloat16 precision

## API Integration

### LLM API Example:
```python
import requests

# Chat completion
response = requests.post(
    "http://localhost:8001/v1/chat/completions",
    json={
        "model": "qwen3-8b-mlx",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "max_tokens": 100
    }
)
```

### Embedding API Example:
```python
import requests

# Generate embeddings
response = requests.post(
    "http://localhost:8002/embeddings",
    json={
        "texts": ["Text to embed", "Another text"]
    }
)
embeddings = response.json()["embeddings"]
```

## Performance Characteristics

### Qwen3-8B-MLX:
- Memory Usage: ~16GB
- Inference Speed: Fast on Apple Silicon
- Context Length: 8192 tokens
- Language Support: Multilingual (strong in Chinese and English)

### Embedding Service:
- Model Size: ~80MB (all-MiniLM-L6-v2)
- Embedding Speed: <100ms for batch of 10 texts
- Dimension: 384 (compact but effective)
- GPU Acceleration: Enabled via MPS

## Troubleshooting

### Common Issues Resolved:

1. **MLX-LM Server Path Restrictions**:
   - Issue: MLX server requires relative paths
   - Solution: Created custom Flask API server

2. **Sentence Transformers Compatibility**:
   - Issue: Version 2.2.2 incompatible with latest huggingface_hub
   - Solution: Upgraded to sentence-transformers 5.1.0

3. **Model Format Mismatch**:
   - Issue: LM Studio downloads PyTorch format
   - Solution: Converted to MLX format using mlx_lm.convert

## Service Management

### Check Service Status:
```bash
# LLM Service
curl http://localhost:8001/health

# Embedding Service
curl http://localhost:8002/health
```

### Stop Services:
```bash
# Find and kill processes
lsof -i :8001  # Find LLM service PID
lsof -i :8002  # Find embedding service PID
kill <PID>     # Stop service
```

## Future Improvements

1. **Production Deployment**:
   - Use WSGI server (gunicorn) instead of development server
   - Add systemd service files for automatic startup
   - Implement proper logging and monitoring

2. **Model Options**:
   - Switch back to BAAI/bge-large-zh-v1.5 for better Chinese support
   - Consider adding reranking models
   - Explore quantization for reduced memory usage

3. **Performance Optimization**:
   - Implement request batching
   - Add Redis caching for embeddings
   - Use connection pooling for API clients

## References

- [MLX Documentation](https://github.com/ml-explore/mlx)
- [Sentence Transformers](https://www.sbert.net/)
- [Qwen Model Cards](https://huggingface.co/Qwen)
- [Drass Embedding Service Deployment Guide](./EMBEDDING_SERVICE_DEPLOYMENT.md)