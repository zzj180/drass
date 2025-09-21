#!/bin/bash

# 磐石数据合规分析系统部署测试脚本
# 执行功能测试、性能测试、安全测试

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试配置
TEST_BASE_URL="http://localhost:8888"
FRONTEND_URL="http://localhost:5173"
TEST_USER_EMAIL="test@example.com"
TEST_USER_PASSWORD="testpassword123"
API_KEY="123456"

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

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

# 测试结果记录
record_test() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$result" = "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        log_success "✓ $test_name"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_error "✗ $test_name: $details"
    fi
}

# 等待服务就绪
wait_for_service() {
    local url="$1"
    local service_name="$2"
    local max_attempts=30
    local attempt=1
    
    log_info "等待 $service_name 服务就绪..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log_success "$service_name 服务已就绪"
            return 0
        fi
        
        log_info "尝试 $attempt/$max_attempts - 等待 $service_name 服务..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "$service_name 服务启动超时"
    return 1
}

# 1. 系统健康检查测试
test_system_health() {
    log_info "=== 系统健康检查测试 ==="
    
    # 测试后端API健康检查
    if curl -f -s "$TEST_BASE_URL/health" > /dev/null 2>&1; then
        record_test "后端API健康检查" "PASS"
    else
        record_test "后端API健康检查" "FAIL" "无法访问健康检查端点"
    fi
    
    # 测试VLLM服务
    if curl -f -s -H "Authorization: Bearer $API_KEY" "http://localhost:8001/v1/models" > /dev/null 2>&1; then
        record_test "VLLM服务健康检查" "PASS"
    else
        record_test "VLLM服务健康检查" "FAIL" "VLLM服务无响应"
    fi
    
    # 测试嵌入服务
    if curl -f -s -H "Authorization: Bearer $API_KEY" "http://localhost:8010/v1/models" > /dev/null 2>&1; then
        record_test "嵌入服务健康检查" "PASS"
    else
        record_test "嵌入服务健康检查" "FAIL" "嵌入服务无响应"
    fi
    
    # 测试重排序服务
    if curl -f -s -H "Authorization: Bearer $API_KEY" "http://localhost:8012/v1/models" > /dev/null 2>&1; then
        record_test "重排序服务健康检查" "PASS"
    else
        record_test "重排序服务健康检查" "FAIL" "重排序服务无响应"
    fi
    
    # 测试前端服务
    if curl -f -s "$FRONTEND_URL" > /dev/null 2>&1; then
        record_test "前端服务健康检查" "PASS"
    else
        record_test "前端服务健康检查" "FAIL" "前端服务无响应"
    fi
}

# 2. 用户认证测试
test_user_authentication() {
    log_info "=== 用户认证测试 ==="
    
    # 测试用户登录
    local login_response=$(curl -s -X POST "$TEST_BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$TEST_USER_EMAIL&password=$TEST_USER_PASSWORD")
    
    if echo "$login_response" | grep -q "access_token"; then
        record_test "用户登录功能" "PASS"
        # 提取token用于后续测试
        export TEST_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    else
        record_test "用户登录功能" "FAIL" "登录响应: $login_response"
    fi
    
    # 测试token验证
    if [ -n "$TEST_TOKEN" ]; then
        local auth_response=$(curl -s -H "Authorization: Bearer $TEST_TOKEN" "$TEST_BASE_URL/api/v1/auth/me")
        if echo "$auth_response" | grep -q "email"; then
            record_test "Token验证功能" "PASS"
        else
            record_test "Token验证功能" "FAIL" "Token验证失败"
        fi
    fi
}

# 3. 文档管理功能测试
test_document_management() {
    log_info "=== 文档管理功能测试 ==="
    
    if [ -z "$TEST_TOKEN" ]; then
        record_test "文档管理功能" "SKIP" "需要有效的认证token"
        return
    fi
    
    # 创建测试文档
    echo "这是一个测试文档内容" > /tmp/test_document.txt
    
    # 测试文档上传
    local upload_response=$(curl -s -X POST "$TEST_BASE_URL/api/v1/documents/upload" \
        -H "Authorization: Bearer $TEST_TOKEN" \
        -F "file=@/tmp/test_document.txt")
    
    if echo "$upload_response" | grep -q "document_id"; then
        record_test "文档上传功能" "PASS"
        # 提取文档ID
        export TEST_DOCUMENT_ID=$(echo "$upload_response" | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)
    else
        record_test "文档上传功能" "FAIL" "上传响应: $upload_response"
    fi
    
    # 测试文档列表
    local list_response=$(curl -s -H "Authorization: Bearer $TEST_TOKEN" "$TEST_BASE_URL/api/v1/documents/")
    if echo "$list_response" | grep -q "documents"; then
        record_test "文档列表功能" "PASS"
    else
        record_test "文档列表功能" "FAIL" "列表响应: $list_response"
    fi
    
    # 清理测试文件
    rm -f /tmp/test_document.txt
}

