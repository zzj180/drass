# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Drass is a hybrid Dify + LangChain compliance assistant platform that combines:
- **Dify Platform**: Core deployment infrastructure using Docker Compose
- **LangChain Implementation**: Custom compliance assistant with RAG and Agent capabilities  
- **Microservices Architecture**: Separate services for document processing, embeddings, and reranking
- **Figma Integration**: UI development assistant that integrates Figma designs with GitHub issues

## Development Commands

### Local LLM Model Setup (Qwen3-8B with MLX)
```bash
# Convert and run Qwen3-8B model
mlx_lm.convert --hf-path local_model_qwen3 --mlx-path mlx_qwen3_converted --dtype bfloat16
python qwen3_api_server.py  # Start API server on port 8001

# Alternative: Use Ollama for model serving
ollama serve                # Start Ollama service
ollama pull qwen2.5:7b      # Download model (if needed)
```

### Frontend (React + TypeScript)
```bash
cd frontend
npm install              # Install dependencies
npm run dev              # Start development server (Vite)
npm run build            # Build for production
npm run lint             # Run ESLint
npm run type-check       # TypeScript type checking
npm run test             # Run tests with Vitest
npm run test:coverage    # Run tests with coverage
```

### Backend (FastAPI + LangChain)
```bash
cd services/main-app
pip install -r requirements.txt    # Install dependencies
uvicorn app.main:app --reload      # Run development server
pytest                              # Run all tests
pytest app/chains/tests/ -v        # Run specific test directory
pytest -m integration               # Run integration tests only
```

### Docker Services
```bash
docker-compose up -d                          # Start all services
docker-compose -f docker-compose.yml up api   # Start specific service
docker-compose logs -f api                    # View logs
docker-compose down                           # Stop all services
docker-compose down -v                        # Stop and remove volumes
```

### Dify Platform Scripts
```bash
python scripts/deploy.py --environment development    # Deploy to development
python scripts/validate.py --all                     # Validate all configs
python scripts/dify-deploy.py --app apps/*.yaml      # Deploy Dify apps
```

### Figma Assistant
```bash
python scripts/figma_cli.py --interactive           # Interactive mode
python scripts/figma_cli.py --file-key YOUR_KEY     # Command line mode
python scripts/figma_webhook.py                     # Start webhook server
./scripts/quick_start.sh                            # Quick start (Chinese)
```

### Testing Commands

#### Backend Unit Tests
```bash
cd services/main-app
pytest -v                                    # Run all tests with verbose output
pytest app/chains/tests/test_rag_chain.py   # Run specific test file
pytest -k "test_multi_query"                # Run tests matching pattern
pytest --cov=app --cov-report=html          # Generate coverage report
```

#### Frontend Tests
```bash
cd frontend
npm run test                                # Run tests in watch mode
npm run test:ui                             # Run tests with UI
npm run test:coverage                       # Generate coverage report
npm test -- --run                           # Run tests once (CI mode)
```

## High-Level Architecture

### System Components

1. **Frontend Layer** (`/frontend`)
   - React 18 with TypeScript and Vite build system
   - Redux Toolkit for state management (slices in `src/store/slices/`)
   - Material-UI theme system with dark/light mode support
   - WebSocket client for real-time features
   - Organized by feature modules with lazy loading

2. **Backend API Layer** (`/services/main-app`)
   - FastAPI framework with full async/await support
   - JWT-based authentication (`app/core/security.py`)
   - Rate limiting and request tracking middleware
   - RESTful API routes in `app/api/v1/`
   - WebSocket support for streaming responses

3. **LangChain Core** (`/services/main-app/app/`)
   - **RAG Chain** (`chains/compliance_rag_chain.py`): Multi-query retrieval with optional reranking
   - **Agent System** (`agents/compliance_agent.py`): Orchestrates specialized agents with tools
   - **Prompt Templates** (`chains/prompts.py`): Compliance-specific prompts for different scenarios
   - Factory patterns for creating specialized chains and agents

4. **Tool Ecosystem** (`/services/main-app/app/agents/tools/`)
   - **Document Tools**: Search, analysis, extraction from documents
   - **Search Tools**: Knowledge base, web, and semantic search
   - **Analysis Tools**: Compliance analysis, risk assessment, gap analysis, checklist generation

5. **Microservices Architecture**
   - **Document Processor** (`/services/doc-processor`): Converts documents to Markdown with OCR
   - **Scheduler Service** (`/services/scheduler`): Task scheduling and workflow orchestration
   - **Dify Platform**: Container-based deployment with PostgreSQL, Redis, Weaviate
   - Model services for embeddings and reranking (configured via environment variables)

### Key Design Patterns

1. **Factory Pattern**: Creating specialized components
   - `ComplianceRAGChainFactory` for different RAG configurations
   - `SpecializedAgentFactory` for domain-specific agents

2. **Orchestrator Pattern**: Complex task coordination
   - `AgentOrchestrator` manages multiple agents
   - Sequential, parallel, and hierarchical execution strategies

3. **Middleware Pipeline**: Request processing
   - Error handling, request ID tracking, rate limiting
   - Structured JSON logging for production

