# LM Studio Deployment Guide

## Overview

This guide documents the deployment and configuration of LM Studio as the local LLM provider for the Drass Compliance Assistant, replacing Ollama with a more user-friendly interface.

## Why LM Studio?

LM Studio provides several advantages over Ollama:
- **Better UI Control**: Full graphical interface for model management
- **OpenAI API Compatibility**: Drop-in replacement for OpenAI API
- **Model Management**: Easy download, switching, and configuration
- **Performance Monitoring**: Built-in metrics and monitoring
- **No Command Line Required**: Everything manageable through GUI

## Model Configuration

### Selected Model: Qwen2.5-8B-Instruct

- **Model**: Qwen2.5-8B-Instruct-GGUF
- **Precision**: bfloat16 (bf16)
- **Size**: ~16GB
- **Context Length**: 32,768 tokens
- **RAM Required**: 16GB minimum
- **Features**: 
  - Excellent Chinese/English support
  - Strong instruction following
  - Optimized for compliance tasks

### Alternative Models

For systems with limited resources:

1. **Qwen2.5-7B-Instruct** (Q8_0)
   - Size: ~8GB
   - RAM: 12GB minimum

2. **Qwen2.5-3B-Instruct** (Q8_0)
   - Size: ~3GB
   - RAM: 8GB minimum

## Installation Steps

### 1. Install LM Studio

```bash
# macOS - Download from website
open https://lmstudio.ai

# Or check if already installed
ls -la "/Applications/LM Studio.app"
```

### 2. Run Deployment Script

```bash
# Navigate to project root
cd /Users/arthurren/projects/drass

# Run the deployment script
./scripts/deploy_lmstudio.sh
```

This script will:
- Check LM Studio installation
- Create configuration files
- Set up Python integration
- Generate test scripts

### 3. Download Model in LM Studio

1. Open LM Studio application
2. Go to **"Discover"** tab
3. Search for: `Qwen2.5-8B-Instruct-GGUF`
4. Download variant: `qwen2.5-8b-instruct-bf16.gguf`
5. Wait for download to complete (~16GB)

### 4. Start Local Server

1. Go to **"Local Server"** tab in LM Studio
2. Select the downloaded Qwen2.5-8B model
3. Configure settings:
   - **Port**: 1234
   - **Context Length**: 32768
   - **GPU Layers**: -1 (use all)
   - **Temperature**: 0.7
   - **Threads**: 8
4. Click **"Start Server"**

### 5. Verify Connection

```bash
# Test API endpoint
curl http://localhost:1234/v1/models

# Run integration test
python3 test_lmstudio_integration.py
```

## Configuration Files

### Environment Configuration (.env.local)

```env
# LM Studio Configuration
LLM_PROVIDER=openai  # LM Studio uses OpenAI-compatible API
LLM_MODEL=qwen2.5-8b
LLM_API_KEY=not-required
LLM_BASE_URL=http://localhost:1234/v1
LLM_CONTEXT_LENGTH=32768
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Performance Settings
THREADS=8
GPU_LAYERS=-1
BATCH_SIZE=512
USE_MLOCK=true
USE_MMAP=true
```

### Backend Configuration Updates

The backend has been updated to recognize LM Studio:

```python
# services/main-app/app/core/config.py
LLM_PROVIDER: str = "openai"  # LM Studio uses OpenAI API
LLM_BASE_URL: str = "http://localhost:1234/v1"
LLM_API_KEY: str = "not-required"
```

### RAG Chain Updates

The RAG chain now supports LM Studio through OpenAI-compatible interface:

```python
# services/main-app/app/chains/compliance_rag_chain.py
elif settings.LLM_PROVIDER == "openai":
    # LM Studio uses OpenAI-compatible API
    return ChatOpenAI(
        model_name=settings.LLM_MODEL,
        openai_api_key="not-required",
        openai_api_base="http://localhost:1234/v1",
        ...
    )
```

## Python Integration

### Using LM Studio Client

