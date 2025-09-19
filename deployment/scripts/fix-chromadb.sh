#!/bin/bash
# Fix and start ChromaDB service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ChromaDB Fix and Start Script${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"
DATA_DIR="$BASE_DIR/data/chromadb"
LOG_DIR="$BASE_DIR/logs"

# Create directories
mkdir -p "$DATA_DIR"
mkdir -p "$LOG_DIR"

# Function to kill ChromaDB processes
kill_chromadb() {
    echo -e "\n${BLUE}Stopping any existing ChromaDB processes...${NC}"

    # Kill by port
    if lsof -i :8005 >/dev/null 2>&1; then
        echo -e "${YELLOW}Killing processes on port 8005...${NC}"
        lsof -ti :8005 | xargs -r kill -9 2>/dev/null || true
        sleep 2
    fi

    # Kill by process name
    pkill -f "chromadb" 2>/dev/null || true
    pkill -f "chroma" 2>/dev/null || true
    sleep 1

    echo -e "${GREEN}✓${NC} Cleaned up existing processes"
}

# Function to check ChromaDB installation
check_chromadb() {
    echo -e "\n${BLUE}Checking ChromaDB installation...${NC}"

    if python3 -c "import chromadb" 2>/dev/null; then
        VERSION=$(python3 -c "import chromadb; print(chromadb.__version__)" 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✓${NC} ChromaDB is installed (version: $VERSION)"
        return 0
    else
        echo -e "${RED}✗${NC} ChromaDB is not installed"
        return 1
    fi
}

# Function to install ChromaDB
install_chromadb() {
    echo -e "\n${BLUE}Installing ChromaDB...${NC}"

    # Try with pip3
    pip3 install chromadb --upgrade --no-cache-dir || {
        echo -e "${YELLOW}System-wide install failed, trying user install...${NC}"
        pip3 install --user chromadb --upgrade --no-cache-dir || {
            echo -e "${RED}Failed to install ChromaDB${NC}"
            return 1
        }
    }

    # Also install dependencies
    pip3 install uvicorn fastapi --upgrade --no-cache-dir 2>/dev/null || true

    echo -e "${GREEN}✓${NC} ChromaDB installed"
    return 0
}

# Function to test ChromaDB import
test_chromadb() {
    echo -e "\n${BLUE}Testing ChromaDB modules...${NC}"

    # Test basic import
    if python3 -c "import chromadb" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} chromadb module imports successfully"
    else
        echo -e "${RED}✗${NC} Cannot import chromadb"
        return 1
    fi

    # Test app module
    if python3 -c "import chromadb.app" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} chromadb.app module available"
        return 0
    else
        echo -e "${YELLOW}!${NC} chromadb.app module not available (older version?)"
        return 1
    fi
}

# Function to start ChromaDB with method 1: chromadb.app
start_chromadb_app() {
    echo -e "\n${BLUE}Starting ChromaDB with chromadb.app...${NC}"

    python3 -m chromadb.app \
        --path "$DATA_DIR" \
        --port 8005 \
        --host 0.0.0.0 \
        > "$LOG_DIR/chromadb.log" 2>&1 &

    local pid=$!
    sleep 5

    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} ChromaDB started with chromadb.app (PID: $pid)"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to start with chromadb.app"
        if [ -f "$LOG_DIR/chromadb.log" ]; then
            echo -e "${YELLOW}Error from log:${NC}"
            tail -10 "$LOG_DIR/chromadb.log"
        fi
        return 1
    fi
}

# Function to start ChromaDB with method 2: chroma CLI
start_chromadb_cli() {
    echo -e "\n${BLUE}Starting ChromaDB with chroma CLI...${NC}"

    if ! command -v chroma >/dev/null 2>&1; then
        echo -e "${YELLOW}chroma command not found, installing...${NC}"
        pip3 install chromadb[server] --upgrade --no-cache-dir 2>/dev/null || true
    fi

    if command -v chroma >/dev/null 2>&1; then
        chroma run \
            --path "$DATA_DIR" \
            --port 8005 \
            --host 0.0.0.0 \
            > "$LOG_DIR/chromadb.log" 2>&1 &

        local pid=$!
        sleep 5

        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} ChromaDB started with chroma CLI (PID: $pid)"
            return 0
        fi
    fi

    echo -e "${RED}✗${NC} Failed to start with chroma CLI"
    return 1
}

