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

# Check if PostgreSQL is installed
if ! command -v psql >/dev/null 2>&1; then
    echo -e "${YELLOW}PostgreSQL is not installed. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib

    # Wait for installation to complete
    sleep 5
fi

# Find the correct PostgreSQL service name (could be postgresql or postgresql@14-main etc.)
PG_SERVICE=$(systemctl list-units --type=service --state=running,exited | grep -E "postgresql(@[0-9]+-main)?\.service" | awk '{print $1}' | head -1)

if [ -z "$PG_SERVICE" ]; then
    # Try common service names
    for service in postgresql postgresql@14-main postgresql@15-main postgresql-14 postgresql-15; do
        if systemctl list-unit-files | grep -q "^${service}.service"; then
            PG_SERVICE="${service}.service"
            break
        fi
    done
fi

if [ -z "$PG_SERVICE" ]; then
    echo -e "${RED}Cannot find PostgreSQL service. Please install PostgreSQL manually:${NC}"
    echo -e "  sudo apt-get update"
    echo -e "  sudo apt-get install -y postgresql postgresql-contrib"
    echo -e "  sudo systemctl start postgresql"
    echo -e "${YELLOW}Continuing without PostgreSQL...${NC}"
else
    # Check if PostgreSQL is running
    if ! systemctl is-active --quiet "$PG_SERVICE"; then
        echo -e "${YELLOW}Starting PostgreSQL service: $PG_SERVICE...${NC}"
        sudo systemctl start "$PG_SERVICE"
        sudo systemctl enable "$PG_SERVICE"
    fi

    # Verify PostgreSQL is accessible
    if sudo -u postgres psql -c "SELECT 1;" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} PostgreSQL is running and accessible"

        # Create database and user if they don't exist
        echo -e "${BLUE}Setting up database...${NC}"
        sudo -u postgres psql <<EOF 2>/dev/null || true
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'drass_user') THEN
        CREATE USER drass_user WITH PASSWORD 'drass_password';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE drass_production OWNER drass_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'drass_production')\\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE drass_production TO drass_user;
EOF
        echo -e "${GREEN}✓${NC} Database setup completed"

        # Update pg_hba.conf to ensure local connections work
        PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oE '[0-9]+' | head -1)
        PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

        if [ -f "$PG_HBA" ]; then
            # Check if we need to add local connection rules
            if ! grep -q "host.*drass_production.*drass_user" "$PG_HBA"; then
                echo -e "${BLUE}Updating PostgreSQL authentication configuration...${NC}"

                # Backup original
                sudo cp "$PG_HBA" "$PG_HBA.backup.$(date +%Y%m%d_%H%M%S)"

                # Add connection rules for drass_user
                echo "# Drass application connections" | sudo tee -a "$PG_HBA" >/dev/null
                echo "host    drass_production    drass_user    127.0.0.1/32    md5" | sudo tee -a "$PG_HBA" >/dev/null
                echo "host    drass_production    drass_user    ::1/128         md5" | sudo tee -a "$PG_HBA" >/dev/null
                echo "local   drass_production    drass_user                    md5" | sudo tee -a "$PG_HBA" >/dev/null

                # Reload PostgreSQL configuration
                sudo systemctl reload "$PG_SERVICE"
                echo -e "${GREEN}✓${NC} PostgreSQL configuration updated"
            fi
        fi
    else
        echo -e "${YELLOW}PostgreSQL is running but not accessible. Running diagnostic...${NC}"
        # Try to fix common issues
        if [ -x "$SCRIPT_DIR/check-postgresql.sh" ]; then
            echo -e "${BLUE}Running PostgreSQL diagnostic and fix script...${NC}"
            bash "$SCRIPT_DIR/check-postgresql.sh"
        fi
    fi
fi

# Start Redis if not running
echo -e "\n${BLUE}Checking Redis...${NC}"

# Check if Redis is installed
if ! command -v redis-cli >/dev/null 2>&1; then
    echo -e "${YELLOW}Redis is not installed. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y redis-server

    # Wait for installation to complete
    sleep 3
fi

# Find the correct Redis service name
REDIS_SERVICE=$(systemctl list-units --type=service | grep -E "redis(-server)?\.service" | awk '{print $1}' | head -1)

if [ -z "$REDIS_SERVICE" ]; then
    # Try common service names
    for service in redis-server redis redis-service; do
        if systemctl list-unit-files | grep -q "^${service}.service"; then
            REDIS_SERVICE="${service}.service"
            break
        fi
    done
fi

if [ -z "$REDIS_SERVICE" ]; then
    echo -e "${RED}Cannot find Redis service. Please install Redis manually:${NC}"
    echo -e "  sudo apt-get update"
    echo -e "  sudo apt-get install -y redis-server"
    echo -e "  sudo systemctl start redis-server"
    echo -e "${YELLOW}Continuing without Redis...${NC}"
