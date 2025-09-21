"""
Database migration: Create audit logs tables
Migration ID: 001
Description: Create audit_logs and audit_logs_archive tables with indexes
"""

from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)


def upgrade(engine):
    """Upgrade database schema"""
    logger.info("Starting migration 001: Create audit logs tables")
    
    with engine.connect() as conn:
        # Create audit_logs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id VARCHAR(36) PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                user_id VARCHAR(100) NOT NULL,
                user_name VARCHAR(255) NOT NULL,
                user_role VARCHAR(100),
                action VARCHAR(255) NOT NULL,
                resource_type VARCHAR(100) NOT NULL DEFAULT 'system',
                resource_id VARCHAR(100),
                details JSONB,
                severity VARCHAR(20) NOT NULL,
                status VARCHAR(20) NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                session_id VARCHAR(100),
                request_id VARCHAR(100),
                outcome VARCHAR(255) NOT NULL DEFAULT 'completed',
                error_message TEXT,
                success BOOLEAN DEFAULT TRUE,
                metadata_json JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create audit_logs_archive table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs_archive (
                id VARCHAR(36) PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                user_id VARCHAR(100) NOT NULL,
                user_name VARCHAR(255) NOT NULL,
                user_role VARCHAR(100),
                action VARCHAR(255) NOT NULL,
                resource_type VARCHAR(100) NOT NULL,
                resource_id VARCHAR(100),
                details JSONB,
                severity VARCHAR(20) NOT NULL,
                status VARCHAR(20) NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                session_id VARCHAR(100),
                request_id VARCHAR(100),
                outcome VARCHAR(255) NOT NULL,
                error_message TEXT,
                success BOOLEAN DEFAULT TRUE,
                metadata_json JSONB,
                archived_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                original_created_at TIMESTAMP NOT NULL,
                original_updated_at TIMESTAMP NOT NULL
            )
        """))
        
        # Create indexes for audit_logs
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs (event_type)",
            "CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_logs (severity)",
            "CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_logs (status)",
            "CREATE INDEX IF NOT EXISTS idx_audit_success ON audit_logs (success)",
            "CREATE INDEX IF NOT EXISTS idx_audit_request_id ON audit_logs (request_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_time_type ON audit_logs (timestamp, event_type)",
            "CREATE INDEX IF NOT EXISTS idx_audit_user_time ON audit_logs (user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_success_time ON audit_logs (success, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_severity_time ON audit_logs (severity, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_status_time ON audit_logs (status, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_resource_time ON audit_logs (resource_type, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_request_time ON audit_logs (request_id, timestamp)"
        ]
        
        for index_sql in indexes:
            conn.execute(text(index_sql))
        
        # Create indexes for audit_logs_archive
        archive_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_audit_archive_timestamp ON audit_logs_archive (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_archive_event_type ON audit_logs_archive (event_type)",
            "CREATE INDEX IF NOT EXISTS idx_audit_archive_user_id ON audit_logs_archive (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_archive_severity ON audit_logs_archive (severity)",
            "CREATE INDEX IF NOT EXISTS idx_audit_archive_status ON audit_logs_archive (status)",
            "CREATE INDEX IF NOT EXISTS idx_audit_archive_success ON audit_logs_archive (success)",
            "CREATE INDEX IF NOT EXISTS idx_audit_archive_request_id ON audit_logs_archive (request_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_archive_time_type ON audit_logs_archive (timestamp, event_type)",
            "CREATE INDEX IF NOT EXISTS idx_audit_archive_user_time ON audit_logs_archive (user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_archive_archived_time ON audit_logs_archive (archived_at, timestamp)"
        ]
        
        for index_sql in archive_indexes:
            conn.execute(text(index_sql))
        
        conn.commit()
        logger.info("Migration 001 completed successfully")


def downgrade(engine):
    """Downgrade database schema"""
    logger.info("Starting rollback of migration 001: Drop audit logs tables")
    
    with engine.connect() as conn:
        # Drop tables
        conn.execute(text("DROP TABLE IF EXISTS audit_logs_archive"))
        conn.execute(text("DROP TABLE IF EXISTS audit_logs"))
        conn.commit()
        logger.info("Migration 001 rollback completed")


def get_migration_info():
    """Get migration information"""
    return {
        "id": "001",
        "name": "create_audit_logs",
        "description": "Create audit_logs and audit_logs_archive tables with indexes",
        "created_at": datetime.utcnow().isoformat(),
        "dependencies": []
    }
