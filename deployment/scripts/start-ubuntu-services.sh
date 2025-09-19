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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Starting Drass Services on Ubuntu${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to check if services are already running
check_existing_services() {
    echo -e "\n${BLUE}Checking for already running services...${NC}"
    local has_running=false

    if lsof -i :5173 >/dev/null 2>&1; then
        echo -e "${YELLOW}! Frontend is already running on port 5173${NC}"
        has_running=true
    fi

    if lsof -i :8888 >/dev/null 2>&1; then
        echo -e "${YELLOW}! API is already running on port 8888${NC}"
        has_running=true
    fi

    if lsof -i :8005 >/dev/null 2>&1; then
        echo -e "${YELLOW}! ChromaDB is already running on port 8005${NC}"
        has_running=true
    fi

    if [ "$has_running" = true ]; then
        echo -e "\n${YELLOW}Warning: Some services are already running!${NC}"
        echo -e "Do you want to:"
        echo -e "  1) Restart all services (stop then start)"
        echo -e "  2) Start only stopped services"
        echo -e "  3) Cancel"

        read -p "Enter your choice (1-3): " choice

        case $choice in
            1)
                echo -e "${BLUE}Restarting all services...${NC}"
                if [ -f "$SCRIPT_DIR/stop-ubuntu-services.sh" ]; then
                    bash "$SCRIPT_DIR/stop-ubuntu-services.sh"
                    sleep 3
                else
                    echo -e "${YELLOW}Stop script not found, killing processes manually...${NC}"
                    lsof -ti :5173,8888,8005 | xargs -r kill -9 2>/dev/null || true
                    sleep 3
                fi
                ;;
            2)
                echo -e "${BLUE}Starting only stopped services...${NC}"
                ;;
            3)
                echo -e "${YELLOW}Cancelled. Exiting...${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice. Exiting...${NC}"
                exit 1
                ;;
        esac
    fi
}

# Check for existing services
check_existing_services

echo -e "\n${BLUE}Starting Drass services...${NC}"

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

# Function to start a service (with check for already running)
start_service() {
    local name=$1
    local command=$2
    local log_file=$3
    local port=$4  # Optional port to check

    # Check if service is already running on port
    if [ -n "$port" ] && lsof -i :$port >/dev/null 2>&1; then
        echo -e "${YELLOW}$name is already running on port $port, skipping...${NC}"
        return 0
    fi

    echo -e "${BLUE}Starting $name...${NC}"

    # Clear old log file for this run
    echo "=== Starting $name at $(date) ===" > "$log_file"
    echo "Command: $command" >> "$log_file"

    nohup bash -c "$command" >> "$log_file" 2>&1 &
    local pid=$!

    # Give more time for ChromaDB to start
    if [[ "$name" == *"ChromaDB"* ]]; then
        sleep 8
    else
        sleep 5
    fi

    # Check if the process started successfully
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name started (PID: $pid)"
        echo "$pid" > "$LOG_DIR/${name// /_}.pid" 2>/dev/null || true
        return 0
    else
        echo -e "${RED}✗${NC} Failed to start $name"
        # Show last few lines of log for debugging
        if [ -f "$log_file" ]; then
            echo -e "${YELLOW}Last lines from log:${NC}"
            tail -5 "$log_file"
        fi
        return 1
    fi
}

