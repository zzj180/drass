"""
Notification service for handling real-time notifications
"""

import logging
from typing import Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications and real-time updates"""
    
    def __init__(self):
        self.subscribers = defaultdict(list)
    
    async def subscribe(self, session_id: str, callback):
        """Subscribe to notifications for a session"""
        self.subscribers[session_id].append(callback)
        logger.info(f"Subscribed to notifications for session: {session_id}")
    
    async def unsubscribe(self, session_id: str, callback):
        """Unsubscribe from notifications"""
        if session_id in self.subscribers:
            if callback in self.subscribers[session_id]:
                self.subscribers[session_id].remove(callback)
            if not self.subscribers[session_id]:
                del self.subscribers[session_id]
        logger.info(f"Unsubscribed from notifications for session: {session_id}")
    
    async def notify(self, session_id: str, message: Dict[str, Any]):
        """Send notification to all subscribers of a session"""
        if session_id in self.subscribers:
            for callback in self.subscribers[session_id]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Error sending notification: {e}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all sessions"""
        for session_id in self.subscribers:
            await self.notify(session_id, message)


# Singleton instance
notification_service = NotificationService()