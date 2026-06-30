"""
Test Suite for WP-3.4: RAG Architecture — Evaluation & Metrics

Tests cover:
- Retrieval evaluation metrics
- Answer quality evaluation
- Citation accuracy
- Latency profiling
- Cost analysis
- Comparison framework
"""

import pytest
import time
from examples_3_4 import (
    RetrievalEvaluator,
    AnswerEvaluator,
    LatencyProfiler,
    CostAnalyzer,
    EvaluationDataset,
    RAGComparison,
    EvaluationReport,
    RetrievalMetrics,
    AnswerMetrics,
    PerformanceMetrics,
    CostMetrics,
    create_evaluation_benchmark,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def retrieval_evaluator():
    """Create retrieval evaluator."""
    return RetrievalEvaluator()


@pytest.fixture
def latency_profiler():
    """Create latency profiler."""
    return LatencyProfiler()


@pytest.fixture
def cost_analyzer():
    """Create cost analyzer."""
    return CostAnalyzer()


@pytest.fixture
def evaluation_dataset():
    """Create evaluation dataset."""
    return create_evaluation_benchmark()


# ============================================================================
# TESTS: RETRIEVAL EVALUATOR
# ============================================================================

class TestRetrievalEvaluator:
    """Test suite for RetrievalEvaluator."""
    
    def test_evaluator_init(self, retrieval_evaluator):
        """Test evaluator initialization."""
        assert retrieval_evaluator is not None
    
    def test_precision_calculation(self, retrieval_evaluator):
        """Test precision@k calculation."""
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = {"a", "c"}
        
        metrics = retrieval_evaluator.evaluate(retrieved, list(relevant))
        
        # Precision@5 = 2/5 = 0.4
        assert metrics.precision_at_5 == 0.4
    
    def test_recall_calculation(self, retrieval_evaluator):
        """Test recall@k calculation."""
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = {"a", "c", "f"}  # 3 relevant total, only 2 in top-5
        
        metrics = retrieval_evaluator.evaluate(retrieved, list(relevant))
        
        # Recall@5 = 2/3 = 0.667
        assert abs(metrics.recall_at_5 - 0.667) < 0.01
    
    def test_mrr_calculation(self, retrieval_evaluator):
        """Test MRR (Mean Reciprocal Rank)."""
        retrieved = ["x", "y", "a", "b", "c"]
        relevant = {"a", "b"}
        
        metrics = retrieval_evaluator.evaluate(retrieved, list(relevant))
        
        # First relevant at position 3, MRR = 1/3
        assert abs(metrics.mrr - 0.333) < 0.01
    
    def test_mrr_no_relevant(self, retrieval_evaluator):
        """Test MRR when no relevant docs found."""
        retrieved = ["x", "y", "z"]
        relevant = {"a", "b"}
        
        metrics = retrieval_evaluator.evaluate(retrieved, list(relevant))
        
        assert metrics.mrr == 0.0
    
    def test_ndcg_calculation(self, retrieval_evaluator):
        """Test NDCG calculation."""
        retrieved = ["a", "b", "c"]
        relevant = {"a", "c"}
        
        metrics = retrieval_evaluator.evaluate(retrieved, list(relevant))
        
        # Should be between 0 and 1
        assert 0 <= metrics.ndcg_at_5 <= 1.0
    
    def test_perfect_ranking(self, retrieval_evaluator):
        """Test perfect ranking."""
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = {"a", "b", "c"}
        
        metrics = retrieval_evaluator.evaluate(retrieved, list(relevant))
        
        # Perfect ranking: precision=recall=1.0, MRR=1.0
        assert metrics.precision_at_5 == 1.0
        assert metrics.recall_at_5 == 1.0
        assert metrics.mrr == 1.0
    
    def test_worst_ranking(self, retrieval_evaluator):
        """Test worst ranking."""
        retrieved = ["x", "y", "z", "w"]
        relevant = {"a", "b"}
        
        metrics = retrieval_evaluator.evaluate(retrieved, list(relevant))
        
        # No relevant found
        assert metrics.precision_at_5 == 0.0
        assert metrics.recall_at_5 == 0.0
        assert metrics.mrr == 0.0


# ============================================================================
# TESTS: LATENCY PROFILER
# ============================================================================

class TestLatencyProfiler:
    """Test suite for LatencyProfiler."""
    
    def test_profiler_init(self, latency_profiler):
        """Test profiler initialization."""
        assert latency_profiler is not None
    
    def test_stage_timing(self, latency_profiler):
        """Test timing a single stage."""
        stage_id = latency_profiler.start_stage("embedding")
        time.sleep(0.05)
        elapsed = latency_profiler.end_stage(stage_id)
        
        # Should be roughly 0.05 seconds
        assert elapsed >= 0.04
    
    def test_multiple_stages(self, latency_profiler):
        """Test profiling multiple stages."""
        # Stage 1: embedding
        stage1 = latency_profiler.start_stage("embedding")
        time.sleep(0.05)
        latency_profiler.end_stage(stage1)
        
        # Stage 2: search
        stage2 = latency_profiler.start_stage("search")
        time.sleep(0.03)
        latency_profiler.end_stage(stage2)
        
        # Get metrics
        metrics = latency_profiler.get_metrics()
        
        # Total should be ~0.08 seconds
        assert metrics.total_latency >= 0.07
        assert metrics.embedding_latency >= 0.04
        assert metrics.search_latency >= 0.02
    
    def test_metrics_structure(self, latency_profiler):
        """Test metrics structure."""
        stage = latency_profiler.start_stage("generation")
        time.sleep(0.01)
        latency_profiler.end_stage(stage)
        
        metrics = latency_profiler.get_metrics()
        
        # Check all fields exist
        assert hasattr(metrics, 'total_latency')
        assert hasattr(metrics, 'embedding_latency')
        assert hasattr(metrics, 'generation_latency')


# ============================================================================
# TESTS: COST ANALYZER
# ============================================================================

class TestCostAnalyzer:
    """Test suite for CostAnalyzer."""
    
    def test_analyzer_init(self, cost_analyzer):
        """Test analyzer initialization."""
        assert cost_analyzer is not None
    
    def test_basic_cost_calculation(self, cost_analyzer):
        """Test basic cost calculation."""
        cost_metrics = cost_analyzer.calculate(
            query_tokens=50,
            doc_tokens=100,
            num_docs=5,
            input_prompt_tokens=500,
            output_tokens=50,
        )
        
        # Should have positive costs
        assert cost_metrics.embedding_cost > 0
        assert cost_metrics.llm_cost > 0
        assert cost_metrics.total_cost > 0
    
    def test_cost_breakdown(self, cost_analyzer):
        """Test cost breakdown structure."""
        cost_metrics = cost_analyzer.calculate(
            query_tokens=50,
            doc_tokens=100,
            num_docs=5,
            input_prompt_tokens=500,
            output_tokens=50,
        )
        
        breakdown = cost_metrics.breakdown()
        
        # Check all components present
        assert "embedding" in breakdown
        assert "llm" in breakdown
        assert "total" in breakdown
    
    def test_cost_scaling(self, cost_analyzer):
        """Test that cost scales with usage."""
        # Low usage
        cost1 = cost_analyzer.calculate(
            query_tokens=10,
            doc_tokens=50,
            num_docs=1,
            input_prompt_tokens=100,
            output_tokens=10,
        ).total_cost
        
        # High usage (10x)
        cost2 = cost_analyzer.calculate(
            query_tokens=100,
            doc_tokens=500,
            num_docs=10,
            input_prompt_tokens=1000,
            output_tokens=100,
        ).total_cost
        
        # Cost2 should be significantly higher
        assert cost2 > cost1 * 5  # Should be roughly 10x but allowing variance


# ============================================================================
# TESTS: EVALUATION DATASET
# ============================================================================

class TestEvaluationDataset:
    """Test suite for EvaluationDataset."""
    
    def test_dataset_creation(self):
        """Test dataset creation."""
        dataset = EvaluationDataset()
        assert len(dataset) == 0
    
    def test_add_sample(self):
        """Test adding samples."""
        dataset = EvaluationDataset()
        
        dataset.add_sample(
            query_id="q1",
            query="test query",
            expected_answer="test answer",
            relevant_doc_ids=["d1", "d2"],
            sources=[{"id": "d1", "content": "content"}],
        )
        
        assert len(dataset) == 1
    
    def test_dataset_iteration(self):
        """Test iterating over dataset."""
        dataset = EvaluationDataset()
        
        for i in range(3):
            dataset.add_sample(
                query_id=f"q{i}",
                query="query",
                expected_answer="answer",
                relevant_doc_ids=[f"d{i}"],
                sources=[],
            )
        
        count = 0
        for sample in dataset:
            count += 1
        
        assert count == 3
    
    def test_by_category(self):
        """Test filtering by category."""
        dataset = EvaluationDataset()
        
        dataset.add_sample(
            query_id="q1",
            query="q",
            expected_answer="a",
            relevant_doc_ids=[],
            sources=[],
            category="contract",
        )
        
        dataset.add_sample(
            query_id="q2",
            query="q",
            expected_answer="a",
            relevant_doc_ids=[],
            sources=[],
            category="financial",
        )
        
        contract_samples = dataset.by_category("contract")
        assert len(contract_samples) == 1
        assert contract_samples[0].category == "contract"


# ============================================================================
# TESTS: COMPARISON FRAMEWORK
# ============================================================================

class TestRAGComparison:
    """Test suite for RAG comparison."""
    
    def test_comparison_creation(self, evaluation_dataset):
        """Test comparison creation."""
        comparison = RAGComparison(evaluation_dataset)
        assert comparison is not None
    
    def test_add_result(self, evaluation_dataset):
        """Test adding results."""
        comparison = RAGComparison(evaluation_dataset)
        
        # Create sample metrics
        retrieval_metrics = [
            RetrievalMetrics(
                precision_at_5=0.8,
                precision_at_10=0.75,
                recall_at_5=0.7,
                recall_at_10=0.85,
                mrr=0.9,
                ndcg_at_5=0.8,
                ndcg_at_10=0.8,
            )
        ]
        
        answer_metrics = [
            AnswerMetrics(
                relevance_score=4.0,
                completeness_score=3.5,
                hallucination_rate=0.05,
                citation_accuracy=0.95,
            )
        ]
        
        perf_metrics = [
            PerformanceMetrics(
                total_latency=1.5,
                embedding_latency=0.1,
                search_latency=0.3,
                reranking_latency=0.0,
                generation_latency=1.0,
                other_latency=0.1,
            )
        ]
        
        cost_metrics = [
            CostMetrics(
                embedding_cost=0.001,
                search_cost=0.0,
                reranking_cost=0.0,
                llm_cost=0.01,
                total_cost=0.011,
            )
        ]
        
        comparison.add_result("naive_rag", retrieval_metrics, answer_metrics, perf_metrics, cost_metrics)
        
        assert "naive_rag" in comparison.results
    
    def test_comparison_summary(self, evaluation_dataset):
        """Test getting comparison summary."""
        comparison = RAGComparison(evaluation_dataset)
        
        # Add mock results for two RAGs
        for rag_name in ["rag_a", "rag_b"]:
            retrieval_metrics = [
                RetrievalMetrics(0.8, 0.75, 0.7, 0.85, 0.9, 0.8, 0.8)
            ]
            answer_metrics = [
                AnswerMetrics(4.0, 3.5, 0.05, 0.95)
            ]
            perf_metrics = [
                PerformanceMetrics(1.5, 0.1, 0.3, 0.0, 1.0, 0.1)
            ]
            cost_metrics = [
                CostMetrics(0.001, 0.0, 0.0, 0.01, 0.011)
            ]
            
            comparison.add_result(rag_name, retrieval_metrics, answer_metrics, perf_metrics, cost_metrics)
        
        summary = comparison.get_summary()
        
        assert len(summary) == 2
        assert "retrieval_score" in summary["rag_a"]


# ============================================================================
# TESTS: EVALUATION REPORT
# ============================================================================

class TestEvaluationReport:
    """Test suite for evaluation reports."""
    
    def test_report_generation(self):
        """Test report generation."""
        retrieval_metrics = [
            RetrievalMetrics(0.8, 0.75, 0.7, 0.85, 0.9, 0.8, 0.8)
        ]
        answer_metrics = [
            AnswerMetrics(4.0, 3.5, 0.05, 0.95)
        ]
        perf_metrics = [
            PerformanceMetrics(1.5, 0.1, 0.3, 0.0, 1.0, 0.1)
        ]
        cost_metrics = [
            CostMetrics(0.001, 0.0, 0.0, 0.01, 0.011)
        ]
        
        report = EvaluationReport.generate_report(
            rag_name="test_rag",
            dataset_size=100,
            retrieval_metrics=retrieval_metrics,
            answer_metrics=answer_metrics,
            performance_metrics=perf_metrics,
            cost_metrics=cost_metrics,
        )
        
        assert report["rag_name"] == "test_rag"
        assert report["dataset_size"] == 100
        assert "retrieval" in report
        assert "answer" in report
        assert "performance" in report
        assert "cost" in report


# ============================================================================
# TESTS: INTEGRATION
# ============================================================================

class TestIntegration:
    """Integration tests for evaluation framework."""
    
    def test_end_to_end_evaluation(self, evaluation_dataset):
        """Test complete evaluation pipeline."""
        retrieval_eval = RetrievalEvaluator()
        
        # Simulate retrieval
        retrieved = ["section_5.2", "section_4.1", "section_2.1"]
        relevant = ["section_5.2", "section_5.3"]
        
        metrics = retrieval_eval.evaluate(retrieved, relevant)
        
        # Should have valid metrics
        assert 0 <= metrics.precision_at_5 <= 1.0
        assert 0 <= metrics.recall_at_5 <= 1.0
        assert metrics.mrr >= 0
    
    def test_benchmark_dataset(self):
        """Test benchmark dataset creation."""
        dataset = create_evaluation_benchmark()
        
        assert len(dataset) > 0
        
        # Check structure
        for sample in dataset:
            assert sample.query_id
            assert sample.query
            assert sample.expected_answer


# ============================================================================
# TESTS: EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_retrieval_list(self, retrieval_evaluator):
        """Test with empty retrieval list."""
        metrics = retrieval_evaluator.evaluate([], ["a", "b"])
        
        assert metrics.precision_at_5 == 0.0
        assert metrics.mrr == 0.0
    
    def test_empty_relevant_list(self, retrieval_evaluator):
        """Test with empty relevant list."""
        metrics = retrieval_evaluator.evaluate(["a", "b", "c"], [])
        
        # Should handle gracefully
        assert isinstance(metrics, RetrievalMetrics)
    
    def test_large_dataset(self):
        """Test with large evaluation dataset."""
        dataset = EvaluationDataset()
        
        for i in range(1000):
            dataset.add_sample(
                query_id=f"q{i}",
                query=f"query {i}",
                expected_answer=f"answer {i}",
                relevant_doc_ids=[f"d{i}"],
                sources=[],
            )
        
        assert len(dataset) == 1000
    
    def test_zero_cost(self, cost_analyzer):
        """Test with zero tokens."""
        cost = cost_analyzer.calculate(
            query_tokens=0,
            doc_tokens=0,
            num_docs=0,
            input_prompt_tokens=0,
            output_tokens=0,
        )
        
        assert cost.total_cost == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
