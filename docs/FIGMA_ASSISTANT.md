# Figma UI开发助手使用文档

## 概述

Figma UI开发助手是一个自动化工具，能够：
- 通过Figma API获取设计文件
- 智能分析UI结构和组件
- 自动生成开发需求backlog
- 创建GitHub Issues和项目看板
- 支持实时Webhook更新

## 功能特性

### 🎨 设计文件分析
- 自动识别页面和组件结构
- 分析布局类型和样式信息
- 提取组件层次关系
- 生成详细的设计分析报告

### 📋 任务生成
- 智能生成开发任务
- 自动估算工时
- 识别任务依赖关系
- 支持多种任务类型（页面、组件、集成）

### 🚀 GitHub集成
- 自动创建Issues
- 生成项目看板
- 支持标签和分配
- 实时同步设计更新

### 🔄 实时更新
- Webhook支持
- 自动检测设计变更
- 队列处理机制
- 后台异步处理

## 安装配置

### 1. 环境要求
- Python 3.7+
- 网络访问权限
- Figma账户和API访问权限
- GitHub账户和Personal Access Token

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 环境变量配置
复制 `config/figma-assistant.env.example` 为 `.env` 并配置：

```bash
# Figma API配置
FIGMA_ACCESS_TOKEN=your_figma_access_token_here

# GitHub API配置
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_OWNER=your_github_username_or_org_name
GITHUB_REPOSITORY=your_repository_name

# Webhook配置（可选）
FIGMA_WEBHOOK_SECRET=your_webhook_secret_here
```

### 4. 获取API密钥

