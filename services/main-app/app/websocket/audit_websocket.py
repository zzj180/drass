"""
Audit WebSocket Manager
Handles real-time audit event broadcasting via WebSocket
"""

import asyncio
import json
import logging
from typing import Dict, Set, List, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import asdict

from app.services.audit_service import AuditLogEntry
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditWebSocketManager:
    """Manages WebSocket connections for real-time audit event broadcasting"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        # Store broadcast queues for each connection
        self.broadcast_queues: Dict[WebSocket, asyncio.Queue] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Accept a WebSocket connection and add it to the active connections
        
        Args:
            websocket: The WebSocket connection
            user_id: ID of the user connecting
        """
        try:
            await websocket.accept()
            
            async with self._lock:
                # Add connection to user's connection set
                if user_id not in self.active_connections:
                    self.active_connections[user_id] = set()
                
                self.active_connections[user_id].add(websocket)
                
                # Store connection metadata
                self.connection_metadata[websocket] = {
                    "user_id": user_id,
                    "connected_at": datetime.now(),
                    "last_activity": datetime.now(),
                    "message_count": 0
                }
                
                # Create broadcast queue for this connection
                self.broadcast_queues[websocket] = asyncio.Queue(maxsize=100)
                
                logger.info(f"WebSocket connected for user {user_id}")
                
                # Send welcome message
                await self._send_to_connection(websocket, {
                    "type": "connection_established",
                    "message": "Connected to audit event stream",
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Start message processing for this connection
                asyncio.create_task(self._process_connection_messages(websocket))
                
        except Exception as e:
            logger.error(f"Error connecting WebSocket for user {user_id}: {e}")
            await self.disconnect(websocket, user_id)
    
    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Remove a WebSocket connection from active connections
        
        Args:
            websocket: The WebSocket connection to remove
            user_id: ID of the user disconnecting
        """
        try:
            async def _disconnect():
                async with self._lock:
                    # Remove from user's connections
                    if user_id in self.active_connections:
                        self.active_connections[user_id].discard(websocket)
                        
                        # Clean up empty user connection sets
                        if not self.active_connections[user_id]:
                            del self.active_connections[user_id]
                    
                    # Remove metadata
                    if websocket in self.connection_metadata:
                        del self.connection_metadata[websocket]
                    
                    # Remove broadcast queue
                    if websocket in self.broadcast_queues:
                        del self.broadcast_queues[websocket]
                    
                    logger.info(f"WebSocket disconnected for user {user_id}")
            
            # Run the disconnect logic
            asyncio.create_task(_disconnect())
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket for user {user_id}: {e}")
    
    async def broadcast_audit_event(self, audit_entry: AuditLogEntry) -> None:
        """
        Broadcast an audit event to all connected users
        
        Args:
            audit_entry: The audit log entry to broadcast
        """
        try:
            # Convert audit entry to broadcastable format
            event_data = {
                "type": "audit_event",
                "event_id": audit_entry.id,
                "timestamp": audit_entry.timestamp.isoformat(),
                "event_type": audit_entry.event_type.value,
                "user_id": audit_entry.user_id,
                "user_info": audit_entry.user_info,
                "resource_type": audit_entry.resource_type,
                "resource_id": audit_entry.resource_id,
                "action": audit_entry.action,
                "severity": audit_entry.severity.value,
                "status": audit_entry.status.value,
                "outcome": audit_entry.outcome,
                "details": audit_entry.details,
                "metadata": audit_entry.metadata
            }
            
            # Broadcast to all active connections
            await self._broadcast_to_all(event_data)
            
            logger.debug(f"Broadcasted audit event {audit_entry.id} to all connections")
            
        except Exception as e:
            logger.error(f"Error broadcasting audit event: {e}")
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to a specific user
        
        Args:
            user_id: ID of the user to send message to
            message: Message to send
        """
        try:
            async with self._lock:
                if user_id in self.active_connections:
                    connections = self.active_connections[user_id].copy()
                    
                    for websocket in connections:
                        try:
                            await self._send_to_connection(websocket, message)
                        except Exception as e:
                            logger.error(f"Error sending message to user {user_id}: {e}")
                            # Remove failed connection
                            self.active_connections[user_id].discard(websocket)
                            if websocket in self.connection_metadata:
                                del self.connection_metadata[websocket]
                            if websocket in self.broadcast_queues:
                                del self.broadcast_queues[websocket]
            
            logger.debug(f"Broadcasted message to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting to user {user_id}: {e}")
    
    async def _broadcast_to_all(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all active connections
        
        Args:
            message: Message to broadcast
        """
        try:
            async with self._lock:
                all_connections = []
                for user_connections in self.active_connections.values():
                    all_connections.extend(user_connections)
                
                # Send to all connections
                for websocket in all_connections:
                    try:
                        await self._send_to_connection(websocket, message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to connection: {e}")
                        # Remove failed connection
                        await self._remove_failed_connection(websocket)
            
        except Exception as e:
            logger.error(f"Error in broadcast to all: {e}")
    
    async def _send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """
        Send a message to a specific WebSocket connection
        
        Args:
            websocket: The WebSocket connection
            message: Message to send
        """
        try:
            # Add to broadcast queue
            if websocket in self.broadcast_queues:
                try:
                    self.broadcast_queues[websocket].put_nowait(message)
                except asyncio.QueueFull:
                    logger.warning("Broadcast queue full, dropping message")
            
        except Exception as e:
            logger.error(f"Error queuing message for connection: {e}")
    
    async def _process_connection_messages(self, websocket: WebSocket) -> None:
        """
        Process messages for a specific connection
        
        Args:
            websocket: The WebSocket connection
        """
        try:
            while True:
                # Get message from queue
                if websocket in self.broadcast_queues:
                    try:
                        message = await asyncio.wait_for(
                            self.broadcast_queues[websocket].get(),
                            timeout=1.0
                        )
                        
                        # Send message via WebSocket
                        await websocket.send_text(json.dumps(message, ensure_ascii=False))
                        
                        # Update connection metadata
                        if websocket in self.connection_metadata:
                            self.connection_metadata[websocket]["last_activity"] = datetime.now()
                            self.connection_metadata[websocket]["message_count"] += 1
                        
                    except asyncio.TimeoutError:
                        # No message in queue, continue
                        continue
                    except WebSocketDisconnect:
                        # Connection closed
                        break
                    except Exception as e:
                        logger.error(f"Error processing message for connection: {e}")
                        break
                else:
                    # Connection no longer exists
                    break
                    
        except Exception as e:
            logger.error(f"Error in message processing for connection: {e}")
        finally:
            # Clean up connection
            await self._cleanup_connection(websocket)
    
    async def _remove_failed_connection(self, websocket: WebSocket) -> None:
        """
        Remove a failed connection from all tracking structures
        
        Args:
            websocket: The failed WebSocket connection
        """
        try:
            async with self._lock:
                # Find and remove from user connections
                for user_id, connections in self.active_connections.items():
                    if websocket in connections:
                        connections.discard(websocket)
                        if not connections:
                            del self.active_connections[user_id]
                        break
                
                # Remove metadata
                if websocket in self.connection_metadata:
                    del self.connection_metadata[websocket]
                
                # Remove broadcast queue
                if websocket in self.broadcast_queues:
                    del self.broadcast_queues[websocket]
                
        except Exception as e:
            logger.error(f"Error removing failed connection: {e}")
    
    async def _cleanup_connection(self, websocket: WebSocket) -> None:
        """
        Clean up a connection when it's closed
        
        Args:
            websocket: The WebSocket connection to clean up
        """
        try:
            # Find user_id for this connection
            user_id = None
            if websocket in self.connection_metadata:
                user_id = self.connection_metadata[websocket].get("user_id")
            
            if user_id:
                self.disconnect(websocket, user_id)
            
        except Exception as e:
            logger.error(f"Error cleaning up connection: {e}")
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about active connections
        
        Returns:
            Dict[str, Any]: Connection statistics
        """
        try:
            async with self._lock:
                total_connections = sum(len(connections) for connections in self.active_connections.values())
                total_users = len(self.active_connections)
                
                # Calculate average messages per connection
                total_messages = sum(
                    metadata.get("message_count", 0)
                    for metadata in self.connection_metadata.values()
                )
                avg_messages = total_messages / total_connections if total_connections > 0 else 0
                
                # Get connection age statistics
                now = datetime.now()
                connection_ages = []
                for metadata in self.connection_metadata.values():
                    connected_at = metadata.get("connected_at", now)
                    age_seconds = (now - connected_at).total_seconds()
                    connection_ages.append(age_seconds)
                
                avg_age = sum(connection_ages) / len(connection_ages) if connection_ages else 0
                
                return {
                    "total_connections": total_connections,
                    "total_users": total_users,
                    "total_messages_sent": total_messages,
                    "average_messages_per_connection": avg_messages,
                    "average_connection_age_seconds": avg_age,
                    "users_with_connections": list(self.active_connections.keys()),
                    "timestamp": now.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting connection stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Health check for WebSocket manager
        
        Returns:
            Dict[str, Any]: Health status
        """
        try:
            stats = await self.get_connection_stats()
            
            return {
                "status": "healthy",
                "service": "audit_websocket",
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "audit_websocket",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Create global WebSocket manager instance
audit_websocket_manager = AuditWebSocketManager()