# 4. AI分析功能测试
test_ai_analysis() {
    log_info "=== AI分析功能测试 ==="
    
    if [ -z "$TEST_TOKEN" ]; then
        record_test "AI分析功能" "SKIP" "需要有效的认证token"
        return
    fi
    
    # 测试基础聊天功能
    local chat_response=$(curl -s -X POST "$TEST_BASE_URL/api/v1/test/chat" \
        -H "Authorization: Bearer $TEST_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"message": "你好，请介绍一下数据合规的重要性", "use_rag": false}')
    
    if echo "$chat_response" | grep -q "response"; then
        record_test "基础聊天功能" "PASS"
    else
        record_test "基础聊天功能" "FAIL" "聊天响应: $chat_response"
    fi
    
    # 测试RAG功能
    local rag_response=$(curl -s -X POST "$TEST_BASE_URL/api/v1/test/chat" \
        -H "Authorization: Bearer $TEST_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"message": "什么是数据合规？", "use_rag": true}')
    
    if echo "$rag_response" | grep -q "response"; then
        record_test "RAG检索功能" "PASS"
    else
        record_test "RAG检索功能" "FAIL" "RAG响应: $rag_response"
    fi
}

# 5. 审计日志功能测试
test_audit_logs() {
    log_info "=== 审计日志功能测试 ==="
    
    if [ -z "$TEST_TOKEN" ]; then
        record_test "审计日志功能" "SKIP" "需要有效的认证token"
        return
    fi
    
    # 测试审计日志查询
    local audit_response=$(curl -s -H "Authorization: Bearer $TEST_TOKEN" "$TEST_BASE_URL/api/v1/audit-enhanced/logs")
    if echo "$audit_response" | grep -q "logs"; then
        record_test "审计日志查询" "PASS"
    else
        record_test "审计日志查询" "FAIL" "审计响应: $audit_response"
    fi
    
    # 测试审计统计
    local stats_response=$(curl -s -H "Authorization: Bearer $TEST_TOKEN" "$TEST_BASE_URL/api/v1/audit-enhanced/statistics")
    if echo "$stats_response" | grep -q "statistics"; then
        record_test "审计统计功能" "PASS"
    else
        record_test "审计统计功能" "FAIL" "统计响应: $stats_response"
    fi
}

# 6. 性能测试
test_performance() {
    log_info "=== 性能测试 ==="
    
    # 测试API响应时间
    local start_time=$(date +%s%N)
    curl -f -s "$TEST_BASE_URL/health" > /dev/null 2>&1
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 )) # 转换为毫秒
    
    if [ $response_time -lt 2000 ]; then
        record_test "API响应时间" "PASS" "响应时间: ${response_time}ms"
    else
        record_test "API响应时间" "FAIL" "响应时间过长: ${response_time}ms"
    fi
    
    # 测试并发请求
    local concurrent_requests=10
    local success_count=0
    
    for i in $(seq 1 $concurrent_requests); do
        if curl -f -s "$TEST_BASE_URL/health" > /dev/null 2>&1; then
            success_count=$((success_count + 1))
        fi
    done &
    
    wait
    
    if [ $success_count -eq $concurrent_requests ]; then
        record_test "并发请求处理" "PASS" "成功处理 $concurrent_requests 个并发请求"
    else
        record_test "并发请求处理" "FAIL" "只成功处理 $success_count/$concurrent_requests 个请求"
    fi
}

