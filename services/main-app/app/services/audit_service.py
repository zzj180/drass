"""
Audit Service
Handles audit logging and event tracking for compliance
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from enum import Enum
from dataclasses import dataclass, asdict
import json
import asyncio
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditEventType(Enum):
    """Audit event types"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_ACCESS = "document_access"
    COMPLIANCE_ANALYSIS = "compliance_analysis"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    API_ACCESS = "api_access"
    ERROR_EVENT = "error_event"
    SECURITY_EVENT = "security_event"
    OTHER = "other"


class AuditSeverity(Enum):
    """Audit event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(Enum):
    """Audit event status"""
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    PENDING = "pending"


@dataclass
class AuditLogEntry:
    """Audit log entry data structure"""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: str
    user_info: Dict[str, Any]
    request_id: Optional[str]
    request_context: Dict[str, Any]
    resource_type: str
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    severity: AuditSeverity
    status: AuditStatus
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    outcome: str
    error_message: Optional[str]
    metadata: Dict[str, Any]


class AuditService:
    """Service for managing audit logs and events"""
    
    def __init__(self):
        self.audit_logs: List[AuditLogEntry] = []
        self.audit_file_path = Path("./data/audit_logs.json")
        self.audit_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_audit_logs()
        self.event_broadcasters: List[callable] = []
    
    def _load_audit_logs(self):
        """Load audit logs from persistent storage"""
        try:
            if self.audit_file_path.exists():
                with open(self.audit_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry_data in data:
                        # Convert string enums back to enum objects
                        entry_data['event_type'] = AuditEventType(entry_data['event_type'])
                        entry_data['severity'] = AuditSeverity(entry_data['severity'])
                        entry_data['status'] = AuditStatus(entry_data['status'])
                        entry_data['timestamp'] = datetime.fromisoformat(entry_data['timestamp'])
                        
                        entry = AuditLogEntry(**entry_data)
                        self.audit_logs.append(entry)
                
                logger.info(f"Loaded {len(self.audit_logs)} audit log entries")
            else:
                logger.info("No existing audit logs found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading audit logs: {e}")
            self.audit_logs = []
    
    def _save_audit_logs(self):
        """Save audit logs to persistent storage"""
        try:
            # Convert audit logs to serializable format
            serializable_logs = []
            for entry in self.audit_logs:
                entry_dict = asdict(entry)
                # Convert enums to strings
                entry_dict['event_type'] = entry.event_type.value
                entry_dict['severity'] = entry.severity.value
                entry_dict['status'] = entry.status.value
                entry_dict['timestamp'] = entry.timestamp.isoformat()
                serializable_logs.append(entry_dict)
            
            with open(self.audit_file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_logs, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Saved {len(self.audit_logs)} audit log entries")
        except Exception as e:
            logger.error(f"Error saving audit logs: {e}")
    
    async def log_audit_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        details: Dict[str, Any],
        request_id: Optional[str] = None,
        resource_type: str = "system",
        resource_id: Optional[str] = None,
        action: str = "access",
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        status: AuditStatus = AuditStatus.SUCCESS,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        outcome: str = "completed",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLogEntry:
        """
        Log an audit event
        
        Args:
            event_type: Type of audit event
            user_id: ID of the user performing the action
            details: Additional details about the event
            request_id: ID of the request (optional)
            resource_type: Type of resource being accessed
            resource_id: ID of the resource (optional)
            action: Action being performed
            severity: Severity level of the event
            status: Status of the event
            ip_address: IP address of the user
            user_agent: User agent string
            session_id: Session ID
            outcome: Outcome of the action
            error_message: Error message if applicable
            metadata: Additional metadata
            
        Returns:
            AuditLogEntry: The created audit log entry
        """
        try:
            # Generate unique ID
            audit_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Get user information
            user_info = await self._get_user_info(user_id)
            
            # Get request context
            request_context = await self._get_request_context(request_id)
            
            # Create audit log entry
            audit_entry = AuditLogEntry(
                id=audit_id,
                timestamp=timestamp,
                event_type=event_type,
                user_id=user_id,
                user_info=user_info,
                request_id=request_id,
                request_context=request_context,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                details=details,
                severity=severity,
                status=status,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                outcome=outcome,
                error_message=error_message,
                metadata=metadata or {}
            )
            
            # Store audit log
            await self._store_audit_log(audit_entry)
            
            # Broadcast event
            await self._broadcast_audit_event(audit_entry)
            
            logger.info(f"Audit event logged: {event_type.value} by user {user_id}")
            return audit_entry
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            raise
    
    async def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information for audit logging"""
        try:
            # In a real implementation, this would query the user database
            # For demo purposes, return mock user information
            return {
                "user_id": user_id,
                "username": f"user_{user_id}",
                "email": f"user_{user_id}@example.com",
                "role": "user",
                "department": "IT",
                "last_login": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {
                "user_id": user_id,
                "username": "unknown",
                "email": "unknown@example.com",
                "role": "unknown",
                "error": str(e)
            }
    
    async def _get_request_context(self, request_id: Optional[str]) -> Dict[str, Any]:
        """Get request context information"""
        try:
            if not request_id:
                return {}
            
            # In a real implementation, this would query request logs or middleware
            # For demo purposes, return mock request context
            return {
                "request_id": request_id,
                "method": "POST",
                "path": "/api/v1/example",
                "headers": {
                    "content-type": "application/json",
                    "user-agent": "Mozilla/5.0"
                },
                "query_params": {},
                "body_size": 1024
            }
        except Exception as e:
            logger.error(f"Error getting request context: {e}")
            return {"error": str(e)}
    
    async def _store_audit_log(self, audit_entry: AuditLogEntry):
        """Store audit log entry"""
        try:
            # Add to in-memory list
            self.audit_logs.append(audit_entry)
            
            # Persist to file
            self._save_audit_logs()
            
            logger.debug(f"Stored audit log entry: {audit_entry.id}")
        except Exception as e:
            logger.error(f"Error storing audit log: {e}")
            raise
    
    async def _broadcast_audit_event(self, audit_entry: AuditLogEntry):
        """Broadcast audit event to subscribers"""
        try:
            # Broadcast to registered broadcasters
            for broadcaster in self.event_broadcasters:
                try:
                    if asyncio.iscoroutinefunction(broadcaster):
                        await broadcaster(audit_entry)
                    else:
                        broadcaster(audit_entry)
                except Exception as e:
                    logger.error(f"Error in audit event broadcaster: {e}")
            
            # Broadcast to WebSocket manager if available
            try:
                from app.websocket.audit_websocket import audit_websocket_manager
                await audit_websocket_manager.broadcast_audit_event(audit_entry)
            except ImportError:
                # WebSocket manager not available, skip
                pass
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket manager: {e}")
            
            logger.debug(f"Broadcasted audit event: {audit_entry.id}")
        except Exception as e:
            logger.error(f"Error broadcasting audit event: {e}")
    
    def add_event_broadcaster(self, broadcaster: callable):
        """Add an event broadcaster function"""
        self.event_broadcasters.append(broadcaster)
        logger.info(f"Added audit event broadcaster: {broadcaster.__name__}")
    
    def remove_event_broadcaster(self, broadcaster: callable):
        """Remove an event broadcaster function"""
        if broadcaster in self.event_broadcasters:
            self.event_broadcasters.remove(broadcaster)
            logger.info(f"Removed audit event broadcaster: {broadcaster.__name__}")
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        status: Optional[AuditStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogEntry]:
        """
        Get audit logs with filtering
        
        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            severity: Filter by severity
            status: Filter by status
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[AuditLogEntry]: Filtered audit log entries
        """
        try:
            filtered_logs = self.audit_logs.copy()
            
            # Apply filters
            if user_id:
                filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
            
            if event_type:
                filtered_logs = [log for log in filtered_logs if log.event_type == event_type]
            
            if severity:
                filtered_logs = [log for log in filtered_logs if log.severity == severity]
            
            if status:
                filtered_logs = [log for log in filtered_logs if log.status == status]
            
            if start_date:
                filtered_logs = [log for log in filtered_logs if log.timestamp >= start_date]
            
            if end_date:
                filtered_logs = [log for log in filtered_logs if log.timestamp <= end_date]
            
            # Sort by timestamp (newest first)
            filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply pagination
            start_idx = offset
            end_idx = offset + limit
            return filtered_logs[start_idx:end_idx]
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []
    
    async def get_audit_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get audit statistics
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Dict[str, Any]: Audit statistics
        """
        try:
            # Get logs in date range
            logs = await self.get_audit_logs(
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Get all logs for statistics
            )
            
            # Calculate statistics
            total_events = len(logs)
            success_events = len([log for log in logs if log.status == AuditStatus.SUCCESS])
            failure_events = len([log for log in logs if log.status == AuditStatus.FAILURE])
            warning_events = len([log for log in logs if log.status == AuditStatus.WARNING])
            
            # Count by event type
            event_type_counts = {}
            for log in logs:
                event_type = log.event_type.value
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            
            # Count by severity
            severity_counts = {}
            for log in logs:
                severity = log.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by user
            user_counts = {}
            for log in logs:
                user_id = log.user_id
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
            
            return {
                "total_events": total_events,
                "success_events": success_events,
                "failure_events": failure_events,
                "warning_events": warning_events,
                "success_rate": (success_events / total_events * 100) if total_events > 0 else 0,
                "event_type_counts": event_type_counts,
                "severity_counts": severity_counts,
                "user_counts": user_counts,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {e}")
            return {}
    
    async def search_audit_logs(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogEntry]:
        """
        Search audit logs by text query
        
        Args:
            query: Search query
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[AuditLogEntry]: Matching audit log entries
        """
        try:
            query_lower = query.lower()
            matching_logs = []
            
            for log in self.audit_logs:
                # Search in various fields
                searchable_text = [
                    log.event_type.value,
                    log.user_id,
                    log.action,
                    log.outcome,
                    log.resource_type,
                    str(log.details),
                    log.error_message or ""
                ]
                
                if any(query_lower in text.lower() for text in searchable_text):
                    matching_logs.append(log)
            
            # Sort by timestamp (newest first)
            matching_logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply pagination
            start_idx = offset
            end_idx = offset + limit
            return matching_logs[start_idx:end_idx]
            
        except Exception as e:
            logger.error(f"Error searching audit logs: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for audit service"""
        try:
            return {
                "status": "healthy",
                "service": "audit",
                "total_logs": len(self.audit_logs),
                "storage_path": str(self.audit_file_path),
                "broadcasters": len(self.event_broadcasters),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "audit",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Create service instance
audit_service = AuditService()