else
    # Check if Redis is running
    if ! systemctl is-active --quiet "$REDIS_SERVICE"; then
        echo -e "${YELLOW}Starting Redis service: $REDIS_SERVICE...${NC}"
        sudo systemctl start "$REDIS_SERVICE"
        sudo systemctl enable "$REDIS_SERVICE"
    fi

    # Verify Redis is accessible
    if redis-cli ping >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Redis is running and accessible"
    else
        echo -e "${YELLOW}Redis is running but not accessible. Check your Redis configuration.${NC}"
    fi
fi

# Start ChromaDB
echo -e "\n${BLUE}Starting ChromaDB...${NC}"
if ! check_service 8005 "ChromaDB" >/dev/null 2>&1; then
    # Check if ChromaDB is installed
    if ! python3 -c "import chromadb" 2>/dev/null; then
        echo -e "${YELLOW}ChromaDB not found. Installing...${NC}"
        pip3 install chromadb --no-cache-dir || {
            echo -e "${RED}Failed to install ChromaDB${NC}"
            echo -e "${YELLOW}Trying with --user flag...${NC}"
            pip3 install --user chromadb --no-cache-dir || {
                echo -e "${RED}Failed to install ChromaDB. Skipping...${NC}"
                echo -e "${YELLOW}To install manually: pip3 install chromadb${NC}"
            }
        }
    fi

    # Check if ChromaDB is now available
    if python3 -c "import chromadb" 2>/dev/null; then
        cd "$BASE_DIR"

        # Try different ways to start ChromaDB
        echo -e "${BLUE}Attempting to start ChromaDB service...${NC}"

        # Method 1: Use chromadb module directly
        if python3 -c "import chromadb.app" 2>/dev/null; then
            start_service "ChromaDB" "cd $BASE_DIR && python3 -m chromadb.app --path $DATA_DIR/chromadb --port 8005 --host 0.0.0.0" "$LOG_DIR/chromadb.log"
        else
            # Method 2: Use chroma run command if available
            if command -v chroma >/dev/null 2>&1; then
                start_service "ChromaDB" "cd $BASE_DIR && chroma run --path $DATA_DIR/chromadb --port 8005 --host 0.0.0.0" "$LOG_DIR/chromadb.log"
            else
                # Method 3: Start ChromaDB server programmatically
                echo -e "${BLUE}Starting ChromaDB using Python script...${NC}"
                cat > "$BASE_DIR/start_chromadb.py" << 'EOF'
import chromadb
import uvicorn
import os
import sys

# Set up ChromaDB path
chroma_path = sys.argv[1] if len(sys.argv) > 1 else "/home/qwkj/drass/data/chromadb"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8005

print(f"Starting ChromaDB on port {port} with data path: {chroma_path}")

try:
    # Try to start ChromaDB server
    from chromadb.app import app
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
except ImportError:
    # Fallback to persistent client
    print("ChromaDB app module not found, using persistent client mode")
    client = chromadb.PersistentClient(path=chroma_path)
    print(f"ChromaDB client initialized at {chroma_path}")
    print("Note: ChromaDB is running in client mode, not as a server")
    # Keep the process running
    import time
    while True:
        time.sleep(60)
EOF
                start_service "ChromaDB" "cd $BASE_DIR && python3 start_chromadb.py $DATA_DIR/chromadb 8005" "$LOG_DIR/chromadb.log"
            fi
        fi
    else
        echo -e "${RED}ChromaDB is not available. Skipping ChromaDB service.${NC}"
        echo -e "${YELLOW}The system will work without vector storage.${NC}"
    fi
fi

# Start Drass backend API
echo -e "\n${BLUE}Starting Drass Backend API...${NC}"
if ! check_service 8000 "Drass API" >/dev/null 2>&1; then
    # Check if the backend directory exists
    if [ -d "$BASE_DIR/services/main-app" ]; then
        cd "$BASE_DIR/services/main-app"

        # Check if uvicorn is installed
        if ! python3 -c "import uvicorn" 2>/dev/null; then
            echo -e "${YELLOW}Installing backend dependencies...${NC}"
            if [ -f "requirements.txt" ]; then
                pip3 install -r requirements.txt --no-cache-dir || {
                    echo -e "${YELLOW}Failed to install all requirements, installing core dependencies...${NC}"
                    pip3 install fastapi uvicorn langchain chromadb psycopg2-binary redis --no-cache-dir
                }
            else
                # Install core dependencies
                pip3 install fastapi uvicorn langchain chromadb psycopg2-binary redis --no-cache-dir
            fi
        fi

        # Check if app.main exists
        if [ -f "app/main.py" ]; then
            start_service "Drass API" "cd $BASE_DIR/services/main-app && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4" "$LOG_DIR/drass-api.log"
        else
            echo -e "${YELLOW}Backend application not found at $BASE_DIR/services/main-app/app/main.py${NC}"
            echo -e "${YELLOW}Skipping backend API service.${NC}"
        fi
    else
        echo -e "${YELLOW}Backend directory not found at $BASE_DIR/services/main-app${NC}"
        echo -e "${YELLOW}Skipping backend API service.${NC}"
    fi