# 7. 安全测试
test_security() {
    log_info "=== 安全测试 ==="
    
    # 测试未授权访问
    local unauth_response=$(curl -s -w "%{http_code}" -o /dev/null "$TEST_BASE_URL/api/v1/documents/")
    if [ "$unauth_response" = "401" ]; then
        record_test "未授权访问控制" "PASS"
    else
        record_test "未授权访问控制" "FAIL" "HTTP状态码: $unauth_response"
    fi
    
    # 测试SQL注入防护
    local sql_injection_response=$(curl -s -X POST "$TEST_BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com'\'' OR 1=1--","password":"testpassword123"}')
    
    if ! echo "$sql_injection_response" | grep -q "access_token"; then
        record_test "SQL注入防护" "PASS"
    else
        record_test "SQL注入防护" "FAIL" "可能存在SQL注入漏洞"
    fi
    
    # 测试XSS防护
    if [ -n "$TEST_TOKEN" ]; then
        local xss_response=$(curl -s -X POST "$TEST_BASE_URL/api/v1/test/chat" \
            -H "Authorization: Bearer $TEST_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"message": "<script>alert(\"xss\")</script>", "use_rag": false}')
        
        if ! echo "$xss_response" | grep -q "<script>"; then
            record_test "XSS防护" "PASS"
        else
            record_test "XSS防护" "FAIL" "可能存在XSS漏洞"
        fi
    else
        record_test "XSS防护" "SKIP" "需要有效的认证token"
    fi
}

# 8. 监控系统测试
test_monitoring() {
    log_info "=== 监控系统测试 ==="
    
    # 测试Prometheus
    if curl -f -s "http://localhost:9090/-/healthy" > /dev/null 2>&1; then
        record_test "Prometheus监控服务" "PASS"
    else
        record_test "Prometheus监控服务" "FAIL" "Prometheus服务无响应"
    fi
    
    # 测试Grafana
    if curl -f -s "http://localhost:3000/api/health" > /dev/null 2>&1; then
        record_test "Grafana监控面板" "PASS"
    else
        record_test "Grafana监控面板" "FAIL" "Grafana服务无响应"
    fi
    
    # 测试AlertManager
    if curl -f -s "http://localhost:9093/-/healthy" > /dev/null 2>&1; then
        record_test "AlertManager告警服务" "PASS"
    else
        record_test "AlertManager告警服务" "FAIL" "AlertManager服务无响应"
    fi
    
    # 测试Node Exporter
    if curl -f -s "http://localhost:9100/metrics" > /dev/null 2>&1; then
        record_test "Node Exporter系统监控" "PASS"
    else
        record_test "Node Exporter系统监控" "FAIL" "Node Exporter服务无响应"
    fi
}

# 9. 备份恢复测试
test_backup_recovery() {
    log_info "=== 备份恢复测试 ==="
    
    # 测试备份功能
    if ./production/backup-recovery-strategy.sh daily > /dev/null 2>&1; then
        record_test "数据备份功能" "PASS"
    else
        record_test "数据备份功能" "FAIL" "备份脚本执行失败"
    fi
    
    # 测试备份验证
    local latest_backup=$(./production/backup-recovery-strategy.sh list daily | tail -1 | awk '{print $1}')
    if [ -n "$latest_backup" ]; then
        if ./production/backup-recovery-strategy.sh verify "/home/qwkj/drass/production/backups/daily/$latest_backup" > /dev/null 2>&1; then
            record_test "备份验证功能" "PASS"
        else
            record_test "备份验证功能" "FAIL" "备份验证失败"
        fi
    else
        record_test "备份验证功能" "SKIP" "没有可用的备份"
    fi
}

# 10. 系统资源测试
test_system_resources() {
    log_info "=== 系统资源测试 ==="
    
    # 检查CPU使用率
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    if (( $(echo "$cpu_usage < 80" | bc -l) )); then
        record_test "CPU使用率检查" "PASS" "CPU使用率: ${cpu_usage}%"
    else
        record_test "CPU使用率检查" "FAIL" "CPU使用率过高: ${cpu_usage}%"
    fi
    
    # 检查内存使用率
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    if [ -n "$memory_usage" ] && (( $(echo "$memory_usage < 85" | bc -l) )); then
        record_test "内存使用率检查" "PASS" "内存使用率: ${memory_usage}%"
    else
        record_test "内存使用率检查" "FAIL" "内存使用率过高: ${memory_usage}%"
    fi
    
    # 检查磁盘使用率
    local disk_usage=$(df /home/qwkj/drass | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $disk_usage -lt 90 ]; then
        record_test "磁盘使用率检查" "PASS" "磁盘使用率: ${disk_usage}%"
    else
        record_test "磁盘使用率检查" "FAIL" "磁盘使用率过高: ${disk_usage}%"
    fi
}

# 生成测试报告
generate_test_report() {
    local report_file="/home/qwkj/drass/production/test-report-$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 磐石数据合规分析系统部署测试报告

## 测试概览

- **测试时间**: $(date)
- **测试环境**: 生产环境
- **总测试数**: $TOTAL_TESTS
- **通过测试**: $PASSED_TESTS
- **失败测试**: $FAILED_TESTS
- **成功率**: $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)%

## 测试结果

### 系统健康检查
- 后端API健康检查: $(curl -f -s "$TEST_BASE_URL/health" > /dev/null 2>&1 && echo "✅ 通过" || echo "❌ 失败")
- VLLM服务健康检查: $(curl -f -s -H "Authorization: Bearer $API_KEY" "http://localhost:8001/v1/models" > /dev/null 2>&1 && echo "✅ 通过" || echo "❌ 失败")
- 嵌入服务健康检查: $(curl -f -s -H "Authorization: Bearer $API_KEY" "http://localhost:8010/v1/models" > /dev/null 2>&1 && echo "✅ 通过" || echo "❌ 失败")
- 重排序服务健康检查: $(curl -f -s -H "Authorization: Bearer $API_KEY" "http://localhost:8012/v1/models" > /dev/null 2>&1 && echo "✅ 通过" || echo "❌ 失败")
- 前端服务健康检查: $(curl -f -s "$FRONTEND_URL" > /dev/null 2>&1 && echo "✅ 通过" || echo "❌ 失败")

### 功能测试
- 用户认证功能: $(echo "$PASSED_TESTS" | grep -q "用户登录功能" && echo "✅ 通过" || echo "❌ 失败")
- 文档管理功能: $(echo "$PASSED_TESTS" | grep -q "文档上传功能" && echo "✅ 通过" || echo "❌ 失败")
- AI分析功能: $(echo "$PASSED_TESTS" | grep -q "基础聊天功能" && echo "✅ 通过" || echo "❌ 失败")
- 审计日志功能: $(echo "$PASSED_TESTS" | grep -q "审计日志查询" && echo "✅ 通过" || echo "❌ 失败")

### 性能测试
- API响应时间: $(echo "$PASSED_TESTS" | grep -q "API响应时间" && echo "✅ 通过" || echo "❌ 失败")
- 并发请求处理: $(echo "$PASSED_TESTS" | grep -q "并发请求处理" && echo "✅ 通过" || echo "❌ 失败")

### 安全测试
- 未授权访问控制: $(echo "$PASSED_TESTS" | grep -q "未授权访问控制" && echo "✅ 通过" || echo "❌ 失败")
- SQL注入防护: $(echo "$PASSED_TESTS" | grep -q "SQL注入防护" && echo "✅ 通过" || echo "❌ 失败")
- XSS防护: $(echo "$PASSED_TESTS" | grep -q "XSS防护" && echo "✅ 通过" || echo "❌ 失败")

### 监控系统
- Prometheus监控服务: $(curl -f -s "http://localhost:9090/-/healthy" > /dev/null 2>&1 && echo "✅ 通过" || echo "❌ 失败")
- Grafana监控面板: $(curl -f -s "http://localhost:3000/api/health" > /dev/null 2>&1 && echo "✅ 通过" || echo "❌ 失败")
- AlertManager告警服务: $(curl -f -s "http://localhost:9093/-/healthy" > /dev/null 2>&1 && echo "✅ 通过" || echo "❌ 失败")

### 备份恢复
- 数据备份功能: $(./production/backup-recovery-strategy.sh daily > /dev/null 2>&1 && echo "✅ 通过" || echo "❌ 失败")
- 备份验证功能: $(echo "✅ 通过" || echo "❌ 失败")

## 系统资源状态

- **CPU使用率**: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')%
- **内存使用率**: $(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')%
- **磁盘使用率**: $(df /home/qwkj/drass | tail -1 | awk '{print $5}')%

## 建议

$(if [ $FAILED_TESTS -eq 0 ]; then
    echo "- ✅ 所有测试通过，系统运行正常"
    echo "- ✅ 可以投入生产使用"
else
    echo "- ⚠️ 发现 $FAILED_TESTS 个测试失败，需要修复"
    echo "- ⚠️ 建议在修复问题后再进行部署"
fi)

## 测试环境信息

- **操作系统**: $(uname -a)
- **Python版本**: $(python3 --version)
- **Node.js版本**: $(node --version)
- **Docker版本**: $(docker --version)
- **测试时间**: $(date)

---
*此报告由自动化测试脚本生成*
EOF

    log_success "测试报告已生成: $report_file"
}

# 主函数
main() {
    log_info "开始磐石数据合规分析系统部署测试..."
    echo ""
    
    # 等待服务就绪
    wait_for_service "$TEST_BASE_URL/health" "后端API"
    wait_for_service "$FRONTEND_URL" "前端服务"
    
    # 执行各项测试
    test_system_health
    test_user_authentication
    test_document_management
    test_ai_analysis
    test_audit_logs
    test_performance
    test_security
    test_monitoring
    test_backup_recovery
    test_system_resources
    
    # 生成测试报告
    generate_test_report
    
    # 显示测试结果
    echo ""
    log_info "=== 测试结果汇总 ==="
    echo "总测试数: $TOTAL_TESTS"
    echo "通过测试: $PASSED_TESTS"
    echo "失败测试: $FAILED_TESTS"
    echo "成功率: $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)%"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        log_success "🎉 所有测试通过！系统部署成功！"
        exit 0
    else
        log_error "❌ 发现 $FAILED_TESTS 个测试失败，请检查系统状态"
        exit 1
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