4. **Service Layer**: Business logic separation
   - Services handle core logic
   - API routes handle HTTP concerns only

### Configuration Management

**Environment Variables** (set in `.env` or system):
- **LLM Configuration**: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `OPENROUTER_API_KEY`
  - For local Qwen3-8B: `OPENAI_API_BASE=http://localhost:8001/v1`, `LLM_MODEL=qwen3-8b-mlx`
- **Vector Store**: `VECTOR_STORE_TYPE`, `VECTOR_STORE_HOST`, `CHROMA_PERSIST_DIRECTORY`
- **Embeddings**: `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_API_KEY`
- **Reranking**: `RERANKING_ENABLED`, `RERANKING_PROVIDER`, `RERANKING_API_KEY`
- **Database**: `DATABASE_URL`, `REDIS_URL`, `DB_PASSWORD`
- **Security**: `SECRET_KEY`, `ENCRYPTION_KEY`, `JWT_ALGORITHM`
- **Dify Platform**: `DIFY_PLATFORM_URL`, `DIFY_API_KEY`, `DIFY_WORKSPACE_ID`
- **External APIs**: `FIGMA_ACCESS_TOKEN`, `GITHUB_TOKEN`, `GITHUB_OWNER`

**Settings Module** (`services/main-app/app/core/config.py`):
- Pydantic-based configuration with validation
- Environment-specific settings (development/staging/production)
- Feature flags: `ENABLE_STREAMING`, `ENABLE_AGENT`, `ENABLE_MEMORY`

### Critical Files to Understand

1. **Task Management**: `TASK_LIST_LANGCHAIN.md` - Complete project task breakdown with status tracking
2. **API Entry Point**: `services/main-app/app/main.py` - FastAPI application setup and lifecycle
3. **RAG Implementation**: `services/main-app/app/chains/compliance_rag_chain.py` - Core RAG logic
4. **Agent System**: `services/main-app/app/agents/compliance_agent.py` - Agent orchestration
5. **Frontend State**: `frontend/src/store/index.ts` - Redux store configuration
6. **Docker Services**: `docker-compose.yml` - Complete service definitions
7. **Local LLM Server**: `qwen3_api_server.py` - Flask API server for Qwen3-8B-MLX model
8. **LLM Documentation**: `docs/LLM_API_CONFIG_GUIDE.md` - Detailed LLM setup instructions

### Integration Points

- **LLM Providers**: 
  - OpenRouter for cloud models
  - Local Qwen3-8B-MLX via custom API server
  - Ollama for local model management
- **Vector Stores**: ChromaDB (default), Weaviate, Pinecone, Qdrant support
- **Document Processing**: PDF, DOCX, XLSX, PPTX with OCR capabilities
- **Reranking**: Optional Cohere reranking for improved retrieval accuracy
- **Real-time**: WebSocket support for streaming chat responses

### Testing Strategy

- **Unit Tests**: Mock external dependencies (`pytest`, `vitest`)
- **Integration Tests**: Test with real services (`pytest -m integration`)
- **Test Organization**: Tests colocated with code in `tests/` subdirectories
- **Frontend Testing**: React Testing Library with Vitest

### Current Implementation Status

- ✅ **Frontend**: Complete React architecture with Redux and Material-UI
- ✅ **Backend API**: Full FastAPI implementation with auth and middleware
- ✅ **LangChain RAG**: Streaming-capable RAG chain with multi-query support
- ✅ **Agent System**: Comprehensive tool set with specialized agents
- ✅ **Local LLM**: Qwen3-8B-MLX model converted and API server implemented
- 📋 **Deployment**: Docker Compose ready, AWS infrastructure documented in `AWS_DEPLOYMENT_RESOURCES.md`

### Common Development Workflows

#### Starting the Full Stack with Local LLM
```bash
# Start local Qwen3-8B model server
python qwen3_api_server.py  # Runs on port 8001

# Start all Docker services (Dify, PostgreSQL, Redis, Weaviate)
docker-compose up -d

# Start backend API server
cd services/main-app
uvicorn app.main:app --reload --port 8000

# Start frontend development server
cd frontend
npm run dev
```

#### Adding a New LangChain Tool
1. Create tool in `services/main-app/app/agents/tools/`
2. Register in `services/main-app/app/agents/tool_registry.py`
3. Update agent configuration in `compliance_agent.py`
4. Add tests in corresponding `tests/` directory

#### Modifying the RAG Pipeline
1. Core logic: `services/main-app/app/chains/compliance_rag_chain.py`
2. Prompts: `services/main-app/app/chains/prompts.py`
3. Retrieval config: `services/main-app/app/core/config.py` (embedding/reranking settings)

### Project-Specific Conventions

- **API Versioning**: All API routes under `/api/v1/` prefix
- **Error Handling**: Use custom exceptions in `app/core/exceptions.py`
- **Logging**: Structured JSON logging configured in `app/core/logging.py`
- **State Management**: Redux slices organized by feature in `frontend/src/store/slices/`
- **Component Structure**: Feature-based organization with lazy loading
- **Test Files**: Colocated with source code in `tests/` subdirectories
- **Environment Files**: `.env` for local development, never commit secrets