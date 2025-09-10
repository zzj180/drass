#!/bin/bash

# Deploy MLX-LM Server for Apple Silicon Macs
# This serves MLX models with OpenAI-compatible API

echo "Setting up MLX-LM Server for MLX models..."

# Check if running on Apple Silicon Mac
if [[ $(uname -s) != "Darwin" ]] || [[ $(uname -m) != "arm64" ]]; then
    echo "Error: MLX-LM Server requires Apple Silicon Mac (M1/M2/M3)"
    exit 1
fi

# Install MLX-LM if not already installed
echo "Installing/Updating MLX-LM..."
pip install --upgrade mlx-lm

# Create server startup script
cat > run_mlx_server.py << 'EOF'
#!/usr/bin/env python3

import argparse
from mlx_lm import load, generate
from mlx_lm.server import app
import uvicorn

def main():
    parser = argparse.ArgumentParser(description="Run MLX-LM Server")
    parser.add_argument("--model", default="mlx-community/Qwen2.5-7B-Instruct-4bit", 
                       help="Model to load")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--max-tokens", type=int, default=4096, 
                       help="Maximum tokens to generate")
    parser.add_argument("--temperature", type=float, default=0.7, 
                       help="Temperature for generation")
    
    args = parser.parse_args()
    
    # Start server with the model
    print(f"Starting MLX-LM Server with model: {args.model}")
    print(f"Server will be available at http://{args.host}:{args.port}")
    
    # Run the server
    uvicorn.run(
        "mlx_lm.server:app",
        host=args.host,
        port=args.port,
        reload=False
    )

if __name__ == "__main__":
    main()
EOF

chmod +x run_mlx_server.py

# Create service management script
cat > mlx_server_manager.sh << 'EOF'
#!/bin/bash

MODEL=${1:-"mlx-community/Qwen2.5-7B-Instruct-4bit"}
PORT=${2:-8001}
ACTION=${3:-start}

case $ACTION in
    start)
        echo "Starting MLX-LM Server with model: $MODEL on port $PORT"
        mlx_lm.server \
            --model $MODEL \
            --host 0.0.0.0 \
            --port $PORT \
            --trust-remote-code &
        echo $! > mlx_server.pid
        echo "Server started with PID: $(cat mlx_server.pid)"
        echo "API available at: http://localhost:$PORT/v1"
        ;;
    stop)
        if [ -f mlx_server.pid ]; then
            kill $(cat mlx_server.pid)
            rm mlx_server.pid
            echo "Server stopped"
        else
            echo "No server running"
        fi
        ;;
    status)
        if [ -f mlx_server.pid ]; then
            if ps -p $(cat mlx_server.pid) > /dev/null; then
                echo "Server is running with PID: $(cat mlx_server.pid)"
            else
                echo "Server PID file exists but process is not running"
                rm mlx_server.pid
            fi
        else
            echo "Server is not running"
        fi
        ;;
    *)
        echo "Usage: $0 [model] [port] [start|stop|status]"
        echo "Example: $0 mlx-community/Qwen2.5-7B-Instruct-4bit 8001 start"
        ;;
esac
EOF

chmod +x mlx_server_manager.sh

echo ""
echo "MLX-LM Server setup complete!"
echo ""
echo "Available MLX models for Qwen:"
echo "  - mlx-community/Qwen2.5-7B-Instruct-4bit (Recommended)"
echo "  - mlx-community/Qwen2.5-3B-Instruct-4bit (Smaller, faster)"
echo "  - mlx-community/Qwen2.5-14B-Instruct-4bit (Larger, better quality)"
echo ""
echo "To start the server:"
echo "  mlx_lm.server --model mlx-community/Qwen2.5-7B-Instruct-4bit --port 8001"
echo ""
echo "Or use the manager script:"
echo "  ./mlx_server_manager.sh mlx-community/Qwen2.5-7B-Instruct-4bit 8001 start"
echo ""
echo "Test the API:"
echo '  curl http://localhost:8001/v1/chat/completions \'
echo '    -H "Content-Type: application/json" \'
echo '    -d "{"model": "default", "messages": [{"role": "user", "content": "Hello"}]}"'