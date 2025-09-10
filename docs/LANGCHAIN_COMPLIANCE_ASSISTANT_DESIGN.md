# LangChain智能合规助手技术方案

## 项目概述

基于LangChain框架构建的企业级数据合规智能助手，采用微服务架构，支持多模型网关、独立的Embedding/Reranking服务，以及React前端。系统同时支持Docker Compose本地部署和AWS云原生分布式部署。

## 系统架构

### 1. 总体架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     前端层 (React.js)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   React SPA   │   Redux   │   Material-UI/Ant Design │  │
│  │   WebSocket   │   Axios   │   React Query           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                         Nginx / ALB
                              │
┌─────────────────────────────────────────────────────────────┐
│                    API网关层 (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   认证授权   │   限流   │   路由   │   监控          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│               LangChain应用层 (Python Services)              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         主服务 (langchain-main-service)             │    │
│  │  - LangChain Chains & Agents                       │    │
│  │  - Memory Management                               │    │
│  │  - Tool Integration                                │    │
│  │  - Workflow Orchestration                          │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │      文档处理服务 (document-processor)              │    │
│  │  - Document Loaders                                │    │
│  │  - Text Splitters                                  │    │
│  │  - Markdown Converter                              │    │
│  │  - OCR Service                                     │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │        知识库服务 (knowledge-service)               │    │
│  │  - Vector Store Management                         │    │
│  │  - Index Management                                │    │
│  │  - Metadata Management                             │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    模型服务层 (Model Services)               │
│  ┌────────────────────────────────────────────────────┐    │
│  │           LLM网关服务 (llm-gateway)                 │    │
│  │  - OpenRouter Integration                          │    │
│  │  - Local vLLM Support                              │    │
│  │  - Model Router & Load Balancer                    │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │      Embedding服务 (embedding-service)              │    │
│  │  - Text Embedding Models                           │    │
│  │  - Batch Processing                                │    │
│  │  - Cache Layer                                     │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │      Reranking服务 (reranking-service)              │    │
│  │  - Cross-Encoder Models                            │    │
│  │  - Score Normalization                             │    │
│  │  - Result Optimization                             │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    数据存储层 (Data Layer)                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐     │
│  │Postgres │  │  Redis  │  │ChromaDB │  │    S3    │     │
│  │   RDS   │  │ElastiCache│ │  ECS   │  │  Bucket  │     │
│  └─────────┘  └─────────┘  └─────────┘  └──────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 2. 核心技术栈

```yaml
frontend:
  framework: React 18
  state_management: Redux Toolkit
  ui_library: Material-UI / Ant Design
  build_tool: Vite
  language: TypeScript
  
backend:
  framework: FastAPI
  langchain_version: ">=0.3.0"
  python_version: "3.11"
  async_support: asyncio + aiohttp
  
model_services:
  llm_gateway:
    - OpenRouter API
    - vLLM (local serving)
    - LiteLLM (unified interface)
  embedding:
    - sentence-transformers
    - OpenAI API
    - Custom BERT models
  reranking:
    - Cross-Encoder models
    - ColBERT
    - Custom rerankers
    
storage:
  vector_db: ChromaDB / Pinecone / Weaviate
  sql_db: PostgreSQL
  cache: Redis
  object_storage: S3 / MinIO
  
deployment:
  local: Docker Compose
  cloud: AWS ECS / EKS
  ci_cd: GitHub Actions / AWS CodePipeline
```

## LangChain核心组件设计

### 1. LLM配置与管理

```python
# config/llm_config.py
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel

class LLMProvider(Enum):
    OPENROUTER = "openrouter"
    LOCAL_VLLM = "vllm"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"

class LLMConfig(BaseModel):
    """LLM配置模型"""
    provider: LLMProvider
    model_name: str
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 8000
    top_p: float = 0.5
    stream: bool = True
    
    # OpenRouter特定配置
    openrouter_config: Optional[Dict[str, Any]] = None
    
    # vLLM特定配置
    vllm_config: Optional[Dict[str, Any]] = None
    
# services/llm_service.py
from langchain.chat_models import ChatOpenAI
from langchain.llms import VLLM
from langchain_community.chat_models import ChatOpenRouter
import litellm

class LLMService:
    """统一的LLM服务接口"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        if self.config.provider == LLMProvider.OPENROUTER:
            return ChatOpenRouter(
                model=self.config.model_name,
                openrouter_api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                streaming=self.config.stream
            )
        elif self.config.provider == LLMProvider.LOCAL_VLLM:
            return VLLM(
                model=self.config.model_name,
                tensor_parallel_size=1,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                vllm_kwargs=self.config.vllm_config or {}
            )
        elif self.config.provider == LLMProvider.OPENAI:
            return ChatOpenAI(
                model_name=self.config.model_name,
                openai_api_key=self.config.api_key,
                openai_api_base=self.config.api_base,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                streaming=self.config.stream
            )
        else:
            # 使用LiteLLM作为通用接口
            return litellm.completion
```

### 2. RAG链设计

```python
# chains/compliance_rag_chain.py
from langchain.chains import RetrievalQA
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

class ComplianceRAGChain:
    """合规助手RAG链"""
    
    def __init__(self, llm_service, retriever, reranker):
        self.llm = llm_service.llm
        self.retriever = retriever
        self.reranker = reranker
        self.memory = ConversationBufferWindowMemory(
            k=10,  # 保留最近10轮对话
            memory_key="chat_history",
            return_messages=True
        )
        
        # 构建提示模板
        self.prompt_template = PromptTemplate(
            template="""你是一位专业的企业数据合规顾问。
            
基于以下检索到的知识库内容和对话历史，为用户提供准确的合规建议。

知识库内容：
{context}

对话历史：
{chat_history}

用户问题：{question}

请提供详细的合规分析和建议（不少于5000字），使用Markdown格式：
""",
            input_variables=["context", "chat_history", "question"]
        )
        
        # 构建检索QA链
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            memory=self.memory,
            return_source_documents=True,
            chain_type_kwargs={
                "prompt": self.prompt_template,
                "verbose": True
            },
            callbacks=[StreamingStdOutCallbackHandler()]
        )
    
    async def process_query(self, query: str, metadata: dict = None):
        """处理用户查询"""
        # 1. 检索相关文档
        docs = await self.retriever.aget_relevant_documents(query)
        
        # 2. 重排序
        if self.reranker:
            docs = await self.reranker.rerank(query, docs)
        
        # 3. 生成回答
        result = await self.qa_chain.ainvoke({
            "query": query,
            "metadata": metadata
        })
        
        return {
            "answer": result["result"],
            "source_documents": result["source_documents"],
            "metadata": {
                "tokens_used": result.get("tokens_used", 0),
                "retrieval_score": result.get("retrieval_score", 0)
            }
        }
```

### 3. 向量存储与检索

```python
# services/vector_store_service.py
from langchain.vectorstores import Chroma, Pinecone, Weaviate
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredMarkdownLoader

class VectorStoreService:
    """向量存储服务"""
    
    def __init__(self, embedding_service_url: str, vector_db_type: str = "chroma"):
        self.embedding_service_url = embedding_service_url
        self.embeddings = self._initialize_embeddings()
        self.vector_store = self._initialize_vector_store(vector_db_type)
        
        # 文本分割器（父子段策略）
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )
        
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )
    
    def _initialize_embeddings(self):
        """初始化嵌入模型（调用独立的Embedding服务）"""
        return RemoteEmbeddings(
            api_url=self.embedding_service_url,
            model_name="bge-large-zh-v1.5"
        )
    
    def _initialize_vector_store(self, db_type: str):
        """初始化向量数据库"""
        if db_type == "chroma":
            return Chroma(
                collection_name="compliance_knowledge",
                embedding_function=self.embeddings,
                persist_directory="./data/chroma"
            )
        elif db_type == "pinecone":
            return Pinecone.from_existing_index(
                index_name="compliance-index",
                embedding=self.embeddings
            )
        elif db_type == "weaviate":
            return Weaviate(
                url="http://weaviate:8080",
                index_name="ComplianceKnowledge",
                embedding=self.embeddings
            )
    
    async def add_documents(self, file_path: str, metadata: dict = None):
        """添加文档到知识库"""
        # 1. 加载文档
        loader = self._get_loader(file_path)
        documents = loader.load()
        
        # 2. 转换为Markdown（调用文档处理服务）
        markdown_docs = await self._convert_to_markdown(documents)
        
        # 3. 分割文档（父子段策略）
        parent_chunks = self.parent_splitter.split_documents(markdown_docs)
        all_chunks = []
        
        for parent in parent_chunks:
            # 为父段添加元数据
            parent.metadata["chunk_type"] = "parent"
            parent.metadata["parent_id"] = generate_uuid()
            all_chunks.append(parent)
            
            # 创建子段
            child_chunks = self.child_splitter.split_text(parent.page_content)
            for child_text in child_chunks:
                child_doc = Document(
                    page_content=child_text,
                    metadata={
                        **parent.metadata,
                        "chunk_type": "child",
                        "parent_id": parent.metadata["parent_id"]
                    }
                )
                all_chunks.append(child_doc)
        
        # 4. 添加到向量存储
        ids = await self.vector_store.aadd_documents(all_chunks)
        
        return {
            "document_count": len(all_chunks),
            "ids": ids,
            "parent_count": len(parent_chunks)
        }
```

### 4. Agent设计

```python
# agents/compliance_agent.py
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_core.messages import SystemMessage

class ComplianceAgent:
    """合规助手Agent"""
    
    def __init__(self, llm_service, vector_store_service):
        self.llm = llm_service.llm
        self.vector_store = vector_store_service
        
        # 定义工具
        self.tools = [
            Tool(
                name="search_knowledge_base",
                func=self._search_knowledge_base,
                description="搜索合规知识库获取相关法规和政策"
            ),
            Tool(
                name="analyze_compliance_risk",
                func=self._analyze_risk,
                description="分析特定场景的合规风险"
            ),
            Tool(
                name="generate_compliance_report",
                func=self._generate_report,
                description="生成详细的合规报告"
            ),
            Tool(
                name="update_knowledge_base",
                func=self._update_knowledge,
                description="更新知识库内容"
            )
        ]
        
        # 创建Agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            system_message=SystemMessage(content="""
                你是一位专业的数据合规顾问。你可以：
                1. 搜索知识库获取相关法规
                2. 分析合规风险
                3. 生成合规报告
                4. 更新知识库
                
                请根据用户需求选择合适的工具，提供专业的合规建议。
            """)
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
    
    async def run(self, user_input: str, context: dict = None):
        """运行Agent"""
        result = await self.agent_executor.ainvoke({
            "input": user_input,
            "context": context or {}
        })
        return result
```

## 微服务实现

### 1. Embedding服务

```yaml
# services/embedding-service/docker-compose.yml
version: '3.8'

services:
  embedding-service:
    build: .
    container_name: embedding-service
    ports:
      - "8001:8001"
    environment:
      - MODEL_NAME=BAAI/bge-large-zh-v1.5
      - DEVICE=cuda
      - BATCH_SIZE=32
      - MAX_LENGTH=512
      - CACHE_SIZE=10000
    volumes:
      - ./models:/app/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

```python
# services/embedding-service/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import torch
from typing import List
import numpy as np
from functools import lru_cache

app = FastAPI(title="Embedding Service")

class EmbeddingRequest(BaseModel):
    texts: List[str]
    normalize: bool = True

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    dimensions: int

class EmbeddingService:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=self.device)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    @lru_cache(maxsize=10000)
    def embed_text(self, text: str, normalize: bool = True) -> List[float]:
        """缓存单个文本的嵌入"""
        embedding = self.model.encode(text, normalize_embeddings=normalize)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], normalize: bool = True) -> List[List[float]]:
        """批量嵌入"""
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            batch_size=32,
            show_progress_bar=False
        )
        return embeddings.tolist()