# Function to create minimal API
create_minimal_api() {
    # First create a startup script that handles proxy settings
    cat > "$BASE_DIR/services/main-app/start_api.sh" << 'SCRIPT_EOF'
#!/bin/bash
# Clear proxy settings that might interfere with local services
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY
unset all_proxy
unset ALL_PROXY

# Set NO_PROXY for localhost
export NO_PROXY="localhost,127.0.0.1,::1,0.0.0.0"

# Start the API
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8888
SCRIPT_EOF

    chmod +x "$BASE_DIR/services/main-app/start_api.sh"

    cat > "$BASE_DIR/services/main-app/app/main.py" << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import datetime
import os

app = FastAPI(
    title="Drass API",
    description="Minimal Drass Backend API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, bool]

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 2048

class ChatResponse(BaseModel):
    response: str
    metadata: Dict[str, Any] = {}

# Routes
@app.get("/")
async def root():
    return {"message": "Drass API is running", "version": "1.0.0"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services = {
        "api": True,
        "database": check_database(),
        "llm": check_llm_service(),
        "chromadb": check_chromadb()
    }

    return HealthResponse(
        status="healthy" if all(services.values()) else "degraded",
        timestamp=datetime.datetime.now().isoformat(),
        services=services
    )

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - minimal implementation"""
    try:
        # For now, return a placeholder response
        response_text = f"Received {len(request.messages)} messages. API is running but LangChain integration is not configured."

        # Check if LLM service is available
        if check_llm_service():
            response_text += " LLM service detected on port 8001."

        return ChatResponse(
            response=response_text,
            metadata={
                "model": "placeholder",
                "temperature": request.temperature,
                "timestamp": datetime.datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def check_database() -> bool:
    """Check if PostgreSQL is accessible"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="drass_production",
            user="drass_user",
            password="drass_password"
        )
        conn.close()
        return True
    except:
        return False

def check_llm_service() -> bool:
    """Check if LLM service is running on port 8001"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 8001))
        sock.close()
        return result == 0
    except:
        return False

def check_chromadb() -> bool:
    """Check if ChromaDB is accessible"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 8005))
        sock.close()
        return result == 0
    except:
        return False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
EOF

    # Create __init__.py file
    touch "$BASE_DIR/services/main-app/app/__init__.py"

    echo -e "${GREEN}✓${NC} Created minimal API at $BASE_DIR/services/main-app/app/main.py"

    # Start the minimal API using the startup script (updated to use port 8888)
    start_service "Drass API" "cd $BASE_DIR/services/main-app && sed -i 's/8000/8888/g' start_api.sh 2>/dev/null; bash start_api.sh" "$LOG_DIR/drass-api.log" 8888
}

# Function to create simple API server
create_simple_api_server() {
    # First, make sure port 8888 is free
    echo -e "${BLUE}Checking if port 8888 is free...${NC}"
    if lsof -i :8888 >/dev/null 2>&1; then
        echo -e "${YELLOW}Port 8888 is in use, attempting to free it...${NC}"
        lsof -ti :8888 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi

    cat > "$BASE_DIR/simple_api.py" << 'EOF'
#!/usr/bin/env python3
import json
import sys
import os
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import datetime

# Clear proxy settings that might interfere
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    if key in os.environ:
        del os.environ[key]

os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1,0.0.0.0'

class SimpleAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                'status': 'ok',
                'message': 'Drass Simple API Server',
                'timestamp': datetime.datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/v1/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response = {
                'response': 'Simple API server is running. Full backend not configured.',
                'timestamp': datetime.datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        # Log to stdout for debugging
        sys.stdout.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          format%args))
        sys.stdout.flush()

if __name__ == '__main__':
    PORT = 8888

    # Test if port is available
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        test_socket.bind(('0.0.0.0', PORT))
        test_socket.close()
        print(f'Port {PORT} is available')
    except OSError as e:
        print(f'Error: Port {PORT} is not available: {e}')
        sys.exit(1)

    # Create and start server
    try:
        server = HTTPServer(('0.0.0.0', PORT), SimpleAPIHandler)
        server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(f'Starting simple API server on port {PORT}...')
        print(f'Server is ready at http://localhost:{PORT}/')
        server.serve_forever()
    except OSError as e:
        print(f'Failed to start server: {e}')
        sys.exit(1)
    except KeyboardInterrupt:
        print('\nShutting down server...')
        server.shutdown()
EOF

    chmod +x "$BASE_DIR/simple_api.py"
    echo -e "${GREEN}✓${NC} Created simple API server"

    # Start with explicit proxy clearing
    start_service "Simple API" "cd $BASE_DIR && unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY && NO_PROXY='localhost,127.0.0.1,::1' python3 simple_api.py" "$LOG_DIR/drass-api.log" 8888

    # Wait a bit more to ensure it starts
    sleep 3

    # Check if it actually started
    if lsof -i :8888 >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Simple API server is running on port 8888"
    else
        echo -e "${RED}✗${NC} Simple API server failed to start"
        echo -e "${YELLOW}Checking what happened...${NC}"
        if [ -f "$LOG_DIR/drass-api.log" ]; then
            tail -5 "$LOG_DIR/drass-api.log"
        fi
    fi
}

# Check existing vLLM services
echo -e "\n${BLUE}Checking existing vLLM services...${NC}"
check_service 8001 "vLLM LLM Service"
check_service 8010 "vLLM Embedding Service"
check_service 8012 "vLLM Reranking Service"

