# Drass 项目架构分析与依赖关系图

## 一、项目概述

Drass 是一个混合 Dify + LangChain 合规助手平台，采用微服务架构：

- **Dify Platform**: 核心部署基础设施 (Docker Compose)
- **LangChain Implementation**: 自定义合规助手，支持 RAG 和 Agent 能力
- **Microservices Architecture**: 文档处理、嵌入和重排序的独立服务
- **Figma Integration**: UI 开发助手，集成 Figma 设计与 GitHub issues

---

## 二、系统整体架构图

```mermaid
flowchart TB
    subgraph CLIENT["🖥️ 客户端层"]
        direction TB
        FE[React Frontend<br/>端口:5173]
        FE_VITE[Vite Build<br/>开发服务器]
        FE_REACT[React 18<br/>TypeScript]
        FE_REDUX[Redux Toolkit<br/>状态管理]
        FE_MUI[Material-UI<br/>主题系统]
        FE_WS[WebSocket<br/>实时通信]
    end
    
    subgraph API_GW["🌐 API 网关层"]
        direction TB
        FAST[FastAPI<br/>端口:8000]
        AUTH[JWT Auth<br/>认证授权]
        MID[Middleware<br/>限流/日志/追踪]
        ROUTES[API Routes<br/>/api/v1/]
        WS[WebSocket<br/>流式响应]
    end
    
    subgraph LANGCHAIN["🔗 LangChain 核心层"]
        direction TB
        RAG[RAG Chain<br/>compliance_rag_chain.py]
        RAG_SUB[Multi-Query<br/>Reranking<br/>Streaming]
        AGENT[Agent System<br/>compliance_agent.py]
        AGENT_SUB[Tool Orchestration<br/>Agent Factory]
        PROMPTS[Prompt Templates<br/>prompts.py<br/>compliance_prompts.py]
        FACTORY[Factory Pattern<br/>ComplianceRAGChainFactory<br/>SpecializedAgentFactory]
    end
    
    subgraph TOOLS["🛠️ 工具生态层"]
        direction TB
        DT[Document Tools<br/>搜索/分析/提取]
        ST[Search Tools<br/>知识库/语义搜索]
        AT[Analysis Tools<br/>合规/风险/差距分析]
    end
    
    subgraph SERVICES["⚙️ 微服务层"]
        direction TB
        EMB[Embedding Service<br/>端口:8002]
        DOC[Doc Processor<br/>文档处理]
        SCH[Scheduler<br/>任务调度]
    end
    
    subgraph PLATFORM["📦 Dify 平台"]
        direction TB
        DIFY[Dify Platform<br/>Docker]
        DIFY_SUB[PostgreSQL<br/>Redis<br/>Weaviate]
    end
    
    subgraph LLM["🤖 模型层"]
        direction TB
        QWEN[Qwen3-8B-MLX<br/>端口:8001]
        OLLAMA[Ollama<br/>本地模型]
        OPEN[OpenRouter<br/>云端模型]
    end
    
    subgraph STORAGE["💾 数据层"]
        direction TB
        CHROMA[ChromaDB<br/>向量存储]
        VECTOR[Vector Store<br/>ChromaDB/Weaviate<br/>Pinecone/Qdrant]
    end

    %% 依赖关系
    FE --> FE_VITE
    FE --> FE_REACT
    FE_REACT --> FE_REDUX
    FE_REACT --> FE_MUI
    FE --> FE_WS
    
    FE --> FAST
    
    FAST --> AUTH
    FAST --> MID
    FAST --> ROUTES
    FAST --> WS
    
    ROUTES --> RAG
    ROUTES --> AGENT
    
    RAG --> RAG_SUB
    RAG --> PROMPTS
    RAG --> CHROMA
    RAG --> EMB
    RAG --> FACTORY
    
    AGENT --> AGENT_SUB
    AGENT --> PROMPTS
    AGENT --> DT
    AGENT --> ST
    AGENT --> AT
    AGENT --> FACTORY
    
    DT --> CHROMA
    ST --> CHROMA
    AT --> LLM
    
    EMB --> CHROMA
    DOC --> CHROMA
    SCH --> DIFY_SUB
    
    DIFY --> DIFY_SUB
    
    QWEN --> CHROMA
    OLLAMA --> CHROMA
    OPEN --> CHROMA
    
    CHROMA --> VECTOR
```

---

## 三、核心依赖关系图

