#!/bin/bash

# LM Studio Local LLM Deployment Script for macOS
# This script configures LM Studio with Qwen2.5-8B model

set -e

echo "========================================"
echo "LM Studio Local LLM Deployment"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LMSTUDIO_PORT=1234
MODEL_NAME="qwen2.5-8b-instruct"
MODEL_VARIANT="Q8_0"  # or Q5_K_M for smaller size

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}This script is designed for macOS. Please use the appropriate script for your OS.${NC}"
    exit 1
fi

# Step 1: Check if LM Studio is installed
echo -e "\n${YELLOW}Step 1: Checking LM Studio installation...${NC}"

if [ -d "/Applications/LM Studio.app" ]; then
    echo -e "${GREEN}✓ LM Studio is installed${NC}"
    LMSTUDIO_VERSION=$(/Applications/LM\ Studio.app/Contents/MacOS/lms --version 2>/dev/null || echo "Version check not available")
    echo "Version: $LMSTUDIO_VERSION"
else
    echo -e "${RED}✗ LM Studio is not installed${NC}"
    echo ""
    echo "Please install LM Studio first:"
    echo "1. Visit https://lmstudio.ai"
    echo "2. Download LM Studio for Mac"
    echo "3. Install the application"
    echo "4. Run this script again"
    exit 1
fi

# Step 2: Create model download script
echo -e "\n${YELLOW}Step 2: Creating model configuration...${NC}"

# Create LM Studio configuration directory
CONFIG_DIR="$HOME/.cache/lm-studio/config"
mkdir -p "$CONFIG_DIR"

# Create model list file
cat > "$CONFIG_DIR/recommended_models.txt" << EOF
# Recommended Models for Compliance Assistant

## Primary Model (8B parameter, bf16 precision)
Qwen/Qwen2.5-8B-Instruct-GGUF
- Variant: qwen2.5-8b-instruct-bf16.gguf
- Size: ~16GB
- RAM Required: 16GB minimum
- Features: Excellent Chinese/English, instruction following

## Alternative Models
Qwen/Qwen2.5-7B-Instruct-GGUF
- Variant: qwen2.5-7b-instruct-q8_0.gguf
- Size: ~8GB
- RAM Required: 12GB minimum

Qwen/Qwen2.5-3B-Instruct-GGUF
- Variant: qwen2.5-3b-instruct-q8_0.gguf
- Size: ~3GB
- RAM Required: 8GB minimum
- Features: Faster, lower resource usage
EOF

echo -e "${GREEN}✓ Model configuration created${NC}"

# Step 3: Create LM Studio server configuration
echo -e "\n${YELLOW}Step 3: Creating server configuration...${NC}"

cat > "$CONFIG_DIR/server_config.json" << EOF
{
  "host": "0.0.0.0",
  "port": $LMSTUDIO_PORT,
  "cors": true,
  "corsOrigin": "*",
  "models": {
    "qwen2.5-8b": {
      "path": "Qwen/Qwen2.5-8B-Instruct-GGUF/qwen2.5-8b-instruct-bf16.gguf",
      "context_length": 32768,
      "gpu_layers": -1,
      "temperature": 0.7,
      "top_p": 0.9,
      "top_k": 40,
      "repeat_penalty": 1.1,
      "threads": 8,
      "batch_size": 512,
      "use_mlock": true,
      "use_mmap": true,
      "rope_freq_base": 1000000,
      "rope_freq_scale": 1.0
    }
  },
  "defaultModel": "qwen2.5-8b"
}
EOF

echo -e "${GREEN}✓ Server configuration created${NC}"

# Step 4: Create start script for LM Studio
echo -e "\n${YELLOW}Step 4: Creating LM Studio start script...${NC}"

cat > "start_lmstudio.sh" << 'EOF'
#!/bin/bash

# Start LM Studio Local Server

echo "Starting LM Studio Server..."

# Configuration
PORT=1234
MODEL="qwen2.5-8b"

# Check if LM Studio is running
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "✓ LM Studio server is already running on port $PORT"
    exit 0
fi

