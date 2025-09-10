#!/bin/bash

# Fix LM Studio MLX dependencies for macOS

echo "Fixing LM Studio MLX dependencies..."

# Check if running on macOS with Apple Silicon
if [[ $(uname -s) != "Darwin" ]] || [[ $(uname -m) != "arm64" ]]; then
    echo "This script is for macOS Apple Silicon only"
    exit 1
fi

# Install system-wide Python packages that LM Studio might use
echo "Installing MLX dependencies system-wide..."

# Check if pip3 is available
if ! command -v pip3 &> /dev/null; then
    echo "pip3 not found. Installing via Homebrew..."
    brew install python@3.11
fi

# Install required packages
echo "Installing huggingface_hub and MLX packages..."
pip3 install --user --upgrade huggingface_hub
pip3 install --user --upgrade mlx mlx-lm
pip3 install --user --upgrade transformers tokenizers safetensors

# Alternative: Install using system Python if available
if [ -f /usr/bin/python3 ]; then
    echo "Also installing with system Python..."
    /usr/bin/python3 -m pip install --user --upgrade huggingface_hub
    /usr/bin/python3 -m pip install --user --upgrade mlx mlx-lm
fi

# Check LM Studio's potential Python locations
echo ""
echo "Checking LM Studio Python environments..."

# Common LM Studio Python locations
LMSTUDIO_PATHS=(
    "$HOME/Library/Application Support/LM Studio"
    "/Applications/LM Studio.app/Contents/Resources"
    "/Applications/LM Studio.app/Contents/MacOS"
)

for path in "${LMSTUDIO_PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "Found LM Studio path: $path"
        # Look for Python in this path
        find "$path" -name "python*" -type f 2>/dev/null | head -5
    fi
done

echo ""
echo "Installation complete!"
echo ""
echo "Please try the following in LM Studio:"
echo "1. Restart LM Studio completely"
echo "2. Try loading a non-MLX model first (like GGUF format)"
echo "3. If MLX still fails, try downloading the model again"
echo ""
echo "Alternative solution:"
echo "Use a GGUF format model instead of MLX. Qwen models are available in GGUF format:"
echo "- Qwen2.5-7B-Instruct-GGUF"
echo "- Qwen2.5-14B-Instruct-GGUF"
echo ""
echo "These GGUF models work better with LM Studio and don't require MLX."