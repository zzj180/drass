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
class KnowledgeBase(BaseModel):
    id: str = Field(..., description="Knowledge base ID")
    name: str = Field(..., description="Knowledge base name")
    description: Optional[str] = Field(default=None, description="Description")
    source_count: int = Field(default=0, description="Number of sources")
    total_chunks: int = Field(default=0, description="Total number of chunks")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CreateKnowledgeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Knowledge base name")
    description: Optional[str] = Field(default=None, max_length=1000, description="Description")


class KnowledgeSource(BaseModel):
    id: str = Field(..., description="Source ID")
    knowledge_base_id: str = Field(..., description="Knowledge base ID")
    name: str = Field(..., description="Source name")
    type: str = Field(..., description="Source type: file, url, or text")
    status: str = Field(..., description="Processing status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class AddTextSource(BaseModel):
    name: str = Field(..., description="Source name")
    content: str = Field(..., description="Text content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")


class AddUrlSource(BaseModel):
    url: str = Field(..., description="URL to fetch and index")
    name: Optional[str] = Field(default=None, description="Optional source name")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    knowledge_base_ids: Optional[List[str]] = Field(default=None, description="Specific knowledge bases to search")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    similarity_threshold: float = Field(default=0.7, ge=0, le=1, description="Minimum similarity score")
    rerank: bool = Field(default=False, description="Enable reranking")


class SearchResult(BaseModel):
    id: str = Field(..., description="Result ID")
    content: str = Field(..., description="Content snippet")
    score: float = Field(..., description="Similarity score")
    metadata: Dict[str, Any] = Field(..., description="Result metadata")
    source: Dict[str, Any] = Field(..., description="Source information")


@router.get("/bases", response_model=List[KnowledgeBase])
async def get_knowledge_bases(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get all knowledge bases for the current user
    """
    try:
        from app.services.knowledge_service import knowledge_service
        
        bases = await knowledge_service.get_user_knowledge_bases(user_id=current_user["id"])
        
        return [
            KnowledgeBase(
                id=base["id"],
                name=base["name"],
                description=base.get("description"),
                source_count=base["source_count"],
                total_chunks=base["total_chunks"],
                created_at=base["created_at"],
                updated_at=base["updated_at"]
            )
            for base in bases
        ]
        
    except Exception as e:
        logger.error(f"Get knowledge bases error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve knowledge bases: {str(e)}"
        )


@router.post("/bases", response_model=KnowledgeBase)
async def create_knowledge_base(
    request: CreateKnowledgeBase,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Create a new knowledge base
    """
    try:
        from app.services.knowledge_service import knowledge_service
        
        base = await knowledge_service.create_knowledge_base(
            user_id=current_user["id"],
            name=request.name,
            description=request.description
        )
        
        return KnowledgeBase(
            id=base["id"],
            name=base["name"],
            description=base.get("description"),
            source_count=0,
            total_chunks=0,
            created_at=base["created_at"],
            updated_at=base["updated_at"]
        )
        
    except Exception as e:
        logger.error(f"Create knowledge base error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge base: {str(e)}"
        )


@router.get("/bases/{base_id}", response_model=KnowledgeBase)
async def get_knowledge_base(
    base_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific knowledge base
    """
    try:
        from app.services.knowledge_service import knowledge_service
        
        base = await knowledge_service.get_knowledge_base(
            base_id=base_id,
            user_id=current_user["id"]
        )
        
        if not base:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        return KnowledgeBase(
            id=base["id"],
            name=base["name"],
            description=base.get("description"),
            source_count=base["source_count"],
            total_chunks=base["total_chunks"],
            created_at=base["created_at"],
            updated_at=base["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get knowledge base error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve knowledge base: {str(e)}"
        )


@router.delete("/bases/{base_id}")
async def delete_knowledge_base(
    base_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Delete a knowledge base
    """
    try:
        from app.services.knowledge_service import knowledge_service
        
        success = await knowledge_service.delete_knowledge_base(
            base_id=base_id,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        return {"message": "Knowledge base deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete knowledge base error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete knowledge base: {str(e)}"
        )


@router.get("/bases/{base_id}/sources", response_model=List[KnowledgeSource])
async def get_knowledge_sources(
    base_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get all sources in a knowledge base
    """
    try:
        from app.services.knowledge_service import knowledge_service
        
        sources = await knowledge_service.get_knowledge_sources(
            base_id=base_id,
            user_id=current_user["id"]
        )
        
        return [
            KnowledgeSource(
                id=source["id"],
                knowledge_base_id=source["knowledge_base_id"],
                name=source["name"],
                type=source["type"],
                status=source["status"],
                metadata=source.get("metadata", {}),
                created_at=source["created_at"],
                updated_at=source["updated_at"]
            )
            for source in sources
        ]
        
    except Exception as e:
        logger.error(f"Get knowledge sources error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve knowledge sources: {str(e)}"
        )


@router.post("/bases/{base_id}/upload", response_model=KnowledgeSource)
async def upload_document(
    base_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Upload a document to a knowledge base
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
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        
        from app.services.knowledge_service import knowledge_service
        
        source = await knowledge_service.add_document_source(
            base_id=base_id,
            user_id=current_user["id"],
            file=file,
            content=content
        )
        
        return KnowledgeSource(
            id=source["id"],
            knowledge_base_id=source["knowledge_base_id"],
            name=source["name"],
            type="file",
            status=source["status"],
            metadata=source.get("metadata", {}),
            created_at=source["created_at"],
            updated_at=source["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload document error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.post("/bases/{base_id}/text", response_model=KnowledgeSource)
async def add_text_source(
    base_id: str,
    request: AddTextSource,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Add text content as a knowledge source
    """
    try:
        from app.services.knowledge_service import knowledge_service
        
        source = await knowledge_service.add_text_source(
            base_id=base_id,
            user_id=current_user["id"],
            name=request.name,
            content=request.content,
            metadata=request.metadata
        )
        
        return KnowledgeSource(
            id=source["id"],
            knowledge_base_id=source["knowledge_base_id"],
            name=source["name"],
            type="text",
            status=source["status"],
            metadata=source.get("metadata", {}),
            created_at=source["created_at"],
            updated_at=source["updated_at"]
        )
        
    except Exception as e:
        logger.error(f"Add text source error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add text source: {str(e)}"
        )


@router.post("/bases/{base_id}/url", response_model=KnowledgeSource)
async def add_url_source(
    base_id: str,
    request: AddUrlSource,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Add URL content as a knowledge source
    """
    try:
        from app.services.knowledge_service import knowledge_service
        
        source = await knowledge_service.add_url_source(
            base_id=base_id,
            user_id=current_user["id"],
            url=request.url,
            name=request.name,
            metadata=request.metadata
        )
        
        return KnowledgeSource(
            id=source["id"],
            knowledge_base_id=source["knowledge_base_id"],
            name=source["name"],
            type="url",
            status=source["status"],
            metadata=source.get("metadata", {}),
            created_at=source["created_at"],
            updated_at=source["updated_at"]
        )
        
    except Exception as e:
        logger.error(f"Add URL source error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add URL source: {str(e)}"
        )


@router.delete("/bases/{base_id}/sources/{source_id}")
async def delete_knowledge_source(
    base_id: str,
    source_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Delete a knowledge source
    """
    try:
        from app.services.knowledge_service import knowledge_service
        
        success = await knowledge_service.delete_knowledge_source(
            base_id=base_id,
            source_id=source_id,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge source not found"
            )
        
        return {"message": "Knowledge source deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete knowledge source error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete knowledge source: {str(e)}"
        )


@router.post("/search", response_model=List[SearchResult])
async def search_knowledge(
    request: SearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Search across knowledge bases
    """
    try:
        from app.services.knowledge_service import knowledge_service
        
        results = await knowledge_service.search(
            query=request.query,
            user_id=current_user["id"],
            knowledge_base_ids=request.knowledge_base_ids,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold,
            rerank=request.rerank
        )
        
        return [
            SearchResult(
                id=result["id"],
                content=result["content"],
                score=result["score"],
                metadata=result["metadata"],
                source=result["source"]
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Search knowledge error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )