#!/bin/bash
# Install dependencies for Drass deployment on Ubuntu 22.04

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Installing Dependencies for Drass${NC}"
echo -e "${BLUE}========================================${NC}"

# Update package list
echo -e "\n${BLUE}Updating package list...${NC}"
sudo apt-get update

# Install system dependencies
echo -e "\n${BLUE}Installing system dependencies...${NC}"
sudo apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    python3-pip \
    python3-venv \
    python3-dev \
    lsof

# Install PostgreSQL
echo -e "\n${BLUE}Installing PostgreSQL...${NC}"
if ! command -v psql >/dev/null 2>&1; then
    # Get Ubuntu version
    UBUNTU_VERSION=$(lsb_release -rs)

    # Add PostgreSQL official APT repository for latest version
    sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
    sudo apt-get update

    # Install PostgreSQL
    sudo apt-get install -y postgresql postgresql-contrib

    # Start and enable PostgreSQL
    sudo systemctl start postgresql
    sudo systemctl enable postgresql

    echo -e "${GREEN}✓${NC} PostgreSQL installed successfully"

    # Setup database and user
    echo -e "${BLUE}Setting up PostgreSQL database...${NC}"
    sudo -u postgres psql <<EOF
-- Create user
CREATE USER drass_user WITH PASSWORD 'drass_password';

-- Create database
CREATE DATABASE drass_production OWNER drass_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE drass_production TO drass_user;

-- Show created database
\l drass_production
EOF

    echo -e "${GREEN}✓${NC} Database 'drass_production' created with user 'drass_user'"
    echo -e "${YELLOW}Note: Default password is 'drass_password'. Please change it in production!${NC}"
else
    echo -e "${GREEN}✓${NC} PostgreSQL is already installed"
fi

# Install Redis
echo -e "\n${BLUE}Installing Redis...${NC}"
if ! command -v redis-cli >/dev/null 2>&1; then
    sudo apt-get install -y redis-server

    # Configure Redis for production
    sudo sed -i 's/^# maxmemory <bytes>/maxmemory 2gb/' /etc/redis/redis.conf
    sudo sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf

    # Start and enable Redis
    sudo systemctl start redis-server
    sudo systemctl enable redis-server

    echo -e "${GREEN}✓${NC} Redis installed successfully"
else
    echo -e "${GREEN}✓${NC} Redis is already installed"
fi

# Install Node.js (for frontend)
echo -e "\n${BLUE}Installing Node.js...${NC}"
if ! command -v node >/dev/null 2>&1; then
    # Install Node.js 18.x
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs

    echo -e "${GREEN}✓${NC} Node.js $(node -v) installed successfully"
else
    echo -e "${GREEN}✓${NC} Node.js $(node -v) is already installed"
fi

# Install Python packages
echo -e "\n${BLUE}Installing Python packages...${NC}"
pip3 install --upgrade pip
pip3 install \
    chromadb \
    psutil \
    pyyaml \
    python-dotenv

echo -e "${GREEN}✓${NC} Python packages installed"

# Create necessary directories
echo -e "\n${BLUE}Creating necessary directories...${NC}"
sudo mkdir -p /home/qwkj/drass/{data,logs,uploads}
sudo chown -R $USER:$USER /home/qwkj/drass

# Check services status
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Service Status:${NC}"
echo -e "${BLUE}========================================${NC}"

# Check PostgreSQL
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✓${NC} PostgreSQL is running"

    # Test connection
    if PGPASSWORD=drass_password psql -U drass_user -h localhost -d drass_production -c "SELECT 1;" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} PostgreSQL connection test successful"
    else
        echo -e "${YELLOW}!${NC} PostgreSQL is running but connection test failed"
        echo -e "   Try: PGPASSWORD=drass_password psql -U drass_user -h localhost -d drass_production"
    fi
else
    echo -e "${RED}✗${NC} PostgreSQL is not running"
fi

# Check Redis
if systemctl is-active --quiet redis-server; then
    echo -e "${GREEN}✓${NC} Redis is running"

    # Test connection
    if redis-cli ping >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Redis connection test successful"
    else
        echo -e "${YELLOW}!${NC} Redis is running but connection test failed"
    fi
else
    echo -e "${RED}✗${NC} Redis is not running"
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}Installation completed!${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${YELLOW}Important Notes:${NC}"
echo -e "1. Default PostgreSQL password is 'drass_password' - change it for production!"
echo -e "2. Update /etc/postgresql/*/main/pg_hba.conf if you have connection issues"
echo -e "3. Update /etc/redis/redis.conf for production settings"
echo -e "4. Create .env.production file with your actual passwords"

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "1. cd /home/qwkj/drass"
echo -e "2. Create virtual environment: python3 -m venv venv"
echo -e "3. Activate it: source venv/bin/activate"
echo -e "4. Install Python requirements: pip install -r services/main-app/requirements.txt"
echo -e "5. Run the startup script: ./deployment/scripts/start-ubuntu-services.sh"