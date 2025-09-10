"""
Search-related tools for the compliance agent
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge base search"""
    query: str = Field(..., description="Search query")
    knowledge_base_id: Optional[str] = Field(None, description="Specific knowledge base to search")
    limit: int = Field(5, description="Maximum number of results")


class WebSearchInput(BaseModel):
    """Input schema for web search"""
    query: str = Field(..., description="Search query")
    domain_filter: Optional[str] = Field(None, description="Limit search to specific domain")
    limit: int = Field(5, description="Maximum number of results")


class SemanticSearchInput(BaseModel):
    """Input schema for semantic search"""
    query: str = Field(..., description="Search query")
    similarity_threshold: float = Field(0.7, description="Minimum similarity score")
    limit: int = Field(5, description="Maximum number of results")


class KnowledgeSearchTool:
    """Tool for searching knowledge bases"""
    
    def __init__(self):
        self.name = "knowledge_search"
        self.description = """Search the compliance knowledge base for relevant information.
        Use this to find answers from previously indexed compliance documents and regulations.
        Input should be a search query and optional knowledge base ID."""
    
    async def _run(self, **kwargs) -> str:
        """Execute knowledge base search"""
        try:
            query = kwargs.get("query", "")
            knowledge_base_id = kwargs.get("knowledge_base_id")
            limit = kwargs.get("limit", 5)
            
            # Search knowledge base (mock)
            results = await self._search_knowledge(query, knowledge_base_id, limit)
            
            if not results:
                return "No relevant information found in the knowledge base."
            
            # Format results
            formatted = []
            for idx, result in enumerate(results, 1):
                formatted.append(
                    f"{idx}. [{result['score']:.2f}] {result['content'][:200]}...\n"
                    f"   Source: {result['source']}"
                )
            
            return f"Knowledge Base Search Results:\n\n" + "\n\n".join(formatted)
            
        except Exception as e:
            logger.error(f"Knowledge search error: {str(e)}")
            return f"Error searching knowledge base: {str(e)}"
    
    async def _search_knowledge(
        self,
        query: str,
        knowledge_base_id: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Mock knowledge base search"""
        # In production, integrate with vector store
        mock_results = [
            {
                "content": "GDPR Article 32 requires implementation of appropriate technical and organizational measures to ensure security of processing",
                "source": "GDPR Regulation",
                "score": 0.92
            },
            {
                "content": "Data controllers must conduct Data Protection Impact Assessments (DPIA) for high-risk processing activities",
                "source": "GDPR Article 35",
                "score": 0.88
            },
            {
                "content": "Organizations must appoint a Data Protection Officer if they process large amounts of personal data",
                "source": "GDPR Article 37",
                "score": 0.85
            }
        ]
        
        # Filter by query relevance (mock)
        relevant_results = []
        for result in mock_results:
            if query.lower() in result["content"].lower():
                relevant_results.append(result)
        
        return relevant_results[:limit] if relevant_results else mock_results[:limit]
    
    def as_tool(self) -> Tool:
        """Convert to LangChain tool"""
        return Tool(
            name=self.name,
            description=self.description,
            func=lambda **kwargs: self._run(**kwargs),
            args_schema=KnowledgeSearchInput
        )


class WebSearchTool:
    """Tool for searching the web"""
    
    def __init__(self):
        self.name = "web_search"
        self.description = """Search the web for current compliance information and regulations.
        Use this to find the latest regulatory updates, news, and external resources.
        Input should be a search query and optional domain filter."""
    
    async def _run(self, **kwargs) -> str:
        """Execute web search"""
        try:
            query = kwargs.get("query", "")
            domain_filter = kwargs.get("domain_filter")
            limit = kwargs.get("limit", 5)
            
            # Perform web search (mock)
            results = await self._search_web(query, domain_filter, limit)
            
            if not results:
                return "No relevant web results found."
            
            # Format results
            formatted = []
            for idx, result in enumerate(results, 1):
                formatted.append(
                    f"{idx}. {result['title']}\n"
                    f"   URL: {result['url']}\n"
                    f"   {result['snippet']}"
                )
            
            return f"Web Search Results:\n\n" + "\n\n".join(formatted)
            
        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            return f"Error searching web: {str(e)}"
    
    async def _search_web(
        self,
        query: str,
        domain_filter: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Mock web search"""
        # In production, integrate with search API
        mock_results = [
            {
                "title": "Latest GDPR Enforcement Actions - 2024",
                "url": "https://example.com/gdpr-enforcement",
                "snippet": "Recent GDPR enforcement actions show increased focus on data breach notifications..."
            },
            {
                "title": "SOC 2 Compliance Guide for SaaS Companies",
                "url": "https://example.com/soc2-guide",
                "snippet": "Comprehensive guide to achieving SOC 2 Type II certification for SaaS providers..."
            },
            {
                "title": "ISO 27001:2022 Changes and Updates",
                "url": "https://example.com/iso27001-updates",
                "snippet": "Key changes in the latest ISO 27001:2022 standard including new controls..."
            }
        ]
        
        # Apply domain filter if specified
        if domain_filter:
            mock_results = [
                r for r in mock_results
                if domain_filter in r["url"]
            ]
        
        return mock_results[:limit]
    
    def as_tool(self) -> Tool:
        """Convert to LangChain tool"""
        return Tool(
            name=self.name,
            description=self.description,
            func=lambda **kwargs: self._run(**kwargs),
            args_schema=WebSearchInput
        )


class SemanticSearchTool:
    """Tool for semantic search across all sources"""
    
    def __init__(self):
        self.name = "semantic_search"
        self.description = """Perform semantic search across all available sources.
        Use this for complex queries that require understanding context and meaning.
        Input should be a natural language query."""
    
    async def _run(self, **kwargs) -> str:
        """Execute semantic search"""
        try:
            query = kwargs.get("query", "")
            similarity_threshold = kwargs.get("similarity_threshold", 0.7)
            limit = kwargs.get("limit", 5)
            
            # Perform semantic search (mock)
            results = await self._semantic_search(query, similarity_threshold, limit)
            
            if not results:
                return "No semantically similar content found."
            
            # Format results
            formatted = []
            for idx, result in enumerate(results, 1):
                formatted.append(
                    f"{idx}. Similarity: {result['similarity']:.2f}\n"
                    f"   Type: {result['type']}\n"
                    f"   Content: {result['content'][:200]}...\n"
                    f"   Context: {result['context']}"
                )
            
            return f"Semantic Search Results:\n\n" + "\n\n".join(formatted)
            
        except Exception as e:
            logger.error(f"Semantic search error: {str(e)}")
            return f"Error performing semantic search: {str(e)}"
    
    async def _semantic_search(
        self,
        query: str,
        similarity_threshold: float,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Mock semantic search"""
        # In production, use embeddings and vector search
        mock_results = [
            {
                "content": "Organizations must implement privacy by design principles in all new systems and processes",
                "similarity": 0.89,
                "type": "regulation",
                "context": "GDPR compliance requirement"
            },
            {
                "content": "Risk assessments should be conducted annually or when significant changes occur",
                "similarity": 0.85,
                "type": "best_practice",
                "context": "ISO 27001 risk management"
            },
            {
                "content": "Data breach response procedures must include notification within 72 hours",
                "similarity": 0.82,
                "type": "requirement",
                "context": "GDPR breach notification"
            },
            {
                "content": "Access controls should follow the principle of least privilege",
                "similarity": 0.78,
                "type": "control",
                "context": "SOC 2 security principle"
            }
        ]
        
        # Filter by similarity threshold
        filtered_results = [
            r for r in mock_results
            if r["similarity"] >= similarity_threshold
        ]
        
        # Sort by similarity score
        filtered_results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return filtered_results[:limit]
    
    def as_tool(self) -> Tool:
        """Convert to LangChain tool"""
        return Tool(
            name=self.name,
            description=self.description,
            func=lambda **kwargs: self._run(**kwargs),
            args_schema=SemanticSearchInput
        )