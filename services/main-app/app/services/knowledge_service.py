"""
Knowledge Base Service
Handles knowledge base operations including creation, management, and search
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.core.logging import get_logger
from app.services.vector_store import vector_store_service
from app.services.embedding_service import embedding_service

logger = get_logger(__name__)


class KnowledgeService:
    """Knowledge base service for managing documents and search"""
    
    def __init__(self):
        self.knowledge_bases = {}  # In-memory storage for demo
        self.knowledge_sources = {}  # In-memory storage for demo
    
    async def get_user_knowledge_bases(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all knowledge bases for a user"""
        try:
            # For demo purposes, return a default knowledge base
            default_base = {
                "id": "default-compliance-base",
                "name": "数据合规知识库",
                "description": "包含数据保护法规和合规指南的知识库",
                "source_count": 0,
                "total_chunks": 0,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            return [default_base]
        except Exception as e:
            logger.error(f"Error getting knowledge bases: {e}")
            return []
    
    async def create_knowledge_base(self, user_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new knowledge base"""
        try:
            base_id = str(uuid.uuid4())
            base = {
                "id": base_id,
                "name": name,
                "description": description,
                "source_count": 0,
                "total_chunks": 0,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            self.knowledge_bases[base_id] = base
            return base
        except Exception as e:
            logger.error(f"Error creating knowledge base: {e}")
            raise
    
    async def get_knowledge_base(self, base_id: str, user_id: str) -> Dict[str, Any]:
        """Get a specific knowledge base"""
        try:
            if base_id in self.knowledge_bases:
                return self.knowledge_bases[base_id]
            else:
                # Return default base if not found
                return {
                    "id": "default-compliance-base",
                    "name": "数据合规知识库",
                    "description": "包含数据保护法规和合规指南的知识库",
                    "source_count": 0,
                    "total_chunks": 0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
        except Exception as e:
            logger.error(f"Error getting knowledge base: {e}")
            raise
    
    async def delete_knowledge_base(self, base_id: str, user_id: str) -> bool:
        """Delete a knowledge base"""
        try:
            if base_id in self.knowledge_bases:
                del self.knowledge_bases[base_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting knowledge base: {e}")
            return False
    
    async def get_knowledge_sources(self, base_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all sources in a knowledge base"""
        try:
            # For demo purposes, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting knowledge sources: {e}")
            return []
    
    async def add_document_source(self, base_id: str, user_id: str, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Add a document to the knowledge base"""
        try:
            source_id = str(uuid.uuid4())
            source = {
                "id": source_id,
                "knowledge_base_id": base_id,
                "name": filename,
                "type": "file",
                "status": "processed",
                "metadata": {"filename": filename},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            self.knowledge_sources[source_id] = source
            return source
        except Exception as e:
            logger.error(f"Error adding document source: {e}")
            raise
    
    async def add_text_source(self, base_id: str, user_id: str, name: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add text content to the knowledge base"""
        try:
            source_id = str(uuid.uuid4())
            source = {
                "id": source_id,
                "knowledge_base_id": base_id,
                "name": name,
                "type": "text",
                "status": "processed",
                "metadata": metadata or {},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            self.knowledge_sources[source_id] = source
            return source
        except Exception as e:
            logger.error(f"Error adding text source: {e}")
            raise
    
    async def add_url_source(self, base_id: str, user_id: str, url: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Add URL content to the knowledge base"""
        try:
            source_id = str(uuid.uuid4())
            source = {
                "id": source_id,
                "knowledge_base_id": base_id,
                "name": name or url,
                "type": "url",
                "status": "processed",
                "metadata": {"url": url},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            self.knowledge_sources[source_id] = source
            return source
        except Exception as e:
            logger.error(f"Error adding URL source: {e}")
            raise
    
    async def delete_knowledge_source(self, source_id: str, user_id: str) -> bool:
        """Delete a knowledge source"""
        try:
            if source_id in self.knowledge_sources:
                del self.knowledge_sources[source_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting knowledge source: {e}")
            return False
    
    async def search(self, query: str, base_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the knowledge base"""
        try:
            # For demo purposes, return some sample compliance-related results
            sample_results = [
                {
                    "id": "result-1",
                    "content": "《个人信息保护法》规定，处理个人信息应当遵循合法、正当、必要原则，不得过度收集个人信息。",
                    "metadata": {"source": "个人信息保护法", "article": "第5条"},
                    "score": 0.95
                },
                {
                    "id": "result-2", 
                    "content": "数据控制者应当建立数据保护影响评估制度，对可能对个人权利和自由造成高风险的数据处理活动进行评估。",
                    "metadata": {"source": "GDPR", "article": "第35条"},
                    "score": 0.88
                },
                {
                    "id": "result-3",
                    "content": "企业应当制定数据安全管理制度，明确数据安全负责人，建立数据安全事件应急响应机制。",
                    "metadata": {"source": "网络安全法", "article": "第21条"},
                    "score": 0.82
                }
            ]
            return sample_results
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []


# Global instance
knowledge_service = KnowledgeService()
