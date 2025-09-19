#!/bin/bash
# Comprehensive test script for all vLLM services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing All vLLM Services${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"

# Function to test service
test_service() {
    local name=$1
    local port=$2
    local endpoint=$3
    local api_key=${4:-"123456"}

    echo -e "\n${BLUE}Testing $name on port $port...${NC}"

    # Check if port is open
    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Port $port is open"
    else
        echo -e "${RED}✗${NC} Port $port is not open"
        return 1
    fi

    # Test health endpoint
    if curl -s -H "Authorization: Bearer $api_key" http://localhost:$port$endpoint >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name endpoint is responding"

        # Show response sample
        echo -e "${BLUE}Response sample:${NC}"
        curl -s -H "Authorization: Bearer $api_key" http://localhost:$port$endpoint 2>/dev/null | head -c 200
        echo
    else
        echo -e "${RED}✗${NC} $name endpoint not responding"
        return 1
    fi

    return 0
}

# Test vLLM LLM Service
echo -e "\n${BLUE}=== 1. vLLM LLM Service (Port 8001) ===${NC}"
test_service "LLM" 8001 "/v1/models" "123456"
LLM_OK=$?

# Test with completion
if [ $LLM_OK -eq 0 ]; then
    echo -e "\n${BLUE}Testing LLM completion...${NC}"

    RESPONSE=$(curl -s -X POST http://localhost:8001/v1/completions \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer 123456" \
        -d '{
            "model": "vllm",
            "prompt": "Hello, world!",
            "max_tokens": 50,
            "temperature": 0.7
        }' 2>/dev/null || echo "{}")

    if echo "$RESPONSE" | grep -q "choices"; then
        echo -e "${GREEN}✓${NC} LLM completion works"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -20
    else
        echo -e "${YELLOW}!${NC} LLM completion test failed"
    fi
fi

# Test vLLM Embedding Service
echo -e "\n${BLUE}=== 2. vLLM Embedding Service (Port 8010) ===${NC}"
test_service "Embedding" 8010 "/v1/models" "123456"
EMBED_OK=$?

# Test embedding generation
if [ $EMBED_OK -eq 0 ]; then
    echo -e "\n${BLUE}Testing embedding generation...${NC}"

    RESPONSE=$(curl -s -X POST http://localhost:8010/v1/embeddings \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer 123456" \
        -d '{
            "model": "Qwen3-Embedding-8B",
            "input": "Test text for embedding"
        }' 2>/dev/null || echo "{}")

    if echo "$RESPONSE" | grep -q "data\|embedding"; then
        echo -e "${GREEN}✓${NC} Embedding generation works"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -20
    else
        echo -e "${YELLOW}!${NC} Embedding generation test failed"
        echo "$RESPONSE" | head -100
    fi
fi

# Test vLLM Reranking Service
echo -e "\n${BLUE}=== 3. vLLM Reranking Service (Port 8012) ===${NC}"
test_service "Reranking" 8012 "/v1/models" "123456"
RERANK_OK=$?

# Test reranking
if [ $RERANK_OK -eq 0 ]; then
    echo -e "\n${BLUE}Testing reranking...${NC}"

    RESPONSE=$(curl -s -X POST http://localhost:8012/v1/rerank \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer 123456" \
        -d '{
            "model": "Qwen3-Reranker-8B",
            "query": "What is the capital of France?",
            "documents": ["Paris is the capital of France", "London is the capital of UK", "Berlin is the capital of Germany"]
        }' 2>/dev/null || echo "{}")

    if echo "$RESPONSE" | grep -q "results\|scores\|data"; then
        echo -e "${GREEN}✓${NC} Reranking works"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -20
    else
        echo -e "${YELLOW}!${NC} Reranking test might not be configured"
        echo -e "Note: Reranking endpoint might use different API format"
    fi
fi

# Test other services
echo -e "\n${BLUE}=== 4. Other Services ===${NC}"

