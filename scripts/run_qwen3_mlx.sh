#!/bin/bash

# Run Qwen3-8B-MLX-bf16 with MLX-LM Server
# Using the model downloaded by LM Studio

MODEL_PATH="$HOME/.lmstudio/models/Qwen/Qwen3-8B-MLX-bf16"
PORT=${1:-8001}

echo "Starting MLX-LM Server with Qwen3-8B-MLX-bf16"
echo "Model path: $MODEL_PATH"
echo "Port: $PORT"
echo ""

# Check if model exists
if [ ! -d "$MODEL_PATH" ]; then
    echo "Error: Model not found at $MODEL_PATH"
    echo "Please download Qwen3-8B-MLX-bf16 in LM Studio first"
    exit 1
fi

# Check if config.json exists and is MLX format
if [ ! -f "$MODEL_PATH/config.json" ]; then
    echo "Error: config.json not found in model directory"
    exit 1
fi

echo "Starting server..."
echo "API will be available at: http://localhost:$PORT/v1"
echo ""

# Start MLX-LM server with local model path
mlx_lm.server \
    --model "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port $PORT \
    --trust-remote-code \
    --max-tokens 4096 \
    --temp 0.7

# Alternative command if the above doesn't work:
# python -m mlx_lm.server \
#     --model "$MODEL_PATH" \
#     --host 0.0.0.0 \
#     --port $PORT