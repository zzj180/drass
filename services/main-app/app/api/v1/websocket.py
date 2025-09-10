"""
WebSocket endpoints for real-time communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, Set, Optional, Any
import json
import asyncio
import logging
from datetime import datetime

from app.core.security import decode_token
from app.api.v1.connection_manager import ConnectionManager
from app.services.chat_service import chat_service
from app.services.notification_service import notification_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    Main WebSocket endpoint for real-time communication
    """
    user_id = None
    
    try:
        # Authenticate user if token provided
        if token:
            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
            except Exception as e:
                logger.error(f"Token validation failed: {e}")
                await websocket.close(code=1008, reason="Invalid authentication")
                return
        
        # Accept connection
        await manager.connect(websocket, user_id)
        logger.info(f"WebSocket connection established for user {user_id}")
        
        # Send connection confirmation
        await manager.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id
            },
            websocket
        )
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await handle_message(websocket, user_id, message)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        
    finally:
        # Clean up connection
        manager.disconnect(websocket, user_id)


async def handle_message(
    websocket: WebSocket,
    user_id: Optional[str],
    message: Dict[str, Any]
):
    """
    Handle incoming WebSocket messages
    """
    message_type = message.get("type")
    
    if message_type == "ping":
        # Respond to ping
        await manager.send_personal_message(
            {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
            websocket
        )
        
    elif message_type == "chat":
        # Handle chat message
        await handle_chat_message(websocket, user_id, message)
        
    elif message_type == "subscribe":
        # Subscribe to a channel
        channel = message.get("channel")
        if channel:
            await manager.subscribe_to_channel(websocket, channel)
            await manager.send_personal_message(
                {"type": "subscribed", "channel": channel},
                websocket
            )
            
    elif message_type == "unsubscribe":
        # Unsubscribe from a channel
        channel = message.get("channel")
        if channel:
            await manager.unsubscribe_from_channel(websocket, channel)
            await manager.send_personal_message(
                {"type": "unsubscribed", "channel": channel},
                websocket
            )
            
    elif message_type == "broadcast":
        # Broadcast to a channel (if authorized)
        if user_id:  # Only authenticated users can broadcast
            channel = message.get("channel")
            data = message.get("data")
            if channel and data:
                await manager.broadcast_to_channel(channel, {
                    "type": "broadcast",
                    "channel": channel,
                    "data": data,
                    "sender": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    else:
        # Unknown message type
        await manager.send_personal_message(
            {"type": "error", "message": f"Unknown message type: {message_type}"},
            websocket
        )


async def handle_chat_message(
    websocket: WebSocket,
    user_id: Optional[str],
    message: Dict[str, Any]
):
    """
    Handle chat messages with streaming support
    """
    try:
        chat_content = message.get("content")
        conversation_id = message.get("conversation_id")
        stream = message.get("stream", False)
        
        if not chat_content:
            await manager.send_personal_message(
                {"type": "error", "message": "No content provided"},
                websocket
            )
            return
        
        if stream:
            # Stream the response
            await stream_chat_response(
                websocket,
                user_id,
                chat_content,
                conversation_id
            )
        else:
            # Send complete response
            response = await chat_service.process_chat(
                messages=[{"role": "user", "content": chat_content}],
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            await manager.send_personal_message(
                {
                    "type": "chat_response",
                    "conversation_id": conversation_id,
                    "content": response.get("message", {}).get("content"),
                    "sources": response.get("sources"),
                    "timestamp": datetime.utcnow().isoformat()
                },
                websocket
            )
            
    except Exception as e:
        logger.error(f"Chat message handling error: {e}", exc_info=True)
        await manager.send_personal_message(
            {"type": "error", "message": f"Failed to process chat message: {str(e)}"},
            websocket
        )


async def stream_chat_response(
    websocket: WebSocket,
    user_id: Optional[str],
    content: str,
    conversation_id: Optional[str]
):
    """
    Stream chat response token by token
    """
    try:
        # Start streaming indicator
        await manager.send_personal_message(
            {
                "type": "stream_start",
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )
        
        # Stream tokens
        accumulated_content = ""
        async for chunk in chat_service.process_chat_stream(
            messages=[{"role": "user", "content": content}],
            conversation_id=conversation_id,
            user_id=user_id
        ):
            if "content" in chunk:
                accumulated_content += chunk["content"]
                await manager.send_personal_message(
                    {
                        "type": "stream_chunk",
                        "conversation_id": conversation_id,
                        "content": chunk["content"],
                        "accumulated": accumulated_content,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    websocket
                )
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
        
        # End streaming
        await manager.send_personal_message(
            {
                "type": "stream_end",
                "conversation_id": conversation_id,
                "final_content": accumulated_content,
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )
        
    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        await manager.send_personal_message(
            {
                "type": "stream_error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time notifications
    """
    try:
        # Validate token and get user
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=1008, reason="Invalid authentication")
            return
        
        # Accept connection
        await websocket.accept()
        
        # Subscribe to user's notification channel
        notification_channel = f"notifications:{user_id}"
        await manager.connect(websocket, user_id)
        await manager.subscribe_to_channel(websocket, notification_channel)
        
        logger.info(f"Notification WebSocket connected for user {user_id}")
        
        # Send any pending notifications
        pending = await notification_service.get_pending_notifications(user_id)
        for notification in pending:
            await manager.send_personal_message(
                {
                    "type": "notification",
                    "data": notification,
                    "timestamp": datetime.utcnow().isoformat()
                },
                websocket
            )
        
        # Keep connection alive
        try:
            while True:
                # Wait for messages (mainly for ping/pong)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
        except WebSocketDisconnect:
            logger.info(f"Notification WebSocket disconnected for user {user_id}")
            
    except Exception as e:
        logger.error(f"Notification WebSocket error: {e}", exc_info=True)
        await websocket.close(code=1011, reason="Internal server error")
        
    finally:
        manager.disconnect(websocket, user_id)


@router.websocket("/ws/collaborate/{room_id}")
async def websocket_collaboration(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint for collaborative sessions
    """
    try:
        # Validate token and get user
        payload = decode_token(token)
        user_id = payload.get("sub")
        user_name = payload.get("name", "Anonymous")
        
        if not user_id:
            await websocket.close(code=1008, reason="Invalid authentication")
            return
        
        # Accept connection and join room
        await websocket.accept()
        room_channel = f"room:{room_id}"
        
        await manager.connect(websocket, user_id)
        await manager.subscribe_to_channel(websocket, room_channel)
        
        # Notify others in room
        await manager.broadcast_to_channel(
            room_channel,
            {
                "type": "user_joined",
                "user_id": user_id,
                "user_name": user_name,
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude=[websocket]
        )
        
        logger.info(f"User {user_id} joined collaboration room {room_id}")
        
        try:
            while True:
                # Receive and broadcast collaboration messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Add user info to message
                message["user_id"] = user_id
                message["user_name"] = user_name
                message["timestamp"] = datetime.utcnow().isoformat()
                
                # Broadcast to room
                await manager.broadcast_to_channel(
                    room_channel,
                    message,
                    exclude=[websocket]  # Don't send back to sender
                )
                
        except WebSocketDisconnect:
            # Notify others that user left
            await manager.broadcast_to_channel(
                room_channel,
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "user_name": user_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"User {user_id} left collaboration room {room_id}")
            
    except Exception as e:
        logger.error(f"Collaboration WebSocket error: {e}", exc_info=True)
        await websocket.close(code=1011, reason="Internal server error")
        
    finally:
        manager.disconnect(websocket, user_id)