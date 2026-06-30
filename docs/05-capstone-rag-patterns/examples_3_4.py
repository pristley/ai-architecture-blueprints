"""
Work Product 3.4: RAG Architecture — Evaluation & Metrics

This module provides a comprehensive evaluation framework for RAG systems:
- Retrieval metrics (precision, recall, MRR, NDCG)
- Answer quality evaluation (relevance, completeness)
- Citation accuracy verification
- Latency profiling (per-stage breakdown)
- Cost analysis
- Comparison framework for different RAG patterns

Example Usage:
    >>> from examples_3_4 import (
    ...     RetrievalEvaluator, AnswerEvaluator, LatencyProfiler,
    ...     EvaluationDataset, create_evaluation_benchmark
    ... )
    >>> dataset = create_evaluation_benchmark()
    >>> results = evaluate_rag(rag_system, dataset)
"""

import logging
import time
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import numpy as np

# LangChain
from langchain_openai import ChatOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# SECTION 1: DATA STRUCTURES
# ============================================================================

@dataclass
class EvaluationSample:
    """Single evaluation sample: query + answer + ground truth."""
    query_id: str
    query: str
    expected_answer: str
    relevant_doc_ids: List[str]
    sources: List[Dict[str, str]]  # List of {id, title, content}
    category: str = "general"  # For grouping


@dataclass
class RetrievalMetrics:
    """Retrieval performance metrics."""
    precision_at_5: float
    precision_at_10: float
    recall_at_5: float
    recall_at_10: float
    mrr: float  # Mean Reciprocal Rank
    ndcg_at_5: float
    ndcg_at_10: float
    
    def average_score(self) -> float:
        """Get average score across metrics."""
        scores = [
            self.precision_at_5,
            self.recall_at_5,
            self.mrr,
            self.ndcg_at_5,
        ]
        return np.mean(scores)


@dataclass
class AnswerMetrics:
    """Answer quality metrics."""
    relevance_score: float  # 1-5
    completeness_score: float  # 1-5
    hallucination_rate: float  # 0-1
    citation_accuracy: float  # 0-1
    
    def average_score(self) -> float:
        """Get average score."""
        return (
            (self.relevance_score + self.completeness_score) / 2 * 0.2 +
            (1.0 - self.hallucination_rate) * 0.4 +
            self.citation_accuracy * 0.4
        )


@dataclass
class PerformanceMetrics:
    """Latency and performance metrics."""
    total_latency: float  # seconds
    embedding_latency: float
    search_latency: float
    reranking_latency: float
    generation_latency: float
    other_latency: float
    
    def breakdown(self) -> Dict[str, float]:
        """Get latency breakdown."""
        return {
            "embedding": self.embedding_latency,
            "search": self.search_latency,
            "reranking": self.reranking_latency,
            "generation": self.generation_latency,
            "other": self.other_latency,
        }


@dataclass
class CostMetrics:
    """Cost analysis metrics."""
    embedding_cost: float
    search_cost: float
    reranking_cost: float
    llm_cost: float
    total_cost: float
    
    def breakdown(self) -> Dict[str, float]:
        """Get cost breakdown."""
        return {
            "embedding": self.embedding_cost,
            "search": self.search_cost,
            "reranking": self.reranking_cost,
            "llm": self.llm_cost,
            "total": self.total_cost,
        }


# ============================================================================
# SECTION 2: RETRIEVAL EVALUATOR
# ============================================================================

