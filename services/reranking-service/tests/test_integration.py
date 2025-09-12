"""
Integration tests for the reranking service API
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import patch, MagicMock
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the models before importing app
with patch('models.reranker.CrossEncoder') as mock_cross_encoder:
    mock_instance = MagicMock()
    mock_cross_encoder.return_value = mock_instance
    from app import app

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def mock_reranker():
    """Mock the global reranker"""
    with patch('app.reranker') as mock:
        mock_instance = MagicMock()
        mock_instance.model_name = "test-model"
        mock_instance.device = "cpu"
        mock_instance.cache_hits = 10
        mock_instance.cache_misses = 5
        mock_instance.get_model_info.return_value = {
            "model_name": "test-model",
            "device": "cpu",
            "max_length": 512,
            "cache_hits": 10,
            "cache_misses": 5,
            "cache_size": 15
        }
        mock = mock_instance
        yield mock_instance

class TestRerankAPI:
    """Test the rerank API endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Reranking Service"
        assert "endpoints" in data
    
    @patch('app.reranker')
    def test_rerank_success(self, mock_reranker, client):
        """Test successful reranking"""
        # Setup mock
        mock_reranker.rerank.return_value = (
            ["doc2", "doc1", "doc3"],
            [0.9, 0.7, 0.3],
            [1, 0, 2]
        )
        
        request_data = {
            "query": "test query",
            "documents": ["doc1", "doc2", "doc3"],
            "top_k": 3
        }
        
        response = client.post("/rerank", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["reranked_documents"] == ["doc2", "doc1", "doc3"]
        assert data["scores"] == [0.9, 0.7, 0.3]
        assert data["indices"] == [1, 0, 2]
        assert "processing_time_ms" in data
    
    def test_rerank_empty_query(self, client):
        """Test reranking with empty query"""
        request_data = {
            "query": "",
            "documents": ["doc1", "doc2"]
        }
        
        response = client.post("/rerank", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_rerank_empty_documents(self, client):
        """Test reranking with empty documents list"""
        request_data = {
            "query": "test query",
            "documents": []
        }
        
        response = client.post("/rerank", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_rerank_too_many_documents(self, client):
        """Test reranking with too many documents"""
        request_data = {
            "query": "test query",
            "documents": ["doc"] * 101  # Exceeds max of 100
        }
        
        response = client.post("/rerank", json=request_data)
        assert response.status_code == 422
    
    @patch('app.reranker')
    def test_rerank_with_normalization(self, mock_reranker, client):
        """Test reranking with score normalization"""
        mock_reranker.rerank.return_value = (
            ["doc1"],
            [2.0],  # Raw score
            [0]
        )
        
        request_data = {
            "query": "test query",
            "documents": ["doc1"],
            "normalize_scores": True
        }
        
        response = client.post("/rerank", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        # Score should be normalized using sigmoid
        assert 0 < data["scores"][0] < 1
    
    @patch('app.reranker')
    def test_batch_rerank_success(self, mock_reranker, client):
        """Test batch reranking"""
        mock_reranker.batch_rerank.return_value = [
            (["doc2", "doc1"], [0.8, 0.6], [1, 0]),
            (["doc3"], [0.9], [0])
        ]
        
        request_data = {
            "queries": ["query1", "query2"],
            "documents_list": [
                ["doc1", "doc2"],
                ["doc3"]
            ],
            "top_k": 2
        }
        
        response = client.post("/batch_rerank", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["queries_processed"] == 2
        assert "processing_time_ms" in data
    
    def test_batch_rerank_mismatched_lengths(self, client):
        """Test batch reranking with mismatched query/document lengths"""
        request_data = {
            "queries": ["query1", "query2"],
            "documents_list": [["doc1"]]  # Only one list, should be two
        }
        
        response = client.post("/batch_rerank", json=request_data)
        assert response.status_code == 422
    
    @patch('app.reranker')
    def test_health_check_healthy(self, mock_reranker, client):
        """Test health check when service is healthy"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model"] == "test-model"
        assert data["device"] == "cpu"
        assert data["cache_hits"] == 10
        assert data["cache_misses"] == 5
    
    @patch('app.reranker', None)
    def test_health_check_not_ready(self, client):
        """Test health check when service is not ready"""
        response = client.get("/health")
        assert response.status_code == 503
    
    @patch('app.model_loader')
    @patch('app.reranker')
    def test_get_model_info(self, mock_reranker, mock_loader, client):
        """Test getting model information"""
        mock_reranker.model_name = "test-model"
        mock_reranker.device = "cpu"
        mock_loader.list_available_models.return_value = {
            "model1": {"loaded": True},
            "model2": {"loaded": False}
        }
        mock_loader.get_loaded_models.return_value = ["model1"]
        
        response = client.get("/models")
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_model"] == "test-model"
        assert data["device"] == "cpu"
        assert "available_models" in data
        assert data["loaded_models"] == ["model1"]
    
    @patch('app.reranker')
    def test_clear_cache(self, mock_reranker, client):
        """Test cache clearing"""
        response = client.post("/clear_cache")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        mock_reranker.clear_cache.assert_called_once()
    
    @patch('app.reranker', None)
    def test_rerank_service_unavailable(self, client):
        """Test reranking when service is not initialized"""
        request_data = {
            "query": "test",
            "documents": ["doc1"]
        }
        
        response = client.post("/rerank", json=request_data)
        assert response.status_code == 503
    
    @patch('app.settings.ENABLE_METRICS', True)
    @patch('app.generate_latest')
    def test_metrics_endpoint(self, mock_generate, client):
        """Test metrics endpoint"""
        mock_generate.return_value = b"metrics_data"
        
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert response.content == b"metrics_data"
    
    @patch('app.settings.ENABLE_METRICS', False)
    def test_metrics_disabled(self, client):
        """Test metrics when disabled"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Metrics disabled"


class TestValidation:
    """Test request validation"""
    
    def test_invalid_top_k(self, client):
        """Test with invalid top_k value"""
        request_data = {
            "query": "test",
            "documents": ["doc1"],
            "top_k": 0  # Should be >= 1
        }
        
        response = client.post("/rerank", json=request_data)
        assert response.status_code == 422
    
    def test_top_k_too_large(self, client):
        """Test with top_k exceeding limit"""
        request_data = {
            "query": "test",
            "documents": ["doc1"],
            "top_k": 101  # Max is 100
        }
        
        response = client.post("/rerank", json=request_data)
        assert response.status_code == 422
    
    def test_empty_document_in_list(self, client):
        """Test with empty document in list"""
        request_data = {
            "query": "test",
            "documents": ["doc1", "", "doc2"]  # Empty document
        }
        
        response = client.post("/rerank", json=request_data)
        assert response.status_code == 422
    
    def test_whitespace_only_document(self, client):
        """Test with whitespace-only document"""
        request_data = {
            "query": "test",
            "documents": ["doc1", "   ", "doc2"]  # Whitespace only
        }
        
        response = client.post("/rerank", json=request_data)
        assert response.status_code == 422