"""
WebSocket connection manager for handling multiple connections
"""

from typing import Dict, Set, List, Optional, Any
from fastapi import WebSocket
import json
import asyncio
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and message routing
    """
    
    def __init__(self):
        # Active connections: websocket -> user_id mapping
        self.active_connections: Dict[WebSocket, Optional[str]] = {}
        
        # User connections: user_id -> set of websockets
        self.user_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        
        # Channel subscriptions: channel -> set of websockets
        self.channel_subscriptions: Dict[str, Set[WebSocket]] = defaultdict(set)
        
        # WebSocket to channels mapping
        self.websocket_channels: Dict[WebSocket, Set[str]] = defaultdict(set)
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """
        Accept and register a new WebSocket connection
        
        Args:
            websocket: The WebSocket connection
            user_id: Optional user ID for authenticated connections
        """
        await websocket.accept()
        
        async with self._lock:
            self.active_connections[websocket] = user_id
            
            if user_id:
                self.user_connections[user_id].add(websocket)
                
            logger.info(f"Connection established. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """
        Remove a WebSocket connection and clean up subscriptions
        
        Args:
            websocket: The WebSocket connection to remove
            user_id: Optional user ID for cleanup
        """
        try:
            # Remove from active connections
            if websocket in self.active_connections:
                del self.active_connections[websocket]
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove from all channel subscriptions
            channels = self.websocket_channels.get(websocket, set())
            for channel in channels:
                self.channel_subscriptions[channel].discard(websocket)
                if not self.channel_subscriptions[channel]:
                    del self.channel_subscriptions[channel]
            
            # Clean up websocket channels mapping
            if websocket in self.websocket_channels:
                del self.websocket_channels[websocket]
            
            logger.info(f"Connection removed. Total connections: {len(self.active_connections)}")
            
        except Exception as e:
            logger.error(f"Error disconnecting websocket: {e}")
    
    async def send_personal_message(self, message: Any, websocket: WebSocket):
        """
        Send a message to a specific WebSocket connection
        
        Args:
            message: The message to send (will be JSON-encoded if dict)
            websocket: The target WebSocket connection
        """
        try:
            if isinstance(message, dict):
                await websocket.send_json(message)
            else:
                await websocket.send_text(str(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            # Connection might be closed, clean it up
            user_id = self.active_connections.get(websocket)
            self.disconnect(websocket, user_id)
    
    async def send_to_user(self, user_id: str, message: Any):
        """
        Send a message to all connections of a specific user
        
        Args:
            user_id: The target user ID
            message: The message to send
        """
        connections = self.user_connections.get(user_id, set()).copy()
        
        for websocket in connections:
            await self.send_personal_message(message, websocket)
    
    async def broadcast(self, message: Any, exclude: Optional[List[WebSocket]] = None):
        """
        Broadcast a message to all connected clients
        
        Args:
            message: The message to broadcast
            exclude: Optional list of WebSockets to exclude
        """
        exclude = exclude or []
        disconnected = []
        
        for websocket in self.active_connections:
            if websocket not in exclude:
                try:
                    await self.send_personal_message(message, websocket)
                except Exception as e:
                    logger.error(f"Error broadcasting to websocket: {e}")
                    disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            user_id = self.active_connections.get(websocket)
            self.disconnect(websocket, user_id)
    
    async def subscribe_to_channel(self, websocket: WebSocket, channel: str):
        """
        Subscribe a WebSocket to a channel
        
        Args:
            websocket: The WebSocket connection
            channel: The channel name
        """
        async with self._lock:
            self.channel_subscriptions[channel].add(websocket)
            self.websocket_channels[websocket].add(channel)
            
        logger.info(f"WebSocket subscribed to channel: {channel}")
    
    async def unsubscribe_from_channel(self, websocket: WebSocket, channel: str):
        """
        Unsubscribe a WebSocket from a channel
        
        Args:
            websocket: The WebSocket connection
            channel: The channel name
        """
        async with self._lock:
            self.channel_subscriptions[channel].discard(websocket)
            if not self.channel_subscriptions[channel]:
                del self.channel_subscriptions[channel]
            
            self.websocket_channels[websocket].discard(channel)
            
        logger.info(f"WebSocket unsubscribed from channel: {channel}")
    
    async def broadcast_to_channel(
        self,
        channel: str,
        message: Any,
        exclude: Optional[List[WebSocket]] = None
    ):
        """
        Broadcast a message to all subscribers of a channel
        
        Args:
            channel: The channel name
            message: The message to broadcast
            exclude: Optional list of WebSockets to exclude
        """
        exclude = exclude or []
        subscribers = self.channel_subscriptions.get(channel, set()).copy()
        disconnected = []
        
        for websocket in subscribers:
            if websocket not in exclude:
                try:
                    await self.send_personal_message(message, websocket)
                except Exception as e:
                    logger.error(f"Error broadcasting to channel subscriber: {e}")
                    disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            user_id = self.active_connections.get(websocket)
            self.disconnect(websocket, user_id)
    
    def get_connection_count(self) -> int:
        """Get the total number of active connections"""
        return len(self.active_connections)
    
    def get_user_count(self) -> int:
        """Get the number of unique connected users"""
        return len(self.user_connections)
    
    def get_channel_count(self) -> int:
        """Get the number of active channels"""
        return len(self.channel_subscriptions)
    
    def get_channel_subscribers(self, channel: str) -> int:
        """Get the number of subscribers for a channel"""
        return len(self.channel_subscriptions.get(channel, set()))
    
    def get_user_channels(self, user_id: str) -> Set[str]:
        """Get all channels a user is subscribed to"""
        channels = set()
        for websocket in self.user_connections.get(user_id, set()):
            channels.update(self.websocket_channels.get(websocket, set()))
        return channels
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": self.get_connection_count(),
            "unique_users": self.get_user_count(),
            "active_channels": self.get_channel_count(),
            "channels": {
                channel: self.get_channel_subscribers(channel)
                for channel in self.channel_subscriptions
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all connections
        
        Returns:
            Health status of connections
        """
        healthy = 0
        unhealthy = 0
        
        for websocket in list(self.active_connections.keys()):
            try:
                # Try to ping the connection
                await websocket.send_json({"type": "health_check"})
                healthy += 1
            except Exception:
                unhealthy += 1
                # Remove unhealthy connection
                user_id = self.active_connections.get(websocket)
                self.disconnect(websocket, user_id)
        
        return {
            "status": "healthy" if unhealthy == 0 else "degraded",
            "healthy_connections": healthy,
            "unhealthy_connections": unhealthy,
            "total_connections": healthy + unhealthy
        }


# Singleton instance
connection_manager = ConnectionManager()