# 初始化服务
embedding_service = EmbeddingService(
    model_name=os.getenv("MODEL_NAME", "BAAI/bge-large-zh-v1.5")
)

@app.post("/embed", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest):
    """生成文本嵌入"""
    try:
        embeddings = embedding_service.embed_batch(
            request.texts,
            request.normalize
        )
        
        return EmbeddingResponse(
            embeddings=embeddings,
            model=embedding_service.model_name,
            dimensions=embedding_service.dimension
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model": embedding_service.model_name,
        "device": embedding_service.device,
        "dimensions": embedding_service.dimension
    }
```

### 2. Reranking服务

```yaml
# services/reranking-service/docker-compose.yml
version: '3.8'

services:
  reranking-service:
    build: .
    container_name: reranking-service
    ports:
      - "8002:8002"
    environment:
      - MODEL_NAME=BAAI/bge-reranker-large
      - DEVICE=cuda
      - MAX_LENGTH=512
      - TOP_K=10
    volumes:
      - ./models:/app/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

```python
# services/reranking-service/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import CrossEncoder
import torch
from typing import List, Tuple
import numpy as np

app = FastAPI(title="Reranking Service")

class RerankRequest(BaseModel):
    query: str
    documents: List[str]
    top_k: int = 10

class RerankResponse(BaseModel):
    reranked_documents: List[str]
    scores: List[float]
    indices: List[int]

class RerankingService:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CrossEncoder(model_name, device=self.device)
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10
    ) -> Tuple[List[str], List[float], List[int]]:
        """重排序文档"""
        # 创建查询-文档对
        pairs = [[query, doc] for doc in documents]
        
        # 计算分数
        scores = self.model.predict(pairs)
        
        # 排序
        sorted_indices = np.argsort(scores)[::-1][:top_k]
        
        reranked_docs = [documents[i] for i in sorted_indices]
        reranked_scores = [float(scores[i]) for i in sorted_indices]
        
        return reranked_docs, reranked_scores, sorted_indices.tolist()

# 初始化服务
reranking_service = RerankingService(
    model_name=os.getenv("MODEL_NAME", "BAAI/bge-reranker-large")
)

@app.post("/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest):
    """重排序文档"""
    try:
        docs, scores, indices = reranking_service.rerank(
            request.query,
            request.documents,
            request.top_k
        )
        
        return RerankResponse(
            reranked_documents=docs,
            scores=scores,
            indices=indices
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model": reranking_service.model_name,
        "device": reranking_service.device
    }
```

### 3. 主应用服务

```python
# services/main-app/app.py
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from typing import Optional

from chains.compliance_rag_chain import ComplianceRAGChain
from agents.compliance_agent import ComplianceAgent
from services.llm_service import LLMService, LLMConfig, LLMProvider
from services.vector_store_service import VectorStoreService

# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    app.state.llm_service = LLMService(
        LLMConfig(
            provider=LLMProvider.OPENROUTER,
            model_name="anthropic/claude-3.5-sonnet",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=0.3,
            max_tokens=8000
        )
    )
    
    app.state.vector_store = VectorStoreService(
        embedding_service_url="http://embedding-service:8001",
        vector_db_type="chroma"
    )
    
    app.state.rag_chain = ComplianceRAGChain(
        llm_service=app.state.llm_service,
        retriever=app.state.vector_store.vector_store.as_retriever(
            search_kwargs={"k": 10}
        ),
        reranker=RemoteReranker("http://reranking-service:8002")
    )
    
    app.state.agent = ComplianceAgent(
        llm_service=app.state.llm_service,
        vector_store_service=app.state.vector_store
    )
    
    yield
    
    # 关闭时清理
    await app.state.vector_store.close()

app = FastAPI(
    title="LangChain Compliance Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API端点
@app.post("/api/chat")
async def chat(
    message: str,
    use_agent: bool = False,
    conversation_id: Optional[str] = None
):
    """对话接口"""
    try:
        if use_agent:
            # 使用Agent处理复杂任务
            result = await app.state.agent.run(message)
        else:
            # 使用RAG链处理常规查询
            result = await app.state.rag_chain.process_query(message)
        
        return {
            "status": "success",
            "response": result["answer"],
            "sources": result.get("source_documents", []),
            "conversation_id": conversation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket流式对话"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message")
            
            # 流式生成响应
            async for chunk in app.state.rag_chain.stream_response(message):
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk
                })
            
            await websocket.send_json({
                "type": "done",
                "message": "Response completed"
            })
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()

@app.post("/api/knowledge/upload")
async def upload_document(
    file: UploadFile = File(...),
    purpose: str = "update_knowledge_base"
):
    """上传文档到知识库"""
    try:
        # 保存文件
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 添加到知识库
        result = await app.state.vector_store.add_documents(
            file_path,
            metadata={
                "filename": file.filename,
                "purpose": purpose,
                "upload_time": datetime.now().isoformat()
            }
        )
        
        return {
            "status": "success",
            "message": f"Document {file.filename} uploaded successfully",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "llm": "connected",
            "vector_store": "connected",
            "embedding": "connected",
            "reranking": "connected"
        }
    }
```

