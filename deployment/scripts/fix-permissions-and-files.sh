#!/bin/bash

# Fix permissions and Python environment issues

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_DIR="/home/qwkj/drass"

echo -e "${BLUE}=== Fixing Drass Deployment Issues ===${NC}"
echo ""

# 1. Fix file ownership
echo -e "${BLUE}1. Fixing file ownership...${NC}"
if [ -f "$BASE_DIR/standalone_api.py" ]; then
    sudo chown qwkj:qwkj "$BASE_DIR/standalone_api.py"
    echo -e "${GREEN}✓${NC} Fixed standalone_api.py ownership"
fi

if [ -f "$BASE_DIR/services/main-app/start_production.py" ]; then
    sudo chown qwkj:qwkj "$BASE_DIR/services/main-app/start_production.py"
    echo -e "${GREEN}✓${NC} Fixed start_production.py ownership"
fi

# Fix any other root-owned files in the project
find "$BASE_DIR" -user root -type f 2>/dev/null | while read -r file; do
    if [[ "$file" != *"/logs/"* ]] && [[ "$file" != *"/.git/"* ]]; then
        echo "  Fixing: $file"
        sudo chown qwkj:qwkj "$file"
    fi
done

# 2. Update simple_api.py with the correct content
echo -e "\n${BLUE}2. Updating simple_api.py...${NC}"
cat > "$BASE_DIR/simple_api.py" << 'EOF'
#!/usr/bin/env python3
"""
FALLBACK API - This should NOT be used in production!
If this is running, it means the main API failed to start.
"""

# CRITICAL: Prevent any imports from app
import sys
import os

# Remove all paths that could lead to app imports BEFORE any other imports
clean_paths = []
for p in sys.path:
    if 'services' not in p and 'main-app' not in p:
        clean_paths.append(p)
sys.path = clean_paths

# Now safe to import standard library
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import datetime

print("=" * 50)
print("WARNING: Running FALLBACK simple_api.py")
print("This means the main API failed to start!")
print("Check /home/qwkj/drass/logs/drass-api.log")
print("=" * 50)

PORT = 8888

class FallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {
            'status': 'fallback',
            'message': 'Main API failed - running fallback',
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        self.send_response(503)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        response = {
            'error': 'Main API unavailable',
            'message': 'Check logs at /home/qwkj/drass/logs/drass-api.log'
        }
        self.wfile.write(json.dumps(response).encode())

if __name__ == '__main__':
    print(f'Starting fallback server on port {PORT}...')
    try:
        server = HTTPServer(('0.0.0.0', PORT), FallbackHandler)
        server.serve_forever()
    except Exception as e:
        print(f'Fallback server error: {e}')
        sys.exit(1)
EOF

chmod +x "$BASE_DIR/simple_api.py"
chown qwkj:qwkj "$BASE_DIR/simple_api.py"
echo -e "${GREEN}✓${NC} Updated simple_api.py"

# 3. Create a proper startup wrapper that ensures correct Python
echo -e "\n${BLUE}3. Creating Python wrapper script...${NC}"
cat > "$BASE_DIR/services/main-app/run_api.sh" << 'EOF'
#!/bin/bash

# Ensure we use the correct Python and environment
cd /home/qwkj/drass/services/main-app

# Use system Python 3.10 (not venv)
PYTHON_CMD="/usr/bin/python3"

# Clear any problematic environment
unset PYTHONPATH
unset PYTHONHOME

# Set required environment variables
export PORT=8888
export HOST=0.0.0.0

echo "Starting API with Python: $($PYTHON_CMD --version)"
echo "Working directory: $(pwd)"

# Run the API directly with uvicorn
exec $PYTHON_CMD -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8888 \
    --workers 1 \
    --loop asyncio \
    --log-level info
EOF

chmod +x "$BASE_DIR/services/main-app/run_api.sh"
chown qwkj:qwkj "$BASE_DIR/services/main-app/run_api.sh"
echo -e "${GREEN}✓${NC} Created run_api.sh"

# 4. Check Python environments
echo -e "\n${BLUE}4. Python environment check:${NC}"
echo "System Python: $(which python3) - $(/usr/bin/python3 --version)"

if [ -d "$BASE_DIR/.venv-deploy" ]; then
    echo -e "${YELLOW}Found .venv-deploy (Python 3.13) - this might cause issues${NC}"
    echo "Consider removing: rm -rf $BASE_DIR/.venv-deploy"
fi

# 5. Verify uvicorn is installed for system Python
echo -e "\n${BLUE}5. Checking uvicorn installation...${NC}"
if /usr/bin/python3 -c "import uvicorn" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} uvicorn is installed"
else
    echo -e "${YELLOW}!${NC} uvicorn not found, installing..."
    /usr/bin/python3 -m pip install uvicorn --user
fi

# 6. Test that main app can be imported
echo -e "\n${BLUE}6. Testing main app import...${NC}"
cd "$BASE_DIR/services/main-app"
if /usr/bin/python3 -c "from app.main import app; print('✓ Main app imports successfully')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Main app can be imported"
else
    echo -e "${RED}✗${NC} Main app import failed:"
    /usr/bin/python3 -c "from app.main import app" 2>&1 | head -10
fi

echo -e "\n${BLUE}=== Fix Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Clear port 8888: sudo lsof -ti :8888 | xargs -r kill -9"
echo "2. Try running directly: cd $BASE_DIR/services/main-app && ./run_api.sh"
echo "3. Or use the startup script: sudo bash $BASE_DIR/deployment/scripts/start-ubuntu-services.sh"