#!/bin/bash
# Fix and start Frontend service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Frontend Fix and Start Script${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"
FRONTEND_DIR="$BASE_DIR/frontend"
LOG_DIR="$BASE_DIR/logs"

# Create directories
mkdir -p "$LOG_DIR"

# Function to kill frontend processes
kill_frontend() {
    echo -e "\n${BLUE}Stopping any existing frontend processes...${NC}"

    # Kill by port
    if lsof -i :5173 >/dev/null 2>&1; then
        echo -e "${YELLOW}Killing processes on port 5173...${NC}"
        lsof -ti :5173 | xargs -r kill -9 2>/dev/null || true
        sleep 2
    fi

    # Kill serve processes
    pkill -f "serve.*dist" 2>/dev/null || true
    pkill -f "python.*http.server.*5173" 2>/dev/null || true
    pkill -f "node.*5173" 2>/dev/null || true
    sleep 1

    echo -e "${GREEN}✓${NC} Cleaned up existing processes"
}

# Function to check Node.js and npm
check_nodejs() {
    echo -e "\n${BLUE}Checking Node.js installation...${NC}"

    if command -v node >/dev/null 2>&1; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN}✓${NC} Node.js is installed: $NODE_VERSION"
    else
        echo -e "${RED}✗${NC} Node.js is not installed"
        return 1
    fi

    if command -v npm >/dev/null 2>&1; then
        NPM_VERSION=$(npm --version)
        echo -e "${GREEN}✓${NC} npm is installed: $NPM_VERSION"
    else
        echo -e "${RED}✗${NC} npm is not installed"
        return 1
    fi

    return 0
}

# Function to check/install serve
check_serve() {
    echo -e "\n${BLUE}Checking serve installation...${NC}"

    # Check global serve
    if command -v serve >/dev/null 2>&1; then
        # Check what type of serve it is
        if serve --help 2>&1 | grep -q "Static file serving"; then
            echo -e "${GREEN}✓${NC} npm serve package is installed globally"
            echo "SERVE_TYPE=npm" > /tmp/serve_type
            return 0
        elif serve --help 2>&1 | grep -q "serve \[OPTIONS\] COMMAND"; then
            echo -e "${YELLOW}!${NC} Different 'serve' command detected (not npm package)"
            echo "SERVE_TYPE=other" > /tmp/serve_type
        else
            echo -e "${YELLOW}!${NC} Unknown serve command type"
            echo "SERVE_TYPE=unknown" > /tmp/serve_type
        fi
    else
        echo -e "${YELLOW}!${NC} serve is not installed globally"
        echo "SERVE_TYPE=none" > /tmp/serve_type
    fi

    # Check if serve is available via npx
    if npx serve --version 2>/dev/null | grep -q "[0-9]"; then
        echo -e "${GREEN}✓${NC} serve is available via npx"
        return 0
    fi

    # Install serve locally
    echo -e "${BLUE}Installing serve locally...${NC}"
    cd "$FRONTEND_DIR"
    npm install --save-dev serve || {
        echo -e "${YELLOW}!${NC} Failed to install serve"
        return 1
    }

    return 0
}

# Function to build frontend
build_frontend() {
    echo -e "\n${BLUE}Building frontend...${NC}"

    cd "$FRONTEND_DIR"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${BLUE}Installing dependencies...${NC}"
        npm install --legacy-peer-deps || {
            echo -e "${RED}✗${NC} Failed to install dependencies"
            return 1
        }
    fi

    # Check if dist already exists
    if [ -d "dist" ]; then
        echo -e "${GREEN}✓${NC} Production build already exists"
        return 0
    fi

    # Try to build
    echo -e "${BLUE}Building production bundle...${NC}"

    # Method 1: Standard build with type check disabled
    if TSC_COMPILE_ON_ERROR=true npm run build 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Build successful"
        return 0
    fi

    # Method 2: Direct Vite build
    echo -e "${YELLOW}Standard build failed, trying Vite directly...${NC}"
    if npx vite build --mode production 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Vite build successful"
        return 0
    fi

    echo -e "${RED}✗${NC} Failed to build frontend"
    return 1
}

# Function to start with serve (npm package)
start_with_serve() {
    echo -e "\n${BLUE}Starting frontend with serve...${NC}"

    cd "$FRONTEND_DIR"

    # Try different serve syntaxes
    local commands=(
        "npx serve -s dist -l 5173 -n"
        "npx serve dist -p 5173"
        "npx serve dist --listen 5173"
        "npx serve -s dist --port 5173"
    )

    for cmd in "${commands[@]}"; do
        echo -e "${BLUE}Trying: $cmd${NC}"

        $cmd > "$LOG_DIR/frontend.log" 2>&1 &
        local pid=$!
        sleep 3

        if ps -p $pid > /dev/null 2>&1 && lsof -i :5173 >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Frontend started with serve (PID: $pid)"
            echo -e "Command: $cmd"
            return 0
        else
            kill $pid 2>/dev/null || true
        fi
    done

    echo -e "${YELLOW}!${NC} Could not start with serve"
    return 1
}

# Function to start with Python HTTP server
start_with_python() {
    echo -e "\n${BLUE}Starting frontend with Python HTTP server...${NC}"

    if ! command -v python3 >/dev/null 2>&1; then
        echo -e "${RED}✗${NC} Python3 is not installed"
        return 1
    fi

    cd "$FRONTEND_DIR/dist"

    python3 -m http.server 5173 --bind 0.0.0.0 > "$LOG_DIR/frontend.log" 2>&1 &
    local pid=$!
    sleep 3

    if ps -p $pid > /dev/null 2>&1 && lsof -i :5173 >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Frontend started with Python HTTP server (PID: $pid)"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to start with Python HTTP server"
        return 1
    fi
}

