#!/bin/bash

# 启动监控服务脚本
# 启动Prometheus、Grafana和AlertManager

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

# 检查Docker是否运行
check_docker() {
    if ! docker info &> /dev/null; then
        log_error "Docker未运行，请先启动Docker"
        exit 1
    fi
    log_success "Docker运行正常"
}

# 创建监控网络
create_monitoring_network() {
    log_info "创建监控网络..."
    
    if ! docker network ls | grep -q "monitoring"; then
        docker network create monitoring
        log_success "监控网络创建完成"
    else
        log_info "监控网络已存在"
    fi
}

# 启动Prometheus
start_prometheus() {
    log_info "启动Prometheus..."
    
    # 停止现有容器
    docker stop prometheus 2>/dev/null || true
    docker rm prometheus 2>/dev/null || true
    
    # 启动Prometheus
    docker run -d \
        --name prometheus \
        --network monitoring \
        -p 9090:9090 \
        -v /home/qwkj/drass/production/configs/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
        -v /home/qwkj/drass/production/data/prometheus:/prometheus \
        prom/prometheus:latest \
        --config.file=/etc/prometheus/prometheus.yml \
        --storage.tsdb.path=/prometheus \
        --web.console.libraries=/etc/prometheus/console_libraries \
        --web.console.templates=/etc/prometheus/consoles \
        --storage.tsdb.retention.time=200h \
        --web.enable-lifecycle
    
    log_success "Prometheus启动完成"
}

# 启动Grafana
start_grafana() {
    log_info "启动Grafana..."
    
    # 停止现有容器
    docker stop grafana 2>/dev/null || true
    docker rm grafana 2>/dev/null || true
    
    # 启动Grafana
    docker run -d \
        --name grafana \
        --network monitoring \
        -p 3000:3000 \
        -e GF_SECURITY_ADMIN_PASSWORD=drass_production_2025 \
        -e GF_USERS_ALLOW_SIGN_UP=false \
        -v /home/qwkj/drass/production/data/grafana:/var/lib/grafana \
        -v /home/qwkj/drass/production/configs/monitoring/grafana/datasources:/etc/grafana/provisioning/datasources \
        grafana/grafana:latest
    
    log_success "Grafana启动完成"
}

# 启动Node Exporter
start_node_exporter() {
    log_info "启动Node Exporter..."
    
    # 停止现有容器
    docker stop node-exporter 2>/dev/null || true
    docker rm node-exporter 2>/dev/null || true
    
    # 启动Node Exporter
    docker run -d \
        --name node-exporter \
        --network monitoring \
        -p 9100:9100 \
        -v /proc:/host/proc:ro \
        -v /sys:/host/sys:ro \
        -v /:/rootfs:ro \
        prom/node-exporter:latest \
        --path.procfs=/host/proc \
        --path.rootfs=/rootfs \
        --path.sysfs=/host/sys \
        --collector.filesystem.mount-points-exclude='^/(sys|proc|dev|host|etc)($$|/)'
    
    log_success "Node Exporter启动完成"
}

# 启动AlertManager
start_alertmanager() {
    log_info "启动AlertManager..."
    
    # 创建AlertManager配置
    mkdir -p /home/qwkj/drass/production/configs/monitoring/alertmanager
    cat > /home/qwkj/drass/production/configs/monitoring/alertmanager/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@drass.example.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://localhost:5001/'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF
    
    # 停止现有容器
    docker stop alertmanager 2>/dev/null || true
    docker rm alertmanager 2>/dev/null || true
    
    # 启动AlertManager
    docker run -d \
        --name alertmanager \
        --network monitoring \
        -p 9093:9093 \
        -v /home/qwkj/drass/production/configs/monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
        prom/alertmanager:latest \
        --config.file=/etc/alertmanager/alertmanager.yml \
        --storage.path=/alertmanager
    
    log_success "AlertManager启动完成"
}

# 创建告警规则
create_alert_rules() {
    log_info "创建告警规则..."
    
    mkdir -p /home/qwkj/drass/production/configs/monitoring/prometheus/rules
    cat > /home/qwkj/drass/production/configs/monitoring/prometheus/rules/drass-alerts.yml << 'EOF'
groups:
- name: drass-alerts
  rules:
  # 服务可用性告警
  - alert: ServiceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "服务 {{ $labels.instance }} 不可用"
      description: "服务 {{ $labels.instance }} 已经不可用超过1分钟"

  # 高CPU使用率告警
  - alert: HighCPUUsage
    expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "CPU使用率过高"
      description: "实例 {{ $labels.instance }} CPU使用率超过80%"

  # 高内存使用率告警
  - alert: HighMemoryUsage
    expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "内存使用率过高"
      description: "实例 {{ $labels.instance }} 内存使用率超过85%"

  # 磁盘空间不足告警
  - alert: DiskSpaceLow
    expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 90
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "磁盘空间不足"
      description: "实例 {{ $labels.instance }} 磁盘使用率超过90%"

  # API响应时间告警
  - alert: HighAPIResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "API响应时间过长"
      description: "API 95%响应时间超过2秒"

  # 错误率告警
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "错误率过高"
      description: "HTTP 5xx错误率超过5%"
EOF
    
    log_success "告警规则创建完成"
}

# 等待服务启动
wait_for_services() {
    log_info "等待监控服务启动..."
    
    # 等待Prometheus
    for i in {1..30}; do
        if curl -f http://localhost:9090/-/healthy &> /dev/null; then
            log_success "Prometheus已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Prometheus启动超时"
            exit 1
        fi
        sleep 2
    done
    
    # 等待Grafana
    for i in {1..30}; do
        if curl -f http://localhost:3000/api/health &> /dev/null; then
            log_success "Grafana已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Grafana启动超时"
            exit 1
        fi
        sleep 2
    done
    
    # 等待AlertManager
    for i in {1..30}; do
        if curl -f http://localhost:9093/-/healthy &> /dev/null; then
            log_success "AlertManager已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "AlertManager启动超时"
            exit 1
        fi
        sleep 2
    done
}

# 显示监控信息
show_monitoring_info() {
    log_success "监控服务启动完成！"
    echo ""
    echo "=== 监控服务访问地址 ==="
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3000 (admin/drass_production_2025)"
    echo "  AlertManager: http://localhost:9093"
    echo "  Node Exporter: http://localhost:9100/metrics"
    echo ""
    echo "=== 管理命令 ==="
    echo "  查看容器状态: docker ps | grep -E '(prometheus|grafana|alertmanager|node-exporter)'"
    echo "  查看Prometheus日志: docker logs prometheus"
    echo "  查看Grafana日志: docker logs grafana"
    echo "  重启Prometheus: docker restart prometheus"
    echo "  重启Grafana: docker restart grafana"
    echo ""
    echo "=== 配置说明 ==="
    echo "  Prometheus配置: /home/qwkj/drass/production/configs/monitoring/prometheus.yml"
    echo "  Grafana数据源: /home/qwkj/drass/production/configs/monitoring/grafana/datasources/"
    echo "  告警规则: /home/qwkj/drass/production/configs/monitoring/prometheus/rules/"
    echo "  AlertManager配置: /home/qwkj/drass/production/configs/monitoring/alertmanager/"
    echo ""
}

# 主函数
main() {
    log_info "启动监控服务..."
    
    check_docker
    create_monitoring_network
    create_alert_rules
    start_prometheus
    start_grafana
    start_node_exporter
    start_alertmanager
    wait_for_services
    show_monitoring_info
    
    log_success "监控服务启动完成！"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