#### Figma Access Token
1. 登录 [Figma](https://www.figma.com)
2. 进入 Settings > Account > Personal access tokens
3. 点击 "Generate new token"
4. 复制生成的token

#### GitHub Personal Access Token
1. 登录 [GitHub](https://github.com)
2. 进入 Settings > Developer settings > Personal access tokens
3. 点击 "Generate new token (classic)"
4. 选择需要的权限：
   - `repo` - 仓库访问权限
   - `workflow` - 工作流权限（可选）

## 使用方法

### 1. 命令行使用

#### 基本用法
```bash
# 分析Figma文件
python scripts/figma_assistant.py --file-key YOUR_FIGMA_FILE_KEY

# 分析并创建GitHub Issues
python scripts/figma_assistant.py --file-key YOUR_FIGMA_FILE_KEY --create-issues

# 分析并创建项目看板
python scripts/figma_assistant.py --file-key YOUR_FIGMA_FILE_KEY --create-board

# 保存分析结果到文件
python scripts/figma_assistant.py --file-key YOUR_FIGMA_FILE_KEY --output analysis_result.json
```

#### 完整示例
```bash
python scripts/figma_assistant.py \
  --file-key "abc123def456" \
  --create-issues \
  --create-board \
  --project-name "新功能开发" \
  --output "ui_analysis.json"
```

### 2. Webhook服务

#### 启动Webhook服务
```bash
python scripts/figma_webhook.py
```

#### 配置Figma Webhook
1. 在Figma中进入文件设置
2. 选择 "Integrations" > "Webhooks"
3. 添加新的webhook：
   - URL: `https://your-domain.com/webhook/figma`
   - Events: 选择 "File update"
   - Secret: 设置webhook密钥

#### Webhook端点
- `POST /webhook/figma` - 接收Figma更新
- `GET /health` - 健康检查
- `POST /process/<file_key>` - 手动触发处理
- `GET /status` - 获取处理状态

### 3. 程序化使用

```python
from scripts.figma_assistant import FigmaAssistant

# 创建助手实例
assistant = FigmaAssistant()

# 处理Figma文件
result = assistant.process_figma_file("your_file_key")

# 创建GitHub Issues
tasks = result["tasks"]
issues = assistant.create_github_issues(tasks)

# 创建项目看板
board = assistant.create_project_board("UI开发项目", tasks)
```

## 配置说明

### 应用配置 (`apps/figma-assistant.yml`)

```yaml
name: "Figma UI开发助手"
description: "通过Figma API获取设计文件，拆解UI页面，生成开发需求backlog并创建GitHub Issue"
version: "1.0.0"
type: "assistant"

# 应用配置
app_config:
  model:
    provider: "openai"
    name: "gpt-4"
    parameters:
      temperature: 0.7
      max_tokens: 4000
  
  prompt_template: |
    你是一个专业的UI开发助手，负责分析Figma设计文件并生成开发需求。
    # ... 更多配置
```

### 工作流配置

```yaml
workflow:
  - name: "获取Figma文件"
    type: "api_call"
    config:
      api: "figma"
      endpoint: "get_file"
      parameters:
        file_key: "{file_key}"
  
  - name: "分析UI结构"
    type: "processing"
    config:
      algorithm: "ui_analysis"
      output_format: "structured_data"
  
  # ... 更多工作流步骤
```

## 输出格式

### 分析结果结构
```json
{
  "file_info": {
    "name": "设计文件名",
    "lastModified": "最后修改时间",
    "version": "版本号"
  },
  "pages": [
    {
      "id": "页面ID",
      "name": "页面名称",
      "components": [...],
      "layout": {...},
      "styles": {...}
    }
  ],
  "tasks": [
    {
      "title": "任务标题",
      "description": "任务描述",
      "priority": "优先级",
      "estimated_hours": 8.0,
      "dependencies": [...],
      "components": [...]
    }
  ],
  "report": "Markdown格式的分析报告"
}
```

### GitHub Issue格式
每个Issue包含：
- 任务描述和详情
- 优先级和预估工时
- 依赖关系
- 设计参考链接
- 验收标准
- 技术实现指导
- 开发步骤
- 测试用例

## 高级功能

### 1. 自定义任务模板
修改 `DevelopmentTaskGenerator` 类中的 `task_templates` 来定制任务生成规则。

### 2. 组件模式识别
在 `UIAnalyzer` 类中扩展 `component_patterns` 来识别更多组件类型。

### 3. 样式分析增强
扩展 `_analyze_styles` 方法来提取更多样式信息，如：
- 阴影效果
- 渐变填充
- 动画属性
- 响应式断点

### 4. 多文件处理
支持批量处理多个Figma文件：
```python
file_keys = ["key1", "key2", "key3"]
for key in file_keys:
    result = assistant.process_figma_file(key)
    # 处理结果
```

## 故障排除

### 常见问题

#### 1. Figma API访问失败
- 检查 `FIGMA_ACCESS_TOKEN` 是否正确
- 确认token是否过期
- 验证文件访问权限

#### 2. GitHub API错误
- 检查 `GITHUB_TOKEN` 权限
- 确认仓库名称和所有者正确
- 验证token是否有效

#### 3. Webhook接收失败
- 检查网络连接
- 验证webhook URL可访问
- 确认签名验证配置

#### 4. 组件识别不准确
- 检查Figma文件结构
- 确认组件命名规范
- 调整组件模式匹配规则

### 日志调试
设置环境变量 `LOG_LEVEL=DEBUG` 获取详细日志信息。

## 最佳实践

### 1. 设计文件组织
- 使用清晰的页面命名
- 组件命名要规范
- 保持文件结构清晰

### 2. 任务管理
- 定期审查生成的任务
- 调整工时估算
- 优化任务依赖关系

### 3. 团队协作
- 统一Issue标签规范
- 建立代码审查流程
- 保持文档同步更新

### 4. 自动化流程
- 集成CI/CD流程
- 设置自动测试
- 配置部署自动化

## 扩展开发

### 1. 添加新的分析器
继承 `UIAnalyzer` 类并实现自定义分析逻辑。

### 2. 集成其他平台
扩展 `GitHubAPI` 类或创建新的API客户端类。

### 3. 自定义输出格式
修改报告生成逻辑来支持不同的输出格式。

### 4. 添加机器学习
集成ML模型来改进组件识别和任务生成。

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](../LICENSE) 文件。

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件到项目维护者
- 参与项目讨论






