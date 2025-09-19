#!/bin/bash
# Fix proxy configuration issues for Drass API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Fixing Proxy Configuration for Drass API${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"

# Check current proxy settings
echo -e "\n${BLUE}Current proxy settings:${NC}"
echo "  http_proxy: ${http_proxy:-not set}"
echo "  https_proxy: ${https_proxy:-not set}"
echo "  all_proxy: ${all_proxy:-not set}"
echo "  NO_PROXY: ${NO_PROXY:-not set}"

# Create environment configuration file
echo -e "\n${BLUE}Creating proxy bypass configuration...${NC}"

cat > "$BASE_DIR/.env.proxy" << 'EOF'
# Proxy bypass configuration for local services
export NO_PROXY="localhost,127.0.0.1,::1,0.0.0.0,*.local"

# If you need to use proxy for external services, uncomment and set these:
# export HTTP_PROXY="http://127.0.0.1:7890"
# export HTTPS_PROXY="http://127.0.0.1:7890"

# Disable SOCKS proxy for Python libraries that don't support it
unset all_proxy
unset ALL_PROXY
EOF

echo -e "${GREEN}✓${NC} Created $BASE_DIR/.env.proxy"

# Create wrapper script for the main app
echo -e "\n${BLUE}Creating API startup wrapper...${NC}"

cat > "$BASE_DIR/services/main-app/start_api_no_proxy.sh" << 'EOF'
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
EOF

chmod +x "$BASE_DIR/services/main-app/start_api_no_proxy.sh"
echo -e "${GREEN}✓${NC} Created startup wrapper script"

# Create systemd service file (optional)
echo -e "\n${BLUE}Creating systemd service file...${NC}"

cat > "$BASE_DIR/drass-api.service" << 'EOF'
[Unit]
Description=Drass API Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=qwkj
WorkingDirectory=/home/qwkj/drass/services/main-app
Environment="PATH=/home/qwkj/.pyenv/shims:/home/qwkj/.pyenv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="NO_PROXY=localhost,127.0.0.1,::1,0.0.0.0"
ExecStart=/home/qwkj/drass/services/main-app/start_api_no_proxy.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓${NC} Created systemd service file at $BASE_DIR/drass-api.service"
echo -e "${YELLOW}To install as a system service, run:${NC}"
echo -e "  sudo cp $BASE_DIR/drass-api.service /etc/systemd/system/"
echo -e "  sudo systemctl daemon-reload"
echo -e "  sudo systemctl enable drass-api"
echo -e "  sudo systemctl start drass-api"

# Test if we can import the problematic modules
echo -e "\n${BLUE}Testing Python imports with cleared proxy...${NC}"

(
    unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
    export NO_PROXY="localhost,127.0.0.1,::1"

    python3 << 'PYTHON_EOF'
import os
import sys

print(f"Python version: {sys.version}")
print(f"NO_PROXY: {os.environ.get('NO_PROXY', 'not set')}")
print(f"http_proxy: {os.environ.get('http_proxy', 'not set')}")
print(f"all_proxy: {os.environ.get('all_proxy', 'not set')}")

try:
    # Test OpenAI import
    from openai import OpenAI
    print("✓ OpenAI library imported successfully")
except Exception as e:
    print(f"✗ OpenAI import failed: {e}")

try:
    # Test LangChain import
    from langchain_openai import ChatOpenAI
    print("✓ LangChain OpenAI imported successfully")

    # Try to create a client with local endpoint
    try:
        client = ChatOpenAI(
            api_key="dummy",
            base_url="http://localhost:8001/v1",
            model="vllm"
        )
        print("✓ Created LangChain client with local endpoint")
    except Exception as e:
        print(f"! Client creation warning: {e}")

except Exception as e:
    print(f"✗ LangChain import failed: {e}")

print("\nProxy configuration test completed.")
PYTHON_EOF
)

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Configuration Complete${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${GREEN}Next steps:${NC}"
echo -e "1. Start the API using the wrapper script:"
echo -e "   ${BLUE}$BASE_DIR/services/main-app/start_api_no_proxy.sh${NC}"
echo -e ""
echo -e "2. Or restart using the main startup script:"
echo -e "   ${BLUE}$BASE_DIR/deployment/scripts/start-ubuntu-services.sh${NC}"
echo -e ""
echo -e "3. Check API status:"
echo -e "   ${BLUE}curl http://localhost:8000/health${NC}"