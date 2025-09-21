"""
Compliance Monitoring Service
Handles real-time monitoring of compliance metrics and generates alerts
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path

from app.core.logging import get_logger
from app.services.audit_service_enhanced import audit_service_enhanced, AuditEventType, AuditSeverity, AuditStatus

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class MetricType(Enum):
    """Metric types for monitoring"""
    DATA_ACCESS_COUNT = "data_access_count"
    SENSITIVE_DATA_QUERIES = "sensitive_data_queries"
    COMPLIANCE_SCORE = "compliance_score"
    RISK_INCIDENTS = "risk_incidents"
    FAILED_OPERATIONS = "failed_operations"
    USER_ACTIVITY = "user_activity"
    SYSTEM_PERFORMANCE = "system_performance"


@dataclass
class MonitoringMetric:
    """Monitoring metric data structure"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    unit: str
    threshold: Optional[float] = None
    status: str = "normal"
    metadata: Dict[str, Any] = None


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    metric_type: MetricType
    threshold_value: float
    actual_value: float
    timestamp: datetime
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


@dataclass
class RiskIncident:
    """Risk incident data structure"""
    id: str
    incident_type: str
    severity: AlertSeverity
    description: str
    affected_resources: List[str]
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    mitigation_actions: List[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class MonitoringResult:
    """Monitoring result data structure"""
    timestamp: datetime
    metrics: Dict[MetricType, MonitoringMetric]
    alerts: List[Alert]
    risk_incidents: List[RiskIncident]
    compliance_score: float
    overall_status: str
    metadata: Dict[str, Any] = None


class ComplianceMonitoringService:
    """Service for monitoring compliance metrics and generating alerts"""
    
    def __init__(self):
        self.metrics_history: List[MonitoringMetric] = []
        self.active_alerts: List[Alert] = []
        self.risk_incidents: List[RiskIncident] = []
        self.monitoring_config = self._load_monitoring_config()
        self.alert_broadcasters: List[callable] = []
        
        # Monitoring thresholds
        self.thresholds = {
            MetricType.DATA_ACCESS_COUNT: {"warning": 100, "critical": 500},
            MetricType.SENSITIVE_DATA_QUERIES: {"warning": 50, "critical": 200},
            MetricType.COMPLIANCE_SCORE: {"warning": 80, "critical": 60},
            MetricType.FAILED_OPERATIONS: {"warning": 10, "critical": 50},
            MetricType.USER_ACTIVITY: {"warning": 200, "critical": 1000}
        }
        
        # Start monitoring loop
        self._monitoring_task = None
        self._is_monitoring = False
    
    def _load_monitoring_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        config_path = Path("./data/monitoring_config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading monitoring config: {e}")
        
        # Default configuration
        return {
            "monitoring_interval": 30,  # seconds
            "alert_retention_days": 30,
            "metrics_retention_days": 7,
            "auto_resolve_alerts": True,
            "notification_channels": ["websocket", "email"],
            "enabled_metrics": [
                "data_access_count",
                "sensitive_data_queries", 
                "compliance_score",
                "failed_operations",
                "user_activity"
            ]
        }
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        if self._is_monitoring:
            logger.warning("Monitoring is already running")
            return
        
        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Compliance monitoring started")
    
    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        if not self._is_monitoring:
            return
        
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Compliance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._is_monitoring:
            try:
                # Collect metrics
                monitoring_result = await self.monitor_compliance_metrics()
                
                # Process alerts
                await self._process_alerts(monitoring_result)
                
                # Store metrics
                await self._store_metrics(monitoring_result)
                
                # Broadcast updates
                await self._broadcast_monitoring_update(monitoring_result)
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.monitoring_config["monitoring_interval"])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def monitor_compliance_metrics(self) -> MonitoringResult:
        """
        Monitor compliance metrics and generate monitoring result
        
        Returns:
            MonitoringResult: Current monitoring state
        """
        try:
            current_time = datetime.utcnow()
            metrics = {}
            
            # Collect various metrics
            metrics[MetricType.DATA_ACCESS_COUNT] = await self._get_data_access_count(current_time)
            metrics[MetricType.SENSITIVE_DATA_QUERIES] = await self._get_sensitive_data_queries(current_time)
            metrics[MetricType.COMPLIANCE_SCORE] = await self._calculate_compliance_score(current_time)
            metrics[MetricType.FAILED_OPERATIONS] = await self._get_failed_operations_count(current_time)
            metrics[MetricType.USER_ACTIVITY] = await self._get_user_activity_count(current_time)
            
            # Calculate overall compliance score
            compliance_score = await self._calculate_compliance_score(current_time)
            
            # Get risk incidents
            risk_incidents = await self._get_risk_incidents(current_time)
            
            # Generate alerts based on metrics
            alerts = await self._check_thresholds_and_generate_alerts(metrics)
            
            # Determine overall status
            overall_status = self._determine_overall_status(alerts, compliance_score)
            
            return MonitoringResult(
                timestamp=current_time,
                metrics=metrics,
                alerts=alerts,
                risk_incidents=risk_incidents,
                compliance_score=compliance_score,
                overall_status=overall_status,
                metadata={
                    "monitoring_version": "1.0",
                    "config": self.monitoring_config
                }
            )
            
        except Exception as e:
            logger.error(f"Error monitoring compliance metrics: {e}")
            raise
    
    async def _get_data_access_count(self, current_time: datetime) -> MonitoringMetric:
        """Get data access count for the last hour"""
        try:
            start_time = current_time - timedelta(hours=1)
            
            # Query audit logs for data access events
            logs = await audit_service_enhanced.get_audit_logs(
                event_type=AuditEventType.DOCUMENT_ACCESS,
                start_date=start_time,
                end_date=current_time,
                limit=10000
            )
            
            count = len(logs)
            
            return MonitoringMetric(
                metric_type=MetricType.DATA_ACCESS_COUNT,
                value=count,
                timestamp=current_time,
                unit="count",
                threshold=self.thresholds[MetricType.DATA_ACCESS_COUNT]["warning"],
                status="normal" if count < self.thresholds[MetricType.DATA_ACCESS_COUNT]["warning"] else "warning"
            )
            
        except Exception as e:
            logger.error(f"Error getting data access count: {e}")
            return MonitoringMetric(
                metric_type=MetricType.DATA_ACCESS_COUNT,
                value=0,
                timestamp=current_time,
                unit="count",
                status="error"
            )
    
    async def _get_sensitive_data_queries(self, current_time: datetime) -> MonitoringMetric:
        """Get sensitive data queries count for the last hour"""
        try:
            start_time = current_time - timedelta(hours=1)
            
            # Query audit logs for sensitive data operations
            logs = await audit_service_enhanced.get_audit_logs(
                event_type=AuditEventType.COMPLIANCE_ANALYSIS,
                start_date=start_time,
                end_date=current_time,
                limit=10000
            )
            
            count = len(logs)
            
            return MonitoringMetric(
                metric_type=MetricType.SENSITIVE_DATA_QUERIES,
                value=count,
                timestamp=current_time,
                unit="count",
                threshold=self.thresholds[MetricType.SENSITIVE_DATA_QUERIES]["warning"],
                status="normal" if count < self.thresholds[MetricType.SENSITIVE_DATA_QUERIES]["warning"] else "warning"
            )
            
        except Exception as e:
            logger.error(f"Error getting sensitive data queries: {e}")
            return MonitoringMetric(
                metric_type=MetricType.SENSITIVE_DATA_QUERIES,
                value=0,
                timestamp=current_time,
                unit="count",
                status="error"
            )
    
    async def _calculate_compliance_score(self, current_time: datetime) -> MonitoringMetric:
        """Calculate overall compliance score"""
        try:
            # Get audit statistics for the last 24 hours
            start_time = current_time - timedelta(hours=24)
            stats = await audit_service_enhanced.get_audit_statistics(
                start_date=start_time,
                end_date=current_time
            )
            
            # Calculate compliance score based on success rate and other factors
            success_rate = stats.get("success_rate", 100)
            total_events = stats.get("total_events", 0)
            
            # Base score on success rate
            base_score = success_rate
            
            # Penalize for high failure rates
            failure_events = stats.get("failure_events", 0)
            if total_events > 0:
                failure_rate = (failure_events / total_events) * 100
                base_score -= failure_rate * 0.5
            
            # Ensure score is between 0 and 100
            compliance_score = max(0, min(100, base_score))
            
            return MonitoringMetric(
                metric_type=MetricType.COMPLIANCE_SCORE,
                value=compliance_score,
                timestamp=current_time,
                unit="percentage",
                threshold=self.thresholds[MetricType.COMPLIANCE_SCORE]["warning"],
                status="normal" if compliance_score >= self.thresholds[MetricType.COMPLIANCE_SCORE]["warning"] else "warning"
            )
            
        except Exception as e:
            logger.error(f"Error calculating compliance score: {e}")
            return MonitoringMetric(
                metric_type=MetricType.COMPLIANCE_SCORE,
                value=0,
                timestamp=current_time,
                unit="percentage",
                status="error"
            )
    
    async def _get_failed_operations_count(self, current_time: datetime) -> MonitoringMetric:
        """Get failed operations count for the last hour"""
        try:
            start_time = current_time - timedelta(hours=1)
            
            # Query audit logs for failed operations
            logs = await audit_service_enhanced.get_audit_logs(
                status=AuditStatus.FAILURE,
                start_date=start_time,
                end_date=current_time,
                limit=10000
            )
            
            count = len(logs)
            
            return MonitoringMetric(
                metric_type=MetricType.FAILED_OPERATIONS,
                value=count,
                timestamp=current_time,
                unit="count",
                threshold=self.thresholds[MetricType.FAILED_OPERATIONS]["warning"],
                status="normal" if count < self.thresholds[MetricType.FAILED_OPERATIONS]["warning"] else "warning"
            )
            
        except Exception as e:
            logger.error(f"Error getting failed operations count: {e}")
            return MonitoringMetric(
                metric_type=MetricType.FAILED_OPERATIONS,
                value=0,
                timestamp=current_time,
                unit="count",
                status="error"
            )
    
    async def _get_user_activity_count(self, current_time: datetime) -> MonitoringMetric:
        """Get user activity count for the last hour"""
        try:
            start_time = current_time - timedelta(hours=1)
            
            # Query audit logs for user activity
            logs = await audit_service_enhanced.get_audit_logs(
                start_date=start_time,
                end_date=current_time,
                limit=10000
            )
            
            # Count unique users
            unique_users = set(log.user_id for log in logs)
            count = len(unique_users)
            
            return MonitoringMetric(
                metric_type=MetricType.USER_ACTIVITY,
                value=count,
                timestamp=current_time,
                unit="count",
                threshold=self.thresholds[MetricType.USER_ACTIVITY]["warning"],
                status="normal" if count < self.thresholds[MetricType.USER_ACTIVITY]["warning"] else "warning"
            )
            
        except Exception as e:
            logger.error(f"Error getting user activity count: {e}")
            return MonitoringMetric(
                metric_type=MetricType.USER_ACTIVITY,
                value=0,
                timestamp=current_time,
                unit="count",
                status="error"
            )
    
    async def _get_risk_incidents(self, current_time: datetime) -> List[RiskIncident]:
        """Get current risk incidents"""
        try:
            # Get recent high-severity audit events
            start_time = current_time - timedelta(hours=24)
            logs = await audit_service_enhanced.get_audit_logs(
                severity=AuditSeverity.HIGH,
                start_date=start_time,
                end_date=current_time,
                limit=100
            )
            
            incidents = []
            for log in logs:
                if log.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
                    incident = RiskIncident(
                        id=f"incident_{log.id}",
                        incident_type=log.event_type.value,
                        severity=AlertSeverity.ERROR if log.severity == AuditSeverity.HIGH else AlertSeverity.CRITICAL,
                        description=f"High severity event: {log.action}",
                        affected_resources=[log.resource_type],
                        detected_at=log.timestamp,
                        mitigation_actions=["Review event details", "Investigate root cause"],
                        metadata={"audit_log_id": log.id}
                    )
                    incidents.append(incident)
            
            return incidents
            
        except Exception as e:
            logger.error(f"Error getting risk incidents: {e}")
            return []
    
    async def _check_thresholds_and_generate_alerts(self, metrics: Dict[MetricType, MonitoringMetric]) -> List[Alert]:
        """Check metric thresholds and generate alerts"""
        alerts = []
        
        for metric_type, metric in metrics.items():
            if metric_type not in self.thresholds:
                continue
            
            threshold_config = self.thresholds[metric_type]
            
            # Check critical threshold
            if metric.value >= threshold_config["critical"]:
                alert = Alert(
                    id=f"alert_{metric_type.value}_{metric.timestamp.timestamp()}",
                    title=f"Critical: {metric_type.value.replace('_', ' ').title()}",
                    description=f"{metric_type.value.replace('_', ' ').title()} has reached critical level: {metric.value} {metric.unit}",
                    severity=AlertSeverity.CRITICAL,
                    status=AlertStatus.ACTIVE,
                    metric_type=metric_type,
                    threshold_value=threshold_config["critical"],
                    actual_value=metric.value,
                    timestamp=metric.timestamp,
                    metadata={"metric_unit": metric.unit}
                )
                alerts.append(alert)
            
            # Check warning threshold
            elif metric.value >= threshold_config["warning"]:
                alert = Alert(
                    id=f"alert_{metric_type.value}_{metric.timestamp.timestamp()}",
                    title=f"Warning: {metric_type.value.replace('_', ' ').title()}",
                    description=f"{metric_type.value.replace('_', ' ').title()} has reached warning level: {metric.value} {metric.unit}",
                    severity=AlertSeverity.WARNING,
                    status=AlertStatus.ACTIVE,
                    metric_type=metric_type,
                    threshold_value=threshold_config["warning"],
                    actual_value=metric.value,
                    timestamp=metric.timestamp,
                    metadata={"metric_unit": metric.unit}
                )
                alerts.append(alert)
        
        return alerts
    
    def _determine_overall_status(self, alerts: List[Alert], compliance_score: float) -> str:
        """Determine overall system status"""
        if not alerts:
            return "healthy"
        
        # Check for critical alerts
        critical_alerts = [alert for alert in alerts if alert.severity == AlertSeverity.CRITICAL]
        if critical_alerts:
            return "critical"
        
        # Check for warning alerts
        warning_alerts = [alert for alert in alerts if alert.severity == AlertSeverity.WARNING]
        if warning_alerts:
            return "warning"
        
        # Check compliance score
        if compliance_score < 60:
            return "critical"
        elif compliance_score < 80:
            return "warning"
        
        return "healthy"
    
    async def _process_alerts(self, monitoring_result: MonitoringResult):
        """Process and manage alerts"""
        try:
            # Add new alerts to active alerts
            for alert in monitoring_result.alerts:
                if not any(a.id == alert.id for a in self.active_alerts):
                    self.active_alerts.append(alert)
                    logger.warning(f"New alert generated: {alert.title}")
            
            # Auto-resolve alerts if configured
            if self.monitoring_config.get("auto_resolve_alerts", True):
                await self._auto_resolve_alerts(monitoring_result)
            
            # Clean up old alerts
            await self._cleanup_old_alerts()
            
        except Exception as e:
            logger.error(f"Error processing alerts: {e}")
    
    async def _auto_resolve_alerts(self, monitoring_result: MonitoringResult):
        """Auto-resolve alerts when conditions improve"""
        for alert in self.active_alerts[:]:  # Copy list to avoid modification during iteration
            if alert.status != AlertStatus.ACTIVE:
                continue
            
            # Check if the metric has improved
            metric = monitoring_result.metrics.get(alert.metric_type)
            if metric and metric.value < alert.threshold_value:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                logger.info(f"Alert auto-resolved: {alert.title}")
    
    async def _cleanup_old_alerts(self):
        """Clean up old resolved alerts"""
        retention_days = self.monitoring_config.get("alert_retention_days", 30)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        self.active_alerts = [
            alert for alert in self.active_alerts
            if alert.status == AlertStatus.ACTIVE or 
            (alert.resolved_at and alert.resolved_at > cutoff_date)
        ]
    
    async def _store_metrics(self, monitoring_result: MonitoringResult):
        """Store monitoring metrics"""
        try:
            # Add metrics to history
            for metric in monitoring_result.metrics.values():
                self.metrics_history.append(metric)
            
            # Clean up old metrics
            retention_days = self.monitoring_config.get("metrics_retention_days", 7)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            self.metrics_history = [
                metric for metric in self.metrics_history
                if metric.timestamp > cutoff_date
            ]
            
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
    
    async def _broadcast_monitoring_update(self, monitoring_result: MonitoringResult):
        """Broadcast monitoring updates to subscribers"""
        try:
            for broadcaster in self.alert_broadcasters:
                try:
                    if asyncio.iscoroutinefunction(broadcaster):
                        await broadcaster(monitoring_result)
                    else:
                        broadcaster(monitoring_result)
                except Exception as e:
                    logger.error(f"Error in monitoring broadcaster: {e}")
            
            # Broadcast to WebSocket manager if available
            try:
                from app.websocket.monitoring_websocket import monitoring_websocket_manager
                await monitoring_websocket_manager.broadcast_monitoring_update(monitoring_result)
            except ImportError:
                # WebSocket manager not available, skip
                pass
            except Exception as e:
                logger.error(f"Error broadcasting to monitoring WebSocket manager: {e}")
            
        except Exception as e:
            logger.error(f"Error broadcasting monitoring update: {e}")
    
    def add_alert_broadcaster(self, broadcaster: callable):
        """Add an alert broadcaster function"""
        self.alert_broadcasters.append(broadcaster)
        logger.info(f"Added monitoring alert broadcaster: {broadcaster.__name__}")
    
    def remove_alert_broadcaster(self, broadcaster: callable):
        """Remove an alert broadcaster function"""
        if broadcaster in self.alert_broadcasters:
            self.alert_broadcasters.remove(broadcaster)
            logger.info(f"Removed monitoring alert broadcaster: {broadcaster.__name__}")
    
    async def get_current_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        try:
            if not self.metrics_history:
                return {
                    "status": "no_data",
                    "message": "No monitoring data available",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Get latest metrics
            latest_metrics = {}
            for metric_type in MetricType:
                latest_metric = None
                for metric in reversed(self.metrics_history):
                    if metric.metric_type == metric_type:
                        latest_metric = metric
                        break
                if latest_metric:
                    latest_metrics[metric_type.value] = {
                        "value": latest_metric.value,
                        "unit": latest_metric.unit,
                        "status": latest_metric.status,
                        "timestamp": latest_metric.timestamp.isoformat()
                    }
            
            return {
                "status": "monitoring",
                "is_monitoring": self._is_monitoring,
                "latest_metrics": latest_metrics,
                "active_alerts": len(self.active_alerts),
                "total_metrics": len(self.metrics_history),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting current status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for monitoring service"""
        try:
            return {
                "status": "healthy",
                "service": "compliance_monitoring",
                "is_monitoring": self._is_monitoring,
                "active_alerts": len(self.active_alerts),
                "metrics_count": len(self.metrics_history),
                "broadcasters": len(self.alert_broadcasters),
                "config": self.monitoring_config,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "compliance_monitoring",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Create service instance
monitoring_service = ComplianceMonitoringService()
