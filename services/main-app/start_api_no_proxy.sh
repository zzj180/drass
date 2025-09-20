#!/bin/bash
# Startup script for Drass API with proxy bypass

# Clear problematic proxy settings
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY
unset all_proxy
unset ALL_PROXY

# Set NO_PROXY for localhost connections
export NO_PROXY="localhost,127.0.0.1,::1,0.0.0.0"

# Optional: If you need HTTP proxy (not SOCKS), uncomment these:
# export HTTP_PROXY="http://127.0.0.1:7890"
# export HTTPS_PROXY="http://127.0.0.1:7890"

echo "Starting API with proxy settings:"
echo "  NO_PROXY: $NO_PROXY"
echo "  HTTP_PROXY: ${HTTP_PROXY:-not set}"
echo "  HTTPS_PROXY: ${HTTPS_PROXY:-not set}"

# Change to app directory
cd /home/qwkj/drass/services/main-app

# Start the API
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --loop asyncio
