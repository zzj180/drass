"""
Unit tests for the compliance RAG chain
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import List, Dict, Any

from app.chains.compliance_rag_chain import (
    ComplianceRAGChain,
    ComplianceRAGChainFactory,
    StreamingCallbackHandler
)
from app.chains.prompts import PromptSelector


class TestComplianceRAGChain:
    """Test cases for ComplianceRAGChain"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM"""
        llm = MagicMock()
        llm.astream = AsyncMock()
        llm.ainvoke = AsyncMock()
        return llm
    
    @pytest.fixture
    def mock_embeddings(self):
        """Create mock embeddings"""
        return MagicMock()
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store"""
        vector_store = MagicMock()
        retriever = MagicMock()
        retriever.aget_relevant_documents = AsyncMock(return_value=[])
        vector_store.as_retriever.return_value = retriever
        return vector_store
    
    @pytest.fixture
    def rag_chain(self, mock_llm, mock_embeddings, mock_vector_store):
        """Create RAG chain instance"""
        return ComplianceRAGChain(
            llm=mock_llm,
            embeddings=mock_embeddings,
            vector_store=mock_vector_store,
            use_reranking=False,
            use_multi_query=False
        )
    
    @pytest.mark.asyncio
    async def test_ask_simple_question(self, rag_chain):
        """Test asking a simple question without history"""
        # Setup mock response
        rag_chain.qa_chain = MagicMock()
        rag_chain.qa_chain.ainvoke = AsyncMock(return_value={
            "answer": "Test answer",
            "context": []
        })
        
        # Ask question
        response = await rag_chain.ask("What is compliance?")
        
        # Verify
        assert response["answer"] == "Test answer"
        assert response["sources"] == []
        assert response["context_count"] == 0
    
    @pytest.mark.asyncio
    async def test_ask_with_chat_history(self, rag_chain):
        """Test asking with chat history"""
        # Setup mock response
        rag_chain.conversational_chain = MagicMock()
        rag_chain.conversational_chain.ainvoke = AsyncMock(return_value={
            "answer": "Answer with context",
            "context": []
        })
        
        # Ask with history
        chat_history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
        ]
        
        response = await rag_chain.ask(
            "Follow-up question",
            chat_history=chat_history
        )
        
        # Verify
        assert response["answer"] == "Answer with context"
        rag_chain.conversational_chain.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_streaming_response(self, rag_chain):
        """Test streaming response"""
        # Setup mock streaming
        async def mock_stream(*args, **kwargs):
            for token in ["Hello", " ", "world"]:
                yield {"answer": token}
        
        rag_chain.qa_chain = MagicMock()
        rag_chain.qa_chain.astream = mock_stream
        
        # Collect streaming response
        tokens = []
        async for chunk in rag_chain.qa_chain.astream({"input": "test"}):
            tokens.append(chunk["answer"])
        
        # Verify
        assert tokens == ["Hello", " ", "world"]
    
    def test_format_chat_history(self, rag_chain):
        """Test chat history formatting"""
        chat_history = [
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant message"},
            {"role": "system", "content": "System message"}
        ]
        
        formatted = rag_chain._format_chat_history(chat_history)
        
        assert len(formatted) == 3
        assert formatted[0].content == "User message"
        assert formatted[1].content == "Assistant message"
        assert formatted[2].content == "System message"
    
    def test_format_response(self, rag_chain):
        """Test response formatting"""
        # Test with dict response
        response = {
            "answer": "Test answer",
            "context": [
                MagicMock(
                    page_content="Document content",
                    metadata={"source": "test.pdf"}
                )
            ]
        }
        
        formatted = rag_chain._format_response(response)
        
        assert formatted["answer"] == "Test answer"
        assert len(formatted["sources"]) == 1
        assert formatted["sources"][0]["metadata"]["source"] == "test.pdf"
        assert formatted["context_count"] == 1
    
    def test_update_vector_store(self, rag_chain, mock_vector_store):
        """Test updating vector store"""
        new_vector_store = MagicMock()
        new_retriever = MagicMock()
        new_vector_store.as_retriever.return_value = new_retriever
        
        rag_chain.update_vector_store(new_vector_store)
        
        assert rag_chain.vector_store == new_vector_store
        assert rag_chain.retriever is not None
    
    def test_clear_memory(self, rag_chain):
        """Test clearing memory"""
        rag_chain.memory = MagicMock()
        rag_chain.clear_memory()
        rag_chain.memory.clear.assert_called_once()


class TestComplianceRAGChainFactory:
    """Test cases for ComplianceRAGChainFactory"""
    
    def test_create_simple_chain(self):
        """Test creating simple chain"""
        mock_vector_store = MagicMock()
        
        with patch('app.chains.compliance_rag_chain.ComplianceRAGChain') as MockChain:
            chain = ComplianceRAGChainFactory.create_simple_chain(mock_vector_store)
            
            MockChain.assert_called_with(
                vector_store=mock_vector_store,
                use_reranking=False,
                use_multi_query=False
            )
    
    def test_create_enhanced_chain(self):
        """Test creating enhanced chain"""
        mock_vector_store = MagicMock()
        
        with patch('app.chains.compliance_rag_chain.ComplianceRAGChain') as MockChain:
            chain = ComplianceRAGChainFactory.create_enhanced_chain(mock_vector_store)
            
            MockChain.assert_called_with(
                vector_store=mock_vector_store,
                use_reranking=True,
                use_multi_query=True,
                k=10,
                rerank_k=5
            )
    
    def test_create_streaming_chain(self):
        """Test creating streaming chain"""
        mock_vector_store = MagicMock()
        mock_callback = AsyncMock()
        
        with patch('app.chains.compliance_rag_chain.ChatOpenAI') as MockLLM:
            with patch('app.chains.compliance_rag_chain.ComplianceRAGChain') as MockChain:
                chain = ComplianceRAGChainFactory.create_streaming_chain(
                    mock_vector_store,
                    mock_callback
                )
                
                # Verify LLM created with streaming
                MockLLM.assert_called()
                call_kwargs = MockLLM.call_args.kwargs
                assert call_kwargs["streaming"] is True
                assert mock_callback in call_kwargs["callbacks"]


class TestStreamingCallbackHandler:
    """Test cases for StreamingCallbackHandler"""
    
    @pytest.mark.asyncio
    async def test_on_llm_new_token(self):
        """Test handling new token"""
        queue = asyncio.Queue()
        handler = StreamingCallbackHandler(queue)
        
        await handler.on_llm_new_token("test_token")
        
        item = await queue.get()
        assert item["type"] == "token"
        assert item["content"] == "test_token"
    
    @pytest.mark.asyncio
    async def test_on_llm_end(self):
        """Test handling LLM end"""
        queue = asyncio.Queue()
        handler = StreamingCallbackHandler(queue)
        
        await handler.on_llm_end(None)
        
        item = await queue.get()
        assert item["type"] == "end"
    
    @pytest.mark.asyncio
    async def test_on_llm_error(self):
        """Test handling LLM error"""
        queue = asyncio.Queue()
        handler = StreamingCallbackHandler(queue)
        
        error = Exception("Test error")
        await handler.on_llm_error(error)
        
        item = await queue.get()
        assert item["type"] == "error"
        assert item["error"] == "Test error"


class TestPromptSelector:
    """Test cases for PromptSelector"""
    
    def test_detect_risk_query(self):
        """Test detecting risk-related query"""
        questions = [
            "What are the compliance risks?",
            "Identify potential threats",
            "Assess vulnerability exposure"
        ]
        
        for question in questions:
            query_type = PromptSelector.detect_query_type(question)
            assert query_type == "risk"
    
    def test_detect_implementation_query(self):
        """Test detecting implementation query"""
        questions = [
            "How to implement GDPR compliance?",
            "Deploy the security measures",
            "Setup audit logging"
        ]
        
        for question in questions:
            query_type = PromptSelector.detect_query_type(question)
            assert query_type == "implementation"
    
    def test_detect_analysis_query(self):
        """Test detecting analysis query"""
        questions = [
            "Analyze the compliance gaps",
            "Evaluate current controls",
            "Review the assessment results"
        ]
        
        for question in questions:
            query_type = PromptSelector.detect_query_type(question)
            assert query_type == "analysis"
    
    def test_detect_checklist_query(self):
        """Test detecting checklist query"""
        questions = [
            "Create a compliance checklist",
            "List the required steps",
            "What tasks need to be done?"
        ]
        
        for question in questions:
            query_type = PromptSelector.detect_query_type(question)
            assert query_type == "checklist"
    
    def test_detect_general_query(self):
        """Test detecting general query"""
        question = "What is SOC 2 compliance?"
        query_type = PromptSelector.detect_query_type(question)
        assert query_type == "general"
    
    def test_select_prompt(self):
        """Test prompt selection"""
        from app.chains.prompts import (
            COMPLIANCE_QA_PROMPT,
            RISK_ASSESSMENT_PROMPT
        )
        
        # Test general prompt
        prompt = PromptSelector.select_prompt("general")
        assert prompt == COMPLIANCE_QA_PROMPT
        
        # Test risk prompt
        prompt = PromptSelector.select_prompt("risk")
        assert prompt == RISK_ASSESSMENT_PROMPT
        
        # Test unknown type (should default to general)
        prompt = PromptSelector.select_prompt("unknown")
        assert prompt == COMPLIANCE_QA_PROMPT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])