```mermaid
flowchart LR
    subgraph L1["第1层: 用户交互"]
        USER[用户 Browser]
    end
    
    subgraph L2["第2层: 前端应用"]
        direction TB
        REACT[React 18<br/>TypeScript<br/>Vite]
        REDUX[Redux Toolkit<br/>状态管理]
        MUI[Material-UI<br/>主题系统]
    end
    
    subgraph L3["第3层: API 网关"]
        direction TB
        FASTAPI[FastAPI<br/>异步框架]
        JWT[JWT 认证]
        RATE[Rate Limiting<br/>限流]
        TRACK[Request Tracking<br/>请求追踪]
    end
    
    subgraph L4["第4层: 业务逻辑"]
        direction TB
        RAG[RAG Chain<br/>多查询检索<br/>重排序]
        AGENT[Agent System<br/>工具编排<br/>代理工厂]
    end
    
    subgraph L5["第5层: 工具服务"]
        direction TB
        DOC[文档工具]
        SEARCH[搜索工具]
        ANALYZE[分析工具]
    end
    
    subgraph L6["第6层: 微服务"]
        direction TB
        EMB[Embedding]
        DOC_PROC[文档处理]
        SCHED[调度服务]
    end
    
    subgraph L7["第7层: 基础设施"]
        direction TB
        LLM_PROV[LLM 提供商]
        VECTOR_DB[(向量数据库)]
        REL_DB[(关系数据库)]
    end

    USER --> REACT
    REACT --> REDUX
    REACT --> MUI
    REDUX --> FASTAPI
    FASTAPI --> JWT
    FASTAPI --> RATE
    FASTAPI --> TRACK
    JWT --> RAG
    JWT --> AGENT
    RAG --> DOC
    RAG --> SEARCH
    RAG --> ANALYZE
    AGENT --> DOC
    AGENT --> SEARCH
    AGENT --> ANALYZE
    DOC --> EMB
    SEARCH --> EMB
    ANALYZE --> LLM_PROV
    EMB --> VECTOR_DB
    DOC_PROC --> REL_DB
    SCHED --> REL_DB
```

---

## 四、模块间依赖关系详细图

```mermaid
flowchart TB
    subgraph FRONTEND["前端模块 (frontend)"]
        direction TB
        FE_APP[App.tsx<br/>根组件]
        FE_ROUTER[React Router<br/>路由管理]
        FE_STORE[Redux Store<br/>状态管理]
        FE_CHAT[chatSlice.ts<br/>聊天状态]
        FE_CONFIG[configSlice.ts<br/>配置状态]
        FE_COMPONENTS[Components<br/>UI 组件]
        FE_API[API Client<br/>Axios]
        FE_WS[WebSocket<br/>实时通信]
    end
    
    subgraph BACKEND["后端模块 (services/main-app)"]
        direction TB
        BE_MAIN[main.py<br/>FastAPI 入口]
        BE_CORE[core/<br/>核心模块]
        BE_CONFIG[config.py<br/>配置管理]
        BE_SECURITY[security.py<br/>安全模块]
        BE_LOGGING[logging.py<br/>日志模块]
        BE_EXCEPT[exceptions.py<br/>异常处理]
        BE_API[api/v1/<br/>API 路由]
        BE_CHAT[chat.py<br/>聊天接口]
        BE_AUTH[auth.py<br/>认证接口]
    end
    
    subgraph LANGCHAIN_CORE["LangChain 核心"]
        direction TB
        LC_CHAINS[chains/<br/>链模块]
        LC_RAG[compliance_rag_chain.py<br/>RAG 链]
        LC_PROMPTS[prompts.py<br/>提示模板]
        LC_COMPLIANCE_PROMPTS[compliance_prompts.py<br/>合规提示]
        LC_AGENTS[agents/<br/>代理模块]
        LC_AGENT[compliance_agent.py<br/>代理系统]
        LC_TOOLS[tools/<br/>工具集]
        LC_DOC_TOOLS[document_tools.py<br/>文档工具]
        LC_SEARCH_TOOLS[search_tools.py<br/>搜索工具]
        LC_ANALYSIS_TOOLS[analysis_tools.py<br/>分析工具]
        LC_REGISTRY[tool_registry.py<br/>工具注册]
    end
    
    subgraph SERVICES["微服务"]
        direction TB
        SVC_EMB[embedding-service<br/>嵌入服务]
        SVC_DOC[doc-processor<br/>文档处理]
        SVC_SCH[scheduler<br/>调度服务]
    end
    
    subgraph LLM["模型层"]
        direction TB
        LLM_QWEN[Qwen3-8B-MLX<br/>本地模型]
        LLM_OLLAMA[Ollama<br/>本地模型]
        LLM_OPENROUTER[OpenRouter<br/>云端模型]
    end
    
    subgraph STORAGE["数据层"]
        direction TB
        DB_CHROMA[ChromaDB<br/>向量存储]
        DB_WEAVIATE[Weaviate<br/>向量存储]
        DB_POSTGRES[PostgreSQL<br/>关系数据库]
        DB_REDIS[Redis<br/>缓存]
    end

    %% 前端内部依赖
    FE_APP --> FE_ROUTER
    FE_APP --> FE_STORE
    FE_STORE --> FE_CHAT
    FE_STORE --> FE_CONFIG
    FE_ROUTER --> FE_COMPONENTS
    FE_COMPONENTS --> FE_API
    FE_COMPONENTS --> FE_WS
    
    %% 前端到后端
    FE_API --> BE_MAIN
    FE_WS --> BE_MAIN
    
    %% 后端内部依赖
    BE_MAIN --> BE_CORE
    BE_MAIN --> BE_API
    BE_CORE --> BE_CONFIG
    BE_CORE --> BE_SECURITY
    BE_CORE --> BE_LOGGING
    BE_CORE --> BE_EXCEPT
    BE_API --> BE_CHAT
    BE_API --> BE_AUTH
    BE_AUTH --> BE_SECURITY
    
    %% 后端到 LangChain
    BE_CHAT --> LC_CHAINS
    BE_CHAT --> LC_AGENTS
    LC_CHAINS --> LC_RAG
    LC_CHAINS --> LC_PROMPTS
    LC_CHAINS --> LC_COMPLIANCE_PROMPTS
    LC_AGENTS --> LC_AGENT
    LC_AGENT --> LC_TOOLS
    LC_TOOLS --> LC_DOC_TOOLS
    LC_TOOLS --> LC_SEARCH_TOOLS
    LC_TOOLS --> LC_ANALYSIS_TOOLS
    LC_TOOLS --> LC_REGISTRY
    
    %% LangChain 到服务
    LC_RAG --> SVC_EMB
    LC_DOC_TOOLS --> SVC_DOC
    
    %% LangChain 到模型
    LC_RAG --> LLM_QWEN
    LC_AGENT --> LLM_QWEN
    LC_ANALYSIS_TOOLS --> LLM_QWEN
    LLM_QWEN --> LLM_OLLAMA
    LLM_QWEN --> LLM_OPENROUTER
    
    %% LangChain 到存储
    LC_RAG --> DB_CHROMA
    LC_DOC_TOOLS --> DB_CHROMA
    LC_SEARCH_TOOLS --> DB_CHROMA
    SVC_DOC --> DB_POSTGRES
    SVC_SCH --> DB_REDIS
    DB_CHROMA --> DB_WEAVIATE
```

