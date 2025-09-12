# Reranking Service

A high-performance document reranking service using cross-encoder models for improved search relevance.

## Overview

This service provides document reranking capabilities using state-of-the-art cross-encoder models. It takes a query and a list of documents, then reorders them based on their relevance to the query, significantly improving search result quality.

## Features

- **Multiple Model Support**: Supports various cross-encoder models including BGE-reranker and MS-MARCO models
- **High Performance**: Batch processing, caching, and GPU acceleration support
- **RESTful API**: Simple HTTP API with comprehensive documentation
- **Score Normalization**: Optional score normalization to [0, 1] range
- **Batch Processing**: Process multiple queries in a single request
- **Metrics & Monitoring**: Prometheus metrics for monitoring performance
- **Caching**: Built-in caching for improved performance on repeated queries
- **Health Checks**: Comprehensive health check endpoints

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t reranking-service .

# Run the service
docker run -p 8002:8002 reranking-service
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python app.py
```

The service will be available at `http://localhost:8002`

## API Endpoints

### Rerank Documents

**POST** `/rerank`

Rerank documents based on relevance to a query.

```json
{
  "query": "What are the GDPR requirements for data retention?",
  "documents": [
    "GDPR requires data to be kept for no longer than necessary.",
    "Data retention policies must be clearly defined.",
    "Personal data should be deleted after the retention period."
  ],
  "top_k": 2,
  "normalize_scores": false
}
```

Response:
```json
{
  "reranked_documents": [
    "GDPR requires data to be kept for no longer than necessary.",
    "Data retention policies must be clearly defined."
  ],
  "scores": [0.95, 0.87],
  "indices": [0, 1],
  "processing_time_ms": 125.5
}
```

### Batch Rerank

**POST** `/batch_rerank`

Process multiple queries with their respective documents.

```json
{
  "queries": ["query1", "query2"],
  "documents_list": [
    ["doc1", "doc2"],
    ["doc3", "doc4", "doc5"]
  ],
  "top_k": 2
}
```

### Health Check

**GET** `/health`

Check service health and get cache statistics.

### Model Information

**GET** `/models`

Get information about available and loaded models.

### Clear Cache

**POST** `/clear_cache`

Clear the reranker cache to free memory.

### Metrics

**GET** `/metrics`

Prometheus metrics endpoint for monitoring.

## Configuration

The service can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Service host | 0.0.0.0 |
| `PORT` | Service port | 8002 |
| `MODEL_NAME` | Cross-encoder model to use | BAAI/bge-reranker-large |
| `DEVICE` | Device to run model on (cuda/cpu/mps) | cpu |
| `MAX_LENGTH` | Maximum sequence length | 512 |
| `BATCH_SIZE` | Batch size for processing | 32 |
| `DEFAULT_TOP_K` | Default number of top documents | 10 |
| `MAX_DOCUMENTS` | Maximum documents per request | 100 |
| `CACHE_ENABLED` | Enable result caching | true |
| `CACHE_TTL` | Cache time-to-live in seconds | 3600 |
| `REDIS_URL` | Redis URL for distributed caching | None |
| `ENABLE_METRICS` | Enable Prometheus metrics | true |

## Supported Models

The service supports the following pre-trained models:

1. **BAAI/bge-reranker-large** (Default)
   - High accuracy, slower performance
   - Best for production use with GPU

2. **BAAI/bge-reranker-base**
   - Balanced accuracy and speed
   - Good for most use cases

3. **BAAI/bge-reranker-v2-m3**
   - Multilingual support
   - Supports longer contexts (up to 8192 tokens)

4. **cross-encoder/ms-marco-MiniLM-L-12-v2**
   - Fast inference
   - Good for English documents

5. **cross-encoder/ms-marco-electra-base**
   - High quality for English
   - Better accuracy than MiniLM

## Performance Optimization

### GPU Acceleration

For production use, GPU acceleration is highly recommended:

```bash
docker run --gpus all -p 8002:8002 -e DEVICE=cuda reranking-service
```

### Caching

The service includes built-in caching. For distributed caching, configure Redis:

```bash
docker run -p 8002:8002 \
  -e REDIS_URL=redis://redis:6379 \
  reranking-service
```

### Batch Processing

For better throughput, use the batch endpoint when processing multiple queries:

```python
import requests

response = requests.post(
    "http://localhost:8002/batch_rerank",
    json={
        "queries": queries,
        "documents_list": documents_list,
        "top_k": 5
    }
)
```

## Testing

Run the test suite:

```bash
# Unit tests
pytest tests/test_reranking.py -v

# Integration tests
pytest tests/test_integration.py -v

# All tests with coverage
pytest --cov=. --cov-report=html
```

## Monitoring

The service exposes Prometheus metrics at `/metrics`:

- `rerank_requests_total`: Total number of rerank requests
- `rerank_duration_seconds`: Time spent processing requests
- `documents_processed_total`: Total documents processed
- `model_load_time_seconds`: Model loading time
- `cache_hit_rate`: Cache hit rate percentage

## Docker Compose Integration

Add to your `docker-compose.yml`:

```yaml
reranking-service:
  build: ./services/reranking-service
  container_name: reranking-service
  ports:
    - "8002:8002"
  environment:
    - MODEL_NAME=BAAI/bge-reranker-large
    - DEVICE=cpu
    - BATCH_SIZE=32
    - CACHE_ENABLED=true
  volumes:
    - ./models:/app/models
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`

## License

This service is part of the LangChain Compliance Assistant project.