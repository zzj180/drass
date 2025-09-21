"""
Database migration manager
Handles database schema migrations for audit logs and other components
"""

import os
import importlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.migrations_dir = Path(__file__).parent / "migrations"
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Ensure migrations tracking table exists"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    checksum VARCHAR(64)
                )
            """))
            conn.commit()
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration IDs"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT id FROM schema_migrations ORDER BY applied_at"))
            return [row[0] for row in result.fetchall()]
    
    def get_available_migrations(self) -> List[Dict[str, Any]]:
        """Get list of available migration files"""
        migrations = []
        
        if not self.migrations_dir.exists():
            return migrations
        
        for migration_file in sorted(self.migrations_dir.glob("*.py")):
            if migration_file.name.startswith("__"):
                continue
            
            try:
                # Import migration module
                module_name = f"app.database.migrations.{migration_file.stem}"
                module = importlib.import_module(module_name)
                
                if hasattr(module, 'get_migration_info'):
                    migration_info = module.get_migration_info()
                    migrations.append(migration_info)
                else:
                    # Extract migration info from filename
                    migration_id = migration_file.stem.split('_')[0]
                    migrations.append({
                        "id": migration_id,
                        "name": migration_file.stem,
                        "description": f"Migration {migration_id}",
                        "created_at": datetime.fromtimestamp(migration_file.stat().st_mtime).isoformat(),
                        "dependencies": []
                    })
            except Exception as e:
                logger.error(f"Error loading migration {migration_file}: {e}")
        
        return migrations
    
    def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """Get list of pending migrations"""
        applied = set(self.get_applied_migrations())
        available = self.get_available_migrations()
        
        pending = []
        for migration in available:
            if migration["id"] not in applied:
                # Check dependencies
                dependencies_met = all(
                    dep in applied for dep in migration.get("dependencies", [])
                )
                if dependencies_met:
                    pending.append(migration)
        
        return pending
    
    def apply_migration(self, migration_id: str) -> bool:
        """Apply a specific migration"""
        try:
            # Find migration file
            migration_file = self.migrations_dir / f"{migration_id}_*.py"
            migration_files = list(self.migrations_dir.glob(f"{migration_id}_*.py"))
            
            if not migration_files:
                logger.error(f"Migration {migration_id} not found")
                return False
            
            migration_file = migration_files[0]
            
            # Import and run migration
            module_name = f"app.database.migrations.{migration_file.stem}"
            module = importlib.import_module(module_name)
            
            if not hasattr(module, 'upgrade'):
                logger.error(f"Migration {migration_id} missing upgrade function")
                return False
            
            logger.info(f"Applying migration {migration_id}")
            module.upgrade(self.engine)
            
            # Record migration as applied
            migration_info = module.get_migration_info() if hasattr(module, 'get_migration_info') else {
                "id": migration_id,
                "name": migration_file.stem,
                "description": f"Migration {migration_id}"
            }
            
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO schema_migrations (id, name, description, applied_at)
                    VALUES (:id, :name, :description, :applied_at)
                """), {
                    "id": migration_info["id"],
                    "name": migration_info["name"],
                    "description": migration_info["description"],
                    "applied_at": datetime.utcnow()
                })
                conn.commit()
            
            logger.info(f"Migration {migration_id} applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error applying migration {migration_id}: {e}")
            return False
    
    def rollback_migration(self, migration_id: str) -> bool:
        """Rollback a specific migration"""
        try:
            # Find migration file
            migration_files = list(self.migrations_dir.glob(f"{migration_id}_*.py"))
            
            if not migration_files:
                logger.error(f"Migration {migration_id} not found")
                return False
            
            migration_file = migration_files[0]
            
            # Import and run rollback
            module_name = f"app.database.migrations.{migration_file.stem}"
            module = importlib.import_module(module_name)
            
            if not hasattr(module, 'downgrade'):
                logger.error(f"Migration {migration_id} missing downgrade function")
                return False
            
            logger.info(f"Rolling back migration {migration_id}")
            module.downgrade(self.engine)
            
            # Remove migration record
            with self.engine.connect() as conn:
                conn.execute(text("DELETE FROM schema_migrations WHERE id = :id"), {"id": migration_id})
                conn.commit()
            
            logger.info(f"Migration {migration_id} rolled back successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back migration {migration_id}: {e}")
            return False
    
    def migrate(self) -> bool:
        """Apply all pending migrations"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return True
        
        logger.info(f"Found {len(pending)} pending migrations")
        
        for migration in pending:
            if not self.apply_migration(migration["id"]):
                logger.error(f"Failed to apply migration {migration['id']}")
                return False
        
        logger.info("All migrations applied successfully")
        return True
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status information"""
        applied = self.get_applied_migrations()
        available = self.get_available_migrations()
        pending = self.get_pending_migrations()
        
        return {
            "applied_count": len(applied),
            "available_count": len(available),
            "pending_count": len(pending),
            "applied_migrations": applied,
            "pending_migrations": [m["id"] for m in pending],
            "last_migration": applied[-1] if applied else None,
            "database_url": self.database_url
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for migration system"""
        try:
            status = self.get_migration_status()
            return {
                "status": "healthy",
                "service": "migration_manager",
                "migration_status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "migration_manager",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


def create_migration_manager(database_url: Optional[str] = None) -> MigrationManager:
    """Create migration manager instance"""
    if not database_url:
        # Default to SQLite for development
        database_url = "sqlite:///./data/audit_logs.db"
    
    return MigrationManager(database_url)
