# 🎨 Figma UI开发助手

一个智能的Figma设计文件分析工具，能够自动拆解UI页面，生成开发需求backlog，并以GitHub Issue的形式创建开发任务。

## ✨ 主要功能

- 🔍 **智能分析**: 通过Figma API自动分析设计文件结构
- 📄 **页面拆解**: 识别并拆解UI页面和组件
- 📋 **任务生成**: 自动生成开发需求backlog
- 🚀 **GitHub集成**: 自动创建Issues和项目看板
- 🔄 **实时更新**: 支持Webhook实时同步设计变更
- 🖥️ **友好界面**: 提供交互式CLI和Web界面

## 🚀 快速开始

### 1. 环境要求
- Python 3.7+
- Figma账户和API访问权限
- GitHub账户和Personal Access Token

### 2. 一键启动
```bash
# 克隆项目
git clone <your-repo-url>
cd drass

# 运行快速启动脚本
./scripts/quick_start.sh
```

### 3. 手动安装
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp config/figma-assistant.env.example .env
# 编辑 .env 文件，填入API密钥
```

## 📖 使用方法

### 交互式模式（推荐）
```bash
python scripts/figma_cli.py --interactive
```

### 命令行模式
```bash
# 分析Figma文件
python scripts/figma_cli.py --file-key YOUR_FILE_KEY

# 分析并创建GitHub Issues
python scripts/figma_cli.py --file-key YOUR_FILE_KEY --create-issues

# 分析并创建项目看板
python scripts/figma_cli.py --file-key YOUR_FILE_KEY --create-board

# 保存分析结果
python scripts/figma_cli.py --file-key YOUR_FILE_KEY --output result.json
```

### Webhook服务
```bash
# 启动Webhook服务
python scripts/figma_webhook.py

# 服务将在 http://localhost:5000 启动
# 配置Figma Webhook指向 /webhook/figma 端点
```

## ⚙️ 配置说明

### 环境变量
```bash
# Figma API配置
FIGMA_ACCESS_TOKEN=your_figma_access_token

# GitHub API配置
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_username
GITHUB_REPOSITORY=your_repository_name

# Webhook配置（可选）
FIGMA_WEBHOOK_SECRET=your_webhook_secret
```

### 获取API密钥

#### Figma Access Token
1. 登录 [Figma](https://www.figma.com)
2. 进入 Settings > Account > Personal access tokens
3. 点击 "Generate new token"
4. 复制生成的token

#### GitHub Personal Access Token
1. 登录 [GitHub](https://github.com)
2. 进入 Settings > Developer settings > Personal access tokens
3. 点击 "Generate new token (classic)"
4. 选择权限：`repo`, `workflow`

## 🏗️ 项目结构

```
drass/
├── apps/
│   └── figma-assistant.yml          # 应用配置文件
├── config/
│   └── figma-assistant.env.example  # 环境变量模板
├── scripts/
│   ├── figma_assistant.py           # 核心助手脚本
│   ├── figma_cli.py                 # 交互式CLI工具
│   ├── figma_webhook.py             # Webhook服务
│   └── quick_start.sh               # 快速启动脚本
├── templates/
│   └── figma-issue-template.md      # GitHub Issue模板
├── docs/
│   └── FIGMA_ASSISTANT.md           # 详细使用文档
└── requirements.txt                  # Python依赖
```

## 🔧 核心组件

### FigmaAssistant
主要的助手类，负责：
- 加载配置文件
- 管理API客户端
- 协调分析流程
- 生成报告和任务

### UIAnalyzer
UI结构分析器，负责：
- 解析Figma节点结构
- 识别组件和布局
- 提取样式信息
- 分析页面层次

### DevelopmentTaskGenerator
开发任务生成器，负责：
- 根据页面生成任务
- 估算工时
- 识别依赖关系
- 应用任务模板

### GitHubAPI
GitHub集成客户端，负责：
- 创建Issues
- 管理项目看板
- 处理标签和分配

## 📊 输出示例

### 分析报告
```markdown
# Figma设计文件分析报告

## 文件信息
- **文件名**: 用户界面设计
- **最后修改**: 2024-01-15T10:30:00Z
- **版本**: 1.0.0

## 页面分析
共发现 3 个页面：

### 首页
- **页面ID**: 1:2
- **组件数量**: 15
- **布局类型**: VERTICAL
- **主要组件**: Header, Navigation, Hero, Footer

## 开发任务概览
共生成 8 个开发任务：

### 1. 开发首页页面
- **优先级**: high
- **预估工时**: 16.0 小时
- **依赖**: 无
```

### GitHub Issue
每个Issue包含：
- 📋 任务描述和详情
- 🎯 优先级和预估工时
- 🔗 依赖关系
- 📱 设计参考链接
- ✅ 验收标准
- 🛠️ 技术实现指导
- 📝 开发步骤
- 🧪 测试用例

## 🔄 工作流程

1. **获取设计文件**: 通过Figma API获取文件信息
2. **分析UI结构**: 解析页面、组件和布局
3. **生成开发任务**: 基于分析结果创建任务
4. **创建GitHub Issues**: 自动生成开发任务清单
5. **管理项目看板**: 创建项目管理和跟踪

## 🌟 高级功能

### 批量处理
支持同时处理多个Figma文件：
```bash
python scripts/figma_cli.py --interactive
# 选择"批量处理"选项
```

### 自定义模板
可以修改任务生成模板和Issue模板来适应团队需求。

### 实时同步
通过Webhook实现设计变更的实时同步，自动更新开发任务。

### 扩展分析
支持添加自定义的分析器和组件识别规则。

## 🐛 故障排除

### 常见问题

#### API访问失败
- 检查API密钥是否正确
- 确认密钥是否过期
- 验证访问权限

#### 组件识别不准确
- 检查Figma文件结构
- 确认组件命名规范
- 调整识别规则

#### Webhook接收失败
- 检查网络连接
- 验证URL可访问性
- 确认签名配置

### 日志调试
设置环境变量获取详细日志：
```bash
export LOG_LEVEL=DEBUG
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

### 开发环境设置
```bash
# 克隆项目
git clone <your-repo-url>
cd drass

# 创建开发分支
git checkout -b feature/your-feature

# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 提交更改
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature
```

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](../LICENSE) 文件。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件到项目维护者
- 参与项目讨论

## 🙏 致谢

感谢以下开源项目的支持：
- [Figma API](https://www.figma.com/developers/api)
- [GitHub API](https://docs.github.com/en/rest)
- [Rich](https://rich.readthedocs.io/) - 美化终端输出
- [Click](https://click.palletsprojects.com/) - CLI框架

---

🎉 **开始使用Figma助手，让UI开发更高效！**









