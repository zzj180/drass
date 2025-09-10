from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.security import get_current_active_user, require_role
from app.core.config import settings as app_settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Pydantic models
class LLMSettings(BaseModel):
    provider: str = Field(..., description="LLM provider")
    model: str = Field(..., description="Model name")
    api_key: Optional[str] = Field(default=None, description="API key (write-only)")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1)


class EmbeddingSettings(BaseModel):
    provider: str = Field(..., description="Embedding provider")
    model: str = Field(..., description="Model name")
    api_key: Optional[str] = Field(default=None, description="API key (write-only)")
    dimensions: int = Field(default=1536, ge=1)
    batch_size: int = Field(default=100, ge=1)


class VectorStoreSettings(BaseModel):
    type: str = Field(..., description="Vector store type")
    host: str = Field(..., description="Host address")
    port: int = Field(..., description="Port number")
    collection: str = Field(..., description="Collection/index name")
    api_key: Optional[str] = Field(default=None, description="API key if required")


class RerankingSettings(BaseModel):
    enabled: bool = Field(default=False)
    provider: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    top_k: int = Field(default=10, ge=1)


class UserSettings(BaseModel):
    theme: str = Field(default="system", description="UI theme")
    language: str = Field(default="en", description="Interface language")
    notifications_enabled: bool = Field(default=True)
    auto_save: bool = Field(default=True)
    streaming_enabled: bool = Field(default=True)


class SystemSettings(BaseModel):
    llm: LLMSettings
    embedding: EmbeddingSettings
    vector_store: VectorStoreSettings
    reranking: RerankingSettings