## 部署配置

### 1. Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: compliance-frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_WS_URL=ws://localhost:8000
    depends_on:
      - main-app
    networks:
      - compliance-network

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: compliance-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - main-app
    networks:
      - compliance-network

  # 主应用服务
  main-app:
    build:
      context: ./services/main-app
      dockerfile: Dockerfile
    container_name: compliance-main-app
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - DATABASE_URL=postgresql://user:pass@postgres:5432/compliance
      - REDIS_URL=redis://redis:6379
      - VECTOR_DB_URL=http://chroma:8000
      - EMBEDDING_SERVICE_URL=http://embedding-service:8001
      - RERANKING_SERVICE_URL=http://reranking-service:8002
    depends_on:
      - postgres
      - redis
      - chroma
      - embedding-service
      - reranking-service
    networks:
      - compliance-network
    volumes:
      - ./data/uploads:/app/uploads

  # Embedding服务
  embedding-service:
    build:
      context: ./services/embedding-service
      dockerfile: Dockerfile
    container_name: compliance-embedding
    ports:
      - "8001:8001"
    environment:
      - MODEL_NAME=BAAI/bge-large-zh-v1.5
      - DEVICE=cuda
    volumes:
      - ./models/embedding:/app/models
    networks:
      - compliance-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Reranking服务
  reranking-service:
    build:
      context: ./services/reranking-service
      dockerfile: Dockerfile
    container_name: compliance-reranking
    ports:
      - "8002:8002"
    environment:
      - MODEL_NAME=BAAI/bge-reranker-large
      - DEVICE=cuda
    volumes:
      - ./models/reranking:/app/models
    networks:
      - compliance-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # LLM Gateway (可选，用于本地vLLM)
  llm-gateway:
    build:
      context: ./services/llm-gateway
      dockerfile: Dockerfile
    container_name: compliance-llm-gateway
    ports:
      - "8003:8003"
    environment:
      - MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
      - TENSOR_PARALLEL_SIZE=4
      - GPU_MEMORY_UTILIZATION=0.95
    volumes:
      - ./models/llm:/app/models
    networks:
      - compliance-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  # 文档处理服务
  document-processor:
    build:
      context: ./services/document-processor
      dockerfile: Dockerfile
    container_name: compliance-doc-processor
    ports:
      - "8004:8004"
    environment:
      - MAX_FILE_SIZE=50MB
      - OCR_ENABLED=true
    volumes:
      - ./data/documents:/app/documents
    networks:
      - compliance-network

  # 向量数据库 - ChromaDB
  chroma:
    image: chromadb/chroma:latest
    container_name: compliance-chroma
    ports:
      - "8005:8000"
    volumes:
      - ./data/chroma:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - PERSIST_DIRECTORY=/chroma/chroma
      - ANONYMIZED_TELEMETRY=FALSE
    networks:
      - compliance-network

  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    container_name: compliance-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=compliance
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=compliance_db
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    networks:
      - compliance-network

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: compliance-redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    command: redis-server --appendonly yes
    networks:
      - compliance-network

  # 监控 - Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: compliance-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./data/prometheus:/prometheus
    networks:
      - compliance-network

  # 监控 - Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: compliance-grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - ./data/grafana:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    networks:
      - compliance-network

