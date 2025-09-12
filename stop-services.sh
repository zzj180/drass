#!/bin/bash

# ======================================================
# Stop All Services Script
# ======================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo "========================================================"
echo "          Stopping All Services"
echo "========================================================"
echo

# Method 1: Try to read PIDs from file
if [ -f ".running_processes" ]; then
    print_warning "Reading process information..."
    source .running_processes
    
    if [ ! -z "$LLM_PID" ]; then
        print_warning "Stopping LLM Server (PID: $LLM_PID)..."
        kill $LLM_PID 2>/dev/null && print_success "LLM Server stopped"
    fi
    
    if [ ! -z "$BACKEND_PID" ]; then
        print_warning "Stopping Backend API (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null && print_success "Backend API stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        print_warning "Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null && print_success "Frontend stopped"
    fi
    
    rm -f .running_processes
fi

# Method 2: Kill by port
print_warning "Checking for remaining processes on ports..."

# Kill processes on specific ports
for port in 8001 8080 8000 3000 5173; do
    pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        print_warning "Killing processes on port $port: $pids"
        kill -9 $pids 2>/dev/null
    fi
done

# Method 3: Kill by process name
print_warning "Checking for remaining Python and Node processes..."
pkill -f "qwen3_api_server.py" 2>/dev/null
pkill -f "simple_backend.py" 2>/dev/null
pkill -f "main-app/app/main.py" 2>/dev/null
pkill -f "vite" 2>/dev/null

echo
print_success "All services have been stopped!"
echo "========================================================"