@router.get("/user", response_model=UserSettings)
async def get_user_settings(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get user-specific settings
    """
    try:
        from app.services.settings_service import settings_service
        
        settings = await settings_service.get_user_settings(current_user["id"])
        
        return UserSettings(
            theme=settings.get("theme", "system"),
            language=settings.get("language", "en"),
            notifications_enabled=settings.get("notifications_enabled", True),
            auto_save=settings.get("auto_save", True),
            streaming_enabled=settings.get("streaming_enabled", True)
        )
        
    except Exception as e:
        logger.error(f"Get user settings error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user settings: {str(e)}"
        )


@router.put("/user", response_model=UserSettings)
async def update_user_settings(
    settings: UserSettings,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Update user-specific settings
    """
    try:
        from app.services.settings_service import settings_service
        
        updated_settings = await settings_service.update_user_settings(
            user_id=current_user["id"],
            settings=settings.dict()
        )
        
        return UserSettings(**updated_settings)
        
    except Exception as e:
        logger.error(f"Update user settings error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user settings: {str(e)}"
        )


@router.get("/system")
async def get_system_settings(
    current_user: Dict[str, Any] = Depends(require_role("admin"))
):
    """
    Get system-wide settings (admin only)
    """
    try:
        # Return current configuration (without sensitive data)
        return {
            "llm": {
                "provider": app_settings.LLM_PROVIDER,
                "model": app_settings.LLM_MODEL,
                "temperature": app_settings.LLM_TEMPERATURE,
                "max_tokens": app_settings.LLM_MAX_TOKENS,
                "api_key": "***" if app_settings.LLM_API_KEY else None
            },
            "embedding": {
                "provider": app_settings.EMBEDDING_PROVIDER,
                "model": app_settings.EMBEDDING_MODEL,
                "dimensions": app_settings.EMBEDDING_DIMENSIONS,
                "batch_size": app_settings.EMBEDDING_BATCH_SIZE,
                "api_key": "***" if app_settings.EMBEDDING_API_KEY else None
            },
            "vector_store": {
                "type": app_settings.VECTOR_STORE_TYPE,
                "host": app_settings.VECTOR_STORE_HOST,
                "port": app_settings.VECTOR_STORE_PORT,
                "collection": app_settings.VECTOR_STORE_COLLECTION,
                "api_key": "***" if app_settings.VECTOR_STORE_API_KEY else None
            },
            "reranking": {
                "enabled": app_settings.RERANKING_ENABLED,
                "provider": app_settings.RERANKING_PROVIDER,
                "model": app_settings.RERANKING_MODEL,
                "top_k": app_settings.RERANKING_TOP_K,
                "api_key": "***" if app_settings.RERANKING_API_KEY else None
            },
            "document_processing": {
                "max_file_size_mb": app_settings.MAX_FILE_SIZE_MB,
                "allowed_file_types": app_settings.ALLOWED_FILE_TYPES,
                "chunk_size": app_settings.CHUNK_SIZE,
                "chunk_overlap": app_settings.CHUNK_OVERLAP
            },
            "features": {
                "streaming": app_settings.ENABLE_STREAMING,
                "memory": app_settings.ENABLE_MEMORY,
                "tools": app_settings.ENABLE_TOOLS,
                "agent": app_settings.ENABLE_AGENT
            }
        }
        
    except Exception as e:
        logger.error(f"Get system settings error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system settings: {str(e)}"
        )


@router.post("/test/llm")
async def test_llm_connection(
    settings: LLMSettings,
    current_user: Dict[str, Any] = Depends(require_role("admin"))
):
    """
    Test LLM connection with provided settings
    """
    try:
        from app.services.llm_service import test_llm_connection
        
        result = await test_llm_connection(
            provider=settings.provider,
            model=settings.model,
            api_key=settings.api_key,
            temperature=settings.temperature
        )
        
        return {
            "status": "success" if result["success"] else "failed",
            "message": result.get("message", "Connection test completed"),
            "response": result.get("response")
        }
        
    except Exception as e:
        logger.error(f"LLM connection test error: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "message": str(e)
        }


@router.post("/test/embedding")
async def test_embedding_connection(
    settings: EmbeddingSettings,
    current_user: Dict[str, Any] = Depends(require_role("admin"))
):
    """
    Test embedding service connection
    """
    try:
        from app.services.embedding_service import test_embedding_connection
        
        result = await test_embedding_connection(
            provider=settings.provider,
            model=settings.model,
            api_key=settings.api_key
        )
        
        return {
            "status": "success" if result["success"] else "failed",
            "message": result.get("message", "Connection test completed"),
            "dimensions": result.get("dimensions")
        }
        
    except Exception as e:
        logger.error(f"Embedding connection test error: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "message": str(e)
        }


@router.post("/test/vector-store")
async def test_vector_store_connection(
    settings: VectorStoreSettings,
    current_user: Dict[str, Any] = Depends(require_role("admin"))
):
    """
    Test vector store connection
    """
    try:
        from app.services.vector_store import test_vector_store_connection
        
        result = await test_vector_store_connection(
            type=settings.type,
            host=settings.host,
            port=settings.port,
            collection=settings.collection,
            api_key=settings.api_key
        )
        
        return {
            "status": "success" if result["success"] else "failed",
            "message": result.get("message", "Connection test completed"),
            "collections": result.get("collections")
        }
        
    except Exception as e:
        logger.error(f"Vector store connection test error: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "message": str(e)
        }


@router.get("/stats")
async def get_system_stats(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get system usage statistics
    """
    try:
        from app.services.stats_service import stats_service
        
        stats = await stats_service.get_user_stats(current_user["id"])
        
        return {
            "user_stats": {
                "total_conversations": stats.get("total_conversations", 0),
                "total_messages": stats.get("total_messages", 0),
                "total_documents": stats.get("total_documents", 0),
                "total_knowledge_bases": stats.get("total_knowledge_bases", 0),
                "storage_used_mb": stats.get("storage_used_mb", 0),
                "tokens_used": stats.get("tokens_used", 0)
            },
            "limits": {
                "max_file_size_mb": app_settings.MAX_FILE_SIZE_MB,
                "rate_limit_per_minute": app_settings.RATE_LIMIT_PER_MINUTE
            }
        }
        
    except Exception as e:
        logger.error(f"Get stats error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.post("/clear-cache")
async def clear_cache(
    current_user: Dict[str, Any] = Depends(require_role("admin"))
):
    """
    Clear system cache (admin only)
    """
    try:
        from app.services.cache_service import cache_service
        
        await cache_service.clear_all()
        
        return {"message": "Cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Clear cache error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )