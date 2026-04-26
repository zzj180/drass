# Drass 部署工具与基础架构分析

## 一、部署工具分析

### 1.1 核心部署工具

| 工具 | 用途 | 版本 |
|------|------|------|
| **Docker Compose** | 容器编排与服务编排 | 最新 |
| **Shell 脚本** | 自动化部署流程 | Bash |
| **Python** | 部署配置与脚本 | 3.8+ |
| **Nginx** | 反向代理与负载均衡 | Alpine |

### 1.2 可选部署工具

```mermaid
flowchart LR
    subgraph DeployTools["部署工具集"]
        DOCKER[Docker Compose<br/>容器编排]
        SCRIPT[Shell 脚本<br/>自动化]
        PYTHON[Python<br/>配置管理]
        NGINX[Nginx<br/>反向代理]
        AWS[AWS CLI<br/>云端部署]
        K8S[Kubernetes<br/>生产部署]
    end
    
    subgraph Optional["可选组件"]
        PROMETHEUS[Prometheus<br/>监控]
        GRAFANA[Grafana<br/>可视化]
    end

    DOCKER --> SCRIPT
    SCRIPT --> PYTHON
    PYTHON --> NGINX
    DOCKER --> AWS
    DOCKER --> K8S
    PROMETHEUS --> GRAFANA
```

---

## 二、部署详情

### 2.1 服务架构

```mermaid
flowchart TB
    subgraph Frontend["前端服务"]
        FE[React Frontend<br/>:5173]
    end
    
    subgraph Backend["后端服务"]
        API[FastAPI Main<br/>:8000]
    end
    
    subgraph ML_Services["ML 服务"]
        EMB[Embedding<br/>:8002]
        RERANK[Reranking<br/>:8004]
        DOC[Doc Processor<br/>:5003]
        LLM[LLM Gateway<br/>:8003]
    end
    
    subgraph Data["数据服务"]
        PG[PostgreSQL<br/>:5432]
        REDIS[Redis<br/>:6379]
        CHROMA[ChromaDB<br/>:8005]
    end
    
    subgraph Infra["基础设施"]
        NGINX[Nginx<br/>:80]
        PRO[Prometheus<br/>:9090]
        GRAF[Grafana<br/>:3001]
    end

    NGINX --> FE
    NGINX --> API
    API --> EMB
    API --> RERANK
    API --> DOC
    API --> LLM
    EMB --> CHROMA
    RERANK --> CHROMA
    API --> PG
    API --> REDIS
    PRO --> GRAF
```

### 2.2 容器配置详情

```yaml
# docker-compose.yml 服务配置
services:
  # ==================== 前端 ====================
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
      - VITE_WS_URL=ws://localhost:8000
    networks:
      - langchain-network
    depends_on:
      - main-app

  # ==================== 后端 ====================
  main-app:
    build:
      context: ./services/main-app
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      # LLM 配置
      - LLM_PROVIDER=openai
      - OPENAI_API_BASE=http://host.docker.internal:8001/v1
      - LLM_MODEL=qwen3-8b-mlx
      
      # Embedding 配置
      - EMBEDDING_API_BASE=http://embedding-service:8001
      - EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
      
      # Reranking 配置
      - RERANKING_ENABLED=true
      - RERANKING_API_BASE=http://reranking-service:8002
      
      # Vector Store
      - VECTOR_STORE_TYPE=chromadb
      - CHROMA_SERVER_HOST=chromadb
      - CHROMA_SERVER_PORT=8000
      
      # Database
      - DATABASE_URL=postgresql://langchain:langchain123@postgres:5432/langchain_db
      - REDIS_URL=redis://redis:6379
      
      # Security
      - SECRET_KEY=your-secret-key-change-in-production
      - JWT_ALGORITHM=HS256
      
      # Features
      - ENABLE_STREAMING=true
      - ENABLE_AGENT=true
      - ENABLE_MEMORY=true

  # ==================== ML 服务 ====================
  embedding-service:
    build:
      context: ./services/embedding-service
      dockerfile: Dockerfile
    ports:
      - "8002:8001"
    environment:
      - MODEL_NAME=BAAI/bge-base-en-v1.5
      - CACHE_TYPE=redis
      - REDIS_URL=redis://redis:6379
      - BATCH_SIZE=32
      - MAX_LENGTH=512

  reranking-service:
    build:
      context: ./services/reranking-service
      dockerfile: Dockerfile
      target: app
    ports:
      - "8004:8002"
    environment:
      - RERANKING_PROVIDER=sentence-transformers
      - RERANKING_MODEL=cross-encoder/ms-marco-MiniLM-L-12-v2
      - RERANKING_DEVICE=cpu
      - RERANKING_BATCH_SIZE=32
    # 资源限制
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  doc-processor:
    build:
      context: ./services/doc-processor
      dockerfile: Dockerfile
    ports:
      - "5003:5003"
    environment:
      - MAX_FILE_SIZE=50
      - OCR_ENABLED=true
      - OCR_LANGUAGE=chi_sim+eng

  llm-gateway:
    build:
      context: ./services/llm-gateway
      dockerfile: Dockerfile
    ports:
      - "8003:8003"
    environment:
      - REDIS_URL=redis://redis:6379
      - CACHE_TTL=3600

  # ==================== 数据服务 ====================
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=langchain
      - POSTGRES_PASSWORD=langchain123
      - POSTGRES_DB=langchain_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langchain"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8005:8000"
    environment:
      - CHROMA_SERVER_AUTH_PROVIDER=chromadb.auth.token_authn.TokenAuthenticationServerProvider
      - CHROMA_SERVER_AUTH_CREDENTIALS_PROVIDER=chromadb.auth.token_authn.TokenConfigServerCredentialsProvider
      - CHROMA_SERVER_AUTH_TOKEN_TRANSPORT_HEADER=AUTHORIZATION
      - CHROMA_SERVER_AUTH_CREDENTIALS=test-token
      - PERSIST_DIRECTORY=/chroma/chroma
      - IS_PERSISTENT=TRUE
    volumes:
      - chroma_data:/chroma/chroma

  # ==================== 基础设施 ====================
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    profiles:
      - production

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    profiles:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    profiles:
      - monitoring
```