# PostgreSQL
echo -e "\n${BLUE}Testing PostgreSQL...${NC}"
if PGPASSWORD=drass_password psql -U drass_user -h localhost -d drass_production -c "SELECT 1;" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} PostgreSQL is accessible"
else
    echo -e "${RED}✗${NC} PostgreSQL connection failed"
fi

# Redis
echo -e "\n${BLUE}Testing Redis...${NC}"
if redis-cli ping >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is accessible"
else
    echo -e "${RED}✗${NC} Redis connection failed"
fi

# ChromaDB
echo -e "\n${BLUE}Testing ChromaDB...${NC}"
if curl -s http://localhost:8005/api/v1/collections >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} ChromaDB is accessible"
else
    echo -e "${YELLOW}!${NC} ChromaDB API might not be accessible"
fi

# Test Python integration
echo -e "\n${BLUE}=== 5. Python Integration Test ===${NC}"

cat > /tmp/test_integration.py << 'EOF'
#!/usr/bin/env python3
import os
import sys

# Clear proxy
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
    if key in os.environ:
        del os.environ[key]

os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

print("Testing Python integration...")

try:
    # Test OpenAI client with LLM
    from openai import OpenAI

    llm_client = OpenAI(
        api_key="123456",
        base_url="http://localhost:8001/v1"
    )

    models = llm_client.models.list()
    print("✓ LLM client connected")

    # Test embedding client
    embed_client = OpenAI(
        api_key="123456",
        base_url="http://localhost:8010/v1"
    )

    try:
        embedding = embed_client.embeddings.create(
            model="Qwen3-Embedding-8B",
            input="Test text"
        )
        print("✓ Embedding client connected")
    except Exception as e:
        print(f"! Embedding test: {e}")

    # Test LangChain
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    llm = ChatOpenAI(
        api_key="123456",
        base_url="http://localhost:8001/v1",
        model="vllm"
    )
    print("✓ LangChain LLM initialized")

    embeddings = OpenAIEmbeddings(
        api_key="123456",
        base_url="http://localhost:8010/v1",
        model="Qwen3-Embedding-8B"
    )
    print("✓ LangChain Embeddings initialized")

except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

print("\n✓ All Python integrations successful")
EOF

python3 /tmp/test_integration.py || true

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Service Status Summary${NC}"
echo -e "${BLUE}========================================${NC}"

STATUS_OK=true

if [ $LLM_OK -eq 0 ]; then
    echo -e "${GREEN}✓${NC} vLLM LLM Service (8001)"
else
    echo -e "${RED}✗${NC} vLLM LLM Service (8001)"
    STATUS_OK=false
fi

if [ $EMBED_OK -eq 0 ]; then
    echo -e "${GREEN}✓${NC} vLLM Embedding Service (8010)"
else
    echo -e "${RED}✗${NC} vLLM Embedding Service (8010)"
    STATUS_OK=false
fi

if [ $RERANK_OK -eq 0 ]; then
    echo -e "${GREEN}✓${NC} vLLM Reranking Service (8012)"
else
    echo -e "${YELLOW}!${NC} vLLM Reranking Service (8012) - May need configuration"
fi

echo -e "\n${BLUE}Configuration for API:${NC}"
echo "LLM_BASE_URL=http://localhost:8001/v1"
echo "LLM_API_KEY=123456"
echo "LLM_MODEL=vllm"
echo "EMBEDDING_API_BASE=http://localhost:8010/v1"
echo "EMBEDDING_API_KEY=123456"
echo "EMBEDDING_MODEL=Qwen3-Embedding-8B"
echo "RERANKING_API_BASE=http://localhost:8012/v1"
echo "RERANKING_API_KEY=123456"

if [ "$STATUS_OK" = true ]; then
    echo -e "\n${GREEN}✓ All critical services are operational${NC}"
else
    echo -e "\n${RED}✗ Some services need attention${NC}"
fi