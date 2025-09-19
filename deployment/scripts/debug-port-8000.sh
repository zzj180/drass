#!/bin/bash
# Debug script for port 8000 issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Debugging Port 8000 Issues${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"
LOG_DIR="$BASE_DIR/logs"

# Function to check port usage
check_port() {
    local port=$1
    echo -e "\n${BLUE}Checking port $port...${NC}"

    # Method 1: lsof
    echo -e "${BLUE}Using lsof:${NC}"
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i :$port 2>/dev/null; then
            echo -e "${YELLOW}Port $port is in use (lsof)${NC}"
        else
            echo -e "${GREEN}Port $port is free (lsof)${NC}"
        fi
    else
        echo -e "${YELLOW}lsof not available${NC}"
    fi

    # Method 2: netstat
    echo -e "\n${BLUE}Using netstat:${NC}"
    if command -v netstat >/dev/null 2>&1; then
        if sudo netstat -tlnp 2>/dev/null | grep ":$port"; then
            echo -e "${YELLOW}Port $port is in use (netstat)${NC}"
        else
            echo -e "${GREEN}Port $port is free (netstat)${NC}"
        fi
    else
        echo -e "${YELLOW}netstat not available${NC}"
    fi

    # Method 3: ss
    echo -e "\n${BLUE}Using ss:${NC}"
    if command -v ss >/dev/null 2>&1; then
        if sudo ss -tlnp 2>/dev/null | grep ":$port"; then
            echo -e "${YELLOW}Port $port is in use (ss)${NC}"
        else
            echo -e "${GREEN}Port $port is free (ss)${NC}"
        fi
    else
        echo -e "${YELLOW}ss not available${NC}"
    fi

    # Method 4: Python socket test
    echo -e "\n${BLUE}Testing with Python socket:${NC}"
    python3 << EOF
import socket
import sys

def test_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('0.0.0.0', port))
        sock.close()
        print(f"✓ Can bind to port {port}")
        return True
    except OSError as e:
        print(f"✗ Cannot bind to port {port}: {e}")
        return False

test_port($port)
EOF
}

# Function to kill process on port
kill_port() {
    local port=$1
    echo -e "\n${BLUE}Attempting to kill process on port $port...${NC}"

    # Try to find and kill process
    if lsof -ti :$port >/dev/null 2>&1; then
        local pids=$(lsof -ti :$port)
        echo -e "${YELLOW}Found PIDs on port $port: $pids${NC}"

        for pid in $pids; do
            echo -e "Process info for PID $pid:"
            ps -fp $pid || true

            echo -e "${YELLOW}Killing PID $pid...${NC}"
            kill -9 $pid 2>/dev/null || sudo kill -9 $pid 2>/dev/null || true
        done

        sleep 2
        echo -e "${GREEN}Processes killed${NC}"
    else
        echo -e "${GREEN}No process found on port $port${NC}"
    fi
}

# Test simple HTTP server
test_simple_server() {
    echo -e "\n${BLUE}Testing simple HTTP server on port 8000...${NC}"

    # Kill any existing process
    kill_port 8000

    # Create test server
    cat > /tmp/test_server.py << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import socket
import sys
import os

# Clear proxy settings
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    if key in os.environ:
        del os.environ[key]

os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'

PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logs

try:
    # Try with SO_REUSEADDR
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(f"✓ Server started on port {PORT}")
        print(f"Test with: curl http://localhost:{PORT}/")
        print("Press Ctrl+C to stop...")
        httpd.serve_forever()
except OSError as e:
    print(f"✗ Failed to start server: {e}")
    sys.exit(1)
EOF

    chmod +x /tmp/test_server.py

    # Start server in background
    echo -e "${BLUE}Starting test server...${NC}"
    timeout 5 python3 /tmp/test_server.py &
    local pid=$!

    sleep 2

    # Test if server is running
    if ps -p $pid >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Test server started successfully${NC}"

        # Test with curl
        if curl -s http://localhost:8000/ >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Server responds to HTTP requests${NC}"
        else
            echo -e "${RED}✗ Server doesn't respond to HTTP requests${NC}"
        fi

        # Kill test server
        kill $pid 2>/dev/null || true
    else
        echo -e "${RED}✗ Test server failed to start${NC}"
    fi
}

