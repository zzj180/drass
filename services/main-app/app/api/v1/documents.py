from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from app.core.security import get_current_active_user
from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Pydantic models
class Document(BaseModel):
    id: str = Field(..., description="Document ID")
    name: str = Field(..., description="Document name")
    type: str = Field(..., description="Document type")
    size: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Processing status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Document tags")


class DocumentFolder(BaseModel):
    id: str = Field(..., description="Folder ID")
    name: str = Field(..., description="Folder name")
    parent_id: Optional[str] = Field(default=None, description="Parent folder ID")
    document_count: int = Field(default=0, description="Number of documents")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CreateFolder(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Folder name")
    parent_id: Optional[str] = Field(default=None, description="Parent folder ID")


class ProcessingResult(BaseModel):
    document_id: str = Field(..., description="Document ID")
    status: str = Field(..., description="Processing status")
    extracted_text: Optional[str] = Field(default=None, description="Extracted text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    processing_time: float = Field(..., description="Processing time in seconds")


@router.get("/", response_model=List[Document])
async def get_documents(
    folder_id: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get documents with optional filtering
    """
    try:
        from app.services.document_service import document_service
        
        documents = await document_service.get_user_documents(
            user_id=current_user["id"],
            folder_id=folder_id,
            status=status,
            tags=tags,
            limit=limit,
            offset=offset
        )
        
        return [
            Document(
                id=doc["id"],
                name=doc["name"],
                type=doc["type"],
                size=doc["size"],
                status=doc["status"],
                metadata=doc.get("metadata", {}),
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
                tags=doc.get("tags", [])
            )
            for doc in documents
        ]
        
    except Exception as e:
        logger.error(f"Get documents error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.post("/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    auto_process: bool = Form(True),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Upload a document
    """
    try:
        # Validate file type
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file_extension}' is not allowed"
            )
        
        # Validate file size
        content = await file.read()
        file_size = len(content)
        
        if file_size > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
        
        from app.services.document_service import document_service
        
        document = await document_service.upload_document(
            user_id=current_user["id"],
            file=file,
            content=content,
            folder_id=folder_id,
            tags=tag_list,
            auto_process=auto_process
        )
        
        return Document(
            id=document["id"],
            name=document["name"],
            type=document["type"],
            size=document["size"],
            status=document["status"],
            metadata=document.get("metadata", {}),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            tags=document.get("tags", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload document error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.post("/upload-batch", response_model=List[Document])
async def upload_documents_batch(
    files: List[UploadFile] = File(...),
    folder_id: Optional[str] = Form(None),
    auto_process: bool = Form(True),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Upload multiple documents at once
    """
    try:
        uploaded_documents = []
        errors = []
        
        for file in files:
            try:
                # Validate file type
                file_extension = file.filename.split(".")[-1].lower()
                if file_extension not in settings.ALLOWED_FILE_TYPES:
                    errors.append({
                        "filename": file.filename,
                        "error": f"File type '{file_extension}' is not allowed"
                    })
                    continue
                
                # Validate file size
                content = await file.read()
                file_size = len(content)
                
                if file_size > settings.max_file_size_bytes:
                    errors.append({
                        "filename": file.filename,
                        "error": f"File size exceeds maximum allowed size"
                    })
                    continue
                
                # Reset file pointer
                await file.seek(0)
                
                from app.services.document_service import document_service
                
                document = await document_service.upload_document(
                    user_id=current_user["id"],
                    file=file,
                    content=content,
                    folder_id=folder_id,
                    auto_process=auto_process
                )
                
                uploaded_documents.append(Document(
                    id=document["id"],
                    name=document["name"],
                    type=document["type"],
                    size=document["size"],
                    status=document["status"],
                    metadata=document.get("metadata", {}),
                    created_at=document["created_at"],
                    updated_at=document["updated_at"],
                    tags=document.get("tags", [])
                ))
                
            except Exception as e:
                errors.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        if errors and not uploaded_documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "All uploads failed", "errors": errors}
            )
        
        if errors:
            # Some uploads succeeded, some failed
            logger.warning(f"Partial batch upload failure: {errors}")
        
        return uploaded_documents
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch upload error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific document
    """
    try:
        from app.services.document_service import document_service
        
        document = await document_service.get_document(
            document_id=document_id,
            user_id=current_user["id"]
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return Document(
            id=document["id"],
            name=document["name"],
            type=document["type"],
            size=document["size"],
            status=document["status"],
            metadata=document.get("metadata", {}),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            tags=document.get("tags", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.post("/{document_id}/process", response_model=ProcessingResult)
async def process_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Process a document to extract text and metadata
    """
    try:
        from app.services.document_service import document_service
        
        result = await document_service.process_document(
            document_id=document_id,
            user_id=current_user["id"]
        )
        
        return ProcessingResult(
            document_id=result["document_id"],
            status=result["status"],
            extracted_text=result.get("extracted_text"),
            metadata=result.get("metadata", {}),
            processing_time=result["processing_time"]
        )
        
    except Exception as e:
        logger.error(f"Process document error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get extracted content of a document
    """
    try:
        from app.services.document_service import document_service
        
        content = await document_service.get_document_content(
            document_id=document_id,
            user_id=current_user["id"]
        )
        
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document content not found"
            )
        
        return {"document_id": document_id, "content": content}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document content error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document content: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Delete a document
    """
    try:
        from app.services.document_service import document_service
        
        success = await document_service.delete_document(
            document_id=document_id,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/folders/", response_model=List[DocumentFolder])
async def get_folders(
    parent_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get document folders
    """
    try:
        from app.services.document_service import document_service
        
        folders = await document_service.get_user_folders(
            user_id=current_user["id"],
            parent_id=parent_id
        )
        
        return [
            DocumentFolder(
                id=folder["id"],
                name=folder["name"],
                parent_id=folder.get("parent_id"),
                document_count=folder["document_count"],
                created_at=folder["created_at"],
                updated_at=folder["updated_at"]
            )
            for folder in folders
        ]
        
    except Exception as e:
        logger.error(f"Get folders error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve folders: {str(e)}"
        )


@router.post("/folders/", response_model=DocumentFolder)
async def create_folder(
    request: CreateFolder,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Create a new folder
    """
    try:
        from app.services.document_service import document_service
        
        folder = await document_service.create_folder(
            user_id=current_user["id"],
            name=request.name,
            parent_id=request.parent_id
        )
        
        return DocumentFolder(
            id=folder["id"],
            name=folder["name"],
            parent_id=folder.get("parent_id"),
            document_count=0,
            created_at=folder["created_at"],
            updated_at=folder["updated_at"]
        )
        
    except Exception as e:
        logger.error(f"Create folder error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create folder: {str(e)}"
        )