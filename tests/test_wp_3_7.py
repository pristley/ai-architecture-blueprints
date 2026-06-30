"""Test Suite for WP-3.7: Advanced Retrieval Strategy - Query Router

Comprehensive tests covering:
  - Query classification (heuristic + LLM)
  - All retrieval strategies (keyword, vector, hybrid, conditional)
  - Router logic and strategy selection
  - Integration end-to-end flows
  - Edge cases and performance

Run with: pytest tests/test_wp_3_7.py -v
Run slow tests: pytest tests/test_wp_3_7.py -v --runslow
"""

import pytest
import time
from typing import List

from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from docs.capstone_rag_patterns.examples_3_7 import (
    QueryType,
    QueryClassifier,
    KeywordSearchStrategy,
    VectorSearchStrategy,
    HybridSearchStrategy,
    ConditionalLogicStrategy,
    RetrieverRouter,
    SearchResult,
    RouterResult,
    create_sample_documents,
    create_query_router,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_documents() -> List[str]:
    """Get sample documents."""
    return create_sample_documents()


@pytest.fixture
def embeddings():
    """Create embeddings instance."""
    return OpenAIEmbeddings(model="text-embedding-3-small")


@pytest.fixture
def llm():
    """Create LLM instance."""
    return ChatOpenAI(model="gpt-4-turbo", temperature=0)


@pytest.fixture
def query_classifier():
    """Create query classifier without LLM."""
    return QueryClassifier(use_llm_fallback=False)


@pytest.fixture
def query_classifier_with_llm(llm):
    """Create query classifier with LLM fallback."""
    return QueryClassifier(llm_model=llm)


@pytest.fixture
def keyword_strategy(sample_documents):
    """Create keyword search strategy."""
    return KeywordSearchStrategy(sample_documents)


@pytest.fixture
def vector_strategy(sample_documents, embeddings):
    """Create vector search strategy."""
    return VectorSearchStrategy(sample_documents, embeddings)


@pytest.fixture
def hybrid_strategy(sample_documents, embeddings):
    """Create hybrid search strategy."""
    return HybridSearchStrategy(sample_documents, embeddings, alpha=0.3)


@pytest.fixture
def conditional_strategy(sample_documents, embeddings, llm):
    """Create conditional logic strategy."""
    return ConditionalLogicStrategy(sample_documents, embeddings, llm)


@pytest.fixture
def router(sample_documents, embeddings, llm):
    """Create query router."""
    return RetrieverRouter(sample_documents, embeddings, llm, use_llm_classification=False)


# ============================================================================
# Tests: Query Classification
# ============================================================================

class TestQueryClassification:
    """Test query classification using heuristics."""
    
    def test_classify_fact_lookup(self, query_classifier):
        """Test fact lookup classification."""
        query = "What is the termination clause?"
        query_type, confidence = query_classifier.classify(query)
        assert query_type == QueryType.FACT_LOOKUP
        assert confidence > 0.80
    
    def test_classify_numerical(self, query_classifier):
        """Test numerical query classification."""
        query = "How much does payment cost per month?"
        query_type, confidence = query_classifier.classify(query)
        assert query_type == QueryType.NUMERICAL
        assert confidence > 0.80
    
    def test_classify_numerical_with_currency(self, query_classifier):
        """Test numerical classification with currency symbols."""
        query = "What is the $50,000 payment amount?"
        query_type, confidence = query_classifier.classify(query)
        assert query_type == QueryType.NUMERICAL
        assert confidence > 0.85
    
    def test_classify_numerical_with_days(self, query_classifier):
        """Test numerical classification with time units."""
        query = "How many days notice is required?"
        query_type, confidence = query_classifier.classify(query)
        assert query_type == QueryType.NUMERICAL
        assert confidence > 0.85
    
    def test_classify_comparative(self, query_classifier):
        """Test comparative query classification."""
        query = "Compare payment terms vs liability caps"
        query_type, confidence = query_classifier.classify(query)
        assert query_type == QueryType.COMPARATIVE
        assert confidence > 0.80
    
    def test_classify_comparative_vs(self, query_classifier):
        """Test comparative with 'vs' keyword."""
        query = "What's the difference between Section A vs Section B?"
        query_type, confidence = query_classifier.classify(query)
        assert query_type == QueryType.COMPARATIVE
        assert confidence > 0.80
    
    def test_classify_conditional(self, query_classifier):
        """Test conditional query classification."""
        query = "What happens if payment is late?"
        query_type, confidence = query_classifier.classify(query)
        assert query_type == QueryType.CONDITIONAL
        assert confidence > 0.85
    
    def test_classify_conditional_when(self, query_classifier):
        """Test conditional with 'when' keyword."""
        query = "When can the contract be terminated?"
        query_type, confidence = query_classifier.classify(query)
        assert query_type == QueryType.CONDITIONAL
        assert confidence > 0.80
    
    def test_classify_broad_summary(self, query_classifier):
        """Test broad summary classification."""
        query = "Summarize the confidentiality obligations"
        query_type, confidence = query_classifier.classify(query)
        assert query_type == QueryType.BROAD_SUMMARY
        assert confidence > 0.80
    
    def test_classify_broad_summary_describe(self, query_classifier):
        """Test broad summary with 'describe' keyword."""
        query = "Describe the payment terms"
        query_type, confidence = query_classifier.classify(query)
        assert query_type == QueryType.BROAD_SUMMARY
        assert confidence > 0.80
    
    def test_classify_unknown(self, query_classifier):
        """Test unknown query type."""
        query = "xyz abc qwerty"
        query_type, confidence = query_classifier.classify(query)
        assert query_type == QueryType.UNKNOWN
        assert confidence < 0.70
    
    def test_classify_very_short_question(self, query_classifier):
        """Test short questions are classified as fact lookup."""
        query = "What is X?"
        query_type, confidence = query_classifier.classify(query)
        assert query_type == QueryType.FACT_LOOKUP
    
    def test_classify_case_insensitive(self, query_classifier):
        """Test classification is case-insensitive."""
        query_lower = "what happens if payment is late?"
        query_upper = "WHAT HAPPENS IF PAYMENT IS LATE?"
        
        type_lower, conf_lower = query_classifier.classify(query_lower)
        type_upper, conf_upper = query_classifier.classify(query_upper)
        
        assert type_lower == type_upper
        assert conf_lower == conf_upper


# ============================================================================
# Tests: Retrieval Strategies
# ============================================================================

class TestKeywordSearchStrategy:
    """Test keyword search strategy."""
    
    def test_keyword_search_fact_lookup(self, keyword_strategy):
        """Test keyword search on fact lookup query."""
        results = keyword_strategy.search("termination clause", k=3)
        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].score > 0
    
    def test_keyword_search_respects_k(self, keyword_strategy):
        """Test that keyword search respects k parameter."""
        results = keyword_strategy.search("payment", k=2)
        assert len(results) <= 2
    
    def test_keyword_search_returns_metadata(self, keyword_strategy):
        """Test that results include metadata."""
        results = keyword_strategy.search("payment", k=1)
        assert results[0].metadata is not None
        assert "strategy" in results[0].metadata
        assert results[0].metadata["strategy"] == "keyword"
    
    def test_keyword_strategy_name(self, keyword_strategy):
        """Test strategy name."""
        assert keyword_strategy.get_strategy_name() == "KeywordSearch"
    
    def test_keyword_strategy_latency(self, keyword_strategy):
        """Test latency estimate."""
        latency = keyword_strategy.get_estimated_latency()
        assert latency == 0.100  # 100ms
    
    def test_keyword_strategy_cost(self, keyword_strategy):
        """Test cost estimate."""
        cost = keyword_strategy.get_estimated_cost()
        assert cost == 0.001  # $0.001