networks:
  compliance-network:
    driver: bridge
    name: compliance-network

volumes:
  postgres_data:
  redis_data:
  chroma_data:
  model_cache:
```

### 2. AWS部署配置

```yaml
# aws/ecs/task-definition.json
{
  "family": "compliance-assistant",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "4096",
  "memory": "8192",
  "containerDefinitions": [
    {
      "name": "main-app",
      "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/compliance-main-app:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENROUTER_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:openrouter-api-key"
        },
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:database-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/compliance-assistant",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "main-app"
        }
      }
    }
  ]
}
```

```yaml
# aws/cloudformation/infrastructure.yml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Compliance Assistant Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues:
      - development
      - staging
      - production

Resources:
  # VPC配置
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true

  # ECS集群
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub compliance-cluster-${Environment}
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT

  # RDS PostgreSQL
  Database:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: !Sub compliance-db-${Environment}
      Engine: postgres
      EngineVersion: '15.4'
      DBInstanceClass: db.r5.xlarge
      AllocatedStorage: 100
      StorageEncrypted: true
      MasterUsername: compliance
      MasterUserPassword: !Ref DBPassword
      VPCSecurityGroups:
        - !Ref DatabaseSecurityGroup

  # ElastiCache Redis
  RedisCluster:
    Type: AWS::ElastiCache::CacheCluster
    Properties:
      CacheNodeType: cache.r6g.xlarge
      Engine: redis
      NumCacheNodes: 1
      VpcSecurityGroupIds:
        - !Ref RedisSecurityGroup

  # S3存储桶
  DocumentBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub compliance-documents-${Environment}
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256

  # Application Load Balancer
  LoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub compliance-alb-${Environment}
      Type: application
      Scheme: internet-facing
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2

  # Auto Scaling
  AutoScalingTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    Properties:
      ServiceNamespace: ecs
      ResourceId: !Sub service/${ECSCluster}/compliance-service
      ScalableDimension: ecs:service:DesiredCount
      MinCapacity: 2
      MaxCapacity: 10

  # CloudWatch Dashboard
  MonitoringDashboard:
    Type: AWS::CloudWatch::Dashboard
    Properties:
      DashboardName: !Sub compliance-monitoring-${Environment}
      DashboardBody: !Sub |
        {
          "widgets": [
            {
              "type": "metric",
              "properties": {
                "metrics": [
                  ["AWS/ECS", "CPUUtilization", {"stat": "Average"}],
                  [".", "MemoryUtilization", {"stat": "Average"}]
                ],
                "period": 300,
                "stat": "Average",
                "region": "${AWS::Region}"
              }
            }
          ]
        }
