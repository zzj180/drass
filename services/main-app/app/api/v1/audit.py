"""
Audit API endpoints
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from app.services.audit_service import (
    audit_service,
    AuditEventType,
    AuditSeverity,
    AuditStatus,
    AuditLogEntry
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class AuditEventRequest(BaseModel):
    """Request model for logging audit events"""
    event_type: str = Field(..., description="Type of audit event")
    user_id: str = Field(..., description="ID of the user performing the action")
    details: Dict[str, Any] = Field(..., description="Additional details about the event")
    request_id: Optional[str] = Field(None, description="ID of the request")
    resource_type: str = Field("system", description="Type of resource being accessed")
    resource_id: Optional[str] = Field(None, description="ID of the resource")
    action: str = Field("access", description="Action being performed")
    severity: str = Field("medium", description="Severity level of the event")
    status: str = Field("success", description="Status of the event")
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    session_id: Optional[str] = Field(None, description="Session ID")
    outcome: str = Field("completed", description="Outcome of the action")
    error_message: Optional[str] = Field(None, description="Error message if applicable")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AuditLogResponse(BaseModel):
    """Response model for audit log entries"""
    id: str
    timestamp: datetime
    event_type: str
    user_id: str
    user_info: Dict[str, Any]
    request_id: Optional[str]
    request_context: Dict[str, Any]
    resource_type: str
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    severity: str
    status: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    outcome: str
    error_message: Optional[str]
    metadata: Dict[str, Any]


class AuditStatisticsResponse(BaseModel):
    """Response model for audit statistics"""
    total_events: int
    success_events: int
    failure_events: int
    warning_events: int
    success_rate: float
    event_type_counts: Dict[str, int]
    severity_counts: Dict[str, int]
    user_counts: Dict[str, int]
    date_range: Dict[str, Optional[str]]


@router.post("/log", response_model=AuditLogResponse)
async def log_audit_event(request: AuditEventRequest):
    """
    Log an audit event
    
    Args:
        request: Audit event request
        
    Returns:
        AuditLogResponse: Created audit log entry
    """
    try:
        # Validate and convert enums
        try:
            event_type = AuditEventType(request.event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: {request.event_type}"
            )
        
        try:
            severity = AuditSeverity(request.severity)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity: {request.severity}"
            )
        
        try:
            status = AuditStatus(request.status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {request.status}"
            )
        
        # Log the audit event
        audit_entry = await audit_service.log_audit_event(
            event_type=event_type,
            user_id=request.user_id,
            details=request.details,
            request_id=request.request_id,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            action=request.action,
            severity=severity,
            status=status,
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            session_id=request.session_id,
            outcome=request.outcome,
            error_message=request.error_message,
            metadata=request.metadata
        )
        
        # Convert to response format
        response = AuditLogResponse(
            id=audit_entry.id,
            timestamp=audit_entry.timestamp,
            event_type=audit_entry.event_type.value,
            user_id=audit_entry.user_id,
            user_info=audit_entry.user_info,
            request_id=audit_entry.request_id,
            request_context=audit_entry.request_context,
            resource_type=audit_entry.resource_type,
            resource_id=audit_entry.resource_id,
            action=audit_entry.action,
            details=audit_entry.details,
            severity=audit_entry.severity.value,
            status=audit_entry.status.value,
            ip_address=audit_entry.ip_address,
            user_agent=audit_entry.user_agent,
            session_id=audit_entry.session_id,
            outcome=audit_entry.outcome,
            error_message=audit_entry.error_message,
            metadata=audit_entry.metadata
        )
        
        logger.info(f"Audit event logged: {audit_entry.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging audit event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(100, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip")
):
    """
    Get audit logs with filtering
    
    Returns:
        List[AuditLogResponse]: Filtered audit log entries
    """
    try:
        # Convert string parameters to enums
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AuditEventType(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event type: {event_type}"
                )
        
        severity_enum = None
        if severity:
            try:
                severity_enum = AuditSeverity(severity)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid severity: {severity}"
                )
        
        status_enum = None
        if status:
            try:
                status_enum = AuditStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}"
                )
        
        # Get audit logs
        audit_logs = await audit_service.get_audit_logs(
            user_id=user_id,
            event_type=event_type_enum,
            severity=severity_enum,
            status=status_enum,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        response = []
        for log in audit_logs:
            response.append(AuditLogResponse(
                id=log.id,
                timestamp=log.timestamp,
                event_type=log.event_type.value,
                user_id=log.user_id,
                user_info=log.user_info,
                request_id=log.request_id,
                request_context=log.request_context,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                action=log.action,
                details=log.details,
                severity=log.severity.value,
                status=log.status.value,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                session_id=log.session_id,
                outcome=log.outcome,
                error_message=log.error_message,
                metadata=log.metadata
            ))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[AuditLogResponse])
async def search_audit_logs(
    query: str = Query(..., description="Search query"),
    limit: int = Query(100, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip")
):
    """
    Search audit logs by text query
    
    Returns:
        List[AuditLogResponse]: Matching audit log entries
    """
    try:
        # Search audit logs
        audit_logs = await audit_service.search_audit_logs(
            query=query,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        response = []
        for log in audit_logs:
            response.append(AuditLogResponse(
                id=log.id,
                timestamp=log.timestamp,
                event_type=log.event_type.value,
                user_id=log.user_id,
                user_info=log.user_info,
                request_id=log.request_id,
                request_context=log.request_context,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                action=log.action,
                details=log.details,
                severity=log.severity.value,
                status=log.status.value,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                session_id=log.session_id,
                outcome=log.outcome,
                error_message=log.error_message,
                metadata=log.metadata
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error searching audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=AuditStatisticsResponse)
async def get_audit_statistics(
    start_date: Optional[datetime] = Query(None, description="Start date for statistics"),
    end_date: Optional[datetime] = Query(None, description="End date for statistics")
):
    """
    Get audit statistics
    
    Returns:
        AuditStatisticsResponse: Audit statistics
    """
    try:
        # Get statistics
        stats = await audit_service.get_audit_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return AuditStatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting audit statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/event-types")
async def get_event_types():
    """
    Get available audit event types
    
    Returns:
        List[str]: Available event types
    """
    try:
        return [event_type.value for event_type in AuditEventType]
    except Exception as e:
        logger.error(f"Error getting event types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/severity-levels")
async def get_severity_levels():
    """
    Get available severity levels
    
    Returns:
        List[str]: Available severity levels
    """
    try:
        return [severity.value for severity in AuditSeverity]
    except Exception as e:
        logger.error(f"Error getting severity levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status-types")
async def get_status_types():
    """
    Get available status types
    
    Returns:
        List[str]: Available status types
    """
    try:
        return [status.value for status in AuditStatus]
    except Exception as e:
        logger.error(f"Error getting status types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint for audit service
    
    Returns:
        Dict[str, Any]: Service health status
    """
    try:
        return await audit_service.health_check()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "audit",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
