#!/bin/bash

# 生产环境性能优化脚本

echo "⚡ 开始生产环境性能优化..."

# 1. 创建生产环境数据目录
echo "📁 创建生产环境目录..."
mkdir -p /home/qwkj/drass/data/chromadb_production
mkdir -p /home/qwkj/drass/data/uploads_production
mkdir -p /home/qwkj/drass/logs/production
mkdir -p /home/qwkj/drass/backups/production

# 2. 优化SQLite配置
echo "🗄️ 优化数据库配置..."

# 创建SQLite优化配置
cat > /home/qwkj/drass/config/production/sqlite_optimize.sql << 'SQL'
-- SQLite性能优化
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456;
PRAGMA optimize;
SQL

# 3. 创建启动优化脚本
cat > /home/qwkj/drass/scripts/start_production.sh << 'START'
#!/bin/bash

# 生产环境启动脚本

echo "🚀 启动生产环境服务..."

# 设置环境变量
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
export WORKERS=4

# 创建生产环境数据目录
mkdir -p /home/qwkj/drass/data/chromadb_production
mkdir -p /home/qwkj/drass/data/uploads_production
mkdir -p /home/qwkj/drass/logs/production

# 启动VLLM服务
echo "启动VLLM服务..."
cd /home/qwkj/drass
nohup python3 -m vllm.entrypoints.openai.api_server \
    --model /home/qwkj/drass/models/DeepSeek-R1-0528-Qwen3-8B \
    --host 0.0.0.0 \
    --port 8001 \
    --api-key 123456 \
    --served-model-name vllm \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.8 \
    --tensor-parallel-size 1 \
    --trust-remote-code \
    > logs/vllm_production.log 2>&1 &

# 启动嵌入服务
echo "启动嵌入服务..."
nohup python3 -m vllm.entrypoints.openai.api_server \
    --model /home/qwkj/drass/models/Qwen3-Embedding-8B \
    --host 0.0.0.0 \
    --port 8010 \
    --api-key 123456 \
    --served-model-name Qwen3-Embedding-8B \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.6 \
    --tensor-parallel-size 1 \
    --trust-remote-code \
    > logs/embedding_production.log 2>&1 &

# 启动ChromaDB
echo "启动ChromaDB..."
nohup chroma run --host 0.0.0.0 --port 8005 --path /home/qwkj/drass/data/chromadb_production \
    > logs/chromadb_production.log 2>&1 &

# 等待服务启动
echo "等待服务启动..."
sleep 30

# 启动后端API（使用生产配置）
echo "启动后端API..."
cd /home/qwkj/drass/services/main-app
nohup uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8888 \
    --workers 4 \
    --env-file /home/qwkj/drass/config/production/backend.env \
    > ../../logs/production/backend.log 2>&1 &

# 启动前端
echo "启动前端服务..."
cd /home/qwkj/drass/frontend
nohup npm run build && npm run preview -- --host 0.0.0.0 --port 5173 \
    > ../logs/production/frontend.log 2>&1 &

echo "✅ 生产环境服务启动完成！"
echo "🌐 访问地址: http://localhost:5173"
echo "📊 监控地址: http://localhost:9090"
echo "📋 日志目录: /home/qwkj/drass/logs/production/"
START

chmod +x /home/qwkj/drass/scripts/start_production.sh

# 5. 创建健康检查脚本
echo "🏥 创建健康检查脚本..."

cat > /home/qwkj/drass/scripts/health_check_production.sh << 'HEALTH'
#!/bin/bash

# 生产环境健康检查脚本

echo "🏥 执行生产环境健康检查..."

# 检查服务状态
check_service() {
    local service_name=$1
    local port=$2
    local endpoint=${3:-"/health"}
    
    if curl -s -f "http://localhost:$port$endpoint" > /dev/null; then
        echo "✅ $service_name (端口 $port) - 正常"
        return 0
    else
        echo "❌ $service_name (端口 $port) - 异常"
        return 1
    fi
}

# 检查所有服务
echo "检查服务状态..."
check_service "VLLM服务" 8001 "/health"
check_service "嵌入服务" 8010 "/health"
check_service "ChromaDB" 8005 "/api/v1/heartbeat"
check_service "后端API" 8888 "/health"
check_service "前端服务" 5173

