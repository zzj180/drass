#!/bin/bash
# Stop all Drass services on Ubuntu

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Stopping Drass Services on Ubuntu${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"
LOG_DIR="$BASE_DIR/logs"

# Function to stop a service by port
stop_service_by_port() {
    local service_name=$1
    local port=$2

    echo -e "\n${BLUE}Stopping $service_name on port $port...${NC}"

    # Find and kill processes on the port
    if lsof -i :$port >/dev/null 2>&1; then
        PIDS=$(lsof -ti :$port)
        if [ -n "$PIDS" ]; then
            echo -e "${YELLOW}Found PIDs on port $port: $PIDS${NC}"
            for pid in $PIDS; do
                # Get process info before killing
                PROCESS_INFO=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
                echo -e "  Stopping process: $PROCESS_INFO (PID: $pid)"
                kill $pid 2>/dev/null || true
            done

            # Wait a moment
            sleep 2

            # Force kill if still running
            for pid in $PIDS; do
                if ps -p $pid > /dev/null 2>&1; then
                    echo -e "${YELLOW}  Force killing PID $pid${NC}"
                    kill -9 $pid 2>/dev/null || true
                fi
            done

            echo -e "${GREEN}✓${NC} $service_name stopped"
        fi
    else
        echo -e "${YELLOW}!${NC} No process found on port $port"
    fi
}

# Function to stop a service by process name
stop_service_by_name() {
    local service_name=$1
    local process_pattern=$2

    echo -e "\n${BLUE}Stopping $service_name...${NC}"

    # Find processes matching pattern
    PIDS=$(pgrep -f "$process_pattern" 2>/dev/null || true)

    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}Found PIDs for $service_name: $PIDS${NC}"
        for pid in $PIDS; do
            echo -e "  Stopping PID: $pid"
            kill $pid 2>/dev/null || true
        done

        sleep 2

        # Force kill if still running
        for pid in $PIDS; do
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}  Force killing PID $pid${NC}"
                kill -9 $pid 2>/dev/null || true
            fi
        done

        echo -e "${GREEN}✓${NC} $service_name stopped"
    else
        echo -e "${YELLOW}!${NC} No $service_name processes found"
    fi
}

# 1. Stop Frontend Service (port 5173)
echo -e "\n${BLUE}=== Stopping Frontend Service ===${NC}"
stop_service_by_port "Frontend" 5173

# 2. Stop API Service (port 8888)
echo -e "\n${BLUE}=== Stopping API Service ===${NC}"
stop_service_by_port "Drass API" 8888

# Also check for uvicorn processes
stop_service_by_name "Uvicorn" "uvicorn.*app.main:app.*8888"

# 3. Stop ChromaDB (port 8005)
echo -e "\n${BLUE}=== Stopping ChromaDB ===${NC}"
stop_service_by_port "ChromaDB" 8005

# Also stop by process name
stop_service_by_name "ChromaDB Process" "chroma.*8005"

# 4. Stop Redis (port 6379)
echo -e "\n${BLUE}=== Stopping Redis ===${NC}"
if command -v redis-cli >/dev/null 2>&1; then
    echo -e "${BLUE}Shutting down Redis gracefully...${NC}"
    redis-cli shutdown 2>/dev/null || true
    sleep 1
fi

# Also check port
if lsof -i :6379 >/dev/null 2>&1; then
    stop_service_by_port "Redis" 6379
else
    echo -e "${GREEN}✓${NC} Redis is not running"
fi

# 5. Stop PostgreSQL (optional, usually we keep it running)
echo -e "\n${BLUE}=== PostgreSQL Status ===${NC}"
echo -e "${YELLOW}Note: PostgreSQL is a system service and will not be stopped${NC}"
echo -e "To stop PostgreSQL manually, run: ${BLUE}sudo systemctl stop postgresql${NC}"

# 6. Stop any Python simple servers
echo -e "\n${BLUE}=== Stopping Python HTTP Servers ===${NC}"
stop_service_by_name "Python HTTP Server" "python.*http.server"
stop_service_by_name "Python SimpleHTTP" "python.*SimpleHTTPServer"

# 7. Stop any serve processes
echo -e "\n${BLUE}=== Stopping Node Serve Processes ===${NC}"
stop_service_by_name "Node Serve" "serve.*dist"

# 8. Clean up any orphaned processes
echo -e "\n${BLUE}=== Cleaning up orphaned processes ===${NC}"

# Check for any uvicorn processes
UVICORN_PIDS=$(pgrep -f "uvicorn" 2>/dev/null || true)
if [ -n "$UVICORN_PIDS" ]; then
    echo -e "${YELLOW}Found orphaned uvicorn processes: $UVICORN_PIDS${NC}"
    for pid in $UVICORN_PIDS; do
        kill -9 $pid 2>/dev/null || true
    done
fi

# Check for any node processes in frontend directory
NODE_PIDS=$(pgrep -f "$BASE_DIR/frontend" 2>/dev/null || true)
if [ -n "$NODE_PIDS" ]; then
    echo -e "${YELLOW}Found orphaned node processes: $NODE_PIDS${NC}"
    for pid in $NODE_PIDS; do
        kill -9 $pid 2>/dev/null || true
    done
fi

echo -e "${GREEN}✓${NC} Cleanup completed"

# 9. Check final status
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Service Status Summary${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to check if port is in use
check_port() {
    local port=$1
    local service=$2

    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${RED}✗${NC} Port $port still in use ($service)"
        return 1
    else
        echo -e "${GREEN}✓${NC} Port $port is free ($service)"
        return 0
    fi
}

# Check all service ports
ALL_STOPPED=true
check_port 5173 "Frontend" || ALL_STOPPED=false
check_port 8888 "API" || ALL_STOPPED=false
check_port 8005 "ChromaDB" || ALL_STOPPED=false
check_port 6379 "Redis" || ALL_STOPPED=false

if [ "$ALL_STOPPED" = true ]; then
    echo -e "\n${GREEN}✓ All Drass services have been stopped successfully${NC}"
else
    echo -e "\n${YELLOW}! Some services may still be running${NC}"
    echo -e "You can force stop all services with:"
    echo -e "  ${BLUE}sudo lsof -ti :5173,8888,8005 | xargs -r kill -9${NC}"
fi

# Optional: Clear logs
echo -e "\n${BLUE}Log files:${NC}"
echo -e "Logs are preserved at: ${BLUE}$LOG_DIR${NC}"
echo -e "To clear logs, run: ${BLUE}rm -f $LOG_DIR/*.log${NC}"