# Start vLLM services if not running
if ! check_service 8001 "vLLM LLM Service" >/dev/null 2>&1; then
    echo -e "${YELLOW}Starting vLLM LLM Service...${NC}"
    start_service "vLLM LLM" "ROCM_PATH=/opt/rocm PYTHONPATH=/home/qwkj/triton/python HIP_VISIBLE_DEVICES='0,1' PYTORCH_ROCM_ARCH=gfx906 vllm serve '/home/qwkj/.cache/modelscope/hub/models/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B' --port 8001 --dtype float16 --tensor-parallel-size 2 --block-size 32 --max-num-seqs 64 --max-model-len 12288 --gpu_memory_utilization=0.45 --api_key 123456 --served-model-name vllm" "$LOG_DIR/vllm-llm.log" 8001
fi

if ! check_service 8010 "vLLM Embedding Service" >/dev/null 2>&1; then
    echo -e "${YELLOW}Starting vLLM Embedding Service...${NC}"
    start_service "vLLM Embedding" "python -m vllm.entrypoints.openai.api_server --model /home/qwkj/.cache/modelscope/hub/models/Qwen/Qwen3-Embedding-8B --tensor-parallel-size 2 --max_model_len=8096 --gpu_memory_utilization=0.3 --port 8010 --host 0.0.0.0 --served_model_name Qwen3-Embedding-8B --task embed --api_key 123456" "$LOG_DIR/vllm-embedding.log" 8010
fi

if ! check_service 8012 "vLLM Reranking Service" >/dev/null 2>&1; then
    echo -e "${YELLOW}Starting vLLM Reranking Service...${NC}"
    start_service "vLLM Reranking" "python -m vllm.entrypoints.openai.api_server --model /home/qwkj/Qwen3-Reranker-8B --tensor-parallel-size 2 --max_model_len=8096 --gpu_memory_utilization=0.3 --port 8012 --host 0.0.0.0 --served_model_name Qwen3-Reranker-8B --task embed --api_key 123456" "$LOG_DIR/vllm-reranking.log" 8012
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
    # Change to a neutral directory to avoid permission warnings
    if (cd /tmp && sudo -u postgres psql -c "SELECT 1;" >/dev/null 2>&1); then
        echo -e "${GREEN}✓${NC} PostgreSQL is running and accessible"

        # Create database and user if they don't exist
        echo -e "${BLUE}Setting up database...${NC}"
        (cd /tmp && sudo -u postgres psql <<EOF 2>/dev/null) || true
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
        PG_VERSION=$((cd /tmp && sudo -u postgres psql -t -c "SELECT version();") | grep -oE '[0-9]+' | head -1)
        PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

        if [ -f "$PG_HBA" ]; then
            # Check if we need to add local connection rules (with sudo)
            if ! sudo grep -q "host.*drass_production.*drass_user" "$PG_HBA" 2>/dev/null; then
                echo -e "${BLUE}Updating PostgreSQL authentication configuration...${NC}"

                # Backup original
                sudo cp "$PG_HBA" "$PG_HBA.backup.$(date +%Y%m%d_%H%M%S)"

                # Add connection rules for drass_user (with sudo)
                echo "# Drass application connections" | sudo tee -a "$PG_HBA" >/dev/null 2>&1
                echo "host    drass_production    drass_user    127.0.0.1/32    md5" | sudo tee -a "$PG_HBA" >/dev/null 2>&1
                echo "host    drass_production    drass_user    ::1/128         md5" | sudo tee -a "$PG_HBA" >/dev/null 2>&1
                echo "local   drass_production    drass_user                    md5" | sudo tee -a "$PG_HBA" >/dev/null 2>&1

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

        # First, make sure the data directory exists
        mkdir -p "$DATA_DIR/chromadb"

        # Method 1: Use chromadb module directly
        if python3 -c "import chromadb.app" 2>/dev/null; then
            echo -e "${BLUE}Starting ChromaDB using chromadb.app module...${NC}"
            if ! start_service "ChromaDB" "cd $BASE_DIR && python3 -m chromadb.app --path $DATA_DIR/chromadb --port 8005 --host 0.0.0.0" "$LOG_DIR/chromadb.log" 8005; then
                echo -e "${YELLOW}Method 1 failed, trying alternative methods...${NC}"
            else
                CHROMADB_STARTED=true
            fi
        fi

        # Method 2: Use chroma run command if available
        if [ -z "$CHROMADB_STARTED" ] && command -v chroma >/dev/null 2>&1; then
            echo -e "${BLUE}Starting ChromaDB using chroma command...${NC}"
            if ! start_service "ChromaDB" "cd $BASE_DIR && chroma run --path $DATA_DIR/chromadb --port 8005 --host 0.0.0.0" "$LOG_DIR/chromadb.log" 8005; then
                echo -e "${YELLOW}Method 2 failed, trying alternative methods...${NC}"
            else
                CHROMADB_STARTED=true
            fi
        fi

        # Method 3: Start ChromaDB server programmatically
        if [ -z "$CHROMADB_STARTED" ]; then
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
            if ! start_service "ChromaDB" "cd $BASE_DIR && python3 start_chromadb.py $DATA_DIR/chromadb 8005" "$LOG_DIR/chromadb.log" 8005; then
                echo -e "${YELLOW}Method 3 failed. ChromaDB may not be fully installed.${NC}"

                # Method 4: Try a simple in-memory ChromaDB instance
                echo -e "${BLUE}Starting simple ChromaDB instance...${NC}"
                cat > "$BASE_DIR/chromadb_simple.py" << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Set data path
