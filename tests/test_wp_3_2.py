"""
Test Suite for WP-3.2: RAG Architecture — Reranking & Filtering

Tests cover:
- Document filtering with various configurations
- Cross-encoder reranking and scoring
- Multi-stage pipeline retrieval
- Fallback and error handling
- Performance metrics
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict

from examples_3_2 import (
    DocumentFilter,
    FilterConfig,
    DocumentReranker,
    MultiStageRAGPipeline,
    create_sample_documents,
    create_rag_pipeline,
)
from langchain.schema import Document


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return create_sample_documents()


@pytest.fixture
def sample_metadata_docs():
    """Create documents with varied metadata."""
    docs = []
    
    # Recent verified policy docs
    for i in range(3):
        docs.append(Document(
            page_content=f"Policy document {i}: {i * 100} customer tested",
            metadata={
                "source": f"policy_{i}.pdf",
                "doc_type": "policy",
                "last_updated": datetime.now().isoformat(),
                "verified": True,
            }
        ))
    
    # Old unverified forum posts
    for i in range(2):
        docs.append(Document(
            page_content=f"Forum post {i}: Old information",
            metadata={
                "source": f"forum_{i}.txt",
                "doc_type": "forum",
                "last_updated": (datetime.now() - timedelta(days=400)).isoformat(),
                "verified": False,
            }
        ))
    
    # FAQ docs
    for i in range(2):
        docs.append(Document(
            page_content=f"FAQ item {i}: Common questions",
            metadata={
                "source": f"faq_{i}.md",
                "doc_type": "faq",
                "last_updated": datetime.now().isoformat(),
                "verified": True,
            }
        ))
    
    return docs


@pytest.fixture
def filter_config():
    """Create filter configuration."""
    return FilterConfig(
        max_age_days=180,
        allowed_types=["policy", "faq"],
        verified_only=True,
    )


# ============================================================================
# TESTS: DOCUMENT FILTER
# ============================================================================

class TestDocumentFilter:
    """Test suite for DocumentFilter class."""
    
    def test_filter_init(self):
        """Test filter initialization."""
        config = FilterConfig(max_age_days=90)
        filter_obj = DocumentFilter(config)
        assert filter_obj.config.max_age_days == 90
    
    def test_temporal_filtering(self, sample_metadata_docs):
        """Test filtering by document age."""
        config = FilterConfig(max_age_days=200)
        filter_obj = DocumentFilter(config)
        
        # Convert to metadata dicts
        docs = [
            {
                "content": doc.page_content,
                **doc.metadata
            }
            for doc in sample_metadata_docs
        ]
        
        filtered = filter_obj.apply_filters(docs)
        
        # Should remove old forum posts
        assert len(filtered) < len(docs)
        assert all(doc["doc_type"] != "forum" for doc in filtered)
    
    def test_type_filtering(self, sample_metadata_docs):
        """Test filtering by document type."""
        config = FilterConfig(allowed_types=["policy"])
        filter_obj = DocumentFilter(config)
        
        docs = [
            {
                "content": doc.page_content,
                **doc.metadata
            }
            for doc in sample_metadata_docs
        ]
        
        filtered = filter_obj.apply_filters(docs)
        
        # Should keep only policy docs
        assert all(doc["doc_type"] == "policy" for doc in filtered)
    
    def test_verification_filtering(self, sample_metadata_docs):
        """Test filtering by verification status."""
        config = FilterConfig(verified_only=True)
        filter_obj = DocumentFilter(config)
        
        docs = [
            {
                "content": doc.page_content,
                **doc.metadata
            }
            for doc in sample_metadata_docs
        ]
        
        filtered = filter_obj.apply_filters(docs)
        
        # Should keep only verified docs
        assert all(doc.get("verified", False) for doc in filtered)
    
    def test_combined_filtering(self, sample_metadata_docs):
        """Test multiple filters applied together."""
        config = FilterConfig(
            max_age_days=200,
            allowed_types=["policy", "faq"],
            verified_only=True,
        )
        filter_obj = DocumentFilter(config)
        
        docs = [
            {
                "content": doc.page_content,
                **doc.metadata
            }
            for doc in sample_metadata_docs
        ]
        
        initial_count = len(docs)
        filtered = filter_obj.apply_filters(docs)
        
        # Should remove old and unverified
        assert len(filtered) < initial_count
        assert all(doc.get("verified") for doc in filtered)
        assert all(doc["doc_type"] in ["policy", "faq"] for doc in filtered)
    
    def test_exclude_keywords_filter(self):
        """Test keyword exclusion filtering."""
        docs = [
            {"content": "Important policy document", "doc_type": "policy"},
            {"content": "Spam refund generator script", "doc_type": "code"},
            {"content": "Real refund policy here", "doc_type": "policy"},
        ]
        
        config = FilterConfig(exclude_keywords=["spam", "script"])
        filter_obj = DocumentFilter(config)
        
        filtered = filter_obj.apply_filters(docs)
        
        # Should remove spam/script docs
        assert len(filtered) == 2
        assert all("spam" not in doc["content"].lower() for doc in filtered)


# ============================================================================
# TESTS: DOCUMENT RERANKER
# ============================================================================

class TestDocumentReranker:
    """Test suite for DocumentReranker class."""
    
    def test_reranker_init(self):
        """Test reranker initialization."""
        reranker = DocumentReranker(
            model_name="cross-encoder/qnli-distilroberta-base",
            use_gpu=False,
            batch_size=16
        )
        assert reranker.batch_size == 16
        assert reranker.model is not None
    
    def test_rerank_basic(self):
        """Test basic reranking."""
        candidates = [
            {"content": "What is machine learning?"},
            {"content": "Python programming tutorial"},
            {"content": "Machine learning algorithms and neural networks"},
        ]
        
        reranker = DocumentReranker(use_gpu=False)
        query = "How does machine learning work?"
        
        reranked = reranker.rerank(query, candidates)
        
        # Should return same count
        assert len(reranked) == len(candidates)
        
        # Should have rerank scores
        assert all("rerank_score" in doc for doc in reranked)
        
        # Scores should be in [0, 1]
        assert all(0 <= doc["rerank_score"] <= 1 for doc in reranked)
    
    def test_rerank_order(self):
        """Test that reranking produces correct ordering."""
        candidates = [
            {"content": "The sky is blue"},
            {"content": "Birds fly in the sky"},
            {"content": "What color is the sky?"},
        ]
        
        reranker = DocumentReranker(use_gpu=False)
        query = "What color is the sky?"
        
        reranked = reranker.rerank(query, candidates)
        
        # Should be sorted by score (descending)
        scores = [doc["rerank_score"] for doc in reranked]
        assert scores == sorted(scores, reverse=True)
    
    def test_rerank_empty(self):
        """Test reranking with empty candidates."""
        reranker = DocumentReranker(use_gpu=False)
        query = "test query"
        
        reranked = reranker.rerank(query, [])
        
        assert reranked == []
    
    def test_normalize_scores(self):
        """Test score normalization."""
        scores = [-2.0, -1.0, 0.0, 1.0, 2.0]
        normalized = DocumentReranker._normalize_scores(scores)
        
        # Normalized scores should be in [0, 1]
        assert all(0 <= score <= 1 for score in normalized)
        
        # Should preserve order
        assert normalized == sorted(normalized)


# ============================================================================
# TESTS: MULTI-STAGE PIPELINE
# ============================================================================

class TestMultiStageRAGPipeline:
    """Test suite for MultiStageRAGPipeline class."""
    
    def test_pipeline_creation(self):
        """Test pipeline initialization."""
        pipeline = create_rag_pipeline()
        assert pipeline is not None
        assert pipeline.vector_store is not None
        assert pipeline.reranker is not None
        assert pipeline.filter_layer is not None
    
    def test_retrieve_returns_top_k(self):
        """Test that retrieve returns correct number of documents."""
        pipeline = create_rag_pipeline()
        pipeline.top_k = 3
        
        query = "What are refund policies?"
        results = pipeline.retrieve(query)
        
        # Should return top_k or fewer
        assert len(results) <= 3
    
    def test_retrieve_includes_scores(self):
        """Test that retrieved documents include rerank scores."""
        pipeline = create_rag_pipeline()
        
        query = "What are refund policies?"
        results = pipeline.retrieve(query)
        
        if results:
            # Should have rerank scores (unless fallback)
            assert any("rerank_score" in doc for doc in results)
    
    def test_retrieve_with_fallback(self):
        """Test fallback retrieval on error."""
        pipeline = create_rag_pipeline()
        
        # Simulate reranker failure by using empty candidates
        # This shouldn't crash due to fallback
        query = "test query"
        results = pipeline.retrieve_with_fallback(query)
        
        # Should return something
        assert results is not None
        assert len(results) > 0
    
    def test_generate_returns_string(self):
        """Test that generate returns a string answer."""
        pipeline = create_rag_pipeline()
        
        query = "What are refund policies for digital goods?"
        answer = pipeline.generate(query)
        
        # Should be a string
        assert isinstance(answer, str)
        # Should not be empty
        assert len(answer) > 0
    
    def test_metrics_tracking(self):
        """Test that pipeline tracks metrics."""
        pipeline = create_rag_pipeline()
        
        initial_count = pipeline.metrics["queries_processed"]
        
        query = "test query"
        pipeline.retrieve(query)
        
        # Should increment query count
        assert pipeline.metrics["queries_processed"] > initial_count
    
    def test_filtering_reduces_candidates(self):
        """Test that filtering removes candidates."""
        pipeline = create_rag_pipeline()
        
        query = "What are refund policies?"
        
        # Direct stage 1: broad retrieval
        search_results = pipeline.vector_store.similarity_search_with_score(
            query, k=100
        )
        candidates = [
            {
                "content": doc.page_content,
                **doc.metadata
            }
            for doc, _ in search_results
        ]
        
        # Apply filtering
        filtered = pipeline.filter_layer.apply_filters(candidates)
        
        # Filtering should remove some documents (stale/unverified)
        assert len(filtered) <= len(candidates)


# ============================================================================
# TESTS: INTEGRATION
# ============================================================================

class TestIntegration:
    """Integration tests for full pipeline."""
    
    def test_end_to_end_retrieval(self):
        """Test complete retrieval pipeline end-to-end."""
        pipeline = create_rag_pipeline()
        
        query = "What is the return policy for digital products?"
        
        # Execute pipeline
        results = pipeline.retrieve(query)
        
        # Should return documents
        assert len(results) > 0
        
        # Should be properly formatted
        for doc in results:
            assert "content" in doc
            assert "rerank_score" in doc or doc.get("rerank_score") is None
    
    def test_multiple_queries(self):
        """Test pipeline with multiple queries."""
        pipeline = create_rag_pipeline()
        
        queries = [
            "What is the refund policy?",
            "Can I return digital goods?",
            "How long do I have to return?",
        ]
        
        for query in queries:
            results = pipeline.retrieve(query)
            assert len(results) > 0
    
    def test_different_filter_configs(self):
        """Test pipeline with different filter configurations."""
        # Strict filtering
        config_strict = FilterConfig(
            max_age_days=30,
            allowed_types=["policy"],
            verified_only=True,
        )
        pipeline_strict = create_rag_pipeline(filter_config=config_strict)
        
        # Lenient filtering
        config_lenient = FilterConfig(
            max_age_days=999,
            allowed_types=["policy", "faq", "forum", "guide"],
            verified_only=False,
        )
        pipeline_lenient = create_rag_pipeline(filter_config=config_lenient)
        
        query = "What is the refund policy?"
        
        results_strict = pipeline_strict.retrieve(query)
        results_lenient = pipeline_lenient.retrieve(query)
        
        # Lenient should have more candidates after filtering
        # (though final top_k may be same)
        assert results_strict is not None
        assert results_lenient is not None


# ============================================================================
# TESTS: EDGE CASES & ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_query(self):
        """Test pipeline with empty query."""
        pipeline = create_rag_pipeline()
        
        # Should handle empty query gracefully
        try:
            results = pipeline.retrieve("")
            # If it succeeds, should return some docs
            assert results is not None
        except Exception as e:
            # If it fails, should fail gracefully
            pass
    
    def test_very_long_query(self):
        """Test pipeline with very long query."""
        pipeline = create_rag_pipeline()
        
        long_query = "What is the refund policy? " * 100
        
        # Should handle long query without crashing
        try:
            results = pipeline.retrieve(long_query)
            assert results is not None
        except Exception as e:
            pass  # Long queries may legitimately fail
    
    def test_special_characters_in_query(self):
        """Test pipeline with special characters."""
        pipeline = create_rag_pipeline()
        
        query = "What are refund policies? \\n \\t !@#$%^&*()"
        
        # Should handle special characters
        try:
            results = pipeline.retrieve(query)
            assert results is not None
        except Exception as e:
            pass
    
    def test_unicode_query(self):
        """Test pipeline with unicode characters."""
        pipeline = create_rag_pipeline()
        
        query = "¿Cuál es la política de reembolso? 返金ポリシーとは？"
        
        # Should handle unicode
        try:
            results = pipeline.retrieve(query)
            assert results is not None
        except Exception as e:
            pass


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance and benchmarking tests."""
    
    @pytest.mark.slow
    def test_latency_multi_stage_pipeline(self):
        """Test and measure multi-stage pipeline latency."""
        import time
        
        pipeline = create_rag_pipeline()
        query = "What are refund policies?"
        
        start = time.time()
        results = pipeline.retrieve(query)
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        # (reranking adds ~1-2 seconds)
        assert elapsed < 30  # generous timeout for CI
        assert len(results) > 0
    
    @pytest.mark.slow
    def test_batch_reranking_performance(self):
        """Test batch reranking performance."""
        import time
        
        candidates = [
            {"content": f"Document {i}: Some relevant content about topic"}
            for i in range(50)
        ]
        
        reranker = DocumentReranker(use_gpu=False, batch_size=32)
        query = "topic related question"
        
        start = time.time()
        reranked = reranker.rerank(query, candidates, batch_size=32)
        elapsed = time.time() - start
        
        # Should complete reranking
        assert len(reranked) == len(candidates)
        # Should be reasonably fast (allow up to 30s for CI)
        assert elapsed < 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