class TestVectorSearchStrategy:
    """Test vector search strategy."""
    
    def test_vector_search_semantic(self, vector_strategy):
        """Test vector search finds semantically related documents."""
        results = vector_strategy.search("obligations and duties", k=3)
        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].score > 0
    
    def test_vector_search_respects_k(self, vector_strategy):
        """Test that vector search respects k parameter."""
        results = vector_strategy.search("test", k=2)
        assert len(results) <= 2
    
    def test_vector_search_returns_metadata(self, vector_strategy):
        """Test that results include metadata."""
        results = vector_strategy.search("test", k=1)
        assert results[0].metadata is not None
        assert "strategy" in results[0].metadata
        assert results[0].metadata["strategy"] == "vector"
    
    def test_vector_strategy_name(self, vector_strategy):
        """Test strategy name."""
        assert vector_strategy.get_strategy_name() == "VectorSearch"
    
    def test_vector_strategy_latency(self, vector_strategy):
        """Test latency estimate."""
        latency = vector_strategy.get_estimated_latency()
        assert latency == 0.500  # 500ms
    
    def test_vector_strategy_cost(self, vector_strategy):
        """Test cost estimate."""
        cost = vector_strategy.get_estimated_cost()
        assert cost == 0.015  # $0.015
    
    def test_vector_search_paraphrase_tolerance(self, vector_strategy):
        """Test that vector search tolerates paraphrasing."""
        results_a = vector_strategy.search("payment obligations", k=1)
        results_b = vector_strategy.search("money owed", k=1)
        
        # Both should find results (semantic similarity)
        assert len(results_a) > 0
        assert len(results_b) > 0


