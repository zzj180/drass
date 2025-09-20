"""
Test endpoints for RAG functionality without authentication
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.services.chat_service import chat_service
from app.services.vector_store import vector_store_service
from app.services.llm_service import llm_service
from app.services.embedding_service import embedding_service

router = APIRouter()
logger = logging.getLogger(__name__)


class TestChatRequest(BaseModel):
    """Test chat request model"""
    message: str = Field(..., description="User message")
    context: Optional[str] = Field(None, description="Optional context")
    use_rag: bool = Field(default=True, description="Whether to use RAG")
    temperature: Optional[float] = Field(default=0.7, description="Temperature for generation")
    max_tokens: Optional[int] = Field(default=4096, description="Maximum tokens to generate")


class TestEmbeddingRequest(BaseModel):
    """Test embedding request model"""
    text: str = Field(..., description="Text to embed")


class TestDocumentRequest(BaseModel):
    """Test document request model"""
    content: str = Field(..., description="Document content")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Document metadata")


@router.post("/chat")
async def test_chat(request: TestChatRequest) -> Dict[str, Any]:
    """
    Test chat endpoint without authentication
    """
    try:
        logger.info(f"Test chat request: {request.message[:50]}...")
        
        if request.use_rag:
            # Use RAG chain for response
            result = await chat_service.process_message(
                message=request.message,
                session_id="test-session"
            )
            response = result.get("response", "")
        else:
            # Direct LLM call with provided temperature
            response = await llm_service.generate(
                prompt=request.message,
                max_tokens=request.max_tokens or 2048,  # 使用更大的默认token数量
                temperature=request.temperature
            )
        
        return {
            "status": "success",
            "message": request.message,
            "response": response,
            "used_rag": request.use_rag
        }
        
    except Exception as e:
        logger.error(f"Test chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embedding")
async def test_embedding(request: TestEmbeddingRequest) -> Dict[str, Any]:
    """
    Test embedding generation endpoint
    """
    try:
        logger.info(f"Test embedding request for text: {request.text[:50]}...")
        
        # Generate embedding
        embedding = await embedding_service.embed_query(request.text)
        
        return {
            "status": "success",
            "text": request.text,
            "embedding_size": len(embedding) if embedding else 0,
            "embedding_sample": embedding[:5] if embedding else None
        }
        
    except Exception as e:
        logger.error(f"Test embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-document")
async def test_add_document(request: TestDocumentRequest) -> Dict[str, Any]:
    """
    Test adding document to vector store
    """
    try:
        logger.info("Test add document request")
        
        # Add document to vector store
        success = await vector_store_service.add_documents([{
            "content": request.content,
            "metadata": request.metadata
        }])
        
        return {
            "status": "success" if success else "failed",
            "message": "Document added to vector store" if success else "Failed to add document"
        }
        
    except Exception as e:
        logger.error(f"Test add document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def test_search(query: str, k: int = 5) -> Dict[str, Any]:
    """
    Test vector store search
    """
    try:
        logger.info(f"Test search request: {query}")
        
        # Search in vector store
        results = await vector_store_service.search(
            query=query,
            k=k
        )
        
        return {
            "status": "success",
            "query": query,
            "num_results": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Test search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services-status")
async def test_services_status() -> Dict[str, Any]:
    """
    Get status of all services
    """
    try:
        status = {
            "llm_service": await llm_service.health_check(),
            "embedding_service": await embedding_service.health_check(),
            "vector_store": await vector_store_service.health_check(),
            "chat_service": {
                "status": "healthy" if chat_service.rag_chain else "not_initialized"
            }
        }
        
        return {
            "status": "success",
            "services": status
        }
        
    except Exception as e:
        logger.error(f"Test services status error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/test-rag-pipeline")
async def test_rag_pipeline() -> Dict[str, Any]:
    """
    Test the complete RAG pipeline with sample data
    """
    try:
        logger.info("Testing complete RAG pipeline")
        
        # Step 1: Add test documents
        test_docs = [
            {
                "content": "LangChain is a framework for developing applications powered by language models.",
                "metadata": {"source": "test", "topic": "langchain"}
            },
            {
                "content": "RAG (Retrieval-Augmented Generation) combines retrieval with generation for better responses.",
                "metadata": {"source": "test", "topic": "rag"}
            },
            {
                "content": "Compliance management involves ensuring adherence to regulations and standards.",
                "metadata": {"source": "test", "topic": "compliance"}
            }
        ]
        
        add_result = await vector_store_service.add_documents(test_docs)
        
        # Step 2: Test retrieval
        search_results = await vector_store_service.search(
            query="What is RAG?",
            k=2
        )
        
        # Step 3: Test generation with context
        chat_result = await chat_service.process_message(
            message="Explain RAG in simple terms",
            session_id="test-pipeline"
        )
        chat_response = chat_result.get("response", "")
        
        return {
            "status": "success",
            "pipeline_test": {
                "documents_added": add_result,
                "retrieval_count": len(search_results),
                "retrieval_sample": search_results[0] if search_results else None,
                "generation_response": chat_response
            }
        }
        
    except Exception as e:
        logger.error(f"RAG pipeline test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))