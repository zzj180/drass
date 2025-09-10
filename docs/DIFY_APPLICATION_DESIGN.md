# 智能合规助手应用设计方案

## 项目概述

基于Dify平台构建的企业级数据合规智能助手，采用通用语言模型（vLLM）+ 知识库架构，支持动态知识库更新和个性化合规方案生成。

## 系统架构

### 1. 核心架构组件（Docker容器映射）

```
┌─────────────────────────────────────────────────────────┐
│                     前端应用层                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Nginx容器 (drass-nginx) - Port 80               │   │
│  │  - Web界面路由                                    │   │
│  │  - API反向代理                                    │   │
│  │  - 静态资源服务                                   │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                     Dify平台层                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │     API容器 (drass-api) - Port 5001              │   │
│  │  - 对话管理服务                                   │   │
│  │  - 工作流引擎                                     │   │
│  │  - 文件上传处理                                   │   │
│  │  - 知识库管理API                                  │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │    Worker容器 (drass-worker) - Celery            │   │
│  │  - 异步任务处理                                   │   │
│  │  - 文档向量化任务                                 │   │
│  │  - 知识库更新任务                                 │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │    Web容器 (drass-web) - Port 3000               │   │
│  │  - React前端应用                                  │   │
│  │  - 用户界面                                       │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  文档处理容器 (drass-doc-processor) - Port 5003  │   │
│  │  - 文档转Markdown服务                             │   │
│  │  - OCR图片识别                                    │   │
│  │  - 格式转换引擎                                   │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                  数据存储层                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │   PostgreSQL容器 (drass-db) - Port 5432          │   │
│  │   - 应用数据存储                                  │   │
│  │   - 知识库元数据                                  │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │   Redis容器 (drass-redis) - Port 6379            │   │
│  │   - 缓存服务                                      │   │
│  │   - Celery消息队列                                │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │   Weaviate容器 (drass-weaviate) - Port 8080      │   │
│  │   - 向量数据库                                    │   │
│  │   - 语义搜索引擎                                  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

所有容器通过 drass-network (bridge) 网络互联
```

### 2. 模型配置

#### 主模型（vLLM）
- **模型名称**: vllm
- **提供商**: yangyaofei/vllm
- **参数配置**:
  - temperature: 0.3 (保证输出稳定性)
  - top_p: 0.5 (控制输出多样性)
  - 模式: chat (对话模式)

#### 检索增强模型
- **Embedding模型**: 
  - 模型名称: text-embedding-ada-002 (或其他兼容模型)
  - 提供商: OpenAI兼容接口
  - 向量维度: 1536
  - 用途: 文档和查询的向量化表示
  - 配置参数:
    ```yaml
    embedding_model:
      provider: openai_api_compatible
      model_name: text-embedding-ada-002
      api_base: ${EMBEDDING_API_BASE}
      api_key: ${EMBEDDING_API_KEY}
    ```

- **Reranking模型**: Qwen3-Reranker-8B
  - 提供商: langgenius/openai_api_compatible
  - 用途: 对检索结果重新排序，提高相关性
  - 配置参数:
    ```yaml
    reranking_model:
      provider: langgenius/openai_api_compatible
      model_name: Qwen3-Reranker-8B
      api_base: ${RERANKING_API_BASE}
    ```

### 3. 知识库架构

#### 知识库组成
```yaml
knowledge_base:
  datasets:
    - id: 05aad86e-653a-4196-8278-a8fc4cfc1de8  # 合规知识库
      enabled: true
      retrieval_settings:
        retrieval_model: multiple  # 多路检索
        top_k: 4  # 返回前4个最相关文档
        reranking_enable: true  # 启用重排序以提升准确性
        reranking_model:
          model_name: Qwen3-Reranker-8B
          provider: langgenius/openai_api_compatible
```

#### 文档处理流程
1. **文档上传** → 2. **格式转换(转Markdown)** → 3. **文本提取** → 4. **分段处理** → 5. **向量化** → 6. **索引存储**

## 功能设计

### 功能1: 动态知识库更新

#### 实现方案

##### 1.1 文档上传接口
```python
# API端点: POST /api/knowledge-base/upload
{
    "file": "multipart/form-data",
    "metadata": {
        "category": "法规文档|企业政策|行业标准",
        "version": "1.0",
        "effective_date": "2024-01-01",
        "tags": ["数据安全", "个人信息"]
    }
}
```

##### 1.2 文档处理工作流
```yaml
workflow:
  steps:
    - name: file_validation
      action: 
        - 检查文件格式 (PDF/DOC/DOCX/TXT/图片)
        - 验证文件大小 (<50MB)
        - 病毒扫描
    
    - name: format_conversion
      action:
        - 将所有文档转换为Markdown格式
        - PDF/DOC/DOCX → Markdown转换
        - 图片文件OCR识别 → Markdown
        - 保留原始格式和结构信息
    
    - name: content_extraction
      action:
        - 从Markdown提取文本内容
        - 识别文档结构（章节、段落）
        - 提取元数据和标题层级
    
    - name: intelligent_segmentation
      action:
        - 父子段分割策略
        - 保持上下文完整性
        - 生成段落ID关联
    
    - name: embedding_generation
      action:
        - 调用Embedding模型(text-embedding-ada-002)
        - 生成1536维向量表示
        - 计算相似度阈值
    
    - name: knowledge_base_update
      action:
        - 检查重复内容
        - 版本控制
        - 增量更新Weaviate索引
        - 更新统计信息
```

##### 1.3 支持的文件格式
- 文档类: PDF, DOC, DOCX, PPT, PPTX
- 数据类: XLS, XLSX, CSV, JSON, XML
- 文本类: TXT, MD
- 压缩包: ZIP, RAR, 7Z

##### 1.4 版本管理机制
```python
version_control = {
    "document_id": "uuid",
    "versions": [
        {
            "version": "1.0",
            "upload_time": "2024-01-01",
            "uploader": "admin",
            "changes": "初始版本",
            "status": "archived"
        },
        {
            "version": "2.0",
            "upload_time": "2024-02-01",
            "uploader": "admin",
            "changes": "更新第3章内容",
            "status": "active"
        }
    ]
}
```

### 功能2: 用户资料与需求处理

#### 实现方案

##### 2.1 用户输入表单设计
```yaml
user_input_form:
  - name: file_upload
    type: file
    label: 附件上传
    required: false
    max_files: 5
    help: 上传需要分析的合规相关文档
    
  - name: file_purpose
    type: select
    label: 处理目的
    required: true
    options:
      - value: update_knowledge_base
        label: 更新知识库
      - value: generate_compliance_report
        label: 生成合规方案
        
  - name: business_scenario
    type: textarea
    label: 业务场景描述
    required: false
    placeholder: 描述您的业务场景和合规需求
```

##### 2.2 智能分析流程
```python
def process_user_request(request):
    # 1. 解析用户输入
    context = {
        "files": request.files,
        "purpose": request.file_purpose,
        "scenario": request.business_scenario
    }
    
    # 2. 根据目的选择处理路径
    if context["purpose"] == "update_knowledge_base":
        return knowledge_base_update_flow(context)
    elif context["purpose"] == "generate_compliance_report":
        return compliance_report_generation_flow(context)

def knowledge_base_update_flow(context):
    """知识库更新流程"""
    # 1. 文档格式转换
    markdown_docs = convert_to_markdown(context["files"])
    
    # 2. 内容验证和清洗
    cleaned_docs = validate_and_clean(markdown_docs)
    
    # 3. 智能分段
    segments = intelligent_segmentation(cleaned_docs)
    
    # 4. 向量化处理
    embeddings = generate_embeddings(segments)
    
    # 5. 更新知识库
    update_result = update_knowledge_base(
        segments=segments,
        embeddings=embeddings,
        metadata=context["metadata"]
    )
    
    return {
        "status": "success",
        "documents_processed": len(context["files"]),
        "segments_created": len(segments),
        "update_summary": update_result
    }
    
def compliance_report_generation_flow(context):
    """合规方案生成流程"""
    # 1. 文档格式转换（统一转为Markdown）
    markdown_docs = convert_to_markdown(context["files"])
    
    # 2. 文档内容分析
    document_analysis = analyze_markdown_documents(markdown_docs)
    
    # 3. 知识库检索（启用重排序）
    relevant_knowledge = retrieve_from_knowledge_base(
        query=document_analysis + context["scenario"],
        top_k=10,
        reranking_enabled=True
    )
    
    # 4. 生成合规方案
    compliance_plan = generate_compliance_plan(
        user_context=document_analysis,
        knowledge_base=relevant_knowledge,
        requirements=context["scenario"]
    )
    
    # 5. 格式化输出（Markdown格式，5000字以上）
    return format_markdown_report(compliance_plan, min_words=5000)

def convert_to_markdown(files):
    """统一文档格式转换"""
    markdown_docs = []
    for file in files:
        if file.type in ['pdf', 'doc', 'docx']:
            # 调用文档处理容器服务
            md_content = doc_processor_service.convert(file)
        elif file.type in ['jpg', 'png', 'jpeg']:
            # OCR识别后转换
            md_content = doc_processor_service.ocr_convert(file)
        elif file.type == 'md':
            md_content = file.content
        else:
            # 其他格式的通用处理
            md_content = doc_processor_service.generic_convert(file)
        
        markdown_docs.append({
            'content': md_content,
            'metadata': extract_metadata(file)
        })
    
    return markdown_docs
```

