"""Semantic document splitting using sentence embeddings and similarity."""

import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


@dataclass 
class SemanticChunk:
    """Represents a semantically coherent chunk."""
    content: str
    chunk_id: str
    start_idx: int
    end_idx: int
    metadata: Dict[str, Any] = None
    embeddings: Optional[np.ndarray] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SemanticSplitter:
    """Split documents based on semantic similarity between sentences.
    
    Groups sentences with high semantic similarity into chunks,
    creating natural semantic boundaries.
    """
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        similarity_threshold: float = 0.5,
        sentence_encoder=None
    ):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.similarity_threshold = similarity_threshold
        self.sentence_encoder = sentence_encoder
        
    def split_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[SemanticChunk]:
        """Split document into semantically coherent chunks.
        
        Args:
            text: Document text to split
            metadata: Optional document metadata
            
        Returns:
            List of SemanticChunk objects
        """
        if not text:
            return []
            
        # Split into sentences
        sentences = self._split_sentences(text)
        if not sentences:
            return []
            
        # Get embeddings if encoder is available
        if self.sentence_encoder:
            embeddings = self._get_sentence_embeddings(sentences)
            chunks = self._create_semantic_chunks_with_embeddings(
                sentences, embeddings, metadata
            )
        else:
            # Fallback to rule-based semantic grouping
            chunks = self._create_semantic_chunks_rule_based(
                sentences, metadata
            )
            
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences with position tracking."""
        # Enhanced sentence splitting pattern
        sentence_endings = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*\n+'
        sentences = re.split(sentence_endings, text)
        
        # Filter and clean sentences
        cleaned_sentences = []
        for sent in sentences:
            sent = sent.strip()
            if sent and len(sent) > 10:  # Min sentence length
                cleaned_sentences.append(sent)
                
        return cleaned_sentences
    
    def _get_sentence_embeddings(self, sentences: List[str]) -> np.ndarray:
        """Get embeddings for sentences using the encoder."""
        if not self.sentence_encoder:
            raise ValueError("Sentence encoder not provided")
            
        try:
            # Assuming encoder has an encode method
            embeddings = self.sentence_encoder.encode(sentences)
            return np.array(embeddings)
        except Exception as e:
            logger.error(f"Error encoding sentences: {e}")
            return np.array([])
    
    def _create_semantic_chunks_with_embeddings(
        self,
        sentences: List[str],
        embeddings: np.ndarray,
        metadata: Optional[Dict[str, Any]]
    ) -> List[SemanticChunk]:
        """Create chunks based on semantic similarity of embeddings."""
        chunks = []
        current_chunk = []
        current_size = 0
        current_embeddings = []
        
        for i, (sent, emb) in enumerate(zip(sentences, embeddings)):
            sent_size = len(sent)
            
            # Check if we should start a new chunk
            should_split = False
            
            if current_chunk:
                # Check size constraint
                if current_size + sent_size > self.max_chunk_size:
                    should_split = True
                else:
                    # Check semantic similarity
                    avg_embedding = np.mean(current_embeddings, axis=0)
                    similarity = cosine_similarity(
                        [emb], [avg_embedding]
                    )[0][0]
                    
                    if similarity < self.similarity_threshold:
                        # Low similarity, consider splitting
                        if current_size >= self.min_chunk_size:
                            should_split = True
            
            if should_split and current_chunk:
                # Create chunk from current sentences
                chunk_text = ' '.join(current_chunk)
                chunk_id = self._generate_chunk_id(chunk_text)
                
                chunk_metadata = {
                    'sentence_count': len(current_chunk),
                    'chunk_size': current_size,
                    'chunk_index': len(chunks),
                    'avg_similarity': self._calculate_avg_similarity(current_embeddings),
                    **(metadata or {})
                }
                
                chunks.append(SemanticChunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    start_idx=i - len(current_chunk),
                    end_idx=i - 1,
                    metadata=chunk_metadata,
                    embeddings=np.mean(current_embeddings, axis=0)
                ))
                
                # Start new chunk
                current_chunk = [sent]
                current_size = sent_size
                current_embeddings = [emb]
            else:
                # Add to current chunk
                current_chunk.append(sent)
                current_size += sent_size
                current_embeddings.append(emb)
        
        # Add remaining sentences
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_id = self._generate_chunk_id(chunk_text)
            
            chunk_metadata = {
                'sentence_count': len(current_chunk),
                'chunk_size': current_size,
                'chunk_index': len(chunks),
                'avg_similarity': self._calculate_avg_similarity(current_embeddings),
                **(metadata or {})
            }
            
            chunks.append(SemanticChunk(
                content=chunk_text,
                chunk_id=chunk_id,
                start_idx=len(sentences) - len(current_chunk),
                end_idx=len(sentences) - 1,
                metadata=chunk_metadata,
                embeddings=np.mean(current_embeddings, axis=0)
            ))
        
        return chunks
    
    def _create_semantic_chunks_rule_based(
        self,
        sentences: List[str],
        metadata: Optional[Dict[str, Any]]
    ) -> List[SemanticChunk]:
        """Create chunks using rule-based semantic grouping."""
        chunks = []
        current_chunk = []
        current_size = 0
        
        # Keywords that indicate topic transitions
        transition_keywords = [
            'however', 'furthermore', 'additionally', 'moreover',
            'on the other hand', 'in contrast', 'alternatively',
            'in conclusion', 'to summarize', 'first', 'second',
            'finally', 'next', 'then', 'therefore', 'thus'
        ]
        
        for i, sent in enumerate(sentences):
            sent_size = len(sent)
            sent_lower = sent.lower()
            
            # Check for semantic boundary
            is_boundary = any(
                keyword in sent_lower[:50]  # Check beginning of sentence
                for keyword in transition_keywords
            )
            
            # Check if we should create a new chunk
            should_split = False
            
            if current_chunk:
                if current_size + sent_size > self.max_chunk_size:
                    should_split = True
                elif is_boundary and current_size >= self.min_chunk_size:
                    should_split = True
            
            if should_split and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk_id = self._generate_chunk_id(chunk_text)
                
                chunk_metadata = {
                    'sentence_count': len(current_chunk),
                    'chunk_size': current_size,
                    'chunk_index': len(chunks),
                    'semantic_boundary': True,
                    **(metadata or {})
                }
                
                chunks.append(SemanticChunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    start_idx=i - len(current_chunk),
                    end_idx=i - 1,
                    metadata=chunk_metadata
                ))
                
                # Start new chunk
                current_chunk = [sent]
                current_size = sent_size
            else:
                current_chunk.append(sent)
                current_size += sent_size
        
        # Add remaining sentences
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_id = self._generate_chunk_id(chunk_text)
            
            chunk_metadata = {
                'sentence_count': len(current_chunk),
                'chunk_size': current_size,
                'chunk_index': len(chunks),
                'semantic_boundary': False,
                **(metadata or {})
            }
            
            chunks.append(SemanticChunk(
                content=chunk_text,
                chunk_id=chunk_id,
                start_idx=len(sentences) - len(current_chunk),
                end_idx=len(sentences) - 1,
                metadata=chunk_metadata
            ))
        
        return chunks
    
    def _calculate_avg_similarity(self, embeddings: List[np.ndarray]) -> float:
        """Calculate average pairwise similarity within embeddings."""
        if len(embeddings) < 2:
            return 1.0
            
        embeddings_array = np.array(embeddings)
        similarities = cosine_similarity(embeddings_array)
        
        # Get upper triangle (excluding diagonal)
        upper_triangle = np.triu(similarities, k=1)
        non_zero_count = np.count_nonzero(upper_triangle)
        
        if non_zero_count > 0:
            return np.sum(upper_triangle) / non_zero_count
        return 1.0
    
    def _generate_chunk_id(self, text: str) -> str:
        """Generate unique ID for chunk."""
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def merge_small_chunks(
        self,
        chunks: List[SemanticChunk],
        min_size: int = None
    ) -> List[SemanticChunk]:
        """Merge chunks that are too small."""
        if min_size is None:
            min_size = self.min_chunk_size
            
        merged_chunks = []
        current_merge = None
        
        for chunk in chunks:
            chunk_size = len(chunk.content)
            
            if chunk_size < min_size and current_merge:
                # Merge with previous
                current_merge.content += ' ' + chunk.content
                current_merge.end_idx = chunk.end_idx
                current_merge.metadata['sentence_count'] += chunk.metadata.get('sentence_count', 1)
                current_merge.metadata['chunk_size'] = len(current_merge.content)
            else:
                if current_merge:
                    merged_chunks.append(current_merge)
                current_merge = chunk
        
        if current_merge:
            merged_chunks.append(current_merge)
            
        return merged_chunks