# Test with FastAPI
test_fastapi_server() {
    echo -e "\n${BLUE}Testing FastAPI server...${NC}"

    cat > /tmp/test_fastapi.py << 'EOF'
#!/usr/bin/env python3
import os
import sys

# Clear proxy settings
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    if key in os.environ:
        del os.environ[key]

os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'

try:
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI()

    @app.get("/")
    def read_root():
        return {"status": "ok", "message": "Test FastAPI server"}

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")

except ImportError as e:
    print(f"✗ FastAPI not available: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
EOF

    chmod +x /tmp/test_fastapi.py

    # Start FastAPI server
    echo -e "${BLUE}Starting FastAPI test server...${NC}"
    timeout 5 python3 /tmp/test_fastapi.py 2>/dev/null &
    local pid=$!

    sleep 3

    # Test if server is running
    if ps -p $pid >/dev/null 2>&1; then
        echo -e "${GREEN}✓ FastAPI server started${NC}"

        # Test with curl
        if curl -s http://localhost:8000/health | grep -q "healthy"; then
            echo -e "${GREEN}✓ FastAPI responds correctly${NC}"
        else
            echo -e "${RED}✗ FastAPI doesn't respond correctly${NC}"
        fi

        # Kill test server
        kill $pid 2>/dev/null || true
    else
        echo -e "${RED}✗ FastAPI server failed to start${NC}"
    fi
}

# Check firewall rules
check_firewall() {
    echo -e "\n${BLUE}Checking firewall rules...${NC}"

    # Check iptables
    if command -v iptables >/dev/null 2>&1; then
        echo -e "${BLUE}iptables rules for port 8000:${NC}"
        sudo iptables -L -n | grep -E "8000|ACCEPT.*0\.0\.0\.0" | head -10 || echo "  No specific rules for port 8000"
    fi

    # Check ufw
    if command -v ufw >/dev/null 2>&1; then
        echo -e "\n${BLUE}UFW status:${NC}"
        sudo ufw status | grep -E "8000|Anywhere" | head -10 || echo "  No UFW rules for port 8000"
    fi
}

# Check system limits
check_limits() {
    echo -e "\n${BLUE}Checking system limits...${NC}"

    echo -e "Open file limits:"
    ulimit -n

    echo -e "\nProcess limits:"
    ulimit -u

    echo -e "\nCurrent user: $(whoami)"
    echo -e "Groups: $(groups)"
}

# Main diagnostic flow
echo -e "\n${YELLOW}Starting diagnostics...${NC}"

# Check port 8000
check_port 8000

# Check firewall
check_firewall

# Check system limits
check_limits

# Test servers
test_simple_server
test_fastapi_server

# Check logs
echo -e "\n${BLUE}Checking recent API logs...${NC}"
if [ -f "$LOG_DIR/drass-api.log" ]; then
    echo -e "${BLUE}Last 10 lines of drass-api.log:${NC}"
    tail -10 "$LOG_DIR/drass-api.log" 2>/dev/null || echo "  Log file empty or inaccessible"
fi

# Recommendations
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Recommendations:${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n1. If port is in use, kill the process:"
echo -e "   ${YELLOW}lsof -ti :8000 | xargs kill -9${NC}"

echo -e "\n2. Start a minimal test server:"
echo -e "   ${YELLOW}python3 -m http.server 8000${NC}"

echo -e "\n3. Check for permission issues:"
echo -e "   ${YELLOW}sudo -u $(whoami) python3 -m http.server 8000${NC}"

echo -e "\n4. Try a different port:"
echo -e "   ${YELLOW}python3 -m http.server 8080${NC}"

echo -e "\n5. Check network interfaces:"
echo -e "   ${YELLOW}ip addr show${NC}"
echo -e "   ${YELLOW}netstat -tuln | grep LISTEN${NC}"