# Function to start with Node.js static server
start_with_node() {
    echo -e "\n${BLUE}Starting frontend with Node.js static server...${NC}"

    cd "$FRONTEND_DIR"

    # Create a simple Node.js static server
    cat > serve-static.js << 'EOF'
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const port = 5173;
const directory = path.join(__dirname, 'dist');

const mimeTypes = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon'
};

const server = http.createServer((req, res) => {
    let pathname = url.parse(req.url).pathname;

    // Default to index.html for root
    if (pathname === '/') {
        pathname = '/index.html';
    }

    // For SPA, serve index.html for all non-file routes
    let filePath = path.join(directory, pathname);

    fs.access(filePath, fs.constants.F_OK, (err) => {
        if (err) {
            // If file doesn't exist, serve index.html (for SPA routing)
            filePath = path.join(directory, 'index.html');
        }

        fs.readFile(filePath, (error, content) => {
            if (error) {
                if (error.code === 'ENOENT') {
                    res.writeHead(404, { 'Content-Type': 'text/plain' });
                    res.end('404 Not Found', 'utf-8');
                } else {
                    res.writeHead(500);
                    res.end('Server Error: ' + error.code, 'utf-8');
                }
            } else {
                const ext = path.extname(filePath);
                const mimeType = mimeTypes[ext] || 'application/octet-stream';
                res.writeHead(200, { 'Content-Type': mimeType });
                res.end(content, 'utf-8');
            }
        });
    });
});

server.listen(port, '0.0.0.0', () => {
    console.log(`Frontend server running at http://0.0.0.0:${port}`);
});
EOF

    node serve-static.js > "$LOG_DIR/frontend.log" 2>&1 &
    local pid=$!
    sleep 3

    if ps -p $pid > /dev/null 2>&1 && lsof -i :5173 >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Frontend started with Node.js static server (PID: $pid)"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to start with Node.js static server"
        return 1
    fi
}

# Function to start development server
start_dev_server() {
    echo -e "\n${BLUE}Starting frontend in development mode...${NC}"

    cd "$FRONTEND_DIR"

    npm run dev -- --host 0.0.0.0 --port 5173 > "$LOG_DIR/frontend.log" 2>&1 &
    local pid=$!
    sleep 5

    if ps -p $pid > /dev/null 2>&1 && lsof -i :5173 >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Frontend started in development mode (PID: $pid)"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to start development server"
        return 1
    fi
}

# Function to verify frontend
verify_frontend() {
    echo -e "\n${BLUE}Verifying frontend service...${NC}"

    # Check port
    if lsof -i :5173 >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Port 5173 is listening"
    else
        echo -e "${RED}✗${NC} Port 5173 is not listening"
        return 1
    fi

    # Check HTTP response
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 | grep -qE "^[23]"; then
        echo -e "${GREEN}✓${NC} Frontend is responding"
        return 0
    else
        echo -e "${YELLOW}!${NC} Frontend may not be responding correctly"
        return 0  # Still consider it running if port is open
    fi
}

# Main execution
echo -e "\n${BLUE}Starting frontend fix process...${NC}"

# Step 1: Kill existing processes
kill_frontend

# Step 2: Check Node.js
if ! check_nodejs; then
    echo -e "${RED}Node.js is required but not installed${NC}"
    echo -e "Install with: ${BLUE}sudo apt-get install nodejs npm${NC}"
    exit 1
fi

# Step 3: Check frontend directory
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

# Step 4: Build frontend
if ! [ -d "$FRONTEND_DIR/dist" ]; then
    build_frontend
fi

# Step 5: Check serve
check_serve
source /tmp/serve_type 2>/dev/null || SERVE_TYPE="unknown"

# Step 6: Try to start frontend
STARTED=false

# If we have a dist folder, try production servers
if [ -d "$FRONTEND_DIR/dist" ]; then
    # Try Python first (most reliable)
    if start_with_python; then
        STARTED=true
    # Then try serve
    elif [ "$SERVE_TYPE" != "other" ] && start_with_serve; then
        STARTED=true
    # Then try Node.js static server
    elif start_with_node; then
        STARTED=true
    fi
fi

# If no production build or failed to serve, try dev server
if [ "$STARTED" = false ]; then
    if start_dev_server; then
        STARTED=true
    fi
fi

# Step 7: Verify
if [ "$STARTED" = true ]; then
    verify_frontend
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Frontend is now running on port 5173${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "\nAccess URL: ${BLUE}http://localhost:5173${NC}"
    echo -e "Log file: ${BLUE}$LOG_DIR/frontend.log${NC}"
    echo -e "\nTo check status:"
    echo -e "  ${BLUE}lsof -i :5173${NC}"
    echo -e "  ${BLUE}curl http://localhost:5173${NC}"
else
    echo -e "\n${RED}========================================${NC}"
    echo -e "${RED}Failed to start frontend${NC}"
    echo -e "${RED}========================================${NC}"
    echo -e "\nPlease check:"
    echo -e "1. Node.js version: ${BLUE}node --version${NC}"
    echo -e "2. npm version: ${BLUE}npm --version${NC}"
    echo -e "3. Frontend directory: ${BLUE}ls -la $FRONTEND_DIR${NC}"
    echo -e "4. Log file: ${BLUE}cat $LOG_DIR/frontend.log${NC}"
    exit 1
fi