```python
from lmstudio_client import LMStudioClient

# Create client
client = LMStudioClient(
    base_url="http://localhost:1234/v1",
    model="qwen2.5-8b"
)

# Regular chat
response = client.chat([
    {"role": "system", "content": "You are a compliance assistant."},
    {"role": "user", "content": "What is GDPR?"}
])

# Streaming
for chunk in client.stream_chat(messages):
    print(chunk, end="", flush=True)
```

### LangChain Integration

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="qwen2.5-8b",
    openai_api_key="not-required",
    openai_api_base="http://localhost:1234/v1",
    temperature=0.7,
    streaming=True
)
```

## Testing

### Quick Test

```bash
# Test LM Studio connection
python3 test_lmstudio.py
```

### Integration Test

```bash
# Full integration test
python3 test_lmstudio_integration.py
```

Expected output:
```
✓ LM Studio server is running
✓ OpenAI API compatibility confirmed
✓ Streaming response received
✓ LangChain integration successful
✓ RAG chain with LM Studio works
✓ Performance metrics collected
```

## Performance Optimization

### GPU Acceleration

For Apple Silicon Macs:
- LM Studio automatically uses Metal Performance Shaders
- Set `gpu_layers: -1` to use all available GPU

### Memory Management

```json
{
  "use_mlock": true,  // Lock model in RAM
  "use_mmap": true,   // Memory-mapped files
  "threads": 8,       // CPU threads
  "batch_size": 512   // Processing batch size
}
```

### Context Window

- Default: 32,768 tokens
- Can be reduced for faster response
- Adjust based on document size

## Troubleshooting

### LM Studio Not Starting

```bash
# Check if port is in use
lsof -i :1234

# Kill process if needed
kill -9 <PID>
```

### Model Not Loading

1. Check available RAM (need 16GB+ free)
2. Try smaller quantization (Q5_K_M instead of bf16)
3. Reduce context length to 16384

### Slow Response

1. Reduce `max_tokens` in requests
2. Lower context window size
3. Use smaller model (7B or 3B)

### API Connection Failed

```bash
# Verify server is running
curl http://localhost:1234/v1/models

# Check firewall settings
sudo pfctl -s rules | grep 1234
```

## Migration from Ollama

### Key Differences

| Feature | Ollama | LM Studio |
|---------|--------|-----------|
| API | Custom | OpenAI-compatible |
| UI | Terminal only | Full GUI |
| Model Format | GGUF | GGUF |
| Port | 11434 | 1234 |
| API Key | Not required | Not required |

### Configuration Changes

1. Update `.env.local`:
   - Change `LLM_PROVIDER` from `ollama` to `openai`
   - Change port from 11434 to 1234
   - Update model name format

2. Update code references:
   - Replace Ollama client with OpenAI client
   - Update base URL to LM Studio endpoint

## Monitoring

### Built-in Metrics

LM Studio provides:
- Token usage per request
- Response time tracking
- GPU/CPU utilization
- Memory usage

### API Metrics

```python
# Get usage statistics
response = requests.get("http://localhost:1234/v1/usage")
print(response.json())
```

## Production Considerations

### Systemd Service (Linux)

```ini
[Unit]
Description=LM Studio Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/opt/lmstudio
ExecStart=/opt/lmstudio/lms serve --port 1234
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker Deployment

```dockerfile
# Dockerfile for LM Studio (conceptual)
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://lmstudio.ai/install.sh | sh
EXPOSE 1234
CMD ["lms", "serve", "--port", "1234"]
```

## Next Steps

1. **Start Services**:
   ```bash
   # Start all backend services
   ./scripts/start_all_services.sh
   ```

2. **Run Tests**:
   ```bash
   # Full test suite
   ./run_all_tests.sh
   ```

3. **Access Application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - LM Studio: http://localhost:1234

## Support

For issues with LM Studio:
- Documentation: https://lmstudio.ai/docs
- Community: https://discord.gg/lmstudio
- GitHub: https://github.com/lmstudio-ai

For Drass-specific issues:
- Check `GAP_ANALYSIS_REPORT.md`
- Review `TASK_LIST_LANGCHAIN.md`
- See `docs/LANGCHAIN_COMPLIANCE_ASSISTANT_DESIGN.md`