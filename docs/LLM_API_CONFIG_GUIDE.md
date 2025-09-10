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

### 方案4: 本地大模型（免费，Apple Silicon优化）

使用LM Studio部署MLX优化的本地模型服务，专为Apple Silicon Mac优化。

#### LM Studio + MLX方式（推荐 - Apple Silicon最佳性能）：

LM Studio配合MLX优化模型，在Apple Silicon上提供最佳性能。

1. **安装LM Studio**
   ```bash
   # macOS - 从官网下载
   open https://lmstudio.ai
   
   # 验证安装
   ls -la "/Applications/LM Studio.app"
   ```

2. **下载MLX优化模型**
   ```bash
   # 使用部署脚本
   ./scripts/deploy_lmstudio_mlx.sh
   ```
   
   在LM Studio中搜索并下载：
   - **mlx-community/Qwen3-8B-MLX-bf16** (推荐)
   - 大小: ~8GB
   - 精度: bfloat16
   - 优化: Apple Silicon Metal GPU

3. **启动LM Studio服务**
   - 打开LM Studio应用
   - 选择 Qwen3-8B-MLX-bf16 模型
   - 进入 "Local Server" 标签
   - 配置:
     - Port: 1234
     - Context Length: 32768
     - GPU Layers: -1 (使用全部)
   - 点击 "Start Server"

4. **配置.env文件**
   ```bash
   LLM_PROVIDER=openai  # LM Studio使用OpenAI兼容API
   LLM_MODEL=qwen3-8b-mlx-bf16
   LLM_API_KEY=not-required
   LLM_BASE_URL=http://localhost:1234/v1
   MODEL_PRECISION=bfloat16
   USE_MLX=true  # 启用MLX优化
   ```

5. **MLX模型优势**
   ```
   Apple Silicon优化：
   - Metal GPU加速：充分利用M1/M2/M3芯片
   - 内存效率：减少50%内存使用
   - 推理速度：比CPU快5-10倍
   - bf16精度：保持高质量输出
   
   推荐模型：
   - Qwen3-8B-MLX-bf16: 8GB, 最佳质量
   - Qwen3-8B-MLX-q8: 8.5GB, 8位量化
   - Qwen3-8B-MLX-q4: 4.5GB, 更快但质量略低
   ```

#### 其他选项：

**vLLM（高吞吐量服务器）**:
```bash
# 适合NVIDIA GPU或大规模部署
pip install vllm
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-8B-Instruct \
  --port 8001
```

**Ollama（简单但性能较低）**:
```bash
# 安装
brew install ollama  # macOS
# 启动
ollama serve
# 下载模型
ollama pull qwen2.5:7b
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