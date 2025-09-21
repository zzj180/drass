"""
Audit Log Maintenance API endpoints
Provides backup, cleanup, monitoring, and maintenance functionality
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from app.services.audit_backup_service import audit_backup_service
from app.services.audit_cleanup_service import audit_cleanup_service
from app.services.audit_monitoring_service import audit_monitoring_service
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-maintenance", tags=["audit-maintenance"])


@router.get("/health")
async def health_check():
    """Health check for audit maintenance services"""
    try:
        health_status = await audit_monitoring_service.run_health_check()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup")
async def create_backup(
    backup_name: Optional[str] = None,
    include_archives: bool = True,
    compress: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Create a backup of audit logs"""
    try:
        backup_info = await audit_backup_service.create_backup(
            backup_name=backup_name,
            include_archives=include_archives,
            compress=compress
        )
        return {
            "success": True,
            "message": "Backup created successfully",
            "backup_info": backup_info
        }
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups")
async def list_backups(current_user: dict = Depends(get_current_user)):
    """List all available backups"""
    try:
        backups = await audit_backup_service.list_backups()
        return {
            "success": True,
            "backups": backups,
            "total_count": len(backups)
        }
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/{backup_name}/restore")
async def restore_backup(
    backup_name: str,
    restore_archives: bool = True,
    clear_existing: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Restore audit logs from backup"""
    try:
        restore_info = await audit_backup_service.restore_backup(
            backup_name=backup_name,
            restore_archives=restore_archives,
            clear_existing=clear_existing
        )
        return {
            "success": True,
            "message": "Backup restored successfully",
            "restore_info": restore_info
        }
    except Exception as e:
        logger.error(f"Backup restore failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/backup/{backup_name}")
async def delete_backup(
    backup_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a backup file"""
    try:
        delete_info = await audit_backup_service.delete_backup(backup_name)
        return {
            "success": True,
            "message": "Backup deleted successfully",
            "delete_info": delete_info
        }
    except Exception as e:
        logger.error(f"Backup deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/{backup_name}/compress")
async def compress_backup(
    backup_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Compress an uncompressed backup"""
    try:
        compress_info = await audit_backup_service.compress_backup(backup_name)
        return {
            "success": True,
            "message": "Backup compressed successfully",
            "compress_info": compress_info
        }
    except Exception as e:
        logger.error(f"Backup compression failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_old_logs(
    dry_run: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Clean up old audit logs"""
    try:
        cleanup_result = await audit_cleanup_service.cleanup_old_logs(dry_run=dry_run)
        return {
            "success": True,
            "message": "Cleanup completed successfully",
            "cleanup_result": cleanup_result
        }
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compress-archives")
async def compress_archived_logs(
    dry_run: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Compress archived logs"""
    try:
        compression_result = await audit_cleanup_service.compress_archived_logs(dry_run=dry_run)
        return {
            "success": True,
            "message": "Compression completed successfully",
            "compression_result": compression_result
        }
    except Exception as e:
        logger.error(f"Compression failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-database")
async def optimize_database(current_user: dict = Depends(get_current_user)):
    """Optimize database performance"""
    try:
        optimization_result = await audit_cleanup_service.optimize_database()
        return {
            "success": True,
            "message": "Database optimization completed successfully",
            "optimization_result": optimization_result
        }
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(current_user: dict = Depends(get_current_user)):
    """Get system statistics"""
    try:
        # Get backup statistics
        backup_stats = await audit_backup_service.get_backup_statistics()
        
        # Get cleanup statistics
        cleanup_stats = await audit_cleanup_service.get_cleanup_statistics()
        
        # Get monitoring dashboard data
        monitoring_data = await audit_monitoring_service.get_monitoring_dashboard_data()
        
        return {
            "success": True,
            "statistics": {
                "backup": backup_stats,
                "cleanup": cleanup_stats,
                "monitoring": monitoring_data,
                "generated_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard(current_user: dict = Depends(get_current_user)):
    """Get monitoring dashboard data"""
    try:
        dashboard_data = await audit_monitoring_service.get_monitoring_dashboard_data()
        return {
            "success": True,
            "dashboard_data": dashboard_data
        }
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance/full")
async def run_full_maintenance(
    dry_run: bool = False,
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    """Run full maintenance cycle"""
    try:
        # This would typically run in background for long operations
        # For now, we'll run it synchronously
        
        # Create backup
        backup_info = await audit_backup_service.create_backup(
            backup_name=f"maintenance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            compress=True
        )
        
        # Run cleanup
        cleanup_result = await audit_cleanup_service.cleanup_old_logs(dry_run=dry_run)
        
        # Optimize database
        optimization_result = await audit_cleanup_service.optimize_database()
        
        # Cleanup old backups
        backup_cleanup = await audit_backup_service.cleanup_old_backups()
        
        return {
            "success": True,
            "message": "Full maintenance completed successfully",
            "results": {
                "backup": backup_info,
                "cleanup": cleanup_result,
                "optimization": optimization_result,
                "backup_cleanup": backup_cleanup
            }
        }
    except Exception as e:
        logger.error(f"Full maintenance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cleanup/statistics")
async def get_cleanup_statistics(current_user: dict = Depends(get_current_user)):
    """Get cleanup statistics and recommendations"""
    try:
        cleanup_stats = await audit_cleanup_service.get_cleanup_statistics()
        return {
            "success": True,
            "cleanup_statistics": cleanup_stats
        }
    except Exception as e:
        logger.error(f"Failed to get cleanup statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backup/statistics")
async def get_backup_statistics(current_user: dict = Depends(get_current_user)):
    """Get backup statistics"""
    try:
        backup_stats = await audit_backup_service.get_backup_statistics()
        return {
            "success": True,
            "backup_statistics": backup_stats
        }
    except Exception as e:
        logger.error(f"Failed to get backup statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/old-backups")
async def cleanup_old_backups(current_user: dict = Depends(get_current_user)):
    """Clean up old backup files"""
    try:
        cleanup_result = await audit_backup_service.cleanup_old_backups()
        return {
            "success": True,
            "message": "Old backups cleaned up successfully",
            "cleanup_result": cleanup_result
        }
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
