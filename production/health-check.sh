#!/bin/bash

# 生产环境健康检查脚本
echo "=== 磐石数据合规分析系统健康检查 ==="
echo "检查时间: $(date)"
echo ""

# 检查VLLM服务
echo -n "VLLM服务 (端口8001): "
if curl -f http://localhost:8001/v1/models &> /dev/null; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

# 检查嵌入服务
echo -n "嵌入服务 (端口8010): "
if curl -f http://localhost:8010/v1/models &> /dev/null; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

# 检查重排序服务
echo -n "重排序服务 (端口8012): "
if curl -f http://localhost:8012/v1/models &> /dev/null; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

# 检查后端API
echo -n "后端API (端口8888): "
if curl -f http://localhost:8888/health &> /dev/null; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

# 检查前端服务
echo -n "前端服务 (端口5173): "
if curl -f http://localhost:5173 &> /dev/null; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

# 检查磁盘空间
echo ""
echo "=== 系统资源检查 ==="
echo "磁盘使用情况:"
df -h /home/qwkj/drass

echo ""
echo "内存使用情况:"
free -h

echo ""
echo "CPU使用情况:"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print "CPU使用率: " 100 - $1 "%"}'
