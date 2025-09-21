# 磐石数据合规分析系统常见问题FAQ

## 📋 目录

1. [系统访问问题](#系统访问问题)
2. [功能使用问题](#功能使用问题)
3. [性能相关问题](#性能相关问题)
4. [数据管理问题](#数据管理问题)
5. [安全相关问题](#安全相关问题)
6. [故障排除问题](#故障排除问题)
7. [部署配置问题](#部署配置问题)

---

## 系统访问问题

### Q1: 无法访问系统首页，显示"连接被拒绝"

**A:** 可能的原因和解决方案：

1. **服务未启动**
   ```bash
   # 检查服务状态
   ./production/health-check.sh
   
   # 启动服务
   sudo systemctl start drass-main-app
   sudo systemctl start drass-frontend
   ```

2. **端口被占用**
   ```bash
   # 检查端口占用
   lsof -i :5173,8888
   
   # 释放端口
   sudo kill -9 $(lsof -ti:5173)
   sudo kill -9 $(lsof -ti:8888)
   ```

3. **防火墙阻止**
   ```bash
   # 检查防火墙状态
   sudo ufw status
   
   # 开放端口
   sudo ufw allow 5173
   sudo ufw allow 8888
   ```

### Q2: 登录时提示"用户名或密码错误"

**A:** 解决方案：

1. **检查账户信息**
   - 默认测试账户：test@example.com / testpassword123
   - 确认邮箱格式正确
   - 检查密码大小写

2. **重置密码**
   ```bash
   # 联系管理员重置密码
   ./production/reset-password.sh test@example.com
   ```

3. **检查数据库连接**
   ```bash
   # 检查数据库文件
   ls -la /home/qwkj/drass/data/database.db
   
   # 检查数据库完整性
   sqlite3 /home/qwkj/drass/data/database.db "PRAGMA integrity_check;"
   ```

### Q3: 页面加载缓慢或超时

**A:** 可能的原因和解决方案：

1. **系统资源不足**
   ```bash
   # 检查系统资源
   free -h
   df -h
   top
   ```

2. **网络连接问题**
   ```bash
   # 检查网络连接
   ping localhost
   curl -I http://localhost:8888/health
   ```

3. **服务响应慢**
   ```bash
   # 检查服务日志
   tail -f /home/qwkj/drass/production/logs/app/main-app.log
   ```

---

## 功能使用问题

### Q4: 文档上传失败，提示"文件格式不支持"

**A:** 解决方案：

1. **检查文件格式**
   - 支持格式：PDF、DOC、DOCX、XLS、XLSX、PPT、PPTX、TXT、MD、CSV
   - 确认文件扩展名正确
   - 检查文件是否损坏

2. **检查文件大小**
   - 单个文件最大100MB
   - 批量上传总大小限制500MB
   - 压缩大文件后上传

3. **检查存储空间**
   ```bash
   # 检查磁盘空间
   df -h /home/qwkj/drass/data/uploads
   ```

### Q5: AI分析助手无响应或回答质量差

**A:** 解决方案：

1. **检查VLLM服务**
   ```bash
   # 检查VLLM服务状态
   curl -H "Authorization: Bearer 123456" http://localhost:8001/v1/models
   
   # 重启VLLM服务
   sudo systemctl restart vllm-service
   ```

2. **检查模型加载**
   ```bash
   # 检查模型文件
   ls -la /models/Qwen2.5-8B-Instruct/
   
   # 检查GPU内存
   nvidia-smi
   ```

3. **调整参数设置**
   - 减少max_tokens数量
   - 调整temperature参数
   - 启用/禁用RAG模式

### Q6: 审计日志显示不完整或缺失

**A:** 解决方案：

1. **检查日志服务**
   ```bash
   # 检查审计服务状态
   curl http://localhost:8888/api/v1/audit-enhanced/health
   
   # 查看审计日志
   tail -f /home/qwkj/drass/production/logs/audit/audit.log
   ```

2. **检查数据库连接**
   ```bash
   # 检查审计数据库
   sqlite3 /home/qwkj/drass/data/audit_logs.db "SELECT COUNT(*) FROM audit_logs;"
   ```

3. **重新生成日志**
   - 重启审计服务
   - 清理缓存数据
   - 重新执行操作

---

## 性能相关问题

### Q7: 系统响应速度慢，操作卡顿

**A:** 解决方案：

1. **检查系统资源**
   ```bash
   # 检查CPU使用率
   top -p $(pgrep -d',' -f "vllm|uvicorn|npm")
   
   # 检查内存使用
   free -h
   
   # 检查磁盘I/O
   iostat -x 1
   ```

2. **优化系统配置**
   ```bash
   # 调整工作进程数
   vim /home/qwkj/drass/production/.env.production
   # 修改 WORKERS=2
   
   # 重启服务
   sudo systemctl restart drass-main-app
   ```

3. **清理系统资源**
   ```bash
   # 清理临时文件
   find /tmp -name "drass_*" -mtime +1 -delete
   
   # 清理日志文件
   find /home/qwkj/drass/production/logs -name "*.log" -mtime +7 -delete
   ```

### Q8: 并发用户数限制，多用户访问时系统变慢

**A:** 解决方案：

1. **增加系统资源**
   - 增加CPU核心数
   - 增加内存容量
   - 使用SSD存储

2. **优化配置参数**
   ```bash
   # 增加工作进程数
   WORKERS=8
   
   # 增加连接池大小
   DB_POOL_SIZE=20
   
   # 启用缓存
   ENABLE_CACHE=true
   ```

3. **使用负载均衡**
   - 部署多个实例
   - 配置Nginx负载均衡
   - 使用Redis共享会话

### Q9: 内存使用率过高，系统不稳定

**A:** 解决方案：

1. **检查内存泄漏**
   ```bash
   # 检查进程内存使用
   ps aux --sort=-%mem | head -10
   
   # 检查内存详情
   cat /proc/meminfo
   ```

2. **优化内存配置**
   ```bash
   # 调整VLLM内存使用
   vim /home/qwkj/drass/production/.env.production
   # 修改 GPU_MEMORY_UTILIZATION=0.6
   ```

3. **重启服务释放内存**
   ```bash
   # 重启所有服务
   sudo systemctl restart drass-main-app
   sudo systemctl restart drass-frontend
   ```

---

## 数据管理问题

### Q10: 文档上传后无法在知识库中找到

**A:** 解决方案：

1. **检查文档处理状态**
   - 查看文档处理进度
   - 等待处理完成
   - 检查处理错误信息

2. **检查向量数据库**
   ```bash
   # 检查ChromaDB状态
   ls -la /home/qwkj/drass/data/chromadb/
   
   # 重启向量数据库
   pkill -f chromadb
   python -m chromadb.app --path /home/qwkj/drass/data/chromadb --port 8005 &
   ```

3. **重新处理文档**
   - 删除失败的文档
   - 重新上传文档
   - 检查文档格式

### Q11: 数据备份失败或备份文件损坏

**A:** 解决方案：

1. **检查备份脚本**
   ```bash
   # 手动执行备份
   ./production/backup-recovery-strategy.sh daily
   
   # 检查备份日志
   tail -f /home/qwkj/drass/production/logs/backup.log
   ```

2. **检查存储空间**
   ```bash
   # 检查备份目录空间
   df -h /home/qwkj/drass/production/backups/
   
   # 清理旧备份
   ./production/backup-recovery-strategy.sh cleanup
   ```

3. **验证备份完整性**
   ```bash
   # 验证最新备份
   ./production/backup-recovery-strategy.sh verify $(./production/backup-recovery-strategy.sh list daily | tail -1)
   ```

### Q12: 数据库文件损坏或丢失

**A:** 解决方案：

1. **检查数据库状态**
   ```bash
   # 检查数据库文件
   ls -la /home/qwkj/drass/data/database.db
   
   # 检查数据库完整性
   sqlite3 /home/qwkj/drass/data/database.db "PRAGMA integrity_check;"
   ```

2. **从备份恢复**
   ```bash
   # 停止服务
   sudo systemctl stop drass-main-app
   
   # 恢复数据库
   ./production/backup-recovery-strategy.sh restore /path/to/backup
   
   # 启动服务
   sudo systemctl start drass-main-app
   ```

3. **重建数据库**
   ```bash
   # 删除损坏的数据库
   rm /home/qwkj/drass/data/database.db
   
   # 重新初始化数据库
   cd services/main-app
   python -c "from app.database.migration_manager import create_migration_manager; create_migration_manager().run_migrations()"
   ```

---

## 安全相关问题

### Q13: 系统提示"权限不足"或"访问被拒绝"

**A:** 解决方案：

1. **检查用户权限**
   - 确认用户角色
   - 联系管理员分配权限
   - 检查权限配置

2. **检查文件权限**
   ```bash
   # 检查数据目录权限
   ls -la /home/qwkj/drass/data/
   
   # 修复权限
   chmod -R 755 /home/qwkj/drass/data/
   chown -R qwkj:qwkj /home/qwkj/drass/data/
   ```

3. **检查服务权限**
   ```bash
   # 检查服务用户
   ps aux | grep -E "(vllm|uvicorn|npm)"
   
   # 重启服务
   sudo systemctl restart drass-main-app
   ```

### Q14: 系统检测到异常登录或安全威胁

**A:** 解决方案：

1. **检查登录日志**
   ```bash
   # 查看登录日志
   grep "login" /home/qwkj/drass/production/logs/audit/audit.log
   
   # 查看失败登录
   grep "failed" /home/qwkj/drass/production/logs/audit/audit.log
   ```

2. **加强安全措施**
   - 修改默认密码
   - 启用IP白名单
   - 设置登录失败锁定
   - 启用双因素认证

3. **联系安全团队**
   - 报告安全事件
   - 获取安全建议
   - 执行安全审计

### Q15: SSL证书过期或配置错误

**A:** 解决方案：

1. **检查证书状态**
   ```bash
   # 检查证书有效期
   openssl x509 -in /home/qwkj/drass/production/nginx/ssl/cert.pem -text -noout | grep "Not After"
   
   # 测试SSL连接
   openssl s_client -connect localhost:443 -servername localhost
   ```

2. **更新证书**
   ```bash
   # 生成新证书
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
       -keyout /home/qwkj/drass/production/nginx/ssl/key.pem \
       -out /home/qwkj/drass/production/nginx/ssl/cert.pem
   
   # 重启Nginx
   docker restart nginx
   ```

3. **配置自动续期**
   - 使用Let's Encrypt
   - 设置自动续期脚本
   - 配置证书监控

---

## 故障排除问题

### Q16: 系统突然崩溃或服务异常停止

**A:** 解决方案：

1. **检查系统日志**
   ```bash
   # 查看系统日志
   journalctl -u drass-main-app --since "1 hour ago"
   journalctl -u drass-frontend --since "1 hour ago"
   
   # 查看应用日志
   tail -100 /home/qwkj/drass/production/logs/app/*.log
   ```

2. **检查系统资源**
   ```bash
   # 检查系统负载
   uptime
   top
   
   # 检查内存使用
   free -h
   
   # 检查磁盘空间
   df -h
   ```

3. **重启服务**
   ```bash
   # 重启所有服务
   sudo systemctl restart drass-main-app
   sudo systemctl restart drass-frontend
   
   # 检查服务状态
   sudo systemctl status drass-main-app
   sudo systemctl status drass-frontend
   ```

### Q17: 监控系统无数据或告警失效

**A:** 解决方案：

1. **检查监控服务**
   ```bash
   # 检查Prometheus状态
   docker ps | grep prometheus
   curl http://localhost:9090/-/healthy
   
   # 检查Grafana状态
   docker ps | grep grafana
   curl http://localhost:3000/api/health
   ```

2. **检查指标收集**
   ```bash
   # 检查指标端点
   curl http://localhost:8888/metrics
   curl http://localhost:9100/metrics
   
   # 检查Prometheus配置
   docker exec prometheus cat /etc/prometheus/prometheus.yml
   ```

3. **重启监控服务**
   ```bash
   # 重启监控服务
   docker restart prometheus
   docker restart grafana
   docker restart node-exporter
   ```

### Q18: 系统升级后功能异常

**A:** 解决方案：

1. **回滚到之前版本**
   ```bash
   # 停止服务
   sudo systemctl stop drass-main-app
   sudo systemctl stop drass-frontend
   
   # 恢复备份
   ./production/backup-recovery-strategy.sh restore /path/to/backup
   
   # 启动服务
   sudo systemctl start drass-main-app
   sudo systemctl start drass-frontend
   ```

2. **检查配置文件**
   ```bash
   # 检查配置文件
   diff /home/qwkj/drass/production/.env.production /home/qwkj/drass/production/.env.production.backup
   
   # 恢复配置文件
   cp /home/qwkj/drass/production/.env.production.backup /home/qwkj/drass/production/.env.production
   ```

3. **重新部署**
   ```bash
   # 重新部署系统
   ./deployment/production/deploy-production.sh
   ```

---

## 部署配置问题

### Q19: 部署过程中出现依赖错误

**A:** 解决方案：

1. **检查系统依赖**
   ```bash
   # 检查Python版本
   python3 --version
   
   # 检查Node.js版本
   node --version
   
   # 检查Docker版本
   docker --version
   docker-compose --version
   ```

2. **安装缺失依赖**
   ```bash
   # 安装Python依赖
   pip install -r services/main-app/requirements.txt
   
   # 安装Node.js依赖
   cd frontend && npm install
   
   # 安装系统依赖
   sudo apt update
   sudo apt install -y python3-pip nodejs npm docker.io docker-compose
   ```

3. **清理并重新安装**
   ```bash
   # 清理缓存
   pip cache purge
   npm cache clean --force
   
   # 重新安装
   pip install -r services/main-app/requirements.txt
   cd frontend && npm install
   ```

### Q20: 配置文件格式错误或参数无效

**A:** 解决方案：

1. **验证配置文件**
   ```bash
   # 验证YAML格式
   python -c "import yaml; yaml.safe_load(open('/home/qwkj/drass/production/configs/monitoring/prometheus.yml'))"
   
   # 验证JSON格式
   python -c "import json; json.load(open('/home/qwkj/drass/production/configs/monitoring/grafana/datasources/prometheus.yml'))"
   ```

2. **检查配置参数**
   ```bash
   # 检查环境变量
   cat /home/qwkj/drass/production/.env.production
   
   # 验证配置
   ./deployment/production/validate-config.sh
   ```

3. **使用默认配置**
   ```bash
   # 恢复默认配置
   cp /home/qwkj/drass/deployment/configs/presets/ubuntu-amd-production.yaml /home/qwkj/drass/production/configs/
   
   # 重新生成配置
   ./deployment/production/deploy-production.sh config
   ```

### Q21: 端口冲突或服务启动失败

**A:** 解决方案：

1. **检查端口占用**
   ```bash
   # 检查所有端口占用
   netstat -tlnp | grep -E "(8001|8010|8012|8888|5173|9090|3000)"
   
   # 释放被占用的端口
   sudo kill -9 $(lsof -ti:8001)
   sudo kill -9 $(lsof -ti:8010)
   sudo kill -9 $(lsof -ti:8012)
   sudo kill -9 $(lsof -ti:8888)
   sudo kill -9 $(lsof -ti:5173)
   ```

2. **修改端口配置**
   ```bash
   # 修改配置文件
   vim /home/qwkj/drass/production/.env.production
   
   # 修改端口号
   API_PORT=8889
   FRONTEND_PORT=5174
   ```

3. **重新启动服务**
   ```bash
   # 重新启动所有服务
   ./deployment/production/deploy-production.sh restart
   ```

---

## 联系支持

### 获取帮助

如果您遇到的问题不在上述FAQ中，请通过以下方式获取帮助：

1. **在线文档**
   - 用户手册：http://localhost:5173/docs/user-manual
   - 管理员手册：http://localhost:5173/docs/admin-manual
   - API文档：http://localhost:8888/docs

2. **技术支持**
   - 邮箱：support@drass.example.com
   - 电话：400-xxx-xxxx
   - 在线客服：http://localhost:5173/support

3. **社区支持**
   - GitHub Issues：https://github.com/drass/drass/issues
   - 技术论坛：http://localhost:5173/forum
   - 用户群组：QQ群 123456789

### 问题报告

在报告问题时，请提供以下信息：

1. **系统信息**
   - 操作系统版本
   - 系统架构
   - 内存和CPU信息

2. **错误信息**
   - 错误消息截图
   - 相关日志文件
   - 复现步骤

3. **环境信息**
   - 系统版本
   - 配置信息
   - 最近的操作

---

**版本信息**
- 文档版本：v1.0.0
- 系统版本：v1.0.0
- 更新日期：2025年9月21日
- 适用环境：生产环境
