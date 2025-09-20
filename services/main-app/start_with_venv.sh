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
