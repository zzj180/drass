#!/bin/bash

# ==================================================
# Drass LangChain Compliance Assistant - Quick Start Script
# ==================================================
# This script helps you quickly set up and run the project on macOS
# Usage: ./quick_start.sh [command]
# Commands: setup, start, stop, restart, status, logs, clean

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
BACKEND_DIR="${PROJECT_ROOT}/services/main-app"
DATA_DIR="${PROJECT_ROOT}/data"

# Print colored message
print_message() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Check system requirements
check_requirements() {
    print_message $BLUE "🔍 Checking system requirements..."
    
    local missing_deps=()
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("Python 3.11+")
    else
        python_version=$(python3 --version | cut -d' ' -f2)
        print_message $GREEN "✓ Python ${python_version} found"
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        missing_deps+=("Node.js 18+")
    else
        node_version=$(node --version)
        print_message $GREEN "✓ Node.js ${node_version} found"
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("Docker")
    else
        docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_message $GREEN "✓ Docker ${docker_version} found"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_deps+=("Docker Compose")
    else
        print_message $GREEN "✓ Docker Compose found"
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_message $RED "❌ Missing dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        echo ""
        print_message $YELLOW "📦 Install missing dependencies:"
        echo "  brew install python@3.11 node docker docker-compose"
        exit 1
    fi
    
    print_message $GREEN "✅ All requirements satisfied!"
}

# Setup environment
setup_environment() {
    print_message $BLUE "🔧 Setting up environment..."
    
    # Create .env file if not exists
    if [ ! -f "${PROJECT_ROOT}/.env" ]; then
        cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
        print_message $YELLOW "📝 Created .env file from .env.example"
        print_message $YELLOW "⚠️  Please edit .env and add your API keys:"
        echo "    - OPENROUTER_API_KEY or OPENAI_API_KEY"
        echo "    - Other service API keys as needed"
        echo ""
        read -p "Press Enter after updating .env file to continue..."
    else
        print_message $GREEN "✓ .env file exists"
    fi
    
    # Create data directories
    mkdir -p "${DATA_DIR}/uploads"
    mkdir -p "${DATA_DIR}/chroma"
    mkdir -p "${DATA_DIR}/api"
    print_message $GREEN "✓ Data directories created"
}

# Install dependencies
install_dependencies() {
    print_message $BLUE "📦 Installing dependencies..."
    
    # Install Python dependencies
    print_message $YELLOW "Installing Python packages..."
    cd "${BACKEND_DIR}"
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_message $GREEN "✓ Python virtual environment created"
    fi
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    print_message $GREEN "✓ Python dependencies installed"
    
    # Install Node dependencies
    print_message $YELLOW "Installing Node packages..."
    cd "${FRONTEND_DIR}"
    npm install
    print_message $GREEN "✓ Node dependencies installed"
    
    cd "${PROJECT_ROOT}"
}

# Start Docker services
start_docker() {
    print_message $BLUE "🐳 Starting Docker services..."
    
    # Check if services are already running
    if docker-compose ps | grep -q "Up"; then
        print_message $YELLOW "⚠️  Some Docker services are already running"
        read -p "Do you want to restart them? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down
            sleep 2
        else
            return
        fi
    fi
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    print_message $YELLOW "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    if docker-compose ps | grep -q "Exit"; then
        print_message $RED "❌ Some services failed to start"
        docker-compose logs --tail=50
        exit 1
    fi
    
    print_message $GREEN "✅ Docker services started successfully"
}

# Start backend API
start_backend() {
    print_message $BLUE "🚀 Starting backend API..."
    
    cd "${BACKEND_DIR}"
    source venv/bin/activate
    
    # Export environment variables
    export $(grep -v '^#' "${PROJECT_ROOT}/.env" | xargs)
    
    # Start FastAPI in background
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "${DATA_DIR}/backend.log" 2>&1 &
    echo $! > "${DATA_DIR}/backend.pid"
    
    sleep 5
    
    # Check if backend started
    if curl -s http://localhost:8000/health > /dev/null; then
        print_message $GREEN "✅ Backend API started on http://localhost:8000"
        print_message $YELLOW "📚 API docs available at http://localhost:8000/docs"
    else
        print_message $RED "❌ Backend failed to start"
        tail -n 50 "${DATA_DIR}/backend.log"
        exit 1
    fi
    
    cd "${PROJECT_ROOT}"
}

# Start frontend
start_frontend() {
    print_message $BLUE "🎨 Starting frontend..."
    
    cd "${FRONTEND_DIR}"
    
    # Start Vite dev server in background
    nohup npm run dev > "${DATA_DIR}/frontend.log" 2>&1 &
    echo $! > "${DATA_DIR}/frontend.pid"
    
    sleep 5
    
    print_message $GREEN "✅ Frontend started on http://localhost:5173"
    
    cd "${PROJECT_ROOT}"
}