class RetrievalEvaluator:
    """Evaluate retrieval quality using standard IR metrics."""
    
    def __init__(self):
        """Initialize retrieval evaluator."""
        pass
    
    def evaluate(
        self,
        retrieved_ids: List[str],
        relevant_ids: List[str],
        scores: Optional[List[float]] = None,
    ) -> RetrievalMetrics:
        """
        Evaluate retrieved results against ground truth.
        
        Args:
            retrieved_ids: IDs of retrieved documents (ranked list)
            relevant_ids: IDs of truly relevant documents
            scores: Optional relevance scores for NDCG calculation
            
        Returns:
            RetrievalMetrics with all calculations
        """
        relevant_set = set(relevant_ids)
        
        # Calculate metrics at different k values
        precision_at_5 = self._precision_at_k(retrieved_ids, relevant_set, k=5)
        precision_at_10 = self._precision_at_k(retrieved_ids, relevant_set, k=10)
        
        recall_at_5 = self._recall_at_k(retrieved_ids, relevant_set, k=5)
        recall_at_10 = self._recall_at_k(retrieved_ids, relevant_set, k=10)
        
        mrr = self._mean_reciprocal_rank(retrieved_ids, relevant_set)
        
        ndcg_at_5 = self._ndcg_at_k(retrieved_ids, relevant_set, scores, k=5)
        ndcg_at_10 = self._ndcg_at_k(retrieved_ids, relevant_set, scores, k=10)
        
        return RetrievalMetrics(
            precision_at_5=precision_at_5,
            precision_at_10=precision_at_10,
            recall_at_5=recall_at_5,
            recall_at_10=recall_at_10,
            mrr=mrr,
            ndcg_at_5=ndcg_at_5,
            ndcg_at_10=ndcg_at_10,
        )
    
    @staticmethod
    def _precision_at_k(retrieved: List[str], relevant: set, k: int) -> float:
        """Calculate precision@k."""
        if k == 0 or len(retrieved) == 0:
            return 0.0
        
        top_k = set(retrieved[:k])
        intersect = len(top_k & relevant)
        return intersect / k if k > 0 else 0.0
    
    @staticmethod
    def _recall_at_k(retrieved: List[str], relevant: set, k: int) -> float:
        """Calculate recall@k."""
        if len(relevant) == 0:
            return 1.0
        
        top_k = set(retrieved[:k])
        intersect = len(top_k & relevant)
        return intersect / len(relevant) if len(relevant) > 0 else 0.0
    
    @staticmethod
    def _mean_reciprocal_rank(retrieved: List[str], relevant: set) -> float:
        """Calculate MRR (Mean Reciprocal Rank)."""
        for rank, doc_id in enumerate(retrieved, 1):
            if doc_id in relevant:
                return 1.0 / rank
        return 0.0
    
    @staticmethod
    def _ndcg_at_k(
        retrieved: List[str],
        relevant: set,
        scores: Optional[List[float]],
        k: int
    ) -> float:
        """Calculate NDCG@k (Normalized Discounted Cumulative Gain)."""
        # DCG calculation
        dcg = 0.0
        for i, doc_id in enumerate(retrieved[:k], 1):
            relevance = 1.0 if doc_id in relevant else 0.0
            dcg += relevance / np.log2(i + 1)
        
        # iDCG (ideal DCG - all relevant at top)
        idcg = 0.0
        for i in range(1, min(k, len(relevant)) + 1):
            idcg += 1.0 / np.log2(i + 1)
        
        return dcg / idcg if idcg > 0 else 0.0


# ============================================================================
# SECTION 3: ANSWER EVALUATOR
# ============================================================================

