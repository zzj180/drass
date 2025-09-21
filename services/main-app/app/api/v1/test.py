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
from app.core.performance_config import performance_config

router = APIRouter()
logger = logging.getLogger(__name__)


class TestChatRequest(BaseModel):
    """Test chat request model"""
    message: str = Field(..., description="User message")
    context: Optional[str] = Field(None, description="Optional context")
    use_rag: bool = Field(default=True, description="Whether to use RAG")
    temperature: Optional[float] = Field(default=0.7, description="Temperature for generation")
    max_tokens: Optional[int] = Field(default=512, description="Maximum tokens to generate")
    response_type: Optional[str] = Field(default="standard", description="Response type: quick, standard, detailed, analysis")


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
    Test chat endpoint without authentication with performance optimization
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Test chat request: {request.message[:50]}...")
        
        # Get performance-optimized configuration
        perf_config = performance_config.get_config_for_type(request.response_type or "standard")
        
        # Calculate optimal parameters
        optimal_tokens = performance_config.get_optimal_tokens(
            len(request.message), 
            request.response_type or "standard"
        )
        optimal_timeout = performance_config.get_optimal_timeout(optimal_tokens)
        
        # Use provided max_tokens or calculated optimal tokens
        final_max_tokens = request.max_tokens or optimal_tokens
        
        logger.info(f"Performance config - Tokens: {final_max_tokens}, Timeout: {optimal_timeout}s, Type: {request.response_type}")
        
        if request.use_rag:
            # Use optimized RAG service
            from app.services.rag_optimization_service import rag_optimization_service
            
            # Initialize if needed
            if not rag_optimization_service._initialized:
                await rag_optimization_service.initialize()
            
            # Use optimized RAG query
            result = await rag_optimization_service.optimized_query(
                query=request.message,
                response_type=request.response_type or "standard",
                use_adaptive=True
            )
            
            response = result.get("answer", "")
            optimization_info = result.get("optimization", {})
        else:
            # Direct LLM call with optimized parameters
            response = await llm_service.generate(
                prompt=request.message,
                max_tokens=final_max_tokens,
                temperature=request.temperature or perf_config["temperature"]
            )
            optimization_info = {}
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Log slow requests
        if performance_config.LOG_SLOW_REQUESTS and response_time > performance_config.SLOW_REQUEST_THRESHOLD:
            logger.warning(f"Slow request detected: {response_time:.2f}s (threshold: {performance_config.SLOW_REQUEST_THRESHOLD}s)")
        
        return {
            "status": "success",
            "message": request.message,
            "response": response,
            "used_rag": request.use_rag,
            "performance": {
                "response_time": round(response_time, 2),
                "optimization": optimization_info,
                "max_tokens": final_max_tokens,
                "response_type": request.response_type,
                "timeout_configured": optimal_timeout
            }
        }
        
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        logger.error(f"Test chat error after {response_time:.2f}s: {e}")
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