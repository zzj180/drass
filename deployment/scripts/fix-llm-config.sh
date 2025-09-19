#!/bin/bash
# Fix LLM configuration for the API to use vLLM services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Fixing LLM Configuration for API${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"
API_DIR="$BASE_DIR/services/main-app"

# Check vLLM services
echo -e "\n${BLUE}Checking vLLM services...${NC}"

check_service() {
    local port=$1
    local name=$2
    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running on port $port"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not running on port $port"
        return 1
    fi
}

check_service 8001 "vLLM LLM Service"
LLM_OK=$?
check_service 8010 "vLLM Embedding Service"
EMBED_OK=$?
check_service 8012 "vLLM Reranking Service"
RERANK_OK=$?

if [ $LLM_OK -ne 0 ]; then
    echo -e "${YELLOW}Warning: vLLM LLM service is not running on port 8001${NC}"
    echo -e "Start it with the appropriate vLLM command or run start-ubuntu-services.sh"
fi

# Test vLLM endpoints
echo -e "\n${BLUE}Testing vLLM endpoints...${NC}"

# Test LLM endpoint
echo -e "${BLUE}Testing LLM endpoint (8001)...${NC}"
if curl -s -H "Authorization: Bearer 123456" http://localhost:8001/v1/models | grep -q "model"; then
    echo -e "${GREEN}✓${NC} LLM endpoint is responding"
else
    echo -e "${YELLOW}!${NC} LLM endpoint not responding properly"
fi

# Test Embedding endpoint
echo -e "${BLUE}Testing Embedding endpoint (8010)...${NC}"
if curl -s -H "Authorization: Bearer 123456" http://localhost:8010/v1/models 2>/dev/null | grep -q "model\|Qwen"; then
    echo -e "${GREEN}✓${NC} Embedding endpoint is responding"
else
    echo -e "${YELLOW}!${NC} Embedding endpoint not responding properly"
fi

# Test Reranking endpoint
echo -e "${BLUE}Testing Reranking endpoint (8012)...${NC}"
if curl -s -H "Authorization: Bearer 123456" http://localhost:8012/v1/models 2>/dev/null | grep -q "model\|Qwen"; then
    echo -e "${GREEN}✓${NC} Reranking endpoint is responding"
else
    echo -e "${YELLOW}!${NC} Reranking endpoint not responding properly"
fi

# Create .env file
echo -e "\n${BLUE}Creating .env configuration...${NC}"

cat > "$API_DIR/.env" << 'EOF'
# Environment configuration for vLLM services
APP_NAME="Drass Compliance Assistant"
ENVIRONMENT="production"
DEBUG=false
LOG_LEVEL="INFO"

# Server Configuration
HOST="0.0.0.0"
PORT=8888

# Database
DATABASE_URL="postgresql://drass_user:drass_password@localhost:5432/drass_production"
DB_ECHO=false

# Redis
REDIS_URL="redis://localhost:6379/0"

# Security
SECRET_KEY="drass-secret-key-change-in-production"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS="http://localhost:5173,http://localhost:8888"

# LLM Configuration - Using local vLLM service
LLM_PROVIDER="openai"
LLM_MODEL="vllm"
LLM_API_KEY="123456"
LLM_BASE_URL="http://localhost:8001/v1"
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048

# OpenAI compatibility
OPENAI_API_BASE="http://localhost:8001/v1"
OPENAI_API_KEY="123456"
OPENAI_MODEL="vllm"

# Embedding Configuration - Using vLLM embedding service on port 8010
EMBEDDING_PROVIDER="openai"
EMBEDDING_MODEL="Qwen3-Embedding-8B"
EMBEDDING_API_KEY="123456"
EMBEDDING_API_BASE="http://localhost:8010/v1"
EMBEDDING_DIMENSIONS=1024
EMBEDDING_BATCH_SIZE=100

# Reranking Configuration - Using vLLM reranking service on port 8012
RERANKING_ENABLED=true
RERANKING_PROVIDER="custom"
RERANKING_MODEL="Qwen3-Reranker-8B"
RERANKING_API_KEY="123456"
RERANKING_API_BASE="http://localhost:8012/v1"

# Vector Store
VECTOR_STORE_TYPE="chroma"
CHROMA_HOST="localhost"
CHROMA_PORT=8005
CHROMA_PERSIST_DIRECTORY="/home/qwkj/drass/data/chromadb"

