"""
Tests for Document Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import io
from uuid import uuid4
from datetime import datetime

from app.services.document_service import DocumentService
from app.services.storage_service import StorageService
from app.models.document import (
    Document,
    DocumentCreate,
    DocumentStatus,
    DocumentType,
    DocumentFolder,
    DocumentFolderCreate,
    DocumentProcessingRequest,
    StorageLocation
)


@pytest.fixture
def document_service():
    """Create document service instance"""
    service = DocumentService()
    service._initialized = True
    return service


@pytest.fixture
def storage_service():
    """Create storage service instance"""
    service = StorageService()
    service._initialized = True
    service.storage_type = 'local'
    return service


@pytest.fixture
def sample_file():
    """Create sample file for testing"""
    content = b"This is a test document content"
    file = io.BytesIO(content)
    return file, content


@pytest.mark.asyncio
class TestDocumentService:
    """Test Document Service"""
    
    async def test_service_initialization(self):
        """Test service initialization"""
        service = DocumentService()
        
        with patch('app.services.storage_service.storage_service.initialize') as mock_storage:
            mock_storage.return_value = None
            
            await service.initialize()
            
            assert service._initialized
            mock_storage.assert_called_once()
    
    async def test_upload_document(self, document_service, sample_file):
        """Test document upload"""
        file, content = sample_file
        user_id = "test_user"
        filename = "test.pdf"
        
        with patch('app.services.storage_service.storage_service.store_file') as mock_store:
            mock_store.return_value = f"uploads/{user_id}/test.pdf"
            
            result = await document_service.upload_document(
                user_id=user_id,
                file=file,
                filename=filename,
                content_type="application/pdf",
                tags=["test"],
                auto_process=False
            )
            
            assert result.filename == filename
            assert result.file_type == DocumentType.PDF
            assert result.user_id == user_id
            assert result.status == DocumentStatus.PENDING
            assert "test" in result.tags
            
            mock_store.assert_called_once()
    
    async def test_upload_duplicate_detection(self, document_service, sample_file):
        """Test duplicate document detection"""
        file, content = sample_file
        user_id = "test_user"
        filename = "test.pdf"
        
        with patch('app.services.storage_service.storage_service.store_file') as mock_store:
            mock_store.return_value = f"uploads/{user_id}/test.pdf"
            
            # Upload first document
            doc1 = await document_service.upload_document(
                user_id=user_id,
                file=io.BytesIO(content),
                filename=filename,
                content_type="application/pdf",
                auto_process=False
            )
            
            # Try to upload duplicate
            doc2 = await document_service.upload_document(
                user_id=user_id,
                file=io.BytesIO(content),
                filename="duplicate.pdf",
                content_type="application/pdf",
                auto_process=False
            )
            
            # Should return the same document (duplicate detected)
            assert doc1.id == doc2.id
            assert doc1.checksum == doc2.checksum
    
    async def test_file_size_validation(self, document_service):
        """Test file size validation"""
        user_id = "test_user"
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        file = io.BytesIO(large_content)
        
        with pytest.raises(ValueError, match="File size exceeds"):
            await document_service.upload_document(
                user_id=user_id,
                file=file,
                filename="large.pdf",
                content_type="application/pdf"
            )
    
    async def test_file_type_validation(self, document_service):
        """Test file type validation"""
        user_id = "test_user"
        file = io.BytesIO(b"test content")
        
        with pytest.raises(ValueError, match="File type .exe not allowed"):
            await document_service.upload_document(
                user_id=user_id,
                file=file,
                filename="malicious.exe",
                content_type="application/octet-stream"
            )
    
    async def test_get_user_documents(self, document_service):
        """Test getting user documents with filtering"""
        user_id = "test_user"
        
        # Create test documents
        doc1 = Document(
            id=uuid4(),
            user_id=user_id,
            filename="doc1.pdf",
            file_type=DocumentType.PDF,
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            storage_location=StorageLocation.LOCAL,
            storage_path="path1",
            tags=["important"],
            created_at=datetime.utcnow()
        )
        
        doc2 = Document(
            id=uuid4(),
            user_id=user_id,
            filename="doc2.docx",
            file_type=DocumentType.DOCX,
            file_size=2000,
            mime_type="application/docx",
            status=DocumentStatus.PENDING,
            storage_location=StorageLocation.LOCAL,
            storage_path="path2",
            tags=["draft"],
            created_at=datetime.utcnow()
        )
        
        document_service.documents[doc1.id] = doc1
        document_service.documents[doc2.id] = doc2
        
        # Get all documents
        docs = await document_service.get_user_documents(user_id)
        assert len(docs) == 2
        
        # Filter by status
        completed_docs = await document_service.get_user_documents(
            user_id, status=DocumentStatus.COMPLETED.value
        )
        assert len(completed_docs) == 1
        assert completed_docs[0].id == doc1.id
        
        # Filter by tags
        important_docs = await document_service.get_user_documents(
            user_id, tags=["important"]
        )
        assert len(important_docs) == 1
        assert important_docs[0].id == doc1.id
    
    @patch('httpx.AsyncClient')
    async def test_process_document(self, mock_client_class, document_service):
        """Test document processing"""
        user_id = "test_user"
        doc_id = uuid4()
        
        # Create test document
        doc = Document(
            id=doc_id,
            user_id=user_id,
            filename="test.pdf",
            file_type=DocumentType.PDF,
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
            storage_location=StorageLocation.LOCAL,
            storage_path="test/path.pdf",
            created_at=datetime.utcnow()
        )
        document_service.documents[doc_id] = doc
        
        # Mock storage and processor
        with patch('app.services.storage_service.storage_service.get_file') as mock_get:
            mock_get.return_value = b"file content"
            
            # Mock httpx client
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'markdown': 'Extracted text content',
                'metadata': {
                    'page_count': 5,
                    'language': 'en'
                },
                'processing_time': 1.5
            }
            
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock vector store
            with patch('app.services.vector_store.vector_store_service.add_documents') as mock_vector:
                mock_vector.return_value = ['vec1', 'vec2', 'vec3']
                
                processing_request = DocumentProcessingRequest(
                    chunk_size=100,
                    chunk_overlap=20
                )
                
                result = await document_service.process_document(
                    user_id, doc_id, processing_request
                )
                
                assert result.status == DocumentStatus.COMPLETED
                assert result.extracted_text == 'Extracted text content'
                assert result.page_count == 5
                assert result.language == 'en'
                
                # Check document was updated
                assert doc.status == DocumentStatus.COMPLETED
                assert doc.extracted_text == 'Extracted text content'
                assert doc.page_count == 5
                assert len(doc.vector_ids) == 3
    
    async def test_delete_document(self, document_service):
        """Test document deletion"""
        user_id = "test_user"
        doc_id = uuid4()
        
        # Create test document
        doc = Document(
            id=doc_id,
            user_id=user_id,
            filename="test.pdf",
            file_type=DocumentType.PDF,
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            storage_location=StorageLocation.LOCAL,
            storage_path="test/path.pdf",
            vector_ids=['vec1', 'vec2'],
            created_at=datetime.utcnow()
        )
        document_service.documents[doc_id] = doc
        
        with patch('app.services.storage_service.storage_service.delete_file') as mock_delete:
            mock_delete.return_value = True
            
            with patch('app.services.vector_store.vector_store_service.delete_documents') as mock_vector:
                result = await document_service.delete_document(user_id, doc_id)
                
                assert result is True
                assert doc_id not in document_service.documents
                mock_delete.assert_called_once_with("test/path.pdf")
                mock_vector.assert_called_once_with(['vec1', 'vec2'])
    
    async def test_create_folder(self, document_service):
        """Test folder creation"""
        user_id = "test_user"
        
        folder_data = DocumentFolderCreate(
            name="Test Folder",
            description="A test folder"
        )
        
        folder = await document_service.create_folder(user_id, folder_data)
        
        assert folder.name == "Test Folder"
        assert folder.description == "A test folder"
        assert folder.user_id == user_id
        assert folder.id in document_service.folders
        
        # Test duplicate name detection
        with pytest.raises(ValueError, match="already exists"):
            await document_service.create_folder(user_id, folder_data)
    
    async def test_search_documents(self, document_service):
        """Test document search"""
        user_id = "test_user"
        
        # Create test documents
        doc1 = Document(
            id=uuid4(),
            user_id=user_id,
            filename="compliance report.pdf",
            file_type=DocumentType.PDF,
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            storage_location=StorageLocation.LOCAL,
            storage_path="path1",
            description="Annual compliance report",
            tags=["compliance", "2024"],
            created_at=datetime.utcnow()
        )
        
        doc2 = Document(
            id=uuid4(),
            user_id=user_id,
            filename="contract.docx",
            file_type=DocumentType.DOCX,
            file_size=2000,
            mime_type="application/docx",
            status=DocumentStatus.COMPLETED,
            storage_location=StorageLocation.LOCAL,
            storage_path="path2",
            description="Service contract",
            tags=["legal"],
            created_at=datetime.utcnow()
        )
        
        document_service.documents[doc1.id] = doc1
        document_service.documents[doc2.id] = doc2
        
        from app.models.document import DocumentSearchRequest
        
        # Search by query
        search_request = DocumentSearchRequest(
            query="compliance",
            limit=10
        )
        
        result = await document_service.search_documents(user_id, search_request)
        
        assert result.total == 1
        assert result.documents[0].id == doc1.id
        
        # Search by tag
        search_request = DocumentSearchRequest(
            query="",
            tags=["legal"],
            limit=10
        )
        
        result = await document_service.search_documents(user_id, search_request)
        
        assert result.total == 1
        assert result.documents[0].id == doc2.id


@pytest.mark.asyncio
class TestStorageService:
    """Test Storage Service"""
    
    async def test_local_storage(self, storage_service):
        """Test local file storage"""
        content = b"test content"
        file_id = str(uuid4())
        user_id = "test_user"
        
        # Mock file operations
        with patch('aiofiles.open', create=True) as mock_open:
            mock_file = AsyncMock()
            mock_file.write = AsyncMock()
            mock_open.return_value.__aenter__.return_value = mock_file
            
            path = await storage_service.store_file(
                file_content=content,
                file_id=file_id,
                file_extension=".pdf",
                user_id=user_id
            )
            
            assert user_id in path
            assert file_id in path
            assert path.endswith(".pdf")
            mock_file.write.assert_called_once_with(content)
    
    @patch('boto3.Session')
    async def test_s3_storage(self, mock_session):
        """Test S3 file storage"""
        service = StorageService()
        service.storage_type = 's3'
        service.s3_bucket = 'test-bucket'
        
        # Mock S3 client
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        
        await service.initialize()
        
        content = b"test content"
        file_id = str(uuid4())
        user_id = "test_user"
        
        path = await service.store_file(
            file_content=content,
            file_id=file_id,
            file_extension=".pdf",
            user_id=user_id
        )
        
        assert user_id in path
        assert file_id in path
        mock_client.put_object.assert_called_once()
        
        # Test file retrieval
        mock_client.get_object.return_value = {'Body': io.BytesIO(content)}
        retrieved = await service.get_file(path)
        assert retrieved == content