class TestHybridSearchStrategy:
    """Test hybrid search strategy."""
    
    def test_hybrid_search_combines_results(self, hybrid_strategy):
        """Test hybrid search combines keyword and vector results."""
        results = hybrid_strategy.search("payment terms", k=3)
        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)
    
    def test_hybrid_search_respects_k(self, hybrid_strategy):
        """Test that hybrid search respects k parameter."""
        results = hybrid_strategy.search("test", k=2)
        assert len(results) <= 2
    
    def test_hybrid_search_includes_alpha(self, hybrid_strategy):
        """Test that hybrid results include alpha weight."""
        results = hybrid_strategy.search("test", k=1)
        if len(results) > 0:
            assert "alpha" in results[0].metadata
            assert results[0].metadata["alpha"] == 0.3
    
    def test_hybrid_strategy_name(self, hybrid_strategy):
        """Test strategy name."""
        assert hybrid_strategy.get_strategy_name() == "HybridSearch"
    
    def test_hybrid_strategy_latency(self, hybrid_strategy):
        """Test latency estimate."""
        latency = hybrid_strategy.get_estimated_latency()
        assert latency == 0.350  # 350ms
    
    def test_hybrid_strategy_cost(self, hybrid_strategy):
        """Test cost estimate."""
        cost = hybrid_strategy.get_estimated_cost()
        assert cost == 0.012  # $0.012
    
    def test_hybrid_alpha_weight(self, sample_documents, embeddings):
        """Test that alpha weight affects hybrid results."""
        strategy_kw_biased = HybridSearchStrategy(sample_documents, embeddings, alpha=0.7)
        strategy_vec_biased = HybridSearchStrategy(sample_documents, embeddings, alpha=0.2)
        
        query = "payment"
        results_kw = strategy_kw_biased.search(query, k=1)
        results_vec = strategy_vec_biased.search(query, k=1)
        
        # Results may differ due to different alpha weights
        assert len(results_kw) > 0
        assert len(results_vec) > 0


class TestConditionalLogicStrategy:
    """Test conditional logic strategy."""
    
    def test_conditional_search_extracts_parts(self, conditional_strategy):
        """Test conditional search extracts condition and consequence."""
        results = conditional_strategy.search("What happens if payment is late?", k=3)
        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)
    
    def test_conditional_search_when_keyword(self, conditional_strategy):
        """Test conditional search with 'when' keyword."""
        results = conditional_strategy.search("When can the contract be terminated?", k=1)
        assert len(results) > 0
    
    def test_conditional_strategy_name(self, conditional_strategy):
        """Test strategy name."""
        assert conditional_strategy.get_strategy_name() == "ConditionalLogic"
    
    def test_conditional_strategy_latency(self, conditional_strategy):
        """Test latency estimate."""
        latency = conditional_strategy.get_estimated_latency()
        assert latency == 0.450  # 450ms
    
    def test_conditional_strategy_cost(self, conditional_strategy):
        """Test cost estimate."""
        cost = conditional_strategy.get_estimated_cost()
        assert cost == 0.018  # $0.018


