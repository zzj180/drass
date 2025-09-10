# LLM API 配置指南

## 快速开始

### 方案1: OpenRouter（推荐 - 最简单）

OpenRouter 提供统一的API访问多个LLM模型，包括Claude、GPT-4、Llama等。

#### 步骤：

1. **注册账号**
   - 访问 https://openrouter.ai
   - 使用Google账号快速注册
   - 无需等待审核，立即可用

2. **获取API密钥**
   ```
   登录后访问: https://openrouter.ai/keys
   点击 "Create Key" 生成新密钥
   密钥格式: sk-or-v1-xxxxxxxxxxxxxx
   ```

3. **充值额度**
   - 最低充值 $5
   - 支持信用卡、PayPal
   - Claude-3.5-Sonnet: ~$3/百万tokens
   - GPT-4: ~$10/百万tokens

4. **配置.env文件**
   ```bash
   # 编辑 .env 文件
   LLM_PROVIDER=openrouter
   LLM_MODEL=anthropic/claude-3.5-sonnet  # 或其他模型
   OPENROUTER_API_KEY=sk-or-v1-你的密钥
   ```

5. **可用模型列表**
   ```
   anthropic/claude-3.5-sonnet     # 最新最强，推荐
   anthropic/claude-3-opus          # 更强但更贵
   openai/gpt-4-turbo-preview      # GPT-4最新版
   openai/gpt-3.5-turbo            # 便宜快速
   meta-llama/llama-3-70b-instruct # 开源模型
   ```

### 方案2: OpenAI 直接访问

#### 步骤：

1. **注册OpenAI账号**
   - 访问 https://platform.openai.com
   - 需要手机号验证
   - 新用户有$5免费额度

2. **创建API密钥**
   ```
   访问: https://platform.openai.com/api-keys
   点击 "Create new secret key"
   密钥格式: sk-xxxxxxxxxxxxxx
   ```

3. **配置.env文件**
   ```bash
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4-turbo-preview  # 或 gpt-3.5-turbo
   OPENAI_API_KEY=sk-你的密钥
   
   # 同时配置Embedding（可选）
   EMBEDDING_PROVIDER=openai
   EMBEDDING_MODEL=text-embedding-3-small
   EMBEDDING_API_KEY=${OPENAI_API_KEY}  # 复用同一个密钥
   ```

### 方案3: Azure OpenAI（企业推荐）

适合企业用户，需要Azure账号。

#### 步骤：

1. **申请Azure OpenAI服务**
   - 需要Azure订阅
   - 申请访问权限（可能需要等待）

2. **创建资源和部署**
   ```bash
   # Azure Portal中创建OpenAI资源
   # 部署模型（如gpt-4, gpt-35-turbo）
   ```

3. **配置.env文件**
   ```bash
   LLM_PROVIDER=azure_openai
   AZURE_OPENAI_API_KEY=你的密钥
   AZURE_OPENAI_ENDPOINT=https://你的资源名.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=你的部署名
   AZURE_OPENAI_API_VERSION=2024-02-01
   ```

### 方案4: 本地大模型（免费）

多种本地部署方案，适合不同硬件和需求。

#### 方案4.1: MLX-LM Server（Apple Silicon最佳）

专为Apple Silicon优化的MLX模型服务器，提供OpenAI兼容API。

1. **安装MLX-LM**
   ```bash
   # 安装MLX-LM服务器
   pip install mlx-lm
   
   # 或使用部署脚本
   ./scripts/deploy_mlx_server.sh
   ```

2. **使用LM Studio下载的Qwen3-8B-MLX-bf16模型**
   
   如果你已在LM Studio下载了Qwen3-8B-MLX-bf16：
   ```bash
   # 直接使用本地模型启动服务器
   ./scripts/run_qwen3_mlx.sh 8001
   
   # 或手动指定路径
   mlx_lm.server \
     --model ~/.lmstudio/models/Qwen/Qwen3-8B-MLX-bf16 \
     --host 0.0.0.0 \
     --port 8001 \
     --trust-remote-code
   ```

