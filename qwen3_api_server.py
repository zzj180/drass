#!/usr/bin/env python3
"""
Simple API server for Qwen3-8B-MLX model
Provides OpenAI-compatible API
"""

from flask import Flask, request, jsonify
from mlx_lm import load, generate
import time
import uuid

app = Flask(__name__)

# Load model once at startup
print("Loading Qwen3-8B-MLX model...")
model, tokenizer = load("mlx_qwen3_converted")
print("Model loaded successfully!")

@app.route('/v1/models', methods=['GET'])
def list_models():
    """List available models"""
    return jsonify({
        "object": "list",
        "data": [{
            "id": "qwen3-8b-mlx",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "local"
        }]
    })

@app.route('/v1/completions', methods=['POST'])
def completions():
    """Text completion endpoint"""
    data = request.json
    prompt = data.get('prompt', '')
    max_tokens = data.get('max_tokens', 100)
    
    # Generate response
    response_text = generate(
        model, 
        tokenizer, 
        prompt=prompt,
        max_tokens=max_tokens
    )
    
    return jsonify({
        "id": f"cmpl-{uuid.uuid4()}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": "qwen3-8b-mlx",
        "choices": [{
            "text": response_text[len(prompt):],  # Remove prompt from response
            "index": 0,
            "logprobs": None,
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": len(tokenizer.encode(prompt)),
            "completion_tokens": len(tokenizer.encode(response_text)) - len(tokenizer.encode(prompt)),
            "total_tokens": len(tokenizer.encode(response_text))
        }
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Chat completion endpoint"""
    data = request.json
    messages = data.get('messages', [])
    max_tokens = data.get('max_tokens', 100)
    
    # Convert messages to prompt
    prompt = ""
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'system':
            prompt += f"System: {content}\n"
        elif role == 'user':
            prompt += f"User: {content}\n"
        elif role == 'assistant':
            prompt += f"Assistant: {content}\n"
    prompt += "Assistant: "
    
    # Generate response
    response_text = generate(
        model, 
        tokenizer, 
        prompt=prompt,
        max_tokens=max_tokens
    )
    
    # Extract assistant response
    assistant_response = response_text[len(prompt):]
    
    return jsonify({
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "qwen3-8b-mlx",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": assistant_response
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": len(tokenizer.encode(prompt)),
            "completion_tokens": len(tokenizer.encode(assistant_response)),
            "total_tokens": len(tokenizer.encode(prompt)) + len(tokenizer.encode(assistant_response))
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "model": "qwen3-8b-mlx"})

if __name__ == '__main__':
    print("Starting Qwen3-8B API server on http://localhost:8001")
    app.run(host='0.0.0.0', port=8001, debug=False)