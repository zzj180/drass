#!/bin/bash

# Debug script to understand what's happening during API startup

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_DIR="/home/qwkj/drass"
LOG_DIR="$BASE_DIR/logs"

echo -e "${BLUE}=== API Startup Debug ===${NC}"
echo "Date: $(date)"
echo ""

# 1. Check directory structure
echo -e "${BLUE}1. Directory Structure:${NC}"
echo "BASE_DIR: $BASE_DIR"
echo "Current working directory: $(pwd)"
echo ""

# 2. Check what Python files exist
echo -e "${BLUE}2. Python files in BASE_DIR:${NC}"
ls -la $BASE_DIR/*.py 2>/dev/null || echo "No .py files in $BASE_DIR"
echo ""

echo -e "${BLUE}3. Check services/main-app directory:${NC}"
if [ -d "$BASE_DIR/services/main-app" ]; then
    echo "Directory exists"
    echo "Contents:"
    ls -la "$BASE_DIR/services/main-app/" | head -20
    echo ""
    echo "app/ directory:"
    ls -la "$BASE_DIR/services/main-app/app/" | head -10
else
    echo "Directory does not exist!"
fi
echo ""

# 4. Check Python path and imports
echo -e "${BLUE}4. Python Environment:${NC}"
echo "Python version: $(python3 --version)"
echo "Python path:"
python3 -c "import sys; print('\n'.join(sys.path))"
echo ""

# 5. Test what happens when we try to run standalone_api.py
echo -e "${BLUE}5. Test importing standalone_api.py:${NC}"
cd $BASE_DIR
if [ -f "standalone_api.py" ]; then
    echo "standalone_api.py exists"
    echo "First 20 lines:"
    head -20 standalone_api.py
    echo ""
    echo "Testing if it runs:"
    python3 -c "import standalone_api" 2>&1 | head -5 || echo "Import test done"
else
    echo "standalone_api.py NOT FOUND!"
fi
echo ""

# 6. Check what simple_api.py is
echo -e "${BLUE}6. Check simple_api.py:${NC}"
if [ -f "$BASE_DIR/simple_api.py" ]; then
    echo "simple_api.py exists"
    echo "File size: $(stat -c%s simple_api.py 2>/dev/null || stat -f%z simple_api.py 2>/dev/null) bytes"
    echo "First 20 lines:"
    head -20 simple_api.py
else
    echo "simple_api.py NOT FOUND!"
fi
echo ""

# 7. Check if there's a __main__.py or something that redirects
echo -e "${BLUE}7. Check for __main__.py:${NC}"
find $BASE_DIR -name "__main__.py" -type f 2>/dev/null | head -5
echo ""

# 8. Test what actually runs
echo -e "${BLUE}8. Test what Python actually runs:${NC}"
cd $BASE_DIR
echo "Running: python3 -c \"import sys; print('Args:', sys.argv); print('File:', __file__ if '__file__' in globals() else 'N/A')\""
python3 -c "import sys; print('Args:', sys.argv); print('File:', __file__ if '__file__' in globals() else 'N/A')"
echo ""

# 9. Check environment variables
echo -e "${BLUE}9. Environment variables:${NC}"
echo "PYTHONPATH: ${PYTHONPATH:-not set}"
echo "PORT: ${PORT:-not set}"
echo "LLM_PROVIDER: ${LLM_PROVIDER:-not set}"
echo ""

# 10. Check what happens with explicit module run
echo -e "${BLUE}10. Test running app.main directly:${NC}"
cd $BASE_DIR/services/main-app
echo "Current dir: $(pwd)"
echo "Testing: python3 -c \"from app.main import app; print('App imported successfully')\""
python3 -c "from app.main import app; print('App imported successfully')" 2>&1 | head -5 || echo "Import failed"
echo ""

echo -e "${BLUE}=== Debug Complete ===${NC}"