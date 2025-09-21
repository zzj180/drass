#!/bin/bash

# 磐石数据合规分析系统生产环境部署脚本
# 基于当前运行的服务进行生产环境配置

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

# 检查当前服务状态
check_current_services() {
    log_info "检查当前服务状态..."
    
    # 检查VLLM服务
    if curl -f -H "Authorization: Bearer 123456" http://localhost:8001/v1/models &> /dev/null; then
        log_success "VLLM服务正常运行 (端口8001)"
    else
        log_error "VLLM服务未运行"
        exit 1
    fi
    
    # 检查嵌入服务
    if curl -f -H "Authorization: Bearer 123456" http://localhost:8010/v1/models &> /dev/null; then
        log_success "嵌入服务正常运行 (端口8010)"
    else
        log_error "嵌入服务未运行"
        exit 1
    fi
    
    # 检查重排序服务
    if curl -f -H "Authorization: Bearer 123456" http://localhost:8012/v1/models &> /dev/null; then
        log_success "重排序服务正常运行 (端口8012)"
    else
        log_error "重排序服务未运行"
        exit 1
    fi
    
    # 检查后端API
    if curl -f http://localhost:8888/health &> /dev/null; then
        log_success "后端API服务正常运行 (端口8888)"
    else
        log_error "后端API服务未运行"
        exit 1
    fi
    
    # 检查前端服务
    if curl -f http://localhost:5173 &> /dev/null; then
        log_success "前端服务正常运行 (端口5173)"
    else
        log_error "前端服务未运行"
        exit 1
    fi
}

# 创建生产环境目录结构
create_production_directories() {
    log_info "创建生产环境目录结构..."
    
    mkdir -p /home/qwkj/drass/production/{data,logs,configs,backups,monitoring}
    mkdir -p /home/qwkj/drass/production/data/{uploads,chromadb,redis,prometheus,grafana,loki}
    mkdir -p /home/qwkj/drass/production/logs/{nginx,app,audit}
    mkdir -p /home/qwkj/drass/production/configs/{nginx,monitoring}
    mkdir -p /home/qwkj/drass/production/backups/{daily,weekly,monthly}
    mkdir -p /home/qwkj/drass/production/monitoring/{prometheus,grafana,loki}
    
    log_success "生产环境目录结构创建完成"
}

# 创建生产环境配置文件
create_production_configs() {
    log_info "创建生产环境配置文件..."
    
    # 创建生产环境变量文件
    cat > /home/qwkj/drass/production/.env.production << EOF
# 生产环境配置
NODE_ENV=production
DEPLOYMENT_ENV=production
LOG_LEVEL=INFO

# 服务配置
VLLM_BASE_URL=http://localhost:8001/v1
EMBEDDING_BASE_URL=http://localhost:8010/v1
RERANKER_BASE_URL=http://localhost:8012/v1
API_BASE_URL=http://localhost:8888
FRONTEND_URL=http://localhost:5173

# 数据库配置
DATABASE_URL=sqlite:///./production/data/database.db
CHROMA_PERSIST_DIRECTORY=/home/qwkj/drass/production/data/chromadb

# 安全配置
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# 监控配置
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
GRAFANA_PASSWORD=drass_production_2025

# 备份配置
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE="0 2 * * *"  # 每天凌晨2点备份

# 性能配置
MAX_WORKERS=4
WORKER_TIMEOUT=300
REQUEST_TIMEOUT=60
EOF
    
    log_success "生产环境配置文件创建完成"
}

