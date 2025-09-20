#!/bin/bash
# 停止任务监控系统脚本

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

echo -e "${BLUE}🛑 停止数据合规管理系统任务监控${NC}"
echo "=" * 50

# 停止任务状态服务器
if [ -f logs/task_server.pid ]; then
    SERVER_PID=$(cat logs/task_server.pid)
    echo -e "${YELLOW}🌐 停止任务状态服务器 (PID: $SERVER_PID)...${NC}"
    
    if kill $SERVER_PID 2>/dev/null; then
        echo -e "${GREEN}✅ 任务状态服务器已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  服务器进程可能已经停止${NC}"
    fi
    
    rm -f logs/task_server.pid
else
    echo -e "${YELLOW}⚠️  未找到任务状态服务器PID文件${NC}"
fi

# 停止文件监控
if [ -f logs/task_monitor.pid ]; then
    MONITOR_PID=$(cat logs/task_monitor.pid)
    echo -e "${YELLOW}👁️  停止文件监控 (PID: $MONITOR_PID)...${NC}"
    
    if kill $MONITOR_PID 2>/dev/null; then
        echo -e "${GREEN}✅ 文件监控已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  监控进程可能已经停止${NC}"
    fi
    
    rm -f logs/task_monitor.pid
else
    echo -e "${YELLOW}⚠️  未找到文件监控PID文件${NC}"
fi

# 清理可能残留的进程
echo -e "${YELLOW}🧹 清理残留进程...${NC}"

# 查找并停止相关的Python进程
pids=$(pgrep -f "task_status_server.py" 2>/dev/null || true)
if [ ! -z "$pids" ]; then
    echo -e "${YELLOW}发现残留的服务器进程: $pids${NC}"
    kill $pids 2>/dev/null || true
fi

pids=$(pgrep -f "task_status_monitor.py" 2>/dev/null || true)
if [ ! -z "$pids" ]; then
    echo -e "${YELLOW}发现残留的监控进程: $pids${NC}"
    kill $pids 2>/dev/null || true
fi

# 等待进程完全停止
sleep 2

echo ""
echo -e "${GREEN}✅ 任务监控系统已完全停止${NC}"
echo ""
echo -e "${BLUE}📊 状态信息:${NC}"

# 检查状态文件
if [ -f .cursor/task_status.json ]; then
    echo -e "${GREEN}📁 任务状态文件保留: .cursor/task_status.json${NC}"
else
    echo -e "${YELLOW}📁 任务状态文件不存在${NC}"
fi

# 检查日志文件
if [ -f logs/task_monitor.log ]; then
    log_lines=$(wc -l < logs/task_monitor.log)
    echo -e "${GREEN}📝 监控日志保留: logs/task_monitor.log ($log_lines 行)${NC}"
else
    echo -e "${YELLOW}📝 监控日志文件不存在${NC}"
fi

echo ""
echo -e "${BLUE}🔧 重新启动命令:${NC}"
echo "   ./scripts/start_task_monitoring.sh"
echo ""

