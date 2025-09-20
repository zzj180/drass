#!/bin/bash
# 启动任务监控系统脚本

set -e

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 启动数据合规管理系统任务监控${NC}"
echo "=" * 50

# 检查Python环境
echo -e "${YELLOW}📋 检查环境依赖...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi

# 检查并安装Python依赖
echo -e "${YELLOW}📦 检查Python依赖...${NC}"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔧 创建虚拟环境...${NC}"
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -q watchdog fastapi uvicorn websockets

# 创建必要目录
mkdir -p logs
mkdir -p .cursor

echo -e "${GREEN}✅ 环境检查完成${NC}"

# 启动任务状态服务器
echo -e "${YELLOW}🌐 启动任务状态服务器...${NC}"
python3 scripts/task_status_server.py &
SERVER_PID=$!

# 等待服务器启动
sleep 3

# 检查服务器是否启动成功
if curl -s http://localhost:8899/ > /dev/null; then
    echo -e "${GREEN}✅ 任务状态服务器启动成功 (PID: $SERVER_PID)${NC}"
else
    echo -e "${RED}❌ 任务状态服务器启动失败${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# 启动文件监控
echo -e "${YELLOW}👁️  启动文件监控...${NC}"
python3 scripts/task_status_monitor.py &
MONITOR_PID=$!

echo -e "${GREEN}✅ 文件监控启动成功 (PID: $MONITOR_PID)${NC}"

# 保存PID到文件
echo $SERVER_PID > logs/task_server.pid
echo $MONITOR_PID > logs/task_monitor.pid

echo ""
echo -e "${BLUE}📊 任务监控系统启动完成${NC}"
echo "=" * 50
echo -e "${GREEN}🌐 服务地址:${NC}"
echo "   HTTP API: http://localhost:8899"
echo "   WebSocket: ws://localhost:8899/ws/task-status"
echo ""
echo -e "${GREEN}📁 相关文件:${NC}"
echo "   状态文件: .cursor/task_status.json"
echo "   监控日志: logs/task_monitor.log"
echo "   服务器PID: logs/task_server.pid"
echo "   监控器PID: logs/task_monitor.pid"
echo ""
echo -e "${YELLOW}🔧 管理命令:${NC}"
echo "   查看状态: curl http://localhost:8899/api/task-status"
echo "   查看进度: curl http://localhost:8899/api/progress-summary"
echo "   停止服务: ./scripts/stop_task_monitoring.sh"
echo ""
echo -e "${BLUE}💡 提示: 修改以下目录中的文件会自动更新任务状态:${NC}"
echo "   - services/main-app/app/services/"
echo "   - services/main-app/app/api/"
echo "   - services/main-app/app/models/"
echo "   - frontend/src/components/"
echo ""

# 等待用户中断
echo -e "${YELLOW}按 Ctrl+C 停止监控系统...${NC}"

# 信号处理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 正在停止任务监控系统...${NC}"
    
    # 停止服务器和监控器
    if [ -f logs/task_server.pid ]; then
        SERVER_PID=$(cat logs/task_server.pid)
        kill $SERVER_PID 2>/dev/null || true
        rm -f logs/task_server.pid
        echo -e "${GREEN}✅ 任务状态服务器已停止${NC}"
    fi
    
    if [ -f logs/task_monitor.pid ]; then
        MONITOR_PID=$(cat logs/task_monitor.pid)
        kill $MONITOR_PID 2>/dev/null || true
        rm -f logs/task_monitor.pid
        echo -e "${GREEN}✅ 文件监控已停止${NC}"
    fi
    
    echo -e "${BLUE}👋 任务监控系统已完全停止${NC}"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 保持脚本运行
while true; do
    sleep 1
    
    # 检查服务是否还在运行
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo -e "${RED}❌ 任务状态服务器意外停止${NC}"
        cleanup
    fi
    
    if ! kill -0 $MONITOR_PID 2>/dev/null; then
        echo -e "${RED}❌ 文件监控意外停止${NC}"
        cleanup
    fi
done

