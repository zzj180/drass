"""
Reranker model implementation using Cross-Encoder
"""
import torch
import numpy as np
from sentence_transformers import CrossEncoder
from typing import List, Tuple, Optional, Dict, Any
import logging
from functools import lru_cache
import hashlib
import json
import time
import os
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

class Reranker:
    """
    Cross-Encoder based reranker for document relevance scoring
    """
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-large",
        device: Optional[str] = None,
        max_length: int = 512,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the reranker model
        
        Args:
            model_name: Name or path of the cross-encoder model
            device: Device to run model on (cuda/cpu/mps)
            max_length: Maximum sequence length for model input
            cache_dir: Directory to cache downloaded models
        """
        self.model_name = model_name
        self.max_length = max_length
        self.cache_dir = cache_dir
        
        # Auto-detect device if not specified
        if device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing reranker model {model_name} on {self.device}")
        
        # Try to load the model with retry logic
        self.model = self._load_model_with_retry(model_name, max_length)
        
        if self.model is None:
            logger.error(f"Failed to load model {model_name} after all retries")
            raise RuntimeError(f"Could not load reranker model: {model_name}")
        
        logger.info(f"Reranker model loaded successfully on {self.device}")
        
        # Cache for computed scores
        self._cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def _load_model_with_retry(self, model_name: str, max_length: int, max_retries: int = 3) -> Optional[CrossEncoder]:
        """
        Load model with retry logic and fallback options
        
        Args:
            model_name: Name of the model to load
            max_length: Maximum sequence length
            max_retries: Maximum number of retry attempts
            
        Returns:
            Loaded CrossEncoder model or None if all attempts fail
        """
        # Fallback models in order of preference (smaller to larger)
        fallback_models = [
            "cross-encoder/ms-marco-MiniLM-L-12-v2",  # 140MB - fastest
            "BAAI/bge-reranker-base",  # 400MB - original target
            "BAAI/bge-reranker-large"  # 1.1GB - largest
        ]
        
        # Remove the target model from fallbacks if it's already there
        if model_name in fallback_models:
            fallback_models.remove(model_name)
        
        # Try the target model first, then fallbacks
        models_to_try = [model_name] + fallback_models
        
        for model_to_try in models_to_try:
            logger.info(f"Attempting to load model: {model_to_try}")
            
            for attempt in range(max_retries):
                try:
                    # Set cache directory if provided
                    if self.cache_dir:
                        os.environ["TRANSFORMERS_CACHE"] = str(self.cache_dir)
                        os.environ["HF_HOME"] = str(self.cache_dir)
                    
                    # Try to download model files first if it's a HuggingFace model
                    if "/" in model_to_try and not os.path.exists(model_to_try):
                        try:
                            logger.info(f"Pre-downloading model files for {model_to_try}")
                            # Download the model files with timeout
                            hf_hub_download(
                                repo_id=model_to_try,
                                filename="config.json",
                                cache_dir=self.cache_dir,
                                local_files_only=False
                            )
                        except Exception as e:
                            logger.warning(f"Pre-download failed for {model_to_try}: {str(e)}")
                    
                    # Load the model
                    model = CrossEncoder(
                        model_to_try,
                        max_length=max_length,
                        device=self.device
                    )
                    
                    logger.info(f"Successfully loaded model: {model_to_try}")
                    return model
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for {model_to_try}: {str(e)}")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All attempts failed for {model_to_try}")
                        continue
        
        logger.error("All model loading attempts failed")
        return None
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
        return_scores: bool = True,
        batch_size: int = 32
    ) -> Tuple[List[str], List[float], List[int]]:
        """
        Rerank documents based on relevance to query
        
        Args:
            query: The search query
            documents: List of documents to rerank
            top_k: Number of top documents to return (None returns all)
            return_scores: Whether to return relevance scores
            batch_size: Batch size for processing
            
        Returns:
            Tuple of (reranked_documents, scores, original_indices)
        """
        if not documents:
            return [], [], []
        
        # Create cache key
        cache_key = self._get_cache_key(query, documents)
        
        # Check cache
        if cache_key in self._cache:
            self.cache_hits += 1
            cached_result = self._cache[cache_key]
            scores = cached_result["scores"]
            logger.debug(f"Cache hit for query: {query[:50]}...")
        else:
            self.cache_misses += 1
            # Create query-document pairs
            pairs = [[query, doc] for doc in documents]
            
            # Score all pairs
            logger.debug(f"Scoring {len(pairs)} query-document pairs")
            scores = self.model.predict(
                pairs,
                batch_size=batch_size,
                show_progress_bar=False
            )
            
            # Cache the result
            self._cache[cache_key] = {"scores": scores.tolist()}
            
        # Convert to numpy array if needed
        if isinstance(scores, list):
            scores = np.array(scores)
            
        # Get sorted indices (descending order)
        sorted_indices = np.argsort(scores)[::-1]
        
        # Apply top_k if specified
        if top_k is not None and top_k < len(sorted_indices):
            sorted_indices = sorted_indices[:top_k]
        
        # Prepare results
        reranked_docs = [documents[i] for i in sorted_indices]
        reranked_scores = [float(scores[i]) for i in sorted_indices]
        
        return reranked_docs, reranked_scores, sorted_indices.tolist()
    
    def score_pairs(
        self,
        pairs: List[List[str]],
        batch_size: int = 32,
        normalize: bool = False
    ) -> List[float]:
        """
        Score query-document pairs directly
        
        Args:
            pairs: List of [query, document] pairs
            batch_size: Batch size for processing
            normalize: Whether to normalize scores to [0, 1]
            
        Returns:
            List of relevance scores
        """
        if not pairs:
            return []
        
        scores = self.model.predict(
            pairs,
            batch_size=batch_size,
            show_progress_bar=False
        )
        
        if normalize:
            scores = self._normalize_scores(scores)
            
        return scores.tolist()
    
    def batch_rerank(
        self,
        queries: List[str],
        documents_list: List[List[str]],
        top_k: Optional[int] = None,
        batch_size: int = 32
    ) -> List[Tuple[List[str], List[float], List[int]]]:
        """
        Rerank multiple queries with their respective documents
        
        Args:
            queries: List of queries
            documents_list: List of document lists (one per query)
            top_k: Number of top documents to return per query
            batch_size: Batch size for processing
            
        Returns:
            List of (reranked_documents, scores, indices) tuples
        """
        results = []
        
        for query, documents in zip(queries, documents_list):
            result = self.rerank(
                query=query,
                documents=documents,
                top_k=top_k,
                batch_size=batch_size
            )
            results.append(result)
            
        return results
    
    def _get_cache_key(self, query: str, documents: List[str]) -> str:
        """Generate a cache key for query-documents combination"""
        content = json.dumps({"query": query, "docs": documents}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normalize scores to [0, 1] range using sigmoid"""
        # Apply sigmoid to convert to [0, 1]
        return 1 / (1 + np.exp(-scores))
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "max_length": self.max_length,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_size": len(self._cache)
        }
    
    def clear_cache(self):
        """Clear the score cache"""
        self._cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        logger.info("Cache cleared")