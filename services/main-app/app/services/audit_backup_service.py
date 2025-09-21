"""
Audit Log Backup and Recovery Service
Handles backup, recovery, compression, and monitoring of audit logs
"""

import os
import json
import gzip
import shutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import asyncio
import sqlite3
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.logging import get_logger
from app.models.audit_log import AuditLogDB, AuditLogArchive
from app.database.migration_manager import create_migration_manager

logger = get_logger(__name__)


class AuditBackupService:
    """Service for audit log backup, recovery, and maintenance operations"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or "sqlite:///./data/audit_logs.db"
        self.migration_manager = create_migration_manager(self.database_url)
        self.engine = self.migration_manager.engine
        self.SessionLocal = self.migration_manager.SessionLocal
        
        # Backup configuration
        self.backup_dir = Path("./data/backups/audit_logs")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Compression settings
        self.compression_enabled = True
        self.compression_level = 6  # 1-9, 6 is good balance
        
        # Retention settings
        self.retention_days = 90  # Keep backups for 90 days
        self.max_backup_size_mb = 100  # Maximum backup file size
        
    def _get_db_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def create_backup(
        self, 
        backup_name: Optional[str] = None,
        include_archives: bool = True,
        compress: bool = True
    ) -> Dict[str, Any]:
        """
        Create a backup of audit logs
        
        Args:
            backup_name: Custom backup name (default: timestamp-based)
            include_archives: Whether to include archived logs
            compress: Whether to compress the backup
            
        Returns:
            Dict with backup information
        """
        try:
            if not backup_name:
                backup_name = f"audit_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = self.backup_dir / f"{backup_name}.json"
            if compress:
                backup_path = backup_path.with_suffix('.json.gz')
            
            logger.info(f"Creating audit log backup: {backup_name}")
            
            # Get all audit logs
            with self._get_db_session() as session:
                # Query active logs
                active_logs = session.query(AuditLogDB).all()
                
                # Query archived logs if requested
                archived_logs = []
                if include_archives:
                    archived_logs = session.query(AuditLogArchive).all()
                
                # Convert to dictionaries
                backup_data = {
                    "backup_info": {
                        "name": backup_name,
                        "created_at": datetime.now().isoformat(),
                        "database_url": self.database_url,
                        "total_active_logs": len(active_logs),
                        "total_archived_logs": len(archived_logs),
                        "compressed": compress
                    },
                    "active_logs": [
                        {
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
                        }
                        for log in active_logs
                    ],
                    "archived_logs": [
                        {
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
                            "archived_at": log.archived_at.isoformat(),
                            "created_at": log.created_at.isoformat(),
                            "updated_at": log.updated_at.isoformat()
                        }
                        for log in archived_logs
                    ]
                }
            
            # Write backup file
            if compress:
                with gzip.open(backup_path, 'wt', compresslevel=self.compression_level) as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            else:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            # Get file size
            file_size = backup_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            backup_info = {
                "name": backup_name,
                "path": str(backup_path),
                "size_bytes": file_size,
                "size_mb": round(file_size_mb, 2),
                "compressed": compress,
                "created_at": datetime.now().isoformat(),
                "total_active_logs": len(active_logs),
                "total_archived_logs": len(archived_logs)
            }
            
            logger.info(f"Backup created successfully: {backup_name} ({file_size_mb:.2f} MB)")
            return backup_info
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    async def restore_backup(
        self, 
        backup_name: str,
        restore_archives: bool = True,
        clear_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Restore audit logs from backup
        
        Args:
            backup_name: Name of the backup to restore
            restore_archives: Whether to restore archived logs
            clear_existing: Whether to clear existing logs before restore
            
        Returns:
            Dict with restore information
        """
        try:
            # Find backup file
            backup_path = None
            for ext in ['.json.gz', '.json']:
                potential_path = self.backup_dir / f"{backup_name}{ext}"
                if potential_path.exists():
                    backup_path = potential_path
                    break
            
            if not backup_path:
                raise FileNotFoundError(f"Backup not found: {backup_name}")
            
            logger.info(f"Restoring audit log backup: {backup_name}")
            
            # Read backup file
            if backup_path.suffix == '.gz':
                with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                    backup_data = json.load(f)
            else:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
            
            with self._get_db_session() as session:
                # Clear existing data if requested
                if clear_existing:
                    logger.info("Clearing existing audit logs...")
                    session.query(AuditLogDB).delete()
                    if restore_archives:
                        session.query(AuditLogArchive).delete()
                    session.commit()
                
                # Restore active logs
                restored_active = 0
                for log_data in backup_data.get("active_logs", []):
                    try:
                        audit_log = AuditLogDB(
                            id=log_data["id"],
                            timestamp=datetime.fromisoformat(log_data["timestamp"]),
                            event_type=log_data["event_type"],
                            user_id=log_data["user_id"],
                            user_name=log_data["user_name"],
                            user_role=log_data.get("user_role"),
                            action=log_data["action"],
                            resource_type=log_data["resource_type"],
                            resource_id=log_data.get("resource_id"),
                            details=log_data["details"],
                            severity=log_data["severity"],
                            status=log_data["status"],
                            ip_address=log_data.get("ip_address"),
                            user_agent=log_data.get("user_agent"),
                            session_id=log_data.get("session_id"),
                            request_id=log_data.get("request_id"),
                            outcome=log_data["outcome"],
                            error_message=log_data.get("error_message"),
                            success=log_data["success"],
                            metadata=log_data["metadata"],
                            created_at=datetime.fromisoformat(log_data["created_at"]),
                            updated_at=datetime.fromisoformat(log_data["updated_at"])
                        )
                        session.add(audit_log)
                        restored_active += 1
                    except Exception as e:
                        logger.warning(f"Failed to restore log {log_data.get('id', 'unknown')}: {e}")
                
                # Restore archived logs if requested
                restored_archived = 0
                if restore_archives:
                    for log_data in backup_data.get("archived_logs", []):
                        try:
                            archived_log = AuditLogArchive(
                                id=log_data["id"],
                                timestamp=datetime.fromisoformat(log_data["timestamp"]),
                                event_type=log_data["event_type"],
                                user_id=log_data["user_id"],
                                user_name=log_data["user_name"],
                                user_role=log_data.get("user_role"),
                                action=log_data["action"],
                                resource_type=log_data["resource_type"],
                                resource_id=log_data.get("resource_id"),
                                details=log_data["details"],
                                severity=log_data["severity"],
                                status=log_data["status"],
                                ip_address=log_data.get("ip_address"),
                                user_agent=log_data.get("user_agent"),
                                session_id=log_data.get("session_id"),
                                request_id=log_data.get("request_id"),
                                outcome=log_data["outcome"],
                                error_message=log_data.get("error_message"),
                                success=log_data["success"],
                                metadata=log_data["metadata"],
                                archived_at=datetime.fromisoformat(log_data["archived_at"]),
                                created_at=datetime.fromisoformat(log_data["created_at"]),
                                updated_at=datetime.fromisoformat(log_data["updated_at"])
                            )
                            session.add(archived_log)
                            restored_archived += 1
                        except Exception as e:
                            logger.warning(f"Failed to restore archived log {log_data.get('id', 'unknown')}: {e}")
                
                session.commit()
            
            restore_info = {
                "backup_name": backup_name,
                "restored_at": datetime.now().isoformat(),
                "restored_active_logs": restored_active,
                "restored_archived_logs": restored_archived,
                "clear_existing": clear_existing
            }
            
            logger.info(f"Backup restored successfully: {restored_active} active, {restored_archived} archived logs")
            return restore_info
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        try:
            backups = []
            for backup_file in self.backup_dir.glob("*.json*"):
                try:
                    stat = backup_file.stat()
                    file_size_mb = stat.st_size / (1024 * 1024)
                    
                    backup_info = {
                        "name": backup_file.stem.replace('.json', ''),
                        "path": str(backup_file),
                        "size_bytes": stat.st_size,
                        "size_mb": round(file_size_mb, 2),
                        "compressed": backup_file.suffix == '.gz',
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                    
                    # Try to read backup info if it's a valid backup
                    try:
                        if backup_file.suffix == '.gz':
                            with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                                backup_data = json.load(f)
                        else:
                            with open(backup_file, 'r', encoding='utf-8') as f:
                                backup_data = json.load(f)
                        
                        if "backup_info" in backup_data:
                            backup_info.update({
                                "total_active_logs": backup_data["backup_info"].get("total_active_logs", 0),
                                "total_archived_logs": backup_data["backup_info"].get("total_archived_logs", 0)
                            })
                    except:
                        pass  # Ignore if can't read backup info
                    
                    backups.append(backup_info)
                except Exception as e:
                    logger.warning(f"Failed to process backup file {backup_file}: {e}")
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            raise
    
    async def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """Delete a backup file"""
        try:
            # Find backup file
            backup_path = None
            for ext in ['.json.gz', '.json']:
                potential_path = self.backup_dir / f"{backup_name}{ext}"
                if potential_path.exists():
                    backup_path = potential_path
                    break
            
            if not backup_path:
                raise FileNotFoundError(f"Backup not found: {backup_name}")
            
            # Get file info before deletion
            file_size = backup_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            # Delete the file
            backup_path.unlink()
            
            delete_info = {
                "backup_name": backup_name,
                "deleted_at": datetime.now().isoformat(),
                "size_bytes": file_size,
                "size_mb": round(file_size_mb, 2)
            }
            
            logger.info(f"Backup deleted: {backup_name} ({file_size_mb:.2f} MB)")
            return delete_info
            
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            raise
    
    async def cleanup_old_backups(self) -> Dict[str, Any]:
        """Clean up old backups based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0
            freed_space_mb = 0
            
            for backup_file in self.backup_dir.glob("*.json*"):
                try:
                    file_modified = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_modified < cutoff_date:
                        file_size = backup_file.stat().st_size
                        file_size_mb = file_size / (1024 * 1024)
                        
                        backup_file.unlink()
                        deleted_count += 1
                        freed_space_mb += file_size_mb
                        
                        logger.info(f"Deleted old backup: {backup_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete old backup {backup_file}: {e}")
            
            cleanup_info = {
                "deleted_count": deleted_count,
                "freed_space_mb": round(freed_space_mb, 2),
                "retention_days": self.retention_days,
                "cleanup_date": datetime.now().isoformat()
            }
            
            logger.info(f"Backup cleanup completed: {deleted_count} files, {freed_space_mb:.2f} MB freed")
            return cleanup_info
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            raise
    
    async def compress_backup(self, backup_name: str) -> Dict[str, Any]:
        """Compress an uncompressed backup"""
        try:
            backup_path = self.backup_dir / f"{backup_name}.json"
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup not found: {backup_name}")
            
            compressed_path = backup_path.with_suffix('.json.gz')
            if compressed_path.exists():
                raise FileExistsError(f"Compressed backup already exists: {backup_name}")
            
            # Compress the file
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb', compresslevel=self.compression_level) as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Get size information
            original_size = backup_path.stat().st_size
            compressed_size = compressed_path.stat().st_size
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            # Delete original file
            backup_path.unlink()
            
            compress_info = {
                "backup_name": backup_name,
                "original_size_bytes": original_size,
                "compressed_size_bytes": compressed_size,
                "compression_ratio": round(compression_ratio, 2),
                "compressed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Backup compressed: {backup_name} ({compression_ratio:.1f}% reduction)")
            return compress_info
            
        except Exception as e:
            logger.error(f"Failed to compress backup: {e}")
            raise
    
    async def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics and storage information"""
        try:
            backups = await self.list_backups()
            
            total_backups = len(backups)
            total_size_bytes = sum(backup["size_bytes"] for backup in backups)
            total_size_mb = total_size_bytes / (1024 * 1024)
            
            compressed_backups = sum(1 for backup in backups if backup["compressed"])
            uncompressed_backups = total_backups - compressed_backups
            
            # Calculate average compression ratio for compressed backups
            avg_compression_ratio = 0
            if compressed_backups > 0:
                # This is a rough estimate since we don't store original sizes
                avg_compression_ratio = 60  # Typical gzip compression ratio
            
            # Get oldest and newest backup dates
            oldest_backup = min(backups, key=lambda x: x["created_at"]) if backups else None
            newest_backup = max(backups, key=lambda x: x["created_at"]) if backups else None
            
            stats = {
                "total_backups": total_backups,
                "total_size_bytes": total_size_bytes,
                "total_size_mb": round(total_size_mb, 2),
                "compressed_backups": compressed_backups,
                "uncompressed_backups": uncompressed_backups,
                "average_compression_ratio": avg_compression_ratio,
                "retention_days": self.retention_days,
                "backup_directory": str(self.backup_dir),
                "oldest_backup": oldest_backup["created_at"] if oldest_backup else None,
                "newest_backup": newest_backup["created_at"] if newest_backup else None,
                "generated_at": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get backup statistics: {e}")
            raise


# Global instance
audit_backup_service = AuditBackupService()
