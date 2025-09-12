"""
Document CRUD operations for database
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func

# Note: In production, these would be SQLAlchemy models
# For now, we'll use in-memory storage via document_service

logger = logging.getLogger(__name__)


class DocumentCRUD:
    """Document database operations"""
    
    @staticmethod
    async def create_document(
        db: AsyncSession,
        document_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create document in database"""
        # In production, this would use SQLAlchemy
        # For now, return the data as-is
        return document_data
    
    @staticmethod
    async def get_document(
        db: AsyncSession,
        document_id: UUID,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        # In production, this would query the database
        from app.services.document_service import document_service
        
        doc = document_service.documents.get(document_id)
        if doc and doc.user_id == user_id:
            return doc.model_dump()
        return None
    
    @staticmethod
    async def get_documents(
        db: AsyncSession,
        user_id: str,
        folder_id: Optional[UUID] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get documents with filtering"""
        from app.services.document_service import document_service
        
        documents = []
        for doc in document_service.documents.values():
            if doc.user_id != user_id:
                continue
            
            # Apply filters
            if folder_id and doc.folder_id != folder_id:
                continue
            if status and doc.status != status:
                continue
            if tags and not any(tag in doc.tags for tag in tags):
                continue
            
            documents.append(doc.model_dump())
        
        # Sort and paginate
        documents.sort(key=lambda x: x['created_at'], reverse=True)
        return documents[skip:skip + limit]
    
    @staticmethod
    async def update_document(
        db: AsyncSession,
        document_id: UUID,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update document in database"""
        from app.services.document_service import document_service
        
        doc = document_service.documents.get(document_id)
        if not doc or doc.user_id != user_id:
            return None
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        
        doc.updated_at = datetime.utcnow()
        return doc.model_dump()
    
    @staticmethod
    async def delete_document(
        db: AsyncSession,
        document_id: UUID,
        user_id: str
    ) -> bool:
        """Delete document from database"""
        from app.services.document_service import document_service
        
        doc = document_service.documents.get(document_id)
        if not doc or doc.user_id != user_id:
            return False
        
        del document_service.documents[document_id]
        return True
    
    @staticmethod
    async def count_documents(
        db: AsyncSession,
        user_id: str,
        folder_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> int:
        """Count documents with filtering"""
        from app.services.document_service import document_service
        
        count = 0
        for doc in document_service.documents.values():
            if doc.user_id != user_id:
                continue
            if folder_id and doc.folder_id != folder_id:
                continue
            if status and doc.status != status:
                continue
            count += 1
        
        return count
    
    @staticmethod
    async def get_document_stats(
        db: AsyncSession,
        user_id: str
    ) -> Dict[str, Any]:
        """Get document statistics for user"""
        from app.services.document_service import document_service
        from app.models.document import DocumentStatus
        
        stats = {
            'total': 0,
            'by_status': {},
            'by_type': {},
            'total_size': 0,
            'total_words': 0,
            'total_pages': 0
        }
        
        for doc in document_service.documents.values():
            if doc.user_id != user_id:
                continue
            
            stats['total'] += 1
            stats['total_size'] += doc.file_size
            
            # Count by status
            status_key = doc.status.value
            stats['by_status'][status_key] = stats['by_status'].get(status_key, 0) + 1
            
            # Count by type
            type_key = doc.file_type.value
            stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1
            
            # Add word and page counts
            if doc.word_count:
                stats['total_words'] += doc.word_count
            if doc.page_count:
                stats['total_pages'] += doc.page_count
        
        return stats


class DocumentFolderCRUD:
    """Document folder database operations"""
    
    @staticmethod
    async def create_folder(
        db: AsyncSession,
        folder_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create folder in database"""
        return folder_data
    
    @staticmethod
    async def get_folder(
        db: AsyncSession,
        folder_id: UUID,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get folder by ID"""
        from app.services.document_service import document_service
        
        folder = document_service.folders.get(folder_id)
        if folder and folder.user_id == user_id:
            return folder.model_dump()
        return None
    
    @staticmethod
    async def get_folders(
        db: AsyncSession,
        user_id: str,
        parent_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get user folders"""
        from app.services.document_service import document_service
        
        folders = []
        for folder in document_service.folders.values():
            if folder.user_id != user_id:
                continue
            if parent_id is not None and folder.parent_id != parent_id:
                continue
            
            # Count documents
            folder.document_count = sum(
                1 for doc in document_service.documents.values()
                if doc.user_id == user_id and doc.folder_id == folder.id
            )
            
            folders.append(folder.model_dump())
        
        folders.sort(key=lambda x: x['name'])
        return folders
    
    @staticmethod
    async def update_folder(
        db: AsyncSession,
        folder_id: UUID,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update folder in database"""
        from app.services.document_service import document_service
        
        folder = document_service.folders.get(folder_id)
        if not folder or folder.user_id != user_id:
            return None
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(folder, key):
                setattr(folder, key, value)
        
        folder.updated_at = datetime.utcnow()
        return folder.model_dump()
    
    @staticmethod
    async def delete_folder(
        db: AsyncSession,
        folder_id: UUID,
        user_id: str,
        cascade: bool = False
    ) -> bool:
        """Delete folder from database"""
        from app.services.document_service import document_service
        
        folder = document_service.folders.get(folder_id)
        if not folder or folder.user_id != user_id:
            return False
        
        # Check if folder has documents
        has_documents = any(
            doc.folder_id == folder_id
            for doc in document_service.documents.values()
            if doc.user_id == user_id
        )
        
        if has_documents and not cascade:
            raise ValueError("Folder contains documents. Use cascade=True to delete all.")
        
        # Delete documents if cascade
        if cascade:
            docs_to_delete = [
                doc.id for doc in document_service.documents.values()
                if doc.user_id == user_id and doc.folder_id == folder_id
            ]
            for doc_id in docs_to_delete:
                del document_service.documents[doc_id]
        
        # Delete folder
        del document_service.folders[folder_id]
        return True
    
    @staticmethod
    async def get_folder_tree(
        db: AsyncSession,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get hierarchical folder structure"""
        from app.services.document_service import document_service
        
        folders = []
        folder_dict = {}
        
        # First pass: create folder dictionary
        for folder in document_service.folders.values():
            if folder.user_id == user_id:
                folder_data = folder.model_dump()
                folder_data['children'] = []
                folder_dict[folder.id] = folder_data
        
        # Second pass: build tree structure
        for folder_data in folder_dict.values():
            if folder_data['parent_id']:
                parent = folder_dict.get(folder_data['parent_id'])
                if parent:
                    parent['children'].append(folder_data)
            else:
                folders.append(folder_data)
        
        return folders


# Export CRUD instances
document_crud = DocumentCRUD()
folder_crud = DocumentFolderCRUD()