# Instructions for manual start (LM Studio requires GUI interaction)
echo "========================================"
echo "LM Studio Server Setup Instructions"
echo "========================================"
echo ""
echo "1. Open LM Studio application"
echo "   open -a 'LM Studio'"
echo ""
echo "2. Download the model (if not already downloaded):"
echo "   - Go to 'Discover' tab"
echo "   - Search for: Qwen2.5-8B-Instruct-GGUF"
echo "   - Download variant: qwen2.5-8b-instruct-bf16.gguf (16GB)"
echo "   - Alternative smaller: qwen2.5-8b-instruct-q8_0.gguf (8GB)"
echo ""
echo "3. Start the local server:"
echo "   - Go to 'Local Server' tab"
echo "   - Select model: Qwen2.5-8B-Instruct"
echo "   - Configure settings:"
echo "     * Port: 1234"
echo "     * Context Length: 32768"
echo "     * GPU Layers: -1 (use all)"
echo "     * Temperature: 0.7"
echo "   - Click 'Start Server'"
echo ""
echo "4. Verify server is running:"
echo "   curl http://localhost:1234/v1/models"
echo ""
echo "========================================"

# Open LM Studio
echo ""
read -p "Press Enter to open LM Studio..." 
open -a "LM Studio"

echo ""
echo "Follow the instructions above to start the server."
echo "The server will be available at: http://localhost:$PORT"
EOF

chmod +x start_lmstudio.sh
echo -e "${GREEN}✓ Start script created${NC}"

# Step 5: Create test script
echo -e "\n${YELLOW}Step 5: Creating test script...${NC}"

cat > "test_lmstudio.py" << 'EOF'
#!/usr/bin/env python3
"""Test script for LM Studio integration"""

import requests
import json
import sys

LMSTUDIO_URL = "http://localhost:1234"

