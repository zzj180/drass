"""
Document management service
"""

import os
import hashlib
import logging
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime
from uuid import UUID, uuid4
import aiofiles
import httpx
from pathlib import Path

from app.core.config import settings
from app.models.document import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentStatus,
    DocumentType,
    DocumentFolder,
    DocumentFolderCreate,
    StorageLocation,
    DocumentProcessingRequest,
    DocumentProcessingResult,
    DocumentContent,
    DocumentSearchRequest,
    DocumentSearchResult
)
from app.services.storage_service import storage_service
from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing documents"""
    
    def __init__(self):
        self._initialized = False
        self.doc_processor_url = getattr(settings, 'DOC_PROCESSOR_URL', 'http://localhost:8004')
        self.storage_path = getattr(settings, 'STORAGE_PATH', './data/uploads')
        self.allowed_types = getattr(settings, 'ALLOWED_FILE_TYPES', [
            '.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.md', '.csv', '.json', '.png', '.jpg', '.jpeg', '.gif', '.bmp'
        ])
        self.max_file_size = getattr(settings, 'MAX_FILE_SIZE_MB', 50) * 1024 * 1024
        
        # In-memory storage for demo (should be replaced with database)
        self.documents: Dict[UUID, Document] = {}
        self.folders: Dict[UUID, DocumentFolder] = {}
    
    async def initialize(self):
        """Initialize document service"""
        if not self._initialized:
            # Create storage directory if it doesn't exist
            Path(self.storage_path).mkdir(parents=True, exist_ok=True)
            
            # Initialize storage service
            await storage_service.initialize()
            
            # Check doc processor service
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.doc_processor_url}/health")
                    if response.status_code == 200:
                        logger.info("Document processor service is available")
            except Exception as e:
                logger.warning(f"Document processor service not available: {e}")
            
            self._initialized = True
            logger.info("Document service initialized")
    
    def _get_file_type(self, filename: str, mime_type: str) -> DocumentType:
        """Determine document type from filename and mime type"""
        ext = Path(filename).suffix.lower()
        
        if ext == '.pdf' or 'pdf' in mime_type:
            return DocumentType.PDF
        elif ext in ['.doc', '.docx'] or 'word' in mime_type:
            return DocumentType.DOCX
        elif ext in ['.xls', '.xlsx'] or 'excel' in mime_type or 'spreadsheet' in mime_type:
            return DocumentType.XLSX
        elif ext in ['.ppt', '.pptx'] or 'powerpoint' in mime_type or 'presentation' in mime_type:
            return DocumentType.PPTX
        elif ext == '.txt' or 'text/plain' in mime_type:
            return DocumentType.TXT
        elif ext == '.md' or 'markdown' in mime_type:
            return DocumentType.MD
        elif ext == '.csv' or 'csv' in mime_type:
            return DocumentType.CSV
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp'] or 'image' in mime_type:
            return DocumentType.IMAGE
        else:
            return DocumentType.OTHER
    
    def _calculate_checksum(self, content: bytes) -> str:
        """Calculate SHA256 checksum of file content"""
        return hashlib.sha256(content).hexdigest()
    
    async def get_user_documents(
        self,
        user_id: str,
        folder_id: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[DocumentResponse]:
        """Get user's documents with filtering"""
        documents = []
        
        for doc in self.documents.values():
            if doc.user_id != user_id:
                continue
            
            # Apply filters
            if folder_id and str(doc.folder_id) != folder_id:
                continue
            if status and doc.status != status:
                continue
            if tags and not any(tag in doc.tags for tag in tags):
                continue
            
            documents.append(doc)
        
        # Sort by created_at descending
        documents.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        paginated = documents[skip:skip + limit]
        
        # Convert to response models
        return [DocumentResponse.model_validate(doc) for doc in paginated]
    
    async def upload_document(
        self,
        user_id: str,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        auto_process: bool = True
    ) -> DocumentResponse:
        """Upload a new document"""
        # Read file content
        content = file.read()
        
        # Validate file size
        if len(content) > self.max_file_size:
            raise ValueError(f"File size exceeds maximum allowed size of {self.max_file_size / 1024 / 1024}MB")
        
        # Validate file type
        file_ext = Path(filename).suffix.lower()
        # Remove the dot from file_ext for comparison
        file_ext_no_dot = file_ext[1:] if file_ext.startswith('.') else file_ext

        # Check if the extension (without dot) is in allowed types
        allowed_types_normalized = []
        for allowed in self.allowed_types:
            if allowed.startswith('.'):
                allowed_types_normalized.append(allowed[1:])
            else:
                allowed_types_normalized.append(allowed)

        if file_ext_no_dot not in allowed_types_normalized:
            raise ValueError(f"File type {file_ext} not allowed. Allowed types: {allowed_types_normalized}")
        
        # Create document record
        doc_id = uuid4()
        file_type = self._get_file_type(filename, content_type)
        checksum = self._calculate_checksum(content)
        
        # Check for duplicate
        for doc in self.documents.values():
            if doc.checksum == checksum and doc.user_id == user_id:
                logger.warning(f"Duplicate document detected: {filename}")
                return DocumentResponse.model_validate(doc)
        
        # Store file
        storage_path = await storage_service.store_file(
            file_content=content,
            file_id=str(doc_id),
            file_extension=file_ext,
            user_id=user_id
        )
        
        # Create document object
        document = Document(
            id=doc_id,
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_size=len(content),
            mime_type=content_type,
            folder_id=folder_id,
            tags=tags or [],
            description=description,
            status=DocumentStatus.PENDING,
            storage_location=StorageLocation.LOCAL if settings.STORAGE_TYPE == "local" else StorageLocation.S3,
            storage_path=storage_path,
            checksum=checksum,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Store in memory (should be database)
        self.documents[doc_id] = document
        
        # Auto-process if requested
        if auto_process:
            # Process asynchronously (in production, use task queue)
            try:
                await self.process_document(user_id, doc_id)
            except Exception as e:
                logger.error(f"Failed to auto-process document {doc_id}: {e}")
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
        
        return DocumentResponse.model_validate(document)
    
    async def get_document(self, user_id: str, document_id: UUID) -> Optional[DocumentResponse]:
        """Get a specific document"""
        doc = self.documents.get(document_id)
        if doc and doc.user_id == user_id:
            return DocumentResponse.model_validate(doc)
        return None
    
    async def process_document(
        self,
        user_id: str,
        document_id: UUID,
        processing_request: Optional[DocumentProcessingRequest] = None
    ) -> DocumentProcessingResult:
        """Process document to extract text and metadata"""
        doc = self.documents.get(document_id)
        if not doc or doc.user_id != user_id:
            raise ValueError("Document not found")
        
        if doc.status == DocumentStatus.PROCESSING:
            raise ValueError("Document is already being processed")
        
        # Update status
        doc.status = DocumentStatus.PROCESSING
        doc.updated_at = datetime.utcnow()
        
        try:
            # Get file content
            file_content = await storage_service.get_file(doc.storage_path)
            
            # Try to call document processor service if available
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    # Quick health check first
                    health_response = await client.get(f"{self.doc_processor_url}/health")
                    if health_response.status_code == 200:
                        # Document processor is available, use it
                        files = {
                            'file': (doc.filename, file_content, doc.mime_type)
                        }

                        # Prepare processing parameters
                        data = {}
                        if processing_request:
                            data = {
                                'chunk_size': processing_request.chunk_size,
                                'chunk_overlap': processing_request.chunk_overlap,
                                'extract_metadata': processing_request.extract_metadata,
                                'language': processing_request.language
                            }

                        response = await client.post(
                            f"{self.doc_processor_url}/convert",
                            files=files,
                            data=data
                        )

                        if response.status_code != 200:
                            raise Exception(f"Document processor error: {response.text}")

                        result = response.json()
                    else:
                        raise Exception("Document processor not available")
            except Exception as e:
                # Fallback: Simple text extraction for text-based files
                logger.warning(f"Document processor not available, using fallback: {e}")
                result = {
                    'markdown': '',
                    'metadata': {
                        'page_count': 1,
                        'language': 'en'
                    }
                }

                # Simple extraction based on file type
                if doc.file_type in [DocumentType.TXT, DocumentType.MD]:
                    result['markdown'] = file_content.decode('utf-8', errors='ignore')
                elif doc.file_type == DocumentType.PDF:
                    # Try to extract text from PDF using PyPDF2
                    try:
                        import io
                        from PyPDF2 import PdfReader

                        pdf_file = io.BytesIO(file_content)
                        pdf_reader = PdfReader(pdf_file)

                        text_content = []
                        page_count = len(pdf_reader.pages)

                        for page_num in range(page_count):
                            page = pdf_reader.pages[page_num]
                            text = page.extract_text()
                            if text:
                                text_content.append(f"--- Page {page_num + 1} ---\n{text}")

                        result['markdown'] = "\n\n".join(text_content) if text_content else "PDF document: Unable to extract text"
                        result['metadata']['page_count'] = page_count
                        logger.info(f"Extracted text from PDF: {doc.filename}, pages: {page_count}")
                    except Exception as pdf_error:
                        logger.error(f"Failed to extract PDF text: {pdf_error}")
                        result['markdown'] = f"PDF document: {doc.filename} (extraction failed: {str(pdf_error)})"
                else:
                    result['markdown'] = f"Document: {doc.filename} (type: {doc.file_type.value})"
                
                # Update document with extracted content
                doc.extracted_text = result.get('markdown', '')
                doc.page_count = result.get('metadata', {}).get('page_count')
                doc.word_count = len(doc.extracted_text.split()) if doc.extracted_text else 0
                doc.language = result.get('metadata', {}).get('language', 'en')
                doc.metadata.update(result.get('metadata', {}))
                doc.status = DocumentStatus.COMPLETED
                doc.processed_at = datetime.utcnow()
                
                # Create chunks for vector storage
                if doc.extracted_text and processing_request:
                    chunks = await self._create_chunks(
                        doc.extracted_text,
                        processing_request.chunk_size,
                        processing_request.chunk_overlap
                    )
                    
                    # Store in vector database
                    vector_ids = await vector_store_service.add_documents(
                        texts=[chunk['text'] for chunk in chunks],
                        metadatas=[{
                            'document_id': str(doc_id),
                            'chunk_index': i,
                            'filename': doc.filename,
                            'user_id': user_id,
                            **chunk.get('metadata', {})
                        } for i, chunk in enumerate(chunks)]
                    )
                    
                    doc.vector_ids = vector_ids
                    doc.chunk_count = len(chunks)
                
                # Create processing result
                return DocumentProcessingResult(
                    document_id=document_id,
                    status=doc.status,
                    extracted_text=doc.extracted_text,
                    chunks=chunks if processing_request else [],
                    metadata=doc.metadata,
                    page_count=doc.page_count,
                    word_count=doc.word_count,
                    language=doc.language,
                    processing_time=result.get('processing_time', 0.0)
                )
                
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            doc.retry_count += 1
            
            return DocumentProcessingResult(
                document_id=document_id,
                status=DocumentStatus.FAILED,
                error_message=str(e)
            )
        finally:
            doc.updated_at = datetime.utcnow()
    
    async def _create_chunks(
        self,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """Create text chunks for vector storage"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - chunk_overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append({
                'text': chunk_text,
                'metadata': {
                    'start_index': i,
                    'end_index': min(i + chunk_size, len(words)),
                    'word_count': len(chunk_words)
                }
            })
        
        return chunks
    
    async def get_document_content(
        self,
        user_id: str,
        document_id: UUID
    ) -> Optional[DocumentContent]:
        """Get extracted content of a document"""
        doc = self.documents.get(document_id)
        if not doc or doc.user_id != user_id:
            return None
        
        if doc.status != DocumentStatus.COMPLETED:
            return None
        
        # Get chunks if available
        chunks = []
        if doc.vector_ids:
            # In production, retrieve chunks from vector store
            chunks = [{'id': vid, 'text': 'chunk_text'} for vid in doc.vector_ids]
        
        return DocumentContent(
            document_id=document_id,
            content=doc.extracted_text or '',
            content_type='text/markdown',
            chunks=chunks,
            metadata={
                'page_count': doc.page_count,
                'word_count': doc.word_count,
                'language': doc.language,
                'processed_at': doc.processed_at.isoformat() if doc.processed_at else None
            }
        )
    
    async def delete_document(self, user_id: str, document_id: UUID) -> bool:
        """Delete a document"""
        doc = self.documents.get(document_id)
        if not doc or doc.user_id != user_id:
            return False
        
        try:
            # Delete from storage
            await storage_service.delete_file(doc.storage_path)
            
            # Delete from vector store
            if doc.vector_ids:
                await vector_store_service.delete_documents(doc.vector_ids)
            
            # Delete from memory (should be database)
            del self.documents[document_id]
            
            logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    async def get_user_folders(self, user_id: str) -> List[DocumentFolder]:
        """Get user's document folders"""
        folders = []
        for folder in self.folders.values():
            if folder.user_id == user_id:
                # Count documents in folder
                folder.document_count = sum(
                    1 for doc in self.documents.values()
                    if doc.user_id == user_id and doc.folder_id == folder.id
                )
                folders.append(folder)
        
        # Sort by name
        folders.sort(key=lambda x: x.name)
        return folders
    
    async def create_folder(
        self,
        user_id: str,
        folder_data: DocumentFolderCreate
    ) -> DocumentFolder:
        """Create a new document folder"""
        # Check for duplicate name
        for folder in self.folders.values():
            if folder.user_id == user_id and folder.name == folder_data.name:
                raise ValueError(f"Folder with name '{folder_data.name}' already exists")
        
        # Create folder
        folder = DocumentFolder(
            id=uuid4(),
            name=folder_data.name,
            description=folder_data.description,
            parent_id=folder_data.parent_id,
            user_id=user_id,
            document_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Store in memory (should be database)
        self.folders[folder.id] = folder
        
        logger.info(f"Created folder {folder.id} for user {user_id}")
        return folder
    
    async def search_documents(
        self,
        user_id: str,
        search_request: DocumentSearchRequest
    ) -> DocumentSearchResult:
        """Search documents with semantic search"""
        # Simple implementation - in production, use vector search
        documents = await self.get_user_documents(
            user_id=user_id,
            folder_id=str(search_request.folder_id) if search_request.folder_id else None,
            tags=search_request.tags,
            status=search_request.status.value if search_request.status else None,
            skip=search_request.offset,
            limit=search_request.limit
        )
        
        # Filter by query (simple text search)
        if search_request.query:
            filtered = []
            query_lower = search_request.query.lower()
            for doc in documents:
                if (query_lower in doc.filename.lower() or
                    (doc.description and query_lower in doc.description.lower()) or
                    any(query_lower in tag.lower() for tag in doc.tags)):
                    filtered.append(doc)
            documents = filtered
        
        return DocumentSearchResult(
            documents=documents,
            total=len(documents),
            limit=search_request.limit,
            offset=search_request.offset,
            query=search_request.query
        )
    
    async def update_document(
        self,
        user_id: str,
        document_id: UUID,
        update_data: DocumentUpdate
    ) -> Optional[DocumentResponse]:
        """Update document metadata"""
        doc = self.documents.get(document_id)
        if not doc or doc.user_id != user_id:
            return None
        
        # Update fields
        if update_data.filename:
            doc.filename = update_data.filename
        if update_data.folder_id is not None:
            doc.folder_id = update_data.folder_id
        if update_data.tags is not None:
            doc.tags = update_data.tags
        if update_data.description is not None:
            doc.description = update_data.description
        if update_data.metadata:
            doc.metadata.update(update_data.metadata)
        
        doc.updated_at = datetime.utcnow()
        
        return DocumentResponse.model_validate(doc)


# Singleton instance
document_service = DocumentService()