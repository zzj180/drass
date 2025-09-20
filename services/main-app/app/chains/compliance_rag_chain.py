"""
LangChain RAG Chain Implementation for Compliance Assistant
"""

from typing import List, Dict, Any, Optional
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.base import AsyncCallbackHandler
import logging

from app.core.config import settings
from app.chains.prompts import (
    COMPLIANCE_SYSTEM_PROMPT,
    COMPLIANCE_QA_PROMPT,
    CONDENSE_QUESTION_PROMPT,
    MULTI_QUERY_PROMPT
)
from app.chains.compliance_prompts import (
    DEFAULT_COMPLIANCE_CONFIG,
    EXPANSION_PROMPT
)

logger = logging.getLogger(__name__)


class StreamingCallbackHandler(AsyncCallbackHandler):
    """
    Custom callback handler for streaming responses
    """
    
    def __init__(self, queue):
        self.queue = queue
        
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when LLM generates a new token"""
        await self.queue.put({"type": "token", "content": token})
        
    async def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM finishes generating"""
        await self.queue.put({"type": "end"})
        
    async def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Called when LLM encounters an error"""
        await self.queue.put({"type": "error", "error": str(error)})


class ComplianceRAGChain:
    """
    Main RAG chain for compliance assistance
    """
    
    def __init__(
        self,
        llm: Optional[Any] = None,
        embeddings: Optional[Any] = None,
        vector_store: Optional[Any] = None,
        memory: Optional[Any] = None,
        use_reranking: bool = False,
        use_multi_query: bool = True,
        k: int = 5,
        rerank_k: int = 3
    ):
        """
        Initialize the RAG chain
        
        Args:
            llm: Language model instance
            embeddings: Embeddings model instance
            vector_store: Vector store instance
            memory: Memory instance for conversation history
            use_reranking: Whether to use reranking
            use_multi_query: Whether to use multi-query retrieval
            k: Number of documents to retrieve
            rerank_k: Number of documents after reranking
        """
        self.llm = llm or self._create_default_llm()
        self.embeddings = embeddings or self._create_default_embeddings()
        self.vector_store = vector_store
        self.memory = memory or self._create_default_memory()
        self.use_reranking = use_reranking
        self.use_multi_query = use_multi_query
        self.k = k
        self.rerank_k = rerank_k
        
        # Initialize components
        self.retriever = None
        self.qa_chain = None
        self.conversational_chain = None
        
        if self.vector_store:
            self._setup_retriever()
            self._setup_chains()
    
    def _create_default_llm(self):
        """Create default LLM instance"""
        if settings.LLM_PROVIDER == "openrouter":
            return ChatOpenAI(
                model_name=settings.LLM_MODEL,
                openai_api_key=settings.OPENROUTER_API_KEY,
                openai_api_base=settings.OPENROUTER_BASE_URL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                streaming=True
            )
        elif settings.LLM_PROVIDER == "openai":
            # LM Studio with MLX or standard OpenAI
            return ChatOpenAI(
                model_name=settings.LLM_MODEL,
                openai_api_key=settings.LLM_API_KEY or "not-required",  # LM Studio doesn't need key
                openai_api_base=settings.LLM_BASE_URL or "http://localhost:1234/v1",
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                streaming=True,
                request_timeout=settings.LLM_TIMEOUT
            )
        elif settings.LLM_PROVIDER == "vllm":
            # vLLM uses OpenAI-compatible API
            return ChatOpenAI(
                model_name=settings.LLM_MODEL,
                openai_api_key="not-required",
                openai_api_base="http://localhost:8001/v1",
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                streaming=True,
                request_timeout=settings.LLM_TIMEOUT
            )
        else:
            # Fallback to standard OpenAI
            return ChatOpenAI(
                model_name=settings.LLM_MODEL,
                openai_api_key=settings.LLM_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                streaming=True
            )
    
    def _create_default_embeddings(self):
        """Create default embeddings instance"""
        # Use local embedding service or fallback to HuggingFace
        if hasattr(settings, 'EMBEDDING_PROVIDER') and settings.EMBEDDING_PROVIDER == "custom":
            # Use custom embedding service via API
            from langchain.embeddings.base import Embeddings
            from typing import List
            import requests
            
            class CustomEmbeddings(Embeddings):
                def embed_documents(self, texts: List[str]) -> List[List[float]]:
                    response = requests.post(
                        f"{settings.EMBEDDING_API_BASE}/embeddings",
                        json={"texts": texts}
                    )
                    return response.json()["embeddings"]
                
                def embed_query(self, text: str) -> List[float]:
                    return self.embed_documents([text])[0]
            
            return CustomEmbeddings()
        else:
            # Fallback to HuggingFace embeddings
            from langchain.embeddings import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
    
    async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a query through the RAG chain asynchronously
        
        Args:
            inputs: Dictionary with 'query' key
            
        Returns:
            Dictionary with 'answer' and 'sources' keys
        """
        query = inputs.get("query", "")
        
        # Check if we have a vector store and knowledge base
        if self.vector_store and hasattr(self, 'retriever') and self.retriever:
            try:
                # Use RAG with knowledge base
                if self.qa_chain:
                    result = await self.qa_chain.ainvoke({"query": query})
                    return {
                        "answer": result.get("answer", ""),
                        "sources": result.get("source_documents", [])
                    }
            except Exception as e:
                logger.warning(f"RAG chain failed, falling back to direct LLM: {e}")
        
        # Fallback: Use LLM directly without RAG prompts
        try:
            from app.services.llm_service import llm_service
            
            response = await llm_service.generate(query, max_tokens=2048)
            
            return {
                "answer": response,
                "sources": []
            }
        except Exception as e:
            logger.error(f"Error in RAG chain ainvoke: {e}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": []
            }
    
    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper for ainvoke
        """
        import asyncio
        try:
            # Use the existing event loop if available
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context, can't use run_until_complete
                # Return a simple response for now
                query = inputs.get("query", "")
                return {
                    "answer": f"Processing query: {query}",
                    "sources": []
                }
            else:
                return loop.run_until_complete(self.ainvoke(inputs))
        except RuntimeError:
            # No event loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.ainvoke(inputs))
            finally:
                loop.close()
    
    def _create_default_memory(self):
        """Create default memory instance"""
        return ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
    
    def _setup_retriever(self):
        """Setup the retriever with optional enhancements"""
        if not self.vector_store:
            raise ValueError("Vector store is required for retriever setup")
        
        # Base retriever
        base_retriever = self.vector_store.as_retriever(
            search_kwargs={"k": self.k}
        )
        
        # Multi-query retriever
        if self.use_multi_query:
            base_retriever = MultiQueryRetriever.from_llm(
                retriever=base_retriever,
                llm=self.llm,
                prompt=MULTI_QUERY_PROMPT
            )
        
        # Reranking
        if self.use_reranking and settings.RERANKING_ENABLED:
            compressor = CohereRerank(
                cohere_api_key=settings.RERANKING_API_KEY,
                model=settings.RERANKING_MODEL,
                top_n=self.rerank_k
            )
            base_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=base_retriever
            )
        
        self.retriever = base_retriever
    
    def _setup_chains(self):
        """Setup QA and conversational chains"""
        # QA Chain for single questions
        self.qa_chain = self._create_qa_chain()
        
        # Conversational chain for chat with history
        self.conversational_chain = self._create_conversational_chain()
    
    def _create_qa_chain(self):
        """Create basic QA chain"""
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", COMPLIANCE_SYSTEM_PROMPT),
            ("human", COMPLIANCE_QA_PROMPT)
        ])
        
        # Create document chain
        document_chain = create_stuff_documents_chain(
            self.llm,
            qa_prompt
        )
        
        # Create retrieval chain
        retrieval_chain = create_retrieval_chain(
            self.retriever,
            document_chain
        )
        
        return retrieval_chain
    
    def _create_conversational_chain(self):
        """Create conversational retrieval chain"""
        # Contextualize question prompt
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", CONDENSE_QUESTION_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])
        
        # Create history-aware retriever
        history_aware_retriever = create_history_aware_retriever(
            self.llm,
            self.retriever,
            contextualize_q_prompt
        )
        
        # Answer prompt
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", COMPLIANCE_SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", COMPLIANCE_QA_PROMPT)
        ])
        
        # Create document chain
        document_chain = create_stuff_documents_chain(
            self.llm,
            qa_prompt
        )
        
        # Create retrieval chain
        retrieval_chain = create_retrieval_chain(
            history_aware_retriever,
            document_chain
        )
        
        return retrieval_chain
    
    async def ask(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        callbacks: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Ask a question using the RAG chain
        
        Args:
            question: The question to ask
            chat_history: Optional chat history
            stream: Whether to stream the response
            callbacks: Optional callbacks for streaming
        
        Returns:
            Dictionary containing answer and sources
        """
        try:
            if chat_history:
                # Use conversational chain
                formatted_history = self._format_chat_history(chat_history)
                
                if stream:
                    # Streaming with history
                    response = await self.conversational_chain.astream(
                        {
                            "input": question,
                            "chat_history": formatted_history
                        },
                        config={"callbacks": callbacks} if callbacks else None
                    )
                else:
                    # Non-streaming with history
                    response = await self.conversational_chain.ainvoke(
                        {
                            "input": question,
                            "chat_history": formatted_history
                        }
                    )
            else:
                # Use simple QA chain
                if stream:
                    # Streaming without history
                    response = await self.qa_chain.astream(
                        {"input": question},
                        config={"callbacks": callbacks} if callbacks else None
                    )
                else:
                    # Non-streaming without history
                    response = await self.qa_chain.ainvoke(
                        {"input": question}
                    )
            
            # Extract and format response
            return self._format_response(response)
            
        except Exception as e:
            logger.error(f"Error in RAG chain: {str(e)}", exc_info=True)
            raise
    
    def _format_chat_history(
        self,
        chat_history: List[Dict[str, str]]
    ) -> List:
        """Format chat history for the chain"""
        formatted = []
        for message in chat_history:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "user":
                formatted.append(HumanMessage(content=content))
            elif role == "assistant":
                formatted.append(AIMessage(content=content))
            elif role == "system":
                formatted.append(SystemMessage(content=content))
        
        return formatted
    
    def _format_response(self, response: Any) -> Dict[str, Any]:
        """Format the chain response with word count validation"""
        if isinstance(response, dict):
            answer = response.get("answer", "")
            context = response.get("context", [])
        else:
            answer = str(response)
            context = []

        # Extract sources from context documents
        sources = []
        for doc in context:
            if hasattr(doc, "metadata"):
                sources.append({
                    "content": doc.page_content[:500],  # Truncate for response
                    "metadata": doc.metadata
                })

        # Check word count for compliance responses
        if self._is_compliance_mode():
            answer = self._ensure_minimum_word_count_sync(answer, sources)

        return {
            "answer": answer,
            "sources": sources,
            "context_count": len(context)
        }
    
    def update_vector_store(self, vector_store: Any):
        """Update the vector store and reinitialize chains"""
        self.vector_store = vector_store
        if self.vector_store:
            self._setup_retriever()
            self._setup_chains()
    
    def clear_memory(self):
        """Clear conversation memory"""
        if self.memory:
            self.memory.clear()

    def _is_compliance_mode(self) -> bool:
        """Check if compliance mode is enabled"""
        # Check configuration for compliance mode
        return getattr(settings, 'COMPLIANCE_MODE_ENABLED', True)

    def _count_chinese_words(self, text: str) -> int:
        """Count Chinese words/characters in text"""
        # For Chinese text, count characters (excluding punctuation and spaces)
        import re
        # Remove spaces, punctuation, and count remaining characters
        chinese_text = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf]+', '', text)
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        return len(chinese_text) + english_words

    async def _ensure_minimum_word_count(
        self,
        answer: str,
        sources: List[Dict[str, Any]],
        min_words: int = None
    ) -> str:
        """
        Ensure the answer meets minimum word count requirement

        Args:
            answer: Current answer text
            sources: Source documents for context
            min_words: Minimum word count (default from config)

        Returns:
            Expanded answer if needed
        """
        if min_words is None:
            min_words = DEFAULT_COMPLIANCE_CONFIG.min_word_count

        current_count = self._count_chinese_words(answer)

        # If already meets requirement, return as is
        if current_count >= min_words:
            logger.info(f"Answer already has {current_count} words, meeting requirement of {min_words}")
            return answer

        logger.info(f"Answer has {current_count} words, expanding to meet {min_words} requirement")

        # Prepare expansion prompt
        expansion_attempts = 0
        max_attempts = 3
        expanded_answer = answer

        while current_count < min_words and expansion_attempts < max_attempts:
            expansion_attempts += 1

            # Create expansion prompt with context
            expansion_context = f"""
当前回答字数：{current_count}
要求字数：{min_words}
还需补充：{min_words - current_count}字

请基于以下已有回答进行深度扩展，确保：
1. 保持原有内容不变，在此基础上补充更多细节
2. 添加更多实例、案例分析、具体步骤说明
3. 深化每个要点的分析，提供更详细的实施指导
4. 补充相关的法规依据、最佳实践、风险提示
5. 确保扩展内容与原回答保持连贯性和一致性

已有回答：
{expanded_answer}

请继续扩展以上内容，使总字数达到{min_words}字以上。
"""

            try:
                # Use LLM to expand the answer
                expansion_response = await self.llm.ainvoke(
                    expansion_context,
                    config={"max_tokens": 4000}
                )

                # Extract the expanded content
                if hasattr(expansion_response, 'content'):
                    expanded_content = expansion_response.content
                else:
                    expanded_content = str(expansion_response)

                # Combine original and expanded content
                expanded_answer = f"{expanded_answer}\n\n{expanded_content}"
                current_count = self._count_chinese_words(expanded_answer)

                logger.info(f"Expansion attempt {expansion_attempts}: now has {current_count} words")

            except Exception as e:
                logger.error(f"Error during expansion attempt {expansion_attempts}: {e}")
                break

        # Add word count indicator
        if current_count >= min_words:
            expanded_answer = f"{expanded_answer}\n\n---\n📊 **字数统计**: {current_count}字 (满足{min_words}字要求)"
        else:
            expanded_answer = f"{expanded_answer}\n\n---\n⚠️ **字数统计**: {current_count}字 (目标{min_words}字)"

        return expanded_answer

    def _ensure_minimum_word_count_sync(
        self,
        answer: str,
        sources: List[Dict[str, Any]],
        min_words: int = None
    ) -> str:
        """Synchronous version of word count expansion"""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self._ensure_minimum_word_count(answer, sources, min_words)
            )
        finally:
            loop.close()


