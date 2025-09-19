#!/bin/bash
# ChromaDB diagnostic and fix script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ChromaDB Diagnostic Tool${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"
DATA_DIR="$BASE_DIR/data"
LOG_DIR="$BASE_DIR/logs"

# Function to check Python version
check_python() {
    echo -e "\n${BLUE}Checking Python installation...${NC}"

    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version)
        echo -e "${GREEN}✓${NC} Python is installed: $PYTHON_VERSION"

        # Check Python version is 3.8+
        PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
        PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            echo -e "${GREEN}✓${NC} Python version is compatible (3.8+)"
            return 0
        else
            echo -e "${YELLOW}!${NC} Python version is too old. ChromaDB requires Python 3.8+"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} Python3 is not installed"
        return 1
    fi
}

# Function to check ChromaDB installation
check_chromadb_install() {
    echo -e "\n${BLUE}Checking ChromaDB installation...${NC}"

    if python3 -c "import chromadb; print(f'ChromaDB version: {chromadb.__version__}')" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} ChromaDB is installed"
        python3 -c "import chromadb; print(f'  Version: {chromadb.__version__}')"
        return 0
    else
        echo -e "${RED}✗${NC} ChromaDB is not installed"
        return 1
    fi
}

# Function to check ChromaDB dependencies
check_dependencies() {
    echo -e "\n${BLUE}Checking ChromaDB dependencies...${NC}"

    DEPS=("numpy" "uvicorn" "fastapi" "pydantic" "onnxruntime")

    for dep in "${DEPS[@]}"; do
        if python3 -c "import $dep" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $dep is installed"
        else
            echo -e "${YELLOW}!${NC} $dep is not installed"
        fi
    done
}

# Function to test ChromaDB functionality
test_chromadb() {
    echo -e "\n${BLUE}Testing ChromaDB functionality...${NC}"

    # Test import and basic functionality
    python3 << 'EOF' 2>/dev/null
import chromadb
import tempfile
import os

try:
    # Test with temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a client
        client = chromadb.PersistentClient(path=tmpdir)

        # Create a collection
        collection = client.create_collection(name="test_collection")

        # Add some documents
        collection.add(
            documents=["This is a test document", "Another test document"],
            ids=["id1", "id2"]
        )

        # Query the collection
        results = collection.query(
            query_texts=["test"],
            n_results=2
        )

        print("✓ ChromaDB basic functionality test passed")
        print(f"  Created collection with {collection.count()} documents")

except Exception as e:
    print(f"✗ ChromaDB test failed: {e}")
    exit(1)
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} ChromaDB is working correctly"
        return 0
    else
        echo -e "${RED}✗${NC} ChromaDB functionality test failed"
        return 1
    fi
}

# Function to check if ChromaDB server can start
check_chromadb_server() {
    echo -e "\n${BLUE}Checking ChromaDB server capability...${NC}"

    # Check if chromadb.app module exists
    if python3 -c "import chromadb.app" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} ChromaDB server module is available"
        return 0
    else
        echo -e "${YELLOW}!${NC} ChromaDB server module not found"
        echo -e "   ChromaDB will run in client-only mode"
        return 1
    fi
}

# Function to check port availability
check_port() {
    echo -e "\n${BLUE}Checking port 8005 availability...${NC}"

    if lsof -i :8005 >/dev/null 2>&1; then
        echo -e "${YELLOW}!${NC} Port 8005 is already in use:"
        lsof -i :8005 | head -5
        return 1
    else
        echo -e "${GREEN}✓${NC} Port 8005 is available"
        return 0
    fi
}

# Function to fix ChromaDB installation
fix_chromadb() {
    echo -e "\n${BLUE}Attempting to fix ChromaDB installation...${NC}"

    # Update pip
    echo -e "${BLUE}Updating pip...${NC}"
    python3 -m pip install --upgrade pip

    # Try to install ChromaDB
    echo -e "${BLUE}Installing ChromaDB...${NC}"

    # Method 1: Standard installation
    if python3 -m pip install chromadb --no-cache-dir; then
        echo -e "${GREEN}✓${NC} ChromaDB installed successfully"
    else
        # Method 2: Install with --user flag
        echo -e "${YELLOW}Standard installation failed, trying with --user flag...${NC}"
        if python3 -m pip install --user chromadb --no-cache-dir; then
            echo -e "${GREEN}✓${NC} ChromaDB installed with --user flag"
        else
            # Method 3: Install minimal version
            echo -e "${YELLOW}Full installation failed, trying minimal installation...${NC}"
            python3 -m pip install --user chromadb-client --no-cache-dir || {
                echo -e "${RED}Failed to install ChromaDB${NC}"
                echo -e "\nTry manual installation:"
                echo -e "  1. Create virtual environment: python3 -m venv venv"
                echo -e "  2. Activate it: source venv/bin/activate"
                echo -e "  3. Install ChromaDB: pip install chromadb"
                return 1
            }
        fi
    fi

    # Install additional dependencies
    echo -e "${BLUE}Installing additional dependencies...${NC}"
    python3 -m pip install uvicorn fastapi pydantic numpy onnxruntime --no-cache-dir 2>/dev/null || true

    return 0
}