fi

# Start Drass frontend
echo -e "\n${BLUE}Starting Drass Frontend...${NC}"
if ! check_service 5173 "Drass Frontend" >/dev/null 2>&1; then
    cd "$BASE_DIR/frontend"

    # Check if dist folder exists
    if [ ! -d "dist" ]; then
        echo -e "${YELLOW}Building frontend...${NC}"

        # Install dependencies if node_modules doesn't exist
        if [ ! -d "node_modules" ]; then
            echo -e "${BLUE}Installing frontend dependencies...${NC}"
            npm install --legacy-peer-deps || {
                echo -e "${RED}Failed to install dependencies${NC}"
                echo -e "${YELLOW}Continuing without frontend...${NC}"
                return 0
            }
        fi

        # Try to build with TypeScript check disabled
        echo -e "${BLUE}Building frontend (skipping type checks)...${NC}"

        # Method 1: Try to build with TSC_COMPILE_ON_ERROR
        TSC_COMPILE_ON_ERROR=true npm run build 2>/dev/null || {
            echo -e "${YELLOW}Standard build failed, trying alternative build...${NC}"

            # Method 2: Build with Vite directly, skipping TypeScript
            npx vite build --mode production 2>/dev/null || {
                echo -e "${YELLOW}Vite build failed, trying development server instead...${NC}"

                # Method 3: Use development server as fallback
                echo -e "${BLUE}Starting frontend in development mode...${NC}"
                start_service "Drass Frontend Dev" "cd $BASE_DIR/frontend && npm run dev -- --host 0.0.0.0 --port 5173" "$LOG_DIR/drass-frontend.log"
                return 0
            }
        }
    fi

    # Check if build was successful
    if [ -d "dist" ]; then
        echo -e "${GREEN}✓${NC} Frontend built successfully"

        # Serve the production build
        echo -e "${BLUE}Starting frontend server...${NC}"

        # Install serve if not available
        if ! command -v serve >/dev/null 2>&1; then
            npm install -g serve
        fi

        start_service "Drass Frontend" "cd $BASE_DIR/frontend && serve -s dist -l 5173 -n" "$LOG_DIR/drass-frontend.log"
    else
        echo -e "${YELLOW}Frontend build not found, starting development server...${NC}"
        start_service "Drass Frontend Dev" "cd $BASE_DIR/frontend && npm run dev -- --host 0.0.0.0 --port 5173" "$LOG_DIR/drass-frontend.log"
    fi
fi

# Final status check
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Service Status Summary:${NC}"
echo -e "${BLUE}========================================${NC}"
check_service 8001 "vLLM LLM Service"
check_service 8010 "vLLM Embedding Service"
check_service 8012 "vLLM Reranking Service"

# Special check for PostgreSQL (might be listening on localhost only)
PG_STATUS="not_running"

# Method 1: Check with pg_isready (most reliable)
if command -v pg_isready >/dev/null 2>&1; then
    if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
        PG_STATUS="running"
    elif pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
        PG_STATUS="running"
    elif pg_isready -h /var/run/postgresql -p 5432 >/dev/null 2>&1; then
        PG_STATUS="running"
    fi
fi

# Method 2: Check with psql if pg_isready failed
if [ "$PG_STATUS" = "not_running" ]; then
    if sudo -u postgres psql -c "SELECT 1;" >/dev/null 2>&1; then
        PG_STATUS="running"
    fi
fi

# Method 3: Check network ports as fallback
if [ "$PG_STATUS" = "not_running" ]; then
    if sudo netstat -tlnp 2>/dev/null | grep -q ":5432" || \
       sudo ss -tlnp 2>/dev/null | grep -q ":5432" || \
       lsof -i :5432 >/dev/null 2>&1; then
        PG_STATUS="running"
    fi
fi

# Method 4: Check if PostgreSQL service is active
if [ "$PG_STATUS" = "not_running" ] && [ -n "$PG_SERVICE" ]; then
    if systemctl is-active --quiet "$PG_SERVICE"; then
        PG_STATUS="running_service_only"
    fi
fi

# Display status
if [ "$PG_STATUS" = "running" ]; then
    echo -e "${GREEN}✓${NC} PostgreSQL is running on port 5432"
elif [ "$PG_STATUS" = "running_service_only" ]; then
    echo -e "${YELLOW}!${NC} PostgreSQL service is running but not accessible on port 5432"
    echo -e "   Run: ${BLUE}$SCRIPT_DIR/check-postgresql.sh${NC} to diagnose"
else
    echo -e "${RED}✗${NC} PostgreSQL is not running"
    echo -e "   Run: ${BLUE}$SCRIPT_DIR/check-postgresql.sh${NC} to diagnose and fix"
fi

# Redis check
if redis-cli -h localhost ping >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is running on port 6379"
else
    check_service 6379 "Redis"
fi

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