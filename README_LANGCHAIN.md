# LangChain Compliance Assistant

A comprehensive compliance assistant built with LangChain, featuring RAG (Retrieval-Augmented Generation), document processing, and knowledge base management.

## 🚀 Quick Start

### One-Click Full System Startup

```bash
# Start all services (recommended)
./start-full-langchain.sh

# Access the application
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### Simple Testing Mode

```bash
# For quick testing without all services
./start-simple.sh

# Stop all services
./stop-services.sh
```

## 📋 Features

- **Document Upload & Processing**: Support for PDF, DOCX, XLSX, PPTX, TXT, MD files
- **Knowledge Base Management**: Automatic document vectorization and storage
- **RAG-based Q&A**: Context-aware responses using your documents
- **Multi-purpose Upload**: 
  - `knowledge_base`: Add documents to permanent knowledge base
  - `business_context`: Use documents for current conversation context
- **Local LLM Support**: Optimized for Apple Silicon with Qwen3-8B-MLX
- **Embedding Service**: Local embeddings with BAAI/bge-base models
- **Reranking**: Improve retrieval accuracy with cross-encoder reranking
- **Vector Store**: ChromaDB for efficient similarity search

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│  Backend    │────▶│  LLM Server │
│   (React)   │     │  (FastAPI)  │     │  (MLX/API)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
            ┌─────────────┐ ┌─────────────┐
            │  Embedding  │ │   Vector    │
            │   Service   │ │   Store     │
            └─────────────┘ │  (ChromaDB) │
                           └─────────────┘
```

## 📦 Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 5173 | React UI with Material-UI |
| Backend API | 8000 | FastAPI with LangChain |
| LLM Server | 8001 | Local MLX model server |
| Embedding | 8002 | Text embedding service |
| Reranking | 8004 | Document reranking service |
| ChromaDB | 8005 | Vector database |
| PostgreSQL | 5432 | Main database |
| Redis | 6379 | Cache and queue |

## 💾 Document Upload Flow

1. **Upload via UI**: Select files and choose purpose
2. **Processing**: Documents are automatically:
   - Extracted (text, tables, metadata)
   - Split into chunks
   - Embedded into vectors
   - Stored in ChromaDB
3. **Knowledge Base Update**: Documents marked as `knowledge_base` are permanently indexed
4. **Query**: Chat interface searches relevant documents and generates responses

## 🧪 Testing

### Test Knowledge Base Upload

```bash
# Run comprehensive test suite
python test_knowledge_base_upload.py

# Quick system check
./quick_test.sh
```

### Manual Testing

1. Start the system: `./start-full-langchain.sh`
2. Open browser: http://localhost:5173
3. Click "Upload" button
4. Select a document
5. Choose purpose: `knowledge_base` or `business_context`
6. Submit and verify processing
7. Ask questions about the uploaded content

## 🔧 Configuration

### Environment Variables (.env)

```bash
# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_BASE=http://localhost:8001/v1
LLM_MODEL=qwen3-8b-mlx

# Embedding Service
EMBEDDING_API_BASE=http://localhost:8002
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5

# Vector Store
VECTOR_STORE_TYPE=chromadb
CHROMA_SERVER_HOST=localhost
CHROMA_SERVER_PORT=8005

# Features
ENABLE_STREAMING=true
ENABLE_AGENT=true
ENABLE_MEMORY=true
ENABLE_RERANKING=true
```

## 📝 API Endpoints

### Document Management

- `POST /api/v1/documents/upload` - Upload single document
- `POST /api/v1/documents/upload-batch` - Upload multiple documents
- `GET /api/v1/documents` - List documents
- `GET /api/v1/documents/{id}` - Get document details
- `DELETE /api/v1/documents/{id}` - Delete document

### Chat & RAG

- `POST /api/v1/chat` - Send message with RAG
- `GET /api/v1/chat/history` - Get chat history
- `WS /ws/chat` - WebSocket for streaming

### Knowledge Base

- `POST /api/v1/knowledge/update` - Update knowledge base
- `GET /api/v1/knowledge/search` - Search knowledge base
- `POST /api/v1/knowledge/query` - Query with context

## 🐛 Troubleshooting

### Services Not Starting

```bash
# Check port availability
lsof -i :8000  # Backend
lsof -i :8001  # LLM
lsof -i :8002  # Embedding

# Check logs
tail -f logs/backend.log
tail -f logs/llm.log
tail -f logs/frontend.log

# Restart everything
./stop-services.sh
./start-full-langchain.sh
```

### Document Upload Issues

1. Check file size (max 50MB by default)
2. Verify file type is supported
3. Check embedding service is running
4. Verify ChromaDB is accessible

### Knowledge Base Not Updating

1. Ensure embedding service is running: `curl http://localhost:8002/health`
2. Check ChromaDB: `curl http://localhost:8005/api/v1`
3. Verify document processing in logs
4. Check vector store configuration in .env

## 🛠️ Development

### Running Individual Services

```bash
# Backend only
cd services/main-app
uvicorn app.main:app --reload

# Frontend only
cd frontend
npm run dev

# LLM Server
python qwen3_api_server.py

# Docker services
docker-compose up -d postgres redis chromadb
```

### Adding New Features

1. Backend: Add endpoints in `services/main-app/app/api/v1/`
2. Frontend: Add components in `frontend/src/components/`
3. LangChain: Modify chains in `services/main-app/app/chains/`
4. Agents: Add tools in `services/main-app/app/agents/tools/`

## 📚 Documentation

- [LangChain Design](docs/LANGCHAIN_COMPLIANCE_ASSISTANT_DESIGN.md)
- [API Documentation](http://localhost:8000/docs)
- [LLM Configuration Guide](docs/LLM_API_CONFIG_GUIDE.md)

## 🔒 Security Notes

- Change default passwords in production
- Use HTTPS for external deployments
- Implement proper authentication
- Secure file upload validation
- Rate limiting on API endpoints

## 📄 License

This project is for demonstration and educational purposes.