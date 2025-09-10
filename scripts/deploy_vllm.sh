#!/bin/bash

# vLLM Local LLM Deployment Script for macOS/Linux
# This script configures vLLM with Qwen2.5-8B model (bf16 precision)

set -e

echo "========================================"
echo "vLLM Local LLM Deployment"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VLLM_PORT=8001
MODEL_NAME="Qwen/Qwen2.5-8B-Instruct"
MODEL_PRECISION="bfloat16"  # bf16 precision
TENSOR_PARALLEL_SIZE=1  # Number of GPUs to use
MAX_MODEL_LEN=32768  # Context length

# Step 1: Check Python version
echo -e "\n${YELLOW}Step 1: Checking Python version...${NC}"

PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    echo -e "${GREEN}✓ Python $PYTHON_VERSION is installed${NC}"
else
    echo -e "${RED}✗ Python 3.8+ is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

# Step 2: Check CUDA/ROCm availability (for GPU support)
echo -e "\n${YELLOW}Step 2: Checking GPU support...${NC}"

if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    GPU_TYPE="cuda"
elif command -v rocm-smi &> /dev/null; then
    echo -e "${GREEN}✓ AMD GPU detected${NC}"
    rocm-smi --showproductname
    GPU_TYPE="rocm"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}⚠ macOS detected - will use Metal/CPU backend${NC}"
    GPU_TYPE="cpu"
    TENSOR_PARALLEL_SIZE=1
else
    echo -e "${YELLOW}⚠ No GPU detected - will use CPU (slower)${NC}"
    GPU_TYPE="cpu"
    TENSOR_PARALLEL_SIZE=1
fi

# Step 3: Create virtual environment
echo -e "\n${YELLOW}Step 3: Setting up Python virtual environment...${NC}"

VENV_DIR="venv_vllm"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source $VENV_DIR/bin/activate

# Step 4: Install vLLM
echo -e "\n${YELLOW}Step 4: Installing vLLM...${NC}"

# Upgrade pip first
pip install --upgrade pip

# Install vLLM based on platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - use CPU version
    echo "Installing vLLM for macOS (CPU mode)..."
    pip install vllm-cpu
    pip install torch torchvision torchaudio
elif [ "$GPU_TYPE" = "cuda" ]; then
    # NVIDIA GPU
    echo "Installing vLLM with CUDA support..."
    pip install vllm
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
elif [ "$GPU_TYPE" = "rocm" ]; then
    # AMD GPU
    echo "Installing vLLM with ROCm support..."
    pip install vllm
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.6
else
    # CPU only
    echo "Installing vLLM for CPU..."
    pip install vllm-cpu
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install additional dependencies
pip install transformers accelerate sentencepiece protobuf

echo -e "${GREEN}✓ vLLM installed${NC}"

# Step 5: Create model download script
echo -e "\n${YELLOW}Step 5: Creating model download script...${NC}"

cat > "download_model.py" << 'EOF'
#!/usr/bin/env python3
"""Download Qwen2.5-8B model for vLLM"""

import os
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

MODEL_NAME = "Qwen/Qwen2.5-8B-Instruct"
CACHE_DIR = "./models"

print(f"Downloading {MODEL_NAME}...")
print("This will download approximately 16GB of data.")

# Create cache directory
os.makedirs(CACHE_DIR, exist_ok=True)