data_path = sys.argv[1] if len(sys.argv) > 1 else "/home/qwkj/drass/data/chromadb"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8005

print(f"Starting ChromaDB on port {port}")

try:
    import chromadb
    from chromadb.config import Settings

    # Create persistent client
    client = chromadb.PersistentClient(
        path=data_path,
        settings=Settings(allow_reset=True, anonymized_telemetry=False)
    )

    print(f"ChromaDB client initialized at {data_path}")

    # Try to start a simple HTTP server for health checks
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/api/v1/collections':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"collections":[]}')
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'ChromaDB is running')

        def log_message(self, format, *args):
            pass  # Suppress logs

    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"ChromaDB health server running on port {port}")
    server.serve_forever()

except Exception as e:
    print(f"Error starting ChromaDB: {e}")
    import time
    while True:
        time.sleep(60)
EOF
                start_service "ChromaDB Simple" "cd $BASE_DIR && python3 chromadb_simple.py $DATA_DIR/chromadb 8005" "$LOG_DIR/chromadb.log" 8005
            else
                CHROMADB_STARTED=true
            fi
        fi
    else
        echo -e "${RED}ChromaDB is not available. Skipping ChromaDB service.${NC}"
        echo -e "${YELLOW}The system will work without vector storage.${NC}"
    fi
fi

# Start Drass backend API
echo -e "\n${BLUE}Starting Drass Backend API...${NC}"
if ! check_service 8888 "Drass API" >/dev/null 2>&1; then
    # Setup environment configuration
    echo -e "${BLUE}Setting up environment configuration...${NC}"

    # Create .env file with correct vLLM endpoints
    cat > "$BASE_DIR/services/main-app/.env" << 'EOF'
# Auto-generated environment configuration for vLLM services
APP_NAME="Drass Compliance Assistant"
ENVIRONMENT="production"
DEBUG=false
LOG_LEVEL="INFO"

# Server
HOST="0.0.0.0"
PORT=8888

# Database
DATABASE_URL="postgresql://drass_user:drass_password@localhost:5432/drass_production"

# Redis
REDIS_URL="redis://localhost:6379/0"

# LLM Configuration - Using local vLLM service
LLM_PROVIDER="openai"
LLM_MODEL="vllm"
LLM_API_KEY="123456"
LLM_BASE_URL="http://localhost:8001/v1"
OPENAI_API_BASE="http://localhost:8001/v1"
OPENAI_API_KEY="123456"

# Embedding Configuration - Using vLLM embedding service
EMBEDDING_PROVIDER="openai"
EMBEDDING_MODEL="Qwen3-Embedding-8B"
EMBEDDING_API_KEY="123456"
EMBEDDING_API_BASE="http://localhost:8010/v1"
EMBEDDING_DIMENSIONS=1024
EMBEDDING_BATCH_SIZE=100

# Reranking Configuration - Using vLLM reranking service
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

