#!/bin/bash

# Setup and manage Python virtual environment for Drass

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_DIR="/home/qwkj/drass"
VENV_DIR="$BASE_DIR/venv"
OWNER="qwkj:qwkj"

echo -e "${BLUE}=== Setting up Python Virtual Environment ===${NC}"
echo ""

# 1. Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Running as root - will fix ownership after setup${NC}"
    # Get the actual user who called sudo
    ACTUAL_USER="${SUDO_USER:-qwkj}"
    OWNER="$ACTUAL_USER:$ACTUAL_USER"
else
    ACTUAL_USER=$(whoami)
fi

echo "Setting up for user: $ACTUAL_USER"

# 2. Remove old/problematic venvs
echo -e "\n${BLUE}Cleaning up old virtual environments...${NC}"
if [ -d "$BASE_DIR/.venv-deploy" ]; then
    echo "Removing .venv-deploy (Python 3.13)..."
    rm -rf "$BASE_DIR/.venv-deploy"
fi

if [ -d "$VENV_DIR" ]; then
    echo "Removing existing venv..."
    rm -rf "$VENV_DIR"
fi

# 3. Create new virtual environment with system Python
echo -e "\n${BLUE}Creating new virtual environment...${NC}"
cd "$BASE_DIR"

# Use system Python 3.10
/usr/bin/python3 -m venv venv
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create virtual environment${NC}"
    echo "Installing python3-venv..."
    apt-get update && apt-get install -y python3-venv
    /usr/bin/python3 -m venv venv
fi

# 4. Fix ownership
echo -e "\n${BLUE}Fixing ownership...${NC}"
chown -R $OWNER "$VENV_DIR"
echo -e "${GREEN}✓${NC} Virtual environment owned by $OWNER"

# 5. Create activation wrapper
echo -e "\n${BLUE}Creating activation wrapper...${NC}"
cat > "$BASE_DIR/activate_venv.sh" << 'EOF'
#!/bin/bash
# Wrapper to activate virtual environment

VENV_DIR="/home/qwkj/drass/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: Virtual environment not found at $VENV_DIR"
    echo "Run: bash /home/qwkj/drass/deployment/scripts/setup-venv.sh"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Export Python path
export PYTHON="$VENV_DIR/bin/python"
export PIP="$VENV_DIR/bin/pip"

echo "Virtual environment activated"
echo "Python: $(which python)"
echo "Version: $(python --version)"
EOF

chmod +x "$BASE_DIR/activate_venv.sh"
chown $OWNER "$BASE_DIR/activate_venv.sh"

# 6. Install dependencies in virtual environment
echo -e "\n${BLUE}Installing dependencies in virtual environment...${NC}"

# Create a requirements installer that uses the venv
cat > "$BASE_DIR/install_deps.sh" << 'EOF'
#!/bin/bash

VENV_DIR="/home/qwkj/drass/venv"
BASE_DIR="/home/qwkj/drass"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

echo "Installing dependencies with $(which pip)..."

# Core dependencies
pip install --upgrade pip
pip install wheel setuptools

# FastAPI and server
pip install fastapi uvicorn[standard] python-multipart aiofiles

# Authentication and security
pip install passlib[bcrypt] python-jose[cryptography] python-dotenv

# Database
pip install sqlalchemy psycopg2-binary asyncpg redis

# LangChain and AI
pip install langchain langchain-community langchain-openai openai tiktoken

# Vector store
pip install chromadb sentence-transformers

# HTTP and async
pip install httpx websockets

# Document processing
pip install pypdf python-docx openpyxl beautifulsoup4 lxml

# If requirements.txt exists, install from it
if [ -f "$BASE_DIR/services/main-app/requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install -r "$BASE_DIR/services/main-app/requirements.txt"
fi

echo "Dependencies installed successfully"
EOF

chmod +x "$BASE_DIR/install_deps.sh"
chown $OWNER "$BASE_DIR/install_deps.sh"

# Run the installer
echo "Installing dependencies..."
su - $ACTUAL_USER -c "cd $BASE_DIR && ./install_deps.sh"

# 7. Create a proper startup script that uses venv
echo -e "\n${BLUE}Creating venv-aware startup script...${NC}"
cat > "$BASE_DIR/services/main-app/start_with_venv.sh" << 'EOF'
#!/bin/bash

# Start API with virtual environment

BASE_DIR="/home/qwkj/drass"
VENV_DIR="$BASE_DIR/venv"

# Must run as qwkj user, not root
if [ "$EUID" -eq 0 ]; then
    echo "ERROR: Do not run API as root!"
    echo "Use: su - qwkj -c '$0'"
    exit 1
fi

# Check virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: Virtual environment not found"
    echo "Run: bash $BASE_DIR/deployment/scripts/setup-venv.sh"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Change to app directory
cd "$BASE_DIR/services/main-app"

# Set environment variables
export HOST=0.0.0.0
export PORT=8888

echo "Starting API with virtual environment"
echo "Python: $(which python)"
echo "Working directory: $(pwd)"

# Start uvicorn
exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8888 \
    --workers 1 \
    --loop asyncio
EOF

chmod +x "$BASE_DIR/services/main-app/start_with_venv.sh"
chown -R $OWNER "$BASE_DIR/services/main-app/start_with_venv.sh"

# 8. Test import
echo -e "\n${BLUE}Testing installation...${NC}"
su - $ACTUAL_USER -c "
    source $VENV_DIR/bin/activate
    cd $BASE_DIR/services/main-app
    python -c 'from app.main import app; print(\"✓ App imports successfully\")'
" 2>/dev/null && echo -e "${GREEN}✓${NC} Import test passed" || echo -e "${RED}✗${NC} Import test failed"

echo -e "\n${BLUE}=== Setup Complete ===${NC}"
echo ""
echo "Virtual environment created at: $VENV_DIR"
echo "Owner: $OWNER"
echo ""
echo "To use:"
echo "1. As qwkj user: source $BASE_DIR/activate_venv.sh"
echo "2. Start API: $BASE_DIR/services/main-app/start_with_venv.sh"
echo ""
echo -e "${YELLOW}Important: Do NOT use sudo to run the API!${NC}"
echo "Instead use: su - qwkj -c 'command'"