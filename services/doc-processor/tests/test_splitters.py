"""Tests for document splitting strategies."""

import pytest
from splitters import (
    ParentChildSplitter,
    SemanticSplitter,
    RecursiveCharacterSplitter,
    DocumentChunk,
    SemanticChunk,
    RecursiveChunk
)


class TestParentChildSplitter:
    """Test parent-child splitting strategy."""
    
    def test_basic_splitting(self):
        """Test basic parent-child splitting."""
        text = "This is a test document. " * 100  # ~2500 chars
        
        splitter = ParentChildSplitter(
            parent_chunk_size=500,
            child_chunk_size=100,
            parent_overlap=50,
            child_overlap=10
        )
        
        chunks = splitter.split_document(text)
        
        # Should have both parent and child chunks
        parent_chunks = [c for c in chunks if c.level == 0]
        child_chunks = [c for c in chunks if c.level == 1]
        
        assert len(parent_chunks) > 0
        assert len(child_chunks) > 0
        
        # Each parent should have children
        for parent in parent_chunks:
            assert len(parent.children_ids) > 0
            
        # Each child should have a parent
        for child in child_chunks:
            assert child.parent_id is not None
    
    def test_section_extraction(self):
        """Test section extraction from markdown."""
        text = """# Section 1
This is section 1 content.

## Subsection 1.1
This is subsection content.

# Section 2
This is section 2 content."""
        
        splitter = ParentChildSplitter(preserve_structure=True)
        chunks = splitter.split_document(text)
        
        # Check that sections are preserved in metadata
        for chunk in chunks:
            if chunk.level == 0:  # Parent chunks
                assert 'section_title' in chunk.metadata
                assert chunk.metadata['section_title'] in ['Section 1', 'Subsection 1.1', 'Section 2']
    
    def test_chunk_tree_generation(self):
        """Test chunk tree generation."""
        text = "Test document. " * 200
        
        splitter = ParentChildSplitter()
        chunks = splitter.split_document(text)
        tree = splitter.get_chunk_tree(chunks)
        
        assert 'parents' in tree
        assert 'total_chunks' in tree
        assert 'total_parents' in tree
        assert 'total_children' in tree
        
        assert tree['total_chunks'] == len(chunks)
        assert tree['total_parents'] + tree['total_children'] == len(chunks)
    
    def test_empty_document(self):
        """Test handling of empty document."""
        splitter = ParentChildSplitter()
        chunks = splitter.split_document("")
        
        assert len(chunks) == 0
    
    def test_small_document(self):
        """Test handling of small document."""
        text = "This is a very small document."
        
        splitter = ParentChildSplitter(
            parent_chunk_size=1000,
            child_chunk_size=500
        )
        chunks = splitter.split_document(text)
        
        # Small doc should still create at least one parent and child
        assert len(chunks) >= 2
        assert any(c.level == 0 for c in chunks)
        assert any(c.level == 1 for c in chunks)


class TestSemanticSplitter:
    """Test semantic splitting strategy."""
    
    def test_rule_based_splitting(self):
        """Test rule-based semantic splitting without embeddings."""
        text = """First, let me introduce the topic.
This is an important concept to understand.
Furthermore, we need to consider additional factors.
However, there are some exceptions to this rule.
In conclusion, the main points are clear."""
        
        splitter = SemanticSplitter(
            max_chunk_size=100,
            min_chunk_size=30
        )
        chunks = splitter.split_document(text)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert isinstance(chunk, SemanticChunk)
            assert len(chunk.content) <= 100
    
    def test_transition_detection(self):
        """Test detection of semantic transitions."""
        text = """This is the first topic discussed here.
We continue with more details about it.
However, now we move to a different topic.
This new topic is quite different.
Finally, we conclude with a summary."""
        
        splitter = SemanticSplitter(
            max_chunk_size=200,
            min_chunk_size=50
        )
        chunks = splitter.split_document(text)
        
        # Should create multiple chunks based on transitions
        assert len(chunks) >= 2
        
        # Check metadata
        for chunk in chunks:
            assert 'sentence_count' in chunk.metadata
            assert 'chunk_size' in chunk.metadata
    
    def test_merge_small_chunks(self):
        """Test merging of small chunks."""
        text = "Short. Very short. Tiny."
        
        splitter = SemanticSplitter(min_chunk_size=50)
        chunks = splitter.split_document(text)
        
        # Initial chunks might be small
        merged = splitter.merge_small_chunks(chunks, min_size=50)
        
        # After merging, chunks should meet minimum size
        for chunk in merged:
            if chunk != merged[-1]:  # Except possibly the last chunk
                assert len(chunk.content) >= 50 or chunk == merged[-1]


