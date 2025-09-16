# 部署配置系统设计方案

## 1. 系统概述

### 1.1 目标
设计一个灵活的部署配置系统，支持多种部署场景（AWS、Docker Compose、本地GPU），通过交互式配置生成器和统一的部署脚本，实现一键部署。

### 1.2 核心原则
- **场景适配**: 支持AWS云端、Docker Compose、本地显卡等多种部署场景
- **配置灵活**: 支持不同的LLM、Embedding、Reranking服务配置
- **用户友好**: 交互式配置向导，降低部署门槛
- **配置持久化**: 配置可保存、复用和版本管理
- **扩展性**: 易于添加新的部署场景和服务配置

## 2. 系统架构

### 2.1 组件结构
```
deployment/
├── configs/                      # 配置文件目录
│   ├── templates/               # 配置模板
│   │   ├── aws.yaml            # AWS部署模板
│   │   ├── docker-compose.yaml # Docker Compose模板
│   │   └── local-gpu.yaml      # 本地GPU模板
│   ├── presets/                # 预设配置
│   │   ├── dev-macos.yaml      # MacOS开发环境
│   │   ├── prod-aws.yaml       # AWS生产环境
│   │   └── test-docker.yaml    # Docker测试环境
│   └── user/                   # 用户生成的配置
│       └── .gitignore          # 忽略用户配置
├── scripts/                     # 部署脚本
│   ├── configure.py            # 交互式配置生成器
│   ├── deploy.py               # 统一部署脚本
│   ├── validate.py             # 配置验证器
│   └── utils/                  # 工具函数
│       ├── config_loader.py    # 配置加载器
│       ├── service_checker.py  # 服务检查器
│       └── env_generator.py    # 环境变量生成器
└── docs/                       # 文档
    ├── configuration-guide.md   # 配置指南
    └── deployment-guide.md      # 部署指南
```

### 2.2 配置文件格式
```yaml
# deployment-config.yaml
version: "1.0"
metadata:
  name: "production-aws"
  created_at: "2024-01-15"
  description: "AWS production environment configuration"

# 部署场景
deployment:
  type: "aws"  # aws | docker-compose | local-gpu | local-cpu
  environment: "production"  # development | staging | production

# 基础设施配置
infrastructure:
  # AWS配置
  aws:
    region: "us-west-2"
    vpc_id: "vpc-xxx"
    instance_types:
      main_app: "t3.xlarge"
      llm_server: "g4dn.xlarge"
    ecs_cluster: "compliance-cluster"

  # Docker配置
  docker:
    compose_file: "docker-compose.yml"
    network: "compliance-network"

  # 本地GPU配置
  local_gpu:
    cuda_version: "12.1"
    gpu_memory: "24GB"

# 服务配置
services:
  # LLM服务
  llm:
    provider: "openrouter"  # openrouter | openai | azure | local-mlx | vllm | ollama
    config:
      model: "anthropic/claude-3.5-sonnet"
      api_key: "${OPENROUTER_API_KEY}"
      base_url: "https://openrouter.ai/api/v1"
      temperature: 0.7
      max_tokens: 4096

  # Embedding服务
  embedding:
    provider: "local"  # openai | local | huggingface
    config:
      model: "BAAI/bge-base-en-v1.5"
      api_base: "http://embedding-service:8002"
      batch_size: 100
      dimensions: 768

  # Reranking服务
  reranking:
    enabled: true
    provider: "local"  # cohere | local
    config:
      model: "BAAI/bge-reranker-base"
      api_base: "http://reranking-service:8004"
      top_k: 10

  # 文档处理服务
  document_processor:
    enabled: true
    config:
      api_base: "http://doc-processor:8003"
      max_file_size: "100MB"
      supported_formats: ["pdf", "docx", "xlsx", "pptx", "txt", "md"]

  # 向量数据库
  vector_store:
    type: "chromadb"  # chromadb | weaviate | pinecone | qdrant
    config:
      host: "localhost"
      port: 8000
      collection_name: "compliance_docs"

  # 数据库
  database:
    type: "postgresql"
    config:
      host: "${DB_HOST}"
      port: 5432
      database: "compliance_assistant"
      user: "${DB_USER}"
      password: "${DB_PASSWORD}"

  # 缓存
  cache:
    type: "redis"
    config:
      host: "${REDIS_HOST}"
      port: 6379
      ttl: 3600

# 应用配置
application:
  main_app:
    port: 8000
    workers: 4
    enable_docs: true
    cors_origins: ["http://localhost:5173"]

  frontend:
    port: 5173
    build_mode: "production"
    api_base: "http://localhost:8000"

# 监控配置
monitoring:
  enabled: true
  prometheus:
    enabled: true
    port: 9090
  grafana:
    enabled: true
    port: 3000

# 日志配置
logging:
  level: "INFO"
  format: "json"
  outputs:
    - type: "file"
      path: "/var/log/compliance-assistant"
    - type: "console"
```

