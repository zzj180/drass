# Drass 微服务组件

本目录包含Drass系统的自定义微服务组件。

## 服务列表

### 1. doc-processor (文档处理服务)

**功能**：将各种格式的文档转换为Markdown格式

**端口**：5003

**支持格式**：
- 文档：PDF, DOC, DOCX, ODT, RTF, TXT, MD
- 表格：XLS, XLSX, CSV, ODS  
- 演示：PPT, PPTX, ODP
- 图片：JPG, JPEG, PNG, GIF, BMP, TIFF（OCR支持）

**API端点**：
- `GET /health` - 健康检查
- `POST /convert` - 单文档转换
- `POST /batch_convert` - 批量文档转换

**环境变量**：
```bash
MAX_FILE_SIZE=50MB              # 最大文件大小
OCR_ENABLED=true                # 启用OCR
OCR_LANGUAGE=chi_sim,eng        # OCR语言（中文简体+英文）
PANDOC_ENABLED=true             # 启用Pandoc转换
```

**使用示例**：
```bash
# 转换单个文档
curl -X POST http://localhost:5003/convert \
  -F "file=@document.pdf"

# 批量转换
curl -X POST http://localhost:5003/batch_convert \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.docx"
```

### 2. scheduler (定时任务调度器)

**功能**：执行定时任务，包括知识库更新、数据清理和备份

**定时任务**：
- 知识库更新：每天凌晨2点
- 数据清理：每周日凌晨3点
- 数据备份：每天凌晨4点
- 健康检查：每5分钟

**环境变量**：
```bash
KNOWLEDGE_BASE_UPDATE_CRON=0 2 * * *    # 知识库更新时间
CLEANUP_CRON=0 3 * * 0                  # 清理任务时间
BACKUP_CRON=0 4 * * *                   # 备份任务时间
API_URL=http://api:5001                 # Dify API地址
DIFY_API_KEY=your-api-key              # API密钥
```

**Cron表达式格式**：
```
分 时 日 月 周
0  2  *  *  *  = 每天凌晨2点
0  3  *  *  0  = 每周日凌晨3点
*/5 * * * *    = 每5分钟
```

## 本地开发

### doc-processor服务

```bash
cd doc-processor

# 安装依赖
pip install -r requirements.txt

# 安装系统依赖（Ubuntu/Debian）
apt-get install pandoc tesseract-ocr tesseract-ocr-chi-sim

# 运行服务
python app.py
```

### scheduler服务

```bash
cd scheduler

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export API_URL=http://localhost:5001
export DIFY_API_KEY=your-api-key

# 运行服务
python scheduler.py
```

## Docker构建

### 构建单个服务

```bash
# 构建doc-processor
docker build -t drass-doc-processor ./doc-processor

# 构建scheduler
docker build -t drass-scheduler ./scheduler
```

### 使用docker-compose构建

在项目根目录运行：

```bash
docker-compose build doc-processor scheduler
```

## 服务监控

### 健康检查

```bash
# doc-processor健康检查
curl http://localhost:5003/health

# 查看scheduler日志
docker logs drass-scheduler
```

### 日志位置

- doc-processor: 输出到stdout
- scheduler: `/app/logs/scheduler.log`

## 故障排除

### doc-processor常见问题

1. **OCR不工作**
   - 确认OCR_ENABLED=true
   - 检查tesseract是否正确安装
   - 验证语言包是否安装（tesseract-ocr-chi-sim）

2. **PDF转换失败**
   - 检查poppler-utils是否安装
   - 尝试使用pandoc作为备选方案

3. **Office文档转换失败**
   - 确认libreoffice已安装
   - 检查文件权限

### scheduler常见问题

1. **任务未执行**
   - 检查cron表达式格式
   - 验证API_URL和API_KEY配置
   - 查看日志文件

2. **备份失败**
   - 确认有足够的磁盘空间
   - 检查备份目录权限
   - 验证API连接

## 扩展开发

### 添加新的文档格式支持

编辑`doc-processor/app.py`，在`DocumentConverter`类中添加新的转换方法：

```python
def _convert_new_format(self, file_path: str) -> str:
    """转换新格式"""
    # 实现转换逻辑
    return markdown_content
```

### 添加新的定时任务

编辑`scheduler/scheduler.py`，在`TaskScheduler`类中添加新任务：

```python
def new_task(self):
    """新的定时任务"""
    # 实现任务逻辑
    pass

# 在_setup_jobs中注册
self.scheduler.add_job(
    func=self.new_task,
    trigger=CronTrigger.from_crontab('0 5 * * *'),
    id='new_task',
    name='New Task'
)
```

## 性能优化

### doc-processor优化

- 使用缓存避免重复转换
- 实施文件大小限制
- 使用异步处理大文件
- 配置worker数量

### scheduler优化

- 避免任务重叠执行
- 实施任务超时机制
- 使用分布式锁避免重复执行
- 监控任务执行时间

## 安全注意事项

1. **文件上传安全**
   - 限制文件大小
   - 验证文件类型
   - 病毒扫描
   - 沙箱环境执行

2. **API安全**
   - 使用强密钥
   - 实施访问控制
   - 日志审计
   - 限流保护

3. **数据安全**
   - 加密敏感数据
   - 定期备份
   - 安全删除临时文件
   - 权限最小化原则