```

## 前端实现（React）

```typescript
// frontend/src/App.tsx
import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Container, Grid, Paper } from '@mui/material';
import ChatInterface from './components/ChatInterface';
import DocumentUpload from './components/DocumentUpload';
import KnowledgeBase from './components/KnowledgeBase';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { QueryClient, QueryClientProvider } from 'react-query';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <WebSocketProvider>
          <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            <Grid container spacing={3}>
              {/* 聊天界面 */}
              <Grid item xs={12} md={8}>
                <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: '80vh' }}>
                  <ChatInterface />
                </Paper>
              </Grid>
              
              {/* 侧边栏 */}
              <Grid item xs={12} md={4}>
                <Grid container spacing={2}>
                  {/* 文档上传 */}
                  <Grid item xs={12}>
                    <Paper sx={{ p: 2 }}>
                      <DocumentUpload />
                    </Paper>
                  </Grid>
                  
                  {/* 知识库管理 */}
                  <Grid item xs={12}>
                    <Paper sx={{ p: 2 }}>
                      <KnowledgeBase />
                    </Paper>
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </Container>
        </WebSocketProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
```

## 监控与运维

### 1. 监控指标

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'main-app'
    static_configs:
      - targets: ['main-app:8000']
    
  - job_name: 'embedding-service'
    static_configs:
      - targets: ['embedding-service:8001']
    
  - job_name: 'reranking-service'
    static_configs:
      - targets: ['reranking-service:8002']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### 2. 日志聚合

```yaml
# monitoring/fluentd/fluent.conf
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<match app.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
  logstash_prefix compliance
  <buffer>
    @type file
    path /var/log/fluentd-buffers/elasticsearch.buffer
  </buffer>
