"""
Enhanced Audit API endpoints
Provides optimized audit log query, export, and statistics functionality
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
import csv
import json
import io

from app.models.audit_log import (
    AuditEventType, AuditSeverity, AuditStatus, AuditLogSearchRequest, 
    AuditLogSearchResult, AuditLogStatistics
)
from app.services.audit_service_enhanced import audit_service_enhanced, AuditLogEntry
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-enhanced", tags=["audit-enhanced"])


@router.get("/health")
async def health_check():
    """Health check for enhanced audit service"""
    try:
        health_status = await audit_service_enhanced.health_check()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs", response_model=AuditLogSearchResult)
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_type: Optional[AuditEventType] = Query(None, description="Filter by event type"),
    severity: Optional[AuditSeverity] = Query(None, description="Filter by severity"),
    status: Optional[AuditStatus] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get audit logs with advanced filtering and pagination
    
    Args:
        user_id: Filter by user ID
        event_type: Filter by event type
        severity: Filter by severity level
        status: Filter by status
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum number of results (1-1000)
        offset: Number of results to skip
        
    Returns:
        AuditLogSearchResult: Paginated audit log results
    """
    try:
        # Get audit logs
        logs = await audit_service_enhanced.get_audit_logs(
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit + 1,  # Get one extra to check if there are more
            offset=offset
        )
        
        # Check if there are more results
        has_more = len(logs) > limit
        if has_more:
            logs = logs[:limit]  # Remove the extra result
        
        # Convert to response format
        log_responses = []
        for log in logs:
            log_responses.append({
                "id": log.id,
                "timestamp": log.timestamp,
                "event_type": log.event_type,
                "user_id": log.user_id,
                "user_name": log.user_name,
                "user_role": log.user_role,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "severity": log.severity,
                "status": log.status,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "session_id": log.session_id,
                "request_id": log.request_id,
                "outcome": log.outcome,
                "error_message": log.error_message,
                "success": log.success,
                "metadata": log.metadata,
                "created_at": log.created_at,
                "updated_at": log.updated_at
            })
        
        return AuditLogSearchResult(
            logs=log_responses,
            total_count=len(log_responses) + (1 if has_more else 0),
            has_more=has_more,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_audit_logs(
    q: str = Query(..., description="Search query"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user)
):
    """
    Search audit logs by text query
    
    Args:
        q: Search query
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        List of matching audit log entries
    """
    try:
        logs = await audit_service_enhanced.search_audit_logs(
            query=q,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        log_responses = []
        for log in logs:
            log_responses.append({
                "id": log.id,
                "timestamp": log.timestamp,
                "event_type": log.event_type,
                "user_id": log.user_id,
                "user_name": log.user_name,
                "user_role": log.user_role,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "severity": log.severity,
                "status": log.status,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "session_id": log.session_id,
                "request_id": log.request_id,
                "outcome": log.outcome,
                "error_message": log.error_message,
                "success": log.success,
                "metadata": log.metadata,
                "created_at": log.created_at,
                "updated_at": log.updated_at
            })
        
        return {
            "logs": log_responses,
            "total_count": len(log_responses),
            "has_more": len(log_responses) == limit,
            "limit": limit,
            "offset": offset,
            "query": q
        }
        
    except Exception as e:
        logger.error(f"Error searching audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=AuditLogStatistics)
async def get_audit_statistics(
    start_date: Optional[datetime] = Query(None, description="Start date for statistics"),
    end_date: Optional[datetime] = Query(None, description="End date for statistics"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get audit log statistics
    
    Args:
        start_date: Start date for statistics
        end_date: End date for statistics
        
    Returns:
        AuditLogStatistics: Audit log statistics
    """
    try:
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        statistics = await audit_service_enhanced.get_audit_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return AuditLogStatistics(**statistics)
        
    except Exception as e:
        logger.error(f"Error getting audit statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/csv")
async def export_audit_logs_csv(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_type: Optional[AuditEventType] = Query(None, description="Filter by event type"),
    severity: Optional[AuditSeverity] = Query(None, description="Filter by severity"),
    status: Optional[AuditStatus] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(10000, ge=1, le=50000, description="Maximum number of results to export"),
    current_user: dict = Depends(get_current_user)
):
    """
    Export audit logs to CSV format
    
    Args:
        user_id: Filter by user ID
        event_type: Filter by event type
        severity: Filter by severity level
        status: Filter by status
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum number of results to export
        
    Returns:
        CSV file download
    """
    try:
        # Get audit logs
        logs = await audit_service_enhanced.get_audit_logs(
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=0
        )
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "ID", "Timestamp", "Event Type", "User ID", "User Name", "User Role",
            "Action", "Resource Type", "Resource ID", "Severity", "Status",
            "IP Address", "User Agent", "Session ID", "Request ID", "Outcome",
            "Error Message", "Success", "Details", "Metadata", "Created At", "Updated At"
        ])
        
        # Write data rows
        for log in logs:
            writer.writerow([
                log.id,
                log.timestamp.isoformat(),
                log.event_type.value,
                log.user_id,
                log.user_name,
                log.user_role,
                log.action,
                log.resource_type,
                log.resource_id,
                log.severity.value,
                log.status.value,
                log.ip_address,
                log.user_agent,
                log.session_id,
                log.request_id,
                log.outcome,
                log.error_message,
                log.success,
                json.dumps(log.details, ensure_ascii=False),
                json.dumps(log.metadata, ensure_ascii=False),
                log.created_at.isoformat(),
                log.updated_at.isoformat()
            ])
        
        # Prepare response
        output.seek(0)
        csv_content = output.getvalue()
        output.close()
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_logs_{timestamp}.csv"
        
        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting audit logs to CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/json")
async def export_audit_logs_json(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_type: Optional[AuditEventType] = Query(None, description="Filter by event type"),
    severity: Optional[AuditSeverity] = Query(None, description="Filter by severity"),
    status: Optional[AuditStatus] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(10000, ge=1, le=50000, description="Maximum number of results to export"),
    current_user: dict = Depends(get_current_user)
):
    """
    Export audit logs to JSON format
    
    Args:
        user_id: Filter by user ID
        event_type: Filter by event type
        severity: Filter by severity level
        status: Filter by status
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum number of results to export
        
    Returns:
        JSON file download
    """
    try:
        # Get audit logs
        logs = await audit_service_enhanced.get_audit_logs(
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=0
        )
        
        # Convert to JSON format
        json_data = []
        for log in logs:
            json_data.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "event_type": log.event_type.value,
                "user_id": log.user_id,
                "user_name": log.user_name,
                "user_role": log.user_role,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "severity": log.severity.value,
                "status": log.status.value,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "session_id": log.session_id,
                "request_id": log.request_id,
                "outcome": log.outcome,
                "error_message": log.error_message,
                "success": log.success,
                "metadata": log.metadata,
                "created_at": log.created_at.isoformat(),
                "updated_at": log.updated_at.isoformat()
            })
        
        # Prepare response
        json_content = json.dumps(json_data, ensure_ascii=False, indent=2)
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_logs_{timestamp}.json"
        
        return StreamingResponse(
            io.BytesIO(json_content.encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting audit logs to JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/archive")
async def archive_old_logs(
    days_old: int = Query(90, ge=1, le=365, description="Number of days old logs to archive"),
    current_user: dict = Depends(get_current_user)
):
    """
    Archive old audit logs to archive table
    
    Args:
        days_old: Number of days old logs to archive
        
    Returns:
        Archive operation result
    """
    try:
        archived_count = await audit_service_enhanced.archive_old_logs(days_old=days_old)
        
        return {
            "message": f"Successfully archived {archived_count} audit logs",
            "archived_count": archived_count,
            "days_old": days_old,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error archiving old logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/migration/status")
async def get_migration_status(current_user: dict = Depends(get_current_user)):
    """Get database migration status"""
    try:
        migration_status = audit_service_enhanced.migration_manager.get_migration_status()
        return migration_status
    except Exception as e:
        logger.error(f"Error getting migration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migration/apply")
async def apply_migrations(current_user: dict = Depends(get_current_user)):
    """Apply pending database migrations"""
    try:
        success = audit_service_enhanced.migration_manager.migrate()
        
        if success:
            return {
                "message": "Migrations applied successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to apply migrations")
            
    except Exception as e:
        logger.error(f"Error applying migrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
