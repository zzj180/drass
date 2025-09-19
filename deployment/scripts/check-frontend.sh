#!/bin/bash
# Frontend diagnostic and fix script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Drass Frontend Diagnostic Tool${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"
FRONTEND_DIR="$BASE_DIR/frontend"
LOG_DIR="$BASE_DIR/logs"

# Function to check port
check_port() {
    local port=$1
    echo -e "\n${BLUE}Checking port $port...${NC}"

    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Port $port is in use by:"
        lsof -i :$port | head -5
        return 0
    else
        echo -e "${YELLOW}!${NC} Port $port is not in use"
        return 1
    fi
}

# Function to check Node.js
check_nodejs() {
    echo -e "\n${BLUE}Checking Node.js installation...${NC}"

    if command -v node >/dev/null 2>&1; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN}✓${NC} Node.js is installed: $NODE_VERSION"

        NPM_VERSION=$(npm --version)
        echo -e "${GREEN}✓${NC} npm is installed: $NPM_VERSION"
        return 0
    else
        echo -e "${RED}✗${NC} Node.js is not installed"
        return 1
    fi
}

# Function to check frontend directory
check_frontend_dir() {
    echo -e "\n${BLUE}Checking frontend directory...${NC}"

    if [ -d "$FRONTEND_DIR" ]; then
        echo -e "${GREEN}✓${NC} Frontend directory exists: $FRONTEND_DIR"

        # Check important files
        if [ -f "$FRONTEND_DIR/package.json" ]; then
            echo -e "${GREEN}✓${NC} package.json found"
        else
            echo -e "${RED}✗${NC} package.json not found"
            return 1
        fi

        # Check node_modules
        if [ -d "$FRONTEND_DIR/node_modules" ]; then
            echo -e "${GREEN}✓${NC} node_modules exists"
        else
            echo -e "${YELLOW}!${NC} node_modules not found (need to run npm install)"
        fi

        # Check dist folder
        if [ -d "$FRONTEND_DIR/dist" ]; then
            echo -e "${GREEN}✓${NC} dist folder exists (production build)"
        else
            echo -e "${YELLOW}!${NC} dist folder not found (need to build)"
        fi

        return 0
    else
        echo -e "${RED}✗${NC} Frontend directory not found at $FRONTEND_DIR"
        return 1
    fi
}

# Function to check serve command
check_serve() {
    echo -e "\n${BLUE}Checking serve command...${NC}"

    if command -v serve >/dev/null 2>&1; then
        SERVE_VERSION=$(serve --version 2>&1 || echo "unknown")
        echo -e "${GREEN}✓${NC} serve is installed: $SERVE_VERSION"

        # Check where serve is installed
        which serve
        return 0
    else
        echo -e "${YELLOW}!${NC} serve is not installed globally"

        # Check if serve is in node_modules
        if [ -f "$FRONTEND_DIR/node_modules/.bin/serve" ]; then
            echo -e "${GREEN}✓${NC} serve found in node_modules"
            return 0
        else
            echo -e "${YELLOW}!${NC} serve not found in node_modules either"
            return 1
        fi
    fi
}

# Function to test simple HTTP server
test_simple_server() {
    echo -e "\n${BLUE}Testing simple HTTP server on port 5173...${NC}"

    # Kill any existing process
    if lsof -i :5173 >/dev/null 2>&1; then
        echo -e "${YELLOW}Port 5173 is in use, killing existing process...${NC}"
        lsof -ti :5173 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi

    # Test with Python HTTP server
    cd "$FRONTEND_DIR/dist" 2>/dev/null || cd "$FRONTEND_DIR"

    timeout 5 python3 -m http.server 5173 >/dev/null 2>&1 &
    local pid=$!

    sleep 2

    if ps -p $pid >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Python HTTP server works on port 5173"
        kill $pid 2>/dev/null || true
    else
        echo -e "${RED}✗${NC} Cannot start server on port 5173"
    fi
}

# Function to start frontend with different methods
start_frontend_methods() {
    echo -e "\n${BLUE}Testing different frontend startup methods...${NC}"

    cd "$FRONTEND_DIR"

    # Method 1: Using serve globally
    echo -e "\n${BLUE}Method 1: Global serve command${NC}"
    if command -v serve >/dev/null 2>&1 && [ -d "dist" ]; then
        echo "Testing: serve -s dist -l 5173 -n"
        timeout 5 serve -s dist -l 5173 -n >/dev/null 2>&1 &
        local pid=$!
        sleep 2

        if ps -p $pid >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Global serve works"
            kill $pid 2>/dev/null || true
        else
            echo -e "${RED}✗${NC} Global serve failed"
        fi
    else
        echo -e "${YELLOW}Skipped (serve not installed globally or no dist)${NC}"
    fi

    # Method 2: Using npx serve
    echo -e "\n${BLUE}Method 2: npx serve${NC}"
    if [ -d "dist" ]; then
        echo "Testing: npx serve -s dist -l 5173"
        timeout 5 npx serve -s dist -l 5173 >/dev/null 2>&1 &
        local pid=$!
        sleep 3

        if ps -p $pid >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} npx serve works"
            kill $pid 2>/dev/null || true
        else
            echo -e "${RED}✗${NC} npx serve failed"
        fi
    else
        echo -e "${YELLOW}Skipped (no dist folder)${NC}"
    fi

    # Method 3: Using npm run dev
    echo -e "\n${BLUE}Method 3: npm run dev${NC}"
    if [ -f "package.json" ]; then
        echo "Testing: npm run dev"
        timeout 5 npm run dev -- --host 0.0.0.0 --port 5173 >/dev/null 2>&1 &
        local pid=$!
        sleep 3

        if ps -p $pid >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} npm run dev works"
            kill $pid 2>/dev/null || true
        else
            echo -e "${RED}✗${NC} npm run dev failed"
        fi
    fi

    # Method 4: Python HTTP server
    echo -e "\n${BLUE}Method 4: Python HTTP server${NC}"
    if [ -d "dist" ]; then
        echo "Testing: python3 -m http.server 5173"
        cd dist
        timeout 5 python3 -m http.server 5173 >/dev/null 2>&1 &
        local pid=$!
        sleep 2

        if ps -p $pid >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Python HTTP server works"
            kill $pid 2>/dev/null || true
        else
            echo -e "${RED}✗${NC} Python HTTP server failed"
        fi
        cd ..
    else
        echo -e "${YELLOW}Skipped (no dist folder)${NC}"
    fi
}