try:
    # Download tokenizer
    print("Downloading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        cache_dir=CACHE_DIR,
        trust_remote_code=True
    )
    
    # Download model with bf16 precision
    print("Downloading model (bf16 precision)...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        cache_dir=CACHE_DIR,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    
    print(f"✓ Model downloaded successfully to {CACHE_DIR}")
    print(f"Model size: {sum(p.numel() for p in model.parameters()) / 1e9:.2f}B parameters")
    
except Exception as e:
    print(f"✗ Error downloading model: {e}")
    exit(1)
EOF

chmod +x download_model.py
echo -e "${GREEN}✓ Model download script created${NC}"

# Step 6: Create vLLM server configuration
echo -e "\n${YELLOW}Step 6: Creating vLLM server configuration...${NC}"

cat > "vllm_config.yaml" << EOF
# vLLM Server Configuration
model: $MODEL_NAME
host: 0.0.0.0
port: $VLLM_PORT
dtype: $MODEL_PRECISION
max-model-len: $MAX_MODEL_LEN
tensor-parallel-size: $TENSOR_PARALLEL_SIZE

# Performance settings
gpu-memory-utilization: 0.9
max-num-seqs: 256
max-num-batched-tokens: 32768

# Model loading
download-dir: ./models
load-format: auto
trust-remote-code: true

# API settings
served-model-name: qwen2.5-8b
chat-template: null  # Use model's default
response-role: assistant

# Quantization (optional)
quantization: null  # Use bf16 without quantization

# Logging
log-level: INFO
EOF

echo -e "${GREEN}✓ vLLM configuration created${NC}"

# Step 7: Create start script for vLLM
echo -e "\n${YELLOW}Step 7: Creating vLLM start script...${NC}"

cat > "start_vllm.sh" << 'EOF'
#!/bin/bash

# Start vLLM Server

echo "Starting vLLM Server..."

# Configuration
MODEL="Qwen/Qwen2.5-8B-Instruct"
PORT=8001
HOST="0.0.0.0"
MAX_MODEL_LEN=32768
DTYPE="bfloat16"

# Activate virtual environment
source venv_vllm/bin/activate

# Check if model is downloaded
if [ ! -d "./models" ]; then
    echo "Model not found. Downloading..."
    python3 download_model.py
fi

# Start vLLM server with OpenAI-compatible API
echo "Starting vLLM server on port $PORT..."

if [[ "$OSTYPE" == "darwin"* ]] || [ ! -x "$(command -v nvidia-smi)" ]; then
    # CPU mode for macOS or no GPU
    python -m vllm.entrypoints.openai.api_server \
        --model $MODEL \
        --host $HOST \
        --port $PORT \
        --dtype $DTYPE \
        --max-model-len $MAX_MODEL_LEN \
        --device cpu \
        --served-model-name "qwen2.5-8b" \
        --trust-remote-code \
        --download-dir ./models
else
    # GPU mode
    python -m vllm.entrypoints.openai.api_server \
        --model $MODEL \
        --host $HOST \
        --port $PORT \
        --dtype $DTYPE \
        --max-model-len $MAX_MODEL_LEN \
        --gpu-memory-utilization 0.9 \
        --served-model-name "qwen2.5-8b" \
        --trust-remote-code \
        --download-dir ./models \
        --tensor-parallel-size 1
fi
EOF

chmod +x start_vllm.sh
echo -e "${GREEN}✓ Start script created${NC}"

# Step 8: Create test script
echo -e "\n${YELLOW}Step 8: Creating test script...${NC}"

cat > "test_vllm.py" << 'EOF'
#!/usr/bin/env python3
"""Test script for vLLM integration"""

import requests
import json
import sys
import time

VLLM_URL = "http://localhost:8001"

def test_server_status():
    """Check if vLLM server is running"""
    try:
        response = requests.get(f"{VLLM_URL}/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print("✓ vLLM server is running")
            print(f"Available models: {models}")
            return True
    except requests.exceptions.RequestException as e:
        print(f"✗ vLLM server is not accessible: {e}")
        return False
    return False

def test_completion():
    """Test text completion"""
    try:
        payload = {
            "model": "qwen2.5-8b",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is data compliance? Answer in one sentence."}
            ],
            "temperature": 0.7,
            "max_tokens": 100,
            "stream": False
        }
        
        response = requests.post(
            f"{VLLM_URL}/v1/chat/completions",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Chat completion successful")
            print(f"Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"✗ Chat completion failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_streaming():
    """Test streaming completion"""
    try:
        payload = {
            "model": "qwen2.5-8b",
            "messages": [
                {"role": "user", "content": "Count from 1 to 5."}
            ],
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": True
        }
        
        response = requests.post(
            f"{VLLM_URL}/v1/chat/completions",
            json=payload,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✓ Streaming completion successful")
            print("Stream output: ", end="")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data = line_str[6:]
                        if data != "[DONE]":
                            try:
                                chunk = json.loads(data)
                                content = chunk['choices'][0].get('delta', {}).get('content', '')
                                print(content, end="", flush=True)
                            except:
                                pass
            print()
            return True
        else:
            print(f"✗ Streaming failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Streaming test failed: {e}")
        return False

def test_performance():
    """Test performance metrics"""
    try:
        start_time = time.time()
        
        payload = {
            "model": "qwen2.5-8b",
            "messages": [
                {"role": "user", "content": "What is 2+2?"}
            ],
            "temperature": 0.1,
            "max_tokens": 10
        }
        
        response = requests.post(
            f"{VLLM_URL}/v1/chat/completions",
            json=payload,
            timeout=30
        )
        
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            response_time = end_time - start_time
            
            print("✓ Performance test completed")
            print(f"Response time: {response_time:.2f} seconds")
            
            usage = result.get("usage", {})
            if usage:
                print(f"Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"Total tokens: {usage.get('total_tokens', 'N/A')}")
            
            return True
        else:
            print(f"✗ Performance test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Performance test error: {e}")
        return False

def main():
    print("="*50)
    print("vLLM Integration Test")
    print("="*50)
    
    # Test 1: Server status
    print("\n1. Testing server status...")
    if not test_server_status():
        print("\nPlease start vLLM server first:")
        print("Run: ./start_vllm.sh")
        sys.exit(1)
    
    # Test 2: Chat completion
    print("\n2. Testing chat completion...")
    test_completion()
    
    # Test 3: Streaming
    print("\n3. Testing streaming...")
    test_streaming()
    
    # Test 4: Performance
    print("\n4. Testing performance...")
    test_performance()
    
    print("\n" + "="*50)
    print("Test completed!")

if __name__ == "__main__":
    main()
EOF

chmod +x test_vllm.py
echo -e "${GREEN}✓ Test script created${NC}"

# Step 9: Create environment configuration
echo -e "\n${YELLOW}Step 9: Creating environment configuration...${NC}"

CONFIG_FILE="config/vllm.env"
mkdir -p config

cat > "$CONFIG_FILE" << EOF
# vLLM Local LLM Configuration
# Generated on $(date)

# LLM Provider Settings
LLM_PROVIDER=openai  # vLLM uses OpenAI-compatible API
LLM_MODEL=qwen2.5-8b
LLM_API_KEY=not-required  # vLLM doesn't require API key
OPENAI_API_BASE=http://localhost:8001/v1

# Model Parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
LLM_TOP_P=0.9
LLM_FREQUENCY_PENALTY=0.0
LLM_PRESENCE_PENALTY=0.0
LLM_CONTEXT_LENGTH=32768

# Model Precision
MODEL_DTYPE=bfloat16  # bf16 precision for better quality

# vLLM Settings
VLLM_PORT=8001
VLLM_HOST=localhost
VLLM_API_URL=http://localhost:8001/v1

# Performance Settings
TENSOR_PARALLEL_SIZE=$TENSOR_PARALLEL_SIZE
GPU_MEMORY_UTILIZATION=0.9
MAX_NUM_SEQS=256
MAX_NUM_BATCHED_TOKENS=32768

# System Settings
ENABLE_STREAMING=true
TRUST_REMOTE_CODE=true
DOWNLOAD_DIR=./models
EOF

echo -e "${GREEN}✓ Configuration file created at $CONFIG_FILE${NC}"

# Step 10: Create Python integration module
echo -e "\n${YELLOW}Step 10: Creating Python integration module...${NC}"

cat > "vllm_client.py" << 'EOF'
"""
vLLM Client for LangChain Integration
Provides OpenAI-compatible interface for vLLM
"""

import os
from typing import Optional, List, Dict, Any, Generator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import requests
import json

class VLLMClient:
    """vLLM client with OpenAI-compatible interface"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8001/v1",
        model: str = "qwen2.5-8b",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """Initialize vLLM client"""
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Create LangChain ChatOpenAI instance pointing to vLLM
        self.llm = ChatOpenAI(
            base_url=base_url,
            api_key="not-required",  # vLLM doesn't need API key
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True
        )
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat completion request"""
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "system":
                langchain_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
        
        response = self.llm.invoke(langchain_messages)
        return response.content
    
    def stream_chat(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Stream chat completion"""
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "system":
                langchain_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
        
        for chunk in self.llm.stream(langchain_messages):
            yield chunk.content
    
    def raw_completion(self, prompt: str, **kwargs) -> str:
        """Raw completion without chat formatting"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": False
        }
        
        response = requests.post(
            f"{self.base_url}/completions",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["text"]
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")
    
    @classmethod
    def from_env(cls):
        """Create client from environment variables"""
        return cls(
            base_url=os.getenv("VLLM_API_URL", "http://localhost:8001/v1"),
            model=os.getenv("LLM_MODEL", "qwen2.5-8b"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096"))
        )
    
    def health_check(self) -> bool:
        """Check if vLLM server is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False

# Example usage
if __name__ == "__main__":
    client = VLLMClient()
    
    # Check health
    if not client.health_check():
        print("vLLM server is not running. Start it with: ./start_vllm.sh")
        exit(1)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant specializing in data compliance."},
        {"role": "user", "content": "What is GDPR?"}
    ]
    
    # Regular chat
    print("Regular response:")
    response = client.chat(messages)
    print(response)
    
    # Streaming
    print("\nStreaming response:")
    for chunk in client.stream_chat(messages):
        print(chunk, end="", flush=True)
    print()
EOF

echo -e "${GREEN}✓ Python integration module created${NC}"

# Step 11: Display summary
echo -e "\n${GREEN}========================================"
echo "vLLM Setup Complete!"
echo "========================================${NC}"
echo ""
echo -e "${BLUE}Model Configuration:${NC}"
echo "  Model: Qwen2.5-8B-Instruct"
echo "  Precision: bfloat16 (bf16)"
echo "  Size: ~16GB"
echo "  Context: 32K tokens"
echo "  Port: 8001"
echo ""
echo -e "${BLUE}Files Created:${NC}"
echo "  Configuration: $CONFIG_FILE"
echo "  Start Script: start_vllm.sh"
echo "  Test Script: test_vllm.py"
echo "  Python Client: vllm_client.py"
echo "  Model Downloader: download_model.py"
echo ""
echo -e "${YELLOW}Setup Instructions:${NC}"
echo ""
echo "1. Download the model (one-time, ~16GB):"
echo "   source venv_vllm/bin/activate"
echo "   python3 download_model.py"
echo ""
echo "2. Start vLLM server:"
echo "   ./start_vllm.sh"
echo ""
echo "3. Test the connection:"
echo "   python3 test_vllm.py"
echo ""
echo "4. Use in your application:"
echo "   source $CONFIG_FILE"
echo ""
echo -e "${GREEN}API Endpoint: http://localhost:8001/v1${NC}"
echo -e "${GREEN}OpenAI-Compatible: Yes${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} vLLM provides high-performance inference with"
echo "continuous batching and PagedAttention for optimal throughput."

# Step 12: Create quick start script
echo -e "\n${YELLOW}Creating quick start script...${NC}"

cat > "quick_start_vllm.sh" << 'EOF'
#!/bin/bash

echo "Quick Start for vLLM"
echo "===================="

# Check if virtual environment exists
if [ ! -d "venv_vllm" ]; then
    echo "Setting up vLLM environment..."
    ./deploy_vllm.sh
fi

# Activate environment
source venv_vllm/bin/activate

# Check if model is downloaded
if [ ! -d "./models" ]; then
    echo "Downloading model (this may take a while)..."
    python3 download_model.py
fi

# Start vLLM server in background
echo "Starting vLLM server..."
./start_vllm.sh &
VLLM_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 10

# Test the server
echo "Testing vLLM server..."
python3 test_vllm.py

echo ""
echo "vLLM server is running with PID: $VLLM_PID"
echo "To stop: kill $VLLM_PID"
echo "API endpoint: http://localhost:8001/v1"
EOF

chmod +x quick_start_vllm.sh

echo -e "${GREEN}✓ Quick start script created${NC}"
echo ""
echo "Run ${GREEN}./quick_start_vllm.sh${NC} for automated setup and testing!"