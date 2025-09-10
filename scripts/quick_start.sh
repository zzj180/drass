#!/bin/bash

# Figma助手快速启动脚本

echo "🎨 Figma UI开发助手 - 快速启动"
echo "=================================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [[ $? -ne 0 ]]; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.7+"
    exit 1
fi

echo "✅ Python版本: $python_version"

# 检查虚拟环境
if [[ ! -d "venv" && ! -d ".venv" ]]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
if [[ -d "venv" ]]; then
    source venv/bin/activate
elif [[ -d ".venv" ]]; then
    source .venv/bin/activate
fi

echo "✅ 虚拟环境已激活"

# 安装依赖
echo "📥 安装依赖包..."
pip install -r requirements.txt

if [[ $? -ne 0 ]]; then
    echo "❌ 依赖安装失败，请检查网络连接和requirements.txt文件"
    exit 1
fi

echo "✅ 依赖安装完成"

# 检查环境变量
echo "🔍 检查环境配置..."

if [[ -z "$FIGMA_ACCESS_TOKEN" ]]; then
    echo "⚠️  警告: FIGMA_ACCESS_TOKEN 未设置"
    echo "   请在 .env 文件中设置或导出环境变量"
fi

if [[ -z "$GITHUB_TOKEN" ]]; then
    echo "⚠️  警告: GITHUB_TOKEN 未设置"
    echo "   请在 .env 文件中设置或导出环境变量"
fi

if [[ -z "$GITHUB_OWNER" ]]; then
    echo "⚠️  警告: GITHUB_OWNER 未设置"
    echo "   请在 .env 文件中设置或导出环境变量"
fi

if [[ -z "$GITHUB_REPOSITORY" ]]; then
    echo "⚠️  警告: GITHUB_REPOSITORY 未设置"
    echo "   请在 .env 文件中设置或导出环境变量"
fi

# 创建.env文件模板
if [[ ! -f ".env" ]]; then
    echo "📝 创建环境变量配置文件..."
    cp config/figma-assistant.env.example .env
    echo "✅ 已创建 .env 文件，请编辑并填入实际的API密钥"
fi

echo ""
echo "🚀 启动完成！"
echo ""
echo "使用方法:"
echo "1. 编辑 .env 文件，填入API密钥"
echo "2. 交互式模式: python scripts/figma_cli.py --interactive"
echo "3. 命令行模式: python scripts/figma_cli.py --file-key YOUR_FILE_KEY"
echo "4. Webhook服务: python scripts/figma_webhook.py"
echo ""
echo "更多帮助请查看: docs/FIGMA_ASSISTANT.md"
echo ""
echo "🎉 开始使用Figma助手吧！"