# Function to create ChromaDB service script
create_service_script() {
    echo -e "\n${BLUE}Creating ChromaDB service script...${NC}"

    cat > "$BASE_DIR/start_chromadb_service.sh" << 'EOF'
#!/bin/bash

# ChromaDB service startup script
BASE_DIR="/home/qwkj/drass"
DATA_DIR="$BASE_DIR/data/chromadb"
LOG_FILE="$BASE_DIR/logs/chromadb.log"
PID_FILE="$BASE_DIR/chromadb.pid"

# Create directories
mkdir -p "$DATA_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "ChromaDB is already running with PID $PID"
        exit 0
    fi
fi

echo "Starting ChromaDB service..."

# Try to start ChromaDB server
if python3 -c "import chromadb.app" 2>/dev/null; then
    # Server mode
    nohup python3 -m chromadb.app --path "$DATA_DIR" --port 8005 --host 0.0.0.0 > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "ChromaDB server started with PID $(cat $PID_FILE)"
else
    # Client mode with persistence
    nohup python3 << 'PYTHON_EOF' > "$LOG_FILE" 2>&1 &
import chromadb
import time
import sys
import os

# Setup ChromaDB client
chroma_path = os.environ.get("CHROMA_PATH", "/home/qwkj/drass/data/chromadb")
print(f"Starting ChromaDB client with path: {chroma_path}")

try:
    client = chromadb.PersistentClient(path=chroma_path)
    print(f"ChromaDB client initialized successfully")

    # Keep the process running
    while True:
        time.sleep(60)
        print("ChromaDB client is running...")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
PYTHON_EOF
    echo $! > "$PID_FILE"
    echo "ChromaDB client started with PID $(cat $PID_FILE)"
fi

# Wait a moment for service to start
sleep 3

# Check if service is running
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo "ChromaDB service started successfully"
    echo "Logs: tail -f $LOG_FILE"
else
    echo "Failed to start ChromaDB service"
    rm -f "$PID_FILE"
    exit 1
fi
EOF

    chmod +x "$BASE_DIR/start_chromadb_service.sh"
    echo -e "${GREEN}✓${NC} Service script created at $BASE_DIR/start_chromadb_service.sh"
}

# Main diagnostic flow
echo -e "\n${YELLOW}Running ChromaDB diagnostics...${NC}"

# Run checks
check_python
PYTHON_OK=$?

if [ $PYTHON_OK -eq 0 ]; then
    check_chromadb_install
    CHROMADB_OK=$?

    if [ $CHROMADB_OK -eq 0 ]; then
        check_dependencies
        test_chromadb
        check_chromadb_server
        check_port
    else
        echo -e "\n${YELLOW}ChromaDB is not installed. Installing...${NC}"
        fix_chromadb

        # Re-check after fix
        check_chromadb_install
        if [ $? -eq 0 ]; then
            test_chromadb
            check_chromadb_server
        fi
    fi
else
    echo -e "\n${RED}Python 3.8+ is required for ChromaDB${NC}"
    echo -e "Install Python 3.8 or higher:"
    echo -e "  sudo apt-get update"
    echo -e "  sudo apt-get install -y python3.9 python3.9-pip"
fi

# Create service script
create_service_script

# Final status
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Final Status:${NC}"
echo -e "${BLUE}========================================${NC}"

if check_chromadb_install >/dev/null 2>&1 && check_port >/dev/null 2>&1; then
    echo -e "${GREEN}✓ ChromaDB is ready to use${NC}"
    echo -e "\nStart ChromaDB with:"
    echo -e "  ${BLUE}$BASE_DIR/start_chromadb_service.sh${NC}"
    echo -e "\nOr manually:"
    echo -e "  ${BLUE}python3 -m chromadb.app --path $DATA_DIR/chromadb --port 8005 --host 0.0.0.0${NC}"
else
    echo -e "${YELLOW}⚠ ChromaDB requires attention${NC}"
    echo -e "\nCheck the diagnostic output above for issues"
fi