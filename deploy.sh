#!/bin/bash

# Drass Dify Platform - One-Click Deployment Script
# Based on official Dify documentation: https://docs.dify.ai/zh-hans/getting-started/install-self-hosted/docker-compose

set -e

echo "🚀 Drass Dify Platform - One-Click Deployment"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check prerequisites
print_status "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    print_status "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    print_status "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check Docker daemon
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi

print_success "Prerequisites check passed"

# Check available memory
print_status "Checking available memory..."
MEMORY_GB=$(docker system info --format '{{.MemTotal}}' | awk '{print int($1/1024/1024/1024)}')
if [ "$MEMORY_GB" -lt 4 ]; then
    print_warning "Available memory is ${MEMORY_GB}GB. Dify requires at least 4GB."
    print_warning "Consider increasing Docker memory allocation."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "Available memory: ${MEMORY_GB}GB"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data/{api,worker,web}
mkdir -p config/{dify,web}
mkdir -p logs
mkdir -p nginx/ssl

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_status "Creating environment configuration..."
    source venv/bin/activate && python scripts/dify-deploy.py --config config/dify-config.yaml
else
    print_warning ".env file already exists. Using existing configuration."
fi

# Deploy Dify platform
print_status "Deploying Dify platform..."
if source venv/bin/activate && python scripts/dify-deploy.py --config config/dify-config.yaml; then
    print_success "Dify platform deployment completed!"
else
    print_error "Dify platform deployment failed!"
    exit 1
fi

# Show final status
echo ""
print_status "Deployment completed successfully!"
echo ""
echo "🌐 Access your Dify platform:"
echo "   - Main Platform: http://localhost"
echo "   - Admin Setup: http://localhost/install"
echo "   - API Documentation: http://localhost/v1"
echo ""
echo "👤 Default Admin Account:"
echo "   - Email: admin@drass.local"
echo "   - Password: admin123"
echo ""
echo "📊 Optional Monitoring:"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "🔧 Management Commands:"
echo "   - View status: docker-compose ps"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Restart: docker-compose restart"
echo ""
print_success "Your Drass Dify platform is ready to use!"
print_warning "Remember to change default passwords in production!"
