#!/bin/bash
# Startup script for Ubuntu AMD GPU deployment
# This script starts all necessary services for Drass on Ubuntu 22.04 with AMD GPUs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="/home/qwkj/drass"
LOG_DIR="$BASE_DIR/logs"
DATA_DIR="$BASE_DIR/data"

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$DATA_DIR/chromadb"
mkdir -p "$DATA_DIR/uploads"

echo -e "${BLUE}Starting Drass services on Ubuntu with AMD GPUs...${NC}"

# Function to check if a service is running
check_service() {
    local port=$1
    local name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running on port $port"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not running on port $port"
        return 1
    fi
}

# Function to start a service
start_service() {
    local name=$1
    local command=$2
    local log_file=$3

    echo -e "${BLUE}Starting $name...${NC}"
    nohup bash -c "$command" > "$log_file" 2>&1 &
    sleep 5
}

# Check existing vLLM services
echo -e "\n${BLUE}Checking existing vLLM services...${NC}"
check_service 8001 "vLLM LLM Service"
check_service 8010 "vLLM Embedding Service"
check_service 8012 "vLLM Reranking Service"

# Start vLLM services if not running
if ! check_service 8001 "vLLM LLM Service" >/dev/null 2>&1; then
    echo -e "${YELLOW}Starting vLLM LLM Service...${NC}"
    start_service "vLLM LLM" "ROCM_PATH=/opt/rocm PYTHONPATH=/home/qwkj/triton/python HIP_VISIBLE_DEVICES='0,1' PYTORCH_ROCM_ARCH=gfx906 vllm serve '/home/qwkj/.cache/modelscope/hub/models/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B' --port 8001 --dtype float16 --tensor-parallel-size 2 --block-size 32 --max-num-seqs 64 --max-model-len 12288 --gpu_memory_utilization=0.45 --api_key 123456 --served-model-name vllm" "$LOG_DIR/vllm-llm.log"
fi

if ! check_service 8010 "vLLM Embedding Service" >/dev/null 2>&1; then
    echo -e "${YELLOW}Starting vLLM Embedding Service...${NC}"
    start_service "vLLM Embedding" "python -m vllm.entrypoints.openai.api_server --model /home/qwkj/.cache/modelscope/hub/models/Qwen/Qwen3-Embedding-8B --tensor-parallel-size 2 --max_model_len=8096 --gpu_memory_utilization=0.3 --port 8010 --host 0.0.0.0 --served_model_name Qwen3-Embedding-8B --task embed --api_key 123456" "$LOG_DIR/vllm-embedding.log"
fi

if ! check_service 8012 "vLLM Reranking Service" >/dev/null 2>&1; then
    echo -e "${YELLOW}Starting vLLM Reranking Service...${NC}"
    start_service "vLLM Reranking" "python -m vllm.entrypoints.openai.api_server --model /home/qwkj/Qwen3-Reranker-8B --tensor-parallel-size 2 --max_model_len=8096 --gpu_memory_utilization=0.3 --port 8012 --host 0.0.0.0 --served_model_name Qwen3-Reranker-8B --task embed --api_key 123456" "$LOG_DIR/vllm-reranking.log"
fi

# Start PostgreSQL if not running
echo -e "\n${BLUE}Checking PostgreSQL...${NC}"
if ! systemctl is-active --quiet postgresql; then
    echo -e "${YELLOW}Starting PostgreSQL...${NC}"
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi
echo -e "${GREEN}✓${NC} PostgreSQL is running"

# Start Redis if not running
echo -e "\n${BLUE}Checking Redis...${NC}"
if ! systemctl is-active --quiet redis-server; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
fi
echo -e "${GREEN}✓${NC} Redis is running"

# Start ChromaDB
echo -e "\n${BLUE}Starting ChromaDB...${NC}"
if ! check_service 8005 "ChromaDB" >/dev/null 2>&1; then
    cd "$BASE_DIR"
    start_service "ChromaDB" "cd $BASE_DIR && python -m chromadb.app --path $DATA_DIR/chromadb --port 8005 --host 0.0.0.0" "$LOG_DIR/chromadb.log"
fi

# Start Drass backend API
echo -e "\n${BLUE}Starting Drass Backend API...${NC}"
if ! check_service 8000 "Drass API" >/dev/null 2>&1; then
    cd "$BASE_DIR/services/main-app"
    start_service "Drass API" "cd $BASE_DIR/services/main-app && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4" "$LOG_DIR/drass-api.log"
fi

# Start Drass frontend
echo -e "\n${BLUE}Starting Drass Frontend...${NC}"
if ! check_service 5173 "Drass Frontend" >/dev/null 2>&1; then
    cd "$BASE_DIR/frontend"
    # Build frontend for production
    if [ ! -d "dist" ]; then
        echo -e "${YELLOW}Building frontend...${NC}"
        npm install
        npm run build
    fi
    # Serve with a simple HTTP server
    start_service "Drass Frontend" "cd $BASE_DIR/frontend && npx serve -s dist -l 5173" "$LOG_DIR/drass-frontend.log"
fi

# Final status check
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Service Status Summary:${NC}"
echo -e "${BLUE}========================================${NC}"
check_service 8001 "vLLM LLM Service"
check_service 8010 "vLLM Embedding Service"
check_service 8012 "vLLM Reranking Service"
check_service 5432 "PostgreSQL"
check_service 6379 "Redis"
check_service 8005 "ChromaDB"
check_service 8000 "Drass API"
check_service 5173 "Drass Frontend"

echo -e "\n${GREEN}All services have been started!${NC}"
echo -e "\nAccess the application at: ${BLUE}http://localhost:5173${NC}"
echo -e "API documentation at: ${BLUE}http://localhost:8000/docs${NC}"
echo -e "\nLogs are available in: ${BLUE}$LOG_DIR${NC}"

# Show how to monitor logs
echo -e "\n${YELLOW}To monitor logs:${NC}"
echo -e "  tail -f $LOG_DIR/drass-api.log"
echo -e "  tail -f $LOG_DIR/vllm-llm.log"
echo -e "  tail -f $LOG_DIR/chromadb.log"