class AnswerEvaluator:
    """Evaluate answer quality using LLM and heuristics."""
    
    def __init__(self, llm_model: str = "gpt-4-turbo"):
        """
        Initialize answer evaluator.
        
        Args:
            llm_model: LLM model for scoring answers
        """
        self.llm = ChatOpenAI(model=llm_model, temperature=0)
    
    def evaluate(
        self,
        query: str,
        generated_answer: str,
        expected_answer: str,
        sources: List[str],
    ) -> AnswerMetrics:
        """
        Evaluate generated answer against expected answer.
        
        Args:
            query: Original query
            generated_answer: LLM-generated answer
            expected_answer: Expected/reference answer
            sources: Source documents used for retrieval
            
        Returns:
            AnswerMetrics with quality scores
        """
        # Score relevance and completeness
        relevance_score = self._score_relevance(
            query, generated_answer, expected_answer
        )
        completeness_score = self._score_completeness(
            generated_answer, expected_answer
        )
        
        # Detect hallucinations
        hallucination_rate = self._detect_hallucinations(
            generated_answer, sources
        )
        
        # Verify citations
        citation_accuracy = self._verify_citations(
            generated_answer, sources
        )
        
        return AnswerMetrics(
            relevance_score=relevance_score,
            completeness_score=completeness_score,
            hallucination_rate=hallucination_rate,
            citation_accuracy=citation_accuracy,
        )
    
    def _score_relevance(
        self,
        query: str,
        answer: str,
        expected: str,
    ) -> float:
        """Score relevance of answer to query (1-5)."""
        prompt = f"""
Question: {query}
Expected answer: {expected}
Generated answer: {answer}

Score the generated answer on relevance to the question (1-5):
1 = Not relevant at all
5 = Directly and fully addresses the question

Return only the score (1-5):
"""
        
        try:
            response = self.llm.invoke(prompt).content.strip()
            score = float(response.split()[0])
            return max(1.0, min(5.0, score))
        except Exception as e:
            logger.error(f"Relevance scoring failed: {e}")
            return 3.0
    
    def _score_completeness(
        self,
        answer: str,
        expected: str,
    ) -> float:
        """Score completeness of answer (1-5)."""
        prompt = f"""
Expected answer: {expected}
Generated answer: {answer}

Score the completeness of the generated answer (1-5):
1 = Missing most details
5 = Comprehensive and complete

Return only the score (1-5):
"""
        
        try:
            response = self.llm.invoke(prompt).content.strip()
            score = float(response.split()[0])
            return max(1.0, min(5.0, score))
        except Exception as e:
            logger.error(f"Completeness scoring failed: {e}")
            return 3.0
    
    def _detect_hallucinations(
        self,
        answer: str,
        sources: List[str],
    ) -> float:
        """Detect hallucination rate (0-1)."""
        if not sources:
            return 0.5
        
        source_text = " ".join(sources)
        
        prompt = f"""
Answer: {answer}
Source documents: {source_text}

Analyze the answer for hallucinations (claims not supported by sources).
Estimate the percentage of the answer that is hallucinated (0-100):
"""
        
        try:
            response = self.llm.invoke(prompt).content.strip()
            # Extract percentage
            percentage = float(response.split()[0])
            return max(0.0, min(1.0, percentage / 100.0))
        except Exception as e:
            logger.error(f"Hallucination detection failed: {e}")
            return 0.3
    
    def _verify_citations(
        self,
        answer: str,
        sources: List[str],
    ) -> float:
        """Verify that citations are accurate (0-1)."""
        if not sources:
            return 0.5
        
        source_text = " ".join(sources)
        
        prompt = f"""
Answer: {answer}
Source documents: {source_text}

Check if the main claims in the answer are supported by the sources.
Report the fraction of claims that are properly cited (0-1):
"""
        
        try:
            response = self.llm.invoke(prompt).content.strip()
            accuracy = float(response.split()[0])
            return max(0.0, min(1.0, accuracy))
        except Exception as e:
            logger.error(f"Citation verification failed: {e}")
            return 0.7


# ============================================================================
# SECTION 4: LATENCY PROFILER
# ============================================================================