# 检查系统资源
echo "检查系统资源..."
echo "CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "内存使用率: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
echo "磁盘使用率: $(df -h / | awk 'NR==2{print $5}')"

# 检查日志错误
echo "检查最近错误..."
if [ -f "/home/qwkj/drass/logs/production/backend.log" ]; then
    error_count=$(tail -n 100 /home/qwkj/drass/logs/production/backend.log | grep -c "ERROR\|CRITICAL" || echo "0")
    echo "最近100行日志中的错误数量: $error_count"
fi

echo "✅ 健康检查完成"
HEALTH

chmod +x /home/qwkj/drass/scripts/health_check_production.sh

# 6. 创建停止脚本
echo "🛑 创建停止脚本..."

cat > /home/qwkj/drass/scripts/stop_production.sh << 'STOP'
#!/bin/bash

# 生产环境停止脚本

echo "🛑 停止生产环境服务..."

# 停止后端API
echo "停止后端API..."
pkill -f "uvicorn.*main:app" || true

# 停止前端
echo "停止前端服务..."
pkill -f "npm.*preview" || true

# 停止VLLM服务
echo "停止VLLM服务..."
pkill -f "vllm.*api_server.*8001" || true

# 停止嵌入服务
echo "停止嵌入服务..."
pkill -f "vllm.*api_server.*8010" || true

# 停止ChromaDB
echo "停止ChromaDB..."
pkill -f "chroma.*run.*8005" || true

echo "✅ 生产环境服务已停止"
STOP

chmod +x /home/qwkj/drass/scripts/stop_production.sh

# 7. 创建日志查看脚本
echo "📋 创建日志查看脚本..."

cat > /home/qwkj/drass/scripts/view_logs_production.sh << 'LOGS'
#!/bin/bash

# 生产环境日志查看脚本

echo "📋 生产环境日志查看工具"
echo "=========================="

case "$1" in
    "backend")
        echo "查看后端日志..."
        tail -f /home/qwkj/drass/logs/production/backend.log
        ;;
    "frontend")
        echo "查看前端日志..."
        tail -f /home/qwkj/drass/logs/production/frontend.log
        ;;
    "vllm")
        echo "查看VLLM日志..."
        tail -f /home/qwkj/drass/logs/vllm_production.log
        ;;
    "embedding")
        echo "查看嵌入服务日志..."
        tail -f /home/qwkj/drass/logs/embedding_production.log
        ;;
    "chromadb")
        echo "查看ChromaDB日志..."
        tail -f /home/qwkj/drass/logs/chromadb_production.log
        ;;
    "all")
        echo "查看所有日志..."
        tail -f /home/qwkj/drass/logs/production/*.log /home/qwkj/drass/logs/*_production.log
        ;;
    *)
        echo "用法: $0 {backend|frontend|vllm|embedding|chromadb|all}"
        echo ""
        echo "可用选项:"
        echo "  backend   - 查看后端API日志"
        echo "  frontend  - 查看前端服务日志"
        echo "  vllm      - 查看VLLM服务日志"
        echo "  embedding - 查看嵌入服务日志"
        echo "  chromadb  - 查看ChromaDB日志"
        echo "  all       - 查看所有日志"
        ;;
esac
LOGS

chmod +x /home/qwkj/drass/scripts/view_logs_production.sh

echo "✅ 生产环境配置完成！"
echo ""
echo "📋 配置摘要："
echo "  ✅ 后端服务配置优化"
echo "  ✅ 监控系统配置"
echo "  ✅ 备份策略配置"
echo "  ✅ 性能优化脚本"
echo "  ✅ 启动脚本"
echo "  ✅ 停止脚本"
echo "  ✅ 健康检查脚本"
echo "  ✅ 日志查看脚本"
echo ""
echo "🚀 启动生产环境: ./scripts/start_production.sh"
echo "🛑 停止生产环境: ./scripts/stop_production.sh"
echo "🏥 健康检查: ./scripts/health_check_production.sh"
echo "📋 查看日志: ./scripts/view_logs_production.sh [service]"
echo "⚡ 性能优化: ./scripts/optimize_production.sh"
