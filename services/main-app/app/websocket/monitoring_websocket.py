"""
Monitoring WebSocket Manager
Handles real-time monitoring updates via WebSocket connections
"""

import asyncio
import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from app.core.logging import get_logger
from app.services.monitoring_service import MonitoringResult, Alert, RiskIncident

logger = get_logger(__name__)


class MonitoringWebSocketManager:
    """Manages WebSocket connections for real-time monitoring updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a WebSocket connection for monitoring updates"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.connection_info[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        
        logger.info(f"Monitoring WebSocket connected for user {user_id}")
        
        # Send initial status
        await self._send_connection_status(websocket, "connected")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        if websocket in self.connection_info:
            del self.connection_info[websocket]
        
        logger.info(f"Monitoring WebSocket disconnected for user {user_id}")
    
    async def broadcast_monitoring_update(self, monitoring_result: MonitoringResult):
        """Broadcast monitoring update to all connected clients"""
        if not self.active_connections:
            return
        
        # Prepare monitoring data for broadcast
        monitoring_data = {
            "type": "monitoring_update",
            "timestamp": monitoring_result.timestamp.isoformat(),
            "compliance_score": monitoring_result.compliance_score,
            "overall_status": monitoring_result.overall_status,
            "metrics": {},
            "alerts": [],
            "risk_incidents": [],
            "metadata": monitoring_result.metadata
        }
        
        # Convert metrics
        for metric_type, metric in monitoring_result.metrics.items():
            monitoring_data["metrics"][metric_type.value] = {
                "value": metric.value,
                "unit": metric.unit,
                "status": metric.status,
                "threshold": metric.threshold,
                "timestamp": metric.timestamp.isoformat()
            }
        
        # Convert alerts
        for alert in monitoring_result.alerts:
            monitoring_data["alerts"].append({
                "id": alert.id,
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "metric_type": alert.metric_type.value,
                "threshold_value": alert.threshold_value,
                "actual_value": alert.actual_value,
                "timestamp": alert.timestamp.isoformat(),
                "acknowledged_by": alert.acknowledged_by,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "metadata": alert.metadata
            })
        
        # Convert risk incidents
        for incident in monitoring_result.risk_incidents:
            monitoring_data["risk_incidents"].append({
                "id": incident.id,
                "incident_type": incident.incident_type,
                "severity": incident.severity.value,
                "description": incident.description,
                "affected_resources": incident.affected_resources,
                "detected_at": incident.detected_at.isoformat(),
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                "mitigation_actions": incident.mitigation_actions or [],
                "metadata": incident.metadata
            })
        
        # Broadcast to all connected clients
        disconnected_websockets = []
        for user_id, websockets in self.active_connections.items():
            for websocket in websockets:
                try:
                    await websocket.send_text(json.dumps(monitoring_data))
                except Exception as e:
                    logger.error(f"Error sending monitoring update to user {user_id}: {e}")
                    disconnected_websockets.append((websocket, user_id))
        
        # Clean up disconnected websockets
        for websocket, user_id in disconnected_websockets:
            self.disconnect(websocket, user_id)
    
    async def broadcast_alert(self, alert: Alert):
        """Broadcast a specific alert to all connected clients"""
        if not self.active_connections:
            return
        
        alert_data = {
            "type": "alert",
            "alert": {
                "id": alert.id,
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "metric_type": alert.metric_type.value,
                "threshold_value": alert.threshold_value,
                "actual_value": alert.actual_value,
                "timestamp": alert.timestamp.isoformat(),
                "acknowledged_by": alert.acknowledged_by,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "metadata": alert.metadata
            }
        }
        
        # Broadcast to all connected clients
        disconnected_websockets = []
        for user_id, websockets in self.active_connections.items():
            for websocket in websockets:
                try:
                    await websocket.send_text(json.dumps(alert_data))
                except Exception as e:
                    logger.error(f"Error sending alert to user {user_id}: {e}")
                    disconnected_websockets.append((websocket, user_id))
        
        # Clean up disconnected websockets
        for websocket, user_id in disconnected_websockets:
            self.disconnect(websocket, user_id)
    
    async def broadcast_risk_incident(self, incident: RiskIncident):
        """Broadcast a risk incident to all connected clients"""
        if not self.active_connections:
            return
        
        incident_data = {
            "type": "risk_incident",
            "incident": {
                "id": incident.id,
                "incident_type": incident.incident_type,
                "severity": incident.severity.value,
                "description": incident.description,
                "affected_resources": incident.affected_resources,
                "detected_at": incident.detected_at.isoformat(),
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                "mitigation_actions": incident.mitigation_actions or [],
                "metadata": incident.metadata
            }
        }
        
        # Broadcast to all connected clients
        disconnected_websockets = []
        for user_id, websockets in self.active_connections.items():
            for websocket in websockets:
                try:
                    await websocket.send_text(json.dumps(incident_data))
                except Exception as e:
                    logger.error(f"Error sending risk incident to user {user_id}: {e}")
                    disconnected_websockets.append((websocket, user_id))
        
        # Clean up disconnected websockets
        for websocket, user_id in disconnected_websockets:
            self.disconnect(websocket, user_id)
    
    async def _send_connection_status(self, websocket: WebSocket, status: str):
        """Send connection status to a specific WebSocket"""
        try:
            status_data = {
                "type": "connection_status",
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_text(json.dumps(status_data))
        except Exception as e:
            logger.error(f"Error sending connection status: {e}")
    
    async def send_ping(self, websocket: WebSocket):
        """Send ping to keep connection alive"""
        try:
            ping_data = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_text(json.dumps(ping_data))
            
            # Update last ping time
            if websocket in self.connection_info:
                self.connection_info[websocket]["last_ping"] = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Error sending ping: {e}")
    
    async def handle_client_message(self, websocket: WebSocket, message: str, user_id: str):
        """Handle incoming messages from clients"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "pong":
                # Update last ping time
                if websocket in self.connection_info:
                    self.connection_info[websocket]["last_ping"] = datetime.utcnow()
            
            elif message_type == "subscribe":
                # Handle subscription requests
                subscription_type = data.get("subscription_type", "all")
                if websocket in self.connection_info:
                    self.connection_info[websocket]["subscription"] = subscription_type
                logger.info(f"User {user_id} subscribed to {subscription_type}")
            
            elif message_type == "unsubscribe":
                # Handle unsubscription requests
                if websocket in self.connection_info:
                    self.connection_info[websocket]["subscription"] = "none"
                logger.info(f"User {user_id} unsubscribed from monitoring updates")
            
            else:
                logger.warning(f"Unknown message type from user {user_id}: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from user {user_id}: {message}")
        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = sum(len(websockets) for websockets in self.active_connections.values())
        
        return {
            "total_connections": total_connections,
            "users_connected": len(self.active_connections),
            "connection_details": {
                user_id: len(websockets) 
                for user_id, websockets in self.active_connections.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup_stale_connections(self):
        """Clean up stale connections"""
        stale_connections = []
        current_time = datetime.utcnow()
        
        for websocket, info in self.connection_info.items():
            # Consider connection stale if no ping for more than 5 minutes
            if (current_time - info["last_ping"]).total_seconds() > 300:
                stale_connections.append((websocket, info["user_id"]))
        
        for websocket, user_id in stale_connections:
            logger.info(f"Cleaning up stale connection for user {user_id}")
            self.disconnect(websocket, user_id)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for monitoring WebSocket manager"""
        try:
            stats = self.get_connection_stats()
            return {
                "status": "healthy",
                "service": "monitoring_websocket",
                "connection_stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "monitoring_websocket",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Create manager instance
monitoring_websocket_manager = MonitoringWebSocketManager()
