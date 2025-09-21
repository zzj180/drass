#!/usr/bin/env python3
"""
Audit Log Maintenance Script
Comprehensive maintenance script for audit log system
"""

import sys
import os
import argparse
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add the services directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "main-app"))

from app.services.audit_backup_service import audit_backup_service
from app.services.audit_cleanup_service import audit_cleanup_service
from app.services.audit_monitoring_service import audit_monitoring_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audit_maintenance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AuditMaintenanceManager:
    """Main maintenance manager for audit log system"""
    
    def __init__(self):
        self.backup_service = audit_backup_service
        self.cleanup_service = audit_cleanup_service
        self.monitoring_service = audit_monitoring_service
    
    async def run_full_maintenance(self, dry_run: bool = False) -> Dict[str, Any]:
        """Run full maintenance cycle"""
        logger.info(f"Starting full audit log maintenance (dry_run={dry_run})")
        
        maintenance_report = {
            "started_at": datetime.now().isoformat(),
            "dry_run": dry_run,
            "operations": {},
            "summary": {},
            "errors": []
        }
        
        try:
            # 1. Health check
            logger.info("Running health check...")
            health_check = await self.monitoring_service.run_health_check()
            maintenance_report["operations"]["health_check"] = health_check
            
            # 2. Create backup
            logger.info("Creating backup...")
            try:
                backup_info = await self.backup_service.create_backup(
                    backup_name=f"maintenance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    compress=True
                )
                maintenance_report["operations"]["backup"] = backup_info
            except Exception as e:
                error_msg = f"Backup failed: {e}"
                logger.error(error_msg)
                maintenance_report["errors"].append(error_msg)
            
            # 3. Cleanup old logs
            logger.info("Cleaning up old logs...")
            try:
                cleanup_result = await self.cleanup_service.cleanup_old_logs(dry_run=dry_run)
                maintenance_report["operations"]["cleanup"] = cleanup_result
            except Exception as e:
                error_msg = f"Cleanup failed: {e}"
                logger.error(error_msg)
                maintenance_report["errors"].append(error_msg)
            
            # 4. Compress archived logs
            logger.info("Compressing archived logs...")
            try:
                compression_result = await self.cleanup_service.compress_archived_logs(dry_run=dry_run)
                maintenance_report["operations"]["compression"] = compression_result
            except Exception as e:
                error_msg = f"Compression failed: {e}"
                logger.error(error_msg)
                maintenance_report["errors"].append(error_msg)
            
            # 5. Optimize database
            logger.info("Optimizing database...")
            try:
                optimization_result = await self.cleanup_service.optimize_database()
                maintenance_report["operations"]["optimization"] = optimization_result
            except Exception as e:
                error_msg = f"Database optimization failed: {e}"
                logger.error(error_msg)
                maintenance_report["errors"].append(error_msg)
            
            # 6. Cleanup old backups
            logger.info("Cleaning up old backups...")
            try:
                backup_cleanup = await self.backup_service.cleanup_old_backups()
                maintenance_report["operations"]["backup_cleanup"] = backup_cleanup
            except Exception as e:
                error_msg = f"Backup cleanup failed: {e}"
                logger.error(error_msg)
                maintenance_report["errors"].append(error_msg)
            
            # Generate summary
            maintenance_report["summary"] = self._generate_summary(maintenance_report["operations"])
            maintenance_report["completed_at"] = datetime.now().isoformat()
            maintenance_report["success"] = len(maintenance_report["errors"]) == 0
            
            logger.info(f"Maintenance completed successfully: {maintenance_report['success']}")
            return maintenance_report
            
        except Exception as e:
            error_msg = f"Maintenance failed: {e}"
            logger.error(error_msg)
            maintenance_report["errors"].append(error_msg)
            maintenance_report["completed_at"] = datetime.now().isoformat()
            maintenance_report["success"] = False
            return maintenance_report
    
    def _generate_summary(self, operations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate maintenance summary"""
        summary = {
            "total_operations": len(operations),
            "successful_operations": 0,
            "failed_operations": 0,
            "space_freed_mb": 0,
            "logs_processed": 0,
            "backups_created": 0
        }
        
        for op_name, op_result in operations.items():
            if isinstance(op_result, dict) and "error" not in op_result:
                summary["successful_operations"] += 1
                
                # Extract metrics based on operation type
                if op_name == "cleanup":
                    summary["space_freed_mb"] += op_result.get("freed_space_mb", 0)
                    summary["logs_processed"] += op_result.get("archived_logs", 0) + op_result.get("deleted_logs", 0)
                elif op_name == "compression":
                    summary["space_freed_mb"] += op_result.get("space_saved_mb", 0)
                elif op_name == "backup":
                    summary["backups_created"] += 1
            else:
                summary["failed_operations"] += 1
        
        return summary
    
    async def run_backup_only(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Run backup operation only"""
        logger.info("Running backup operation...")
        
        try:
            backup_info = await self.backup_service.create_backup(
                backup_name=backup_name,
                compress=True
            )
            
            logger.info(f"Backup created successfully: {backup_info['name']}")
            return {
                "success": True,
                "operation": "backup",
                "result": backup_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Backup failed: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "operation": "backup",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_cleanup_only(self, dry_run: bool = False) -> Dict[str, Any]:
        """Run cleanup operation only"""
        logger.info(f"Running cleanup operation (dry_run={dry_run})...")
        
        try:
            cleanup_result = await self.cleanup_service.cleanup_old_logs(dry_run=dry_run)
            
            logger.info(f"Cleanup completed: {cleanup_result['archived_logs']} archived, {cleanup_result['deleted_logs']} deleted")
            return {
                "success": True,
                "operation": "cleanup",
                "result": cleanup_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Cleanup failed: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "operation": "cleanup",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_health_check_only(self) -> Dict[str, Any]:
        """Run health check only"""
        logger.info("Running health check...")
        
        try:
            health_result = await self.monitoring_service.run_health_check()
            
            logger.info(f"Health check completed: {health_result['overall_status']}")
            return {
                "success": True,
                "operation": "health_check",
                "result": health_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Health check failed: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "operation": "health_check",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
    
    async def list_backups(self) -> Dict[str, Any]:
        """List all available backups"""
        logger.info("Listing backups...")
        
        try:
            backups = await self.backup_service.list_backups()
            
            logger.info(f"Found {len(backups)} backups")
            return {
                "success": True,
                "operation": "list_backups",
                "result": backups,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Failed to list backups: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "operation": "list_backups",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        logger.info("Getting system statistics...")
        
        try:
            # Get backup statistics
            backup_stats = await self.backup_service.get_backup_statistics()
            
            # Get cleanup statistics
            cleanup_stats = await self.cleanup_service.get_cleanup_statistics()
            
            # Get monitoring dashboard data
            monitoring_data = await self.monitoring_service.get_monitoring_dashboard_data()
            
            stats = {
                "backup_statistics": backup_stats,
                "cleanup_statistics": cleanup_stats,
                "monitoring_data": monitoring_data,
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info("Statistics generated successfully")
            return {
                "success": True,
                "operation": "statistics",
                "result": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Failed to get statistics: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "operation": "statistics",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Audit Log Maintenance Script")
    parser.add_argument("--operation", "-o", 
                       choices=["full", "backup", "cleanup", "health", "list-backups", "stats"],
                       default="full",
                       help="Maintenance operation to perform")
    parser.add_argument("--dry-run", "-d", 
                       action="store_true",
                       help="Run in dry-run mode (no actual changes)")
    parser.add_argument("--backup-name", "-b",
                       help="Custom backup name for backup operation")
    parser.add_argument("--output", "-f",
                       help="Output file for results (JSON format)")
    parser.add_argument("--verbose", "-v",
                       action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create maintenance manager
    manager = AuditMaintenanceManager()
    
    # Run the requested operation
    result = None
    
    if args.operation == "full":
        result = await manager.run_full_maintenance(dry_run=args.dry_run)
    elif args.operation == "backup":
        result = await manager.run_backup_only(backup_name=args.backup_name)
    elif args.operation == "cleanup":
        result = await manager.run_cleanup_only(dry_run=args.dry_run)
    elif args.operation == "health":
        result = await manager.run_health_check_only()
    elif args.operation == "list-backups":
        result = await manager.list_backups()
    elif args.operation == "stats":
        result = await manager.get_statistics()
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Exit with appropriate code
    if result and result.get("success", False):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
