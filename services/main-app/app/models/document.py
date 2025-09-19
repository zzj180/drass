"""
Document models for database and API
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4


class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentType(str, Enum):
    """Supported document types"""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    TXT = "txt"
    MD = "md"
    CSV = "csv"
    IMAGE = "image"
    OTHER = "other"


class StorageLocation(str, Enum):
    """Storage location types"""
    LOCAL = "local"
    S3 = "s3"
    MINIO = "minio"


class DocumentBase(BaseModel):
    """Base document model"""
    filename: str
    file_type: DocumentType
    file_size: int
    mime_type: str
    folder_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentCreate(DocumentBase):
    """Document creation model"""
    auto_process: bool = True
    chunk_size: Optional[int] = 500
    chunk_overlap: Optional[int] = 50


class DocumentUpdate(BaseModel):
    """Document update model"""
    filename: Optional[str] = None
    folder_id: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Document(DocumentBase):
    """Document database model"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    status: DocumentStatus = DocumentStatus.PENDING
    storage_location: StorageLocation = StorageLocation.LOCAL
    storage_path: str
    checksum: Optional[str] = None
    
    # Processing results
    extracted_text: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    language: Optional[str] = None
    
    # Vector storage
    vector_ids: List[str] = Field(default_factory=list)
    chunk_count: Optional[int] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0


class DocumentResponse(Document):
    """Document API response model"""
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
    )


class DocumentContent(BaseModel):
    """Document content response"""
    document_id: UUID
    content: str
    content_type: str = "text/plain"
    chunks: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentFolder(BaseModel):
    """Document folder model"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    user_id: str
    document_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentFolderCreate(BaseModel):
    """Folder creation model"""
    name: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None


class DocumentProcessingRequest(BaseModel):
    """Document processing request"""
    strategy: str = "auto"  # auto, ocr, text_only, with_images
    chunk_size: int = 500
    chunk_overlap: int = 50
    extract_metadata: bool = True
    extract_tables: bool = True
    extract_images: bool = False
    language: str = "auto"  # auto, en, zh, etc.


class DocumentProcessingResult(BaseModel):
    """Document processing result"""
    document_id: UUID
    status: DocumentStatus
    extracted_text: Optional[str] = None
    chunks: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    language: Optional[str] = None
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    images: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time: float = 0.0
    error_message: Optional[str] = None


class DocumentSearchRequest(BaseModel):
    """Document search request"""
    query: str
    folder_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    file_types: Optional[List[DocumentType]] = None
    status: Optional[DocumentStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class DocumentSearchResult(BaseModel):
    """Document search result"""
    documents: List[DocumentResponse]
    total: int
    limit: int
    offset: int
    query: str


class DocumentBatchUploadResult(BaseModel):
    """Batch upload result"""
    uploaded: List[DocumentResponse]
    failed: List[Dict[str, Any]]
    total: int
    successful: int