class LatencyProfiler:
    """Profile latency at each stage of RAG pipeline."""
    
    def __init__(self):
        """Initialize profiler."""
        self.stages = {}
    
    def start_stage(self, stage_name: str) -> str:
        """Start timing a stage."""
        stage_id = f"{stage_name}_{time.time()}"
        self.stages[stage_id] = {
            "name": stage_name,
            "start": time.time(),
        }
        return stage_id
    
    def end_stage(self, stage_id: str) -> float:
        """End timing a stage and return elapsed time."""
        if stage_id not in self.stages:
            logger.warning(f"Stage {stage_id} not found")
            return 0.0
        
        elapsed = time.time() - self.stages[stage_id]["start"]
        self.stages[stage_id]["elapsed"] = elapsed
        return elapsed
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get performance metrics from recorded stages."""
        elapsed_by_stage = {}
        for stage_id, data in self.stages.items():
            stage_name = data["name"]
            elapsed = data.get("elapsed", 0.0)
            
            if stage_name not in elapsed_by_stage:
                elapsed_by_stage[stage_name] = 0.0
            elapsed_by_stage[stage_name] += elapsed
        
        # Map stages to standard names
        total = sum(elapsed_by_stage.values())
        
        return PerformanceMetrics(
            total_latency=total,
            embedding_latency=elapsed_by_stage.get("embedding", 0.0),
            search_latency=elapsed_by_stage.get("search", 0.0),
            reranking_latency=elapsed_by_stage.get("reranking", 0.0),
            generation_latency=elapsed_by_stage.get("generation", 0.0),
            other_latency=elapsed_by_stage.get("other", 0.0),
        )


# ============================================================================
# SECTION 5: COST ANALYZER
# ============================================================================

class CostAnalyzer:
    """Analyze cost of RAG query execution."""
    
    # OpenAI pricing (as of 2024)
    EMBEDDING_COST_PER_1K = 0.00002  # GPT-3.5
    GPT_INPUT_COST_PER_1K = 0.0005   # GPT-3.5
    GPT_OUTPUT_COST_PER_1K = 0.0015  # GPT-3.5
    
    def __init__(
        self,
        embedding_cost_per_1k: float = EMBEDDING_COST_PER_1K,
        input_cost_per_1k: float = GPT_INPUT_COST_PER_1K,
        output_cost_per_1k: float = GPT_OUTPUT_COST_PER_1K,
    ):
        """
        Initialize cost analyzer.
        
        Args:
            embedding_cost_per_1k: Cost per 1K embedding tokens
            input_cost_per_1k: Cost per 1K input tokens to LLM
            output_cost_per_1k: Cost per 1K output tokens from LLM
        """
        self.embedding_cost = embedding_cost_per_1k
        self.input_cost = input_cost_per_1k
        self.output_cost = output_cost_per_1k
    
    def calculate(
        self,
        query_tokens: int,
        doc_tokens: int,
        num_docs: int,
        input_prompt_tokens: int,
        output_tokens: int,
        reranking_cost: float = 0.0,
        search_cost: float = 0.0,
    ) -> CostMetrics:
        """
        Calculate total cost breakdown.
        
        Args:
            query_tokens: Tokens in query embedding
            doc_tokens: Average tokens per document
            num_docs: Number of documents embedded/retrieved
            input_prompt_tokens: Tokens in LLM input
            output_tokens: Tokens in LLM output
            reranking_cost: Cost of reranking if used
            search_cost: Cost of vector search if using paid service
            
        Returns:
            CostMetrics with breakdown
        """
        # Embedding costs
        embedding_cost = (
            (query_tokens + doc_tokens * num_docs) / 1000 * self.embedding_cost
        )
        
        # LLM costs
        llm_input_cost = (input_prompt_tokens / 1000) * self.input_cost
        llm_output_cost = (output_tokens / 1000) * self.output_cost
        llm_cost = llm_input_cost + llm_output_cost
        
        # Total
        total_cost = embedding_cost + search_cost + reranking_cost + llm_cost
        
        return CostMetrics(
            embedding_cost=embedding_cost,
            search_cost=search_cost,
            reranking_cost=reranking_cost,
            llm_cost=llm_cost,
            total_cost=total_cost,
        )


# ============================================================================
# SECTION 6: EVALUATION DATASET
# ============================================================================

class EvaluationDataset:
    """Manage evaluation dataset with Q&A pairs."""
    
    def __init__(self):
        """Initialize dataset."""
        self.samples: List[EvaluationSample] = []
    
    def add_sample(
        self,
        query_id: str,
        query: str,
        expected_answer: str,
        relevant_doc_ids: List[str],
        sources: List[Dict],
        category: str = "general",
    ):
        """Add sample to dataset."""
        sample = EvaluationSample(
            query_id=query_id,
            query=query,
            expected_answer=expected_answer,
            relevant_doc_ids=relevant_doc_ids,
            sources=sources,
            category=category,
        )
        self.samples.append(sample)
    
    def __len__(self) -> int:
        """Get dataset size."""
        return len(self.samples)
    
    def __iter__(self):
        """Iterate over samples."""
        return iter(self.samples)
    
    def by_category(self, category: str) -> List[EvaluationSample]:
        """Get samples by category."""
        return [s for s in self.samples if s.category == category]


# ============================================================================
# SECTION 7: COMPARISON FRAMEWORK
# ============================================================================

class RAGComparison:
    """Compare performance of different RAG architectures."""
    
    def __init__(self, dataset: EvaluationDataset):
        """
        Initialize comparison.
        
        Args:
            dataset: Evaluation dataset to run on
        """
        self.dataset = dataset
        self.results = {}
    
    def add_result(
        self,
        rag_name: str,
        retrieval_metrics_list: List[RetrievalMetrics],
        answer_metrics_list: List[AnswerMetrics],
        performance_metrics_list: List[PerformanceMetrics],
        cost_metrics_list: List[CostMetrics],
    ):
        """Add evaluation results for a RAG architecture."""
        self.results[rag_name] = {
            "retrieval": retrieval_metrics_list,
            "answer": answer_metrics_list,
            "performance": performance_metrics_list,
            "cost": cost_metrics_list,
        }
    
    def get_summary(self) -> Dict[str, Dict]:
        """Get summary comparison table."""
        summary = {}
        
        for rag_name, metrics in self.results.items():
            retrieval_avg = np.mean([m.average_score() for m in metrics["retrieval"]])
            answer_avg = np.mean([m.average_score() for m in metrics["answer"]])
            latency_p95 = np.percentile(
                [m.total_latency for m in metrics["performance"]], 95
            )
            cost_avg = np.mean([m.total_cost for m in metrics["cost"]])
            
            summary[rag_name] = {
                "retrieval_score": retrieval_avg,
                "answer_score": answer_avg,
                "latency_p95": latency_p95,
                "cost_per_query": cost_avg,
            }
        
        return summary
    
    def recommend(self) -> str:
        """Recommend best RAG based on metrics."""
        summary = self.get_summary()
        
        # Simple heuristic: balance quality and cost
        best_rag = None
        best_score = -1
        
        for rag_name, metrics in summary.items():
            # Weighted score: 40% answer quality, 30% retrieval, 20% latency, 10% cost
            score = (
                metrics["answer_score"] * 0.4 +
                metrics["retrieval_score"] * 0.3 +
                (1.0 - min(metrics["latency_p95"] / 5.0, 1.0)) * 0.2 +
                (1.0 - min(metrics["cost_per_query"] / 0.10, 1.0)) * 0.1
            )
            
            if score > best_score:
                best_score = score
                best_rag = rag_name
        
        return best_rag or "unknown"


# ============================================================================
# SECTION 8: EVALUATION REPORT
# ============================================================================

class EvaluationReport:
    """Generate evaluation reports."""
    
    @staticmethod
    def generate_report(
        rag_name: str,
        dataset_size: int,
        retrieval_metrics: List[RetrievalMetrics],
        answer_metrics: List[AnswerMetrics],
        performance_metrics: List[PerformanceMetrics],
        cost_metrics: List[CostMetrics],
    ) -> Dict:
        """Generate comprehensive evaluation report."""
        
        # Calculate aggregates
        retrieval_avg = np.mean([m.average_score() for m in retrieval_metrics])
        answer_avg = np.mean([m.average_score() for m in answer_metrics])
        
        latencies = [m.total_latency for m in performance_metrics]
        costs = [m.total_cost for m in cost_metrics]
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "rag_name": rag_name,
            "dataset_size": dataset_size,
            "retrieval": {
                "average_score": retrieval_avg,
                "precision_at_5": np.mean([m.precision_at_5 for m in retrieval_metrics]),
                "recall_at_5": np.mean([m.recall_at_5 for m in retrieval_metrics]),
                "mrr": np.mean([m.mrr for m in retrieval_metrics]),
            },
            "answer": {
                "average_score": answer_avg,
                "relevance": np.mean([m.relevance_score for m in answer_metrics]),
                "completeness": np.mean([m.completeness_score for m in answer_metrics]),
                "hallucination_rate": np.mean([m.hallucination_rate for m in answer_metrics]),
                "citation_accuracy": np.mean([m.citation_accuracy for m in answer_metrics]),
            },
            "performance": {
                "latency_mean": np.mean(latencies),
                "latency_p95": np.percentile(latencies, 95),
                "latency_p99": np.percentile(latencies, 99),
            },
            "cost": {
                "cost_per_query": np.mean(costs),
                "monthly_cost_1k_queries": np.mean(costs) * 1000,
                "monthly_cost_100k_queries": np.mean(costs) * 100000,
            },
        }
        
        return report


# ============================================================================
# SECTION 9: FACTORY FUNCTIONS
# ============================================================================

def create_evaluation_benchmark() -> EvaluationDataset:
    """Create sample evaluation benchmark dataset."""
    dataset = EvaluationDataset()
    
    # Sample evaluation cases
    samples = [
        {
            "query_id": "eval_001",
            "query": "What is the termination fee?",
            "expected": "The termination fee is 10% of remaining contract value",
            "relevant_docs": ["section_5.2", "section_5.3"],
            "sources": [
                {"id": "section_5.2", "content": "Early termination fee: 10% of remaining contract value"},
                {"id": "section_5.3", "content": "This fee applies to cancellations before end of term"},
            ],
            "category": "contract",
        },
        {
            "query_id": "eval_002",
            "query": "How long is the initial commitment period?",
            "expected": "The initial commitment is 12 months from the effective date",
            "relevant_docs": ["section_2.1"],
            "sources": [
                {"id": "section_2.1", "content": "Initial term: 12 months from Effective Date"},
            ],
            "category": "contract",
        },
        {
            "query_id": "eval_003",
            "query": "What payment terms are available?",
            "expected": "Payment is due within 30 days of invoice, with 1.5% monthly interest for late payments",
            "relevant_docs": ["section_4.1", "section_4.2"],
            "sources": [
                {"id": "section_4.1", "content": "Payment due within 30 days of invoice"},
                {"id": "section_4.2", "content": "Late payments incur 1.5% monthly interest"},
            ],
            "category": "financial",
        },
    ]
    
    for sample in samples:
        dataset.add_sample(
            query_id=sample["query_id"],
            query=sample["query"],
            expected_answer=sample["expected"],
            relevant_doc_ids=sample["relevant_docs"],
            sources=sample["sources"],
            category=sample["category"],
        )
    
    return dataset


def demo_evaluation():
    """Demonstrate evaluation framework."""
    print("=" * 80)
    print("DEMO: RAG Evaluation Framework")
    print("=" * 80)
    
    # Create dataset
    dataset = create_evaluation_benchmark()
    print(f"\n📊 Evaluation dataset: {len(dataset)} samples\n")
    
    # Initialize evaluators
    retrieval_eval = RetrievalEvaluator()
    answer_eval = AnswerEvaluator()
    latency_profiler = LatencyProfiler()
    cost_analyzer = CostAnalyzer()
    
    # Simulate evaluation
    retrieved_ids = ["section_5.2", "section_4.1", "section_2.1"]
    relevant_ids = ["section_5.2", "section_5.3"]
    
    retrieval_metrics = retrieval_eval.evaluate(retrieved_ids, relevant_ids)
    
    print(f"🔍 Retrieval Metrics:")
    print(f"  Precision@5: {retrieval_metrics.precision_at_5:.2%}")
    print(f"  Recall@5: {retrieval_metrics.recall_at_5:.2%}")
    print(f"  MRR: {retrieval_metrics.mrr:.2f}")
    print(f"  NDCG@5: {retrieval_metrics.ndcg_at_5:.2f}")
    
    # Simulate latency
    stage1 = latency_profiler.start_stage("embedding")
    time.sleep(0.1)
    latency_profiler.end_stage(stage1)
    
    stage2 = latency_profiler.start_stage("search")
    time.sleep(0.2)
    latency_profiler.end_stage(stage2)
    
    perf_metrics = latency_profiler.get_metrics()
    print(f"\n⏱️  Performance Metrics:")
    print(f"  Total Latency: {perf_metrics.total_latency:.3f}s")
    print(f"  Embedding: {perf_metrics.embedding_latency:.3f}s")
    print(f"  Search: {perf_metrics.search_latency:.3f}s")
    
    # Simulate cost
    cost_metrics = cost_analyzer.calculate(
        query_tokens=50,
        doc_tokens=500,
        num_docs=5,
        input_prompt_tokens=800,
        output_tokens=100,
    )
    print(f"\n💰 Cost Metrics:")
    print(f"  Total Cost: ${cost_metrics.total_cost:.4f}")
    print(f"  Embedding: ${cost_metrics.embedding_cost:.4f}")
    print(f"  LLM: ${cost_metrics.llm_cost:.4f}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demo_evaluation()
