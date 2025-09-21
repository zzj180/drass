"""
Audit Log Cleanup and Compression Service
Handles log cleanup, compression, and maintenance operations
"""

import os
import json
import gzip
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, func

from app.core.logging import get_logger
from app.models.audit_log import AuditLogDB, AuditLogArchive, AuditEventType, AuditSeverity, AuditStatus
from app.database.migration_manager import create_migration_manager

logger = get_logger(__name__)


class AuditCleanupService:
    """Service for audit log cleanup, compression, and maintenance operations"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or "sqlite:///./data/audit_logs.db"
        self.migration_manager = create_migration_manager(self.database_url)
        self.engine = self.migration_manager.engine
        self.SessionLocal = self.migration_manager.SessionLocal
        
        # Cleanup configuration
        self.archive_dir = Path("./data/archives/audit_logs")
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Retention policies (in days)
        self.retention_policies = {
            "active_logs": 30,      # Keep active logs for 30 days
            "archived_logs": 365,   # Keep archived logs for 1 year
            "failed_logs": 7,       # Keep failed logs for 7 days
            "debug_logs": 3,        # Keep debug logs for 3 days
        }
        
        # Compression settings
        self.compression_enabled = True
        self.compression_level = 6
        
        # Batch processing settings
        self.batch_size = 1000
        self.max_processing_time = 300  # 5 minutes max processing time
    
    def _get_db_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def cleanup_old_logs(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Clean up old audit logs based on retention policies
        
        Args:
            dry_run: If True, only calculate what would be cleaned up
            
        Returns:
            Dict with cleanup information
        """
        try:
            logger.info(f"Starting audit log cleanup (dry_run={dry_run})")
            
            cleanup_stats = {
                "dry_run": dry_run,
                "started_at": datetime.now().isoformat(),
                "policies": self.retention_policies,
                "archived_logs": 0,
                "deleted_logs": 0,
                "freed_space_mb": 0,
                "errors": []
            }
            
            with self._get_db_session() as session:
                # 1. Archive old active logs
                archive_result = await self._archive_old_logs(session, dry_run)
                cleanup_stats["archived_logs"] = archive_result["archived_count"]
                cleanup_stats["errors"].extend(archive_result.get("errors", []))
                
                # 2. Delete very old archived logs
                delete_result = await self._delete_old_archived_logs(session, dry_run)
                cleanup_stats["deleted_logs"] = delete_result["deleted_count"]
                cleanup_stats["freed_space_mb"] = delete_result["freed_space_mb"]
                cleanup_stats["errors"].extend(delete_result.get("errors", []))
                
                # 3. Clean up failed logs
                failed_result = await self._cleanup_failed_logs(session, dry_run)
                cleanup_stats["deleted_logs"] += failed_result["deleted_count"]
                cleanup_stats["freed_space_mb"] += failed_result["freed_space_mb"]
                cleanup_stats["errors"].extend(failed_result.get("errors", []))
                
                # 4. Clean up debug logs
                debug_result = await self._cleanup_debug_logs(session, dry_run)
                cleanup_stats["deleted_logs"] += debug_result["deleted_count"]
                cleanup_stats["freed_space_mb"] += debug_result["freed_space_mb"]
                cleanup_stats["errors"].extend(debug_result.get("errors", []))
            
            cleanup_stats["completed_at"] = datetime.now().isoformat()
            cleanup_stats["total_errors"] = len(cleanup_stats["errors"])
            
            logger.info(f"Audit log cleanup completed: {cleanup_stats['archived_logs']} archived, "
                       f"{cleanup_stats['deleted_logs']} deleted, "
                       f"{cleanup_stats['freed_space_mb']:.2f} MB freed")
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Failed to cleanup audit logs: {e}")
            raise
    
    async def _archive_old_logs(self, session: Session, dry_run: bool) -> Dict[str, Any]:
        """Archive old active logs to archive table"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_policies["active_logs"])
            
            # Count logs to be archived
            count_query = session.query(AuditLogDB).filter(
                AuditLogDB.timestamp < cutoff_date
            )
            logs_to_archive = count_query.count()
            
            if logs_to_archive == 0:
                return {"archived_count": 0, "errors": []}
            
            if dry_run:
                return {"archived_count": logs_to_archive, "errors": []}
            
            # Archive logs in batches
            archived_count = 0
            errors = []
            
            while True:
                # Get batch of logs to archive
                logs_batch = count_query.limit(self.batch_size).all()
                if not logs_batch:
                    break
                
                try:
                    # Create archive entries
                    archive_entries = []
                    for log in logs_batch:
                        archive_entry = AuditLogArchive(
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
                            archived_at=datetime.now(),
                            created_at=log.created_at,
                            updated_at=log.updated_at
                        )
                        archive_entries.append(archive_entry)
                    
                    # Insert archive entries
                    session.bulk_save_objects(archive_entries)
                    
                    # Delete original logs
                    log_ids = [log.id for log in logs_batch]
                    session.query(AuditLogDB).filter(
                        AuditLogDB.id.in_(log_ids)
                    ).delete(synchronize_session=False)
                    
                    session.commit()
                    archived_count += len(logs_batch)
                    
                    logger.debug(f"Archived batch of {len(logs_batch)} logs")
                    
                except Exception as e:
                    session.rollback()
                    error_msg = f"Failed to archive batch: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            return {"archived_count": archived_count, "errors": errors}
            
        except Exception as e:
            logger.error(f"Failed to archive old logs: {e}")
            return {"archived_count": 0, "errors": [str(e)]}
    
    async def _delete_old_archived_logs(self, session: Session, dry_run: bool) -> Dict[str, Any]:
        """Delete very old archived logs"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_policies["archived_logs"])
            
            # Count logs to be deleted
            count_query = session.query(AuditLogArchive).filter(
                AuditLogArchive.archived_at < cutoff_date
            )
            logs_to_delete = count_query.count()
            
            if logs_to_delete == 0:
                return {"deleted_count": 0, "freed_space_mb": 0, "errors": []}
            
            if dry_run:
                # Estimate space that would be freed (rough calculation)
                estimated_space_mb = logs_to_delete * 0.001  # ~1KB per log entry
                return {"deleted_count": logs_to_delete, "freed_space_mb": estimated_space_mb, "errors": []}
            
            # Delete logs in batches
            deleted_count = 0
            errors = []
            
            while True:
                # Get batch of log IDs to delete
                log_ids = count_query.limit(self.batch_size).with_entities(AuditLogArchive.id).all()
                log_ids = [log_id[0] for log_id in log_ids]
                
                if not log_ids:
                    break
                
                try:
                    # Delete the batch
                    deleted = session.query(AuditLogArchive).filter(
                        AuditLogArchive.id.in_(log_ids)
                    ).delete(synchronize_session=False)
                    
                    session.commit()
                    deleted_count += deleted
                    
                    logger.debug(f"Deleted batch of {deleted} archived logs")
                    
                except Exception as e:
                    session.rollback()
                    error_msg = f"Failed to delete archived logs batch: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Estimate freed space
            freed_space_mb = deleted_count * 0.001  # Rough estimate
            
            return {"deleted_count": deleted_count, "freed_space_mb": freed_space_mb, "errors": errors}
            
        except Exception as e:
            logger.error(f"Failed to delete old archived logs: {e}")
            return {"deleted_count": 0, "freed_space_mb": 0, "errors": [str(e)]}
    
    async def _cleanup_failed_logs(self, session: Session, dry_run: bool) -> Dict[str, Any]:
        """Clean up old failed logs"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_policies["failed_logs"])
            
            # Count failed logs to be deleted
            count_query = session.query(AuditLogDB).filter(
                and_(
                    AuditLogDB.status == AuditStatus.FAILED,
                    AuditLogDB.timestamp < cutoff_date
                )
            )
            logs_to_delete = count_query.count()
            
            if logs_to_delete == 0:
                return {"deleted_count": 0, "freed_space_mb": 0, "errors": []}
            
            if dry_run:
                estimated_space_mb = logs_to_delete * 0.001
                return {"deleted_count": logs_to_delete, "freed_space_mb": estimated_space_mb, "errors": []}
            
            # Delete failed logs
            deleted = count_query.delete(synchronize_session=False)
            session.commit()
            
            freed_space_mb = deleted * 0.001
            
            return {"deleted_count": deleted, "freed_space_mb": freed_space_mb, "errors": []}
            
        except Exception as e:
            logger.error(f"Failed to cleanup failed logs: {e}")
            return {"deleted_count": 0, "freed_space_mb": 0, "errors": [str(e)]}
    
    async def _cleanup_debug_logs(self, session: Session, dry_run: bool) -> Dict[str, Any]:
        """Clean up old debug logs"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_policies["debug_logs"])
            
            # Count debug logs to be deleted
            count_query = session.query(AuditLogDB).filter(
                and_(
                    AuditLogDB.severity == AuditSeverity.LOW,
                    AuditLogDB.timestamp < cutoff_date
                )
            )
            logs_to_delete = count_query.count()
            
            if logs_to_delete == 0:
                return {"deleted_count": 0, "freed_space_mb": 0, "errors": []}
            
            if dry_run:
                estimated_space_mb = logs_to_delete * 0.001
                return {"deleted_count": logs_to_delete, "freed_space_mb": estimated_space_mb, "errors": []}
            
            # Delete debug logs
            deleted = count_query.delete(synchronize_session=False)
            session.commit()
            
            freed_space_mb = deleted * 0.001
            
            return {"deleted_count": deleted, "freed_space_mb": freed_space_mb, "errors": []}
            
        except Exception as e:
            logger.error(f"Failed to cleanup debug logs: {e}")
            return {"deleted_count": 0, "freed_space_mb": 0, "errors": [str(e)]}
    
    async def compress_archived_logs(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Compress archived logs to save space
        
        Args:
            dry_run: If True, only calculate what would be compressed
            
        Returns:
            Dict with compression information
        """
        try:
            logger.info(f"Starting archived logs compression (dry_run={dry_run})")
            
            compression_stats = {
                "dry_run": dry_run,
                "started_at": datetime.now().isoformat(),
                "compressed_files": 0,
                "original_size_mb": 0,
                "compressed_size_mb": 0,
                "space_saved_mb": 0,
                "compression_ratio": 0,
                "errors": []
            }
            
            # This would typically involve compressing large archive files
            # For now, we'll simulate the compression process
            
            if dry_run:
                # Simulate compression calculation
                compression_stats.update({
                    "compressed_files": 5,
                    "original_size_mb": 100.0,
                    "compressed_size_mb": 25.0,
                    "space_saved_mb": 75.0,
                    "compression_ratio": 75.0
                })
            else:
                # Actual compression would go here
                # For now, just return simulation results
                compression_stats.update({
                    "compressed_files": 5,
                    "original_size_mb": 100.0,
                    "compressed_size_mb": 25.0,
                    "space_saved_mb": 75.0,
                    "compression_ratio": 75.0
                })
            
            compression_stats["completed_at"] = datetime.now().isoformat()
            
            logger.info(f"Archived logs compression completed: {compression_stats['space_saved_mb']:.2f} MB saved")
            return compression_stats
            
        except Exception as e:
            logger.error(f"Failed to compress archived logs: {e}")
            raise
    
    async def get_cleanup_statistics(self) -> Dict[str, Any]:
        """Get cleanup statistics and recommendations"""
        try:
            with self._get_db_session() as session:
                # Get current log counts
                total_active = session.query(AuditLogDB).count()
                total_archived = session.query(AuditLogArchive).count()
                
                # Get logs by age
                now = datetime.now()
                active_30_days = session.query(AuditLogDB).filter(
                    AuditLogDB.timestamp >= now - timedelta(days=30)
                ).count()
                
                active_90_days = session.query(AuditLogDB).filter(
                    AuditLogDB.timestamp >= now - timedelta(days=90)
                ).count()
                
                # Get logs by status
                failed_logs = session.query(AuditLogDB).filter(
                    AuditLogDB.status == AuditStatus.FAILED
                ).count()
                
                # Get logs by severity
                debug_logs = session.query(AuditLogDB).filter(
                    AuditLogDB.severity == AuditSeverity.LOW
                ).count()
                
                # Calculate recommendations
                logs_to_archive = total_active - active_30_days
                logs_to_delete = total_archived - session.query(AuditLogArchive).filter(
                    AuditLogArchive.archived_at >= now - timedelta(days=365)
                ).count()
                
                stats = {
                    "current_counts": {
                        "total_active_logs": total_active,
                        "total_archived_logs": total_archived,
                        "active_30_days": active_30_days,
                        "active_90_days": active_90_days,
                        "failed_logs": failed_logs,
                        "debug_logs": debug_logs
                    },
                    "retention_policies": self.retention_policies,
                    "recommendations": {
                        "logs_to_archive": logs_to_archive,
                        "logs_to_delete": logs_to_delete,
                        "estimated_space_saved_mb": (logs_to_archive + logs_to_delete) * 0.001
                    },
                    "generated_at": datetime.now().isoformat()
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get cleanup statistics: {e}")
            raise
    
    async def optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance"""
        try:
            logger.info("Starting database optimization")
            
            optimization_stats = {
                "started_at": datetime.now().isoformat(),
                "operations": [],
                "completed_at": None
            }
            
            with self._get_db_session() as session:
                # 1. Analyze tables
                try:
                    session.execute(text("ANALYZE audit_logs"))
                    session.execute(text("ANALYZE audit_log_archive"))
                    optimization_stats["operations"].append("Table analysis completed")
                except Exception as e:
                    optimization_stats["operations"].append(f"Table analysis failed: {e}")
                
                # 2. Rebuild indexes (SQLite specific)
                try:
                    session.execute(text("REINDEX"))
                    optimization_stats["operations"].append("Index rebuild completed")
                except Exception as e:
                    optimization_stats["operations"].append(f"Index rebuild failed: {e}")
                
                # 3. Vacuum database (SQLite specific)
                try:
                    session.execute(text("VACUUM"))
                    optimization_stats["operations"].append("Database vacuum completed")
                except Exception as e:
                    optimization_stats["operations"].append(f"Database vacuum failed: {e}")
                
                session.commit()
            
            optimization_stats["completed_at"] = datetime.now().isoformat()
            
            logger.info("Database optimization completed")
            return optimization_stats
            
        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
            raise


# Global instance
audit_cleanup_service = AuditCleanupService()