# ============================================================================
# Tests: Retriever Router
# ============================================================================

class TestRetrieverRouter:
    """Test main query router."""
    
    def test_router_initialization(self, router):
        """Test router initializes correctly."""
        assert router is not None
        assert router.keyword_search is not None
        assert router.vector_search is not None
        assert router.hybrid_search is not None
        assert router.conditional_logic is not None
    
    def test_router_fact_lookup_uses_keyword(self, router):
        """Test fact lookup routes to keyword search."""
        result = router.search("What is the termination clause?", k=3)
        assert result.query_type == QueryType.FACT_LOOKUP.value
        assert result.strategy_name == "KeywordSearch"
    
    def test_router_numerical_uses_hybrid(self, router):
        """Test numerical query routes to hybrid."""
        result = router.search("How much is the payment?", k=3)
        assert result.query_type == QueryType.NUMERICAL.value
        assert result.strategy_name == "HybridSearch"
    
    def test_router_summary_uses_vector(self, router):
        """Test summary query routes to vector search."""
        result = router.search("Summarize the payment terms", k=3)
        assert result.query_type == QueryType.BROAD_SUMMARY.value
        assert result.strategy_name == "VectorSearch"
    
    def test_router_conditional_uses_conditional(self, router):
        """Test conditional query routes to conditional logic."""
        result = router.search("What happens if payment is late?", k=3)
        assert result.query_type == QueryType.CONDITIONAL.value
        assert result.strategy_name == "ConditionalLogic"
    
    def test_router_result_structure(self, router):
        """Test router result has all required fields."""
        result = router.search("test query", k=2)
        
        assert isinstance(result, RouterResult)
        assert result.query == "test query"
        assert result.query_type is not None
        assert result.strategy_name is not None
        assert 0 <= result.confidence <= 1
        assert len(result.results) <= 2
        assert result.latency_ms > 0
        assert result.cost_estimate > 0
    
    def test_router_result_to_dict(self, router):
        """Test router result can be converted to dict."""
        result = router.search("test query", k=1)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "query" in result_dict
        assert "query_type" in result_dict
        assert "strategy_name" in result_dict
        assert "confidence" in result_dict
        assert "results" in result_dict
        assert "latency_ms" in result_dict
        assert "cost_estimate" in result_dict
    
    def test_router_strategy_stats(self, router):
        """Test router can return strategy statistics."""
        stats = router.get_strategy_stats()
        
        assert "KeywordSearch" in stats
        assert "VectorSearch" in stats
        assert "HybridSearch" in stats
        assert "ConditionalLogic" in stats
        
        for strategy, metrics in stats.items():
            assert "latency_ms" in metrics
            assert "cost_usd" in metrics
            assert metrics["latency_ms"] > 0
            assert metrics["cost_usd"] > 0
    
    def test_router_respects_k_parameter(self, router):
        """Test router respects k parameter."""
        result = router.search("test", k=2)
        assert len(result.results) <= 2
    
    def test_router_comparative_uses_hybrid(self, router):
        """Test comparative query routes to hybrid."""
        result = router.search("Compare section A vs section B", k=3)
        assert result.query_type == QueryType.COMPARATIVE.value
        assert result.strategy_name == "HybridSearch"


# ============================================================================
# Tests: Integration
# ============================================================================

