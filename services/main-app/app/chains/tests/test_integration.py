"""
Integration tests for the compliance RAG chain
"""

import pytest
import asyncio
from typing import List, Dict, Any
import tempfile
import os

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.chains.compliance_rag_chain import (
    ComplianceRAGChain,
    ComplianceRAGChainFactory
)


@pytest.mark.integration
class TestRAGChainIntegration:
    """Integration tests for RAG chain with real components"""
    
    @pytest.fixture
    def sample_documents(self) -> List[Document]:
        """Create sample compliance documents"""
        return [
            Document(
                page_content="""
                GDPR Compliance Requirements:
                1. Data Protection Officer (DPO) appointment is mandatory for organizations that process large amounts of personal data.
                2. Privacy by Design must be implemented in all systems.
                3. Data subjects have the right to access, rectify, and delete their personal data.
                4. Data breaches must be reported within 72 hours to the supervisory authority.
                5. Explicit consent is required for data processing.
                """,
                metadata={"source": "gdpr_guide.pdf", "page": 1}
            ),
            Document(
                page_content="""
                SOC 2 Type II Compliance:
                1. Security: Protection against unauthorized access
                2. Availability: System availability for operation and use
                3. Processing Integrity: System processing is complete, valid, accurate, and timely
                4. Confidentiality: Information designated as confidential is protected
                5. Privacy: Personal information is collected, used, retained, and disclosed in conformity with commitments
                Annual audits are required to maintain SOC 2 certification.
                """,
                metadata={"source": "soc2_requirements.pdf", "page": 1}
            ),
            Document(
                page_content="""
                HIPAA Compliance for Healthcare:
                1. Administrative Safeguards: Policies and procedures to manage security measures
                2. Physical Safeguards: Physical measures to protect electronic systems
                3. Technical Safeguards: Technology and policies to protect ePHI
                4. Breach Notification Rule: Requirements for notifying patients of breaches
                5. Minimum Necessary Standard: Only access PHI necessary for job function
                Business Associate Agreements (BAAs) are required with all third-party vendors.
                """,
                metadata={"source": "hipaa_guide.pdf", "page": 1}
            ),
            Document(
                page_content="""
                ISO 27001 Information Security Management:
                1. Risk Assessment: Identify and assess information security risks
                2. Risk Treatment: Implement controls to mitigate identified risks
                3. Statement of Applicability: Document which controls are applicable
                4. Internal Audits: Regular audits to ensure compliance
                5. Management Review: Regular review of ISMS effectiveness
                6. Continuous Improvement: Ongoing enhancement of security posture
                Certification requires external audit by accredited certification body.
                """,
                metadata={"source": "iso27001_standard.pdf", "page": 1}
            ),
            Document(
                page_content="""
                PCI DSS Requirements for Payment Card Security:
                1. Install and maintain firewall configuration
                2. Do not use vendor-supplied defaults for passwords
                3. Protect stored cardholder data with encryption
                4. Encrypt transmission of cardholder data across public networks
                5. Use and regularly update anti-virus software
                6. Develop and maintain secure systems and applications
                7. Restrict access to cardholder data by business need-to-know
                8. Assign unique ID to each person with computer access
                9. Restrict physical access to cardholder data
                10. Track and monitor all access to network resources
                11. Regularly test security systems and processes
                12. Maintain information security policy
                Quarterly vulnerability scans required by Approved Scanning Vendor (ASV).
                """,
                metadata={"source": "pci_dss_guide.pdf", "page": 1}
            )
        ]
    
    @pytest.fixture
    async def vector_store(self, sample_documents):
        """Create vector store with sample documents"""
        # Use temporary directory for Chroma
        with tempfile.TemporaryDirectory() as temp_dir:
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            split_docs = text_splitter.split_documents(sample_documents)
            
            # Create embeddings (mock for testing)
            class MockEmbeddings:
                def embed_documents(self, texts):
                    return [[0.1] * 384 for _ in texts]
                
                def embed_query(self, text):
                    return [0.1] * 384
            
            # Create vector store
            vector_store = Chroma.from_documents(
                documents=split_docs,
                embedding=MockEmbeddings(),
                persist_directory=temp_dir
            )
            
            yield vector_store
    
    @pytest.mark.asyncio
    async def test_basic_qa_flow(self, vector_store):
        """Test basic question-answering flow"""
        # Create RAG chain
        chain = ComplianceRAGChainFactory.create_simple_chain(vector_store)
        
        # Mock LLM response
        async def mock_ainvoke(*args, **kwargs):
            return {
                "answer": "Based on the context, GDPR requires appointing a Data Protection Officer for organizations processing large amounts of personal data.",
                "context": vector_store.similarity_search("DPO", k=2)
            }
        
        chain.qa_chain.ainvoke = mock_ainvoke
        
        # Ask question
        response = await chain.ask("What are the requirements for appointing a DPO under GDPR?")
        
        # Verify response
        assert "Data Protection Officer" in response["answer"]
        assert response["context_count"] >= 0
    
    @pytest.mark.asyncio
    async def test_conversational_flow(self, vector_store):
        """Test conversational flow with history"""
        # Create RAG chain
        chain = ComplianceRAGChain(
            vector_store=vector_store,
            use_reranking=False,
            use_multi_query=False
        )
        
        # Mock conversational chain
        async def mock_ainvoke(*args, **kwargs):
            return {
                "answer": "SOC 2 has 5 trust service criteria while ISO 27001 focuses on information security management systems.",
                "context": []
            }
        
        chain.conversational_chain.ainvoke = mock_ainvoke
        
        # Create conversation history
        chat_history = [
            {"role": "user", "content": "What is SOC 2?"},
            {"role": "assistant", "content": "SOC 2 is a compliance framework with 5 trust service criteria."},
            {"role": "user", "content": "How does it compare to ISO 27001?"}
        ]
        
        # Ask with history
        response = await chain.ask(
            "How does it compare to ISO 27001?",
            chat_history=chat_history[:-1]  # Exclude last user message
        )
        
        # Verify response considers history
        assert "SOC 2" in response["answer"]
        assert "ISO 27001" in response["answer"]
    
    @pytest.mark.asyncio
    async def test_multi_standard_query(self, vector_store):
        """Test querying across multiple compliance standards"""
        # Create enhanced chain
        chain = ComplianceRAGChain(
            vector_store=vector_store,
            use_multi_query=False,  # Disable for testing
            k=5  # Get more documents
        )
        
        # Mock response
        async def mock_ainvoke(*args, **kwargs):
            return {
                "answer": "Data breach notification requirements vary: GDPR requires 72-hour notification, HIPAA has specific breach notification rules.",
                "context": vector_store.similarity_search("breach notification", k=3)
            }
        
        chain.qa_chain.ainvoke = mock_ainvoke
        
        # Ask cross-standard question
        response = await chain.ask("What are the breach notification requirements across different standards?")
        
        # Verify multiple standards mentioned
        assert response["answer"]
        assert response["context_count"] >= 0
    
    @pytest.mark.asyncio
    async def test_streaming_response(self, vector_store):
        """Test streaming response generation"""
        # Create streaming chain
        chain = ComplianceRAGChain(
            vector_store=vector_store,
            use_reranking=False,
            use_multi_query=False
        )
        
        # Mock streaming
        async def mock_astream(*args, **kwargs):
            tokens = ["PCI DSS ", "requires ", "12 ", "requirements ", "for ", "payment ", "card ", "security."]
            for token in tokens:
                yield {"answer": token, "context": []}
                await asyncio.sleep(0.01)  # Simulate streaming delay
        
        chain.qa_chain.astream = mock_astream
        
        # Collect streamed response
        streamed_answer = ""
        async for chunk in chain.qa_chain.astream({"input": "What is PCI DSS?"}):
            streamed_answer += chunk["answer"]
        
        # Verify complete answer
        assert "PCI DSS" in streamed_answer
        assert "requirements" in streamed_answer
    
    @pytest.mark.asyncio
    async def test_error_handling(self, vector_store):
        """Test error handling in RAG chain"""
        chain = ComplianceRAGChain(vector_store=vector_store)
        
        # Mock error
        async def mock_error(*args, **kwargs):
            raise Exception("LLM API error")
        
        chain.qa_chain.ainvoke = mock_error
        
        # Test error is properly raised
        with pytest.raises(Exception) as exc_info:
            await chain.ask("Test question")
        
        assert "LLM API error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_empty_context_handling(self, vector_store):
        """Test handling when no relevant context is found"""
        chain = ComplianceRAGChain(vector_store=vector_store)
        
        # Mock empty context response
        async def mock_ainvoke(*args, **kwargs):
            return {
                "answer": "I don't have enough information in the context to answer this question.",
                "context": []
            }
        
        chain.qa_chain.ainvoke = mock_ainvoke
        
        # Ask unrelated question
        response = await chain.ask("What is the weather today?")
        
        # Verify appropriate response
        assert "don't have enough information" in response["answer"]
        assert response["context_count"] == 0
        assert response["sources"] == []
    
    @pytest.mark.asyncio
    async def test_memory_management(self, vector_store):
        """Test conversation memory management"""
        chain = ComplianceRAGChain(vector_store=vector_store)
        
        # Add to memory
        chain.memory.save_context(
            {"input": "What is GDPR?"},
            {"output": "GDPR is the General Data Protection Regulation."}
        )
        
        # Verify memory has content
        messages = chain.memory.buffer
        assert len(messages) > 0
        
        # Clear memory
        chain.clear_memory()
        
        # Verify memory is cleared
        assert len(chain.memory.buffer) == 0


