#!/bin/bash

# 优化的Docker构建脚本
# 使用国内镜像源和构建缓存加速构建

set -e

echo "🚀 开始优化构建..."

# 启用Docker BuildKit
export DOCKER_BUILDKIT=1

# 设置构建参数
BUILD_ARGS="--build-arg BUILDKIT_INLINE_CACHE=1"

# 构建doc-processor（优化版）
echo "📦 构建doc-processor服务..."
docker-compose build $BUILD_ARGS doc-processor

# 构建reranking-service（如果还没构建）
echo "📦 构建reranking-service服务..."
docker-compose build $BUILD_ARGS reranking-service

# 构建其他服务
echo "📦 构建其他服务..."
docker-compose build $BUILD_ARGS

echo "✅ 所有服务构建完成！"

# 显示镜像大小
echo "📊 镜像大小统计："
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep -E "(doc-processor|reranking-service|main-app|embedding-service)"
