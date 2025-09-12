# 一键启动指南 / One-Click Startup Guide

## 概述 / Overview

本项目提供多种一键启动脚本，根据不同的测试需求选择使用：

This project provides multiple one-click startup scripts for different testing needs:

| 脚本 Script | 用途 Purpose | 复杂度 Complexity | 推荐场景 Recommended Use |
|------------|-------------|-------------------|-------------------------|
| `./start-simple.sh` | 简化版快速测试 | 低 Low | UI开发、基础功能测试 |
| `./start-langchain.sh` | 完整LangChain架构 | 高 High | RAG/Agent功能测试 |
| `./quick_start.sh` | Docker容器化部署 | 中 Medium | 生产环境模拟 |

## 🚀 快速开始 / Quick Start

### 方法一：简化版启动（推荐用于快速测试）
### Method 1: Simple Startup (Recommended for Quick Testing)

```bash
# 一键启动所有服务
# Start all services with one command
./start-simple.sh

# 停止所有服务
# Stop all services
./stop-services.sh
```

**特点 Features:**
- ✅ 自动安装依赖 / Auto-install dependencies
- ✅ 自动修复已知问题 / Auto-fix known issues
- ✅ 自动清理端口冲突 / Auto-clean port conflicts
- ✅ 实时日志监控 / Real-time log monitoring
- ✅ 服务健康检查 / Service health checks

### 方法二：完整LangChain架构启动
### Method 2: Full LangChain Architecture

```bash
# 启动完整系统（包含RAG、Agent等）
# Start full system (including RAG, Agent, etc.)
./start-langchain.sh

# 检查系统就绪状态
# Check system readiness
./check-readiness.sh
```

**特点 Features:**
- ✅ 完整功能支持 / Full feature support
- ✅ Docker容器化 / Docker containerized
- ✅ 微服务架构 / Microservices architecture
- ⚠️ 需要更多资源 / Requires more resources

## 📋 服务架构 / Service Architecture

### 简化版架构 (start-simple.sh)
```
┌─────────────────────────────────────────┐
│   Frontend (React)                      │
│   http://localhost:3000                 │
└─────────────────┬───────────────────────┘
                  │ HTTP/REST
┌─────────────────▼───────────────────────┐
│   Backend API (FastAPI)                 │
│   http://localhost:8080                 │
│   - /api/v1/chat                        │
│   - /health                             │
│   - /docs                               │
└─────────────────┬───────────────────────┘
                  │ HTTP/REST
┌─────────────────▼───────────────────────┐
│   Local LLM (Qwen3-8B-MLX)             │
│   http://localhost:8001                 │
│   - OpenAI Compatible API               │
└─────────────────────────────────────────┘
```

### 完整架构 (start-langchain.sh)
```
┌─────────────────────────────────────────┐
│   Frontend (React)                      │
│   http://localhost:5173                 │
└─────────────────┬───────────────────────┘
                  │ WebSocket + REST
┌─────────────────▼───────────────────────┐
│   Main App (FastAPI + LangChain)        │
│   http://localhost:8000                 │
│   - RAG Chain                           │
│   - Agent System                        │
│   - Document Processing                 │
└──────┬──────────┬──────────┬────────────┘
       │          │          │
┌──────▼────┐ ┌──▼───┐ ┌────▼────┐
│ ChromaDB  │ │Redis │ │PostgreSQL│
│ (Vector)  │ │Cache │ │Database  │
└───────────┘ └──────┘ └──────────┘
```

## 🛠️ 启动脚本详解 / Startup Script Details

### start-simple.sh 功能
### start-simple.sh Features

1. **依赖检查与安装 / Dependency Check & Install**
   ```bash
   # 自动检测并安装缺失的Python包
   # Auto-detect and install missing Python packages
   - flask
   - mlx-lm
   - fastapi
   - uvicorn
   - httpx
   - pydantic
   ```

2. **端口清理 / Port Cleanup**
   ```bash
   # 自动清理占用的端口
   # Auto-clean occupied ports
   - 3000 (Frontend)
   - 8080 (Backend)
   - 8001 (LLM)
   ```

3. **问题修复 / Issue Fixes**
   ```bash
   # 自动修复已知问题
   # Auto-fix known issues
   - highlight.js import error
   - API endpoint configuration
   ```