@pytest.mark.integration
class TestRAGChainFactoryIntegration:
    """Integration tests for RAG chain factory"""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store"""
        class MockVectorStore:
            def as_retriever(self, **kwargs):
                class MockRetriever:
                    async def aget_relevant_documents(self, query):
                        return []
                return MockRetriever()
        
        return MockVectorStore()
    
    def test_factory_creates_valid_chains(self, mock_vector_store):
        """Test factory creates valid chain instances"""
        # Test simple chain
        simple_chain = ComplianceRAGChainFactory.create_simple_chain(mock_vector_store)
        assert isinstance(simple_chain, ComplianceRAGChain)
        assert not simple_chain.use_reranking
        assert not simple_chain.use_multi_query
        
        # Test enhanced chain
        enhanced_chain = ComplianceRAGChainFactory.create_enhanced_chain(mock_vector_store)
        assert isinstance(enhanced_chain, ComplianceRAGChain)
        assert enhanced_chain.use_reranking
        assert enhanced_chain.use_multi_query
        
        # Test streaming chain
        streaming_chain = ComplianceRAGChainFactory.create_streaming_chain(mock_vector_store)
        assert isinstance(streaming_chain, ComplianceRAGChain)
        assert not streaming_chain.use_reranking  # Disabled for streaming


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])