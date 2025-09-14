#!/bin/bash
# Deployment script for Reranking Service
# Handles deployment with health checks and rollback support

set -e

# Configuration
SERVICE_NAME="reranking-service"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=${1:-.env}
DEPLOYMENT_MODE=${2:-rolling}  # rolling, recreate, blue-green

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Header
echo "=========================================="
echo "🚀 Deploying Reranking Service"
echo "=========================================="
echo "Service: $SERVICE_NAME"
echo "Mode: $DEPLOYMENT_MODE"
echo "Environment: $ENV_FILE"
echo "=========================================="

# Check prerequisites
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

if ! docker-compose version > /dev/null 2>&1; then
    print_error "docker-compose is not installed."
    exit 1
fi

# Check environment file
if [[ ! -f "$ENV_FILE" ]]; then
    print_warning "Environment file $ENV_FILE not found. Using defaults."
    ENV_FILE=""
fi

# Save current state for rollback
print_status "Saving current state for rollback..."
CURRENT_IMAGE=$(docker-compose ps -q $SERVICE_NAME 2>/dev/null || echo "")
if [[ -n "$CURRENT_IMAGE" ]]; then
    CURRENT_IMAGE_ID=$(docker inspect --format='{{.Image}}' $CURRENT_IMAGE)
    echo "$CURRENT_IMAGE_ID" > .rollback_state_$SERVICE_NAME
    print_success "Current state saved"
fi

# Deployment based on mode
case $DEPLOYMENT_MODE in
    rolling)
        echo ""
        echo "=========================================="
        echo "📦 Rolling Deployment"
        echo "=========================================="

        # Pull latest image
        print_status "Pulling latest image..."
        docker-compose pull $SERVICE_NAME

        # Stop current service
        print_status "Stopping current service..."
        docker-compose stop $SERVICE_NAME

        # Start new service
        print_status "Starting new service..."
        if [[ -n "$ENV_FILE" ]]; then
            docker-compose --env-file $ENV_FILE up -d $SERVICE_NAME
        else
            docker-compose up -d $SERVICE_NAME
        fi
        ;;

    recreate)
        echo ""
        echo "=========================================="
        echo "🔄 Recreate Deployment"
        echo "=========================================="

        # Remove and recreate
        print_status "Removing current container..."
        docker-compose rm -f -s $SERVICE_NAME

        print_status "Creating new container..."
        if [[ -n "$ENV_FILE" ]]; then
            docker-compose --env-file $ENV_FILE up -d $SERVICE_NAME
        else
            docker-compose up -d $SERVICE_NAME
        fi
        ;;

    blue-green)
        echo ""
        echo "=========================================="
        echo "🔵🟢 Blue-Green Deployment"
        echo "=========================================="

        # Create new container with different name
        print_status "Starting green container..."
        docker-compose run -d --name ${SERVICE_NAME}-green \
            -p 8005:8002 \
            --rm \
            $SERVICE_NAME

        # Wait for green to be healthy
        print_status "Waiting for green container to be healthy..."
        sleep 30

        if curl -f http://localhost:8005/health > /dev/null 2>&1; then
            print_success "Green container is healthy"

            # Switch traffic (would need load balancer in production)
            print_status "Switching traffic to green..."
            docker-compose stop $SERVICE_NAME
            docker rename ${SERVICE_NAME}-green langchain-reranking

            print_success "Traffic switched to green container"
        else
            print_error "Green container health check failed"
            docker stop ${SERVICE_NAME}-green
            exit 1
        fi
        ;;

    *)
        print_error "Unknown deployment mode: $DEPLOYMENT_MODE"
        exit 1
        ;;
esac

# Wait for service to be ready
echo ""
echo "=========================================="
echo "🏥 Health Check"
echo "=========================================="

print_status "Waiting for service to be ready..."
MAX_ATTEMPTS=20
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -sf http://localhost:8004/health > /dev/null 2>&1; then
        print_success "Service is healthy!"

        # Display health status
        echo ""
        echo "Health Status:"
        curl -s http://localhost:8004/health | python3 -m json.tool | head -20
        break
    else
        ATTEMPT=$((ATTEMPT + 1))
        if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
            print_error "Service failed to become healthy after $MAX_ATTEMPTS attempts"

            # Show logs for debugging
            echo ""
            echo "Service Logs:"
            docker-compose logs --tail=50 $SERVICE_NAME

            # Ask for rollback
            read -p "Do you want to rollback? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                ./scripts/rollback-reranking.sh
            fi
            exit 1
        fi

        echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: Service not ready yet..."
        sleep 5
    fi
done

# Verify functionality
echo ""
echo "=========================================="
echo "✅ Verification"
echo "=========================================="

print_status "Testing rerank endpoint..."
TEST_RESPONSE=$(curl -s -X POST http://localhost:8004/rerank \
    -H "Content-Type: application/json" \
    -d '{
        "query": "test query",
        "documents": ["doc1", "doc2", "doc3"],
        "top_k": 2
    }' 2>/dev/null || echo "failed")

if [[ "$TEST_RESPONSE" != "failed" ]] && [[ "$TEST_RESPONSE" == *"reranked_documents"* ]]; then
    print_success "Rerank endpoint is working!"
else
    print_warning "Rerank endpoint test failed (model may still be loading)"
fi

# Cleanup old images
print_status "Cleaning up old images..."
docker image prune -f > /dev/null 2>&1

# Summary
echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo "Service: $SERVICE_NAME"
echo "Status: Running"
echo "Health: http://localhost:8004/health"
echo "Metrics: http://localhost:8004/metrics"
echo ""
echo "Container Info:"
docker-compose ps $SERVICE_NAME
echo ""
echo "Commands:"
echo "  - Logs: docker-compose logs -f $SERVICE_NAME"
echo "  - Stop: docker-compose stop $SERVICE_NAME"
echo "  - Rollback: ./scripts/rollback-reranking.sh"
echo "=========================================="