"""
Enhanced Audit Service with Database Storage
Handles audit logging and event tracking for compliance with database persistence
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from enum import Enum
from dataclasses import dataclass, asdict
import json
import asyncio
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.core.logging import get_logger
from app.models.audit_log import (
    AuditLogDB, AuditLogArchive, AuditEventType, AuditSeverity, AuditStatus
)
from app.database.migration_manager import create_migration_manager

logger = get_logger(__name__)


@dataclass
class AuditLogEntry:
    """Audit log entry data structure"""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: str
    user_info: Dict[str, Any]
    user_name: str
    user_role: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Dict[str, Any]
    severity: AuditSeverity
    status: AuditStatus
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    request_id: Optional[str]
    outcome: str
    error_message: Optional[str]
    success: bool
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AuditServiceEnhanced:
    """Enhanced service for managing audit logs with database storage"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or "sqlite:///./data/audit_logs.db"
        self.migration_manager = create_migration_manager(self.database_url)
        self.engine = self.migration_manager.engine
        self.SessionLocal = self.migration_manager.SessionLocal
        
        # Ensure database is migrated
        self._ensure_database_ready()
        
        # Fallback to JSON storage for compatibility
        self.audit_file_path = Path("./data/audit_logs.json")
        self.audit_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.event_broadcasters: List[callable] = []
        
        # Cache for frequently accessed data
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    def _ensure_database_ready(self):
        """Ensure database is ready and migrated"""
        try:
            # Apply pending migrations
            if not self.migration_manager.migrate():
                logger.error("Failed to apply database migrations")
                raise Exception("Database migration failed")
            
            logger.info("Database is ready for audit logs")
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            # Fallback to JSON storage
            logger.warning("Falling back to JSON storage")
    
    def _get_db_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
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
        Log an audit event to database
        
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
            timestamp = datetime.utcnow()
            
            # Get user information
            user_info = await self._get_user_info(user_id)
            user_name = user_info.get("username", f"user_{user_id}")
            user_role = user_info.get("role")
            
            # Create audit log entry
            audit_entry = AuditLogEntry(
                id=audit_id,
                timestamp=timestamp,
                event_type=event_type,
                user_id=user_id,
                user_info=user_info,
                user_name=user_name,
                user_role=user_role,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                severity=severity,
                status=status,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                request_id=request_id,
                outcome=outcome,
                error_message=error_message,
                success=status == AuditStatus.SUCCESS,
                metadata=metadata or {},
                created_at=timestamp,
                updated_at=timestamp
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
            # Check cache first
            cache_key = f"user_info_{user_id}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if datetime.utcnow() - timestamp < timedelta(seconds=self._cache_ttl):
                    return cached_data
            
            # In a real implementation, this would query the user database
            # For demo purposes, return mock user information
            user_info = {
                "user_id": user_id,
                "username": f"user_{user_id}",
                "email": f"user_{user_id}@example.com",
                "role": "user",
                "department": "IT",
                "last_login": datetime.utcnow().isoformat()
            }
            
            # Cache the result
            self._cache[cache_key] = (user_info, datetime.utcnow())
            
            return user_info
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {
                "user_id": user_id,
                "username": "unknown",
                "email": "unknown@example.com",
                "role": "unknown",
                "error": str(e)
            }
    
    async def _store_audit_log(self, audit_entry: AuditLogEntry):
        """Store audit log entry to database"""
        try:
            db_session = self._get_db_session()
            try:
                # Create database record
                db_record = AuditLogDB(
                    id=audit_entry.id,
                    timestamp=audit_entry.timestamp,
                    event_type=audit_entry.event_type.value,
                    user_id=audit_entry.user_id,
                    user_name=audit_entry.user_name,
                    user_role=audit_entry.user_role,
                    action=audit_entry.action,
                    resource_type=audit_entry.resource_type,
                    resource_id=audit_entry.resource_id,
                    details=audit_entry.details,
                    severity=audit_entry.severity.value,
                    status=audit_entry.status.value,
                    ip_address=audit_entry.ip_address,
                    user_agent=audit_entry.user_agent,
                    session_id=audit_entry.session_id,
                    request_id=audit_entry.request_id,
                    outcome=audit_entry.outcome,
                    error_message=audit_entry.error_message,
                    success=audit_entry.success,
                    metadata_json=audit_entry.metadata,
                    created_at=audit_entry.created_at,
                    updated_at=audit_entry.updated_at
                )
                
                db_session.add(db_record)
                db_session.commit()
                
                logger.debug(f"Stored audit log entry to database: {audit_entry.id}")
                
            except Exception as e:
                db_session.rollback()
                raise e
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error storing audit log to database: {e}")
            # Fallback to JSON storage
            await self._store_audit_log_json(audit_entry)
    
    async def _store_audit_log_json(self, audit_entry: AuditLogEntry):
        """Fallback: Store audit log entry to JSON file"""
        try:
            # Load existing logs
            existing_logs = []
            if self.audit_file_path.exists():
                with open(self.audit_file_path, 'r', encoding='utf-8') as f:
                    existing_logs = json.load(f)
            
            # Add new entry
            entry_dict = asdict(audit_entry)
            # Convert enums to strings
            entry_dict['event_type'] = audit_entry.event_type.value
            entry_dict['severity'] = audit_entry.severity.value
            entry_dict['status'] = audit_entry.status.value
            entry_dict['timestamp'] = audit_entry.timestamp.isoformat()
            entry_dict['created_at'] = audit_entry.created_at.isoformat()
            entry_dict['updated_at'] = audit_entry.updated_at.isoformat()
            # Remove user_info field for JSON storage
            if 'user_info' in entry_dict:
                del entry_dict['user_info']
            
            existing_logs.append(entry_dict)
            
            # Save back to file
            with open(self.audit_file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_logs, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Stored audit log entry to JSON: {audit_entry.id}")
            
        except Exception as e:
            logger.error(f"Error storing audit log to JSON: {e}")
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
        Get audit logs with filtering from database
        
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
            db_session = self._get_db_session()
            try:
                # Build query
                query = db_session.query(AuditLogDB)
                
                # Apply filters
                if user_id:
                    query = query.filter(AuditLogDB.user_id == user_id)
                
                if event_type:
                    query = query.filter(AuditLogDB.event_type == event_type.value)
                
                if severity:
                    query = query.filter(AuditLogDB.severity == severity.value)
                
                if status:
                    query = query.filter(AuditLogDB.status == status.value)
                
                if start_date:
                    query = query.filter(AuditLogDB.timestamp >= start_date)
                
                if end_date:
                    query = query.filter(AuditLogDB.timestamp <= end_date)
                
                # Order by timestamp (newest first)
                query = query.order_by(desc(AuditLogDB.timestamp))
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                # Execute query
                db_records = query.all()
                
                # Convert to AuditLogEntry objects
                audit_entries = []
                for record in db_records:
                    entry = AuditLogEntry(
                        id=record.id,
                        timestamp=record.timestamp,
                        event_type=AuditEventType(record.event_type),
                        user_id=record.user_id,
                        user_info={
                            "user_id": record.user_id,
                            "username": record.user_name,
                            "role": record.user_role or "user"
                        },
                        user_name=record.user_name,
                        user_role=record.user_role,
                        action=record.action,
                        resource_type=record.resource_type,
                        resource_id=record.resource_id,
                        details=record.details or {},
                        severity=AuditSeverity(record.severity),
                        status=AuditStatus(record.status),
                        ip_address=record.ip_address,
                        user_agent=record.user_agent,
                        session_id=record.session_id,
                        request_id=record.request_id,
                        outcome=record.outcome,
                        error_message=record.error_message,
                        success=record.success,
                        metadata=record.metadata_json or {},
                        created_at=record.created_at,
                        updated_at=record.updated_at
                    )
                    audit_entries.append(entry)
                
                return audit_entries
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting audit logs from database: {e}")
            # Fallback to JSON storage
            return await self._get_audit_logs_json(
                user_id, event_type, severity, status, start_date, end_date, limit, offset
            )
    
    async def _get_audit_logs_json(
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
        """Fallback: Get audit logs from JSON file"""
        try:
            if not self.audit_file_path.exists():
                return []
            
            with open(self.audit_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            filtered_logs = []
            for entry_data in data:
                # Convert string enums back to enum objects
                entry_data['event_type'] = AuditEventType(entry_data['event_type'])
                entry_data['severity'] = AuditSeverity(entry_data['severity'])
                entry_data['status'] = AuditStatus(entry_data['status'])
                entry_data['timestamp'] = datetime.fromisoformat(entry_data['timestamp'])
                entry_data['created_at'] = datetime.fromisoformat(entry_data['created_at'])
                entry_data['updated_at'] = datetime.fromisoformat(entry_data['updated_at'])
                
                # Add missing user_info field
                if 'user_info' not in entry_data:
                    entry_data['user_info'] = {
                        "user_id": entry_data.get('user_id', ''),
                        "username": entry_data.get('user_name', ''),
                        "role": entry_data.get('user_role', 'user')
                    }
                
                entry = AuditLogEntry(**entry_data)
                
                # Apply filters
                if user_id and entry.user_id != user_id:
                    continue
                if event_type and entry.event_type != event_type:
                    continue
                if severity and entry.severity != severity:
                    continue
                if status and entry.status != status:
                    continue
                if start_date and entry.timestamp < start_date:
                    continue
                if end_date and entry.timestamp > end_date:
                    continue
                
                filtered_logs.append(entry)
            
            # Sort by timestamp (newest first)
            filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply pagination
            start_idx = offset
            end_idx = offset + limit
            return filtered_logs[start_idx:end_idx]
            
        except Exception as e:
            logger.error(f"Error getting audit logs from JSON: {e}")
            return []
    
    async def get_audit_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get audit statistics from database
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Dict[str, Any]: Audit statistics
        """
        try:
            db_session = self._get_db_session()
            try:
                # Build base query
                query = db_session.query(AuditLogDB)
                
                # Apply date filters
                if start_date:
                    query = query.filter(AuditLogDB.timestamp >= start_date)
                if end_date:
                    query = query.filter(AuditLogDB.timestamp <= end_date)
                
                # Calculate statistics
                total_events = query.count()
                success_events = query.filter(AuditLogDB.success == True).count()
                failure_events = query.filter(AuditLogDB.success == False).count()
                warning_events = query.filter(AuditLogDB.status == AuditStatus.WARNING.value).count()
                
                # Count by event type
                event_type_counts = {}
                event_type_results = query.with_entities(
                    AuditLogDB.event_type, func.count(AuditLogDB.id)
                ).group_by(AuditLogDB.event_type).all()
                
                for event_type, count in event_type_results:
                    event_type_counts[event_type] = count
                
                # Count by severity
                severity_counts = {}
                severity_results = query.with_entities(
                    AuditLogDB.severity, func.count(AuditLogDB.id)
                ).group_by(AuditLogDB.severity).all()
                
                for severity, count in severity_results:
                    severity_counts[severity] = count
                
                # Count by user
                user_counts = {}
                user_results = query.with_entities(
                    AuditLogDB.user_id, func.count(AuditLogDB.id)
                ).group_by(AuditLogDB.user_id).all()
                
                for user_id, count in user_results:
                    user_counts[user_id] = count
                
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
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting audit statistics from database: {e}")
            return {}
    
    async def search_audit_logs(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogEntry]:
        """
        Search audit logs by text query in database
        
        Args:
            query: Search query
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[AuditLogEntry]: Matching audit log entries
        """
        try:
            db_session = self._get_db_session()
            try:
                # Build search query
                search_query = db_session.query(AuditLogDB)
                
                # Search in various fields
                search_conditions = or_(
                    AuditLogDB.event_type.ilike(f"%{query}%"),
                    AuditLogDB.user_id.ilike(f"%{query}%"),
                    AuditLogDB.user_name.ilike(f"%{query}%"),
                    AuditLogDB.action.ilike(f"%{query}%"),
                    AuditLogDB.outcome.ilike(f"%{query}%"),
                    AuditLogDB.resource_type.ilike(f"%{query}%"),
                    AuditLogDB.error_message.ilike(f"%{query}%")
                )
                
                search_query = search_query.filter(search_conditions)
                search_query = search_query.order_by(desc(AuditLogDB.timestamp))
                search_query = search_query.offset(offset).limit(limit)
                
                # Execute query
                db_records = search_query.all()
                
                # Convert to AuditLogEntry objects
                audit_entries = []
                for record in db_records:
                    entry = AuditLogEntry(
                        id=record.id,
                        timestamp=record.timestamp,
                        event_type=AuditEventType(record.event_type),
                        user_id=record.user_id,
                        user_info={
                            "user_id": record.user_id,
                            "username": record.user_name,
                            "role": record.user_role or "user"
                        },
                        user_name=record.user_name,
                        user_role=record.user_role,
                        action=record.action,
                        resource_type=record.resource_type,
                        resource_id=record.resource_id,
                        details=record.details or {},
                        severity=AuditSeverity(record.severity),
                        status=AuditStatus(record.status),
                        ip_address=record.ip_address,
                        user_agent=record.user_agent,
                        session_id=record.session_id,
                        request_id=record.request_id,
                        outcome=record.outcome,
                        error_message=record.error_message,
                        success=record.success,
                        metadata=record.metadata_json or {},
                        created_at=record.created_at,
                        updated_at=record.updated_at
                    )
                    audit_entries.append(entry)
                
                return audit_entries
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error searching audit logs in database: {e}")
            return []
    
    async def archive_old_logs(self, days_old: int = 90) -> int:
        """
        Archive old audit logs to archive table
        
        Args:
            days_old: Number of days old logs to archive
            
        Returns:
            int: Number of logs archived
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            db_session = self._get_db_session()
            try:
                # Get old logs
                old_logs = db_session.query(AuditLogDB).filter(
                    AuditLogDB.timestamp < cutoff_date
                ).all()
                
                archived_count = 0
                for log in old_logs:
                    # Create archive record
                    archive_record = AuditLogArchive(
                        id=log.id,
                        timestamp=log.timestamp,
                        event_type=log.event_type,
                        user_id=log.user_id,
                        user_name=log.user_name,
                        user_role=log.user_role,
                        action=log.action,
                        resource_type=log.resource_type,
                        resource_id=log.resource_id,
                        details=log.details,
                        severity=log.severity,
                        status=log.status,
                        ip_address=log.ip_address,
                        user_agent=log.user_agent,
                        session_id=log.session_id,
                        request_id=log.request_id,
                        outcome=log.outcome,
                        error_message=log.error_message,
                        success=log.success,
                        metadata=log.metadata,
                        archived_at=datetime.utcnow(),
                        original_created_at=log.created_at,
                        original_updated_at=log.updated_at
                    )
                    
                    db_session.add(archive_record)
                    
                    # Delete original record
                    db_session.delete(log)
                    
                    archived_count += 1
                
                db_session.commit()
                logger.info(f"Archived {archived_count} old audit logs")
                return archived_count
                
            except Exception as e:
                db_session.rollback()
                raise e
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error archiving old logs: {e}")
            return 0
    
    def add_event_broadcaster(self, broadcaster: callable):
        """Add an event broadcaster function"""
        self.event_broadcasters.append(broadcaster)
        logger.info(f"Added audit event broadcaster: {broadcaster.__name__}")
    
    def remove_event_broadcaster(self, broadcaster: callable):
        """Remove an event broadcaster function"""
        if broadcaster in self.event_broadcasters:
            self.event_broadcasters.remove(broadcaster)
            logger.info(f"Removed audit event broadcaster: {broadcaster.__name__}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for enhanced audit service"""
        try:
            # Check database connection
            db_session = self._get_db_session()
            try:
                # Test database query
                count = db_session.query(AuditLogDB).count()
                
                # Get migration status
                migration_status = self.migration_manager.get_migration_status()
                
                return {
                    "status": "healthy",
                    "service": "audit_enhanced",
                    "database_connected": True,
                    "total_logs": count,
                    "migration_status": migration_status,
                    "storage_type": "database",
                    "fallback_storage": "json",
                    "broadcasters": len(self.event_broadcasters),
                    "timestamp": datetime.utcnow().isoformat()
                }
            finally:
                db_session.close()
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "audit_enhanced",
                "database_connected": False,
                "error": str(e),
                "storage_type": "json_fallback",
                "timestamp": datetime.utcnow().isoformat()
            }


# Create enhanced service instance
audit_service_enhanced = AuditServiceEnhanced()
