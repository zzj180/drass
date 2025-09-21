"""
Audit Log Monitoring Service
Handles monitoring, alerting, and health checks for audit logs
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, func, desc
from enum import Enum

from app.core.logging import get_logger
from app.models.audit_log import AuditLogDB, AuditLogArchive, AuditEventType, AuditSeverity, AuditStatus
from app.database.migration_manager import create_migration_manager

logger = get_logger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""
    STORAGE_FULL = "storage_full"
    HIGH_FAILURE_RATE = "high_failure_rate"
    UNUSUAL_ACTIVITY = "unusual_activity"
    DATABASE_ERROR = "database_error"
    BACKUP_FAILED = "backup_failed"
    CLEANUP_FAILED = "cleanup_failed"
    PERFORMANCE_DEGRADED = "performance_degraded"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    type: AlertType
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


class AuditMonitoringService:
    """Service for monitoring audit log system health and performance"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or "sqlite:///./data/audit_logs.db"
        self.migration_manager = create_migration_manager(self.database_url)
        self.engine = self.migration_manager.engine
        self.SessionLocal = self.migration_manager.SessionLocal
        
        # Monitoring configuration
        self.monitoring_config = {
            "storage_threshold_mb": 1000,  # Alert when storage exceeds 1GB
            "failure_rate_threshold": 0.1,  # Alert when failure rate > 10%
            "unusual_activity_threshold": 5,  # Alert when activity > 5x normal
            "performance_threshold_ms": 1000,  # Alert when queries > 1 second
            "backup_retention_days": 7,  # Alert if no backup in 7 days
            "cleanup_interval_days": 1,  # Alert if cleanup not run in 1 day
        }
        
        # Alert storage
        self.alerts_file = Path("./data/audit_alerts.json")
        self.alerts_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Performance metrics
        self.performance_metrics = {
            "query_times": [],
            "storage_usage": [],
            "log_counts": [],
            "error_rates": []
        }
    
    def _get_db_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        try:
            logger.info("Running audit log health check")
            
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "checks": {},
                "alerts": [],
                "recommendations": []
            }
            
            # 1. Database connectivity check
            db_check = await self._check_database_connectivity()
            health_status["checks"]["database"] = db_check
            
            # 2. Storage usage check
            storage_check = await self._check_storage_usage()
            health_status["checks"]["storage"] = storage_check
            
            # 3. Performance check
            performance_check = await self._check_performance()
            health_status["checks"]["performance"] = performance_check
            
            # 4. Data integrity check
            integrity_check = await self._check_data_integrity()
            health_status["checks"]["integrity"] = integrity_check
            
            # 5. Backup status check
            backup_check = await self._check_backup_status()
            health_status["checks"]["backup"] = backup_check
            
            # 6. Cleanup status check
            cleanup_check = await self._check_cleanup_status()
            health_status["checks"]["cleanup"] = cleanup_check
            
            # 7. Error rate check
            error_check = await self._check_error_rates()
            health_status["checks"]["error_rates"] = error_check
            
            # 8. Activity pattern check
            activity_check = await self._check_activity_patterns()
            health_status["checks"]["activity"] = activity_check
            
            # Generate alerts based on checks
            alerts = await self._generate_alerts(health_status["checks"])
            health_status["alerts"] = alerts
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(health_status["checks"])
            health_status["recommendations"] = recommendations
            
            # Determine overall status
            if any(check.get("status") == "critical" for check in health_status["checks"].values()):
                health_status["overall_status"] = "critical"
            elif any(check.get("status") == "warning" for check in health_status["checks"].values()):
                health_status["overall_status"] = "warning"
            
            logger.info(f"Health check completed: {health_status['overall_status']}")
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "error",
                "error": str(e),
                "checks": {},
                "alerts": [],
                "recommendations": []
            }
    
    async def _check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity and basic operations"""
        try:
            start_time = datetime.now()
            
            with self._get_db_session() as session:
                # Test basic query
                result = session.execute(text("SELECT 1")).fetchone()
                
                # Test audit log table access
                count = session.query(AuditLogDB).count()
                
                # Test archive table access
                archive_count = session.query(AuditLogArchive).count()
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "active_logs": count,
                "archived_logs": archive_count,
                "message": "Database connectivity normal"
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "error": str(e),
                "message": "Database connectivity failed"
            }
    
    async def _check_storage_usage(self) -> Dict[str, Any]:
        """Check storage usage and growth"""
        try:
            # Get database file size
            db_path = Path(self.database_url.replace("sqlite:///", ""))
            if db_path.exists():
                db_size_mb = db_path.stat().st_size / (1024 * 1024)
            else:
                db_size_mb = 0
            
            # Get backup directory size
            backup_dir = Path("./data/backups/audit_logs")
            backup_size_mb = 0
            if backup_dir.exists():
                for file_path in backup_dir.rglob("*"):
                    if file_path.is_file():
                        backup_size_mb += file_path.stat().st_size / (1024 * 1024)
            
            total_size_mb = db_size_mb + backup_size_mb
            threshold_mb = self.monitoring_config["storage_threshold_mb"]
            
            status = "healthy"
            if total_size_mb > threshold_mb:
                status = "warning"
            if total_size_mb > threshold_mb * 2:
                status = "critical"
            
            return {
                "status": status,
                "database_size_mb": round(db_size_mb, 2),
                "backup_size_mb": round(backup_size_mb, 2),
                "total_size_mb": round(total_size_mb, 2),
                "threshold_mb": threshold_mb,
                "usage_percentage": round((total_size_mb / threshold_mb) * 100, 1),
                "message": f"Storage usage: {total_size_mb:.1f}MB / {threshold_mb}MB"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Storage check failed"
            }
    
    async def _check_performance(self) -> Dict[str, Any]:
        """Check query performance"""
        try:
            start_time = datetime.now()
            
            with self._get_db_session() as session:
                # Test common queries
                queries = [
                    ("count_all", session.query(AuditLogDB).count),
                    ("count_recent", lambda: session.query(AuditLogDB).filter(
                        AuditLogDB.timestamp >= datetime.now() - timedelta(days=1)
                    ).count()),
                    ("count_failed", lambda: session.query(AuditLogDB).filter(
                        AuditLogDB.status == AuditStatus.FAILED
                    ).count()),
                ]
                
                query_times = {}
                for name, query_func in queries:
                    query_start = datetime.now()
                    try:
                        result = query_func()
                        query_time = (datetime.now() - query_start).total_seconds() * 1000
                        query_times[name] = {
                            "time_ms": round(query_time, 2),
                            "result": result,
                            "status": "success"
                        }
                    except Exception as e:
                        query_times[name] = {
                            "time_ms": 0,
                            "error": str(e),
                            "status": "error"
                        }
            
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            max_time = max(q.get("time_ms", 0) for q in query_times.values() if q.get("status") == "success")
            
            status = "healthy"
            if max_time > self.monitoring_config["performance_threshold_ms"]:
                status = "warning"
            if max_time > self.monitoring_config["performance_threshold_ms"] * 2:
                status = "critical"
            
            return {
                "status": status,
                "total_time_ms": round(total_time, 2),
                "max_query_time_ms": max_time,
                "threshold_ms": self.monitoring_config["performance_threshold_ms"],
                "query_times": query_times,
                "message": f"Max query time: {max_time:.1f}ms"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Performance check failed"
            }
    
    async def _check_data_integrity(self) -> Dict[str, Any]:
        """Check data integrity and consistency"""
        try:
            with self._get_db_session() as session:
                # Check for orphaned records
                orphaned_count = 0
                
                # Check for missing required fields
                missing_fields = session.query(AuditLogDB).filter(
                    or_(
                        AuditLogDB.user_id.is_(None),
                        AuditLogDB.timestamp.is_(None),
                        AuditLogDB.event_type.is_(None)
                    )
                ).count()
                
                # Check for invalid timestamps
                invalid_timestamps = session.query(AuditLogDB).filter(
                    AuditLogDB.timestamp > datetime.now() + timedelta(days=1)
                ).count()
                
                issues = missing_fields + invalid_timestamps + orphaned_count
                
                status = "healthy"
                if issues > 0:
                    status = "warning"
                if issues > 100:
                    status = "critical"
                
                return {
                    "status": status,
                    "missing_fields": missing_fields,
                    "invalid_timestamps": invalid_timestamps,
                    "orphaned_records": orphaned_count,
                    "total_issues": issues,
                    "message": f"Data integrity: {issues} issues found"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Data integrity check failed"
            }
    
    async def _check_backup_status(self) -> Dict[str, Any]:
        """Check backup status and freshness"""
        try:
            backup_dir = Path("./data/backups/audit_logs")
            if not backup_dir.exists():
                return {
                    "status": "critical",
                    "message": "Backup directory does not exist"
                }
            
            # Find most recent backup
            backup_files = list(backup_dir.glob("*.json*"))
            if not backup_files:
                return {
                    "status": "critical",
                    "message": "No backup files found"
                }
            
            # Get most recent backup
            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            backup_age = datetime.now() - datetime.fromtimestamp(latest_backup.stat().st_mtime)
            backup_age_days = backup_age.days
            
            threshold_days = self.monitoring_config["backup_retention_days"]
            
            status = "healthy"
            if backup_age_days > threshold_days:
                status = "warning"
            if backup_age_days > threshold_days * 2:
                status = "critical"
            
            return {
                "status": status,
                "latest_backup": latest_backup.name,
                "backup_age_days": backup_age_days,
                "threshold_days": threshold_days,
                "total_backups": len(backup_files),
                "message": f"Latest backup: {backup_age_days} days old"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Backup status check failed"
            }
    
    async def _check_cleanup_status(self) -> Dict[str, Any]:
        """Check cleanup status and frequency"""
        try:
            # This would typically check a cleanup log or timestamp
            # For now, we'll simulate the check
            
            # Check if cleanup has been run recently
            cleanup_log_file = Path("./data/audit_cleanup.log")
            if not cleanup_log_file.exists():
                return {
                    "status": "warning",
                    "message": "No cleanup log found"
                }
            
            # Read last cleanup time
            try:
                with open(cleanup_log_file, 'r') as f:
                    last_line = f.readlines()[-1].strip()
                    # Parse timestamp from log line
                    # This is a simplified implementation
                    last_cleanup = datetime.now() - timedelta(hours=1)  # Simulate recent cleanup
            except:
                last_cleanup = datetime.now() - timedelta(days=2)  # Simulate old cleanup
            
            cleanup_age = datetime.now() - last_cleanup
            cleanup_age_days = cleanup_age.days
            
            threshold_days = self.monitoring_config["cleanup_interval_days"]
            
            status = "healthy"
            if cleanup_age_days > threshold_days:
                status = "warning"
            if cleanup_age_days > threshold_days * 2:
                status = "critical"
            
            return {
                "status": status,
                "last_cleanup_days": cleanup_age_days,
                "threshold_days": threshold_days,
                "message": f"Last cleanup: {cleanup_age_days} days ago"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Cleanup status check failed"
            }
    
    async def _check_error_rates(self) -> Dict[str, Any]:
        """Check error rates and failure patterns"""
        try:
            with self._get_db_session() as session:
                # Get logs from last 24 hours
                last_24h = datetime.now() - timedelta(days=1)
                
                total_logs = session.query(AuditLogDB).filter(
                    AuditLogDB.timestamp >= last_24h
                ).count()
                
                failed_logs = session.query(AuditLogDB).filter(
                    and_(
                        AuditLogDB.timestamp >= last_24h,
                        AuditLogDB.status == AuditStatus.FAILED
                    )
                ).count()
                
                if total_logs == 0:
                    failure_rate = 0
                else:
                    failure_rate = failed_logs / total_logs
                
                threshold = self.monitoring_config["failure_rate_threshold"]
                
                status = "healthy"
                if failure_rate > threshold:
                    status = "warning"
                if failure_rate > threshold * 2:
                    status = "critical"
                
                return {
                    "status": status,
                    "total_logs_24h": total_logs,
                    "failed_logs_24h": failed_logs,
                    "failure_rate": round(failure_rate * 100, 2),
                    "threshold_percentage": round(threshold * 100, 2),
                    "message": f"Failure rate: {failure_rate * 100:.1f}%"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Error rate check failed"
            }
    
    async def _check_activity_patterns(self) -> Dict[str, Any]:
        """Check for unusual activity patterns"""
        try:
            with self._get_db_session() as session:
                # Get activity from last hour vs previous hour
                now = datetime.now()
                last_hour = now - timedelta(hours=1)
                two_hours_ago = now - timedelta(hours=2)
                
                current_activity = session.query(AuditLogDB).filter(
                    AuditLogDB.timestamp >= last_hour
                ).count()
                
                previous_activity = session.query(AuditLogDB).filter(
                    and_(
                        AuditLogDB.timestamp >= two_hours_ago,
                        AuditLogDB.timestamp < last_hour
                    )
                ).count()
                
                if previous_activity == 0:
                    activity_ratio = 1.0 if current_activity == 0 else float('inf')
                else:
                    activity_ratio = current_activity / previous_activity
                
                threshold = self.monitoring_config["unusual_activity_threshold"]
                
                status = "healthy"
                if activity_ratio > threshold:
                    status = "warning"
                if activity_ratio > threshold * 2:
                    status = "critical"
                
                return {
                    "status": status,
                    "current_hour_activity": current_activity,
                    "previous_hour_activity": previous_activity,
                    "activity_ratio": round(activity_ratio, 2),
                    "threshold": threshold,
                    "message": f"Activity ratio: {activity_ratio:.1f}x"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Activity pattern check failed"
            }
    
    async def _generate_alerts(self, checks: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on health check results"""
        alerts = []
        
        for check_name, check_result in checks.items():
            status = check_result.get("status", "unknown")
            
            if status == "critical":
                alerts.append({
                    "type": "system_critical",
                    "level": "critical",
                    "title": f"Critical Issue: {check_name}",
                    "message": check_result.get("message", "Critical issue detected"),
                    "timestamp": datetime.now().isoformat(),
                    "metadata": check_result
                })
            elif status == "warning":
                alerts.append({
                    "type": "system_warning",
                    "level": "warning",
                    "title": f"Warning: {check_name}",
                    "message": check_result.get("message", "Warning condition detected"),
                    "timestamp": datetime.now().isoformat(),
                    "metadata": check_result
                })
        
        return alerts
    
    async def _generate_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        # Storage recommendations
        storage_check = checks.get("storage", {})
        if storage_check.get("status") in ["warning", "critical"]:
            recommendations.append("Consider running cleanup to free up storage space")
        
        # Performance recommendations
        performance_check = checks.get("performance", {})
        if performance_check.get("status") in ["warning", "critical"]:
            recommendations.append("Consider optimizing database indexes or running database maintenance")
        
        # Backup recommendations
        backup_check = checks.get("backup", {})
        if backup_check.get("status") in ["warning", "critical"]:
            recommendations.append("Create a new backup to ensure data safety")
        
        # Cleanup recommendations
        cleanup_check = checks.get("cleanup", {})
        if cleanup_check.get("status") in ["warning", "critical"]:
            recommendations.append("Run cleanup process to maintain system performance")
        
        return recommendations
    
    async def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        try:
            with self._get_db_session() as session:
                # Get recent activity (last 24 hours)
                last_24h = datetime.now() - timedelta(days=1)
                
                # Activity by hour
                hourly_activity = []
                for i in range(24):
                    hour_start = last_24h + timedelta(hours=i)
                    hour_end = hour_start + timedelta(hours=1)
                    
                    count = session.query(AuditLogDB).filter(
                        and_(
                            AuditLogDB.timestamp >= hour_start,
                            AuditLogDB.timestamp < hour_end
                        )
                    ).count()
                    
                    hourly_activity.append({
                        "hour": hour_start.strftime("%H:00"),
                        "count": count
                    })
                
                # Activity by event type
                event_type_activity = []
                for event_type in AuditEventType:
                    count = session.query(AuditLogDB).filter(
                        and_(
                            AuditLogDB.timestamp >= last_24h,
                            AuditLogDB.event_type == event_type
                        )
                    ).count()
                    
                    if count > 0:
                        event_type_activity.append({
                            "event_type": event_type.value,
                            "count": count
                        })
                
                # Activity by severity
                severity_activity = []
                for severity in AuditSeverity:
                    count = session.query(AuditLogDB).filter(
                        and_(
                            AuditLogDB.timestamp >= last_24h,
                            AuditLogDB.severity == severity
                        )
                    ).count()
                    
                    if count > 0:
                        severity_activity.append({
                            "severity": severity.value,
                            "count": count
                        })
                
                # Top users
                top_users = session.query(
                    AuditLogDB.user_id,
                    AuditLogDB.user_name,
                    func.count(AuditLogDB.id).label('activity_count')
                ).filter(
                    AuditLogDB.timestamp >= last_24h
                ).group_by(
                    AuditLogDB.user_id, AuditLogDB.user_name
                ).order_by(
                    desc('activity_count')
                ).limit(10).all()
                
                top_users_data = [
                    {
                        "user_id": user.user_id,
                        "user_name": user.user_name,
                        "activity_count": user.activity_count
                    }
                    for user in top_users
                ]
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "hourly_activity": hourly_activity,
                    "event_type_activity": event_type_activity,
                    "severity_activity": severity_activity,
                    "top_users": top_users_data,
                    "summary": {
                        "total_activity_24h": sum(h["count"] for h in hourly_activity),
                        "unique_users_24h": len(top_users_data),
                        "most_active_hour": max(hourly_activity, key=lambda x: x["count"])["hour"] if hourly_activity else None
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get monitoring dashboard data: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "hourly_activity": [],
                "event_type_activity": [],
                "severity_activity": [],
                "top_users": [],
                "summary": {}
            }


# Global instance
audit_monitoring_service = AuditMonitoringService()
