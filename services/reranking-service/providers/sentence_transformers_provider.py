"""
Sentence Transformers provider for local cross-encoder models
"""
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional
import torch
from sentence_transformers import CrossEncoder
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from .base import BaseRerankingProvider

logger = logging.getLogger(__name__)

class SentenceTransformersProvider(BaseRerankingProvider):
    """
    Provider for sentence-transformers cross-encoder models
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2",
        device: str = "cpu",
        max_length: int = 512,
        batch_size: int = 32,
        cache_dir: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the Sentence Transformers provider

        Args:
            model_name: HuggingFace model name or local path
            device: Device to run on (cpu/cuda/mps)
            max_length: Maximum sequence length
            batch_size: Batch size for processing
            cache_dir: Directory to cache models
        """
        super().__init__(model_name, device, **kwargs)
        self.max_length = max_length
        self.batch_size = batch_size
        self.cache_dir = cache_dir
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=1)

    async def initialize(self) -> None:
        """
        Initialize the cross-encoder model
        """
        try:
            logger.info(f"Loading model {self.model_name} on {self.device}")

            # Auto-detect device if not specified
            if self.device == "auto":
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif torch.backends.mps.is_available():
                    self.device = "mps"
                else:
                    self.device = "cpu"

            # Load model in executor to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor,
                self._load_model
            )

            self.is_initialized = True
            logger.info(f"Model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise

    def _load_model(self) -> CrossEncoder:
        """
        Load the cross-encoder model (sync operation)
        """
        import os

        # Set cache directory if provided
        if self.cache_dir:
            os.environ["TRANSFORMERS_CACHE"] = self.cache_dir
            os.environ["HF_HOME"] = self.cache_dir

        return CrossEncoder(
            self.model_name,
            max_length=self.max_length,
            device=self.device
        )

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
        normalize_scores: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Rerank documents using cross-encoder

        Args:
            query: The search query
            documents: List of documents to rerank
            top_k: Number of top documents to return
            normalize_scores: Whether to normalize scores to [0, 1]

        Returns:
            Dictionary with reranked documents, scores, and indices
        """
        if not self.is_initialized or not self.model:
            raise RuntimeError("Provider not initialized")

        if not documents:
            return {"documents": [], "scores": [], "indices": []}

        # Run scoring in executor to avoid blocking
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            self.executor,
            self._score_documents,
            query,
            documents
        )

        # Convert to numpy array
        scores = np.array(scores)

        # Normalize if requested
        if normalize_scores:
            scores = 1 / (1 + np.exp(-scores))  # Sigmoid normalization

        # Get sorted indices (descending order)
        sorted_indices = np.argsort(scores)[::-1]

        # Apply top_k if specified
        if top_k is not None and top_k < len(sorted_indices):
            sorted_indices = sorted_indices[:top_k]

        # Prepare results
        reranked_docs = [documents[i] for i in sorted_indices]
        reranked_scores = [float(scores[i]) for i in sorted_indices]

        return {
            "documents": reranked_docs,
            "scores": reranked_scores,
            "indices": sorted_indices.tolist()
        }

    def _score_documents(self, query: str, documents: List[str]) -> List[float]:
        """
        Score documents (sync operation)
        """
        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Score with the model
        scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False
        )

        return scores

    async def batch_rerank(
        self,
        queries: List[str],
        documents_list: List[List[str]],
        top_k: Optional[int] = None,
        normalize_scores: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Batch reranking for multiple queries

        Processes queries in parallel for better performance
        """
        if not self.is_initialized or not self.model:
            raise RuntimeError("Provider not initialized")

        # Create tasks for parallel processing
        tasks = []
        for query, documents in zip(queries, documents_list):
            task = self.rerank(
                query=query,
                documents=documents,
                top_k=top_k,
                normalize_scores=normalize_scores,
                **kwargs
            )
            tasks.append(task)

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)
        return results

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the provider
        """
        return {
            "provider": "sentence-transformers",
            "model_name": self.model_name,
            "device": self.device,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "is_initialized": self.is_initialized
        }

    async def close(self) -> None:
        """
        Clean up resources
        """
        if self.executor:
            self.executor.shutdown(wait=False)
        self.model = None
        self.is_initialized = False
        logger.info("Provider closed")