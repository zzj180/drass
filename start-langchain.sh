#!/bin/bash

# LangChain Compliance Assistant - One-Click Startup Script
# This script starts all services needed for local UI testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_COMPOSE_FILE="docker-compose.langchain.yml"
ENV_FILE=".env"
FRONTEND_DIR="frontend"
BACKEND_DIR="services/main-app"
LLM_SERVER_SCRIPT="qwen3_api_server.py"

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    print_message "$YELLOW" "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
            print_message "$GREEN" "✅ $service_name is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_message "$RED" "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Function to start local LLM server
start_llm_server() {
    if port_in_use 8001; then
        print_message "$YELLOW" "⚠️  LLM server already running on port 8001"
    else
        if [ -f "$LLM_SERVER_SCRIPT" ]; then
            print_message "$BLUE" "🚀 Starting local LLM server (Qwen3-8B-MLX)..."
            python "$LLM_SERVER_SCRIPT" > logs/llm_server.log 2>&1 &
            LLM_PID=$!
            echo $LLM_PID > .llm_server.pid
            sleep 5
            wait_for_service "http://localhost:8001/health" "Local LLM Server"
        else
            print_message "$YELLOW" "⚠️  Local LLM server script not found. Using cloud LLM providers..."
        fi
    fi
}

# Function to setup environment
setup_environment() {
    print_message "$BLUE" "🔧 Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        print_message "$YELLOW" "📝 Creating .env file from template..."
        cat > "$ENV_FILE" << EOF
# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_BASE=http://localhost:8001/v1
LLM_MODEL=qwen3-8b-mlx
LLM_API_KEY=none

# Alternative LLM Providers (optional)
OPENROUTER_API_KEY=
ANTHROPIC_API_KEY=

# Database
DATABASE_URL=postgresql://langchain:langchain123@localhost:5432/langchain_db
REDIS_URL=redis://localhost:6379

# Vector Store
VECTOR_STORE_TYPE=chromadb
CHROMA_SERVER_HOST=localhost
CHROMA_SERVER_PORT=8005

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-change-in-production

# Features
ENABLE_STREAMING=true
ENABLE_AGENT=true
ENABLE_MEMORY=true
EOF
        print_message "$GREEN" "✅ .env file created"
    else
        print_message "$GREEN" "✅ .env file already exists"
    fi
    
    # Create necessary directories
    mkdir -p logs data/uploads data/documents data/processed models/embeddings models/reranking
}

# Function to install dependencies
install_dependencies() {
    print_message "$BLUE" "📦 Installing dependencies..."
    
    # Check Python dependencies for backend
    if [ -d "$BACKEND_DIR" ]; then
        cd "$BACKEND_DIR"
        if [ -f "requirements.txt" ]; then
            print_message "$YELLOW" "Installing backend dependencies..."
            pip install -q -r requirements.txt
        fi
        cd - > /dev/null
    fi
    
    # Check Node dependencies for frontend
    if [ -d "$FRONTEND_DIR" ]; then
        cd "$FRONTEND_DIR"
        if [ -f "package.json" ] && [ ! -d "node_modules" ]; then
            print_message "$YELLOW" "Installing frontend dependencies..."
            npm install --silent
        fi
        cd - > /dev/null
    fi
}

# Function to start infrastructure services
start_infrastructure() {
    print_message "$BLUE" "🏗️  Starting infrastructure services..."
    
    # Start only core services first
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres redis chromadb
    
    # Wait for services to be ready
    wait_for_service "http://localhost:8005/api/v1" "ChromaDB"
    
    print_message "$GREEN" "✅ Infrastructure services started"
}