## 3. 交互式配置生成器设计

### 3.1 用户交互流程
```python
# configure.py 交互流程
1. 选择部署场景
   - AWS Cloud (ECS/EC2)
   - Docker Compose (本地/服务器)
   - Local GPU (NVIDIA)
   - Local CPU (Apple Silicon/x86)

2. 选择环境类型
   - Development
   - Staging
   - Production

3. 配置LLM服务
   - Provider选择
   - API配置
   - 模型选择

4. 配置Embedding服务
   - Provider选择
   - 模型配置

5. 配置Reranking服务
   - 是否启用
   - Provider配置

6. 配置存储服务
   - 向量数据库
   - 关系数据库
   - 缓存服务

7. 高级配置（可选）
   - 监控服务
   - 日志配置
   - 性能调优

8. 生成配置
   - 预览配置
   - 保存配置
   - 生成.env文件
```

### 3.2 智能推荐
```python
# 基于硬件的智能推荐
def recommend_configuration(hardware_info):
    if hardware_info['gpu_type'] == 'apple_silicon':
        return {
            'llm': {'provider': 'local-mlx', 'model': 'Qwen3-8B-MLX-bf16'},
            'embedding': {'provider': 'local', 'model': 'BAAI/bge-base-en-v1.5'}
        }
    elif hardware_info['gpu_type'] == 'nvidia':
        return {
            'llm': {'provider': 'vllm', 'model': 'Qwen/Qwen2.5-7B-Instruct'},
            'embedding': {'provider': 'local', 'model': 'BAAI/bge-base-en-v1.5'}
        }
    else:
        return {
            'llm': {'provider': 'openrouter', 'model': 'anthropic/claude-3.5-sonnet'},
            'embedding': {'provider': 'openai', 'model': 'text-embedding-3-small'}
        }
```

## 4. 统一部署脚本设计

### 4.1 部署脚本功能
```python
# deploy.py 主要功能
class UnifiedDeployer:
    def __init__(self, config_path):
        self.config = load_config(config_path)
        self.validator = ConfigValidator()
        self.deployer = self._get_deployer()

    def deploy(self):
        # 1. 验证配置
        self.validator.validate(self.config)

        # 2. 准备环境
        self._prepare_environment()

        # 3. 生成环境变量
        self._generate_env_files()

        # 4. 部署服务
        self.deployer.deploy_services()

        # 5. 健康检查
        self._health_check()

        # 6. 显示访问信息
        self._show_access_info()
```

### 4.2 部署器实现
```python
# 不同场景的部署器
class AWSDeployer:
    def deploy_services(self):
        # ECS任务定义
        # ALB配置
        # RDS/ElastiCache设置
        pass

class DockerComposeDeployer:
    def deploy_services(self):
        # docker-compose up
        # 网络配置
        # 卷挂载
        pass

class LocalGPUDeployer:
    def deploy_services(self):
        # CUDA检查
        # vLLM启动
        # 本地服务启动
        pass
```

