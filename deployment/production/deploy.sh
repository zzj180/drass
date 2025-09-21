#!/bin/bash

# 磐石数据合规分析系统生产环境部署脚本
# 作者: DRASS团队
# 版本: 1.0.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查部署依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查curl
    if ! command -v curl &> /dev/null; then
        log_error "curl未安装，请先安装curl"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p data/uploads
    mkdir -p data/chromadb
    mkdir -p data/redis
    mkdir -p data/prometheus
    mkdir -p data/grafana
    mkdir -p data/loki
    mkdir -p logs/nginx
    mkdir -p nginx/ssl
    mkdir -p models
    
    log_success "目录创建完成"
}

# 生成SSL证书
generate_ssl_certificates() {
    log_info "生成SSL证书..."
    
    if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=DRASS/OU=IT/CN=localhost"
        log_success "SSL证书生成完成"
    else
        log_info "SSL证书已存在，跳过生成"
    fi
}

# 创建环境变量文件
create_env_file() {
    log_info "创建环境变量文件..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# 数据库配置
DATABASE_URL=sqlite:///./data/database.db

# Redis配置
REDIS_URL=redis://:drass_redis_password@redis:6379/0
REDIS_PASSWORD=drass_redis_password

# 安全配置
SECRET_KEY=$(openssl rand -hex 32)

# Grafana配置
GRAFANA_PASSWORD=drass_grafana_password

# 模型路径
MODEL_PATH=/models
EOF
        log_success "环境变量文件创建完成"
    else
        log_info "环境变量文件已存在，跳过创建"
    fi
}

# 下载模型文件
download_models() {
    log_info "检查模型文件..."
    
    # 这里应该下载实际的模型文件
    # 为了演示，我们创建一些占位符文件
    if [ ! -d "models/Qwen2.5-8B-Instruct" ]; then
        log_warning "模型文件不存在，请手动下载模型文件到 models/ 目录"
        log_warning "需要的模型:"
        log_warning "  - Qwen2.5-8B-Instruct"
        log_warning "  - Qwen3-Embedding-8B"
        log_warning "  - Qwen3-Reranker-8B"
    else
        log_success "模型文件检查完成"
    fi
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    
    docker-compose -f docker-compose.prod.yml build --no-cache
    log_success "Docker镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 停止现有服务
    docker-compose -f docker-compose.prod.yml down
    
    # 启动服务
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    # 等待主应用
    log_info "等待主应用启动..."
    for i in {1..30}; do
        if curl -f http://localhost:8888/health &> /dev/null; then
            log_success "主应用已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "主应用启动超时"
            exit 1
        fi
        sleep 10
    done
    
    # 等待VLLM服务
    log_info "等待VLLM服务启动..."
    for i in {1..60}; do
        if curl -f http://localhost:8001/v1/models &> /dev/null; then
            log_success "VLLM服务已就绪"
            break
        fi
        if [ $i -eq 60 ]; then
            log_error "VLLM服务启动超时"
            exit 1
        fi
        sleep 10
    done
    
    # 等待嵌入服务
    log_info "等待嵌入服务启动..."
    for i in {1..60}; do
        if curl -f http://localhost:8010/v1/models &> /dev/null; then
            log_success "嵌入服务已就绪"
            break
        fi
        if [ $i -eq 60 ]; then
            log_error "嵌入服务启动超时"
            exit 1
        fi
        sleep 10
    done
    
    # 等待重排序服务
    log_info "等待重排序服务启动..."
    for i in {1..60}; do
        if curl -f http://localhost:8012/v1/models &> /dev/null; then
            log_success "重排序服务已就绪"
            break
        fi
        if [ $i -eq 60 ]; then
            log_error "重排序服务启动超时"
            exit 1
        fi
        sleep 10
    done
}

# 运行健康检查
health_check() {
    log_info "运行健康检查..."
    
    # 检查主应用
    if curl -f http://localhost:8888/health &> /dev/null; then
        log_success "主应用健康检查通过"
    else
        log_error "主应用健康检查失败"
        exit 1
    fi
    
    # 检查VLLM服务
    if curl -f http://localhost:8001/v1/models &> /dev/null; then
        log_success "VLLM服务健康检查通过"
    else
        log_error "VLLM服务健康检查失败"
        exit 1
    fi
    
    # 检查嵌入服务
    if curl -f http://localhost:8010/v1/models &> /dev/null; then
        log_success "嵌入服务健康检查通过"
    else
        log_error "嵌入服务健康检查失败"
        exit 1
    fi
    
    # 检查重排序服务
    if curl -f http://localhost:8012/v1/models &> /dev/null; then
        log_success "重排序服务健康检查通过"
    else
        log_error "重排序服务健康检查失败"
        exit 1
    fi
    
    # 检查Nginx
    if curl -f http://localhost/health &> /dev/null; then
        log_success "Nginx健康检查通过"
    else
        log_error "Nginx健康检查失败"
        exit 1
    fi
}

# 显示部署信息
show_deployment_info() {
    log_success "部署完成！"
    echo ""
    echo "服务访问地址："
    echo "  主应用: https://localhost"
    echo "  API文档: https://localhost/api/docs"
    echo "  Grafana: http://localhost:3000 (admin/drass_grafana_password)"
    echo "  Prometheus: http://localhost:9090"
    echo ""
    echo "管理命令："
    echo "  查看日志: docker-compose -f docker-compose.prod.yml logs -f"
    echo "  停止服务: docker-compose -f docker-compose.prod.yml down"
    echo "  重启服务: docker-compose -f docker-compose.prod.yml restart"
    echo "  查看状态: docker-compose -f docker-compose.prod.yml ps"
    echo ""
}

# 主函数
main() {
    log_info "开始部署磐石数据合规分析系统..."
    
    check_dependencies
    create_directories
    generate_ssl_certificates
    create_env_file
    download_models
    build_images
    start_services
    wait_for_services
    health_check
    show_deployment_info
    
    log_success "部署完成！"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
