#!/bin/bash

# Non-interactive script to forcefully clean up port 8888

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Force cleaning port 8888...${NC}"

# Kill anything on port 8888
if lsof -i :8888 >/dev/null 2>&1; then
    echo -e "${YELLOW}Killing processes on port 8888...${NC}"
    lsof -ti :8888 | xargs -r kill -9 2>/dev/null
    sleep 1
fi

# Kill any simple_api.py processes
echo -e "${BLUE}Killing any simple_api.py processes...${NC}"
pkill -9 -f "python.*simple_api.py" 2>/dev/null || true

# Kill any uvicorn processes that might be using 8888
echo -e "${BLUE}Killing any uvicorn processes on port 8888...${NC}"
pkill -9 -f "uvicorn.*8888" 2>/dev/null || true
pkill -9 -f "uvicorn.*app.main" 2>/dev/null || true

sleep 1

# Final check
if lsof -i :8888 >/dev/null 2>&1; then
    echo -e "${RED}WARNING: Port 8888 is still in use after cleanup!${NC}"
    lsof -i :8888
    exit 1
else
    echo -e "${GREEN}✓ Port 8888 is now free${NC}"
    exit 0
fi