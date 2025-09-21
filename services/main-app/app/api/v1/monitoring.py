"""
Monitoring API endpoints
Provides real-time compliance monitoring and alerting functionality
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.services.monitoring_service import (
    monitoring_service, MonitoringResult, Alert, RiskIncident, 
    AlertSeverity, AlertStatus, MetricType
)
from app.websocket.monitoring_websocket import monitoring_websocket_manager
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
async def health_check():
    """Health check for monitoring service"""
    try:
        health_status = await monitoring_service.health_check()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_monitoring(current_user: dict = Depends(get_current_user)):
    """Start compliance monitoring"""
    try:
        await monitoring_service.start_monitoring()
        return {
            "message": "Compliance monitoring started successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_monitoring(current_user: dict = Depends(get_current_user)):
    """Stop compliance monitoring"""
    try:
        await monitoring_service.stop_monitoring()
        return {
            "message": "Compliance monitoring stopped successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_monitoring_status(current_user: dict = Depends(get_current_user)):
    """Get current monitoring status"""
    try:
        status = await monitoring_service.get_current_status()
        return status
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_current_metrics(current_user: dict = Depends(get_current_user)):
    """Get current monitoring metrics"""
    try:
        monitoring_result = await monitoring_service.monitor_compliance_metrics()
        
        # Convert metrics to response format
        metrics_response = {}
        for metric_type, metric in monitoring_result.metrics.items():
            metrics_response[metric_type.value] = {
                "value": metric.value,
                "unit": metric.unit,
                "status": metric.status,
                "threshold": metric.threshold,
                "timestamp": metric.timestamp.isoformat()
            }
        
        return {
            "timestamp": monitoring_result.timestamp.isoformat(),
            "compliance_score": monitoring_result.compliance_score,
            "overall_status": monitoring_result.overall_status,
            "metrics": metrics_response,
            "metadata": monitoring_result.metadata
        }
        
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_active_alerts(
    severity: Optional[AlertSeverity] = Query(None, description="Filter by alert severity"),
    status: Optional[AlertStatus] = Query(None, description="Filter by alert status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get active alerts
    
    Args:
        severity: Filter by alert severity
        status: Filter by alert status
        limit: Maximum number of alerts
        
    Returns:
        List of active alerts
    """
    try:
        alerts = monitoring_service.active_alerts.copy()
        
        # Apply filters
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        if status:
            alerts = [alert for alert in alerts if alert.status == status]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        alerts = alerts[:limit]
        
        # Convert to response format
        alerts_response = []
        for alert in alerts:
            alerts_response.append({
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
        
        return {
            "alerts": alerts_response,
            "total_count": len(alerts_response),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Acknowledge an alert"""
    try:
        # Find the alert
        alert = None
        for a in monitoring_service.active_alerts:
            if a.id == alert_id:
                alert = a
                break
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Update alert status
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = current_user.get("user_id", "unknown")
        alert.acknowledged_at = datetime.utcnow()
        
        return {
            "message": f"Alert {alert_id} acknowledged successfully",
            "alert_id": alert_id,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Resolve an alert"""
    try:
        # Find the alert
        alert = None
        for a in monitoring_service.active_alerts:
            if a.id == alert_id:
                alert = a
                break
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Update alert status
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        
        return {
            "message": f"Alert {alert_id} resolved successfully",
            "alert_id": alert_id,
            "resolved_at": alert.resolved_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-incidents")
async def get_risk_incidents(
    severity: Optional[AlertSeverity] = Query(None, description="Filter by incident severity"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of incidents"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get risk incidents
    
    Args:
        severity: Filter by incident severity
        limit: Maximum number of incidents
        
    Returns:
        List of risk incidents
    """
    try:
        # Get current monitoring result to get risk incidents
        monitoring_result = await monitoring_service.monitor_compliance_metrics()
        incidents = monitoring_result.risk_incidents.copy()
        
        # Apply filters
        if severity:
            incidents = [incident for incident in incidents if incident.severity == severity]
        
        # Sort by detected_at (newest first)
        incidents.sort(key=lambda x: x.detected_at, reverse=True)
        
        # Apply limit
        incidents = incidents[:limit]
        
        # Convert to response format
        incidents_response = []
        for incident in incidents:
            incidents_response.append({
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
        
        return {
            "incidents": incidents_response,
            "total_count": len(incidents_response),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting risk incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_monitoring_statistics(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to include in statistics"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get monitoring statistics for the specified time period
    
    Args:
        hours: Number of hours to include in statistics
        
    Returns:
        Monitoring statistics
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get metrics from the specified time period
        relevant_metrics = [
            metric for metric in monitoring_service.metrics_history
            if start_time <= metric.timestamp <= end_time
        ]
        
        # Calculate statistics
        stats = {
            "time_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "metrics_summary": {},
            "alerts_summary": {
                "total_alerts": len(monitoring_service.active_alerts),
                "active_alerts": len([a for a in monitoring_service.active_alerts if a.status == AlertStatus.ACTIVE]),
                "acknowledged_alerts": len([a for a in monitoring_service.active_alerts if a.status == AlertStatus.ACKNOWLEDGED]),
                "resolved_alerts": len([a for a in monitoring_service.active_alerts if a.status == AlertStatus.RESOLVED])
            },
            "severity_breakdown": {
                "critical": len([a for a in monitoring_service.active_alerts if a.severity == AlertSeverity.CRITICAL]),
                "error": len([a for a in monitoring_service.active_alerts if a.severity == AlertSeverity.ERROR]),
                "warning": len([a for a in monitoring_service.active_alerts if a.severity == AlertSeverity.WARNING]),
                "info": len([a for a in monitoring_service.active_alerts if a.severity == AlertSeverity.INFO])
            }
        }
        
        # Calculate metrics summary
        for metric_type in MetricType:
            type_metrics = [m for m in relevant_metrics if m.metric_type == metric_type]
            if type_metrics:
                values = [m.value for m in type_metrics]
                stats["metrics_summary"][metric_type.value] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "latest": values[-1] if values else 0
                }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting monitoring statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{user_id}")
async def monitoring_websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time monitoring updates"""
    await monitoring_websocket_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            await monitoring_websocket_manager.handle_client_message(websocket, data, user_id)
            
    except WebSocketDisconnect:
        monitoring_websocket_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        monitoring_websocket_manager.disconnect(websocket, user_id)


@router.get("/websocket/stats")
async def get_websocket_stats(current_user: dict = Depends(get_current_user)):
    """Get WebSocket connection statistics"""
    try:
        stats = monitoring_websocket_manager.get_connection_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
