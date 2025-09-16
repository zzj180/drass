# 🚀 Drass一键部署系统

## 快速开始

### 最简单的方法 - 一键部署

```bash
# 给脚本执行权限（只需要第一次）
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

就这么简单！脚本会自动：
- ✅ 检测Python环境
- ✅ 创建虚拟环境
- ✅ 安装所有依赖
- ✅ 检测你的硬件（Mac/GPU/CPU）
- ✅ 推荐最佳配置
- ✅ 启动所有服务

## 使用方式

### 1️⃣ 交互式菜单（推荐新手）

```bash
./deploy.sh
```

显示友好的菜单：
- 🚀 **快速部署** - 自动检测硬件，使用最佳默认配置
- ⚙️ **配置并部署** - 交互式配置向导，自定义所有选项
- 📦 **使用现有配置** - 选择之前保存的配置
- 🔧 **管理部署** - 查看状态、停止服务、查看日志
- 🧹 **清理** - 清除虚拟环境和临时文件

### 2️⃣ 命令行模式（高级用户）

```bash
# 快速部署（自动检测并使用最佳配置）
./deploy.sh quick

# 运行配置向导
./deploy.sh configure

# 使用现有配置部署
./deploy.sh deploy

# 查看服务状态
./deploy.sh status

# 停止所有服务
./deploy.sh stop

# 清理环境
./deploy.sh clean

# 查看帮助
./deploy.sh help
```

## 智能硬件检测

脚本会自动检测你的硬件并推荐最佳配置：

| 硬件类型 | 推荐配置 | 说明 |
|---------|---------|------|
| 🍎 **Apple Silicon** | MLX + Metal | 使用本地Qwen3-8B-MLX模型，Metal加速 |
| 🎮 **NVIDIA GPU** | vLLM + CUDA | 使用vLLM服务器，CUDA加速 |
| 💻 **普通CPU** | Docker + 云API | 容器化部署，使用OpenRouter API |
| ☁️ **云服务器** | Docker Compose | 完整容器化部署方案 |

## 功能特点

### 🎯 零门槛使用
- **无需Python知识** - 自动处理Python环境
- **无需pip命令** - 自动安装所有依赖
- **无需配置文件** - 交互式向导生成配置
- **无需Docker经验** - 自动生成docker-compose.yml

### 🛡️ 安全隔离
- **虚拟环境** - 不影响系统Python
- **依赖隔离** - 所有包安装在项目内
- **配置保护** - 敏感信息使用环境变量

### 🔧 灵活配置
- **多种LLM选择** - OpenRouter、OpenAI、本地MLX、vLLM、Ollama
- **多种部署方式** - AWS、Docker、本地GPU、纯CPU
- **可保存配置** - 一次配置，多次使用

## 常见场景

### 场景1: MacBook Pro开发

```bash
./deploy.sh
# 选择 1 (快速部署)
# 自动检测到Apple Silicon
# 自动配置MLX + Qwen3-8B
# 一键启动所有服务
```

### 场景2: 使用云端API

```bash
./deploy.sh
# 选择 2 (配置并部署)
# 选择 OpenRouter
# 输入API Key
# 完成配置并启动
```

### 场景3: Docker部署

```bash
./deploy.sh
# 选择 1 (快速部署)
# 自动生成docker-compose.yml
# 自动启动所有容器
```

## 目录结构

```
deployment/
├── configs/
│   ├── templates/        # 配置模板
│   ├── presets/          # 预设配置
│   └── user/            # 用户生成的配置
├── scripts/
│   ├── configure.py     # 配置生成器
│   ├── deploy.py        # 部署脚本
│   └── utils/           # 工具函数
└── README.md            # 本文档

.venv-deploy/            # 自动创建的虚拟环境
```

## 故障排除

### Python未安装？
脚本会自动检测并提示安装：
- **macOS**: 使用Homebrew安装
- **Linux**: 使用apt/yum安装
- **Windows**: 请手动安装Python 3.8+

### Docker未安装？
- Docker是可选的，只有选择Docker部署时才需要
- macOS: `brew install docker`
- Linux: 参考[Docker官方文档](https://docs.docker.com/install/)

### 端口被占用？
脚本会自动检测并清理占用的端口

### 配置文件在哪里？
- 用户配置：`deployment/configs/user/`
- 环境变量：`.env.generated`

## 进阶使用

### 自定义预设配置

1. 复制模板：
```bash
cp deployment/configs/templates/docker-compose.yaml \
   deployment/configs/presets/my-preset.yaml
```

2. 编辑配置：
```bash
vi deployment/configs/presets/my-preset.yaml
```

3. 使用预设：
```bash
./deploy.sh
# 选择使用预设配置
# 选择 my-preset
```

### 环境变量配置

生成的`.env.generated`文件包含所有环境变量：
```bash
# 编辑环境变量
vi .env.generated

# 重新部署
./deploy.sh deploy
```

## 支持和帮助

遇到问题？
1. 运行 `./deploy.sh help` 查看帮助
2. 查看日志：`tail -f logs/*.log`
3. 检查服务状态：`./deploy.sh status`
4. 清理重试：`./deploy.sh clean` 然后重新运行

## 许可证

MIT License - 详见LICENSE文件