</match>
```

## 安全配置

### 1. API密钥管理

```python
# config/security.py
from cryptography.fernet import Fernet
import os
from typing import Optional

class SecretManager:
    """密钥管理器"""
    
    def __init__(self):
        self.fernet = Fernet(os.getenv("ENCRYPTION_KEY").encode())
    
    def encrypt_api_key(self, api_key: str) -> str:
        """加密API密钥"""
        return self.fernet.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """解密API密钥"""
        return self.fernet.decrypt(encrypted_key.encode()).decode()
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """获取API密钥"""
        # 优先从环境变量获取
        key = os.getenv(f"{provider.upper()}_API_KEY")
        if key:
            return key
        
        # 从AWS Secrets Manager获取
        if os.getenv("USE_AWS_SECRETS"):
            import boto3
            client = boto3.client('secretsmanager')
            response = client.get_secret_value(SecretId=f"compliance/{provider}/api-key")
            return response['SecretString']
        
        return None
```

### 2. 认证授权

```python
# middleware/auth.py
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

security = HTTPBearer()

class AuthMiddleware:
    """认证中间件"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def create_token(self, user_id: str, role: str = "user") -> str:
        """创建JWT令牌"""
        payload = {
            "user_id": user_id,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def verify_token(self, credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
        """验证JWT令牌"""
        token = credentials.credentials
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
```

## 总结

这个基于LangChain的合规助手方案提供了：

### 优势
1. **灵活的模型支持** - 支持OpenRouter、本地vLLM等多种模型服务
2. **独立的微服务** - Embedding和Reranking服务独立部署，易于扩展
3. **现代化架构** - React前端 + FastAPI后端 + LangChain核心
4. **双重部署支持** - Docker Compose本地部署 + AWS云原生部署
5. **完整的监控** - Prometheus + Grafana监控体系
6. **强大的RAG能力** - 利用LangChain的检索增强生成功能
7. **Agent智能** - 支持复杂任务的自主决策和执行

### 关键特性
- 流式对话支持（WebSocket）
- 父子段文档分割策略
- 多级缓存优化性能
- 完整的API密钥管理
- JWT认证授权
- 自动扩展能力
- 全面的日志和监控

这个方案充分利用了LangChain的生态系统，提供了更灵活、可扩展的架构设计。