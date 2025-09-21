#!/bin/bash

# 磐石数据合规分析系统备份恢复策略脚本
# 提供完整的备份、恢复、验证和清理功能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BACKUP_BASE_DIR="/home/qwkj/drass/production/backups"
DAILY_BACKUP_DIR="$BACKUP_BASE_DIR/daily"
WEEKLY_BACKUP_DIR="$BACKUP_BASE_DIR/weekly"
MONTHLY_BACKUP_DIR="$BACKUP_BASE_DIR/monthly"
RETENTION_DAYS=30
RETENTION_WEEKS=12
RETENTION_MONTHS=12

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

# 创建备份目录结构
create_backup_directories() {
    log_info "创建备份目录结构..."
    
    mkdir -p "$DAILY_BACKUP_DIR"
    mkdir -p "$WEEKLY_BACKUP_DIR"
    mkdir -p "$MONTHLY_BACKUP_DIR"
    
    log_success "备份目录结构创建完成"
}

# 执行完整备份
perform_full_backup() {
    local backup_type="$1"
    local backup_dir="$2"
    local date=$(date +%Y%m%d_%H%M%S)
    local backup_path="$backup_dir/$date"
    
    log_info "开始执行$backup_type备份到: $backup_path"
    
    # 创建备份目录
    mkdir -p "$backup_path"
    
    # 备份数据库
    log_info "备份数据库..."
    if [ -f "/home/qwkj/drass/data/database.db" ]; then
        cp /home/qwkj/drass/data/database.db "$backup_path/"
        log_success "数据库备份完成"
    else
        log_warning "数据库文件不存在，跳过备份"
    fi
    
    # 备份文档数据
    log_info "备份文档数据..."
    if [ -d "/home/qwkj/drass/data/uploads" ]; then
        tar -czf "$backup_path/uploads.tar.gz" -C /home/qwkj/drass/data uploads
        log_success "文档数据备份完成"
    else
        log_warning "文档目录不存在，跳过备份"
    fi
    
    # 备份向量数据库
    log_info "备份向量数据库..."
    if [ -d "/home/qwkj/drass/data/chromadb" ]; then
        tar -czf "$backup_path/chromadb.tar.gz" -C /home/qwkj/drass/data chromadb
        log_success "向量数据库备份完成"
    else
        log_warning "向量数据库目录不存在，跳过备份"
    fi
    
    # 备份配置文件
    log_info "备份配置文件..."
    if [ -d "/home/qwkj/drass/production/configs" ]; then
        tar -czf "$backup_path/configs.tar.gz" -C /home/qwkj/drass/production configs
        log_success "配置文件备份完成"
    else
        log_warning "配置文件目录不存在，跳过备份"
    fi
    
    # 备份环境变量
    log_info "备份环境变量..."
    if [ -f "/home/qwkj/drass/production/.env.production" ]; then
        cp /home/qwkj/drass/production/.env.production "$backup_path/"
        log_success "环境变量备份完成"
    else
        log_warning "环境变量文件不存在，跳过备份"
    fi
    
    # 创建备份清单
    create_backup_manifest "$backup_path" "$backup_type"
    
    # 验证备份
    verify_backup "$backup_path"
    
    log_success "$backup_type备份完成: $backup_path"
    echo "$backup_path"
}

# 创建备份清单
create_backup_manifest() {
    local backup_path="$1"
    local backup_type="$2"
    
    log_info "创建备份清单..."
    
    cat > "$backup_path/manifest.txt" << EOF
磐石数据合规分析系统备份清单
备份类型: $backup_type
备份时间: $(date)
备份版本: 1.0.0
系统版本: $(uname -a)

包含内容:
- 数据库文件 (database.db)
- 文档数据 (uploads.tar.gz)
- 向量数据库 (chromadb.tar.gz)
- 配置文件 (configs.tar.gz)
- 环境变量 (.env.production)

恢复说明:
1. 停止所有服务
2. 恢复数据库文件到 /home/qwkj/drass/data/database.db
3. 解压文档数据到 /home/qwkj/drass/data/uploads
4. 解压向量数据库到 /home/qwkj/drass/data/chromadb
5. 解压配置文件到 /home/qwkj/drass/production/configs
6. 恢复环境变量文件
7. 重启服务

备份大小: $(du -sh "$backup_path" | cut -f1)
文件数量: $(find "$backup_path" -type f | wc -l)
EOF
    
    log_success "备份清单创建完成"
}

# 验证备份
verify_backup() {
    local backup_path="$1"
    
    log_info "验证备份完整性..."
    
    # 检查必要文件是否存在
    local required_files=("manifest.txt")
    local optional_files=("database.db" "uploads.tar.gz" "chromadb.tar.gz" "configs.tar.gz" ".env.production")
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$backup_path/$file" ]; then
            log_error "必需文件缺失: $file"
            return 1
        fi
    done
    
    # 检查可选文件
    local found_files=0
    for file in "${optional_files[@]}"; do
        if [ -f "$backup_path/$file" ]; then
            found_files=$((found_files + 1))
        fi
    done
    
    if [ $found_files -eq 0 ]; then
        log_error "没有找到任何数据文件"
        return 1
    fi
    
    log_success "备份验证通过 (找到 $found_files 个数据文件)"
}

# 恢复备份
restore_backup() {
    local backup_path="$1"
    local dry_run="${2:-false}"
    
    if [ ! -d "$backup_path" ]; then
        log_error "备份目录不存在: $backup_path"
        return 1
    fi
    
    log_info "开始恢复备份: $backup_path"
    
    if [ "$dry_run" = "true" ]; then
        log_info "这是模拟运行，不会实际恢复数据"
    fi
    
    # 验证备份
    if ! verify_backup "$backup_path"; then
        log_error "备份验证失败，无法恢复"
        return 1
    fi
    
    # 停止服务
    if [ "$dry_run" = "false" ]; then
        log_info "停止服务..."
        # 这里应该停止实际的服务
        # systemctl stop drass-main-app || true
        # systemctl stop drass-frontend || true
    fi
    
    # 恢复数据库
    if [ -f "$backup_path/database.db" ]; then
        log_info "恢复数据库..."
        if [ "$dry_run" = "false" ]; then
            cp "$backup_path/database.db" /home/qwkj/drass/data/
        fi
        log_success "数据库恢复完成"
    fi
    
    # 恢复文档数据
    if [ -f "$backup_path/uploads.tar.gz" ]; then
        log_info "恢复文档数据..."
        if [ "$dry_run" = "false" ]; then
            tar -xzf "$backup_path/uploads.tar.gz" -C /home/qwkj/drass/data
        fi
        log_success "文档数据恢复完成"
    fi
    
    # 恢复向量数据库
    if [ -f "$backup_path/chromadb.tar.gz" ]; then
        log_info "恢复向量数据库..."
        if [ "$dry_run" = "false" ]; then
            tar -xzf "$backup_path/chromadb.tar.gz" -C /home/qwkj/drass/data
        fi
        log_success "向量数据库恢复完成"
    fi
    
    # 恢复配置文件
    if [ -f "$backup_path/configs.tar.gz" ]; then
        log_info "恢复配置文件..."
        if [ "$dry_run" = "false" ]; then
            tar -xzf "$backup_path/configs.tar.gz" -C /home/qwkj/drass/production
        fi
        log_success "配置文件恢复完成"
    fi
    
    # 恢复环境变量
    if [ -f "$backup_path/.env.production" ]; then
        log_info "恢复环境变量..."
        if [ "$dry_run" = "false" ]; then
            cp "$backup_path/.env.production" /home/qwkj/drass/production/
        fi
        log_success "环境变量恢复完成"
    fi
    
    # 启动服务
    if [ "$dry_run" = "false" ]; then
        log_info "启动服务..."
        # 这里应该启动实际的服务
        # systemctl start drass-main-app
        # systemctl start drass-frontend
    fi
    
    log_success "备份恢复完成"
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理旧备份..."
    
    # 清理日备份
    log_info "清理超过 $RETENTION_DAYS 天的日备份..."
    find "$DAILY_BACKUP_DIR" -type d -name "20*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
    
    # 清理周备份
    log_info "清理超过 $RETENTION_WEEKS 周的周备份..."
    find "$WEEKLY_BACKUP_DIR" -type d -name "20*" -mtime +$((RETENTION_WEEKS * 7)) -exec rm -rf {} \; 2>/dev/null || true
    
    # 清理月备份
    log_info "清理超过 $RETENTION_MONTHS 个月的月备份..."
    find "$MONTHLY_BACKUP_DIR" -type d -name "20*" -mtime +$((RETENTION_MONTHS * 30)) -exec rm -rf {} \; 2>/dev/null || true
    
    log_success "旧备份清理完成"
}

