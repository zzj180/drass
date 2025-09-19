#!/bin/bash
# Fix backend dependencies issues for Ubuntu deployment
# This script specifically addresses PDF processing and other missing dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Fixing Backend Dependencies Issues${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
BASE_DIR="/home/qwkj/drass"
VENV_DIR="$BASE_DIR/venv"
API_DIR="$BASE_DIR/services/main-app"

# Check if virtual environment exists
if [ -d "$VENV_DIR" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source "$VENV_DIR/bin/activate"
    echo "Python: $(which python)"
    echo "Pip: $(which pip)"
    PIP_CMD="pip"
    PYTHON_CMD="python"
else
    echo -e "${YELLOW}No virtual environment found, using system Python${NC}"
    # Detect Python version
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
fi

echo ""
echo -e "${BLUE}Python version: $($PYTHON_CMD --version)${NC}"
echo ""

# Function to install a package with fallback
install_with_fallback() {
    local package=$1
    local alternative=$2
    local description=$3

    echo -e "${BLUE}Installing $description...${NC}"

    # Try primary package
    if $PIP_CMD install "$package" --no-cache-dir 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $package installed successfully"
        return 0
    fi

    # Try alternative if provided
    if [ -n "$alternative" ]; then
        echo -e "${YELLOW}Primary package failed, trying $alternative...${NC}"
        if $PIP_CMD install "$alternative" --no-cache-dir 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $alternative installed successfully"
            return 0
        fi
    fi

    # Try with --user flag if not in venv
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}Trying with --user flag...${NC}"
        if $PIP_CMD install "$package" --user --no-cache-dir 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $package installed with --user"
            return 0
        fi
    fi

    echo -e "${RED}✗${NC} Failed to install $description"
    return 1
}

# 1. Fix PDF processing libraries
echo -e "\n${BLUE}=== Fixing PDF Processing Libraries ===${NC}"

# Try multiple PDF libraries
install_with_fallback "PyPDF2>=3.0.0" "pypdf>=3.0.0" "PDF processing (PyPDF2/pypdf)"
install_with_fallback "pdfplumber" "" "PDF table extraction"
install_with_fallback "pymupdf" "" "PDF rendering (optional)"

# Verify PDF library availability
echo -e "\n${BLUE}Verifying PDF libraries...${NC}"
$PYTHON_CMD << EOF
import sys

pdf_libs = []
# Check PyPDF2
try:
    import PyPDF2
    pdf_libs.append(f"PyPDF2 v{PyPDF2.__version__}")
except ImportError:
    pass

# Check pypdf
try:
    import pypdf
    pdf_libs.append(f"pypdf v{pypdf.__version__}")
except ImportError:
    pass

# Check pdfplumber
try:
    import pdfplumber
    pdf_libs.append("pdfplumber")
except ImportError:
    pass

if pdf_libs:
    print(f"✓ PDF libraries available: {', '.join(pdf_libs)}")
else:
    print("✗ No PDF library available!")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: No PDF processing library could be installed${NC}"
    echo -e "${YELLOW}Manual installation required:${NC}"
    echo -e "  $PIP_CMD install pypdf"
fi

# 2. Fix document processing libraries
echo -e "\n${BLUE}=== Fixing Document Processing Libraries ===${NC}"

DOCUMENT_PACKAGES=(
    "python-docx:Word documents"
    "openpyxl:Excel files"
    "python-pptx:PowerPoint files"
    "markdownify:HTML to Markdown"
    "html2text:HTML to text"
    "beautifulsoup4:HTML parsing"
    "lxml:XML processing"
)

for package_info in "${DOCUMENT_PACKAGES[@]}"; do
    IFS=':' read -r package description <<< "$package_info"
    install_with_fallback "$package" "" "$description" || true
done

# 3. Fix authentication libraries (bcrypt issue)
echo -e "\n${BLUE}=== Fixing Authentication Libraries ===${NC}"

# Reinstall bcrypt to fix version detection issue
echo -e "${BLUE}Reinstalling bcrypt...${NC}"
$PIP_CMD uninstall -y bcrypt 2>/dev/null || true
install_with_fallback "bcrypt>=4.0.0" "" "bcrypt password hashing"
install_with_fallback "passlib[bcrypt]" "" "passlib with bcrypt"

# 4. Ensure httpx is installed for API calls
echo -e "\n${BLUE}=== Ensuring HTTP Client Libraries ===${NC}"
install_with_fallback "httpx>=0.24.0" "" "HTTP client"
install_with_fallback "aiohttp>=3.8.0" "" "Async HTTP client"

# 5. Fix any missing core dependencies
echo -e "\n${BLUE}=== Checking Core Dependencies ===${NC}"

CORE_PACKAGES=(
    "fastapi:Web framework"
    "uvicorn[standard]:ASGI server"
    "langchain:LangChain"
    "langchain-community:LangChain Community"
    "langchain-openai:OpenAI integration"
    "chromadb:Vector database"
    "sentence-transformers:Embeddings"
)

for package_info in "${CORE_PACKAGES[@]}"; do
    IFS=':' read -r package description <<< "$package_info"
    # Check if installed first
    if ! $PYTHON_CMD -c "import ${package%%[>=<]*}" 2>/dev/null; then
        echo -e "${YELLOW}$description not found, installing...${NC}"
        install_with_fallback "$package" "" "$description"
    else
        echo -e "${GREEN}✓${NC} $description already installed"
    fi
done

# 6. Final verification
echo -e "\n${BLUE}=== Final Verification ===${NC}"

$PYTHON_CMD << 'EOF'
import sys

print("Checking critical imports...")
critical = {
    "PDF Processing": ["PyPDF2", "pypdf"],
    "FastAPI": ["fastapi"],
    "Authentication": ["passlib", "bcrypt", "jose"],
    "LangChain": ["langchain"],
    "HTTP Client": ["httpx"],
    "Document Processing": ["docx", "openpyxl", "pptx"]
}

all_ok = True
for category, modules in critical.items():
    found = False
    for module in modules:
        try:
            __import__(module)
            found = True
            break
        except ImportError:
            continue

    if found:
        print(f"✓ {category}")
    else:
        print(f"✗ {category} - MISSING")
        all_ok = False

if all_ok:
    print("\n✓ All critical dependencies are available")
else:
    print("\n⚠ Some dependencies are still missing")
    sys.exit(1)
EOF

EXIT_CODE=$?

# Summary
echo -e "\n${BLUE}========================================${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Backend dependencies fixed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Restart the API service:"
    echo "   bash $BASE_DIR/start-api-noproxy.sh"
    echo ""
    echo "2. Or restart all services:"
    echo "   sudo bash $BASE_DIR/deployment/scripts/start-ubuntu-services.sh"
else
    echo -e "${YELLOW}⚠ Some issues remain${NC}"
    echo ""
    echo "Check the output above for specific missing packages."
    echo "You may need to install them manually."
fi
echo -e "${BLUE}========================================${NC}"