---

## 五、数据流架构图

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as Frontend
    participant A as FastAPI
    participant R as RAG Chain
    participant T as Tools
    participant L as LLM
    participant V as Vector Store

    U->>F: 1. 输入查询
    F->>A: 2. POST /api/v1/chat
    A->>R: 3. 调用 RAG Chain
    R->>V: 4. 相似度检索
    V-->>R: 5. 返回文档
    R->>T: 6. 工具处理
    T->>L: 7. 生成回答
    L-->>T: 8. 返回结果
    T-->>R: 9. 处理后结果
    R-->>A: 10. 流式响应
    A-->>F: 11. WebSocket 流
    F-->>U: 12. 实时显示
```

---

## 六、配置管理依赖图

```mermaid
flowchart LR
    subgraph ENV["环境变量配置"]
        direction TB
        LLM[LLM 配置<br/>LLM_PROVIDER<br/>LLM_API_KEY<br/>LLM_BASE_URL]
        EMB[Embeddings<br/>EMBEDDING_PROVIDER<br/>EMBEDDING_API_KEY]
        VEC[向量存储<br/>VECTOR_STORE_TYPE<br/>CHROMA_PERSIST_DIRECTORY]
        DB[数据库<br/>DATABASE_URL<br/>REDIS_URL]
        SEC[安全配置<br/>SECRET_KEY<br/>JWT_ALGORITHM]
        DIFY[Dify 配置<br/>DIFY_PLATFORM_URL<br/>DIFY_API_KEY]
    end
    
    subgraph CONFIG["配置模块"]
        CFG[config.py<br/>Pydantic 验证<br/>环境特定设置<br/>功能开关]
    end
    
    subgraph FEATURE["功能开关"]
        direction TB
        STREAM[ENABLE_STREAMING]
        AGENT[ENABLE_AGENT]
        MEM[ENABLE_MEMORY]
    end

    LLM --> CFG
    EMB --> CFG
    VEC --> CFG
    DB --> CFG
    SEC --> CFG
    DIFY --> CFG
    
    CFG --> STREAM
    CFG --> AGENT
    CFG --> MEM