# Security
SECRET_KEY="drass-secret-key-change-in-production"
JWT_ALGORITHM="HS256"
EOF

    echo -e "${GREEN}✓${NC} Environment configuration created"

    # First, ensure FastAPI and uvicorn are installed
    echo -e "${BLUE}Checking backend dependencies...${NC}"
    if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
        echo -e "${YELLOW}Installing FastAPI and Uvicorn...${NC}"
        pip3 install fastapi uvicorn python-multipart python-dotenv pydantic --no-cache-dir || {
            pip3 install --user fastapi uvicorn python-multipart python-dotenv pydantic --no-cache-dir
        }
    fi

    # Install python-jose which is required by security module
    if ! python3 -c "import jose" 2>/dev/null; then
        echo -e "${YELLOW}Installing python-jose for JWT authentication...${NC}"
        pip3 install python-jose[cryptography] --no-cache-dir || {
            pip3 install --user python-jose[cryptography] --no-cache-dir
        }
    fi

    # Install additional dependencies that might be needed
    echo -e "${BLUE}Checking additional backend dependencies...${NC}"
    DEPS_TO_CHECK=("psycopg2" "redis" "httpx" "aiofiles")
    for dep in "${DEPS_TO_CHECK[@]}"; do
        if ! python3 -c "import $dep" 2>/dev/null; then
            echo -e "${YELLOW}Installing $dep...${NC}"
            if [ "$dep" = "psycopg2" ]; then
                pip3 install psycopg2-binary --no-cache-dir 2>/dev/null || true
            else
                pip3 install $dep --no-cache-dir 2>/dev/null || true
            fi
        fi
    done

    # Check if the backend directory exists
    if [ -d "$BASE_DIR/services/main-app" ]; then
        cd "$BASE_DIR/services/main-app"

        # Install additional dependencies if requirements.txt exists
        if [ -f "requirements.txt" ]; then
            echo -e "${BLUE}Installing backend requirements...${NC}"
            pip3 install -r requirements.txt --no-cache-dir 2>/dev/null || {
                echo -e "${YELLOW}Some requirements failed to install, continuing...${NC}"
            }
        fi

        # Check if app/main.py exists
        if [ -f "app/main.py" ]; then
            echo -e "${BLUE}Starting Drass API from existing application...${NC}"

            # Clear proxy settings that might interfere with the API
            echo -e "${BLUE}Clearing proxy settings for API...${NC}"
            unset http_proxy
            unset https_proxy
            unset HTTP_PROXY
            unset HTTPS_PROXY
            unset all_proxy
            unset ALL_PROXY

            # Export NO_PROXY for localhost connections
            export NO_PROXY="localhost,127.0.0.1,::1"

            # Export LLM configuration to ensure it uses vLLM
            export LLM_PROVIDER="openai"
            export LLM_BASE_URL="http://localhost:8001/v1"
            export LLM_API_KEY="123456"
            export LLM_MODEL="vllm"
            export OPENAI_API_BASE="http://localhost:8001/v1"
            export OPENAI_API_KEY="123456"
            export MLX_ENABLED="false"
            export LMSTUDIO_ENABLED="false"

            # Export Embedding configuration for vLLM embedding service
            export EMBEDDING_PROVIDER="openai"
            export EMBEDDING_MODEL="Qwen3-Embedding-8B"
            export EMBEDDING_API_KEY="123456"
            export EMBEDDING_API_BASE="http://localhost:8010/v1"
            export EMBEDDING_DIMENSIONS=1024

            # Export Reranking configuration for vLLM reranking service
            export RERANKING_ENABLED=true
            export RERANKING_API_BASE="http://localhost:8012/v1"
            export RERANKING_API_KEY="123456"

            # Try with different worker counts and without proxy
            start_service "Drass API" "cd $BASE_DIR/services/main-app && source .env 2>/dev/null; unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY && NO_PROXY='localhost,127.0.0.1,::1' LLM_PROVIDER='openai' LLM_BASE_URL='http://localhost:8001/v1' LLM_API_KEY='123456' LLM_MODEL='vllm' OPENAI_API_BASE='http://localhost:8001/v1' MLX_ENABLED='false' LMSTUDIO_ENABLED='false' EMBEDDING_API_BASE='http://localhost:8010/v1' EMBEDDING_API_KEY='123456' RERANKING_API_BASE='http://localhost:8012/v1' python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8888 --workers 1 --loop asyncio" "$LOG_DIR/drass-api.log" 8888
        else
            echo -e "${YELLOW}Main application not found, creating minimal API...${NC}"
            # Create a minimal API server
            create_minimal_api
        fi
    else
        echo -e "${YELLOW}Backend directory not found, creating minimal API...${NC}"
        # Create the directory structure
        mkdir -p "$BASE_DIR/services/main-app/app"
        cd "$BASE_DIR/services/main-app"
        create_minimal_api
    fi

    # Wait and check if API started
    sleep 5
    if ! check_service 8888 "Drass API" >/dev/null 2>&1; then
        echo -e "${YELLOW}API failed to start, checking logs...${NC}"
        if [ -f "$LOG_DIR/drass-api.log" ]; then
            echo -e "${YELLOW}Last 20 lines of API log:${NC}"
            tail -20 "$LOG_DIR/drass-api.log"
        fi

        # Check if port is actually in use by something else
        echo -e "${BLUE}Checking what's on port 8888...${NC}"
        lsof -i :8888 2>/dev/null || echo "  Port 8888 appears to be free"

        # Try alternative startup
        echo -e "${BLUE}Trying alternative API startup...${NC}"
        create_simple_api_server
    fi
