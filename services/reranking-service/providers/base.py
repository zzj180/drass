"""
Base class for reranking providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio

class BaseRerankingProvider(ABC):
    """
    Abstract base class for reranking providers

    All providers must implement this interface to ensure consistency
    """

    def __init__(self, model_name: str, device: str = "cpu", **kwargs):
        """
        Initialize the provider

        Args:
            model_name: Name of the model to use
            device: Device to run on (cpu/cuda/mps)
            **kwargs: Provider-specific configuration
        """
        self.model_name = model_name
        self.device = device
        self.is_initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the provider and load models

        This method should handle all async initialization
        """
        pass

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
        normalize_scores: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Rerank documents based on relevance to query

        Args:
            query: The search query
            documents: List of documents to rerank
            top_k: Number of top documents to return
            normalize_scores: Whether to normalize scores to [0, 1]
            **kwargs: Provider-specific parameters

        Returns:
            Dictionary with keys:
                - documents: List of reranked documents
                - scores: List of relevance scores
                - indices: List of original indices
        """
        pass

    @abstractmethod
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

        Args:
            queries: List of queries
            documents_list: List of document lists (one per query)
            top_k: Number of top documents to return per query
            normalize_scores: Whether to normalize scores
            **kwargs: Provider-specific parameters

        Returns:
            List of reranking results (one per query)
        """
        # Default implementation: process sequentially
        results = []
        for query, documents in zip(queries, documents_list):
            result = await self.rerank(
                query=query,
                documents=documents,
                top_k=top_k,
                normalize_scores=normalize_scores,
                **kwargs
            )
            results.append(result)
        return results

    @abstractmethod
    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the provider

        Returns:
            Dictionary with provider information
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Clean up resources
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if the provider is healthy

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try a simple rerank operation
            result = await self.rerank(
                query="test",
                documents=["test document"],
                top_k=1
            )
            return result is not None
        except Exception:
            return False