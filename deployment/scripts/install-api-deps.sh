#!/bin/bash
# Install API dependencies for Ubuntu deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Installing API Dependencies${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"
API_DIR="$BASE_DIR/services/main-app"

# Detect Python version and environment
echo -e "\n${BLUE}Checking Python environment...${NC}"

# Check which Python to use
if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_CMD="python3.11"
    PIP_CMD="python3.11 -m pip"
elif command -v python3.10 >/dev/null 2>&1; then
    PYTHON_CMD="python3.10"
    PIP_CMD="python3.10 -m pip"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
    PIP_CMD="python3 -m pip"
else
    echo -e "${RED}Python3 not found!${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo -e "${GREEN}Using Python: $PYTHON_VERSION${NC}"

# Check if running with sudo
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Running with sudo. Will try system-wide installation first.${NC}"
    INSTALL_USER=""
else
    echo -e "${BLUE}Running as regular user. Will use --user flag if needed.${NC}"
    INSTALL_USER="--user"
fi

# Upgrade pip first
echo -e "\n${BLUE}Upgrading pip...${NC}"
$PIP_CMD install --upgrade pip $INSTALL_USER 2>/dev/null || true

# Function to install a package
install_package() {
    local package=$1
    local friendly_name=${2:-$package}

    echo -e "${BLUE}Installing $friendly_name...${NC}"

    # Try without --user first (for system-wide)
    if $PIP_CMD install "$package" --no-cache-dir 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $friendly_name installed successfully"
        return 0
    fi

    # If that fails and we're not root, try with --user
    if [ -n "$INSTALL_USER" ]; then
        if $PIP_CMD install "$package" --no-cache-dir --user 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $friendly_name installed with --user flag"
            return 0
        fi
    fi

    echo -e "${YELLOW}!${NC} Failed to install $friendly_name"
    return 1
}

# Critical dependencies for the API
echo -e "\n${BLUE}=== Installing Critical Dependencies ===${NC}"

CRITICAL_PACKAGES=(
    "passlib[bcrypt]:Password hashing"
    "python-jose[cryptography]:JWT authentication"
    "python-multipart:Form data handling"
    "python-dotenv:Environment variables"
    "pydantic:Data validation"
    "fastapi:Web framework"
    "uvicorn[standard]:ASGI server"
    "sqlalchemy:Database ORM"
    "psycopg2-binary:PostgreSQL adapter"
    "redis:Redis client"
    "httpx:HTTP client"
    "aiofiles:Async file I/O"
)

for package_info in "${CRITICAL_PACKAGES[@]}"; do
    IFS=':' read -r package name <<< "$package_info"
    install_package "$package" "$name"
done

# LangChain dependencies
echo -e "\n${BLUE}=== Installing LangChain Dependencies ===${NC}"

LANGCHAIN_PACKAGES=(
    "langchain:LangChain core"
    "langchain-community:LangChain community"
    "langchain-openai:OpenAI integration"
    "openai:OpenAI client"
    "tiktoken:Token counting"
)

for package_info in "${LANGCHAIN_PACKAGES[@]}"; do
    IFS=':' read -r package name <<< "$package_info"
    install_package "$package" "$name"
done

# Vector store dependencies
echo -e "\n${BLUE}=== Installing Vector Store Dependencies ===${NC}"

install_package "chromadb" "ChromaDB"
install_package "sentence-transformers" "Sentence Transformers"

# Optional but useful packages
echo -e "\n${BLUE}=== Installing Optional Dependencies ===${NC}"

OPTIONAL_PACKAGES=(
    "python-magic:File type detection"
    "python-docx:Word document processing"
    "pypdf:PDF processing"
    "pandas:Data manipulation"
    "numpy:Numerical operations"
    "beautifulsoup4:HTML parsing"
    "lxml:XML processing"
)

for package_info in "${OPTIONAL_PACKAGES[@]}"; do
    IFS=':' read -r package name <<< "$package_info"
    install_package "$package" "$name" || true  # Don't fail on optional packages
done

# If requirements.txt exists, try to install from it
if [ -f "$API_DIR/requirements.txt" ]; then
    echo -e "\n${BLUE}=== Installing from requirements.txt ===${NC}"
    cd "$API_DIR"
    $PIP_CMD install -r requirements.txt --no-cache-dir $INSTALL_USER 2>/dev/null || {
        echo -e "${YELLOW}Some packages from requirements.txt failed, but critical deps are installed${NC}"
    }
fi

# Verify critical imports
echo -e "\n${BLUE}=== Verifying Critical Imports ===${NC}"

CRITICAL_IMPORTS=(
    "fastapi"
    "uvicorn"
    "pydantic"
    "passlib"
    "jose"
    "dotenv"
    "sqlalchemy"
    "langchain"
    "openai"
    "chromadb"
)

ALL_OK=true
for module in "${CRITICAL_IMPORTS[@]}"; do
    if $PYTHON_CMD -c "import $module" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $module"
    else
        echo -e "${RED}✗${NC} $module"
        ALL_OK=false
    fi
done

# Summary
echo -e "\n${BLUE}========================================${NC}"
if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}All critical dependencies are installed!${NC}"
    echo -e "\nYou can now start the API with:"
    echo -e "  ${BLUE}cd $API_DIR${NC}"
    echo -e "  ${BLUE}$PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8888${NC}"
else
    echo -e "${YELLOW}Some dependencies are missing.${NC}"
    echo -e "\nTry running this script again or install manually:"
    echo -e "  ${BLUE}$PIP_CMD install passlib[bcrypt] python-jose[cryptography] fastapi uvicorn${NC}"
fi
echo -e "${BLUE}========================================${NC}"