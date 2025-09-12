"""
Basic API tests that don't require model dependencies
"""
import pytest
import json

def test_service_structure():
    """Test that service files are in place"""
    import os
    import sys
    
    service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check that key files exist
    assert os.path.exists(os.path.join(service_dir, 'app.py'))
    assert os.path.exists(os.path.join(service_dir, 'config.py'))
    assert os.path.exists(os.path.join(service_dir, 'requirements.txt'))
    assert os.path.exists(os.path.join(service_dir, 'Dockerfile'))
    assert os.path.exists(os.path.join(service_dir, 'models', 'reranker.py'))
    assert os.path.exists(os.path.join(service_dir, 'models', 'model_loader.py'))

def test_config_imports():
    """Test that config can be imported"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from config import settings
    
    assert settings.SERVICE_NAME == "Reranking Service"
    assert settings.PORT == 8002
    assert settings.HOST == "0.0.0.0"
    assert settings.MODEL_NAME == "BAAI/bge-reranker-large"
    assert settings.MAX_DOCUMENTS == 100
    assert settings.DEFAULT_TOP_K == 10

def test_request_validation():
    """Test request model validation without importing app"""
    from pydantic import ValidationError
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # We can test the Pydantic models without the full app
    from pydantic import BaseModel, Field, validator
    from typing import List, Optional
    
    class RerankRequest(BaseModel):
        query: str = Field(..., min_length=1)
        documents: List[str] = Field(..., min_items=1, max_items=100)
        top_k: Optional[int] = Field(default=10, ge=1, le=100)
        
        @validator('documents')
        def validate_documents(cls, v):
            if any(not doc.strip() for doc in v):
                raise ValueError("Documents cannot be empty")
            return v
    
    # Valid request
    valid_request = RerankRequest(
        query="test query",
        documents=["doc1", "doc2", "doc3"]
    )
    assert valid_request.query == "test query"
    assert len(valid_request.documents) == 3
    assert valid_request.top_k == 10
    
    # Invalid: empty query
    with pytest.raises(ValidationError):
        RerankRequest(query="", documents=["doc1"])
    
    # Invalid: no documents
    with pytest.raises(ValidationError):
        RerankRequest(query="test", documents=[])
    
    # Invalid: empty document
    with pytest.raises(ValidationError):
        RerankRequest(query="test", documents=["doc1", "", "doc2"])
    
    # Invalid: top_k out of range
    with pytest.raises(ValidationError):
        RerankRequest(query="test", documents=["doc1"], top_k=0)
    
    with pytest.raises(ValidationError):
        RerankRequest(query="test", documents=["doc1"], top_k=101)

def test_dockerfile_content():
    """Test that Dockerfile is properly configured"""
    import os
    
    dockerfile_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'Dockerfile'
    )
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    # Check key components
    assert 'FROM python:3.11-slim' in content
    assert 'WORKDIR /app' in content
    assert 'COPY requirements.txt' in content
    assert 'pip install' in content
    assert 'EXPOSE 8002' in content
    assert 'uvicorn' in content

def test_requirements_content():
    """Test that requirements.txt has necessary packages"""
    import os
    
    req_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'requirements.txt'
    )
    
    with open(req_path, 'r') as f:
        content = f.read()
    
    # Check key dependencies
    assert 'fastapi' in content
    assert 'uvicorn' in content
    assert 'pydantic' in content
    assert 'sentence-transformers' in content
    assert 'torch' in content
    assert 'numpy' in content
    assert 'pytest' in content