---

## 三、基础 Infra Rules

### 3.1 网络规则

```mermaid
flowchart TB
    subgraph Network["langchain-network"]
        direction TB
        FE[frontend<br/>:5173]
        API[main-app<br/>:8000]
        EMB[embedding<br/>:8002]
        RERANK[reranking<br/>:8004]
        DOC[doc-processor<br/>:5003]
        LLM[llm-gateway<br/>:8003]
        PG[postgres<br/>:5432]
        REDIS[redis<br/>:6379]
        CHROMA[chromadb<br/>:8005]
    end

    FE --> API
    API --> EMB
    API --> RERANK
    API --> DOC
    API --> LLM
    API --> PG
    API --> REDIS
    API --> CHROMA
    EMB --> CHROMA
    RERANK --> CHROMA
```

**网络配置规则**:
- 使用 `bridge` 驱动创建自定义网络
- 网络名称: `langchain-network`
- 容器间通过服务名进行通信
- 外部端口映射用于访问

### 3.2 健康检查规则

```yaml
# 健康检查配置示例
healthcheck:
  # PostgreSQL
  test: ["CMD-SHELL", "pg_isready -U langchain"]
  interval: 10s
  timeout: 5s
  retries: 5
  
  # Redis
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
  
  # Reranking Service
  test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

**健康检查规则**:
| 服务 | 检查方式 | 间隔 | 超时 | 重试 |
|------|----------|------|------|------|
| PostgreSQL | pg_isready | 10s | 5s | 5 |
| Redis | redis-cli ping | 10s | 5s | 5 |
| Reranking | HTTP curl | 30s | 10s | 3 |
| 自定义服务 | curl health | 30s | 10s | 3 |

### 3.3 资源限制规则

```yaml
# 资源限制配置
deploy:
  resources:
    limits:
      memory: 2G      # 最大内存
      cpus: '1.0'    # 最大 CPU 核数
    reservations:
      memory: 512M   # 预留内存
      cpus: '0.5'    # 预留 CPU
```

**资源限制规则**:
| 服务 | 内存限制 | CPU 限制 | 内存预留 | CPU 预留 |
|------|----------|----------|----------|----------|
| reranking-service | 2G | 1.0 | 512M | 0.5 |
| main-app | - | - | - | - |
| embedding-service | - | - | - | - |

### 3.4 依赖关系规则

```mermaid
flowchart TB
    subgraph Dependencies["依赖关系"]
        FE["frontend depends_on main-app"]
        API["main-app depends_on postgres, redis, chromadb, embedding-service, reranking-service, doc-processor"]
        EMB["embedding-service depends_on redis"]
        RERANK["reranking-service depends_on redis, postgres"]
    end
```

**依赖规则**:
- `depends_on` 确保服务启动顺序
- 使用 `condition: service_started` 确保健康检查通过
- 避免循环依赖

### 3.5 卷挂载规则

```yaml
# 卷挂载配置
volumes:
  # 命名卷
  postgres_data:
  redis_data:
  chroma_data:
  prometheus_data:
  grafana_data:
  
  # 绑定挂载
  - ./services/main-app:/app
  - ./data/uploads:/app/uploads
  - ./models/embeddings:/app/models
  - ./data/documents:/app/documents
```

**卷挂载规则**:
| 类型 | 用途 | 示例 |
|------|------|------|
| 命名卷 | 持久化数据 | postgres_data, redis_data |
| 绑定挂载 | 代码/配置同步 | ./services/main-app:/app |
| 临时卷 | 缓存/临时文件 | /tmp |

### 3.6 环境变量规则

```yaml
# 环境变量分类
environment:
  # LLM 配置
  - LLM_PROVIDER=openai
  - LLM_MODEL=qwen3-8b-mlx
  - LLM_API_KEY=${LLM_API_KEY}
  
  # Embedding 配置
  - EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
  
  # Vector Store
  - VECTOR_STORE_TYPE=chromadb
  
  # Database
  - DATABASE_URL=postgresql://langchain:langchain123@postgres:5432/langchain_db
  - REDIS_URL=redis://redis:6379
  
  # Security
  - SECRET_KEY=${SECRET_KEY}
  - JWT_ALGORITHM=HS256
  
  # Features
  - ENABLE_STREAMING=true
  - ENABLE_AGENT=true
  - ENABLE_MEMORY=true
```

**环境变量规则**:
- 敏感信息使用 `${VAR}` 引用
- 必需变量无默认值
- 可选变量有默认值

---

## 四、部署流程

### 4.1 部署脚本流程

```mermaid
flowchart LR
    subgraph Deploy["部署流程"]
        CHECK[检查 Python<br/>3.8+]
        INSTALL[安装 Python<br/>如需要]
        VENV[创建虚拟环境]
        DEPS[安装依赖]
        CONFIG[配置向导]
        DEPLOY[执行部署]
    end

    CHECK --> INSTALL
    INSTALL --> VENV
    VENV --> DEPS
    DEPS --> CONFIG
    CONFIG --> DEPLOY
```

### 4.2 快速启动命令

```bash
# 方式1: 一键启动 (推荐)
./start-system.sh

# 方式2: Docker Compose
docker-compose up -d

# 方式3: 手动启动
python qwen3_api_server.py &                    # LLM 服务 (8001)
cd services/embedding-service && python app.py &  # Embedding (8002)
cd services/main-app && uvicorn app.main:app --reload --port 8000 &  # API (8000)
cd frontend && npm run dev                      # 前端 (5173)

# 停止服务
./stop-services.sh
```

### 4.3 生产环境部署

```bash
# 使用 Nginx 反向代理
docker-compose --profile production up -d nginx

# 启用监控
docker-compose --profile monitoring up -d prometheus grafana

# 完整启动
docker-compose -f docker-compose.yml up -d
```

---

## 五、Infra 最佳实践

### 5.1 安全规则

```yaml
# 安全配置
security:
  # 密钥管理
  - SECRET_KEY 必须更改默认值
  - 使用环境变量存储敏感信息
  
  # 网络安全
  - 仅暴露必要端口
  - 使用 Nginx 反向代理
  
  # 认证
  - JWT_ALGORITHM=HS256
  - 启用 Token 认证
```

### 5.2 监控规则

```yaml
# 监控配置
monitoring:
  # Prometheus
  - 端口: 9090
  - 采集间隔: 15s
  - 保留时间: 15d
  
  # Grafana
  - 端口: 3001
  - 数据源: Prometheus
```

### 5.3 日志规则

```yaml
# 日志配置
logging:
  # 级别
  - LOG_LEVEL=INFO (默认)
  - LOG_FORMAT=json
  
  # 输出
  - 控制台输出
  - 文件输出 (可选)
  - Syslog (可选)
```

---

## 六、总结

### 部署工具栈

| 层级 | 工具 | 说明 |
|------|------|------|
| 容器编排 | Docker Compose | 主要部署方式 |
| 自动化 | Shell 脚本 | 一键部署 |
| 配置 | Python | 环境配置 |
| 反向代理 | Nginx | 生产环境 |
| 监控 | Prometheus + Grafana | 可选 |

### 关键端口

| 服务 | 端口 | 用途 |
|------|------|------|
| Frontend | 5173 | React 开发服务器 |
| API | 8000 | FastAPI 后端 |
| LLM | 8001 | Qwen3 API |
| Embedding | 8002 | 嵌入服务 |
| LLM Gateway | 8003 | 多提供商网关 |
| Reranking | 8004 | 重排序服务 |
| ChromaDB | 8005 | 向量存储 |
| PostgreSQL | 5432 | 关系数据库 |
| Redis | 6379 | 缓存 |
| Nginx | 80/443 | 反向代理 |
| Prometheus | 9090 | 监控 |
| Grafana | 3001 | 可视化 |

### 部署检查清单

- [ ] Python 3.8+ 已安装
- [ ] Docker 和 Docker Compose 已安装
- [ ] 环境变量已配置
- [ ] 端口未被占用
- [ ] 磁盘空间充足
- [ ] 网络连接正常