3. **启动服务器（在线模型）**
   ```bash
   # 方式1: 使用Qwen3-8B（会自动下载）
   mlx_lm.server \
     --model Qwen/Qwen2-7B-Instruct \
     --host 0.0.0.0 \
     --port 8001 \
     --trust-remote-code
   
   # 方式2: 使用社区优化版本
   mlx_lm.server \
     --model mlx-community/Qwen2.5-7B-Instruct-4bit \
     --host 0.0.0.0 \
     --port 8001
   ```

4. **可用MLX模型**
   ```
   本地模型（LM Studio下载）：
   - Qwen3-8B-MLX-bf16 (16GB, bfloat16精度，最高质量)
     路径: ~/.lmstudio/models/Qwen/Qwen3-8B-MLX-bf16
   
   在线模型（Hugging Face Hub）：
   - Qwen/Qwen2-7B-Instruct (原版，需转换)
   - mlx-community/Qwen2.5-7B-Instruct-4bit (4.3GB, 推荐)
   - mlx-community/Qwen2.5-3B-Instruct-4bit (1.8GB, 更快)
   - mlx-community/Qwen2.5-14B-Instruct-4bit (8.9GB, 更强)
   ```

5. **配置.env文件**
   ```bash
   # 使用Qwen3-8B-MLX-bf16的配置
   LLM_PROVIDER=openai  # MLX-LM使用OpenAI兼容API
   LLM_MODEL=Qwen3-8B-MLX-bf16
   OPENAI_API_KEY=not-required
   OPENAI_API_BASE=http://localhost:8001/v1
   MODEL_PRECISION=bfloat16
   USE_MLX=true
   
   # 或使用预配置文件
   cp .env.qwen3-mlx .env
   ```

6. **MLX优势**
   ```
   Apple Silicon原生优化：
   - Metal GPU加速：5-10倍速度提升
   - 统一内存架构：高效内存使用
   - bfloat16精度：保持原始模型质量
   - 流式输出：实时响应
   
   Qwen3-8B-MLX-bf16特点：
   - 完整精度：bfloat16保持高质量输出
   - 大上下文：支持32K token上下文
   - 本地运行：无需网络，数据安全
   ```

#### 方案4.2: LM Studio（图形界面）

如果MLX模型在LM Studio中遇到问题，建议使用GGUF格式：

1. **下载GGUF模型**
   在LM Studio搜索：
   - Qwen2.5-7B-Instruct-GGUF (Q4_K_M: 4.9GB)
   - Qwen2.5-3B-Instruct-GGUF (Q4_K_M: 2.0GB)

2. **配置.env**
   ```bash
   LLM_PROVIDER=openai
   LLM_MODEL=local-model
   OPENAI_API_KEY=not-required
   OPENAI_API_BASE=http://localhost:1234/v1
   ```

#### 方案4.3: vLLM（高性能服务器）

适合NVIDIA GPU或需要高吞吐量的场景：

```bash
# 安装vLLM
pip install vllm

# 启动服务器
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --port 8001 \
  --max-model-len 8192

# 配置.env
LLM_PROVIDER=openai
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
OPENAI_API_KEY=not-required
OPENAI_API_BASE=http://localhost:8001/v1
```

#### 方案4.4: Ollama（最简单）

最容易上手，但性能不如专门优化的方案：

```bash
# 安装
brew install ollama

# 启动服务
ollama serve

# 下载模型
ollama pull qwen2.5:7b

# 配置.env
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
```

#### 方案4.5: llama.cpp（轻量级）

CPU友好，支持各种量化格式：

```bash
# 克隆并编译
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# 下载GGUF模型
curl -L "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf" -o qwen2.5-7b.gguf

# 启动服务器
./llama-server -m qwen2.5-7b.gguf -c 8192 --port 8080

# 配置.env
LLM_PROVIDER=openai
LLM_MODEL=local
OPENAI_API_KEY=not-required
OPENAI_API_BASE=http://localhost:8080/v1
```

## Apple Silicon优化建议

### MLX框架优势

对于Apple Silicon Mac用户，强烈推荐使用MLX优化模型：

1. **性能提升**
   - Metal GPU加速：5-10倍速度提升
   - 统一内存架构：高效内存使用
   - 原生bf16支持：保持模型质量

2. **内存效率**
   - 比标准PyTorch减少50%内存
   - 支持更大的上下文窗口
   - 更快的模型加载时间