```

---

## 七、设计模式类图

```mermaid
classDiagram
    %% Factory Pattern
    class ComplianceRAGChainFactory {
        +create_chain() ComplianceRAGChain
        +create_with_reranking() ComplianceRAGChain
        +create_streaming() StreamingRAGChain
    }
    
    class SpecializedAgentFactory {
        +create_agent() BaseAgent
        +create_compliance_agent() ComplianceAgent
        +create_analysis_agent() AnalysisAgent
    }
    
    %% Orchestrator Pattern
    class AgentOrchestrator {
        +execute_sequential()
        +execute_parallel()
        +execute_hierarchical()
    }
    
    %% Service Layer
    class BaseService {
        +core_logic()
    }
    
    class APIRoute {
        +handle_http()
    }
    
    %% Relationships
    ComplianceRAGChainFactory ..> RAGChain : creates
    SpecializedAgentFactory ..> BaseAgent : creates
    AgentOrchestrator --> BaseAgent : manages
    APIRoute --> BaseService : uses
```

---

## 八、Docker 部署架构图

```mermaid
flowchart TB
    subgraph DOCKER["Docker Compose"]
        subgraph FRONTEND["Frontend Container"]
            FE[React App<br/>:5173]
        end
        
        subgraph BACKEND["Backend Container"]
            API[FastAPI<br/>:8000]
        end
        
        subgraph LLM["LLM Container"]
            QWEN[Qwen3 API<br/>:8001]
        end
        
        subgraph EMB["Embedding Container"]
            EMB_SVC[Embedding<br/>Service:8002]
        end
        
        subgraph DIFY_PLATFORM["Dify Platform"]
            DIFY[Dify<br/>Docker]
            PG[PostgreSQL<br/>:5432]
            REDIS[Redis<br/>:6379]
            WEAV[Weaviate<br/>:8080]
        end
    end

    FE --> API
    API --> QWEN
    API --> EMB_SVC
    API --> DIFY
    DIFY --> PG
    DIFY --> REDIS
    DIFY --> WEAV
```

---

## 九、实体关系图

```mermaid
erDiagram
    CLIENT ||--o| FRONTEND : uses
    FRONTEND ||--o| FASTAPI : calls
    FASTAPI ||--o| RAG_CHAIN : invokes
    FASTAPI ||--o| AGENT : invokes
    RAG_CHAIN ||--o| PROMPTS : uses
    RAG_CHAIN ||--o| VECTOR_STORE : queries
    RAG_CHAIN ||--o| LLM : calls
    AGENT ||--o| TOOLS : uses
    AGENT ||--o| LLM : calls
    TOOLS ||--o| VECTOR_STORE : queries
    LLM ||--o| LLM_PROVIDER : connects
    VECTOR_STORE ||--o| CHROMA : stores
    FASTAPI ||--o| DIFY : integrates
    DIFY ||--o| DATABASE : uses
    DIFY ||--o| REDIS : uses
```

---

## 十、项目结构树

```mermaid
mindmap
  root((Drass 项目))
    前端(frontend/)
      src/
        store/slices/
          chatSlice.ts
          configSlice.ts
        components/
        pages/
      package.json
      vite.config.ts
    后端(services/main-app/)
      app/
        main.py
        core/
          config.py
          security.py
          logging.py
          exceptions.py
        api/v1/
          chat.py
          auth.py
        chains/
          compliance_rag_chain.py
          prompts.py
          compliance_prompts.py
        agents/
          compliance_agent.py
          tool_registry.py
          tools/
            document_tools.py
            search_tools.py
            analysis_tools.py
        services/
      requirements.txt
    微服务(services/)
      embedding-service/
      doc-processor/
      scheduler/
    脚本(scripts/)
      deploy.py
      validate.py
      figma_cli.py
    配置
      docker-compose.yml
      .env
      CLAUDE.md
```

---

## 十一、架构总结表

| 层级 | 组件 | 技术栈 | 端口 | 依赖关系 |
|------|------|--------|------|----------|
| 客户端 | React Frontend | React 18 + TypeScript + Redux + MUI | 5173 | → API 网关 |
| API 网关 | FastAPI | FastAPI + JWT + WebSocket | 8000 | → LangChain |
| 业务逻辑 | LangChain | RAG Chain + Agent System | - | → 工具层 |
| 工具生态 | Tools | Document + Search + Analysis | - | → 微服务 |
| 微服务 | Services | Embedding + Doc Processor + Scheduler | 8002+ | → 模型层 |
| 模型层 | LLM | Qwen3-8B-MLX + Ollama + OpenRouter | 8001 | → 数据层 |
| 数据层 | Storage | ChromaDB + Weaviate + PostgreSQL + Redis | - | 底层 |

### 核心设计模式

1. **Factory Pattern**: `ComplianceRAGChainFactory`, `SpecializedAgentFactory`
2. **Orchestrator Pattern**: `AgentOrchestrator` 管理多 Agent
3. **Middleware Pipeline**: 错误处理、请求追踪、限流
4. **Service Layer**: 业务逻辑与 HTTP 关注点分离