# 创建Nginx生产配置
create_nginx_production_config() {
    log_info "创建Nginx生产配置..."
    
    cat > /home/qwkj/drass/production/configs/nginx/nginx.production.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # 基本设置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # 上游服务器
    upstream main_app {
        server localhost:8888;
        keepalive 32;
    }

    upstream frontend_app {
        server localhost:5173;
        keepalive 32;
    }

    # 主服务器配置
    server {
        listen 80;
        server_name localhost;

        # 健康检查端点
        location /health {
            proxy_pass http://main_app/health;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API端点
        location /api/ {
            proxy_pass http://main_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket支持
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 前端应用
        location / {
            proxy_pass http://frontend_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket支持
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # 监控端点
        location /monitoring/ {
            proxy_pass http://localhost:3000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 错误页面
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
EOF
    
    log_success "Nginx生产配置创建完成"
}

# 创建监控配置
create_monitoring_configs() {
    log_info "创建监控配置..."
    
    # 创建Prometheus配置
    cat > /home/qwkj/drass/production/configs/monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

scrape_configs:
  # Prometheus自身监控
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # 主应用监控
  - job_name: 'main-app'
    static_configs:
      - targets: ['localhost:8888']
    metrics_path: '/metrics'
    scrape_interval: 30s

  # VLLM服务监控
  - job_name: 'vllm-service'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/metrics'
    scrape_interval: 30s

  # 嵌入服务监控
  - job_name: 'embedding-service'
    static_configs:
      - targets: ['localhost:8010']
    metrics_path: '/metrics'
    scrape_interval: 30s

  # 重排序服务监控
  - job_name: 'reranker-service'
    static_configs:
      - targets: ['localhost:8012']
    metrics_path: '/metrics'
    scrape_interval: 30s

  # 系统监控
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
    scrape_interval: 30s
EOF
    
    # 创建Grafana数据源配置
    mkdir -p /home/qwkj/drass/production/configs/monitoring/grafana/datasources
    cat > /home/qwkj/drass/production/configs/monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: true
EOF
    
    log_success "监控配置创建完成"
}

# 创建备份脚本
create_backup_script() {
    log_info "创建备份脚本..."
    
    cat > /home/qwkj/drass/production/backup-production.sh << 'EOF'
#!/bin/bash

# 生产环境备份脚本
BACKUP_DIR="/home/qwkj/drass/production/backups/daily"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$DATE"

# 创建备份目录
mkdir -p "$BACKUP_PATH"

# 备份数据库
if [ -f "/home/qwkj/drass/data/database.db" ]; then
    cp /home/qwkj/drass/data/database.db "$BACKUP_PATH/"
fi

# 备份文档数据
if [ -d "/home/qwkj/drass/data/uploads" ]; then
    tar -czf "$BACKUP_PATH/uploads.tar.gz" -C /home/qwkj/drass/data uploads
fi

# 备份向量数据库
if [ -d "/home/qwkj/drass/data/chromadb" ]; then
    tar -czf "$BACKUP_PATH/chromadb.tar.gz" -C /home/qwkj/drass/data chromadb
fi

# 备份配置文件
cp -r /home/qwkj/drass/production/configs "$BACKUP_PATH/"

# 创建备份清单
cat > "$BACKUP_PATH/manifest.txt" << EOL
磐石数据合规分析系统生产环境备份
备份时间: $(date)
备份版本: 1.0.0

包含内容:
- 数据库文件 (database.db)
- 文档数据 (uploads.tar.gz)
- 向量数据库 (chromadb.tar.gz)
- 配置文件 (configs/)

备份大小: $(du -sh "$BACKUP_PATH" | cut -f1)
EOL

echo "备份完成: $BACKUP_PATH"
EOF
    
    chmod +x /home/qwkj/drass/production/backup-production.sh
    log_success "备份脚本创建完成"
}

# 创建系统服务脚本
create_systemd_services() {
    log_info "创建系统服务脚本..."
    
    # 创建主应用服务
    cat > /home/qwkj/drass/production/drass-main-app.service << EOF
[Unit]
Description=DRASS Main Application
After=network.target

[Service]
Type=simple
User=qwkj
WorkingDirectory=/home/qwkj/drass
Environment=PATH=/home/qwkj/drass/venv/bin
ExecStart=/home/qwkj/drass/venv/bin/uvicorn services.main-app.app.main:app --host 0.0.0.0 --port 8888 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 创建前端服务
    cat > /home/qwkj/drass/production/drass-frontend.service << EOF
[Unit]
Description=DRASS Frontend Application
After=network.target

[Service]
Type=simple
User=qwkj
WorkingDirectory=/home/qwkj/drass/frontend
Environment=PATH=/usr/bin:/bin
ExecStart=/usr/bin/npm run dev -- --host 0.0.0.0 --port 5173
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    log_success "系统服务脚本创建完成"
}

# 创建健康检查脚本
create_health_check_script() {
    log_info "创建健康检查脚本..."
    
    cat > /home/qwkj/drass/production/health-check.sh << 'EOF'
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
EOF
    
    chmod +x /home/qwkj/drass/production/health-check.sh
    log_success "健康检查脚本创建完成"
}

# 显示部署信息
show_deployment_info() {
    log_success "生产环境部署完成！"
    echo ""
    echo "=== 服务访问地址 ==="
    echo "  主应用: http://localhost:8888"
    echo "  前端界面: http://localhost:5173"
    echo "  API文档: http://localhost:8888/docs"
    echo "  健康检查: http://localhost:8888/health"
    echo ""
    echo "=== 生产环境目录 ==="
    echo "  配置目录: /home/qwkj/drass/production/configs"
    echo "  数据目录: /home/qwkj/drass/production/data"
    echo "  日志目录: /home/qwkj/drass/production/logs"
    echo "  备份目录: /home/qwkj/drass/production/backups"
    echo ""
    echo "=== 管理命令 ==="
    echo "  健康检查: /home/qwkj/drass/production/health-check.sh"
    echo "  执行备份: /home/qwkj/drass/production/backup-production.sh"
    echo "  查看日志: tail -f /home/qwkj/drass/production/logs/app/*.log"
    echo ""
    echo "=== 监控配置 ==="
    echo "  Prometheus: http://localhost:9090 (如果启动)"
    echo "  Grafana: http://localhost:3000 (如果启动)"
    echo ""
}

# 主函数
main() {
    log_info "开始生产环境部署..."
    
    check_current_services
    create_production_directories
    create_production_configs
    create_nginx_production_config
    create_monitoring_configs
    create_backup_script
    create_systemd_services
    create_health_check_script
    show_deployment_info
    
    log_success "生产环境部署完成！"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