3. **推荐配置**
   ```bash
   # M1/M2 Mac (8GB/16GB RAM)
   模型: Qwen3-8B-MLX-q8  # 8位量化
   
   # M1 Pro/Max, M2 Pro/Max (16GB+ RAM)  
   模型: Qwen3-8B-MLX-bf16  # 完整精度
   
   # M3系列
   模型: Qwen3-8B-MLX-bf16  # 利用M3增强的ML性能
   ```

## 配置验证

### 测试LLM连接

创建测试脚本 `test_llm.py`：

```python
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_openrouter():
    import requests
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        return
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "anthropic/claude-3.5-sonnet",
            "messages": [{"role": "user", "content": "Say 'API works!'"}],
            "max_tokens": 10
        }
    )
    
    if response.status_code == 200:
        print("✅ OpenRouter API works!")
        print(f"Response: {response.json()['choices'][0]['message']['content']}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_openai():
    from openai import OpenAI
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API works!'"}],
            max_tokens=10
        )
        print("✅ OpenAI API works!")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Error: {e}")

# 根据配置测试相应的API
provider = os.getenv("LLM_PROVIDER", "openrouter")
if provider == "openrouter":
    test_openrouter()
elif provider == "openai":
    test_openai()
```

运行测试：
```bash
# 测试LM Studio + MLX
python test_lmstudio_mlx.py

# 或测试其他提供商
cd services/main-app
source venv/bin/activate
python test_llm.py
```

## 在项目中使用

### 1. LangChain集成已配置

查看 `services/main-app/app/core/config.py`：

```python
class Settings(BaseSettings):
    # LLM配置
    llm_provider: str = "openrouter"
    llm_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # 从环境变量加载
    class Config:
        env_file = ".env"
```

### 2. RAG链中使用

查看 `services/main-app/app/chains/compliance_rag_chain.py`：

```python
def _create_llm(self):
    """创建LLM实例"""
    if self.config.llm_provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=self.config.llm_model,
            openai_api_key=self.config.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            streaming=self.config.enable_streaming
        )
    elif self.config.llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=self.config.llm_model,
            openai_api_key=self.config.openai_api_key,
            streaming=self.config.enable_streaming
        )
```

## 费用估算

### 典型使用场景费用（每1000次对话）

| 模型 | 提供商 | 输入价格 | 输出价格 | 预估费用 |
|------|--------|----------|----------|----------|
| Claude-3.5-Sonnet | OpenRouter | $3/M tokens | $15/M tokens | ~$5-10 |
| GPT-4-Turbo | OpenRouter | $10/M tokens | $30/M tokens | ~$15-25 |
| GPT-3.5-Turbo | OpenAI | $0.5/M tokens | $1.5/M tokens | ~$1-2 |
| Llama-3-70B | OpenRouter | $0.7/M tokens | $0.9/M tokens | ~$1-2 |
| Qwen3-8B-MLX (bf16) | LM Studio | 免费 | 免费 | $0 |
| 本地模型 | Ollama/vLLM | 免费 | 免费 | $0 |

注：M tokens = 百万tokens，1000 tokens ≈ 750个单词

## 常见问题

### 1. API密钥无效
- 检查密钥是否完整复制（包括前缀）
- 确认账户有足够额度
- 检查是否在正确的region（OpenAI）

### 2. 模型不可用
- OpenRouter: 检查模型名称是否正确
- OpenAI: 确认账户有GPT-4权限
- LM Studio: 确认MLX模型已下载（mlx-community/Qwen3-8B-MLX-bf16）
- 本地: 确认模型已下载

### 3. 响应速度慢
- 考虑使用流式响应（streaming=True）
- 选择更快的模型（如GPT-3.5-Turbo）
- 使用本地模型避免网络延迟
- Apple Silicon用户：使用MLX优化模型获得最佳性能
- NVIDIA GPU用户：使用vLLM获得高吞吐量

### 4. 费用控制
- 设置max_tokens限制
- 使用便宜的模型进行开发测试
- 实现缓存机制减少重复调用

## 下一步

配置好LLM API后，可以：
1. 运行 `./quick_start.sh start` 启动服务
2. 访问 http://localhost:8000/docs 测试API
3. 继续配置Embedding服务增强搜索能力