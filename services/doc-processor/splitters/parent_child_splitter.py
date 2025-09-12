"""Parent-child document splitting strategy for hierarchical chunking."""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
import json


@dataclass
class DocumentChunk:
    """Represents a document chunk with metadata."""
    content: str
    chunk_id: str
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    metadata: Dict[str, Any] = None
    chunk_type: str = "text"  # text, table, image
    level: int = 0  # 0 for parent, 1 for child
    
    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []
        if self.metadata is None:
            self.metadata = {}


class ParentChildSplitter:
    """Implements parent-child document splitting strategy.
    
    Parent chunks: ~2000 characters (semantic boundaries)
    Child chunks: ~500 characters (fine-grained content)
    """
    
    def __init__(
        self,
        parent_chunk_size: int = 2000,
        child_chunk_size: int = 500,
        parent_overlap: int = 200,
        child_overlap: int = 50,
        preserve_structure: bool = True
    ):
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.parent_overlap = parent_overlap
        self.child_overlap = child_overlap
        self.preserve_structure = preserve_structure
        
    def split_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """Split document into hierarchical parent-child chunks.
        
        Args:
            text: Document text to split
            metadata: Optional document metadata
            
        Returns:
            List of DocumentChunk objects with parent-child relationships
        """
        if not text:
            return []
            
        # Extract document structure if enabled
        if self.preserve_structure:
            sections = self._extract_sections(text)
        else:
            sections = [("Document", text, 0)]
            
        all_chunks = []
        
        for section_title, section_text, section_level in sections:
            # Create parent chunks for this section
            parent_chunks = self._create_parent_chunks(
                section_text,
                section_title,
                section_level,
                metadata
            )
            
            # Create child chunks for each parent
            for parent_chunk in parent_chunks:
                child_chunks = self._create_child_chunks(
                    parent_chunk.content,
                    parent_chunk.chunk_id,
                    parent_chunk.metadata
                )
                
                # Link children to parent
                parent_chunk.children_ids = [child.chunk_id for child in child_chunks]
                
                all_chunks.append(parent_chunk)
                all_chunks.extend(child_chunks)
                
        return all_chunks
    
    def _extract_sections(self, text: str) -> List[Tuple[str, str, int]]:
        """Extract document sections based on headers and structure.
        
        Returns:
            List of (section_title, section_text, level) tuples
        """
        sections = []
        
        # Markdown header patterns
        header_patterns = [
            (r'^#{1}\s+(.+)$', 1),
            (r'^#{2}\s+(.+)$', 2),
            (r'^#{3}\s+(.+)$', 3),
            (r'^#{4,}\s+(.+)$', 4),
        ]
        
        lines = text.split('\n')
        current_section = []
        current_title = "Introduction"
        current_level = 0
        
        for line in lines:
            header_found = False
            
            for pattern, level in header_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    # Save previous section
                    if current_section:
                        sections.append((
                            current_title,
                            '\n'.join(current_section),
                            current_level
                        ))
                    
                    # Start new section
                    current_title = match.group(1)
                    current_level = level
                    current_section = []
                    header_found = True
                    break
            
            if not header_found:
                current_section.append(line)
        
        # Add final section
        if current_section:
            sections.append((
                current_title,
                '\n'.join(current_section),
                current_level
            ))
        
        return sections if sections else [("Document", text, 0)]
    
    def _create_parent_chunks(
        self,
        text: str,
        section_title: str,
        section_level: int,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """Create parent chunks from section text."""
        chunks = []
        
        # Split by paragraphs first for semantic boundaries
        paragraphs = self._split_paragraphs(text)
        
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # If adding this paragraph exceeds parent size, create chunk
            if current_size + para_size > self.parent_chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunk_id = self._generate_chunk_id(chunk_text)
                
                chunk_metadata = {
                    'section_title': section_title,
                    'section_level': section_level,
                    'chunk_size': len(chunk_text),
                    'chunk_index': len(chunks),
                    **(metadata or {})
                }
                
                chunks.append(DocumentChunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    metadata=chunk_metadata,
                    level=0
                ))
                
                # Start new chunk with overlap
                if self.parent_overlap > 0 and current_chunk:
                    # Keep last paragraph for overlap
                    current_chunk = [current_chunk[-1], para]
                    current_size = len(current_chunk[0]) + para_size
                else:
                    current_chunk = [para]
                    current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Add remaining content
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunk_id = self._generate_chunk_id(chunk_text)
            
            chunk_metadata = {
                'section_title': section_title,
                'section_level': section_level,
                'chunk_size': len(chunk_text),
                'chunk_index': len(chunks),
                **(metadata or {})
            }
            
            chunks.append(DocumentChunk(
                content=chunk_text,
                chunk_id=chunk_id,
                metadata=chunk_metadata,
                level=0
            ))
        
        return chunks
    
    def _create_child_chunks(
        self,
        parent_text: str,
        parent_id: str,
        parent_metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """Create child chunks from parent chunk text."""
        chunks = []
        
        # Split into sentences for fine-grained chunks
        sentences = self._split_sentences(parent_text)
        
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # If adding this sentence exceeds child size, create chunk
            if current_size + sentence_size > self.child_chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunk_id = self._generate_chunk_id(chunk_text)
                
                chunk_metadata = {
                    **parent_metadata,
                    'parent_chunk_id': parent_id,
                    'child_chunk_size': len(chunk_text),
                    'child_chunk_index': len(chunks)
                }
                
                chunks.append(DocumentChunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    parent_id=parent_id,
                    metadata=chunk_metadata,
                    level=1
                ))
                
                # Start new chunk with overlap
                if self.child_overlap > 0 and current_chunk:
                    # Keep last sentence for overlap
                    current_chunk = [current_chunk[-1], sentence]
                    current_size = len(current_chunk[0]) + sentence_size
                else:
                    current_chunk = [sentence]
                    current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add remaining content
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_id = self._generate_chunk_id(chunk_text)
            
            chunk_metadata = {
                **parent_metadata,
                'parent_chunk_id': parent_id,
                'child_chunk_size': len(chunk_text),
                'child_chunk_index': len(chunks)
            }
            
            chunks.append(DocumentChunk(
                content=chunk_text,
                chunk_id=chunk_id,
                parent_id=parent_id,
                metadata=chunk_metadata,
                level=1
            ))
        
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split by double newlines or single newlines with next line starting with space/tab
        paragraphs = re.split(r'\n\n+|\n(?=[\t ])', text)
        # Filter out empty paragraphs
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting (can be enhanced with NLTK/spaCy)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _generate_chunk_id(self, text: str) -> str:
        """Generate unique ID for chunk based on content hash."""
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def get_chunk_tree(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """Build hierarchical tree structure from chunks.
        
        Returns:
            Dictionary representing chunk hierarchy
        """
        tree = {
            'parents': [],
            'total_chunks': len(chunks),
            'total_parents': sum(1 for c in chunks if c.level == 0),
            'total_children': sum(1 for c in chunks if c.level == 1)
        }
        
        # Build parent-child map
        for chunk in chunks:
            if chunk.level == 0:  # Parent chunk
                parent_node = {
                    'id': chunk.chunk_id,
                    'title': chunk.metadata.get('section_title', 'Unknown'),
                    'size': len(chunk.content),
                    'children': []
                }
                
                # Find children
                for child in chunks:
                    if child.parent_id == chunk.chunk_id:
                        parent_node['children'].append({
                            'id': child.chunk_id,
                            'size': len(child.content)
                        })
                
                tree['parents'].append(parent_node)
        
        return tree