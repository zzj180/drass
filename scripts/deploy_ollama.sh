#!/bin/bash

# Ollama Local LLM Deployment Script for macOS
# This script installs and configures Ollama with recommended models

set -e

echo "========================================"
echo "Ollama Local LLM Deployment Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}This script is designed for macOS. Please use the appropriate script for your OS.${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Install Ollama if not already installed
echo -e "\n${YELLOW}Step 1: Checking Ollama installation...${NC}"
if command_exists ollama; then
    echo -e "${GREEN}✓ Ollama is already installed${NC}"
    ollama version
else
    echo "Installing Ollama..."
    if command_exists brew; then
        brew install ollama
    else
        echo "Installing Ollama from official website..."
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
    echo -e "${GREEN}✓ Ollama installed successfully${NC}"
fi

# Step 2: Start Ollama service
echo -e "\n${YELLOW}Step 2: Starting Ollama service...${NC}"
if pgrep -x "ollama" > /dev/null; then
    echo -e "${GREEN}✓ Ollama service is already running${NC}"
else
    echo "Starting Ollama service in background..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
    echo -e "${GREEN}✓ Ollama service started${NC}"
fi

# Step 3: Pull recommended models
echo -e "\n${YELLOW}Step 3: Pulling recommended models...${NC}"
echo "This may take a while depending on your internet connection..."

# Recommended models for compliance assistant
MODELS=(
    "qwen2.5:7b"           # Main chat model (Chinese + English)
    "llama3.2:3b"          # Lightweight alternative
    "nomic-embed-text"     # Embedding model for RAG
)

for MODEL in "${MODELS[@]}"; do
    echo -e "\nPulling model: ${MODEL}"
    if ollama list | grep -q "$MODEL"; then
        echo -e "${GREEN}✓ Model $MODEL already exists${NC}"
    else
        ollama pull "$MODEL"
        echo -e "${GREEN}✓ Model $MODEL pulled successfully${NC}"
    fi
done

# Step 4: Test model availability
echo -e "\n${YELLOW}Step 4: Testing model availability...${NC}"
echo "Testing qwen2.5:7b model..."
response=$(echo "Hello, can you respond?" | ollama run qwen2.5:7b --verbose 2>/dev/null | head -n 1)
if [[ -n "$response" ]]; then
    echo -e "${GREEN}✓ Model is responding correctly${NC}"
else
    echo -e "${RED}✗ Model test failed${NC}"
fi

# Step 5: Create configuration file
echo -e "\n${YELLOW}Step 5: Creating configuration file...${NC}"
CONFIG_FILE="config/ollama.env"
mkdir -p config

cat > "$CONFIG_FILE" << EOF
# Ollama Local LLM Configuration
# Generated on $(date)

# LLM Provider Settings
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
LLM_API_KEY=not-required
OLLAMA_BASE_URL=http://localhost:11434

# Alternative Models (uncomment to use)
# LLM_MODEL=llama3.2:3b
# LLM_MODEL=mistral:7b

# Model Parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
LLM_TOP_P=0.9
LLM_FREQUENCY_PENALTY=0.0
LLM_PRESENCE_PENALTY=0.0

# Streaming
ENABLE_STREAMING=true

# Embedding Model (for RAG)
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768

# System Settings
OLLAMA_NUM_PARALLEL=2
OLLAMA_MAX_LOADED_MODELS=2
OLLAMA_KEEP_ALIVE=5m
EOF

echo -e "${GREEN}✓ Configuration file created at $CONFIG_FILE${NC}"

# Step 6: Create Docker Compose configuration
echo -e "\n${YELLOW}Step 6: Creating Docker Compose configuration...${NC}"
cat > "docker-compose.ollama.yml" << 'EOF'
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama-service
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_NUM_PARALLEL=2
      - OLLAMA_MAX_LOADED_MODELS=2
      - OLLAMA_KEEP_ALIVE=5m
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G

volumes:
  ollama_data:
    driver: local
EOF

echo -e "${GREEN}✓ Docker Compose configuration created${NC}"

# Step 7: Create Python test script
echo -e "\n${YELLOW}Step 7: Creating test script...${NC}"
cat > "scripts/test_ollama.py" << 'EOF'
#!/usr/bin/env python3
"""Test script for Ollama local LLM integration"""

import os
import sys
import requests
import json
from typing import Dict, Any

def test_ollama_connection() -> bool:
    """Test if Ollama service is accessible"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        return response.status_code == 200
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def test_model_availability(model: str = "qwen2.5:7b") -> bool:
    """Test if specific model is available"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        models = response.json()
        model_names = [m["name"] for m in models.get("models", [])]
        return any(model in name for name in model_names)
    except Exception as e:
        print(f"Model check failed: {e}")
        return False

def test_generation(model: str = "qwen2.5:7b") -> Dict[str, Any]:
    """Test text generation"""
    try:
        payload = {
            "model": model,
            "prompt": "What is compliance management? Answer in one sentence.",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 100
            }
        }
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def test_embedding(model: str = "nomic-embed-text") -> Dict[str, Any]:
    """Test embedding generation"""
    try:
        payload = {
            "model": model,
            "prompt": "Compliance management system"
        }
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json=payload
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def main():
    print("="*50)
    print("Ollama Integration Test Suite")
    print("="*50)
    
    # Test 1: Connection
    print("\n1. Testing Ollama connection...")
    if test_ollama_connection():
        print("✓ Ollama service is running")
    else:
        print("✗ Ollama service is not accessible")
        print("Please run: ollama serve")
        sys.exit(1)
    
    # Test 2: Model availability
    print("\n2. Testing model availability...")
    models = ["qwen2.5:7b", "nomic-embed-text"]
    for model in models:
        if test_model_availability(model):
            print(f"✓ Model {model} is available")
        else:
            print(f"✗ Model {model} not found")
            print(f"Please run: ollama pull {model}")
    
    # Test 3: Generation
    print("\n3. Testing text generation...")
    result = test_generation()
    if "error" not in result:
        print("✓ Text generation successful")
        print(f"Response: {result.get('response', '')[:100]}...")
    else:
        print(f"✗ Generation failed: {result['error']}")
    
    # Test 4: Embedding
    print("\n4. Testing embedding generation...")
    result = test_embedding()
    if "error" not in result and "embedding" in result:
        print("✓ Embedding generation successful")
        print(f"Embedding dimension: {len(result['embedding'])}")
    else:
        print(f"✗ Embedding failed: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*50)
    print("Test suite completed!")

if __name__ == "__main__":
    main()
EOF

chmod +x scripts/test_ollama.py
echo -e "${GREEN}✓ Test script created${NC}"

# Step 8: Display summary
echo -e "\n${GREEN}========================================"
echo "Ollama Setup Complete!"
echo "========================================${NC}"
echo ""
echo "Installed Models:"
for MODEL in "${MODELS[@]}"; do
    echo "  - $MODEL"
done
echo ""
echo "Configuration file: $CONFIG_FILE"
echo "Docker Compose file: docker-compose.ollama.yml"
echo "Test script: scripts/test_ollama.py"
echo ""
echo "To test the installation:"
echo "  python3 scripts/test_ollama.py"
echo ""
echo "To use in your application:"
echo "  source $CONFIG_FILE"
echo ""
echo "API Endpoint: http://localhost:11434"
echo ""
echo -e "${GREEN}✓ Ollama is ready for use!${NC}"