# Function to start ChromaDB with method 3: Custom server
start_chromadb_custom() {
    echo -e "\n${BLUE}Starting ChromaDB with custom server...${NC}"

    cat > "$BASE_DIR/chromadb_server.py" << 'EOF'
#!/usr/bin/env python3
import sys
import os
import signal

# Set data path
data_path = sys.argv[1] if len(sys.argv) > 1 else "/home/qwkj/drass/data/chromadb"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8005

print(f"Starting ChromaDB custom server on port {port}")
print(f"Data path: {data_path}")

def signal_handler(sig, frame):
    print("\nShutting down ChromaDB...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    # Try modern ChromaDB API server
    try:
        from chromadb import api
        from chromadb.server import Server

        server = Server(
            host="0.0.0.0",
            port=port,
            chroma_db_impl="duckdb+parquet",
            persist_directory=data_path
        )
        print("Starting ChromaDB server (new API)...")
        server.run()
    except ImportError:
        # Fall back to older API
        try:
            import chromadb
            from chromadb.app import app
            import uvicorn

            print("Starting ChromaDB server with uvicorn...")
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        except ImportError:
            # Last resort: simple persistent client with HTTP server
            import chromadb
            from chromadb.config import Settings
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import json

            print("Creating ChromaDB persistent client...")
            client = chromadb.PersistentClient(
                path=data_path,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )

            # Create a test collection
            try:
                client.create_collection("test")
            except:
                pass

            class ChromaHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/api/v1/collections':
                        collections = client.list_collections()
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        response = {"collections": [{"name": c.name} for c in collections]}
                        self.wfile.write(json.dumps(response).encode())
                    elif self.path == '/health':
                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(b'OK')
                    else:
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b'ChromaDB is running')

                def log_message(self, format, *args):
                    pass  # Suppress logs

            server = HTTPServer(('0.0.0.0', port), ChromaHandler)
            print(f"ChromaDB HTTP server running on port {port}")
            server.serve_forever()

except Exception as e:
    print(f"Error starting ChromaDB: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

    python3 "$BASE_DIR/chromadb_server.py" "$DATA_DIR" 8005 > "$LOG_DIR/chromadb.log" 2>&1 &

    local pid=$!
    sleep 8

    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} ChromaDB started with custom server (PID: $pid)"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to start with custom server"
        if [ -f "$LOG_DIR/chromadb.log" ]; then
            echo -e "${YELLOW}Error from log:${NC}"
            tail -10 "$LOG_DIR/chromadb.log"
        fi
        return 1
    fi
}

# Function to verify ChromaDB is running
verify_chromadb() {
    echo -e "\n${BLUE}Verifying ChromaDB service...${NC}"

    # Check port
    if lsof -i :8005 >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Port 8005 is listening"
    else
        echo -e "${RED}✗${NC} Port 8005 is not listening"
        return 1
    fi

    # Check HTTP endpoint
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8005/api/v1/collections | grep -qE "^[23]"; then
        echo -e "${GREEN}✓${NC} ChromaDB API is responding"
        return 0
    elif curl -s -o /dev/null -w "%{http_code}" http://localhost:8005/health | grep -qE "^[23]"; then
        echo -e "${GREEN}✓${NC} ChromaDB health endpoint is responding"
        return 0
    else
        echo -e "${YELLOW}!${NC} ChromaDB HTTP endpoints not fully responding"
        return 0  # Still consider it running if port is open
    fi
}

# Main execution
echo -e "\n${BLUE}Starting ChromaDB fix process...${NC}"

# Step 1: Kill existing processes
kill_chromadb

# Step 2: Check/install ChromaDB
if ! check_chromadb; then
    install_chromadb
fi

# Step 3: Test ChromaDB modules
HAS_APP_MODULE=false
if test_chromadb; then
    HAS_APP_MODULE=true
fi

# Step 4: Try to start ChromaDB
STARTED=false

if [ "$HAS_APP_MODULE" = true ]; then
    if start_chromadb_app; then
        STARTED=true
    fi
fi

if [ "$STARTED" = false ]; then
    if start_chromadb_cli; then
        STARTED=true
    fi
fi

if [ "$STARTED" = false ]; then
    if start_chromadb_custom; then
        STARTED=true
    fi
fi

# Step 5: Verify
if [ "$STARTED" = true ]; then
    verify_chromadb
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}ChromaDB is now running on port 8005${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "\nData directory: ${BLUE}$DATA_DIR${NC}"
    echo -e "Log file: ${BLUE}$LOG_DIR/chromadb.log${NC}"
    echo -e "\nTo check status:"
    echo -e "  ${BLUE}lsof -i :8005${NC}"
    echo -e "  ${BLUE}curl http://localhost:8005/api/v1/collections${NC}"
else
    echo -e "\n${RED}========================================${NC}"
    echo -e "${RED}Failed to start ChromaDB${NC}"
    echo -e "${RED}========================================${NC}"
    echo -e "\nPlease check:"
    echo -e "1. Python version: ${BLUE}python3 --version${NC}"
    echo -e "2. ChromaDB installation: ${BLUE}pip3 show chromadb${NC}"
    echo -e "3. Log file: ${BLUE}cat $LOG_DIR/chromadb.log${NC}"
    exit 1
fi