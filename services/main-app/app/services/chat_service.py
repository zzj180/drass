"""
Chat service for handling LangChain interactions
"""

from typing import Optional, AsyncGenerator, Dict, Any, List
import logging
from app.core.config import settings
from app.chains.compliance_rag_chain import ComplianceRAGChain
from app.core.logging import get_logger

logger = get_logger(__name__)


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

    async def process_chat(
        self,
        messages: List[Dict[str, str]],
        conversation_id: str,
        user_id: str,
        model: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = None,
        use_knowledge_base: bool = True,
        knowledge_base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process chat messages with full conversation context

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            conversation_id: Conversation ID
            user_id: User ID
            model: Optional model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            use_knowledge_base: Whether to use knowledge base
            knowledge_base_id: Optional specific knowledge base ID

        Returns:
            Response dictionary with message, sources, and usage
        """
        try:
            # Get the latest user message
            # Handle both dict and ChatMessage objects
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, 'content'):
                    user_message = last_msg.content
                else:
                    user_message = last_msg.get('content', '')
            else:
                user_message = ""

            # If not using knowledge base or RAG chain not available, use LLM directly
            if not use_knowledge_base or not self.rag_chain:
                from app.services.llm_service_enhanced import unified_llm_service

                # Format messages for LLM
                formatted_messages = []
                for msg in messages:
                    if hasattr(msg, 'role') and hasattr(msg, 'content'):
                        # ChatMessage object
                        formatted_messages.append({
                            "role": msg.role,
                            "content": msg.content
                        })
                    else:
                        # Dictionary
                        formatted_messages.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", "")
                        })

                # Get response from LLM
                response = await unified_llm_service.generate(
                    messages=formatted_messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Handle LLMResponse object
                content = response.content if hasattr(response, 'content') else str(response)
                usage = response.usage if hasattr(response, 'usage') else {}

                return {
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "sources": [],
                    "usage": usage
                }

            # Use RAG chain for knowledge-based response
            result = await self.rag_chain.ainvoke(
                {"query": user_message}
            )

            return {
                "message": {
                    "role": "assistant",
                    "content": result.get("answer", "")
                },
                "sources": result.get("sources", []),
                "usage": {}
            }

        except Exception as e:
            logger.error(f"Error processing chat: {e}", exc_info=True)
            return {
                "message": {
                    "role": "assistant",
                    "content": f"I apologize, but I encountered an error processing your request. Please try again."
                },
                "sources": [],
                "usage": {}
            }

    async def process_chat_stream(
        self,
        messages: List[Dict[str, str]],
        conversation_id: str,
        user_id: str,
        model: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = None,
        use_knowledge_base: bool = True,
        knowledge_base_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response

        Args:
            messages: List of message dictionaries
            conversation_id: Conversation ID
            user_id: User ID
            model: Optional model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            use_knowledge_base: Whether to use knowledge base
            knowledge_base_id: Optional specific knowledge base ID

        Yields:
            Response chunks
        """
        try:
            # Get the latest user message
            # Handle both dict and ChatMessage objects
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, 'content'):
                    user_message = last_msg.content
                else:
                    user_message = last_msg.get('content', '')
            else:
                user_message = ""

            if not use_knowledge_base or not self.rag_chain:
                from app.services.llm_service_enhanced import unified_llm_service

                # Format messages for LLM
                formatted_messages = []
                for msg in messages:
                    if hasattr(msg, 'role') and hasattr(msg, 'content'):
                        # ChatMessage object
                        formatted_messages.append({
                            "role": msg.role,
                            "content": msg.content
                        })
                    else:
                        # Dictionary
                        formatted_messages.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", "")
                        })

                # Stream response from LLM
                async for chunk in unified_llm_service.stream(
                    messages=formatted_messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    yield chunk
            else:
                # Stream from RAG chain
                async for chunk in self.rag_chain.astream(
                    query=user_message,
                    session_id=conversation_id
                ):
                    yield chunk

        except Exception as e:
            logger.error(f"Error streaming chat: {e}", exc_info=True)
            yield f"Error: {str(e)}"


# Singleton instance
chat_service = ChatService()