"""
Message queue integration for WebSocket communication
Supports Redis Pub/Sub for distributed WebSocket servers
"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any, Callable
import redis.asyncio as aioredis
from redis.asyncio.client import PubSub

from app.core.config import settings
from app.api.v1.connection_manager import connection_manager

logger = logging.getLogger(__name__)


class MessageQueue:
    """
    Message queue for distributing WebSocket messages across multiple servers
    """
    
    def __init__(self, redis_url: str = None):
        """
        Initialize message queue with Redis connection
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client: Optional[aioredis.Redis] = None
        self.pubsub: Optional[PubSub] = None
        self.subscriptions: Dict[str, Callable] = {}
        self.listener_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def connect(self):
        """
        Connect to Redis and setup pub/sub
        """
        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Setup pub/sub
            self.pubsub = self.redis_client.pubsub()
            
            # Start listener
            self._running = True
            self.listener_task = asyncio.create_task(self._listen())
            
            logger.info("Message queue connected to Redis")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """
        Disconnect from Redis and cleanup
        """
        self._running = False
        
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Message queue disconnected from Redis")
    
    async def publish(self, channel: str, message: Dict[str, Any]):
        """
        Publish a message to a channel
        
        Args:
            channel: Channel name
            message: Message to publish
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return
        
        try:
            # Serialize message
            message_json = json.dumps(message)
            
            # Publish to Redis
            await self.redis_client.publish(channel, message_json)
            
            logger.debug(f"Published message to channel {channel}")
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
    
    async def subscribe(self, channel: str, callback: Callable = None):
        """
        Subscribe to a channel
        
        Args:
            channel: Channel name
            callback: Optional callback function for messages
        """
        if not self.pubsub:
            logger.warning("PubSub not initialized")
            return
        
        try:
            # Subscribe to channel
            await self.pubsub.subscribe(channel)
            
            # Register callback if provided
            if callback:
                self.subscriptions[channel] = callback
            
            logger.info(f"Subscribed to channel: {channel}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel}: {e}")
    
    async def unsubscribe(self, channel: str):
        """
        Unsubscribe from a channel
        
        Args:
            channel: Channel name
        """
        if not self.pubsub:
            return
        
        try:
            await self.pubsub.unsubscribe(channel)
            
            # Remove callback
            if channel in self.subscriptions:
                del self.subscriptions[channel]
            
            logger.info(f"Unsubscribed from channel: {channel}")
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from channel {channel}: {e}")
    
    async def _listen(self):
        """
        Listen for messages from subscribed channels
        """
        if not self.pubsub:
            return
        
        logger.info("Starting message queue listener")
        
        while self._running:
            try:
                # Get message with timeout
                message = await asyncio.wait_for(
                    self.pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=1.0
                )
                
                if message:
                    await self._handle_message(message)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in message listener: {e}")
                await asyncio.sleep(1)
    
    async def _handle_message(self, message: Dict[str, Any]):
        """
        Handle incoming message from Redis
        
        Args:
            message: Redis pub/sub message
        """
        try:
            channel = message.get("channel")
            data = message.get("data")
            
            if not data:
                return
            
            # Parse JSON data
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError:
                parsed_data = {"raw": data}
            
            # Call registered callback
            if channel in self.subscriptions:
                callback = self.subscriptions[channel]
                if asyncio.iscoroutinefunction(callback):
                    await callback(parsed_data)
                else:
                    callback(parsed_data)
            
            # Default handling for WebSocket channels
            await self._route_to_websocket(channel, parsed_data)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _route_to_websocket(self, channel: str, data: Dict[str, Any]):
        """
        Route message to WebSocket connections
        
        Args:
            channel: Channel name
            data: Message data
        """
        # Route based on channel type
        if channel.startswith("user:"):
            # User-specific message
            user_id = channel.replace("user:", "")
            await connection_manager.send_to_user(user_id, data)
            
        elif channel.startswith("broadcast:"):
            # Broadcast message
            await connection_manager.broadcast(data)
            
        elif channel.startswith("channel:"):
            # Channel broadcast
            ws_channel = channel.replace("channel:", "")
            await connection_manager.broadcast_to_channel(ws_channel, data)


class WebSocketMessageBroker:
    """
    High-level message broker for WebSocket communication
    """
    
    def __init__(self):
        self.message_queue = MessageQueue()
        self._initialized = False
    
    async def initialize(self):
        """
        Initialize the message broker
        """
        if self._initialized:
            return
        
        try:
            await self.message_queue.connect()
            
            # Subscribe to system channels
            await self.message_queue.subscribe("broadcast:system")
            await self.message_queue.subscribe("broadcast:notifications")
            
            self._initialized = True
            logger.info("WebSocket message broker initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize message broker: {e}")
            raise
    
    async def shutdown(self):
        """
        Shutdown the message broker
        """
        if not self._initialized:
            return
        
        await self.message_queue.disconnect()
        self._initialized = False
        logger.info("WebSocket message broker shutdown")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """
        Send message to a specific user across all servers
        
        Args:
            user_id: Target user ID
            message: Message to send
        """
        await self.message_queue.publish(f"user:{user_id}", message)
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast message to all users across all servers
        
        Args:
            message: Message to broadcast
        """
        await self.message_queue.publish("broadcast:all", message)
    
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """
        Broadcast message to a channel across all servers
        
        Args:
            channel: Channel name
            message: Message to broadcast
        """
        await self.message_queue.publish(f"channel:{channel}", message)
    
    async def notify_user(self, user_id: str, notification: Dict[str, Any]):
        """
        Send notification to a user
        
        Args:
            user_id: Target user ID
            notification: Notification data
        """
        message = {
            "type": "notification",
            "data": notification,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_to_user(user_id, message)
    
    async def notify_all(self, notification: Dict[str, Any]):
        """
        Send notification to all users
        
        Args:
            notification: Notification data
        """
        message = {
            "type": "notification",
            "data": notification,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(message)


# Global message broker instance
message_broker = WebSocketMessageBroker()


# Utility functions for easy access
async def send_websocket_message(user_id: str, message: Dict[str, Any]):
    """Send message to user via WebSocket"""
    await message_broker.send_to_user(user_id, message)


async def broadcast_websocket_message(message: Dict[str, Any]):
    """Broadcast message to all WebSocket connections"""
    await message_broker.broadcast(message)


async def send_channel_message(channel: str, message: Dict[str, Any]):
    """Send message to channel subscribers"""
    await message_broker.broadcast_to_channel(channel, message)