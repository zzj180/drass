#!/bin/bash

# Complete Local Deployment Script
# Sets up Ollama LLM and Local Embedding Service

set -e

echo "========================================"
echo "Complete Local AI Stack Deployment"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Step 1: Deploy Ollama
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Part 1: Deploying Ollama LLM${NC}"
echo -e "${BLUE}========================================${NC}"
bash "$SCRIPT_DIR/deploy_ollama.sh"

# Step 2: Deploy Embedding Service  
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Part 2: Deploying Embedding Service${NC}"
echo -e "${BLUE}========================================${NC}"
bash "$SCRIPT_DIR/deploy_local_embedding.sh"

# Step 3: Create combined environment file
echo -e "\n${YELLOW}Creating combined configuration...${NC}"
cat > "$PROJECT_ROOT/.env.local" << 'EOF'
# Local AI Stack Configuration
# Generated for local development

# === LLM Configuration (Ollama) ===
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
LLM_API_KEY=not-required
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
ENABLE_STREAMING=true

# === Embedding Configuration (Local) ===
EMBEDDING_PROVIDER=local
EMBEDDING_SERVICE_URL=http://localhost:8001
EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5
EMBEDDING_DIMENSION=768
MAX_SEQUENCE_LENGTH=512

# === Vector Store Configuration ===
VECTOR_STORE_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./data/chroma
CHROMA_COLLECTION_NAME=compliance_docs

# === Application Settings ===
ENABLE_AGENT=true
ENABLE_MEMORY=true
ENABLE_CACHE=true

# === API Configuration ===
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# === Database Configuration ===
DATABASE_URL=postgresql://postgres:password@localhost:5432/compliance_db
REDIS_URL=redis://localhost:6379/0

# === Security ===
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# === Monitoring ===
LOG_LEVEL=INFO
ENABLE_METRICS=true
EOF

echo -e "${GREEN}✓ Combined configuration created${NC}"

# Step 4: Create startup script
echo -e "\n${YELLOW}Creating startup script...${NC}"
cat > "$PROJECT_ROOT/start_local.sh" << 'EOF'
#!/bin/bash

# Start all local services

echo "Starting Local AI Stack..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get project root
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to check if port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
}

# 1. Start Ollama
echo -e "\n${YELLOW}Starting Ollama...${NC}"
if ! check_port 11434; then
    ollama serve > /dev/null 2>&1 &
    sleep 3
    echo -e "${GREEN}✓ Ollama started${NC}"
else
    echo -e "${GREEN}✓ Ollama already running${NC}"
fi

# 2. Start Embedding Service
echo -e "\n${YELLOW}Starting Embedding Service...${NC}"
if ! check_port 8001; then
    cd "$PROJECT_ROOT/services/embedding-service"
    source venv/bin/activate
    nohup python local_app.py > embedding.log 2>&1 &
    cd "$PROJECT_ROOT"
    sleep 5
    echo -e "${GREEN}✓ Embedding service started${NC}"
else
    echo -e "${GREEN}✓ Embedding service already running${NC}"
fi

# 3. Start Main Application
echo -e "\n${YELLOW}Starting Main Application...${NC}"
if ! check_port 8000; then
    cd "$PROJECT_ROOT/services/main-app"
    source .env.local
    uvicorn app.main:app --reload --port 8000 &
    cd "$PROJECT_ROOT"
    echo -e "${GREEN}✓ Main application started${NC}"
else
    echo -e "${GREEN}✓ Main application already running${NC}"
fi

# 4. Start Frontend
echo -e "\n${YELLOW}Starting Frontend...${NC}"
if ! check_port 5173; then
    cd "$PROJECT_ROOT/frontend"
    npm run dev &
    cd "$PROJECT_ROOT"
    echo -e "${GREEN}✓ Frontend started${NC}"
else
    echo -e "${GREEN}✓ Frontend already running${NC}"
fi

echo -e "\n${GREEN}========================================"
echo "All services started successfully!"
echo "========================================${NC}"
echo ""
echo "Services:"
echo "  Ollama LLM:        http://localhost:11434"
echo "  Embedding Service: http://localhost:8001"
echo "  Backend API:       http://localhost:8000"
echo "  Frontend:          http://localhost:5173"
echo ""
echo "To stop all services, run: ./stop_local.sh"
EOF

chmod +x "$PROJECT_ROOT/start_local.sh"
echo -e "${GREEN}✓ Startup script created${NC}"

# Step 5: Create stop script
echo -e "\n${YELLOW}Creating stop script...${NC}"
cat > "$PROJECT_ROOT/stop_local.sh" << 'EOF'
#!/bin/bash

# Stop all local services

echo "Stopping Local AI Stack..."

# Kill services by port
for PORT in 11434 8001 8000 5173; do
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        kill $PID 2>/dev/null
        echo "✓ Stopped service on port $PORT"
    fi
done

echo "All services stopped."
EOF

chmod +x "$PROJECT_ROOT/stop_local.sh"
echo -e "${GREEN}✓ Stop script created${NC}"

# Step 6: Create test script
echo -e "\n${YELLOW}Creating comprehensive test script...${NC}"
cat > "$PROJECT_ROOT/test_local_stack.sh" << 'EOF'
#!/bin/bash

# Test all local services

echo "========================================"
echo "Testing Local AI Stack"
echo "========================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

# Test Ollama
echo -e "\n${YELLOW}Testing Ollama LLM...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Ollama is not accessible${NC}"
    ((TESTS_FAILED++))
fi

# Test Embedding Service
echo -e "\n${YELLOW}Testing Embedding Service...${NC}"
if curl -s http://localhost:8001/health > /dev/null; then
    echo -e "${GREEN}✓ Embedding service is running${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Embedding service is not accessible${NC}"
    ((TESTS_FAILED++))
fi

# Test Backend API
echo -e "\n${YELLOW}Testing Backend API...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ Backend API is running${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Backend API is not accessible${NC}"
    ((TESTS_FAILED++))
fi

# Test Frontend
echo -e "\n${YELLOW}Testing Frontend...${NC}"
if curl -s http://localhost:5173 > /dev/null; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Frontend is not accessible${NC}"
    ((TESTS_FAILED++))
fi

# Summary
echo -e "\n========================================"
echo "Test Results:"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All services are operational!${NC}"
else
    echo -e "\n${RED}✗ Some services are not running${NC}"
    echo "Run ./start_local.sh to start all services"
fi
EOF

chmod +x "$PROJECT_ROOT/test_local_stack.sh"
echo -e "${GREEN}✓ Test script created${NC}"

# Final summary
echo -e "\n${GREEN}========================================"
echo "Local AI Stack Deployment Complete!"
echo "========================================${NC}"
echo ""
echo "Configuration files created:"
echo "  - .env.local (combined configuration)"
echo "  - config/ollama.env (Ollama settings)"
echo "  - config/embedding.env (Embedding settings)"
echo ""
echo "Scripts created:"
echo "  - start_local.sh (start all services)"
echo "  - stop_local.sh (stop all services)"
echo "  - test_local_stack.sh (test all services)"
echo ""
echo "Quick Start:"
echo "  1. Run: ./start_local.sh"
echo "  2. Visit: http://localhost:5173"
echo ""
echo "To test the setup:"
echo "  ./test_local_stack.sh"
echo ""
echo -e "${GREEN}✓ Your local AI stack is ready!${NC}"