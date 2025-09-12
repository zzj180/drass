"""
Unit tests for the reranking service
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.reranker import Reranker

class TestReranker:
    """Test cases for Reranker class"""
    
    @pytest.fixture
    def mock_cross_encoder(self):
        """Mock CrossEncoder for testing"""
        with patch('models.reranker.CrossEncoder') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def reranker(self, mock_cross_encoder):
        """Create a Reranker instance with mocked model"""
        return Reranker(model_name="test-model", device="cpu")
    
    def test_initialization(self, mock_cross_encoder):
        """Test reranker initialization"""
        reranker = Reranker(
            model_name="test-model",
            device="cpu",
            max_length=256
        )
        
        assert reranker.model_name == "test-model"
        assert reranker.device == "cpu"
        assert reranker.max_length == 256
        assert reranker.cache_hits == 0
        assert reranker.cache_misses == 0
    
    def test_rerank_empty_documents(self, reranker):
        """Test reranking with empty document list"""
        docs, scores, indices = reranker.rerank("test query", [])
        
        assert docs == []
        assert scores == []
        assert indices == []
    
    def test_rerank_single_document(self, reranker, mock_cross_encoder):
        """Test reranking with a single document"""
        mock_cross_encoder.predict.return_value = np.array([0.8])
        
        query = "test query"
        documents = ["test document"]
        
        docs, scores, indices = reranker.rerank(query, documents)
        
        assert docs == ["test document"]
        assert scores == [0.8]
        assert indices == [0]
        
        # Check that predict was called with correct arguments
        mock_cross_encoder.predict.assert_called_once()
    
    def test_rerank_multiple_documents(self, reranker, mock_cross_encoder):
        """Test reranking with multiple documents"""
        # Mock scores in reverse order to test sorting
        mock_cross_encoder.predict.return_value = np.array([0.3, 0.9, 0.6])
        
        query = "test query"
        documents = ["doc1", "doc2", "doc3"]
        
        docs, scores, indices = reranker.rerank(query, documents)
        
        # Should be sorted by score (descending)
        assert docs == ["doc2", "doc3", "doc1"]
        assert scores == [0.9, 0.6, 0.3]
        assert indices == [1, 2, 0]
    
    def test_rerank_with_top_k(self, reranker, mock_cross_encoder):
        """Test reranking with top_k limit"""
        mock_cross_encoder.predict.return_value = np.array([0.3, 0.9, 0.6, 0.7, 0.2])
        
        query = "test query"
        documents = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        
        docs, scores, indices = reranker.rerank(query, documents, top_k=3)
        
        # Should return top 3 documents
        assert len(docs) == 3
        assert docs == ["doc2", "doc4", "doc3"]
        assert scores == [0.9, 0.7, 0.6]
        assert indices == [1, 3, 2]
    
    def test_cache_functionality(self, reranker, mock_cross_encoder):
        """Test that caching works correctly"""
        mock_cross_encoder.predict.return_value = np.array([0.5, 0.8])
        
        query = "test query"
        documents = ["doc1", "doc2"]
        
        # First call - should miss cache
        reranker.rerank(query, documents)
        assert reranker.cache_hits == 0
        assert reranker.cache_misses == 1
        
        # Second call with same inputs - should hit cache
        reranker.rerank(query, documents)
        assert reranker.cache_hits == 1
        assert reranker.cache_misses == 1
        
        # Predict should only be called once due to caching
        assert mock_cross_encoder.predict.call_count == 1
    
    def test_score_pairs(self, reranker, mock_cross_encoder):
        """Test direct scoring of query-document pairs"""
        mock_cross_encoder.predict.return_value = np.array([0.7, 0.4, 0.9])
        
        pairs = [
            ["query1", "doc1"],
            ["query2", "doc2"],
            ["query3", "doc3"]
        ]
        
        scores = reranker.score_pairs(pairs)
        
        assert scores == [0.7, 0.4, 0.9]
        mock_cross_encoder.predict.assert_called_once()
    
    def test_score_pairs_normalized(self, reranker, mock_cross_encoder):
        """Test scoring with normalization"""
        # Use values that will change with sigmoid normalization
        mock_cross_encoder.predict.return_value = np.array([2.0, -1.0, 0.0])
        
        pairs = [["q1", "d1"], ["q2", "d2"], ["q3", "d3"]]
        
        scores = reranker.score_pairs(pairs, normalize=True)
        
        # Check that scores are normalized to [0, 1]
        assert all(0 <= s <= 1 for s in scores)
        # Sigmoid(2.0) ≈ 0.88, Sigmoid(-1.0) ≈ 0.27, Sigmoid(0.0) = 0.5
        assert scores[0] > 0.8  # High positive score
        assert scores[1] < 0.3  # Negative score
        assert 0.4 < scores[2] < 0.6  # Zero score -> ~0.5
    
    def test_batch_rerank(self, reranker, mock_cross_encoder):
        """Test batch reranking functionality"""
        # Mock different scores for each query
        mock_cross_encoder.predict.side_effect = [
            np.array([0.3, 0.7]),
            np.array([0.9, 0.4, 0.6])
        ]
        
        queries = ["query1", "query2"]
        documents_list = [
            ["doc1", "doc2"],
            ["doc3", "doc4", "doc5"]
        ]
        
        results = reranker.batch_rerank(queries, documents_list)
        
        assert len(results) == 2
        
        # Check first query results
        docs1, scores1, indices1 = results[0]
        assert docs1 == ["doc2", "doc1"]
        assert scores1 == [0.7, 0.3]
        
        # Check second query results
        docs2, scores2, indices2 = results[1]
        assert docs2 == ["doc3", "doc5", "doc4"]
        assert scores2 == [0.9, 0.6, 0.4]
    
    def test_clear_cache(self, reranker, mock_cross_encoder):
        """Test cache clearing functionality"""
        mock_cross_encoder.predict.return_value = np.array([0.5])
        
        # Add something to cache
        reranker.rerank("query", ["doc"])
        assert reranker.cache_misses == 1
        assert len(reranker._cache) == 1
        
        # Clear cache
        reranker.clear_cache()
        
        assert len(reranker._cache) == 0
        assert reranker.cache_hits == 0
        assert reranker.cache_misses == 0
    
    def test_get_model_info(self, reranker):
        """Test getting model information"""
        info = reranker.get_model_info()
        
        assert info["model_name"] == "test-model"
        assert info["device"] == "cpu"
        assert info["max_length"] == 512
        assert info["cache_hits"] == 0
        assert info["cache_misses"] == 0
        assert info["cache_size"] == 0


class TestModelLoader:
    """Test cases for ModelLoader class"""
    
    @pytest.fixture
    def model_loader(self, tmp_path):
        """Create a ModelLoader instance with temp cache dir"""
        from models.model_loader import ModelLoader
        return ModelLoader(cache_dir=str(tmp_path))
    
    def test_initialization(self, model_loader, tmp_path):
        """Test model loader initialization"""
        assert model_loader.cache_dir == tmp_path
        assert model_loader._loaded_models == {}
        assert model_loader.cache_dir.exists()
    
    def test_list_available_models(self, model_loader):
        """Test listing available models"""
        models = model_loader.list_available_models()
        
        assert "BAAI/bge-reranker-large" in models
        assert "BAAI/bge-reranker-base" in models
        assert all("loaded" in info for info in models.values())
    
    def test_get_model_info(self, model_loader):
        """Test getting model information"""
        info = model_loader.get_model_info("BAAI/bge-reranker-large")
        
        assert "max_length" in info
        assert "description" in info
        assert "size" in info
        assert "loaded" in info
        assert info["loaded"] is False
    
    def test_get_loaded_models(self, model_loader):
        """Test getting list of loaded models"""
        models = model_loader.get_loaded_models()
        assert models == []
    
    @patch('models.model_loader.CrossEncoder')
    def test_load_model(self, mock_cross_encoder, model_loader):
        """Test loading a model"""
        mock_instance = MagicMock()
        mock_cross_encoder.return_value = mock_instance
        
        model = model_loader.load_model("BAAI/bge-reranker-base")
        
        assert model == mock_instance
        assert "BAAI/bge-reranker-base" in model_loader._loaded_models
        mock_cross_encoder.assert_called_once()
    
    @patch('models.model_loader.CrossEncoder')
    def test_load_model_cached(self, mock_cross_encoder, model_loader):
        """Test loading a cached model"""
        mock_instance = MagicMock()
        mock_cross_encoder.return_value = mock_instance
        
        # Load model twice
        model1 = model_loader.load_model("BAAI/bge-reranker-base")
        model2 = model_loader.load_model("BAAI/bge-reranker-base")
        
        # Should return same instance and only load once
        assert model1 == model2
        mock_cross_encoder.assert_called_once()
    
    @patch('models.model_loader.CrossEncoder')
    def test_clear_cache_specific_model(self, mock_cross_encoder, model_loader):
        """Test clearing a specific model from cache"""
        mock_instance = MagicMock()
        mock_cross_encoder.return_value = mock_instance
        
        model_loader.load_model("BAAI/bge-reranker-base")
        assert len(model_loader._loaded_models) == 1
        
        model_loader.clear_cache("BAAI/bge-reranker-base")
        assert len(model_loader._loaded_models) == 0
    
    def test_get_cache_size(self, model_loader):
        """Test getting cache size information"""
        cache_info = model_loader.get_cache_size()
        
        assert "cache_directory" in cache_info
        assert "loaded_models" in cache_info
        assert "models" in cache_info
        assert cache_info["loaded_models"] == 0