# 列出可用备份
list_backups() {
    local backup_type="${1:-all}"
    
    log_info "可用备份列表:"
    echo ""
    
    if [ "$backup_type" = "all" ] || [ "$backup_type" = "daily" ]; then
        echo "=== 日备份 ==="
        if [ -d "$DAILY_BACKUP_DIR" ]; then
            ls -la "$DAILY_BACKUP_DIR" | grep "^d" | awk '{print $9, $6, $7, $8}' | grep "^20" | while read line; do
                echo "  $line"
            done
        else
            echo "  无日备份"
        fi
        echo ""
    fi
    
    if [ "$backup_type" = "all" ] || [ "$backup_type" = "weekly" ]; then
        echo "=== 周备份 ==="
        if [ -d "$WEEKLY_BACKUP_DIR" ]; then
            ls -la "$WEEKLY_BACKUP_DIR" | grep "^d" | awk '{print $9, $6, $7, $8}' | grep "^20" | while read line; do
                echo "  $line"
            done
        else
            echo "  无周备份"
        fi
        echo ""
    fi
    
    if [ "$backup_type" = "all" ] || [ "$backup_type" = "monthly" ]; then
        echo "=== 月备份 ==="
        if [ -d "$MONTHLY_BACKUP_DIR" ]; then
            ls -la "$MONTHLY_BACKUP_DIR" | grep "^d" | awk '{print $9, $6, $7, $8}' | grep "^20" | while read line; do
                echo "  $line"
            done
        else
            echo "  无月备份"
        fi
        echo ""
    fi
}

# 创建定时备份任务
setup_cron_jobs() {
    log_info "设置定时备份任务..."
    
    # 创建crontab条目
    local cron_entries="
# 磐石数据合规分析系统备份任务
# 每天凌晨2点执行日备份
0 2 * * * /home/qwkj/drass/production/backup-recovery-strategy.sh daily >> /home/qwkj/drass/production/logs/backup.log 2>&1

# 每周日凌晨3点执行周备份
0 3 * * 0 /home/qwkj/drass/production/backup-recovery-strategy.sh weekly >> /home/qwkj/drass/production/logs/backup.log 2>&1

# 每月1日凌晨4点执行月备份
0 4 1 * * /home/qwkj/drass/production/backup-recovery-strategy.sh monthly >> /home/qwkj/drass/production/logs/backup.log 2>&1

# 每天凌晨5点清理旧备份
0 5 * * * /home/qwkj/drass/production/backup-recovery-strategy.sh cleanup >> /home/qwkj/drass/production/logs/backup.log 2>&1
"
    
    # 保存到文件
    echo "$cron_entries" > /home/qwkj/drass/production/backup-cron.txt
    
    log_success "定时备份任务配置已保存到: /home/qwkj/drass/production/backup-cron.txt"
    log_warning "请手动执行以下命令安装定时任务:"
    log_warning "crontab /home/qwkj/drass/production/backup-cron.txt"
}

# 显示帮助信息
show_help() {
    echo "磐石数据合规分析系统备份恢复工具"
    echo ""
    echo "用法: $0 [选项] [参数]"
    echo ""
    echo "选项:"
    echo "  daily                   执行日备份"
    echo "  weekly                  执行周备份"
    echo "  monthly                 执行月备份"
    echo "  restore <backup_path>   恢复指定备份"
    echo "  restore-dry <backup_path> 模拟恢复指定备份"
    echo "  list [type]             列出可用备份 (type: daily/weekly/monthly/all)"
    echo "  cleanup                 清理旧备份"
    echo "  setup-cron              设置定时备份任务"
    echo "  verify <backup_path>    验证备份完整性"
    echo "  help                    显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 daily"
    echo "  $0 restore /home/qwkj/drass/production/backups/daily/20250921_190231"
    echo "  $0 list daily"
    echo "  $0 cleanup"
}

# 主函数
main() {
    case "${1:-help}" in
        "daily")
            create_backup_directories
            perform_full_backup "日备份" "$DAILY_BACKUP_DIR"
            ;;
        "weekly")
            create_backup_directories
            perform_full_backup "周备份" "$WEEKLY_BACKUP_DIR"
            ;;
        "monthly")
            create_backup_directories
            perform_full_backup "月备份" "$MONTHLY_BACKUP_DIR"
            ;;
        "restore")
            if [ -z "$2" ]; then
                log_error "请指定备份路径"
                show_help
                exit 1
            fi
            restore_backup "$2" "false"
            ;;
        "restore-dry")
            if [ -z "$2" ]; then
                log_error "请指定备份路径"
                show_help
                exit 1
            fi
            restore_backup "$2" "true"
            ;;
        "list")
            list_backups "$2"
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        "setup-cron")
            setup_cron_jobs
            ;;
        "verify")
            if [ -z "$2" ]; then
                log_error "请指定备份路径"
                show_help
                exit 1
            fi
            verify_backup "$2"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
