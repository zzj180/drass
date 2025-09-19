#!/bin/bash
# Drass API diagnostic and fix script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Drass API Diagnostic Tool${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"
LOG_DIR="$BASE_DIR/logs"

# Function to check port
check_port() {
    local port=$1
    local name=$2

    echo -e "\n${BLUE}Checking port $port for $name...${NC}"

    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Port $port is in use by:"
        lsof -i :$port | head -5
        return 0
    else
        echo -e "${YELLOW}!${NC} Port $port is not in use"
        return 1
    fi
}

# Function to check Python dependencies
check_dependencies() {
    echo -e "\n${BLUE}Checking Python dependencies for API...${NC}"

    local deps=("fastapi" "uvicorn" "pydantic" "python-multipart" "python-dotenv")
    local missing_deps=()

    for dep in "${deps[@]}"; do
        if python3 -c "import ${dep//-/_}" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $dep is installed"
        else
            echo -e "${RED}✗${NC} $dep is not installed"
            missing_deps+=("$dep")
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}Installing missing dependencies...${NC}"
        pip3 install ${missing_deps[@]} --no-cache-dir || {
            echo -e "${YELLOW}Failed with standard install, trying with --user flag...${NC}"
            pip3 install --user ${missing_deps[@]} --no-cache-dir
        }
    fi
}

# Function to check API directory structure
check_directory_structure() {
    echo -e "\n${BLUE}Checking API directory structure...${NC}"

    if [ -d "$BASE_DIR/services/main-app" ]; then
        echo -e "${GREEN}✓${NC} Main app directory exists"

        if [ -f "$BASE_DIR/services/main-app/app/main.py" ]; then
            echo -e "${GREEN}✓${NC} app/main.py found"
            return 0
        else
            echo -e "${YELLOW}!${NC} app/main.py not found"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} Main app directory not found at $BASE_DIR/services/main-app"
        return 1
    fi
}

# Function to test API with curl
test_api() {
    local port=$1

    echo -e "\n${BLUE}Testing API on port $port...${NC}"

    # Test root endpoint
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/ | grep -q "200\|404"; then
        echo -e "${GREEN}✓${NC} API responds to HTTP requests"

        # Test health endpoint
        response=$(curl -s http://localhost:$port/health 2>/dev/null || echo "{}")
        if echo "$response" | grep -q "status"; then
            echo -e "${GREEN}✓${NC} Health endpoint is working"
            echo "  Response: $response" | head -c 100
        else
            echo -e "${YELLOW}!${NC} Health endpoint not responding properly"
        fi
        return 0
    else
        echo -e "${RED}✗${NC} API is not responding on port $port"
        return 1
    fi
}

# Function to check logs
check_logs() {
    echo -e "\n${BLUE}Checking API logs...${NC}"

    if [ -f "$LOG_DIR/drass-api.log" ]; then
        echo -e "${GREEN}✓${NC} Log file exists: $LOG_DIR/drass-api.log"

        # Show last 20 lines of log
        echo -e "\n${BLUE}Last 20 lines of API log:${NC}"
        tail -20 "$LOG_DIR/drass-api.log" 2>/dev/null || echo "  (empty or inaccessible)"

        # Check for common errors
        echo -e "\n${BLUE}Checking for common errors...${NC}"
        if grep -q "error\|ERROR\|Error" "$LOG_DIR/drass-api.log" 2>/dev/null; then
            echo -e "${YELLOW}!${NC} Errors found in log:"
            grep -i "error" "$LOG_DIR/drass-api.log" | tail -5
        else
            echo -e "${GREEN}✓${NC} No obvious errors in log"
        fi
    else
        echo -e "${YELLOW}!${NC} Log file not found at $LOG_DIR/drass-api.log"
    fi
}

# Function to start test API
start_test_api() {
    echo -e "\n${BLUE}Starting test API server...${NC}"

    # Create test API
    cat > "$BASE_DIR/test_api.py" << 'EOF'
#!/usr/bin/env python3
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Drass Test API")

@app.get("/")
def root():
    return {"message": "Test API is running", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy", "api": "test"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
EOF

    chmod +x "$BASE_DIR/test_api.py"

    echo -e "${BLUE}Starting test API...${NC}"
    cd "$BASE_DIR"
    nohup python3 test_api.py > "$LOG_DIR/test-api.log" 2>&1 &
    local pid=$!

    sleep 3

    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Test API started with PID $pid"
        echo -e "  Stop with: kill $pid"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to start test API"
        if [ -f "$LOG_DIR/test-api.log" ]; then
            echo "  Error log:"
            cat "$LOG_DIR/test-api.log"
        fi
        return 1
    fi
}

# Function to fix common issues
fix_issues() {
    echo -e "\n${BLUE}Attempting to fix common issues...${NC}"

    # Install dependencies
    check_dependencies

    # Create directory structure if missing
    if ! check_directory_structure >/dev/null 2>&1; then
        echo -e "${BLUE}Creating directory structure...${NC}"
        mkdir -p "$BASE_DIR/services/main-app/app"

        # Create minimal main.py
        cat > "$BASE_DIR/services/main-app/app/main.py" << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import datetime

app = FastAPI(title="Drass API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Drass API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "services": {"api": True}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
EOF

        touch "$BASE_DIR/services/main-app/app/__init__.py"
        echo -e "${GREEN}✓${NC} Created minimal API structure"
    fi

    # Kill any process using port 8888
    if lsof -i :8888 >/dev/null 2>&1; then
        echo -e "${YELLOW}Port 8888 is in use, stopping existing process...${NC}"
        lsof -ti :8888 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Main diagnostic flow
echo -e "\n${YELLOW}Running Drass API diagnostics...${NC}"

# Check port status
check_port 8888 "Drass API"
PORT_STATUS=$?

# Check dependencies
check_dependencies

# Check directory structure
check_directory_structure
DIR_STATUS=$?

# Check logs
check_logs

# If API is running, test it
if [ $PORT_STATUS -eq 0 ]; then
    test_api 8888
    API_TEST=$?
else
    API_TEST=1
fi

# Final status and recommendations
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Diagnostic Summary:${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $PORT_STATUS -eq 0 ] && [ $API_TEST -eq 0 ]; then
    echo -e "${GREEN}✓ API is running and responding correctly${NC}"
elif [ $PORT_STATUS -eq 0 ] && [ $API_TEST -ne 0 ]; then
    echo -e "${YELLOW}⚠ Process is running on port 8888 but API is not responding${NC}"
    echo -e "\nRecommendations:"
    echo -e "1. Check if it's the correct process: lsof -i :8888"
    echo -e "2. Restart the API service"
    echo -e "3. Check logs: tail -f $LOG_DIR/drass-api.log"
else
    echo -e "${RED}✗ API is not running${NC}"
    echo -e "\nRecommendations:"

    if [ $DIR_STATUS -ne 0 ]; then
        echo -e "1. Fix directory structure issues"
        fix_issues
    fi

    echo -e "2. Start the API manually:"
    echo -e "   cd $BASE_DIR/services/main-app"
    echo -e "   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8888"
    echo -e ""
    echo -e "3. Or start a test API:"
    read -p "Do you want to start a test API? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_test_api
    fi
fi