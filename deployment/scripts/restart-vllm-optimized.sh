#!/bin/bash
# Restart vLLM services with optimized settings for better performance
# This addresses high VRAM usage and timeout issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Restarting vLLM Services (Optimized)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
BASE_DIR="/home/qwkj/drass"
LOG_DIR="$BASE_DIR/logs"

mkdir -p "$LOG_DIR"

# 1. Stop existing vLLM services
echo -e "${BLUE}Step 1: Stopping existing vLLM services...${NC}"

# Kill all vLLM processes
pkill -f "vllm" 2>/dev/null || true
pkill -f "DeepSeek" 2>/dev/null || true
pkill -f "Qwen3-Embedding" 2>/dev/null || true
pkill -f "Qwen3-Reranker" 2>/dev/null || true

sleep 3

# Verify all stopped
if pgrep -f "vllm" > /dev/null; then
    echo -e "${YELLOW}Some vLLM processes still running, force killing...${NC}"
    pkill -9 -f "vllm" 2>/dev/null || true
    sleep 2
fi

echo -e "${GREEN}✓${NC} All vLLM services stopped"
echo ""

# 2. Check GPU memory before starting
echo -e "${BLUE}Step 2: Checking GPU status...${NC}"
if command -v rocm-smi >/dev/null 2>&1; then
    rocm-smi | grep -E "Device|^0|^1|^2"
else
    echo -e "${YELLOW}rocm-smi not available${NC}"
fi
echo ""

# 3. Start main LLM service with optimized settings
echo -e "${BLUE}Step 3: Starting main LLM service (optimized)...${NC}"

# Optimized settings for faster response:
# - Reduced max_model_len from 12288 to 4096
# - Reduced gpu_memory_utilization from 0.45 to 0.35
# - Reduced max_num_seqs from 64 to 16
# - Increased dtype to float16 for stability

cat > "$LOG_DIR/start-vllm-main.sh" << 'EOF'
#!/bin/bash
export ROCM_PATH=/opt/rocm
export PYTHONPATH=/home/qwkj/triton/python
export HIP_VISIBLE_DEVICES="0,1"
export PYTORCH_ROCM_ARCH=gfx906

vllm serve "/home/qwkj/.cache/modelscope/hub/models/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B" \
    --port 8001 \
    --dtype float16 \
    --tensor-parallel-size 2 \
    --block-size 16 \
    --max-num-seqs 16 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.35 \
    --api-key 123456 \
    --served-model-name vllm \
    --disable-log-requests \
    --trust-remote-code
EOF

chmod +x "$LOG_DIR/start-vllm-main.sh"

echo "Starting optimized vLLM main service..."
nohup bash "$LOG_DIR/start-vllm-main.sh" > "$LOG_DIR/vllm-llm-optimized.log" 2>&1 &
VLLM_PID=$!
echo "Started vLLM main service (PID: $VLLM_PID)"

# Save PID
echo $VLLM_PID > "$LOG_DIR/vllm-llm.pid"

# Wait for service to start
echo "Waiting for service to initialize..."
sleep 10

# Test if service is responding
if curl -s -X GET "http://localhost:8001/v1/models" \
    -H "Authorization: Bearer 123456" \
    --max-time 5 2>/dev/null | grep -q "vllm"; then
    echo -e "${GREEN}✓${NC} Main LLM service is responding"
else
    echo -e "${YELLOW}⚠${NC} Main LLM service may still be starting"
fi
echo ""

# 4. Start embedding service (keep it lightweight)
echo -e "${BLUE}Step 4: Starting embedding service...${NC}"

cat > "$LOG_DIR/start-vllm-embedding.sh" << 'EOF'
#!/bin/bash
export ROCM_PATH=/opt/rocm
export HIP_VISIBLE_DEVICES="0,1"
export PYTORCH_ROCM_ARCH=gfx906

python -m vllm.entrypoints.openai.api_server \
    --model /home/qwkj/.cache/modelscope/hub/models/Qwen/Qwen3-Embedding-8B \
    --tensor-parallel-size 2 \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.2 \
    --port 8010 \
    --host 0.0.0.0 \
    --served-model-name Qwen3-Embedding-8B \
    --task embed \
    --api-key 123456 \
    --disable-log-requests
