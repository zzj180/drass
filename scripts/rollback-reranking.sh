#!/bin/bash
# Rollback script for Reranking Service
# Quickly reverts to previous working version

set -e

# Configuration
SERVICE_NAME="reranking-service"
IMAGE_NAME="drass-reranking-service"
ROLLBACK_TAG=${1:-previous}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
echo "🔄 Rolling Back Reranking Service"
echo "=========================================="
echo "Service: $SERVICE_NAME"
echo "Rollback to: $ROLLBACK_TAG"
echo "=========================================="

# Check if rollback state exists
ROLLBACK_STATE_FILE=".rollback_state_$SERVICE_NAME"
if [[ -f "$ROLLBACK_STATE_FILE" ]]; then
    ROLLBACK_IMAGE=$(cat $ROLLBACK_STATE_FILE)
    print_status "Found rollback state: $ROLLBACK_IMAGE"
else
    print_warning "No rollback state found. Using tag: $ROLLBACK_TAG"
fi

# Stop current service
print_status "Stopping current service..."
docker-compose stop $SERVICE_NAME

# Rollback method 1: Use saved state
if [[ -n "$ROLLBACK_IMAGE" ]]; then
    print_status "Rolling back to saved image..."
    docker tag $ROLLBACK_IMAGE $IMAGE_NAME:latest
    docker-compose up -d $SERVICE_NAME
else
    # Rollback method 2: Use previous tag
    print_status "Rolling back to $IMAGE_NAME:$ROLLBACK_TAG..."

    # Check if image exists
    if docker image inspect $IMAGE_NAME:$ROLLBACK_TAG > /dev/null 2>&1; then
        docker tag $IMAGE_NAME:$ROLLBACK_TAG $IMAGE_NAME:latest
        docker-compose up -d $SERVICE_NAME
    else
        print_error "Rollback image $IMAGE_NAME:$ROLLBACK_TAG not found!"
        print_warning "Available images:"
        docker images $IMAGE_NAME --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}"
        exit 1
    fi
fi

# Wait for service to be healthy
print_status "Waiting for service to be healthy..."
MAX_ATTEMPTS=10
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -sf http://localhost:8004/health > /dev/null 2>&1; then
        print_success "Service is healthy after rollback!"
        break
    else
        ATTEMPT=$((ATTEMPT + 1))
        if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
            print_error "Service failed to become healthy after rollback"
            echo ""
            echo "Service Logs:"
            docker-compose logs --tail=50 $SERVICE_NAME
            exit 1
        fi
        echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: Waiting for service..."
        sleep 5
    fi
done

# Verify rollback
echo ""
echo "=========================================="
echo "✅ Rollback Verification"
echo "=========================================="

# Show current version
print_status "Current running version:"
docker-compose ps $SERVICE_NAME

# Test endpoint
print_status "Testing service endpoint..."
if curl -sf http://localhost:8004/health > /dev/null 2>&1; then
    print_success "Service is responding correctly"

    # Show health status
    echo ""
    echo "Health Status:"
    curl -s http://localhost:8004/health | python3 -m json.tool | head -15
else
    print_error "Service is not responding"
fi

# Clean up rollback state file
rm -f $ROLLBACK_STATE_FILE

# Summary
echo ""
echo "=========================================="
echo "✅ Rollback Complete!"
echo "=========================================="
echo "Service has been rolled back successfully."
echo ""
echo "Next steps:"
echo "  - Check logs: docker-compose logs -f $SERVICE_NAME"
echo "  - Monitor health: curl http://localhost:8004/health"
echo "  - Investigate the issue that caused the rollback"
echo "=========================================="