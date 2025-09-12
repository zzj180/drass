"""
Chat service for handling LangChain interactions
"""

from typing import Optional, AsyncGenerator, Dict, Any
import logging
from app.core.config import settings
from app.chains.compliance_rag_chain import ComplianceRAGChain

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat interactions with LangChain"""
    
    def __init__(self):
        self.rag_chain = None
        self._initialize_chain()
    
    def _initialize_chain(self):
        """Initialize the RAG chain"""
        try:
            self.rag_chain = ComplianceRAGChain()
            logger.info("RAG chain initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG chain: {e}")
            # Continue without RAG chain for now
    
    async def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Process a chat message through the RAG chain
        
        Args:
            message: User message
            session_id: Optional session ID for conversation history
            stream: Whether to stream the response
            
        Returns:
            Response dictionary
        """
        try:
            if not self.rag_chain:
                return {
                    "response": "I'm sorry, the RAG chain is not initialized. Please check the configuration.",
                    "sources": []
                }
            
            # Process message through RAG chain
            # Use ainvoke for async processing
            result = await self.rag_chain.ainvoke(
                {"query": message}
            )
            
            return {
                "response": result.get("answer", ""),
                "sources": result.get("sources", [])
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "response": f"An error occurred: {str(e)}",
                "sources": []
            }
    
    async def stream_response(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from the RAG chain
        
        Args:
            message: User message
            session_id: Optional session ID
            
        Yields:
            Response chunks
        """
        try:
            if not self.rag_chain:
                yield "I'm sorry, the RAG chain is not initialized."
                return
            
            # Stream response from RAG chain
            async for chunk in self.rag_chain.astream(
                query=message,
                session_id=session_id
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield f"An error occurred: {str(e)}"


# Singleton instance
chat_service = ChatService()