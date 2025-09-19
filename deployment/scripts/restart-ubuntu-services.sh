#!/bin/bash
# Restart all Drass services on Ubuntu

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Restarting Drass Services on Ubuntu${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"
SCRIPT_DIR="$BASE_DIR/deployment/scripts"

# Check if stop and start scripts exist
if [ ! -f "$SCRIPT_DIR/stop-ubuntu-services.sh" ]; then
    echo -e "${RED}Error: stop-ubuntu-services.sh not found at $SCRIPT_DIR${NC}"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/start-ubuntu-services.sh" ]; then
    echo -e "${RED}Error: start-ubuntu-services.sh not found at $SCRIPT_DIR${NC}"
    exit 1
fi

# Make scripts executable
chmod +x "$SCRIPT_DIR/stop-ubuntu-services.sh"
chmod +x "$SCRIPT_DIR/start-ubuntu-services.sh"

# Function to wait for port to be free
wait_for_port_free() {
    local port=$1
    local service=$2
    local max_wait=10
    local count=0

    echo -e "${BLUE}Waiting for port $port to be free ($service)...${NC}"

    while [ $count -lt $max_wait ]; do
        if ! lsof -i :$port >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Port $port is free"
            return 0
        fi
        sleep 1
        count=$((count + 1))
        echo -ne "."
    done

    echo -e "\n${YELLOW}! Port $port still in use after ${max_wait}s${NC}"
    return 1
}

# Step 1: Stop all services
echo -e "\n${BLUE}=== Step 1: Stopping all services ===${NC}"
bash "$SCRIPT_DIR/stop-ubuntu-services.sh"

# Step 2: Wait for critical ports to be free
echo -e "\n${BLUE}=== Step 2: Waiting for ports to be free ===${NC}"

wait_for_port_free 5173 "Frontend"
wait_for_port_free 8888 "API"
wait_for_port_free 8005 "ChromaDB"

# Step 3: Clean up any lingering processes (force)
echo -e "\n${BLUE}=== Step 3: Force cleanup ===${NC}"

# Force kill any remaining processes on our ports
for port in 5173 8888 8005; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${YELLOW}Force killing processes on port $port${NC}"
        lsof -ti :$port | xargs -r kill -9 2>/dev/null || true
    fi
done

# Wait a bit for processes to fully terminate
echo -e "${BLUE}Waiting for processes to terminate...${NC}"
sleep 3

# Step 4: Clear stale PID files if any
echo -e "\n${BLUE}=== Step 4: Clearing stale PID files ===${NC}"
if [ -d "$BASE_DIR/run" ]; then
    rm -f "$BASE_DIR/run/*.pid" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Cleared PID files"
fi

# Step 5: Start all services
echo -e "\n${BLUE}=== Step 5: Starting all services ===${NC}"
bash "$SCRIPT_DIR/start-ubuntu-services.sh"

# Step 6: Verify services are running
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Verifying Service Status${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to check service status
check_service_status() {
    local port=$1
    local service=$2
    local url=$3

    echo -e "\n${BLUE}Checking $service...${NC}"

    # Check if port is in use
    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $service is running on port $port"

        # Try to access the service if URL provided
        if [ -n "$url" ]; then
            if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -qE "^[23]"; then
                echo -e "${GREEN}✓${NC} $service is responding at $url"
            else
                echo -e "${YELLOW}!${NC} $service is running but not responding at $url"
            fi
        fi
        return 0
    else
        echo -e "${RED}✗${NC} $service is not running on port $port"
        return 1
    fi
}

# Wait a bit for services to fully start
echo -e "${BLUE}Waiting for services to initialize...${NC}"
sleep 5

# Check each service
ALL_RUNNING=true

check_service_status 5173 "Frontend" "http://localhost:5173" || ALL_RUNNING=false
check_service_status 8888 "API" "http://localhost:8888/health" || ALL_RUNNING=false
check_service_status 8005 "ChromaDB" "http://localhost:8005/api/v1/collections" || ALL_RUNNING=false

# Check Redis
echo -e "\n${BLUE}Checking Redis...${NC}"
if redis-cli ping >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is responding"
else
    echo -e "${YELLOW}!${NC} Redis is not responding"
    ALL_RUNNING=false
fi

# Check PostgreSQL
echo -e "\n${BLUE}Checking PostgreSQL...${NC}"
if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} PostgreSQL is ready"
else
    echo -e "${YELLOW}!${NC} PostgreSQL is not ready"
fi

# Final status
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Restart Summary${NC}"
echo -e "${BLUE}========================================${NC}"

if [ "$ALL_RUNNING" = true ]; then
    echo -e "${GREEN}✓ All Drass services have been restarted successfully!${NC}"
    echo -e "\nAccess points:"
    echo -e "  Frontend: ${BLUE}http://localhost:5173${NC}"
    echo -e "  API:      ${BLUE}http://localhost:8888${NC}"
    echo -e "  API Docs: ${BLUE}http://localhost:8888/docs${NC}"
else
    echo -e "${YELLOW}! Some services may have issues${NC}"
    echo -e "\nTroubleshooting:"
    echo -e "  Check logs:    ${BLUE}tail -f $BASE_DIR/logs/*.log${NC}"
    echo -e "  Check ports:   ${BLUE}lsof -i :5173,8888,8005,6379,5432${NC}"
    echo -e "  Manual start:  ${BLUE}bash $SCRIPT_DIR/start-ubuntu-services.sh${NC}"
fi

# Show log locations
echo -e "\nLog files:"
echo -e "  Frontend: ${BLUE}$BASE_DIR/logs/drass-frontend.log${NC}"
echo -e "  API:      ${BLUE}$BASE_DIR/logs/drass-api.log${NC}"
echo -e "  ChromaDB: ${BLUE}$BASE_DIR/logs/chromadb.log${NC}"