##### 2.3 个性化方案生成模板
```markdown
# 📋 数据合规方案报告

## 📊 业务场景分析
- **场景描述**: {business_scenario}
- **涉及数据类型**: {data_types}
- **合规领域**: {compliance_domains}

## 🎯 合规要求分析
### 法律法规要求
{legal_requirements}

### 企业政策要求
{company_policies}

## 💡 推荐解决方案
### 技术方案
{technical_solutions}

### 管理措施
{management_measures}

## ⚠️ 风险评估
{risk_assessment}

## 📈 实施计划
{implementation_plan}

## 📚 参考依据
{references}
```

## API接口设计

### 1. 知识库管理API

```yaml
endpoints:
  # 上传文档到知识库
  - path: /api/v1/knowledge-base/documents
    method: POST
    description: 上传新文档到知识库
    
  # 查询知识库文档
  - path: /api/v1/knowledge-base/documents
    method: GET
    description: 获取知识库文档列表
    
  # 更新文档
  - path: /api/v1/knowledge-base/documents/{doc_id}
    method: PUT
    description: 更新指定文档
    
  # 删除文档
  - path: /api/v1/knowledge-base/documents/{doc_id}
    method: DELETE
    description: 删除指定文档
```

### 2. 对话管理API

```yaml
endpoints:
  # 发送消息
  - path: /api/v1/chat/messages
    method: POST
    body:
      conversation_id: string
      message: string
      files: array
      context: object
      
  # 获取对话历史
  - path: /api/v1/chat/conversations/{conversation_id}
    method: GET
    
  # 创建新对话
  - path: /api/v1/chat/conversations
    method: POST
```

## 部署配置

### 1. 完整Docker Compose配置