class ComplianceRAGChainFactory:
    """
    Factory for creating RAG chains with different configurations
    """
    
    @staticmethod
    def create_simple_chain(vector_store: Any) -> ComplianceRAGChain:
        """Create a simple RAG chain without enhancements"""
        return ComplianceRAGChain(
            vector_store=vector_store,
            use_reranking=False,
            use_multi_query=False
        )
    
    @staticmethod
    def create_enhanced_chain(vector_store: Any) -> ComplianceRAGChain:
        """Create an enhanced RAG chain with all features"""
        return ComplianceRAGChain(
            vector_store=vector_store,
            use_reranking=True,
            use_multi_query=True,
            k=10,
            rerank_k=5
        )
    
    @staticmethod
    def create_streaming_chain(
        vector_store: Any,
        callback_handler: Optional[AsyncCallbackHandler] = None
    ) -> ComplianceRAGChain:
        """Create a RAG chain optimized for streaming"""
        callbacks = [callback_handler] if callback_handler else []
        
        llm = ChatOpenAI(
            model_name=settings.LLM_MODEL,
            openai_api_key=settings.LLM_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            streaming=True,
            callbacks=callbacks
        )
        
        return ComplianceRAGChain(
            llm=llm,
            vector_store=vector_store,
            use_reranking=False,  # Disable for faster streaming
            use_multi_query=False  # Disable for faster streaming
        )