## 5. 实施任务列表

### Phase 1: 基础架构 (2天)
- [ ] TASK-001: 创建deployment目录结构
- [ ] TASK-002: 设计配置文件schema (YAML)
- [ ] TASK-003: 实现配置加载器和验证器
- [ ] TASK-004: 创建配置模板文件

### Phase 2: 交互式配置器 (3天)
- [ ] TASK-005: 实现configure.py主框架
- [ ] TASK-006: 添加硬件检测功能
- [ ] TASK-007: 实现LLM服务配置向导
- [ ] TASK-008: 实现Embedding/Reranking配置向导
- [ ] TASK-009: 实现存储服务配置向导
- [ ] TASK-010: 添加配置预览和保存功能

### Phase 3: 部署脚本 (3天)
- [ ] TASK-011: 实现UnifiedDeployer基类
- [ ] TASK-012: 实现DockerComposeDeployer
- [ ] TASK-013: 实现LocalGPUDeployer (vLLM/MLX)
- [ ] TASK-014: 实现AWSDeployer (ECS/EC2)
- [ ] TASK-015: 添加健康检查和回滚机制

### Phase 4: 环境管理 (2天)
- [ ] TASK-016: 实现.env文件生成器
- [ ] TASK-017: 添加secrets管理（AWS Secrets Manager/本地加密）
- [ ] TASK-018: 实现配置备份和恢复功能
- [ ] TASK-019: 添加配置版本管理

### Phase 5: 优化和测试 (2天)
- [ ] TASK-020: 添加进度显示和日志输出
- [ ] TASK-021: 实现服务依赖检查
- [ ] TASK-022: 添加性能基准测试
- [ ] TASK-023: 编写部署文档和使用指南
- [ ] TASK-024: 创建常见问题故障排除指南

### Phase 6: 高级功能 (可选)
- [ ] TASK-025: 添加Kubernetes部署支持
- [ ] TASK-026: 实现自动扩缩容配置
- [ ] TASK-027: 添加成本估算功能
- [ ] TASK-028: 实现多环境并行部署
- [ ] TASK-029: 添加A/B测试支持

## 6. 预期效果

### 6.1 用户体验
```bash
# 运行配置向导
$ python deployment/scripts/configure.py

Welcome to Drass Deployment Configurator v1.0
==============================================

Step 1: Select deployment scenario
1) AWS Cloud (ECS/EC2)
2) Docker Compose
3) Local GPU (NVIDIA)
4) Local CPU (Apple Silicon)
> 4

Detected: Apple M2 Pro, 32GB RAM
Recommended configuration: MLX optimized

Step 2: Configure LLM Service
1) Use local MLX model (Qwen3-8B)
2) Use OpenRouter API
3) Use OpenAI API
> 1

...

Configuration saved to: deployment/configs/user/config-20240115.yaml

# 执行部署
$ python deployment/scripts/deploy.py --config deployment/configs/user/config-20240115.yaml

Deploying Drass Compliance Assistant...
✓ Configuration validated
✓ Environment prepared
✓ Services started
✓ Health checks passed

Services are running:
- Frontend: http://localhost:5173
- API: http://localhost:8000/docs
- LLM Server: http://localhost:8001
- Embedding: http://localhost:8002

Run 'deploy.py status' to check service status
```

### 6.2 配置复用
```bash
# 使用预设配置
$ python deployment/scripts/deploy.py --preset dev-macos

# 导出配置供团队使用
$ python deployment/scripts/configure.py --export team-config.yaml

# 从现有环境生成配置
$ python deployment/scripts/configure.py --from-env
```

## 7. 技术栈

- **配置管理**: YAML + Pydantic
- **交互式CLI**: Rich + Questionary
- **部署自动化**: Python + Shell Scripts
- **容器编排**: Docker Compose / ECS
- **云服务**: AWS SDK (Boto3)
- **进程管理**: Supervisor / PM2