class TestRecursiveCharacterSplitter:
    """Test recursive character splitting."""
    
    def test_basic_recursive_split(self):
        """Test basic recursive splitting."""
        text = """Paragraph one with some content.

Paragraph two with more content.

Paragraph three with additional content."""
        
        splitter = RecursiveCharacterSplitter(
            chunk_size=50,
            chunk_overlap=10
        )
        chunks = splitter.split_document(text)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert isinstance(chunk, RecursiveChunk)
            # Check chunk size (allowing for overlap)
            assert len(chunk.content) <= 60  # chunk_size + overlap
    
    def test_separator_hierarchy(self):
        """Test that separators are used in order."""
        text = "Word1 Word2. Sentence two. Another sentence.\n\nNew paragraph here."
        
        splitter = RecursiveCharacterSplitter(
            chunk_size=30,
            separators=["\n\n", ". ", " "]
        )
        chunks = splitter.split_document(text)
        
        # Should split first by paragraphs, then sentences, then words
        assert len(chunks) >= 2
        
        # Check depth tracking
        for chunk in chunks:
            assert 'depth' in chunk.metadata
            assert chunk.depth >= 0
    
    def test_overlap_functionality(self):
        """Test overlap between chunks."""
        text = "The quick brown fox jumps over the lazy dog. " * 5
        
        splitter = RecursiveCharacterSplitter(
            chunk_size=50,
            chunk_overlap=20
        )
        chunks = splitter.split_document(text)
        
        # Check that chunks have overlap
        for i in range(len(chunks) - 1):
            # End of chunk i should overlap with beginning of chunk i+1
            if 'has_overlap' in chunks[i + 1].metadata:
                assert chunks[i + 1].metadata['has_overlap'] is True
    
    def test_header_based_splitting(self):
        """Test splitting based on headers."""
        text = """# Header 1
Content for section 1.

## Header 1.1
Subsection content.

# Header 2
Content for section 2."""
        
        headers = [
            (r'^#\s+(.+)$', 'h1'),
            (r'^##\s+(.+)$', 'h2')
        ]
        
        splitter = RecursiveCharacterSplitter(
            chunk_size=100,
            is_separator_regex=True
        )
        chunks = splitter.split_with_headers(text, headers)
        
        # Should split by headers
        assert len(chunks) >= 3
        
        # Check section metadata
        for chunk in chunks:
            assert 'section_name' in chunk.metadata
            assert 'section_level' in chunk.metadata
    
    def test_keep_separator_option(self):
        """Test keeping vs discarding separators."""
        text = "Part1. Part2. Part3."
        
        # With keeping separator
        splitter_keep = RecursiveCharacterSplitter(
            chunk_size=10,
            separators=[". "],
            keep_separator=True
        )
        chunks_keep = splitter_keep.split_document(text)
        
        # Without keeping separator
        splitter_no_keep = RecursiveCharacterSplitter(
            chunk_size=10,
            separators=[". "],
            keep_separator=False
        )
        chunks_no_keep = splitter_no_keep.split_document(text)
        
        # Both should split the text
        assert len(chunks_keep) > 0
        assert len(chunks_no_keep) > 0


@pytest.fixture
def sample_document():
    """Provide a sample document for testing."""
    return """# Introduction

This document provides an overview of our compliance framework. 
It covers various aspects of regulatory requirements and best practices.

## Key Principles

First, we must ensure data privacy and protection.
Second, we need to maintain transparency in our operations.
Third, regular audits are essential for compliance.

## Implementation Guidelines

The implementation process involves several steps:

1. Assessment of current state
2. Gap analysis  
3. Remediation planning
4. Execution and monitoring

### Technical Requirements

Systems must meet specific technical standards.
Encryption is mandatory for sensitive data.
Access controls should follow the principle of least privilege.

## Conclusion

In summary, compliance requires continuous effort and monitoring.
Regular updates to policies and procedures are necessary.
Training and awareness programs help maintain compliance culture."""


def test_integration_with_sample_document(sample_document):
    """Test all splitters with a real document."""
    
    # Test Parent-Child Splitter
    pc_splitter = ParentChildSplitter(
        parent_chunk_size=500,
        child_chunk_size=150
    )
    pc_chunks = pc_splitter.split_document(sample_document)
    assert len(pc_chunks) > 0
    assert any(c.level == 0 for c in pc_chunks)  # Has parents
    assert any(c.level == 1 for c in pc_chunks)  # Has children
    
    # Test Semantic Splitter
    sem_splitter = SemanticSplitter(
        max_chunk_size=300,
        min_chunk_size=100
    )
    sem_chunks = sem_splitter.split_document(sample_document)
    assert len(sem_chunks) > 0
    for chunk in sem_chunks:
        assert 100 <= len(chunk.content) <= 300 or chunk == sem_chunks[-1]
    
    # Test Recursive Splitter
    rec_splitter = RecursiveCharacterSplitter(
        chunk_size=250,
        chunk_overlap=50
    )
    rec_chunks = rec_splitter.split_document(sample_document)
    assert len(rec_chunks) > 0
    for chunk in rec_chunks:
        assert len(chunk.content) <= 300  # chunk_size + overlap


if __name__ == "__main__":
    pytest.main([__file__, "-v"])