```yaml
version: '3.8'

services:
  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: drass-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./data/static:/usr/share/nginx/html
    depends_on:
      - api
      - web
    networks:
      - drass-network
    restart: unless-stopped

  # Dify API服务
  api:
    image: langgenius/dify-api:latest
    container_name: drass-api
    ports:
      - "5001:5001"
    environment:
      - EDITION=SELF_HOSTED
      - CONSOLE_URL=http://localhost
      - SERVICE_API_URL=http://localhost/v1
      - CELERY_BROKER_URL=redis://redis:6379/1
      - SQLALCHEMY_DATABASE_URI=postgresql://dify:${DB_PASSWORD:-dify123}@db:5432/dify
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - WEAVIATE_ENDPOINT=http://weaviate:8080
      - SECRET_KEY=${SECRET_KEY:-your-secret-key}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY:-your-encryption-key}
      - STORAGE_TYPE=local
      - STORAGE_LOCAL_PATH=/app/storage
      # Embedding模型配置
      - EMBEDDING_MODEL_PROVIDER=openai_api_compatible
      - EMBEDDING_MODEL_NAME=text-embedding-ada-002
      - EMBEDDING_API_BASE=${EMBEDDING_API_BASE}
      - EMBEDDING_API_KEY=${EMBEDDING_API_KEY}
      # Reranking模型配置
      - RERANKING_MODEL_PROVIDER=langgenius/openai_api_compatible
      - RERANKING_MODEL_NAME=Qwen3-Reranker-8B
      - RERANKING_API_BASE=${RERANKING_API_BASE}
      - RERANKING_ENABLED=true
    volumes:
      - ./data/api:/app/storage
      - ./config/dify:/app/config
    depends_on:
      - db
      - redis
      - weaviate
    networks:
      - drass-network
    restart: unless-stopped

  # Dify Worker服务
  worker:
    image: langgenius/dify-api:latest
    container_name: drass-worker
    environment:
      - EDITION=SELF_HOSTED
      - CELERY_BROKER_URL=redis://redis:6379/1
      - SQLALCHEMY_DATABASE_URI=postgresql://dify:${DB_PASSWORD:-dify123}@db:5432/dify
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - WEAVIATE_ENDPOINT=http://weaviate:8080
      - SECRET_KEY=${SECRET_KEY:-your-secret-key}
      - STORAGE_TYPE=local
      - STORAGE_LOCAL_PATH=/app/storage
    volumes:
      - ./data/worker:/app/storage
      - ./config/dify:/app/config
    depends_on:
      - db
      - redis
      - weaviate
    networks:
      - drass-network
    command: ["celery", "-A", "celery_app", "worker", "--loglevel=info"]
    restart: unless-stopped

  # Dify Web前端
  web:
    image: langgenius/dify-web:latest
    container_name: drass-web
    ports:
      - "3000:3000"
    environment:
      - CONSOLE_API_URL=http://api:5001
      - APP_API_URL=http://api:5001
    depends_on:
      - api
    networks:
      - drass-network
    restart: unless-stopped

  # 文档处理服务（已实现）
  doc-processor:
    build:
      context: ./services/doc-processor
      dockerfile: Dockerfile
    container_name: drass-doc-processor
    ports:
      - "5003:5003"
    environment:
      - MAX_FILE_SIZE=50MB
      - SUPPORTED_FORMATS=pdf,doc,docx,xls,xlsx,ppt,pptx,jpg,png,jpeg
      - OCR_ENABLED=true
      - OCR_LANGUAGE=chi_sim,eng
      - PANDOC_ENABLED=true
    volumes:
      - ./data/uploads:/app/uploads
      - ./data/processed:/app/processed
    networks:
      - drass-network
    restart: unless-stopped

  # PostgreSQL数据库
  db:
    image: postgres:15-alpine
    container_name: drass-db
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=dify
      - POSTGRES_PASSWORD=${DB_PASSWORD:-dify123}
      - POSTGRES_DB=dify
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    networks:
      - drass-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dify"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: drass-redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    networks:
      - drass-network
    command: redis-server --save 60 1 --loglevel warning
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Weaviate向量数据库
  weaviate:
    image: semitechnologies/weaviate:latest
    container_name: drass-weaviate
    ports:
      - "8080:8080"
    environment:
      - QUERY_DEFAULTS_LIMIT=20
      - AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
      - PERSISTENCE_DATA_PATH=/var/lib/weaviate
      - DEFAULT_VECTORIZER_MODULE=none
      - ENABLE_MODULES=text2vec-openai
      - CLUSTER_HOSTNAME=weaviate
    volumes:
      - ./data/weaviate:/var/lib/weaviate
    networks:
      - drass-network
    restart: unless-stopped

  # 定时任务调度器（已实现）
  scheduler:
    build:
      context: ./services/scheduler
      dockerfile: Dockerfile
    container_name: drass-scheduler
    environment:
      - KNOWLEDGE_BASE_UPDATE_CRON=0 2 * * *
      - CLEANUP_CRON=0 3 * * 0
      - BACKUP_CRON=0 4 * * *
      - API_URL=http://api:5001
    depends_on:
      - api
    networks:
      - drass-network
    restart: unless-stopped

networks:
  drass-network:
    driver: bridge
    name: drass-network

volumes:
  postgres_data:
  redis_data:
  weaviate_data:
  api_storage:
  worker_storage:
```

### 2. 环境变量配置（.env文件）

```bash
# 数据库配置
DB_PASSWORD=dify123
REDIS_PASSWORD=

# 安全配置
SECRET_KEY=your-secret-key-here-change-in-production
ENCRYPTION_KEY=your-encryption-key-here-change-in-production

# 知识库配置
KNOWLEDGE_BASE_ID=05aad86e-653a-4196-8278-a8fc4cfc1de8
VECTOR_DB_URL=http://weaviate:8080

# Embedding模型配置
EMBEDDING_MODEL_PROVIDER=openai_api_compatible
EMBEDDING_MODEL_NAME=text-embedding-ada-002
EMBEDDING_API_BASE=http://your-embedding-api-url
EMBEDDING_API_KEY=your-embedding-api-key

# Reranking模型配置
RERANKING_MODEL_NAME=Qwen3-Reranker-8B
RERANKING_API_BASE=http://your-reranking-api-url
RERANKING_ENABLED=true

# vLLM主模型配置
VLLM_MODEL_NAME=vllm
VLLM_API_BASE=http://your-vllm-api-url
VLLM_API_KEY=your-vllm-api-key
VLLM_TEMPERATURE=0.3
VLLM_TOP_P=0.5
MAX_TOKENS=8000

# 文档处理配置
MAX_UPLOAD_SIZE=50MB
CHUNK_SIZE=500
CHUNK_OVERLAP=50
ENABLE_OCR=true
OCR_LANGUAGE=chi_sim,eng

# Dify平台配置
DIFY_PLATFORM_URL=http://localhost
DIFY_API_KEY=your-dify-api-key
DIFY_WORKSPACE_ID=your-workspace-id
```

