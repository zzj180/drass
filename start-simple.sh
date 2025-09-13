#!/bin/bash

# ======================================================
# LangChain Compliance Assistant - Simple Startup Script
# ======================================================
# One-click startup for development and testing
# Uses simplified backend for quick testing
# ======================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load configuration from YAML file
CONFIG_FILE="$PROJECT_ROOT/config/app.yaml"
if [ -f "$CONFIG_FILE" ]; then
    FRONTEND_PORT=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['ports']['frontend'])" 2>/dev/null || echo "3000")
    BACKEND_PORT=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['ports']['backend'])" 2>/dev/null || echo "8000")
    LLM_PORT=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['ports']['llm'])" 2>/dev/null || echo "8001")
else
    # Fallback to default values
    FRONTEND_PORT=3000
    BACKEND_PORT=8000
    LLM_PORT=8001
fi

# Log files
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# Function to print colored messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        print_warning "Killing processes on port $port: $pids"
        kill -9 $pids 2>/dev/null || true
        sleep 1
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    print_status "Waiting for $name to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_success "$name is ready!"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
        echo -n "."
    done
    echo
    print_error "$name failed to start (timeout after 30s)"
    return 1
}

# Header
clear
echo "========================================================"
echo "   LangChain Compliance Assistant - Simple Startup"
echo "========================================================"
echo

# Step 1: Check and install dependencies
print_status "Checking Python dependencies..."
cd "$PROJECT_ROOT"

# Check for required Python packages
python3 -c "import flask" 2>/dev/null || {
    print_warning "Installing Flask..."
    pip install flask
}

python3 -c "import mlx_lm" 2>/dev/null || {
    print_warning "Installing mlx-lm..."
    pip install mlx-lm
}

python3 -c "import fastapi" 2>/dev/null || {
    print_warning "Installing FastAPI and dependencies..."
    pip install fastapi uvicorn httpx pydantic
}

# Step 2: Clean up existing processes
print_status "Cleaning up existing processes..."
kill_port $LLM_PORT
kill_port $BACKEND_PORT
kill_port $FRONTEND_PORT

# Step 3: Start LLM Server
print_status "Starting Local LLM Server (Qwen3-8B-MLX) on port $LLM_PORT..."
if [ -f "$PROJECT_ROOT/qwen3_api_server.py" ]; then
    nohup python3 "$PROJECT_ROOT/qwen3_api_server.py" > "$LOG_DIR/llm.log" 2>&1 &
    LLM_PID=$!
    print_success "LLM server started (PID: $LLM_PID)"
    
    # Wait for LLM to be ready
    wait_for_service "http://localhost:$LLM_PORT/health" "LLM Server"
else
    print_error "qwen3_api_server.py not found!"
    print_warning "Continuing without local LLM..."
fi

# Step 4: Start Backend API
print_status "Starting Backend API on port $BACKEND_PORT..."
if [ -f "$PROJECT_ROOT/simple_backend.py" ]; then
    nohup python3 "$PROJECT_ROOT/simple_backend.py" --port $BACKEND_PORT > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    print_success "Backend API started (PID: $BACKEND_PID)"
    
    # Wait for backend to be ready
    wait_for_service "http://localhost:$BACKEND_PORT/health" "Backend API"
else
    print_error "simple_backend.py not found!"
    exit 1
fi

# Step 5: Fix frontend issues and start
print_status "Preparing Frontend..."
cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "Installing frontend dependencies..."
    npm install
fi

# Fix highlight.js issue if needed
if grep -q "highlight.js/styles/github-dark.css" src/components/ChatInterface/MarkdownRenderer.tsx 2>/dev/null; then
    print_warning "Fixing highlight.js import issue..."
    sed -i.bak 's/import "highlight.js\/styles\/github-dark.css";/\/\/ Highlight.js styles handled by rehype-highlight/' \
        src/components/ChatInterface/MarkdownRenderer.tsx
fi

# Update API endpoint to correct port
if grep -q "localhost:8000" src/components/ChatInterface/ChatInterface.tsx 2>/dev/null; then
    print_warning "Updating API endpoint to port $BACKEND_PORT..."
    sed -i.bak "s/localhost:8000/localhost:$BACKEND_PORT/g" \
        src/components/ChatInterface/ChatInterface.tsx
fi

# Start frontend
print_status "Starting Frontend on port $FRONTEND_PORT..."
nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
print_success "Frontend started (PID: $FRONTEND_PID)"

# Wait for frontend to be ready
wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend"

# Step 6: Test the services
echo
print_status "Testing services..."

# Test health endpoint
if curl -s "http://localhost:$BACKEND_PORT/health" | grep -q "healthy"; then
    print_success "Backend API is healthy"
else
    print_warning "Backend API health check failed"
fi

# Test chat endpoint
print_status "Testing chat functionality..."
RESPONSE=$(curl -s -X POST "http://localhost:$BACKEND_PORT/api/v1/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello"}' | python3 -c "import sys, json; print(json.load(sys.stdin).get('response', '')[:50] + '...')" 2>/dev/null)

if [ ! -z "$RESPONSE" ]; then
    print_success "Chat API working: $RESPONSE"
else
    print_warning "Chat API test failed"
fi

# Step 7: Save process information
cat > "$PROJECT_ROOT/.running_processes" << EOF
LLM_PID=$LLM_PID
BACKEND_PID=$BACKEND_PID
FRONTEND_PID=$FRONTEND_PID
STARTUP_TIME=$(date)
EOF

# Step 8: Display summary
echo
echo "========================================================"
echo "            🚀 All Services Started Successfully!"
echo "========================================================"
echo
echo "📋 Service Status:"
echo "  • LLM Server:    http://localhost:$LLM_PORT"
echo "  • Backend API:   http://localhost:$BACKEND_PORT"
echo "  • Frontend UI:   http://localhost:$FRONTEND_PORT"
echo
echo "📁 Log Files:"
echo "  • LLM:      $LOG_DIR/llm.log"
echo "  • Backend:  $LOG_DIR/backend.log"
echo "  • Frontend: $LOG_DIR/frontend.log"
echo
echo "🎯 Quick Tests:"
echo "  • Health Check: curl http://localhost:$BACKEND_PORT/health"
echo "  • API Docs:     http://localhost:$BACKEND_PORT/docs"
echo "  • Chat Test:    curl -X POST http://localhost:$BACKEND_PORT/api/v1/chat \\"
echo "                    -H 'Content-Type: application/json' \\"
echo "                    -d '{\"message\": \"Hello\"}'"
echo
echo "🌐 Open your browser and navigate to:"
echo "   👉 http://localhost:$FRONTEND_PORT"
echo
echo "To stop all services, run: ./stop-services.sh"
echo "========================================================"

# Keep script running and show logs
print_status "Services are running. Press Ctrl+C to stop all services."
print_status "Tailing logs (last 5 lines from each service)..."
echo

# Function to stop all services on exit
cleanup() {
    echo
    print_warning "Stopping all services..."
    [ ! -z "$LLM_PID" ] && kill $LLM_PID 2>/dev/null
    [ ! -z "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    [ ! -z "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    rm -f "$PROJECT_ROOT/.running_processes"
    print_success "All services stopped."
    exit 0
}

trap cleanup INT TERM

# Tail logs
while true; do
    echo "--- LLM Server ---"
    tail -n 5 "$LOG_DIR/llm.log" 2>/dev/null || echo "No logs yet"
    echo
    echo "--- Backend API ---"
    tail -n 5 "$LOG_DIR/backend.log" 2>/dev/null || echo "No logs yet"
    echo
    echo "--- Frontend ---"
    tail -n 5 "$LOG_DIR/frontend.log" 2>/dev/null || echo "No logs yet"
    echo
    echo "========================================================"
    sleep 5
done