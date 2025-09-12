"""Recursive character text splitter with hierarchy preservation."""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib


@dataclass
class RecursiveChunk:
    """Represents a recursively split chunk."""
    content: str
    chunk_id: str
    separators_used: List[str]
    depth: int
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RecursiveCharacterSplitter:
    """Recursively split text using a hierarchy of separators.
    
    Similar to LangChain's RecursiveCharacterTextSplitter but with
    enhanced metadata tracking and structure preservation.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        separators: Optional[List[str]] = None,
        keep_separator: bool = True,
        is_separator_regex: bool = False
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.keep_separator = keep_separator
        self.is_separator_regex = is_separator_regex
        
        # Default separators in order of preference
        if separators is None:
            self.separators = [
                "\n\n\n",  # Triple newline (major sections)
                "\n\n",    # Double newline (paragraphs)
                "\n",      # Single newline
                ". ",      # Sentence endings
                ", ",      # Clause separators
                " ",       # Words
                ""         # Characters (last resort)
            ]
        else:
            self.separators = separators
    
    def split_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[RecursiveChunk]:
        """Split document recursively using separator hierarchy.
        
        Args:
            text: Document text to split
            metadata: Optional document metadata
            
        Returns:
            List of RecursiveChunk objects
        """
        if not text:
            return []
            
        # Start recursive splitting
        chunks = self._recursive_split(
            text,
            self.separators,
            depth=0,
            metadata=metadata
        )
        
        # Post-process chunks
        final_chunks = self._merge_and_overlap(chunks)
        
        return final_chunks
    
    def _recursive_split(
        self,
        text: str,
        separators: List[str],
        depth: int,
        metadata: Optional[Dict[str, Any]]
    ) -> List[RecursiveChunk]:
        """Recursively split text using separators."""
        chunks = []
        
        # Base case: no more separators or text is small enough
        if not separators or len(text) <= self.chunk_size:
            if text.strip():
                chunk_id = self._generate_chunk_id(text)
                chunk_metadata = {
                    'depth': depth,
                    'chunk_size': len(text),
                    **(metadata or {})
                }
                
                return [RecursiveChunk(
                    content=text,
                    chunk_id=chunk_id,
                    separators_used=[],
                    depth=depth,
                    metadata=chunk_metadata
                )]
            return []
        
        # Try current separator
        separator = separators[0]
        remaining_separators = separators[1:]
        
        # Split by current separator
        if self.is_separator_regex:
            splits = re.split(separator, text)
        else:
            splits = text.split(separator)
        
        # Process each split
        current_chunk = []
        current_size = 0
        separators_used = [separator]
        
        for i, split in enumerate(splits):
            split_size = len(split)
            
            # Check if adding this split exceeds chunk size
            if current_size + split_size > self.chunk_size and current_chunk:
                # Create chunk from accumulated splits
                if self.keep_separator and separator and i > 0:
                    chunk_text = separator.join(current_chunk)
                else:
                    chunk_text = ''.join(current_chunk)
                
                # Recursively split if still too large
                if len(chunk_text) > self.chunk_size and remaining_separators:
                    sub_chunks = self._recursive_split(
                        chunk_text,
                        remaining_separators,
                        depth + 1,
                        metadata
                    )
                    chunks.extend(sub_chunks)
                else:
                    chunk_id = self._generate_chunk_id(chunk_text)
                    chunk_metadata = {
                        'depth': depth,
                        'chunk_size': len(chunk_text),
                        'separator': separator,
                        **(metadata or {})
                    }
                    
                    chunks.append(RecursiveChunk(
                        content=chunk_text,
                        chunk_id=chunk_id,
                        separators_used=separators_used,
                        depth=depth,
                        metadata=chunk_metadata
                    ))
                
                # Start new chunk
                current_chunk = [split]
                current_size = split_size
            else:
                current_chunk.append(split)
                current_size += split_size + (len(separator) if self.keep_separator else 0)
        
        # Handle remaining content
        if current_chunk:
            if self.keep_separator and separator:
                chunk_text = separator.join(current_chunk)
            else:
                chunk_text = ''.join(current_chunk)
            
            # Recursively split if needed
            if len(chunk_text) > self.chunk_size and remaining_separators:
                sub_chunks = self._recursive_split(
                    chunk_text,
                    remaining_separators,
                    depth + 1,
                    metadata
                )
                chunks.extend(sub_chunks)
            elif chunk_text.strip():
                chunk_id = self._generate_chunk_id(chunk_text)
                chunk_metadata = {
                    'depth': depth,
                    'chunk_size': len(chunk_text),
                    'separator': separator,
                    **(metadata or {})
                }
                
                chunks.append(RecursiveChunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    separators_used=separators_used,
                    depth=depth,
                    metadata=chunk_metadata
                ))
        
        return chunks
    
    def _merge_and_overlap(self, chunks: List[RecursiveChunk]) -> List[RecursiveChunk]:
        """Merge small chunks and add overlap between chunks."""
        if not chunks:
            return []
            
        final_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Add overlap from previous chunk if needed
            if i > 0 and self.chunk_overlap > 0:
                prev_chunk = chunks[i - 1]
                overlap_text = self._get_overlap_text(
                    prev_chunk.content,
                    self.chunk_overlap
                )
                
                if overlap_text:
                    # Prepend overlap to current chunk
                    chunk.content = overlap_text + ' ' + chunk.content
                    chunk.metadata['has_overlap'] = True
                    chunk.metadata['overlap_size'] = len(overlap_text)
            
            # Update chunk size in metadata
            chunk.metadata['final_size'] = len(chunk.content)
            final_chunks.append(chunk)
        
        return final_chunks
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Extract overlap text from end of previous chunk."""
        if len(text) <= overlap_size:
            return text
            
        # Try to find a good break point (word boundary)
        overlap_text = text[-overlap_size:]
        
        # Find first space to avoid cutting words
        first_space = overlap_text.find(' ')
        if first_space > 0:
            overlap_text = overlap_text[first_space + 1:]
            
        return overlap_text.strip()
    
    def _generate_chunk_id(self, text: str) -> str:
        """Generate unique ID for chunk."""
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def split_with_headers(
        self,
        text: str,
        headers_to_split_on: List[Tuple[str, str]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[RecursiveChunk]:
        """Split text based on headers/sections.
        
        Args:
            text: Document text
            headers_to_split_on: List of (header_pattern, header_name) tuples
            metadata: Optional metadata
            
        Returns:
            List of chunks split by headers
        """
        chunks = []
        sections = self._split_by_headers(text, headers_to_split_on)
        
        for section_name, section_text, section_level in sections:
            section_metadata = {
                'section_name': section_name,
                'section_level': section_level,
                **(metadata or {})
            }
            
            # Recursively split each section
            section_chunks = self.split_document(
                section_text,
                section_metadata
            )
            
            chunks.extend(section_chunks)
        
        return chunks
    
    def _split_by_headers(
        self,
        text: str,
        headers_to_split_on: List[Tuple[str, str]]
    ) -> List[Tuple[str, str, int]]:
        """Split text by header patterns.
        
        Returns:
            List of (section_name, section_text, level) tuples
        """
        sections = []
        lines = text.split('\n')
        
        current_section = []
        current_name = "Introduction"
        current_level = 0
        
        for line in lines:
            header_found = False
            
            for level, (pattern, name_template) in enumerate(headers_to_split_on):
                if self.is_separator_regex:
                    match = re.match(pattern, line)
                else:
                    match = line.startswith(pattern)
                    
                if match:
                    # Save previous section
                    if current_section:
                        sections.append((
                            current_name,
                            '\n'.join(current_section),
                            current_level
                        ))
                    
                    # Extract header name
                    if self.is_separator_regex and hasattr(match, 'group'):
                        current_name = match.group(1) if match.groups() else line
                    else:
                        current_name = line.replace(pattern, '').strip()
                    
                    current_level = level
                    current_section = []
                    header_found = True
                    break
            
            if not header_found:
                current_section.append(line)
        
        # Add final section
        if current_section:
            sections.append((
                current_name,
                '\n'.join(current_section),
                current_level
            ))
        
        return sections if sections else [("Document", text, 0)]