### 3. 快速启动脚本（start.sh）

```bash
#!/bin/bash

echo "🚀 启动Drass智能合规助手系统..."

# 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️  未找到.env文件，复制示例配置..."
    cp .env.example .env
    echo "请编辑.env文件配置必要的API密钥和参数"
    exit 1
fi

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data/{api,worker,postgres,redis,weaviate,uploads,processed,static}
mkdir -p config/dify
mkdir -p nginx
mkdir -p services/{doc-processor,scheduler}

# 拉取镜像
echo "📥 拉取Docker镜像..."
docker-compose pull

# 启动服务
echo "🔧 启动所有服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "✅ 检查服务状态..."
docker-compose ps

# 初始化数据库（如果需要）
echo "🗄️ 初始化数据库..."
docker-compose exec api python manage.py db upgrade

echo "✨ 系统启动完成！"
echo "📍 访问地址："
echo "   - Web界面: http://localhost"
echo "   - API文档: http://localhost/v1/docs"
echo "   - 管理后台: http://localhost:3000"
echo ""
echo "使用 'docker-compose logs -f' 查看日志"
echo "使用 'docker-compose down' 停止服务"
```

## 安全性设计

### 1. 数据安全
- **加密存储**: 所有上传文档使用AES-256加密
- **传输加密**: HTTPS/TLS 1.3
- **访问控制**: 基于角色的权限管理(RBAC)

### 2. 知识库安全
- **版本控制**: 所有更改记录审计日志
- **备份策略**: 每日增量备份，每周全量备份
- **隔离机制**: 不同部门知识库逻辑隔离

### 3. API安全
- **认证**: API Key + JWT Token
- **限流**: 每用户100次/分钟
- **输入验证**: 严格的参数验证和文件类型检查

## 监控与运维

### 1. 关键指标监控
```yaml
metrics:
  - name: knowledge_base_size
    description: 知识库文档数量
    
  - name: daily_queries
    description: 每日查询次数
    
  - name: response_time
    description: 平均响应时间
    
  - name: accuracy_rate
    description: 回答准确率
```

### 2. 日志管理
```python
logging_config = {
    "level": "INFO",
    "formats": {
        "api": "{timestamp} {level} {api_endpoint} {response_time}",
        "knowledge_base": "{timestamp} {action} {document_id} {user}",
        "chat": "{timestamp} {conversation_id} {message_length}"
    }
}
```

## 优化建议

### 1. 性能优化
- 使用Redis缓存高频查询结果
- 实施向量索引优化（HNSW算法）
- 批量处理文档上传

### 2. 用户体验优化
- 实时进度显示
- 智能推荐相关文档
- 多语言支持

### 3. 扩展性设计
- 微服务架构支持水平扩展
- 消息队列处理异步任务
- 支持多租户隔离

## 实施计划

### 第一阶段（2周）
- [x] 部署基础Dify平台
- [ ] 配置vLLM模型和知识库
- [ ] 实现基础对话功能

### 第二阶段（3周）
- [ ] 开发文档上传API
- [ ] 实现知识库更新机制
- [ ] 集成文档处理工作流

### 第三阶段（2周）
- [ ] 开发用户资料处理功能
- [ ] 实现个性化方案生成
- [ ] 优化检索和排序算法

### 第四阶段（1周）
- [ ] 系统测试和优化
- [ ] 部署监控和日志系统
- [ ] 上线和培训

## 总结

该设计方案基于Dify平台的强大能力，通过vLLM主模型+向量知识库的架构，实现了：

1. **动态知识库管理**：支持多格式文档上传、智能分段、版本控制
2. **智能方案生成**：基于用户上传的资料和需求，结合知识库生成个性化合规方案
3. **高度可扩展**：模块化设计，支持功能扩展和性能优化
4. **安全可靠**：完善的安全机制和监控体系

该方案充分利用了Dify平台的对话管理、工作流引擎和知识库检索能力，为企业提供了一个功能完善的智能合规助手解决方案。