def test_server_status():
    """Check if LM Studio server is running"""
    try:
        response = requests.get(f"{LMSTUDIO_URL}/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print("✓ LM Studio server is running")
            print(f"Available models: {models}")
            return True
    except requests.exceptions.RequestException as e:
        print(f"✗ LM Studio server is not accessible: {e}")
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
            f"{LMSTUDIO_URL}/v1/chat/completions",
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

def test_embedding():
    """Test embedding generation (if supported)"""
    try:
        payload = {
            "model": "qwen2.5-8b",
            "input": "Data compliance management"
        }
        
        response = requests.post(
            f"{LMSTUDIO_URL}/v1/embeddings",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Embedding generation successful")
            print(f"Embedding dimension: {len(result['data'][0]['embedding'])}")
            return True
        else:
            print(f"⚠ Embeddings may not be supported: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠ Embedding test skipped: {e}")
        return False

def main():
    print("="*50)
    print("LM Studio Integration Test")
    print("="*50)
    
    # Test 1: Server status
    print("\n1. Testing server status...")
    if not test_server_status():
        print("\nPlease start LM Studio server first:")
        print("Run: ./start_lmstudio.sh")
        sys.exit(1)
    
    # Test 2: Chat completion
    print("\n2. Testing chat completion...")
    test_completion()
    
    # Test 3: Embeddings (optional)
    print("\n3. Testing embeddings...")
    test_embedding()
    
    print("\n" + "="*50)
    print("Test completed!")

if __name__ == "__main__":
    main()
EOF

chmod +x test_lmstudio.py
echo -e "${GREEN}✓ Test script created${NC}"

# Step 6: Create environment configuration
echo -e "\n${YELLOW}Step 6: Creating environment configuration...${NC}"

CONFIG_FILE="config/lmstudio.env"
mkdir -p config

cat > "$CONFIG_FILE" << EOF
# LM Studio Local LLM Configuration
# Generated on $(date)

# LLM Provider Settings
LLM_PROVIDER=openai  # LM Studio uses OpenAI-compatible API
LLM_MODEL=qwen2.5-8b
LLM_API_KEY=not-required  # LM Studio doesn't require API key
OPENAI_API_BASE=http://localhost:1234/v1

# Model Parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
LLM_TOP_P=0.9
LLM_FREQUENCY_PENALTY=0.0
LLM_PRESENCE_PENALTY=0.0
LLM_CONTEXT_LENGTH=32768

# Streaming
ENABLE_STREAMING=true

# Model Variants (for reference)
# MODEL_PRECISION=bf16  # Using bfloat16 for better quality
# MODEL_QUANTIZATION=none  # No quantization for bf16 model

# System Settings
LMSTUDIO_PORT=1234
LMSTUDIO_HOST=localhost

# Performance Settings
THREADS=8  # Adjust based on your CPU
GPU_LAYERS=-1  # Use all available GPU layers
BATCH_SIZE=512
USE_MLOCK=true
USE_MMAP=true

# Rope Settings for Qwen2.5
ROPE_FREQ_BASE=1000000
ROPE_FREQ_SCALE=1.0
EOF

echo -e "${GREEN}✓ Configuration file created at $CONFIG_FILE${NC}"

# Step 7: Create Python integration module
echo -e "\n${YELLOW}Step 7: Creating Python integration module...${NC}"

cat > "lmstudio_client.py" << 'EOF'
"""
LM Studio Client for LangChain Integration
Provides OpenAI-compatible interface for LM Studio
"""

import os
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

class LMStudioClient:
    """LM Studio client with OpenAI-compatible interface"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        model: str = "qwen2.5-8b",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """Initialize LM Studio client"""
        self.base_url = base_url
        self.model = model
        
        # Create LangChain ChatOpenAI instance pointing to LM Studio
        self.llm = ChatOpenAI(
            base_url=base_url,
            api_key="not-required",  # LM Studio doesn't need API key
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
    
    def stream_chat(self, messages: List[Dict[str, str]]):
        """Stream chat completion"""
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "system":
                langchain_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
        
        for chunk in self.llm.stream(langchain_messages):
            yield chunk.content
    
    @classmethod
    def from_env(cls):
        """Create client from environment variables"""
        return cls(
            base_url=os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1"),
            model=os.getenv("LLM_MODEL", "qwen2.5-8b"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096"))
        )

# Example usage
if __name__ == "__main__":
    client = LMStudioClient()
    
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

# Step 8: Update main app configuration
echo -e "\n${YELLOW}Step 8: Creating updated backend configuration...${NC}"

cat > "services/main-app/app/core/lmstudio_config.py" << 'EOF'
"""
LM Studio Configuration for LangChain Backend
"""

import os
from typing import Optional
from pydantic import BaseSettings

class LMStudioSettings(BaseSettings):
    """LM Studio configuration settings"""
    
    # Provider settings (use OpenAI-compatible interface)
    llm_provider: str = "openai"
    
    # LM Studio endpoint
    openai_api_base: str = "http://localhost:1234/v1"
    openai_api_key: str = "not-required"  # LM Studio doesn't need API key
    
    # Model settings
    llm_model: str = "qwen2.5-8b"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    llm_top_p: float = 0.9
    llm_context_length: int = 32768
    
    # Streaming
    enable_streaming: bool = True
    
    # Performance settings
    threads: int = 8
    gpu_layers: int = -1  # Use all available
    batch_size: int = 512
    
    class Config:
        env_file = ".env.lmstudio"
        case_sensitive = False

lmstudio_settings = LMStudioSettings()
EOF

echo -e "${GREEN}✓ Backend configuration created${NC}"

# Step 9: Display summary
echo -e "\n${GREEN}========================================"
echo "LM Studio Setup Complete!"
echo "========================================${NC}"
echo ""
echo -e "${BLUE}Model Configuration:${NC}"
echo "  Model: Qwen2.5-8B-Instruct"
echo "  Precision: bfloat16 (bf16)"
echo "  Size: ~16GB"
echo "  Context: 32K tokens"
echo ""
echo -e "${BLUE}Files Created:${NC}"
echo "  Configuration: $CONFIG_FILE"
echo "  Start Script: start_lmstudio.sh"
echo "  Test Script: test_lmstudio.py"
echo "  Python Client: lmstudio_client.py"
echo ""
echo -e "${YELLOW}Setup Instructions:${NC}"
echo ""
echo "1. Install LM Studio (if not installed):"
echo "   Visit https://lmstudio.ai and download for Mac"
echo ""
echo "2. Start LM Studio:"
echo "   ./start_lmstudio.sh"
echo ""
echo "3. Download Model in LM Studio:"
echo "   - Search: Qwen2.5-8B-Instruct-GGUF"
echo "   - Download: qwen2.5-8b-instruct-bf16.gguf"
echo ""
echo "4. Start Server in LM Studio:"
echo "   - Go to 'Local Server' tab"
echo "   - Select the downloaded model"
echo "   - Port: 1234"
echo "   - Click 'Start Server'"
echo ""
echo "5. Test the connection:"
echo "   python3 test_lmstudio.py"
echo ""
echo "6. Use in your application:"
echo "   source $CONFIG_FILE"
echo ""
echo -e "${GREEN}API Endpoint: http://localhost:1234/v1${NC}"
echo -e "${GREEN}OpenAI-Compatible: Yes${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} LM Studio provides better UI control and model management"
echo "compared to Ollama, with full OpenAI API compatibility."