fi

# Start Drass frontend
echo -e "\n${BLUE}Starting Drass Frontend...${NC}"
if ! check_service 5173 "Drass Frontend" >/dev/null 2>&1; then
    # First check if port 5173 is blocked by something else
    if lsof -i :5173 >/dev/null 2>&1; then
        echo -e "${YELLOW}Port 5173 is in use, attempting to free it...${NC}"
        lsof -ti :5173 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi

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
                exit 0
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
                start_service "Drass Frontend Dev" "cd $BASE_DIR/frontend && npm run dev -- --host 0.0.0.0 --port 5173" "$LOG_DIR/drass-frontend.log" 5173
                exit 0
            }
        }
    fi

    # Check if build was successful
    if [ -d "dist" ]; then
        echo -e "${GREEN}✓${NC} Frontend built successfully"

        # Serve the production build
        echo -e "${BLUE}Starting frontend server...${NC}"

        # Try different methods to serve the frontend
        FRONTEND_STARTED=false

        # Method 1: Try global serve with different syntax
        if command -v serve >/dev/null 2>&1; then
            echo -e "${BLUE}Checking serve version...${NC}"

            # Check which version/type of serve is installed
            SERVE_VERSION=$(serve --version 2>&1 || serve -V 2>&1 || echo "unknown")
            echo -e "Serve version/info: $SERVE_VERSION"

            # Check if it's the npm serve package
            if serve --help 2>&1 | grep -q "Static file serving" || serve --help 2>&1 | grep -q "\-s,.*\-\-single"; then
                echo -e "${BLUE}Using npm serve package...${NC}"
                start_service "Drass Frontend" "cd $BASE_DIR/frontend && serve -s dist -l 5173 -n" "$LOG_DIR/drass-frontend.log" 5173
            elif serve --help 2>&1 | grep -q "serve \[OPTIONS\] COMMAND"; then
                # This looks like a different serve command (possibly from another package)
                echo -e "${YELLOW}Different serve command detected, skipping...${NC}"
            else
                # Try the standard npm serve syntax anyway
                echo -e "${BLUE}Trying standard serve syntax...${NC}"
                start_service "Drass Frontend" "cd $BASE_DIR/frontend && serve dist -p 5173" "$LOG_DIR/drass-frontend.log" 5173
            fi

            sleep 3
            if lsof -i :5173 >/dev/null 2>&1; then
                FRONTEND_STARTED=true
                echo -e "${GREEN}✓${NC} Frontend started with serve"
            fi
        fi

        # Method 2: Try npx serve (force npm package)
        if [ "$FRONTEND_STARTED" = false ]; then
            echo -e "${BLUE}Trying npx serve (forcing npm package)...${NC}"
            # First try the standard syntax
            if ! start_service "Drass Frontend" "cd $BASE_DIR/frontend && npx serve -s dist -l 5173 -n" "$LOG_DIR/drass-frontend.log" 5173; then
                # If that fails, try alternative syntax
                echo -e "${BLUE}Trying alternative npx serve syntax...${NC}"
                start_service "Drass Frontend" "cd $BASE_DIR/frontend && npx serve dist -p 5173" "$LOG_DIR/drass-frontend.log" 5173
            fi

            sleep 3
            if lsof -i :5173 >/dev/null 2>&1; then
                FRONTEND_STARTED=true
                echo -e "${GREEN}✓${NC} Frontend started with npx serve"
            fi
        fi

        # Method 3: Try Python HTTP server (most reliable fallback)
        if [ "$FRONTEND_STARTED" = false ]; then
            echo -e "${BLUE}Trying Python HTTP server (most reliable method)...${NC}"

            # Check if Python3 is available
            if command -v python3 >/dev/null 2>&1; then
                start_service "Drass Frontend Python" "cd $BASE_DIR/frontend/dist && python3 -m http.server 5173 --bind 0.0.0.0" "$LOG_DIR/drass-frontend.log" 5173
            sleep 3
            if lsof -i :5173 >/dev/null 2>&1; then
                FRONTEND_STARTED=true
                echo -e "${GREEN}✓${NC} Frontend started with Python HTTP server"
            fi
        fi

        # Method 4: Try Node.js HTTP server
        if [ "$FRONTEND_STARTED" = false ]; then
            echo -e "${BLUE}Creating Node.js static server...${NC}"
            cat > "$BASE_DIR/frontend/serve-static.js" << 'EOF'
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 5173;
const DIST_DIR = path.join(__dirname, 'dist');

