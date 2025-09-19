#!/bin/bash
# Test vLLM service connection and performance
# This script helps diagnose vLLM timeout issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing vLLM Service Connection${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
VLLM_URL="http://localhost:8001/v1"
API_KEY="123456"

# 1. Test basic connectivity
echo -e "${BLUE}1. Testing basic connectivity...${NC}"
if nc -zv localhost 8001 2>&1 | grep -q succeeded; then
    echo -e "${GREEN}✓${NC} Port 8001 is open"
else
    echo -e "${RED}✗${NC} Cannot connect to port 8001"
    echo "Please check if vLLM service is running:"
    echo "  ps aux | grep vllm"
    exit 1
fi
echo ""

# 2. Test models endpoint with authentication
echo -e "${BLUE}2. Testing /models endpoint...${NC}"
MODELS_RESPONSE=$(curl -s -X GET "$VLLM_URL/models" \
    -H "Authorization: Bearer $API_KEY" \
    --max-time 10 2>/dev/null || echo "TIMEOUT")

if [ "$MODELS_RESPONSE" = "TIMEOUT" ]; then
    echo -e "${RED}✗${NC} Request timed out"
elif echo "$MODELS_RESPONSE" | grep -q "error"; then
    echo -e "${RED}✗${NC} Error response: $MODELS_RESPONSE"
else
    echo -e "${GREEN}✓${NC} Models endpoint responded"
    echo "Response: $MODELS_RESPONSE"
fi
echo ""

# 3. Test with a minimal request
echo -e "${BLUE}3. Testing minimal chat completion (10 tokens)...${NC}"
START_TIME=$(date +%s)

CHAT_RESPONSE=$(curl -s -X POST "$VLLM_URL/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{
        "model": "vllm",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10,
        "temperature": 0.1
    }' \
    --max-time 60 2>/dev/null || echo "TIMEOUT")

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ "$CHAT_RESPONSE" = "TIMEOUT" ]; then
    echo -e "${RED}✗${NC} Request timed out after 60 seconds"
elif echo "$CHAT_RESPONSE" | grep -q "error"; then
    echo -e "${RED}✗${NC} Error response: $CHAT_RESPONSE"
elif echo "$CHAT_RESPONSE" | grep -q "choices"; then
    echo -e "${GREEN}✓${NC} Chat completion successful (took ${DURATION}s)"
    echo "Response excerpt: $(echo "$CHAT_RESPONSE" | head -c 200)..."
else
    echo -e "${YELLOW}⚠${NC} Unexpected response: $CHAT_RESPONSE"
fi
echo ""

# 4. Test with a medium request
echo -e "${BLUE}4. Testing medium chat completion (100 tokens)...${NC}"
START_TIME=$(date +%s)

CHAT_RESPONSE=$(curl -s -X POST "$VLLM_URL/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{
        "model": "vllm",
        "messages": [{"role": "user", "content": "What is artificial intelligence? Give a brief answer."}],
        "max_tokens": 100,
        "temperature": 0.7
    }' \
    --max-time 120 2>/dev/null || echo "TIMEOUT")

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ "$CHAT_RESPONSE" = "TIMEOUT" ]; then
    echo -e "${RED}✗${NC} Request timed out after 120 seconds"
    echo -e "${YELLOW}This suggests the model is too slow for production use${NC}"
elif echo "$CHAT_RESPONSE" | grep -q "choices"; then
    echo -e "${GREEN}✓${NC} Chat completion successful (took ${DURATION}s)"

    if [ $DURATION -gt 30 ]; then
        echo -e "${YELLOW}⚠ Response took more than 30 seconds - may cause timeouts in production${NC}"
    fi
else
    echo -e "${RED}✗${NC} Failed: $CHAT_RESPONSE"
fi
echo ""

# 5. Check GPU memory status
echo -e "${BLUE}5. Checking GPU status...${NC}"
if command -v rocm-smi >/dev/null 2>&1; then
    echo "GPU Memory Usage:"
    rocm-smi --showmeminfo vram | grep -E "GPU|Vram" || rocm-smi | grep -E "VRAM%|GPU%"
else
    echo -e "${YELLOW}rocm-smi not available${NC}"
fi
echo ""

# 6. Check vLLM process status
echo -e "${BLUE}6. Checking vLLM process status...${NC}"
VLLM_PROCS=$(ps aux | grep -E "vllm|DeepSeek" | grep -v grep | wc -l)
if [ $VLLM_PROCS -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Found $VLLM_PROCS vLLM process(es)"
    echo "Process details:"
    ps aux | grep -E "vllm|DeepSeek" | grep -v grep | awk '{print $1, $2, $9, $10, $11}' | head -3
else
    echo -e "${RED}✗${NC} No vLLM processes found"
fi
echo ""

# 7. Recommendations
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Recommendations:${NC}"
echo ""

if [ $VLLM_PROCS -eq 0 ]; then
    echo "1. Start vLLM service with the correct command"
elif [ "$DURATION" -gt 30 ] 2>/dev/null; then
    echo "1. Consider reducing max_model_len to improve speed:"
    echo "   --max-model-len 4096  (instead of 12288)"
    echo ""
    echo "2. Increase GPU memory utilization if GPU has free memory:"
    echo "   --gpu_memory_utilization=0.8  (instead of 0.45)"
    echo ""
    echo "3. Reduce max_num_seqs for faster processing:"
    echo "   --max-num-seqs 32  (instead of 64)"
fi

# Check if GPU memory is nearly full
if command -v rocm-smi >/dev/null 2>&1; then
    VRAM_USAGE=$(rocm-smi | grep -E "^0|^1" | awk '{print $11}' | sed 's/%//' | head -1)
    if [ "$VRAM_USAGE" -gt 95 ] 2>/dev/null; then
        echo -e "${RED}WARNING: GPU VRAM is at ${VRAM_USAGE}% - this will cause severe slowdowns${NC}"
        echo ""
        echo "To fix high VRAM usage:"
        echo "1. Restart vLLM with lower memory utilization:"
        echo "   --gpu_memory_utilization=0.3"
        echo ""
        echo "2. Or reduce model size:"
        echo "   --max-model-len 4096"
        echo ""
        echo "3. Or stop other GPU processes"
    fi
fi

echo -e "${BLUE}========================================${NC}"