4. **服务启动顺序 / Service Startup Order**
   ```
   1. LLM Server (port 8001)
      ↓ wait for ready
   2. Backend API (port 8080)
      ↓ wait for ready
   3. Frontend (port 3000)
      ↓ wait for ready
   4. Health checks
   ```

## 📊 服务状态检查 / Service Status Check

### 手动检查服务状态
### Manual Service Status Check

```bash
# 检查LLM服务
# Check LLM service
curl http://localhost:8001/health

# 检查后端API
# Check backend API
curl http://localhost:8080/health

# 检查前端
# Check frontend
curl http://localhost:3000

# 测试聊天功能
# Test chat functionality
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### 查看日志
### View Logs

```bash
# 实时查看所有日志
# View all logs in real-time
tail -f logs/*.log

# 查看特定服务日志
# View specific service logs
tail -f logs/llm.log      # LLM日志
tail -f logs/backend.log  # 后端日志
tail -f logs/frontend.log # 前端日志
```

## 🔧 故障排除 / Troubleshooting

### 常见问题及解决方案
### Common Issues and Solutions

| 问题 Issue | 原因 Cause | 解决方案 Solution |
|-----------|-----------|------------------|
| 端口被占用 | 其他进程占用端口 | 运行 `./stop-services.sh` 或手动 `kill $(lsof -ti:PORT)` |
| LLM启动失败 | 模型文件缺失 | 确保已运行模型转换脚本 |
| 前端报错 | 依赖未安装 | 在frontend目录运行 `npm install` |
| API连接失败 | CORS问题 | 检查backend的CORS配置 |
| 内存不足 | LLM占用内存过大 | 关闭其他应用或使用更小的模型 |

### 手动启动流程（如果脚本失败）
### Manual Startup Process (If Script Fails)

```bash
# 1. 启动LLM服务
cd /Users/arthurren/projects/drass
python qwen3_api_server.py &

# 2. 启动后端API
python simple_backend.py --port 8080 &

# 3. 修复前端问题
cd frontend
# 编辑 src/components/ChatInterface/MarkdownRenderer.tsx
# 删除 import 'highlight.js/styles/github-dark.css'
# 编辑 src/components/ChatInterface/ChatInterface.tsx
# 更新 fetch URL 为 http://localhost:8080/api/v1/chat

# 4. 启动前端
npm run dev
```

## 📈 性能优化建议 / Performance Optimization

1. **内存管理**
   - LLM服务约占用 8-10GB 内存
   - 建议系统至少有 16GB RAM
   - 可通过环境变量限制模型内存使用

2. **端口配置**
   - 可通过环境变量自定义端口
   ```bash
   export FRONTEND_PORT=3001
   export BACKEND_PORT=8081
   export LLM_PORT=8002
   ./start-simple.sh
   ```

3. **日志管理**
   - 日志文件会持续增长
   - 建议定期清理：`rm -rf logs/*.log`
   - 或使用日志轮转：`logrotate`

## 🚢 生产部署 / Production Deployment

生产环境建议使用Docker Compose部署：

For production, use Docker Compose deployment:

```bash
# 使用Docker Compose启动
# Start with Docker Compose
docker-compose up -d

# 或使用Kubernetes
# Or use Kubernetes
kubectl apply -f k8s/
```

详见 [AWS部署文档](./AWS_DEPLOYMENT_RESOURCES.md)

See [AWS Deployment Guide](./AWS_DEPLOYMENT_RESOURCES.md) for details.

## 📝 更新历史 / Update History

| 日期 Date | 版本 Version | 更新内容 Updates |
|----------|-------------|-----------------|
| 2025-01-12 | v1.0 | 初始版本，简化启动流程 |
| 2025-01-12 | v1.1 | 添加自动问题修复功能 |
| 2025-01-12 | v1.2 | 集成健康检查和日志监控 |

## 🤝 贡献指南 / Contributing

欢迎提交问题和改进建议：

Welcome to submit issues and suggestions:

1. Fork 本仓库 / Fork this repository
2. 创建功能分支 / Create feature branch
3. 提交更改 / Commit changes
4. 发起 Pull Request / Create Pull Request

## 📄 许可证 / License

MIT License - 详见 [LICENSE](../LICENSE) 文件