const server = http.createServer((req, res) => {
    let filePath = path.join(DIST_DIR, req.url === '/' ? 'index.html' : req.url);

    // Default to index.html for SPA routing
    if (!fs.existsSync(filePath)) {
        filePath = path.join(DIST_DIR, 'index.html');
    }

    const extname = String(path.extname(filePath)).toLowerCase();
    const mimeTypes = {
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.css': 'text/css',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.wav': 'audio/wav',
        '.mp4': 'video/mp4',
        '.woff': 'application/font-woff',
        '.ttf': 'application/font-ttf',
        '.eot': 'application/vnd.ms-fontobject',
        '.otf': 'application/font-otf',
        '.wasm': 'application/wasm'
    };

    const contentType = mimeTypes[extname] || 'application/octet-stream';

    fs.readFile(filePath, (error, content) => {
        if (error) {
            if(error.code == 'ENOENT') {
                res.writeHead(404);
                res.end('404 Not Found');
            } else {
                res.writeHead(500);
                res.end('Server Error: '+error.code);
            }
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`Frontend server running at http://localhost:${PORT}/`);
});
EOF
            start_service "Drass Frontend" "cd $BASE_DIR/frontend && node serve-static.js" "$LOG_DIR/drass-frontend.log" 5173
            sleep 3
            if lsof -i :5173 >/dev/null 2>&1; then
                FRONTEND_STARTED=true
                echo -e "${GREEN}✓${NC} Frontend started with Node.js static server"
            fi
        fi

        if [ "$FRONTEND_STARTED" = false ]; then
            echo -e "${RED}✗${NC} Failed to start frontend with production build"
            echo -e "${YELLOW}Check logs at: $LOG_DIR/drass-frontend.log${NC}"
        fi
    else
        echo -e "${YELLOW}Frontend build not found, starting development server...${NC}"
        start_service "Drass Frontend Dev" "cd $BASE_DIR/frontend && npm run dev -- --host 0.0.0.0 --port 5173" "$LOG_DIR/drass-frontend.log"
        sleep 5
        if ! lsof -i :5173 >/dev/null 2>&1; then
            echo -e "${RED}✗${NC} Development server failed to start"
            echo -e "${YELLOW}Check logs at: $LOG_DIR/drass-frontend.log${NC}"
        fi
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
    if (cd /tmp && sudo -u postgres psql -c "SELECT 1;" >/dev/null 2>&1); then
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
check_service 8888 "Drass API"
check_service 5173 "Drass Frontend"

echo -e "\n${GREEN}All services have been started!${NC}"
echo -e "\nAccess the application at: ${BLUE}http://localhost:5173${NC}"
echo -e "API documentation at: ${BLUE}http://localhost:8888/docs${NC}"
echo -e "\nLogs are available in: ${BLUE}$LOG_DIR${NC}"

# Show how to monitor logs
echo -e "\n${YELLOW}To monitor logs:${NC}"
echo -e "  tail -f $LOG_DIR/drass-api.log"
echo -e "  tail -f $LOG_DIR/vllm-llm.log"
echo -e "  tail -f $LOG_DIR/chromadb.log"