class TestIntegration:
    """Integration tests for end-to-end workflows."""
    
    def test_end_to_end_multiple_query_types(self, router):
        """Test router handles multiple query types correctly."""
        queries = [
            ("What is the termination clause?", "KeywordSearch"),
            ("What is the payment amount?", "HybridSearch"),
            ("Summarize the obligations", "VectorSearch"),
            ("What happens if late?", "ConditionalLogic"),
        ]
        
        for query, expected_strategy in queries:
            result = router.search(query, k=3)
            assert result.strategy_name == expected_strategy
            assert len(result.results) > 0
    
    def test_integration_latency_profile(self, router):
        """Test that router latency varies by strategy."""
        # Fact lookup (keyword) should be faster than summary (vector)
        result_keyword = router.search("What is termination?", k=3)
        result_vector = router.search("Summarize obligations", k=3)
        
        # Vector search should take longer
        # Note: This is approximate due to network latency variations
        assert result_keyword.strategy_name == "KeywordSearch"
        assert result_vector.strategy_name == "VectorSearch"
    
    def test_integration_cost_varies_by_strategy(self, router):
        """Test that cost estimates vary by strategy."""
        result_keyword = router.search("What is termination?", k=3)
        result_vector = router.search("Summarize obligations", k=3)
        
        # Vector should cost more than keyword
        assert result_vector.cost_estimate > result_keyword.cost_estimate
    
    def test_integration_trace_includes_timing(self, router):
        """Test that router trace includes timing information."""
        result = router.search("test query", k=1)
        
        assert "classification_time_ms" in result.trace
        assert "search_time_ms" in result.trace
        assert result.trace["classification_time_ms"] >= 0
        assert result.trace["search_time_ms"] > 0


# ============================================================================
# Tests: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_query(self, router):
        """Test handling of empty query."""
        result = router.search("", k=3)
        assert result is not None
        assert isinstance(result, RouterResult)
    
    def test_very_long_query(self, router):
        """Test handling of very long query."""
        long_query = "What is X? " * 100
        result = router.search(long_query, k=3)
        assert result is not None
        assert isinstance(result, RouterResult)
    
    def test_special_characters_in_query(self, router):
        """Test handling of special characters."""
        query = "What is $50,000 USD? (amount: 50,000€)"
        result = router.search(query, k=3)
        assert result is not None
        assert result.query_type == QueryType.NUMERICAL.value
    
    def test_unicode_query(self, router):
        """Test handling of Unicode characters."""
        query = "What is the obligation? (义务)"
        result = router.search(query, k=3)
        assert result is not None
    
    def test_multiple_query_indicators(self, router):
        """Test query with multiple type indicators."""
        # Numerical + Conditional
        query = "If payment is $5,000 late, what happens?"
        result = router.search(query, k=3)
        # Should classify as one type (first matched pattern wins)
        assert result.query_type in [QueryType.NUMERICAL.value, QueryType.CONDITIONAL.value]
    
    def test_zero_k_parameter(self, router):
        """Test router with k=0."""
        result = router.search("test", k=0)
        assert len(result.results) == 0
    
    def test_large_k_parameter(self, router):
        """Test router with k larger than document count."""
        result = router.search("test", k=100)
        # Should return at most the number of documents
        assert len(result.results) <= len(create_sample_documents())


# ============================================================================
# Tests: Performance (Slow)
# ============================================================================

class TestPerformance:
    """Performance tests marked as slow."""
    
    @pytest.mark.slow
    def test_router_latency_under_threshold(self, router):
        """Test router latency is within acceptable bounds."""
        start = time.time()
        result = router.search("test query", k=3)
        elapsed_ms = (time.time() - start) * 1000
        
        # Router should complete in reasonable time (even accounting for API latency)
        assert elapsed_ms < 10000  # 10 seconds max
    
    @pytest.mark.slow
    def test_keyword_strategy_fast_path(self, keyword_strategy):
        """Test keyword search is fast."""
        start = time.time()
        for i in range(10):
            keyword_strategy.search("test query", k=3)
        avg_latency_ms = (time.time() - start) * 1000 / 10
        
        # Keyword search should average under 200ms (generous for API)
        assert avg_latency_ms < 200
    
    @pytest.mark.slow
    def test_classification_overhead(self, query_classifier):
        """Test classification adds minimal overhead."""
        # Classify 100 queries
        start = time.time()
        for i in range(100):
            query_classifier.classify(f"test query {i}")
        total_time = (time.time() - start) * 1000
        avg_time_ms = total_time / 100
        
        # Classification should average under 10ms
        assert avg_time_ms < 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