# Function to install serve
install_serve() {
    echo -e "\n${BLUE}Installing serve...${NC}"

    # Try global install
    echo -e "${BLUE}Trying global install...${NC}"
    npm install -g serve 2>/dev/null || {
        echo -e "${YELLOW}Global install failed, trying local install...${NC}"
        cd "$FRONTEND_DIR"
        npm install --save-dev serve
    }
}

# Function to create startup script
create_startup_script() {
    echo -e "\n${BLUE}Creating frontend startup script...${NC}"

    cat > "$FRONTEND_DIR/start_frontend.sh" << 'EOF'
#!/bin/bash

# Frontend startup script with fallback methods
BASE_DIR="/home/qwkj/drass"
FRONTEND_DIR="$BASE_DIR/frontend"
LOG_FILE="$BASE_DIR/logs/drass-frontend.log"

cd "$FRONTEND_DIR"

echo "Starting frontend service..."
echo "Current directory: $(pwd)"

# Check if dist exists
if [ ! -d "dist" ]; then
    echo "Error: dist folder not found. Building..."
    npm run build || {
        echo "Build failed, starting development server..."
        npm run dev -- --host 0.0.0.0 --port 5173 > "$LOG_FILE" 2>&1
        exit 0
    }
fi

# Try different methods to serve the frontend
echo "Attempting to serve production build..."

# Method 1: serve command
if command -v serve >/dev/null 2>&1; then
    echo "Using global serve..."
    serve -s dist -l 5173 -n > "$LOG_FILE" 2>&1
elif [ -f "node_modules/.bin/serve" ]; then
    echo "Using local serve..."
    ./node_modules/.bin/serve -s dist -l 5173 -n > "$LOG_FILE" 2>&1
elif command -v npx >/dev/null 2>&1; then
    echo "Using npx serve..."
    npx serve -s dist -l 5173 -n > "$LOG_FILE" 2>&1
else
    echo "Falling back to Python HTTP server..."
    cd dist
    python3 -m http.server 5173 > "$LOG_FILE" 2>&1
fi
EOF

    chmod +x "$FRONTEND_DIR/start_frontend.sh"
    echo -e "${GREEN}✓${NC} Created $FRONTEND_DIR/start_frontend.sh"
}

# Main diagnostic flow
echo -e "\n${YELLOW}Running frontend diagnostics...${NC}"

# Run checks
check_nodejs
NODE_OK=$?

check_frontend_dir
DIR_OK=$?

check_serve
SERVE_OK=$?

check_port 5173
PORT_STATUS=$?

# Test server methods
if [ $NODE_OK -eq 0 ] && [ $DIR_OK -eq 0 ]; then
    test_simple_server
    start_frontend_methods
fi

# Install serve if needed
if [ $SERVE_OK -ne 0 ]; then
    echo -e "\n${YELLOW}serve is not installed. Installing...${NC}"
    install_serve
fi

# Create startup script
create_startup_script

# Check logs
echo -e "\n${BLUE}Checking frontend logs...${NC}"
if [ -f "$LOG_DIR/drass-frontend.log" ]; then
    echo -e "${BLUE}Last 10 lines of frontend log:${NC}"
    tail -10 "$LOG_DIR/drass-frontend.log" 2>/dev/null || echo "  Log file empty or inaccessible"
fi

# Final recommendations
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Recommendations:${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $PORT_STATUS -eq 0 ]; then
    echo -e "${YELLOW}Port 5173 is in use. Kill the process:${NC}"
    echo -e "  lsof -ti :5173 | xargs kill -9"
fi

echo -e "\n${GREEN}To start the frontend, use one of these methods:${NC}"
echo -e "1. Using the startup script:"
echo -e "   ${BLUE}$FRONTEND_DIR/start_frontend.sh${NC}"
echo -e ""
echo -e "2. Production build with serve:"
echo -e "   ${BLUE}cd $FRONTEND_DIR && npx serve -s dist -l 5173${NC}"
echo -e ""
echo -e "3. Development server:"
echo -e "   ${BLUE}cd $FRONTEND_DIR && npm run dev -- --host 0.0.0.0 --port 5173${NC}"
echo -e ""
echo -e "4. Simple Python server:"
echo -e "   ${BLUE}cd $FRONTEND_DIR/dist && python3 -m http.server 5173${NC}"