# Embedding服务部署指南

## 概述

Embedding服务将文本转换为向量表示，是RAG（检索增强生成）系统的核心组件。本服务支持多种embedding模型和部署方式。

## 快速部署方案

### 方案1: 使用OpenAI Embedding（最简单）

如果已配置OpenAI API，无需单独部署Embedding服务。

**配置.env：**
```bash
# 复用OpenAI配置
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=${OPENAI_API_KEY}  # 复用OpenAI密钥
```

**优点：**
- 无需部署额外服务
- 高质量embedding
- 支持多语言

**缺点：**
- 需要付费（$0.02/1M tokens）
- 有网络延迟

### 方案2: 本地Sentence Transformers（推荐）

部署本地embedding服务，使用开源模型。

#### 步骤1: 安装依赖

```bash
cd services/embedding-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 步骤2: 配置环境变量

```bash
# .env 文件
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5  # 中文推荐
# EMBEDDING_MODEL=BAAI/bge-large-en-v1.5  # 英文推荐
EMBEDDING_SERVICE_PORT=8001
MODEL_CACHE_DIR=./models
```

#### 步骤3: 启动服务

```bash
# 直接运行
python app.py

# 或使用uvicorn
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

服务将在 http://localhost:8001 启动

#### 步骤4: 验证服务

```bash
# 健康检查
curl http://localhost:8001/health

# 测试embedding
curl -X POST "http://localhost:8001/embeddings" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["测试文本", "另一个测试"]
  }'
```

### 方案3: Docker部署（生产推荐）

#### 步骤1: 构建镜像

```bash
cd services/embedding-service
docker build -t drass-embedding-service .
```

#### 步骤2: 运行容器

```bash
# CPU版本
docker run -d \
  --name embedding-service \
  -p 8001:8001 \
  -v $(pwd)/models:/app/models \
  -e EMBEDDING_PROVIDER=sentence-transformers \
  -e EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5 \
  drass-embedding-service

# GPU版本（需要nvidia-docker）
docker run -d \
  --gpus all \
  --name embedding-service \
  -p 8001:8001 \
  -v $(pwd)/models:/app/models \
  -e EMBEDDING_PROVIDER=sentence-transformers \
  -e EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5 \
  drass-embedding-service
```

#### 步骤3: 集成到docker-compose

添加到 `docker-compose.yml`：

```yaml
services:
  embedding-service:
    build: ./services/embedding-service
    container_name: drass-embedding
    ports:
      - "8001:8001"
    environment:
      - EMBEDDING_PROVIDER=sentence-transformers
      - EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
    volumes:
      - ./data/models:/app/models
    networks:
      - drass-network
    restart: unless-stopped
```

### 方案4: 使用Cohere Embedding

Cohere提供高质量的embedding服务。

**配置：**
```bash
# .env
EMBEDDING_PROVIDER=cohere
EMBEDDING_MODEL=embed-multilingual-v3.0
COHERE_API_KEY=your_cohere_api_key
```

**获取API Key：**
1. 访问 https://cohere.ai
2. 注册账号
3. 在Dashboard创建API Key

## 模型选择指南

### 中文场景推荐

| 模型 | 维度 | 速度 | 质量 | 内存 |
|------|------|------|------|------|
| BAAI/bge-large-zh-v1.5 | 1024 | 中 | 高 | 1.3GB |
| BAAI/bge-base-zh-v1.5 | 768 | 快 | 中 | 400MB |
| text-embedding-3-small | 1536 | 快 | 高 | API |

### 英文场景推荐

| 模型 | 维度 | 速度 | 质量 | 内存 |
|------|------|------|------|------|
| BAAI/bge-large-en-v1.5 | 1024 | 中 | 高 | 1.3GB |
| all-mpnet-base-v2 | 768 | 快 | 中 | 420MB |
| text-embedding-3-small | 1536 | 快 | 高 | API |

### 多语言场景

| 模型 | 维度 | 语言支持 | 质量 |
|------|------|----------|------|
| embed-multilingual-v3.0 | 1024 | 100+ | 高 |
| multilingual-e5-large | 1024 | 100+ | 高 |
| text-embedding-3-large | 3072 | 多语言 | 最高 |

## 性能优化

### 1. 批处理

```python
# 批量处理提高效率
texts = ["文本1", "文本2", ..., "文本100"]
response = requests.post(
    "http://localhost:8001/embeddings",
    json={"texts": texts}
)
```

### 2. 缓存策略

在主应用中实现缓存：

```python
import hashlib
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_embedding_with_cache(text):
    # 生成缓存key
    cache_key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
    
    # 尝试从缓存获取
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 调用embedding服务
    response = requests.post(
        "http://localhost:8001/embeddings",
        json={"texts": [text]}
    )
    embedding = response.json()["embeddings"][0]
    
    # 存入缓存（24小时）
    redis_client.setex(
        cache_key, 
        86400, 
        json.dumps(embedding)
    )
    
    return embedding
```

### 3. GPU加速

如果有GPU，安装CUDA版本的PyTorch：

```bash
# CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### 4. 模型量化

使用量化模型减少内存占用：

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
model.half()  # FP16量化
```

## 集成到主应用

### 1. 更新主应用配置

`services/main-app/app/core/config.py`:

```python
class Settings(BaseSettings):
    # Embedding服务配置
    embedding_service_url: str = "http://localhost:8001"
    use_embedding_service: bool = True
```

### 2. 创建Embedding客户端

`services/main-app/app/services/embedding_client.py`:

```python
import httpx
from typing import List

class EmbeddingClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json={"texts": texts}
            )
            return response.json()["embeddings"]
```

### 3. 在RAG链中使用

```python
from langchain.embeddings.base import Embeddings

class CustomEmbeddings(Embeddings):
    def __init__(self, embedding_service_url: str):
        self.client = EmbeddingClient(embedding_service_url)
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return asyncio.run(self.client.get_embeddings(texts))
        
    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]
```

## 监控和维护

### 健康检查

```bash
# 添加到监控脚本
curl -f http://localhost:8001/health || exit 1
```

### 日志查看

```bash
# Docker日志
docker logs embedding-service -f

# 本地日志
tail -f embedding_service.log
```

### 性能指标

访问 http://localhost:8001/docs 查看API文档和测试接口

## 故障排查

### 问题1: 模型下载失败

**解决方案：**
```bash
# 手动下载模型
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
model.save('./models/bge-large-zh-v1.5')
```

### 问题2: 内存不足

**解决方案：**
- 使用更小的模型（如bge-base）
- 减少批处理大小
- 使用API服务而非本地模型

### 问题3: 速度太慢

**解决方案：**
- 启用GPU加速
- 使用更快的模型
- 实现结果缓存
- 增加服务实例

## 成本对比

| 方案 | 月成本估算 | 适用场景 |
|------|------------|----------|
| OpenAI API | $10-50 | 小规模，快速原型 |
| 本地CPU | $0 | 中等规模，成本敏感 |
| 本地GPU | $0-100 | 大规模，高性能 |
| Cohere API | $20-100 | 多语言，高质量 |

## 下一步

1. 选择合适的部署方案
2. 配置环境变量
3. 启动Embedding服务
4. 集成到主应用
5. 测试RAG功能