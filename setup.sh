#!/bin/bash

# Drass Project Setup Script
# This script sets up the Python virtual environment and installs dependencies

set -e

echo "🚀 Setting up Drass - Data Regulation Assistant"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.7+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.7"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION+ is required, but found $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Dependencies installed successfully"

# Make scripts executable
echo "🔐 Making scripts executable..."
chmod +x scripts/*.py

# Validate configurations
echo "🔍 Validating configurations..."
python scripts/validate.py --all

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "To get started:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Set your environment variables (see README.md)"
echo "3. Validate configurations: python scripts/validate.py --all"
echo "4. Deploy applications: python scripts/deploy.py --help"
echo ""
echo "For more information, see README.md"
