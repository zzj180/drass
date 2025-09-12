"""
Vector store service for managing document embeddings
"""

import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector store operations"""
    
    def __init__(self):
        self.vector_store = None
        self.collection_name = "compliance_docs"
        self._initialized = False
    
    async def initialize(self):
        """Initialize the vector store (async for lifespan)"""
        if not self._initialized:
            self._initialize_store()
            self._initialized = True
    
    def _initialize_store(self):
        """Initialize the vector store based on configuration"""
        try:
            vector_store_type = getattr(settings, 'vector_store_type', 'chroma')
            if vector_store_type == "chroma":
                from langchain.vectorstores import Chroma
                from langchain.embeddings import HuggingFaceEmbeddings
                
                # Use HuggingFace embeddings as fallback
                embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
                
                persist_dir = getattr(settings, 'chroma_persist_directory', './data/chroma')
                self.vector_store = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=embeddings,
                    persist_directory=persist_dir
                )
                logger.info(f"Initialized ChromaDB vector store at {persist_dir}")
            else:
                logger.warning(f"Unsupported vector store type: {settings.vector_store_type}")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector store"""
        try:
            if not self.vector_store:
                logger.error("Vector store not initialized")
                return False
            
            # Convert documents to LangChain format
            from langchain.schema import Document
            docs = [
                Document(
                    page_content=doc.get("content", ""),
                    metadata=doc.get("metadata", {})
                )
                for doc in documents
            ]
            
            # Add to vector store
            self.vector_store.add_documents(docs)
            logger.info(f"Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    async def search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            if not self.vector_store:
                logger.error("Vector store not initialized")
                return []
            
            # Perform similarity search
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter
            )
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def delete_collection(self) -> bool:
        """Delete the entire collection"""
        try:
            if self.vector_store and hasattr(self.vector_store, "_client"):
                self.vector_store._client.delete_collection(name=self.collection_name)
                logger.info(f"Deleted collection: {self.collection_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        try:
            if not self.vector_store:
                return {"status": "not_initialized"}
            
            # Get collection stats if available
            stats = {
                "status": "initialized",
                "type": settings.vector_store_type,
                "collection": self.collection_name
            }
            
            if hasattr(self.vector_store, "_collection"):
                collection = self.vector_store._collection
                stats["document_count"] = collection.count()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"status": "error", "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the vector store"""
        return {
            "status": "healthy" if self._initialized else "not_initialized",
            "type": getattr(settings, 'vector_store_type', 'chroma')
        }
    
    async def close(self):
        """Close the vector store connection"""
        logger.info("Closing vector store connection")
        self._initialized = False


# Singleton instance
vector_store_service = VectorStoreService()