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
        self.collection_name = getattr(settings, 'VECTOR_STORE_COLLECTION', 'compliance_docs')
        self._initialized = False
    
    async def initialize(self):
        """Initialize the vector store (async for lifespan)"""
        if not self._initialized:
            self._initialize_store()
            self._initialized = True
    
    def _initialize_store(self):
        """Initialize the vector store based on configuration"""
        try:
            vector_store_type = getattr(settings, 'VECTOR_STORE_TYPE', 'chromadb').lower()
            if vector_store_type in ["chroma", "chromadb"]:
                from langchain_community.vectorstores import Chroma
                from langchain_community.embeddings import HuggingFaceEmbeddings
                import os
                import shutil

                # Use HuggingFace embeddings as fallback
                embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )

                # Check if we should use ChromaDB server or local persistence
                chroma_server_host = getattr(settings, 'CHROMA_SERVER_HOST', 'localhost')
                chroma_server_port = getattr(settings, 'CHROMA_SERVER_PORT', 8005)
                
                # Try to connect to ChromaDB server first
                try:
                    import chromadb
                    client = chromadb.HttpClient(
                        host=chroma_server_host,
                        port=chroma_server_port
                    )
                    # Test connection
                    client.heartbeat()
                    logger.info(f"Connected to ChromaDB server at {chroma_server_host}:{chroma_server_port}")
                    
                    # Use the server client directly
                    self.vector_store = Chroma(
                        collection_name=self.collection_name,
                        embedding_function=embeddings,
                        client=client
                    )
                    logger.info(f"Initialized ChromaDB vector store with server client")
                except Exception as server_error:
                    logger.warning(f"ChromaDB server not available: {server_error}")
                    logger.info("Falling back to local persistence")
                    
                    persist_dir = getattr(settings, 'CHROMA_PERSIST_DIRECTORY', './data/chroma')
                    
                    # Handle corrupted ChromaDB - clean and retry
                    try:
                        self.vector_store = Chroma(
                            collection_name=self.collection_name,
                            embedding_function=embeddings,
                            persist_directory=persist_dir
                        )
                        logger.info(f"Initialized ChromaDB vector store at {persist_dir}")
                    except Exception as db_error:
                        if "no such column" in str(db_error) or "database" in str(db_error).lower():
                            logger.warning(f"ChromaDB appears corrupted: {db_error}")
                            logger.info("Attempting to clean and reinitialize ChromaDB...")

                            # Remove corrupted database
                            if os.path.exists(persist_dir):
                                shutil.rmtree(persist_dir, ignore_errors=True)
                                logger.info(f"Removed corrupted ChromaDB at {persist_dir}")

                            # Create fresh directory
                            os.makedirs(persist_dir, exist_ok=True)

                            # Try again with fresh database
                            self.vector_store = Chroma(
                                collection_name=self.collection_name,
                                embedding_function=embeddings,
                                persist_directory=persist_dir
                            )
                            logger.info(f"Successfully reinitialized ChromaDB vector store at {persist_dir}")
                        else:
                            raise db_error
            else:
                logger.warning(f"Unsupported vector store type: {vector_store_type}")

        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            # Don't fail completely - allow API to start without vector store
            logger.warning("API will start without vector store functionality")
    
    async def add_documents(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Add documents to the vector store"""
        try:
            if not self.vector_store:
                logger.error("Vector store not initialized")
                return []
            
            # Convert to LangChain Document format
            from langchain.schema import Document
            docs = [
                Document(
                    page_content=text,
                    metadata=metadata if metadata else {}
                )
                for text, metadata in zip(texts, metadatas or [{} for _ in texts])
            ]
            
            # Add to vector store and get IDs
            ids = self.vector_store.add_documents(docs)
            logger.info(f"Added {len(texts)} documents to vector store")
            return ids
            
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
                "type": getattr(settings, 'VECTOR_STORE_TYPE', 'chromadb'),
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