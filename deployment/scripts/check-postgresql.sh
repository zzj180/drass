#!/bin/bash
# PostgreSQL diagnostic and fix script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}PostgreSQL Diagnostic Tool${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to check PostgreSQL installation
check_installation() {
    echo -e "\n${BLUE}Checking PostgreSQL installation...${NC}"

    if command -v psql >/dev/null 2>&1; then
        PSQL_VERSION=$(psql --version | awk '{print $3}')
        echo -e "${GREEN}✓${NC} PostgreSQL is installed: version $PSQL_VERSION"

        # Get PostgreSQL version number
        PG_VERSION=$(psql --version | grep -oE '[0-9]+' | head -1)
        echo -e "  Major version: $PG_VERSION"
        return 0
    else
        echo -e "${RED}✗${NC} PostgreSQL is not installed"
        return 1
    fi
}

# Function to check PostgreSQL service
check_service() {
    echo -e "\n${BLUE}Checking PostgreSQL service...${NC}"

    # Find all possible PostgreSQL service names
    PG_SERVICES=$(systemctl list-units --all --type=service | grep -E 'postgresql' | awk '{print $1}')

    if [ -z "$PG_SERVICES" ]; then
        echo -e "${RED}✗${NC} No PostgreSQL services found"
        return 1
    fi

    echo -e "${GREEN}Found PostgreSQL services:${NC}"
    for service in $PG_SERVICES; do
        STATUS=$(systemctl is-active "$service" 2>/dev/null || echo "inactive")
        if [ "$STATUS" = "active" ]; then
            echo -e "  ${GREEN}✓${NC} $service is $STATUS"
            ACTIVE_SERVICE="$service"
        else
            echo -e "  ${RED}✗${NC} $service is $STATUS"
        fi
    done

    if [ -n "$ACTIVE_SERVICE" ]; then
        return 0
    else
        return 1
    fi
}

# Function to check PostgreSQL port
check_port() {
    echo -e "\n${BLUE}Checking PostgreSQL port 5432...${NC}"

    # Multiple methods to check port
    if lsof -i :5432 >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Port 5432 is in use (lsof)"
        lsof -i :5432 | head -5
        return 0
    elif sudo netstat -tlnp 2>/dev/null | grep -q ":5432"; then
        echo -e "${GREEN}✓${NC} Port 5432 is listening (netstat)"
        sudo netstat -tlnp | grep ":5432"
        return 0
    elif sudo ss -tlnp 2>/dev/null | grep -q ":5432"; then
        echo -e "${GREEN}✓${NC} Port 5432 is listening (ss)"
        sudo ss -tlnp | grep ":5432"
        return 0
    else
        echo -e "${RED}✗${NC} Port 5432 is not listening"
        return 1
    fi
}

# Function to check PostgreSQL connectivity
check_connectivity() {
    echo -e "\n${BLUE}Checking PostgreSQL connectivity...${NC}"

    # Try pg_isready
    if command -v pg_isready >/dev/null 2>&1; then
        echo -e "Testing with pg_isready..."

        # Test different connection methods
        for host in localhost 127.0.0.1 /var/run/postgresql; do
            if pg_isready -h "$host" -p 5432 >/dev/null 2>&1; then
                echo -e "${GREEN}✓${NC} Can connect via $host"
            else
                echo -e "${RED}✗${NC} Cannot connect via $host"
            fi
        done
    fi

    # Try to connect as postgres user
    echo -e "\nTesting database connection..."
    if (cd /tmp && sudo -u postgres psql -c "SELECT 1;" >/dev/null 2>&1); then
        echo -e "${GREEN}✓${NC} Can connect as postgres user"

        # Check for drass database and user
        echo -e "\nChecking drass database..."
        if (cd /tmp && sudo -u postgres psql -lqt) | cut -d \| -f 1 | grep -qw drass_production; then
            echo -e "${GREEN}✓${NC} Database 'drass_production' exists"
        else
            echo -e "${YELLOW}!${NC} Database 'drass_production' does not exist"
        fi

        # Check for drass_user
        if (cd /tmp && sudo -u postgres psql -c "SELECT 1 FROM pg_user WHERE usename='drass_user';") | grep -q 1; then
            echo -e "${GREEN}✓${NC} User 'drass_user' exists"
        else
            echo -e "${YELLOW}!${NC} User 'drass_user' does not exist"
        fi
    else
        echo -e "${RED}✗${NC} Cannot connect as postgres user"
    fi
}

