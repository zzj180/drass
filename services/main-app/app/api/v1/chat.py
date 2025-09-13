from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import json
import uuid

from app.core.security import get_current_active_user
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Pydantic models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Chat messages history")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for context")
    model: Optional[str] = Field(default=None, description="Model to use for generation")
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2, description="Temperature for generation")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=32000, description="Maximum tokens to generate")
    stream: bool = Field(default=False, description="Enable streaming response")
    use_knowledge_base: bool = Field(default=True, description="Use knowledge base for context")
    knowledge_base_id: Optional[str] = Field(default=None, description="Specific knowledge base to use")


class ChatResponse(BaseModel):
    id: str = Field(..., description="Response ID")
    conversation_id: str = Field(..., description="Conversation ID")
    message: ChatMessage = Field(..., description="Assistant's response message")
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="Source documents used")
    usage: Optional[Dict[str, int]] = Field(default=None, description="Token usage statistics")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ConversationSummary(BaseModel):
    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message_count: int = Field(..., description="Number of messages")
    model: Optional[str] = Field(default=None, description="Model used")


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Send a chat message and get a response
    """
    try:
        # Import services here to avoid circular imports
        from app.services.chat_service import chat_service
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Process non-streaming chat
        response = await chat_service.process_chat(
            messages=request.messages,
            conversation_id=conversation_id,
            user_id=current_user["id"],
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            use_knowledge_base=request.use_knowledge_base,
            knowledge_base_id=request.knowledge_base_id
        )
        
        return ChatResponse(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            message=response["message"],
            sources=response.get("sources"),
            usage=response.get("usage"),
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Send a chat message and get a streaming response
    """
    try:
        from app.services.chat_service import chat_service
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        async def generate():
            """Generate streaming response"""
            try:
                async for chunk in chat_service.process_chat_stream(
                    messages=request.messages,
                    conversation_id=conversation_id,
                    user_id=current_user["id"],
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    use_knowledge_base=request.use_knowledge_base,
                    knowledge_base_id=request.knowledge_base_id
                ):
                    # Format as Server-Sent Events
                    data = json.dumps(chunk)
                    yield f"data: {data}\n\n"
            except Exception as e:
                error_data = json.dumps({"error": str(e)})
                yield f"data: {error_data}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable Nginx buffering
            }
        )
        
    except Exception as e:
        logger.error(f"Stream chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stream chat processing failed: {str(e)}"
        )


@router.websocket("/ws")
async def chat_websocket(
    websocket: WebSocket,
    token: str = None
):
    """
    WebSocket endpoint for real-time chat
    """
    try:
        # Validate token and get user
        from app.core.security import decode_token
        
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
        
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
        except Exception:
            await websocket.close(code=1008, reason="Invalid authentication token")
            return
        
        await websocket.accept()
        logger.info(f"WebSocket connection established for user {user_id}")
        
        # Import services
        from app.services.chat_service import chat_service
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Process message
                message_type = data.get("type", "chat")
                
                if message_type == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong"})
                    
                elif message_type == "chat":
                    # Process chat message
                    messages = data.get("messages", [])
                    conversation_id = data.get("conversation_id") or str(uuid.uuid4())
                    
                    # Stream response
                    async for chunk in chat_service.process_chat_stream(
                        messages=messages,
                        conversation_id=conversation_id,
                        user_id=user_id,
                        model=data.get("model"),
                        temperature=data.get("temperature", 0.7),
                        max_tokens=data.get("max_tokens"),
                        use_knowledge_base=data.get("use_knowledge_base", True),
                        knowledge_base_id=data.get("knowledge_base_id")
                    ):
                        await websocket.send_json({
                            "type": "chat_chunk",
                            "data": chunk
                        })
                    
                    # Send completion signal
                    await websocket.send_json({
                        "type": "chat_complete",
                        "conversation_id": conversation_id
                    })
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {str(e)}", exc_info=True)
            await websocket.close(code=1011, reason="Internal server error")
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}", exc_info=True)


@router.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations(
    limit: int = 20,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get user's conversation history
    """
    try:
        from app.services.chat_service import chat_service
        
        conversations = await chat_service.get_user_conversations(
            user_id=current_user["id"],
            limit=limit,
            offset=offset
        )
        
        return [
            ConversationSummary(
                id=conv["id"],
                title=conv["title"],
                created_at=conv["created_at"],
                updated_at=conv["updated_at"],
                message_count=conv["message_count"],
                model=conv.get("model")
            )
            for conv in conversations
        ]
        
    except Exception as e:
        logger.error(f"Get conversations error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversations: {str(e)}"
        )


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific conversation with all messages
    """
    try:
        from app.services.chat_service import chat_service
        
        conversation = await chat_service.get_conversation(
            conversation_id=conversation_id,
            user_id=current_user["id"]
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Delete a conversation
    """
    try:
        from app.services.chat_service import chat_service
        
        success = await chat_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete conversation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )