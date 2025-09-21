"""
Audit Log models for database and API
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, Text, Boolean, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AuditEventType(str, Enum):
    """Audit event types"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_ACCESS = "document_access"
    COMPLIANCE_ANALYSIS = "compliance_analysis"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    API_ACCESS = "api_access"
    ERROR_EVENT = "error_event"
    SECURITY_EVENT = "security_event"
    OTHER = "other"


class AuditSeverity(str, Enum):
    """Audit event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(str, Enum):
    """Audit event status"""
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    PENDING = "pending"


class AuditLogBase(BaseModel):
    """Base audit log model"""
    event_type: AuditEventType
    user_id: str
    user_name: str
    user_role: Optional[str] = None
    action: str
    resource_type: str = "system"
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    severity: AuditSeverity = AuditSeverity.MEDIUM
    status: AuditStatus = AuditStatus.SUCCESS
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    outcome: str = "completed"
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditLogCreate(AuditLogBase):
    """Audit log creation model"""
    pass


class AuditLogUpdate(BaseModel):
    """Audit log update model"""
    status: Optional[AuditStatus] = None
    outcome: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AuditLog(AuditLogBase):
    """Audit log database model"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    success: bool = True
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLogResponse(AuditLog):
    """Audit log API response model"""
    pass


class AuditLogSearchRequest(BaseModel):
    """Audit log search request model"""
    user_id: Optional[str] = None
    event_type: Optional[AuditEventType] = None
    severity: Optional[AuditSeverity] = None
    status: Optional[AuditStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search_query: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class AuditLogSearchResult(BaseModel):
    """Audit log search result model"""
    logs: List[AuditLogResponse]
    total_count: int
    has_more: bool
    limit: int
    offset: int


class AuditLogStatistics(BaseModel):
    """Audit log statistics model"""
    total_events: int
    success_events: int
    failure_events: int
    warning_events: int
    success_rate: float
    event_type_counts: Dict[str, int]
    severity_counts: Dict[str, int]
    user_counts: Dict[str, int]
    date_range: Dict[str, Optional[str]]


# SQLAlchemy Database Model
class AuditLogDB(Base):
    """SQLAlchemy audit log database model"""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    user_name = Column(String, nullable=False)
    user_role = Column(String)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False, default="system")
    resource_id = Column(String)
    details = Column(JSONB)
    severity = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    ip_address = Column(String)
    user_agent = Column(Text)
    session_id = Column(String)
    request_id = Column(String, index=True)
    outcome = Column(String, nullable=False, default="completed")
    error_message = Column(Text)
    success = Column(Boolean, default=True, index=True)
    metadata_json = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite indexes for query optimization
    __table_args__ = (
        Index('idx_audit_time_type', 'timestamp', 'event_type'),
        Index('idx_audit_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_success_time', 'success', 'timestamp'),
        Index('idx_audit_severity_time', 'severity', 'timestamp'),
        Index('idx_audit_status_time', 'status', 'timestamp'),
        Index('idx_audit_resource_time', 'resource_type', 'timestamp'),
        Index('idx_audit_request_time', 'request_id', 'timestamp'),
    )


class AuditLogArchive(Base):
    """SQLAlchemy audit log archive model for old logs"""
    __tablename__ = "audit_logs_archive"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    user_name = Column(String, nullable=False)
    user_role = Column(String)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String)
    details = Column(JSONB)
    severity = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    ip_address = Column(String)
    user_agent = Column(Text)
    session_id = Column(String)
    request_id = Column(String, index=True)
    outcome = Column(String, nullable=False)
    error_message = Column(Text)
    success = Column(Boolean, default=True, index=True)
    metadata_json = Column(JSONB)
    
    # Archive specific fields
    archived_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    original_created_at = Column(DateTime, nullable=False)
    original_updated_at = Column(DateTime, nullable=False)
    
    # Composite indexes for archive queries
    __table_args__ = (
        Index('idx_audit_archive_time_type', 'timestamp', 'event_type'),
        Index('idx_audit_archive_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_archive_archived_time', 'archived_at', 'timestamp'),
    )
