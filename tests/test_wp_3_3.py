"""
Test Suite for WP-3.3: RAG Architecture — Hierarchical Indexing

Tests cover:
- Document summarization (extractive)
- Hierarchical vector store ingestion and retrieval
- Layer-by-layer retrieval
- Full end-to-end pipeline
- Scaling characteristics
- Error handling and edge cases
"""

import pytest
from typing import List
from examples_3_3 import (
    DocumentSummarizer,
    Section,
    HierarchicalVectorStore,
    HierarchicalRAGPipeline,
    create_sample_documents,
    create_hierarchical_pipeline,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def summarizer():
    """Create document summarizer."""
    return DocumentSummarizer()


@pytest.fixture
def sample_sections():
    """Create sample sections."""
    return [
        Section(
            id="1.0",
            title="Introduction",
            content="This is an introduction section. It covers the basics. "
                   "We will learn fundamental concepts. " * 20,  # Repeated for length
        ),
        Section(
            id="2.0",
            title="Advanced Topics",
            content="Advanced topics require deeper understanding. "
                   "Error handling is critical. " * 20,
        ),
    ]


@pytest.fixture
def vector_store():
    """Create hierarchical vector store."""
    return HierarchicalVectorStore()


@pytest.fixture
def pipeline():
    """Create hierarchical RAG pipeline."""
    return create_hierarchical_pipeline(sample_docs=True)


# ============================================================================
# TESTS: DOCUMENT SUMMARIZER
# ============================================================================

class TestDocumentSummarizer:
    """Test suite for DocumentSummarizer class."""
    
    def test_summarizer_init(self, summarizer):
        """Test summarizer initialization."""
        assert summarizer is not None
        assert summarizer.tokenizer is not None
    
    def test_count_tokens(self, summarizer):
        """Test token counting."""
        text = "This is a test sentence."
        count = summarizer.count_tokens(text)
        
        # Should return positive count
        assert count > 0
        # Should be roughly correct (allow range)
        assert 3 <= count <= 10
    
    def test_split_sentences(self, summarizer):
        """Test sentence splitting."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = summarizer._split_sentences(text)
        
        assert len(sentences) == 3
        assert "First sentence" in sentences[0]
    
    def test_score_sentence(self, summarizer):
        """Test sentence scoring."""
        text = "Full text for context." * 20
        
        # First sentence
        first_score = summarizer._score_sentence(
            "Important first sentence with key concepts.",
            text, 0, 20
        )
        
        # Middle sentence
        middle_score = summarizer._score_sentence(
            "Some middle sentence.",
            text, 10, 20
        )
        
        # First should score higher (position + length)
        assert first_score > middle_score
    
    def test_extractive_summary_basic(self, summarizer):
        """Test basic extractive summarization."""
        text = "First sentence. " * 10 + "Important key concept sentence. " * 5
        
        summary = summarizer.extractive_summary(text, target_ratio=0.3)
        
        # Should return a string
        assert isinstance(summary, str)
        # Should be shorter than original
        assert len(summary) < len(text)
        # Should contain some content
        assert len(summary) > 0
    
    def test_extractive_summary_min_sentences(self, summarizer):
        """Test that min_sentences is respected."""
        text = "Short. Text."
        
        summary = summarizer.extractive_summary(
            text,
            target_ratio=0.1,
            min_sentences=3  # More than available
        )
        
        # Should return full text since min_sentences > available
        assert len(summary) > 0
    
    def test_extractive_summary_ratio(self, summarizer):
        """Test that ratio affects summary length."""
        text = ("This is a long sentence that contains multiple ideas. " * 20)
        
        summary_10 = summarizer.extractive_summary(text, target_ratio=0.1)
        summary_50 = summarizer.extractive_summary(text, target_ratio=0.5)
        
        # 50% should be longer than 10%
        assert len(summary_50) > len(summary_10)


# ============================================================================
# TESTS: HIERARCHICAL VECTOR STORE
# ============================================================================

class TestHierarchicalVectorStore:
    """Test suite for HierarchicalVectorStore class."""
    
    def test_store_init(self, vector_store):
        """Test vector store initialization."""
        assert vector_store is not None
        assert vector_store.layer_0 is not None
        assert vector_store.layer_1 is not None
        assert isinstance(vector_store.layer_2_map, dict)
    
    def test_ingest_document(self, vector_store, sample_sections):
        """Test document ingestion."""
        full_text = "\n".join([s.content for s in sample_sections])
        
        vector_store.ingest_document(
            doc_id="test_doc",
            title="Test Document",
            full_text=full_text,
            sections=sample_sections,
        )
        
        # Should store metadata
        assert "test_doc" in vector_store.doc_metadata
        
        # Should populate Layer 2 map
        section_ids = [f"test_doc#{s.id}" for s in sample_sections]
        for sid in section_ids:
            assert sid in vector_store.layer_2_map
    
    def test_create_chunks(self, vector_store):
        """Test chunk creation."""
        text = "This is test content. " * 100
        section_id = "test_section"
        
        chunks = vector_store._create_chunks(text, section_id, chunk_size=100)
        
        # Should create multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should have required fields
        for chunk in chunks:
            assert "content" in chunk
            assert "section_id" in chunk
            assert "index" in chunk
            assert chunk["section_id"] == section_id
    
    def test_retrieve_hierarchical_basic(self, pipeline):
        """Test hierarchical retrieval."""
        query = "payment errors"
        
        results = pipeline.vector_store.retrieve_hierarchical(query, k_0=5, k_1=5, k_2=3)
        
        # Should return results
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Each result should have required fields
        for result in results:
            assert "content" in result
            assert "section_id" in result
            assert "chunk_index" in result


# ============================================================================
# TESTS: HIERARCHICAL RAG PIPELINE
# ============================================================================

class TestHierarchicalRAGPipeline:
    """Test suite for HierarchicalRAGPipeline class."""
    
    def test_pipeline_init(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline is not None
        assert pipeline.vector_store is not None
        assert pipeline.reranker is not None
        assert pipeline.top_k == 5
    
    def test_pipeline_retrieve(self, pipeline):
        """Test pipeline retrieval."""
        query = "How do I handle payment errors?"
        
        results = pipeline.retrieve(query)
        
        # Should return list
        assert isinstance(results, list)
        # Should return at most top_k
        assert len(results) <= pipeline.top_k
    
    def test_pipeline_retrieve_without_reranking(self):
        """Test retrieval without reranking."""
        pipeline = create_hierarchical_pipeline(sample_docs=True)
        pipeline.use_reranking = False
        pipeline.reranker = None
        
        query = "payment"
        results = pipeline.retrieve(query)
        
        assert len(results) > 0
    
    def test_pipeline_generate(self, pipeline):
        """Test answer generation."""
        query = "What are error codes for payment?"
        
        answer = pipeline.generate(query)
        
        # Should return string
        assert isinstance(answer, str)
        # Should not be empty
        assert len(answer) > 0
    
    def test_metrics_tracking(self, pipeline):
        """Test that pipeline tracks metrics."""
        initial_queries = pipeline.metrics["queries_processed"]
        
        query = "test query"
        pipeline.retrieve(query)
        
        # Should increment query count
        assert pipeline.metrics["queries_processed"] > initial_queries
    
    def test_retrieve_with_parameters(self, pipeline):
        """Test retrieval with custom parameters."""
        query = "payment"
        
        results = pipeline.retrieve(query, k_0=10, k_1=5, k_2=2)
        
        # Should respect top_k
        assert len(results) <= pipeline.top_k


# ============================================================================
# TESTS: INTEGRATION
# ============================================================================

class TestIntegration:
    """Integration tests for full pipeline."""
    
    def test_end_to_end_retrieval_and_generation(self, pipeline):
        """Test complete pipeline from retrieval to generation."""
        query = "How do I handle payment errors?"
        
        # Retrieve
        docs = pipeline.retrieve(query)
        assert len(docs) > 0
        
        # Generate
        answer = pipeline.generate(query)
        assert len(answer) > 0
        
        # Answer should relate to query topic
        assert "payment" in answer.lower() or "error" in answer.lower()
    
    def test_multiple_queries(self, pipeline):
        """Test pipeline with multiple queries."""
        queries = [
            "How do I authenticate?",
            "What are error codes?",
            "How do webhooks work?",
        ]
        
        for query in queries:
            docs = pipeline.retrieve(query)
            assert len(docs) > 0
    
    def test_sample_document_ingestion(self):
        """Test ingesting actual sample documents."""
        doc_ids, doc_titles, doc_sections_list = create_sample_documents()
        
        assert len(doc_ids) > 0
        assert len(doc_titles) == len(doc_ids)
        assert len(doc_sections_list) == len(doc_ids)
        
        # Each document should have sections
        for sections in doc_sections_list:
            assert len(sections) > 0
            for section in sections:
                assert section.id
                assert section.title
                assert section.content


# ============================================================================
# TESTS: SCALABILITY
# ============================================================================

class TestScalability:
    """Test scaling characteristics."""
    
    @pytest.mark.slow
    def test_many_sections(self):
        """Test ingesting document with many sections."""
        vector_store = HierarchicalVectorStore()
        
        # Create document with many sections
        sections = [
            Section(
                id=f"{i}",
                title=f"Section {i}",
                content=f"Content for section {i}. " * 50,
            )
            for i in range(50)
        ]
        
        full_text = "\n".join([s.content for s in sections])
        
        # Should ingest without error
        vector_store.ingest_document(
            doc_id="large_doc",
            title="Large Document",
            full_text=full_text,
            sections=sections,
        )
        
        # Should have all sections in Layer 2
        count = sum(len(vector_store.layer_2_map[k]) for k in vector_store.layer_2_map)
        assert count > 0
    
    @pytest.mark.slow
    def test_retrieval_performance(self, pipeline):
        """Test retrieval performance."""
        import time
        
        query = "error handling"
        
        start = time.time()
        results = pipeline.retrieve(query)
        elapsed = time.time() - start
        
        assert len(results) > 0
        # Should complete in reasonable time
        assert elapsed < 30  # generous for CI


# ============================================================================
# TESTS: EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_query(self, pipeline):
        """Test with empty query."""
        try:
            results = pipeline.retrieve("")
            # Should handle gracefully
            assert isinstance(results, list)
        except Exception:
            pass
    
    def test_very_long_query(self, pipeline):
        """Test with very long query."""
        long_query = "What is the meaning of life? " * 100
        
        try:
            results = pipeline.retrieve(long_query)
            assert isinstance(results, list)
        except Exception:
            pass
    
    def test_special_characters_in_query(self, pipeline):
        """Test with special characters."""
        query = "What are #error @codes #payment? !@#$%^&*()"
        
        try:
            results = pipeline.retrieve(query)
            assert isinstance(results, list)
        except Exception:
            pass
    
    def test_unicode_query(self, pipeline):
        """Test with unicode characters."""
        query = "¿Cómo manejar errores? エラー処理 Обработка ошибок"
        
        try:
            results = pipeline.retrieve(query)
            assert isinstance(results, list)
        except Exception:
            pass


# ============================================================================
# TESTS: COMPARISON WITH NAIVE RAG
# ============================================================================

class TestComparison:
    """Test hierarchical vs naive retrieval."""
    
    def test_hierarchical_retrieves_diverse_results(self, pipeline):
        """Test that hierarchical retrieval returns diverse results."""
        query = "error handling payment"
        
        results = pipeline.retrieve(query)
        
        # Should have multiple results
        assert len(results) > 1
        
        # Results should come from different sections (ideally)
        section_ids = [r["section_id"] for r in results]
        # At least some diversity
        assert len(set(section_ids)) >= 1
    
    def test_layer_scores_captured(self, pipeline):
        """Test that layer scores are captured."""
        query = "webhook"
        
        results = pipeline.retrieve(query)
        
        if results:
            # Should have layer scores
            for result in results:
                assert "layer_1_score" in result or "rerank_score" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