# Disable proxy for local services
NO_PROXY="localhost,127.0.0.1,::1,0.0.0.0"

# Disable telemetry
ANONYMIZED_TELEMETRY=false
DO_NOT_TRACK=true
EOF

echo -e "${GREEN}✓${NC} Created $API_DIR/.env"

# Create a Python script to test the configuration
echo -e "\n${BLUE}Creating test script...${NC}"

cat > "$BASE_DIR/test_llm_config.py" << 'EOF'
#!/usr/bin/env python3
"""Test LLM configuration"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Clear proxy settings
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    if key in os.environ:
        del os.environ[key]

os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'

print("Environment Configuration:")
print(f"  LLM_BASE_URL: {os.getenv('LLM_BASE_URL', 'not set')}")
print(f"  LLM_API_KEY: {os.getenv('LLM_API_KEY', 'not set')}")
print(f"  LLM_MODEL: {os.getenv('LLM_MODEL', 'not set')}")
print(f"  OPENAI_API_BASE: {os.getenv('OPENAI_API_BASE', 'not set')}")

try:
    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY", "123456"),
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:8001/v1")
    )

    print("\n✓ OpenAI client created successfully")

    # Try to list models
    try:
        models = client.models.list()
        print(f"✓ Connected to LLM service")
        for model in models:
            print(f"  Available model: {model.id}")
    except Exception as e:
        print(f"✗ Failed to list models: {e}")

except ImportError:
    print("✗ OpenAI library not installed")
    print("  Install with: pip install openai")

try:
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        api_key=os.getenv("LLM_API_KEY", "123456"),
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:8001/v1"),
        model=os.getenv("LLM_MODEL", "vllm"),
        temperature=0.7
    )

    print("\n✓ LangChain ChatOpenAI created successfully")

    # Try a simple completion
    try:
        response = llm.invoke("Say 'API is working'")
        print(f"✓ LLM response: {response.content[:100]}")
    except Exception as e:
        print(f"! LLM test failed: {e}")

except ImportError:
    print("✗ LangChain not properly installed")
except Exception as e:
    print(f"✗ Error creating LangChain client: {e}")
EOF

chmod +x "$BASE_DIR/test_llm_config.py"
echo -e "${GREEN}✓${NC} Created test script"

# Test the configuration
echo -e "\n${BLUE}Testing configuration...${NC}"
cd "$API_DIR"
python3 "$BASE_DIR/test_llm_config.py" || true

# Create startup wrapper
echo -e "\n${BLUE}Creating API startup wrapper...${NC}"

cat > "$API_DIR/start_api_vllm.sh" << 'EOF'
#!/bin/bash
# Start API with vLLM configuration

# Clear proxy settings
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
export NO_PROXY="localhost,127.0.0.1,::1,0.0.0.0"

# Set LLM configuration
export LLM_PROVIDER="openai"
export LLM_MODEL="vllm"
export LLM_API_KEY="123456"
export LLM_BASE_URL="http://localhost:8001/v1"
export OPENAI_API_BASE="http://localhost:8001/v1"
export OPENAI_API_KEY="123456"
export EMBEDDING_API_BASE="http://localhost:8010/v1"
export EMBEDDING_API_KEY="123456"
export EMBEDDING_MODEL="Qwen3-Embedding-8B"
export RERANKING_API_BASE="http://localhost:8012/v1"
export RERANKING_API_KEY="123456"

# Load .env if exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

echo "Starting API with vLLM configuration..."
echo "  LLM endpoint: $LLM_BASE_URL"
echo "  Model: $LLM_MODEL"

# Start the API
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8888 --workers 1
EOF

chmod +x "$API_DIR/start_api_vllm.sh"
echo -e "${GREEN}✓${NC} Created startup wrapper"

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Configuration Complete${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${GREEN}Next steps:${NC}"
echo -e "1. Restart the API using the wrapper:"
echo -e "   ${BLUE}$API_DIR/start_api_vllm.sh${NC}"
echo -e ""
echo -e "2. Or restart all services:"
echo -e "   ${BLUE}$BASE_DIR/deployment/scripts/start-ubuntu-services.sh${NC}"
echo -e ""
echo -e "3. Check API health:"
echo -e "   ${BLUE}curl http://localhost:8888/health${NC}"