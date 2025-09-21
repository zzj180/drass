"""
Audit WebSocket API endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import HTMLResponse
import json
import logging

from app.websocket.audit_websocket import audit_websocket_manager
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.websocket("/ws/audit/{user_id}")
async def audit_websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time audit event streaming
    
    Args:
        websocket: The WebSocket connection
        user_id: ID of the user connecting
    """
    try:
        # Connect to WebSocket manager
        await audit_websocket_manager.connect(websocket, user_id)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                
                # Parse incoming message
                try:
                    message = json.loads(data)
                    await handle_client_message(websocket, user_id, message)
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": "2024-01-01T00:00:00"
                    }))
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user_id}")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message for user {user_id}: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}",
                    "timestamp": "2024-01-01T00:00:00"
                }))
                
    except Exception as e:
        logger.error(f"Error in WebSocket endpoint for user {user_id}: {e}")
    finally:
        # Ensure connection is cleaned up
        audit_websocket_manager.disconnect(websocket, user_id)


async def handle_client_message(websocket: WebSocket, user_id: str, message: Dict[str, Any]):
    """
    Handle incoming messages from WebSocket client
    
    Args:
        websocket: The WebSocket connection
        user_id: ID of the user
        message: The incoming message
    """
    try:
        message_type = message.get("type", "unknown")
        
        if message_type == "ping":
            # Respond to ping with pong
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": "2024-01-01T00:00:00"
            }))
            
        elif message_type == "subscribe":
            # Handle subscription requests
            event_types = message.get("event_types", [])
            await websocket.send_text(json.dumps({
                "type": "subscription_confirmed",
                "event_types": event_types,
                "message": f"Subscribed to {len(event_types)} event types",
                "timestamp": "2024-01-01T00:00:00"
            }))
            
        elif message_type == "unsubscribe":
            # Handle unsubscription requests
            await websocket.send_text(json.dumps({
                "type": "unsubscription_confirmed",
                "message": "Unsubscribed from all events",
                "timestamp": "2024-01-01T00:00:00"
            }))
            
        elif message_type == "get_stats":
            # Send connection statistics
            stats = await audit_websocket_manager.get_connection_stats()
            await websocket.send_text(json.dumps({
                "type": "connection_stats",
                "stats": stats,
                "timestamp": "2024-01-01T00:00:00"
            }))
            
        else:
            # Unknown message type
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": "2024-01-01T00:00:00"
            }))
            
    except Exception as e:
        logger.error(f"Error handling client message: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Error processing message: {str(e)}",
            "timestamp": "2024-01-01T00:00:00"
        }))


@router.get("/ws/audit/test", response_class=HTMLResponse)
async def audit_websocket_test_page():
    """
    Test page for WebSocket audit functionality
    
    Returns:
        HTMLResponse: Test page HTML
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Audit WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .connected { background-color: #d4edda; color: #155724; }
            .disconnected { background-color: #f8d7da; color: #721c24; }
            .message { background-color: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 4px solid #007bff; }
            .error { background-color: #f8d7da; border-left-color: #dc3545; }
            .audit-event { background-color: #e2e3e5; border-left-color: #6c757d; }
            #messages { max-height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; }
            button { padding: 10px 20px; margin: 5px; cursor: pointer; }
            input { padding: 8px; margin: 5px; width: 200px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Audit WebSocket Test</h1>
            
            <div id="status" class="status disconnected">Disconnected</div>
            
            <div>
                <input type="text" id="userId" placeholder="User ID" value="test_user">
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
                <button onclick="sendPing()">Ping</button>
                <button onclick="getStats()">Get Stats</button>
                <button onclick="clearMessages()">Clear Messages</button>
            </div>
            
            <div>
                <h3>Messages</h3>
                <div id="messages"></div>
            </div>
            
            <div>
                <h3>Connection Statistics</h3>
                <div id="stats"></div>
            </div>
        </div>

        <script>
            let ws = null;
            let messageCount = 0;

            function connect() {
                const userId = document.getElementById('userId').value;
                if (!userId) {
                    alert('Please enter a user ID');
                    return;
                }

                const wsUrl = `ws://localhost:8888/api/v1/audit/ws/audit/${userId}`;
                ws = new WebSocket(wsUrl);

                ws.onopen = function(event) {
                    updateStatus('Connected', 'connected');
                    addMessage('WebSocket connection established', 'message');
                };

                ws.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        addMessage(JSON.stringify(data, null, 2), data.type === 'error' ? 'error' : 'message');
                        
                        if (data.type === 'audit_event') {
                            addMessage(`Audit Event: ${data.event_type} by ${data.user_id}`, 'audit-event');
                        }
                    } catch (e) {
                        addMessage(event.data, 'message');
                    }
                };

                ws.onclose = function(event) {
                    updateStatus('Disconnected', 'disconnected');
                    addMessage('WebSocket connection closed', 'message');
                };

                ws.onerror = function(error) {
                    updateStatus('Error', 'disconnected');
                    addMessage('WebSocket error: ' + error, 'error');
                };
            }

            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }

            function sendPing() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'ping' }));
                } else {
                    alert('WebSocket not connected');
                }
            }

            function getStats() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'get_stats' }));
                } else {
                    alert('WebSocket not connected');
                }
            }

            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
                messageCount = 0;
            }

            function updateStatus(text, className) {
                const status = document.getElementById('status');
                status.textContent = text;
                status.className = 'status ' + className;
            }

            function addMessage(text, className) {
                const messages = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + className;
                messageDiv.innerHTML = `<strong>${++messageCount}:</strong> ${text}`;
                messages.appendChild(messageDiv);
                messages.scrollTop = messages.scrollHeight;
            }

            // Auto-connect on page load
            window.onload = function() {
                connect();
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/ws/audit/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics
    
    Returns:
        Dict[str, Any]: Connection statistics
    """
    try:
        stats = await audit_websocket_manager.get_connection_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ws/audit/health")
async def websocket_health_check():
    """
    Health check for WebSocket service
    
    Returns:
        Dict[str, Any]: Health status
    """
    try:
        return await audit_websocket_manager.health_check()
    except Exception as e:
        logger.error(f"Error in WebSocket health check: {e}")
        return {
            "status": "unhealthy",
            "service": "audit_websocket",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00"
        }
