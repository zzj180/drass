#!/bin/bash

# Script to completely clean up port 8888 and diagnose what's using it

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Port 8888 Cleanup and Diagnostic Tool${NC}"
echo -e "${BLUE}========================================${NC}"

# Check what's currently using port 8888
echo -e "\n${BLUE}Checking what's using port 8888...${NC}"
if lsof -i :8888 >/dev/null 2>&1; then
    echo -e "${YELLOW}Found processes on port 8888:${NC}"
    lsof -i :8888
    echo ""

    # Get more details about the processes
    PIDS=$(lsof -ti :8888 2>/dev/null)
    for pid in $PIDS; do
        echo -e "${BLUE}Process details for PID $pid:${NC}"
        ps -f -p $pid 2>/dev/null || echo "Could not get process details"
        echo "Command line:"
        cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ' || echo "Could not get command line"
        echo -e "\n"
    done

    # Ask if we should kill them
    echo -e "${YELLOW}Do you want to kill these processes? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Killing processes...${NC}"
        for pid in $PIDS; do
            echo "Killing PID $pid..."
            kill $pid 2>/dev/null
        done
        sleep 2

        # Force kill if still running
        REMAINING=$(lsof -ti :8888 2>/dev/null)
        if [ -n "$REMAINING" ]; then
            echo -e "${YELLOW}Force killing remaining processes...${NC}"
            for pid in $REMAINING; do
                kill -9 $pid 2>/dev/null
            done
            sleep 1
        fi

        # Final check
        if lsof -i :8888 >/dev/null 2>&1; then
            echo -e "${RED}Failed to clean up port 8888!${NC}"
            lsof -i :8888
        else
            echo -e "${GREEN}✓ Port 8888 is now free${NC}"
        fi
    else
        echo -e "${YELLOW}Skipping process termination${NC}"
    fi
else
    echo -e "${GREEN}Port 8888 is free${NC}"
fi

# Check for any simple_api.py processes
echo -e "\n${BLUE}Checking for simple_api.py processes...${NC}"
SIMPLE_API_PIDS=$(ps aux | grep -E 'python.*simple_api\.py' | grep -v grep | awk '{print $2}')
if [ -n "$SIMPLE_API_PIDS" ]; then
    echo -e "${YELLOW}Found simple_api.py processes:${NC}"
    ps aux | grep -E 'python.*simple_api\.py' | grep -v grep
    echo -e "${BLUE}PIDs: $SIMPLE_API_PIDS${NC}"

    echo -e "${YELLOW}Kill these processes? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        for pid in $SIMPLE_API_PIDS; do
            kill -9 $pid 2>/dev/null
        done
        echo -e "${GREEN}✓ Killed simple_api.py processes${NC}"
    fi
else
    echo -e "${GREEN}No simple_api.py processes found${NC}"
fi

# Check for any uvicorn processes on port 8888
echo -e "\n${BLUE}Checking for uvicorn processes...${NC}"
UVICORN_PIDS=$(ps aux | grep -E 'uvicorn.*8888|uvicorn.*app\.main' | grep -v grep | awk '{print $2}')
if [ -n "$UVICORN_PIDS" ]; then
    echo -e "${YELLOW}Found uvicorn processes:${NC}"
    ps aux | grep -E 'uvicorn.*8888|uvicorn.*app\.main' | grep -v grep
    echo -e "${BLUE}PIDs: $UVICORN_PIDS${NC}"

    echo -e "${YELLOW}Kill these processes? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        for pid in $UVICORN_PIDS; do
            kill -9 $pid 2>/dev/null
        done
        echo -e "${GREEN}✓ Killed uvicorn processes${NC}"
    fi
else
    echo -e "${GREEN}No uvicorn processes found${NC}"
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}Cleanup complete!${NC}"
echo -e "${BLUE}========================================${NC}"

# Final status
echo -e "\n${BLUE}Final status:${NC}"
if lsof -i :8888 >/dev/null 2>&1; then
    echo -e "${RED}Port 8888 is still in use:${NC}"
    lsof -i :8888
else
    echo -e "${GREEN}✓ Port 8888 is free and ready for use${NC}"
fi