# Function to start microservices
start_microservices() {
    print_message "$BLUE" "🎯 Starting microservices..."
    
    # Start document processor
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d doc-processor
    
    # Start embedding service
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d embedding-service
    
    # Start reranking service (if available)
    if [ -d "services/reranking-service" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d reranking-service
    fi
    
    # Optional: Start LLM gateway
    if [ -d "services/llm-gateway" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d llm-gateway
    fi
    
    print_message "$GREEN" "✅ Microservices started"
}

# Function to start main application
start_application() {
    print_message "$BLUE" "🚀 Starting main application..."
    
    # Start backend
    if [ -d "$BACKEND_DIR" ]; then
        cd "$BACKEND_DIR"
        print_message "$YELLOW" "Starting FastAPI backend..."
        uvicorn app.main:app --reload --port 8000 --host 0.0.0.0 > ../../logs/backend.log 2>&1 &
        BACKEND_PID=$!
        echo $BACKEND_PID > ../../.backend.pid
        cd - > /dev/null
        
        wait_for_service "http://localhost:8000/health" "Backend API"
    fi
    
    # Start frontend
    if [ -d "$FRONTEND_DIR" ]; then
        cd "$FRONTEND_DIR"
        print_message "$YELLOW" "Starting React frontend..."
        npm run dev > ../logs/frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > ../.frontend.pid
        cd - > /dev/null
        
        wait_for_service "http://localhost:5173" "Frontend"
    fi
    
    print_message "$GREEN" "✅ Application started"
}

# Function to show status
show_status() {
    print_message "$GREEN" "\n========================================="
    print_message "$GREEN" "🎉 LangChain Compliance Assistant Started!"
    print_message "$GREEN" "========================================="
    print_message "$BLUE" "\n📌 Service URLs:"
    print_message "$NC" "  • Frontend:          http://localhost:5173"
    print_message "$NC" "  • Backend API:       http://localhost:8000"
    print_message "$NC" "  • API Documentation: http://localhost:8000/docs"
    print_message "$NC" "  • ChromaDB:          http://localhost:8005"
    
    if port_in_use 8001; then
        print_message "$NC" "  • Local LLM:         http://localhost:8001"
    fi
    
    if port_in_use 8003; then
        print_message "$NC" "  • LLM Gateway:       http://localhost:8003"
    fi
    
    print_message "$BLUE" "\n📊 Service Status:"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    print_message "$YELLOW" "\n💡 Tips:"
    print_message "$NC" "  • View logs:         ./start-langchain.sh logs"
    print_message "$NC" "  • Stop services:     ./start-langchain.sh stop"
    print_message "$NC" "  • Restart services:  ./start-langchain.sh restart"
    print_message "$NC" "  • Clean everything:  ./start-langchain.sh clean"
}

# Function to stop all services
stop_services() {
    print_message "$YELLOW" "🛑 Stopping all services..."
    
    # Stop Docker services
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    
    # Stop local processes
    if [ -f .llm_server.pid ]; then
        kill $(cat .llm_server.pid) 2>/dev/null || true
        rm .llm_server.pid
    fi
    
    if [ -f .backend.pid ]; then
        kill $(cat .backend.pid) 2>/dev/null || true
        rm .backend.pid
    fi
    
    if [ -f .frontend.pid ]; then
        kill $(cat .frontend.pid) 2>/dev/null || true
        rm .frontend.pid
    fi
    
    print_message "$GREEN" "✅ All services stopped"
}

# Function to show logs
show_logs() {
    case "$1" in
        backend)
            tail -f logs/backend.log
            ;;
        frontend)
            tail -f logs/frontend.log
            ;;
        llm)
            tail -f logs/llm_server.log
            ;;
        docker)
            docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f
            ;;
        *)
            print_message "$YELLOW" "Available logs: backend, frontend, llm, docker"
            ;;
    esac
}

# Function to clean everything
clean_all() {
    print_message "$RED" "🧹 Cleaning all data and volumes..."
    
    stop_services
    
    # Remove Docker volumes
    docker-compose -f "$DOCKER_COMPOSE_FILE" down -v
    
    # Clean local data
    rm -rf data/* logs/* .*.pid
    
    print_message "$GREEN" "✅ Cleanup complete"
}

# Main execution
main() {
    case "$1" in
        start)
            print_message "$BLUE" "🚀 Starting LangChain Compliance Assistant..."
            setup_environment
            install_dependencies
            start_llm_server
            start_infrastructure
            start_microservices
            start_application
            show_status
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            sleep 2
            main start
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        clean)
            clean_all
            ;;
        *)
            print_message "$BLUE" "LangChain Compliance Assistant - One-Click Startup"
            print_message "$NC" "\nUsage: $0 {start|stop|restart|status|logs|clean}"
            print_message "$NC" "\nCommands:"
            print_message "$NC" "  start    - Start all services"
            print_message "$NC" "  stop     - Stop all services"
            print_message "$NC" "  restart  - Restart all services"
            print_message "$NC" "  status   - Show service status"
            print_message "$NC" "  logs     - Show logs (backend|frontend|llm|docker)"
            print_message "$NC" "  clean    - Clean all data and volumes"
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    local missing=()
    
    command_exists docker || missing+=("docker")
    command_exists docker-compose || missing+=("docker-compose")
    command_exists python || missing+=("python")
    command_exists pip || missing+=("pip")
    command_exists node || missing+=("node")
    command_exists npm || missing+=("npm")
    
    if [ ${#missing[@]} -ne 0 ]; then
        print_message "$RED" "❌ Missing prerequisites: ${missing[*]}"
        print_message "$YELLOW" "Please install the missing tools and try again."
        exit 1
    fi
}

# Run checks and main function
check_prerequisites
main "$@"