# Stop all services
stop_all() {
    print_message $BLUE "🛑 Stopping all services..."
    
    # Stop frontend
    if [ -f "${DATA_DIR}/frontend.pid" ]; then
        kill $(cat "${DATA_DIR}/frontend.pid") 2>/dev/null || true
        rm "${DATA_DIR}/frontend.pid"
        print_message $GREEN "✓ Frontend stopped"
    fi
    
    # Stop backend
    if [ -f "${DATA_DIR}/backend.pid" ]; then
        kill $(cat "${DATA_DIR}/backend.pid") 2>/dev/null || true
        rm "${DATA_DIR}/backend.pid"
        print_message $GREEN "✓ Backend stopped"
    fi
    
    # Stop Docker services
    docker-compose down
    print_message $GREEN "✓ Docker services stopped"
    
    print_message $GREEN "✅ All services stopped"
}

# Check service status
check_status() {
    print_message $BLUE "📊 Service Status:"
    echo ""
    
    # Docker services
    print_message $YELLOW "Docker Services:"
    docker-compose ps
    echo ""
    
    # Backend API
    if [ -f "${DATA_DIR}/backend.pid" ] && kill -0 $(cat "${DATA_DIR}/backend.pid") 2>/dev/null; then
        print_message $GREEN "✓ Backend API: Running (PID: $(cat ${DATA_DIR}/backend.pid))"
        curl -s http://localhost:8000/health > /dev/null && print_message $GREEN "  Health check: OK" || print_message $RED "  Health check: Failed"
    else
        print_message $RED "✗ Backend API: Not running"
    fi
    
    # Frontend
    if [ -f "${DATA_DIR}/frontend.pid" ] && kill -0 $(cat "${DATA_DIR}/frontend.pid") 2>/dev/null; then
        print_message $GREEN "✓ Frontend: Running (PID: $(cat ${DATA_DIR}/frontend.pid))"
    else
        print_message $RED "✗ Frontend: Not running"
    fi
    
    echo ""
    print_message $BLUE "📍 URLs:"
    echo "  Frontend: http://localhost:5173"
    echo "  Backend API: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo "  Dify Platform: http://localhost"
}

# Show logs
show_logs() {
    local service=$1
    
    case $service in
        backend)
            print_message $BLUE "📋 Backend logs:"
            tail -f "${DATA_DIR}/backend.log"
            ;;
        frontend)
            print_message $BLUE "📋 Frontend logs:"
            tail -f "${DATA_DIR}/frontend.log"
            ;;
        docker)
            print_message $BLUE "📋 Docker logs:"
            docker-compose logs -f --tail=100
            ;;
        *)
            print_message $YELLOW "Usage: $0 logs [backend|frontend|docker]"
            ;;
    esac
}

# Clean up
cleanup() {
    print_message $BLUE "🧹 Cleaning up..."
    
    stop_all
    
    # Remove data files (optional)
    read -p "Do you want to remove all data files? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "${DATA_DIR}"
        docker-compose down -v
        print_message $GREEN "✓ Data files removed"
    fi
    
    print_message $GREEN "✅ Cleanup complete"
}

# Main execution
main() {
    case ${1:-} in
        setup)
            check_requirements
            setup_environment
            install_dependencies
            print_message $GREEN "✅ Setup complete! Run './quick_start.sh start' to launch the application"
            ;;
        start)
            check_requirements
            setup_environment
            start_docker
            start_backend
            start_frontend
            echo ""
            print_message $GREEN "🎉 Application started successfully!"
            print_message $BLUE "🌐 Access the application at:"
            echo "  - Frontend: http://localhost:5173"
            echo "  - API Docs: http://localhost:8000/docs"
            echo ""
            print_message $YELLOW "💡 Tips:"
            echo "  - Run './quick_start.sh status' to check service status"
            echo "  - Run './quick_start.sh logs [service]' to view logs"
            echo "  - Run './quick_start.sh stop' to stop all services"
            ;;
        stop)
            stop_all
            ;;
        restart)
            stop_all
            sleep 2
            main start
            ;;
        status)
            check_status
            ;;
        logs)
            show_logs ${2:-docker}
            ;;
        clean)
            cleanup
            ;;
        *)
            print_message $BLUE "🚀 Drass Quick Start Script"
            echo ""
            print_message $YELLOW "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  setup    - Install dependencies and configure environment"
            echo "  start    - Start all services"
            echo "  stop     - Stop all services"
            echo "  restart  - Restart all services"
            echo "  status   - Check service status"
            echo "  logs     - Show logs (backend|frontend|docker)"
            echo "  clean    - Stop services and clean up data"
            echo ""
            echo "Quick start:"
            echo "  1. ./quick_start.sh setup"
            echo "  2. Edit .env file with your API keys"
            echo "  3. ./quick_start.sh start"
            ;;
    esac
}

# Run main function
main "$@"