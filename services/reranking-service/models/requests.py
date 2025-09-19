"""
Request and response models for the reranking service
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class RerankRequest(BaseModel):
    """Request model for reranking documents"""
    query: str = Field(
        ...,
        description="The search query",
        min_length=1,
        max_length=5000
    )
    documents: List[str] = Field(
        ...,
        description="List of documents to rerank",
        min_items=1,
        max_items=100
    )
    top_k: Optional[int] = Field(
        default=10,
        description="Number of top documents to return",
        ge=1,
        le=100
    )
    normalize_scores: bool = Field(
        default=False,
        description="Whether to normalize scores to [0, 1]"
    )

    @validator('documents')
    def validate_documents(cls, v):
        """Validate documents are not empty"""
        if any(not doc.strip() for doc in v):
            raise ValueError("Documents cannot be empty")
        return v

class RerankResponse(BaseModel):
    """Response model for reranked documents"""
    reranked_documents: List[str] = Field(
        ...,
        description="Documents ordered by relevance"
    )
    scores: List[float] = Field(
        ...,
        description="Relevance scores for each document"
    )
    indices: List[int] = Field(
        ...,
        description="Original indices of reranked documents"
    )
    processing_time_ms: float = Field(
        ...,
        description="Time taken to process the request in milliseconds"
    )
    model_used: str = Field(
        ...,
        description="Name of the model used for reranking"
    )
    is_cached: bool = Field(
        default=False,
        description="Whether the result was retrieved from cache"
    )

class BatchRerankRequest(BaseModel):
    """Request model for batch reranking"""
    queries: List[str] = Field(
        ...,
        description="List of queries",
        min_items=1,
        max_items=10
    )
    documents_list: List[List[str]] = Field(
        ...,
        description="List of document lists (one per query)",
        min_items=1,
        max_items=10
    )
    top_k: Optional[int] = Field(
        default=10,
        description="Number of top documents to return per query",
        ge=1,
        le=100
    )
    normalize_scores: bool = Field(
        default=False,
        description="Whether to normalize scores to [0, 1]"
    )

    @validator('documents_list')
    def validate_batch_size(cls, v, values):
        """Validate that queries and documents lists match"""
        if 'queries' in values and len(v) != len(values['queries']):
            raise ValueError("Number of document lists must match number of queries")
        return v