#!/usr/bin/env python3
"""Simple FastAPI backend for testing"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import asyncio
import json

app = FastAPI(title="LangChain Compliance Assistant API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM Configuration
LLM_API_BASE = "http://localhost:8001/v1"

class ChatRequest(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    response: str
    
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "langchain-backend"}

@app.get("/")
async def root():
    return {"message": "LangChain Compliance Assistant API", "docs": "/docs"}

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Simple chat endpoint that calls local LLM"""
    try:
        async with httpx.AsyncClient() as client:
            # Call local LLM
            response = await client.post(
                f"{LLM_API_BASE}/completions",
                json={
                    "model": "qwen3-8b-mlx",
                    "prompt": request.message,
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract text from response
            if "choices" in result and len(result["choices"]) > 0:
                text = result["choices"][0].get("text", "No response")
            else:
                text = "No response from model"
                
            return ChatResponse(response=text)
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"LLM service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/models")
async def list_models():
    """List available models"""
    return {
        "models": [
            {"id": "qwen3-8b-mlx", "name": "Qwen3 8B (MLX)", "available": True}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    import sys
    port = 8080 if "--port" in sys.argv else 8000
    uvicorn.run(app, host="0.0.0.0", port=port)