# Function to check PostgreSQL configuration
check_config() {
    echo -e "\n${BLUE}Checking PostgreSQL configuration...${NC}"

    # Find postgresql.conf
    PG_CONFIG=$((cd /tmp && sudo -u postgres psql -t -P format=unaligned -c 'SHOW config_file;' 2>/dev/null) || echo "")

    if [ -n "$PG_CONFIG" ] && [ -f "$PG_CONFIG" ]; then
        echo -e "Configuration file: $PG_CONFIG"

        # Check listen_addresses
        LISTEN_ADDR=$(grep "^listen_addresses" "$PG_CONFIG" 2>/dev/null || grep "^#listen_addresses" "$PG_CONFIG" 2>/dev/null | head -1)
        echo -e "Listen addresses: $LISTEN_ADDR"

        # Check port
        PORT_CONFIG=$(grep "^port" "$PG_CONFIG" 2>/dev/null || grep "^#port" "$PG_CONFIG" 2>/dev/null | head -1)
        echo -e "Port configuration: $PORT_CONFIG"
    else
        echo -e "${YELLOW}Cannot find postgresql.conf${NC}"
    fi

    # Find pg_hba.conf
    PG_HBA=$((cd /tmp && sudo -u postgres psql -t -P format=unaligned -c 'SHOW hba_file;' 2>/dev/null) || echo "")

    if [ -n "$PG_HBA" ] && [ -f "$PG_HBA" ]; then
        echo -e "\nAuthentication file: $PG_HBA"
        echo -e "Local connections:"
        grep -E "^local|^host.*127.0.0.1|^host.*localhost" "$PG_HBA" 2>/dev/null | head -5
    fi
}

# Function to fix PostgreSQL
fix_postgresql() {
    echo -e "\n${BLUE}Attempting to fix PostgreSQL...${NC}"

    # Try to start PostgreSQL service
    echo -e "${YELLOW}Starting PostgreSQL service...${NC}"

    # Try different service names
    for service in postgresql postgresql@14-main postgresql@15-main postgresql-14 postgresql-15; do
        if systemctl list-unit-files | grep -q "^${service}.service"; then
            echo -e "Trying to start $service..."
            sudo systemctl start "$service" 2>/dev/null || true
            sudo systemctl enable "$service" 2>/dev/null || true

            if systemctl is-active --quiet "$service"; then
                echo -e "${GREEN}✓${NC} Started $service successfully"
                break
            fi
        fi
    done

    # Wait for service to be ready
    sleep 3

    # Create database and user if needed
    if (cd /tmp && sudo -u postgres psql -c "SELECT 1;" >/dev/null 2>&1); then
        echo -e "\n${BLUE}Setting up database...${NC}"

        (cd /tmp && sudo -u postgres psql <<EOF 2>/dev/null) || true
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'drass_user') THEN
        CREATE USER drass_user WITH PASSWORD 'drass_password';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE drass_production OWNER drass_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'drass_production')\\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE drass_production TO drass_user;

-- Allow connections
ALTER DATABASE drass_production SET client_encoding TO 'utf8';
EOF

        echo -e "${GREEN}✓${NC} Database setup completed"

        # Update pg_hba.conf to allow local connections
        echo -e "\n${BLUE}Updating authentication configuration...${NC}"
        PG_VERSION=$(psql --version | grep -oE '[0-9]+' | head -1)
        PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

        if [ -f "$PG_HBA" ]; then
            # Backup original
            sudo cp "$PG_HBA" "$PG_HBA.backup"

            # Add local connection rules if not present
            if ! grep -q "host.*drass_production.*drass_user" "$PG_HBA"; then
                echo "host    drass_production    drass_user    127.0.0.1/32    md5" | sudo tee -a "$PG_HBA" >/dev/null
                echo "host    drass_production    drass_user    ::1/128         md5" | sudo tee -a "$PG_HBA" >/dev/null
            fi

            # Reload PostgreSQL
            sudo systemctl reload postgresql
            echo -e "${GREEN}✓${NC} Authentication configuration updated"
        fi
    fi
}

# Main diagnostic flow
echo -e "\n${YELLOW}Running PostgreSQL diagnostics...${NC}"

# Check installation
if ! check_installation; then
    echo -e "\n${RED}PostgreSQL is not installed. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
    sleep 5
fi

# Check service
if ! check_service; then
    echo -e "\n${YELLOW}PostgreSQL service is not running${NC}"
    fix_postgresql
fi

# Check port
check_port

# Check connectivity
check_connectivity

# Check configuration
check_config

# Final status
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Final Status:${NC}"
echo -e "${BLUE}========================================${NC}"

if check_service && check_port; then
    echo -e "${GREEN}✓ PostgreSQL is running and accessible${NC}"
    echo -e "\nConnection details:"
    echo -e "  Host: localhost"
    echo -e "  Port: 5432"
    echo -e "  Database: drass_production"
    echo -e "  User: drass_user"
    echo -e "  Password: drass_password (change in production!)"

    echo -e "\nTest connection with:"
    echo -e "  ${CYAN}PGPASSWORD=drass_password psql -h localhost -U drass_user -d drass_production${NC}"
else
    echo -e "${RED}✗ PostgreSQL has issues${NC}"
    echo -e "\nTry manual fixes:"
    echo -e "1. Restart PostgreSQL: ${CYAN}sudo systemctl restart postgresql${NC}"
    echo -e "2. Check logs: ${CYAN}sudo journalctl -xe -u postgresql${NC}"
    echo -e "3. Check PostgreSQL cluster: ${CYAN}pg_lsclusters${NC}"
    echo -e "4. Reconfigure: ${CYAN}sudo dpkg-reconfigure postgresql${NC}"
fi