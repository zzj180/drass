#!/bin/bash

# LM Studio with MLX-Optimized Model Deployment Script for macOS
# This script configures LM Studio with Qwen3-8B-MLX-bf16 model

set -e

echo "========================================"
echo "LM Studio MLX Model Deployment"
echo "Qwen3-8B-MLX-bf16 for Apple Silicon"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LMSTUDIO_PORT=1234
MODEL_NAME="Qwen3-8B-MLX-bf16"
MODEL_REPO="mlx-community/Qwen3-8B-MLX-bf16"
MODEL_SIZE="~8GB"
CONTEXT_LENGTH=32768

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}This script is designed for macOS with Apple Silicon. MLX models require M1/M2/M3 chips.${NC}"
    exit 1
fi

# Check if Apple Silicon
if [[ $(uname -m) != "arm64" ]]; then
    echo -e "${YELLOW}Warning: This appears to be an Intel Mac. MLX models are optimized for Apple Silicon.${NC}"
    echo "Performance may be significantly reduced on Intel Macs."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Check if LM Studio is installed
echo -e "\n${YELLOW}Step 1: Checking LM Studio installation...${NC}"

if [ -d "/Applications/LM Studio.app" ]; then
    echo -e "${GREEN}✓ LM Studio is installed${NC}"
    
    # Try to get version
    if [ -f "/Applications/LM Studio.app/Contents/Info.plist" ]; then
        VERSION=$(defaults read "/Applications/LM Studio.app/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "Unknown")
        echo "Version: $VERSION"
    fi
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

# Step 2: Check MLX availability
echo -e "\n${YELLOW}Step 2: Checking MLX framework...${NC}"

python3 -c "import platform; print(f'Python: {platform.python_version()}')"
python3 -c "import subprocess; result = subprocess.run(['sysctl', '-n', 'hw.optional.arm64'], capture_output=True, text=True); print(f'Apple Silicon: {\"Yes\" if result.stdout.strip() == \"1\" else \"No\"}')"

# Check if MLX is installed (for testing purposes)
if python3 -c "import mlx" 2>/dev/null; then
    echo -e "${GREEN}✓ MLX framework is available${NC}"
else
    echo -e "${YELLOW}⚠ MLX not installed locally (LM Studio has built-in MLX support)${NC}"
fi

# Step 3: Create model configuration
echo -e "\n${YELLOW}Step 3: Creating MLX model configuration...${NC}"

CONFIG_DIR="$HOME/.lmstudio/models"
mkdir -p "$CONFIG_DIR"

cat > "$CONFIG_DIR/mlx_models.json" << EOF
{
  "recommended_models": [
    {
      "name": "Qwen3-8B-MLX-bf16",
      "repo": "mlx-community/Qwen3-8B-MLX-bf16",
      "size": "8GB",
      "precision": "bfloat16",
      "optimized_for": "Apple Silicon (M1/M2/M3)",
      "features": [
        "MLX optimized for Metal GPU",
        "bf16 precision for quality",
        "32K context window",
        "Excellent Chinese/English support",
        "Low memory footprint on Apple Silicon"
      ],
      "requirements": {
        "ram": "16GB recommended",
        "chip": "Apple M1 or newer",
        "storage": "10GB free space"
      }
    },
    {
      "name": "Qwen3-8B-MLX-q8",
      "repo": "mlx-community/Qwen3-8B-MLX-q8",
      "size": "8.5GB",
      "precision": "8-bit quantized",
      "optimized_for": "Apple Silicon with limited RAM"
    },
    {
      "name": "Qwen3-8B-MLX-q4",
      "repo": "mlx-community/Qwen3-8B-MLX-q4",
      "size": "4.5GB",
      "precision": "4-bit quantized",
      "optimized_for": "Fast inference, lower quality"
    }
  ]
}
EOF

echo -e "${GREEN}✓ MLX model configuration created${NC}"

# Step 4: Create LM Studio server configuration
echo -e "\n${YELLOW}Step 4: Creating server configuration for MLX model...${NC}"

cat > "lmstudio_mlx_config.json" << EOF
{
  "server": {
    "host": "0.0.0.0",
    "port": $LMSTUDIO_PORT,
    "cors": true,
    "corsOrigin": "*"
  },
  "model": {
    "name": "$MODEL_NAME",
    "repo": "$MODEL_REPO",
    "context_length": $CONTEXT_LENGTH,
    "gpu_layers": -1,
    "use_metal": true,
    "mlx_config": {
      "use_mlx": true,
      "precision": "bfloat16",
      "metal_device": "default",
      "max_batch_size": 8,
      "use_cache": true
    }
  },
  "inference": {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "max_tokens": 4096,
    "seed": -1
  },
  "performance": {
    "threads": 0,
    "batch_size": 512,
    "use_mlock": false,
    "use_mmap": true,
    "offload_kqv": true
  }
}
EOF

echo -e "${GREEN}✓ Server configuration created${NC}"

# Step 5: Create start script for LM Studio with MLX
echo -e "\n${YELLOW}Step 5: Creating LM Studio MLX start script...${NC}"

cat > "start_lmstudio_mlx.sh" << 'EOF'
#!/bin/bash

# Start LM Studio with MLX Model

echo "Starting LM Studio with MLX-optimized model..."

# Configuration
PORT=1234
MODEL="Qwen3-8B-MLX-bf16"
MODEL_REPO="mlx-community/Qwen3-8B-MLX-bf16"

# Check if LM Studio is running
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "✓ LM Studio server is already running on port $PORT"
    exit 0
fi

# Instructions for manual start
echo "========================================"
echo "LM Studio MLX Model Setup Instructions"
echo "========================================"
echo ""
echo "1. Open LM Studio application:"
echo "   open -a 'LM Studio'"
echo ""
echo "2. Download the MLX-optimized model:"
echo "   - Go to 'Discover' tab"
echo "   - Search for: mlx-community/Qwen3-8B-MLX-bf16"
echo "   - OR search: Qwen3-8B-MLX"
echo "   - Download the bf16 variant (~8GB)"
echo ""
echo "3. Configure for MLX/Metal acceleration:"
echo "   - Go to 'Settings' > 'Advanced'"
echo "   - Enable 'Use Metal' (should be on by default)"
echo "   - Set 'GPU Layers' to -1 (use all)"
echo ""
echo "4. Start the local server:"
echo "   - Go to 'Local Server' tab"
echo "   - Select model: Qwen3-8B-MLX-bf16"
echo "   - Configure settings:"
echo "     * Port: 1234"
echo "     * Context Length: 32768"
echo "     * GPU Layers: -1 (all)"
echo "     * Temperature: 0.7"
echo "   - Click 'Start Server'"
echo ""
echo "5. Verify MLX acceleration:"
echo "   - Check server logs for 'MLX' or 'Metal' mentions"
echo "   - Monitor GPU usage in Activity Monitor"
echo ""
echo "========================================"

# Open LM Studio
echo ""
read -p "Press Enter to open LM Studio..." 
open -a "LM Studio"

echo ""
echo "Follow the instructions above to set up the MLX model."
echo "The server will be available at: http://localhost:$PORT"
echo ""
echo "Note: MLX models provide optimal performance on Apple Silicon"
echo "with significantly reduced memory usage compared to standard models."
EOF

chmod +x start_lmstudio_mlx.sh
echo -e "${GREEN}✓ Start script created${NC}"

# Step 6: Create test script for MLX model
echo -e "\n${YELLOW}Step 6: Creating MLX model test script...${NC}"

cat > "test_lmstudio_mlx.py" << 'EOF'
#!/usr/bin/env python3
"""Test script for LM Studio with MLX-optimized model"""

import requests
import json
import sys
import time
import platform
import subprocess

LMSTUDIO_URL = "http://localhost:1234"

def check_system():
    """Check if system is Apple Silicon"""
    print("System Information:")
    print(f"  Platform: {platform.platform()}")
    print(f"  Processor: {platform.processor()}")
    print(f"  Architecture: {platform.machine()}")
    
    # Check for Apple Silicon
    try:
        result = subprocess.run(['sysctl', '-n', 'hw.optional.arm64'], 
                              capture_output=True, text=True)
        is_apple_silicon = result.stdout.strip() == "1"
        if is_apple_silicon:
            print("  ✓ Apple Silicon detected (MLX optimized)")
        else:
            print("  ⚠ Intel Mac detected (MLX not optimized)")
    except:
        print("  ⚠ Could not determine processor type")
    
    print()

def test_server_status():
    """Check if LM Studio server is running"""
    try:
        response = requests.get(f"{LMSTUDIO_URL}/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print("✓ LM Studio server is running")
            print(f"Available models: {models}")
            
            # Check for MLX model
            model_ids = [m.get('id', '') for m in models.get('data', [])]
            mlx_models = [m for m in model_ids if 'mlx' in m.lower() or 'qwen3' in m.lower()]
            if mlx_models:
                print(f"✓ MLX model detected: {mlx_models}")
            else:
                print("⚠ No MLX model found. Please load Qwen3-8B-MLX-bf16")
            
            return True
    except requests.exceptions.RequestException as e:
        print(f"✗ LM Studio server is not accessible: {e}")
        return False
    return False

def test_completion():
    """Test text completion with MLX model"""
    try:
        payload = {
            "model": "qwen3-8b-mlx-bf16",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What are the benefits of MLX framework for LLMs? Answer briefly."}
            ],
            "temperature": 0.7,
            "max_tokens": 150,
            "stream": False
        }
        
        start_time = time.time()
        response = requests.post(
            f"{LMSTUDIO_URL}/v1/chat/completions",
            json=payload,
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Chat completion successful")
            print(f"Response time: {end_time - start_time:.2f}s")
            print(f"Response: {result['choices'][0]['message']['content']}")
            
            # Check for MLX-specific performance
            if (end_time - start_time) < 2.0:
                print("✓ Excellent MLX performance (<2s response)")
            
            return True
        else:
            print(f"✗ Chat completion failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_streaming():
    """Test streaming with MLX model"""
    try:
        payload = {
            "model": "qwen3-8b-mlx-bf16",
            "messages": [
                {"role": "user", "content": "Count from 1 to 5."}
            ],
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": True
        }
        
        response = requests.post(
            f"{LMSTUDIO_URL}/v1/chat/completions",
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
    """Test MLX model performance"""
    try:
        test_prompts = [
            ("Short", "Hi", 10),
            ("Medium", "Explain quantum computing in simple terms.", 100),
            ("Long", "Write a detailed analysis of data privacy regulations.", 200)
        ]
        
        print("\nPerformance Test Results:")
        print("-" * 50)
        
        total_tokens = 0
        total_time = 0
        
        for name, prompt, max_tokens in test_prompts:
            payload = {
                "model": "qwen3-8b-mlx-bf16",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": max_tokens
            }
            
            start = time.time()
            response = requests.post(f"{LMSTUDIO_URL}/v1/chat/completions", json=payload)
            end = time.time()
            
            if response.status_code == 200:
                result = response.json()
                usage = result.get("usage", {})
                response_time = end - start
                tokens = usage.get("completion_tokens", 0)
                tokens_per_sec = tokens / response_time if response_time > 0 else 0
                
                print(f"{name:10} | Time: {response_time:.2f}s | Tokens: {tokens:3} | Speed: {tokens_per_sec:.1f} tok/s")
                
                total_tokens += tokens
                total_time += response_time
        
        avg_speed = total_tokens / total_time if total_time > 0 else 0
        print("-" * 50)
        print(f"Average: {avg_speed:.1f} tokens/second")
        
        if avg_speed > 30:
            print("✓ Excellent MLX performance!")
        elif avg_speed > 15:
            print("✓ Good MLX performance")
        else:
            print("⚠ Performance could be improved")
        
        return True
        
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False

def main():
    print("="*50)
    print("LM Studio MLX Model Integration Test")
    print("Model: Qwen3-8B-MLX-bf16")
    print("="*50)
    print()
    
    # Check system
    check_system()
    
    # Test 1: Server status
    print("1. Testing server status...")
    if not test_server_status():
        print("\nPlease start LM Studio server first:")
        print("Run: ./start_lmstudio_mlx.sh")
        sys.exit(1)
    
    # Test 2: Chat completion
    print("\n2. Testing chat completion...")
    test_completion()
    
    # Test 3: Streaming
    print("\n3. Testing streaming...")
    test_streaming()
    
    # Test 4: Performance
    print("\n4. Testing MLX performance...")
    test_performance()
    
    print("\n" + "="*50)
    print("MLX Model Test Complete!")
    print("="*50)
    print("\nMLX Optimization Benefits:")
    print("• Optimized for Apple Silicon Metal GPU")
    print("• Reduced memory footprint")
    print("• Faster inference on M1/M2/M3 chips")
    print("• Native bf16 precision support")

if __name__ == "__main__":
    main()
EOF

chmod +x test_lmstudio_mlx.py
echo -e "${GREEN}✓ Test script created${NC}"

# Step 7: Create environment configuration
echo -e "\n${YELLOW}Step 7: Creating MLX environment configuration...${NC}"

CONFIG_FILE="config/lmstudio_mlx.env"
mkdir -p config

cat > "$CONFIG_FILE" << EOF
# LM Studio MLX Model Configuration
# Qwen3-8B-MLX-bf16 for Apple Silicon
# Generated on $(date)

# LLM Provider Settings
LLM_PROVIDER=openai  # LM Studio uses OpenAI-compatible API
LLM_MODEL=qwen3-8b-mlx-bf16
LLM_API_KEY=not-required  # LM Studio doesn't require API key
OPENAI_API_BASE=http://localhost:1234/v1
LLM_BASE_URL=http://localhost:1234/v1

# Model Parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
LLM_TOP_P=0.9
LLM_FREQUENCY_PENALTY=0.0
LLM_PRESENCE_PENALTY=0.0
LLM_CONTEXT_LENGTH=32768

# MLX Specific Settings
USE_MLX=true
MODEL_PRECISION=bfloat16
USE_METAL=true
METAL_DEVICE=default

# Streaming
ENABLE_STREAMING=true

# System Settings
LMSTUDIO_PORT=1234
LMSTUDIO_HOST=localhost

# Performance Settings (MLX Optimized)
GPU_LAYERS=-1  # Use all Metal GPU layers
BATCH_SIZE=512
USE_MLOCK=false  # Not needed with MLX
USE_MMAP=true
OFFLOAD_KQV=true  # Offload key-query-value to GPU

# Apple Silicon Optimization
MAX_BATCH_SIZE=8
USE_CACHE=true
METAL_THREADS=0  # Auto-detect
EOF

echo -e "${GREEN}✓ Configuration file created at $CONFIG_FILE${NC}"

# Step 8: Display summary
echo -e "\n${GREEN}========================================"
echo "LM Studio MLX Setup Complete!"
echo "========================================${NC}"
echo ""
echo -e "${BLUE}Model Configuration:${NC}"
echo "  Model: Qwen3-8B-MLX-bf16"
echo "  Framework: MLX (Metal Performance)"
echo "  Precision: bfloat16"
echo "  Size: ~8GB"
echo "  Context: 32K tokens"
echo "  Optimized for: Apple Silicon (M1/M2/M3)"
echo ""
echo -e "${BLUE}Files Created:${NC}"
echo "  Configuration: $CONFIG_FILE"
echo "  Start Script: start_lmstudio_mlx.sh"
echo "  Test Script: test_lmstudio_mlx.py"
echo "  Server Config: lmstudio_mlx_config.json"
echo ""
echo -e "${YELLOW}Setup Instructions:${NC}"
echo ""
echo "1. Open LM Studio:"
echo "   ./start_lmstudio_mlx.sh"
echo ""
echo "2. Download MLX Model in LM Studio:"
echo "   - Search: mlx-community/Qwen3-8B-MLX-bf16"
echo "   - Download: bf16 variant (~8GB)"
echo ""
echo "3. Start Server in LM Studio:"
echo "   - Select Qwen3-8B-MLX-bf16"
echo "   - Port: 1234"
echo "   - Enable Metal/MLX acceleration"
echo "   - Click 'Start Server'"
echo ""
echo "4. Test the connection:"
echo "   python3 test_lmstudio_mlx.py"
echo ""
echo -e "${GREEN}API Endpoint: http://localhost:1234/v1${NC}"
echo -e "${GREEN}OpenAI-Compatible: Yes${NC}"
echo -e "${GREEN}MLX Optimized: Yes (Apple Silicon)${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} MLX models provide optimal performance on Apple Silicon"
echo "with native Metal GPU acceleration and reduced memory usage."