EOF

chmod +x "$LOG_DIR/start-vllm-embedding.sh"

nohup bash "$LOG_DIR/start-vllm-embedding.sh" > "$LOG_DIR/vllm-embedding-optimized.log" 2>&1 &
EMBED_PID=$!
echo "Started embedding service (PID: $EMBED_PID)"
echo $EMBED_PID > "$LOG_DIR/vllm-embedding.pid"
echo ""

# 5. Start reranking service (minimal resources)
echo -e "${BLUE}Step 5: Starting reranking service...${NC}"

cat > "$LOG_DIR/start-vllm-reranking.sh" << 'EOF'
#!/bin/bash
export ROCM_PATH=/opt/rocm
export HIP_VISIBLE_DEVICES="0,1"
export PYTORCH_ROCM_ARCH=gfx906

python -m vllm.entrypoints.openai.api_server \
    --model /home/qwkj/Qwen3-Reranker-8B \
    --tensor-parallel-size 2 \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.2 \
    --port 8012 \
    --host 0.0.0.0 \
    --served-model-name Qwen3-Reranker-8B \
    --task embed \
    --api-key 123456 \
    --disable-log-requests
EOF

chmod +x "$LOG_DIR/start-vllm-reranking.sh"

nohup bash "$LOG_DIR/start-vllm-reranking.sh" > "$LOG_DIR/vllm-reranking-optimized.log" 2>&1 &
RERANK_PID=$!
echo "Started reranking service (PID: $RERANK_PID)"
echo $RERANK_PID > "$LOG_DIR/vllm-reranking.pid"
echo ""

# 6. Wait and verify all services
echo -e "${BLUE}Step 6: Verifying services...${NC}"
sleep 10

# Check each service
SERVICES=(
    "8001:Main LLM"
    "8010:Embedding"
    "8012:Reranking"
)

ALL_OK=true
for service_info in "${SERVICES[@]}"; do
    IFS=':' read -r port name <<< "$service_info"
    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name service is running on port $port"
    else
        echo -e "${RED}✗${NC} $name service failed to start on port $port"
        ALL_OK=false
    fi
done
echo ""

# 7. Final GPU status
echo -e "${BLUE}Step 7: Final GPU status...${NC}"
if command -v rocm-smi >/dev/null 2>&1; then
    echo "GPU Memory Usage after restart:"
    rocm-smi | grep -E "VRAM%|^0|^1" | head -3
fi
echo ""

# 8. Test request
if [ "$ALL_OK" = true ]; then
    echo -e "${BLUE}Step 8: Testing with a simple request...${NC}"

    TEST_RESPONSE=$(curl -s -X POST "http://localhost:8001/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer 123456" \
        -d '{
            "model": "vllm",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10,
            "temperature": 0.1
        }' \
        --max-time 30 2>/dev/null || echo "TIMEOUT")

    if echo "$TEST_RESPONSE" | grep -q "choices"; then
        echo -e "${GREEN}✓${NC} Test request successful"
    else
        echo -e "${YELLOW}⚠${NC} Test request failed or timed out"
        echo "Response: $TEST_RESPONSE"
    fi
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}✓ All vLLM services restarted with optimized settings${NC}"
    echo ""
    echo "Optimizations applied:"
    echo "  • Reduced max_model_len to 4096 (was 12288)"
    echo "  • Reduced gpu_memory_utilization to 0.35 (was 0.45)"
    echo "  • Reduced max_num_seqs to 16 (was 64)"
    echo "  • Smaller block_size for better memory management"
    echo ""
    echo "This should significantly improve response times and reduce timeouts."
else
    echo -e "${YELLOW}⚠ Some services failed to start${NC}"
    echo "Check logs for details:"
    echo "  tail -f $LOG_DIR/vllm-llm-optimized.log"
    echo "  tail -f $LOG_DIR/vllm-embedding-optimized.log"
    echo "  tail -f $LOG_DIR/vllm-reranking-optimized.log"
fi
echo -e "${BLUE}========================================${NC}"