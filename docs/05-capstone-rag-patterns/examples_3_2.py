"""
Work Product 3.2: RAG Architecture — Reranking & Filtering

This module demonstrates a production-grade multi-stage retrieval pipeline with:
1. Broad retrieval (semantic search, k=100)
2. Filtering (metadata-based cleanup)
3. Reranking (cross-encoder scoring)
4. Selection (top-5 by reranker score)
5. Context assembly and LLM generation

Example Usage:
    >>> from examples_3_2 import create_rag_pipeline
    >>> pipeline = create_rag_pipeline(documents, filter_config)
    >>> answer = pipeline.generate("What are refund policies for digital goods?")
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

# LangChain
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Cross-encoder for reranking
from sentence_transformers import CrossEncoder
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# SECTION 1: FILTERING LAYER
# ============================================================================

@dataclass
class FilterConfig:
    """Configuration for document filtering."""
    max_age_days: Optional[int] = None
    allowed_types: Optional[List[str]] = None
    verified_only: bool = False
    exclude_keywords: Optional[List[str]] = None


class DocumentFilter:
    """Apply domain-specific filtering rules to retrieve candidates."""
    
    def __init__(self, config: FilterConfig):
        self.config = config
    
    def apply_filters(self, docs: List[Dict]) -> List[Dict]:
        """
        Filter candidates based on rules.
        
        Args:
            docs: List of document dicts with metadata
            
        Returns:
            Filtered document list
        """
        filtered = docs
        initial_count = len(filtered)
        
        # Temporal filtering
        if self.config.max_age_days:
            cutoff = datetime.now() - timedelta(days=self.config.max_age_days)
            filtered = [
                doc for doc in filtered
                if self._parse_date(doc.get("last_updated")) > cutoff
            ]
            logger.info(
                f"Temporal filter: {initial_count} → {len(filtered)} docs "
                f"(max_age={self.config.max_age_days} days)"
            )
            initial_count = len(filtered)
        
        # Document type filtering
        if self.config.allowed_types:
            filtered = [
                doc for doc in filtered
                if doc.get("doc_type", "unknown") in self.config.allowed_types
            ]
            logger.info(
                f"Type filter: {initial_count} → {len(filtered)} docs "
                f"(allowed_types={self.config.allowed_types})"
            )
            initial_count = len(filtered)
        
        # Verification filtering
        if self.config.verified_only:
            filtered = [
                doc for doc in filtered
                if doc.get("verified", False)
            ]
            logger.info(
                f"Verification filter: {initial_count} → {len(filtered)} docs "
                f"(verified_only=True)"
            )
            initial_count = len(filtered)
        
        # Exclude keywords
        if self.config.exclude_keywords:
            original_count = len(filtered)
            filtered = [
                doc for doc in filtered
                if not any(
                    kw.lower() in doc.get("content", "").lower()
                    for kw in self.config.exclude_keywords
                )
            ]
            logger.info(
                f"Keyword exclusion: {original_count} → {len(filtered)} docs "
                f"(excluded: {self.config.exclude_keywords})"
            )
        
        return filtered
    
    @staticmethod
    def _parse_date(date_str: Optional[str]) -> datetime:
        """Parse date string or return far past if invalid."""
        if not date_str:
            return datetime(2000, 1, 1)
        try:
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return datetime(2000, 1, 1)


# ============================================================================
# SECTION 2: RERANKING LAYER
# ============================================================================

class DocumentReranker:
    """Rerank candidates using cross-encoder model."""
    
    def __init__(
        self,
        model_name: str = "cross-encoder/qnli-distilroberta-base",
        use_gpu: bool = False,
        batch_size: int = 32,
    ):
        """
        Initialize reranker with cross-encoder model.
        
        Args:
            model_name: HuggingFace model identifier
            use_gpu: Whether to use GPU (if available)
            batch_size: Batch size for scoring
        """
        self.model = CrossEncoder(
            model_name,
            device="cuda" if use_gpu else "cpu",
            default_activation_function=None  # Return raw scores
        )
        self.batch_size = batch_size
        self.model_name = model_name
        logger.info(f"Loaded cross-encoder: {model_name}")
    
    def rerank(
        self,
        query: str,
        candidates: List[Dict],
        batch_size: Optional[int] = None
    ) -> List[Dict]:
        """
        Score and rerank candidates.
        
        Args:
            query: User query
            candidates: List of document dicts with 'content' key
            batch_size: Override default batch size
            
        Returns:
            Candidates sorted by score (highest first)
        """
        if not candidates:
            return []
        
        batch_size = batch_size or self.batch_size
        texts = [doc.get("content", "") for doc in candidates]
        
        # Create pairs: (query, document)
        pairs = [[query, text] for text in texts]
        
        # Score in batches
        all_scores = []
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i : i + batch_size]
            batch_scores = self.model.predict(batch)
            all_scores.extend(batch_scores)
        
        # Normalize scores to [0, 1] range if needed
        scores = self._normalize_scores(all_scores)
        
        # Attach scores to documents
        for doc, score in zip(candidates, scores):
            doc["rerank_score"] = float(score)
        
        # Sort by score (descending)
        sorted_docs = sorted(
            candidates,
            key=lambda x: x.get("rerank_score", 0),
            reverse=True
        )
        
        logger.info(
            f"Reranked {len(candidates)} docs. "
            f"Top-1 score: {sorted_docs[0].get('rerank_score', 0):.3f}"
        )
        
        return sorted_docs
    
    @staticmethod
    def _normalize_scores(scores: List[float]) -> List[float]:
        """
        Normalize scores to [0, 1] range using sigmoid-like transformation.
        """
        scores_array = np.array(scores)
        
        # If scores are already roughly in [0, 1], use as-is
        if scores_array.min() >= -1 and scores_array.max() <= 1:
            # Apply sigmoid to center around 0.5
            normalized = 1 / (1 + np.exp(-scores_array))
        else:
            # Min-max normalization
            min_score = scores_array.min()
            max_score = scores_array.max()
            if max_score - min_score > 0:
                normalized = (scores_array - min_score) / (max_score - min_score)
            else:
                normalized = np.ones_like(scores_array) * 0.5
        
        return normalized.tolist()


# ============================================================================
# SECTION 3: MULTI-STAGE RETRIEVAL PIPELINE
# ============================================================================

class MultiStageRAGPipeline:
    """
    Production RAG with reranking and filtering.
    
    Architecture:
    1. Broad retrieval: k=100 by embedding similarity
    2. Filtering: Metadata-based cleanup (remove stale, OOB, etc)
    3. Reranking: Cross-encoder scoring
    4. Selection: Top-k by reranker score
    5. Assembly: Format context for LLM
    6. Generation: LLM produces answer
    """
    
    def __init__(
        self,
        vector_store: Chroma,
        filter_config: FilterConfig,
        reranker_model: str = "cross-encoder/qnli-distilroberta-base",
        top_k: int = 5,
        retrieval_k: int = 100,
        use_gpu: bool = False,
        llm_model: str = "gpt-4-turbo",
    ):
        """Initialize the multi-stage pipeline."""
        self.vector_store = vector_store
        self.filter_layer = DocumentFilter(filter_config)
        self.reranker = DocumentReranker(reranker_model, use_gpu=use_gpu)
        self.top_k = top_k
        self.retrieval_k = retrieval_k
        self.llm = ChatOpenAI(model=llm_model, temperature=0)
        
        # Metrics
        self.metrics = {
            "queries_processed": 0,
            "avg_reranker_score": 0,
            "avg_filtering_rate": 0,
        }
    
    def retrieve(self, query: str) -> List[Dict]:
        """
        Execute multi-stage retrieval pipeline.
        
        Returns list of top-k documents with metadata and reranker scores.
        """
        logger.info(f"Starting multi-stage retrieval for: {query[:50]}...")
        
        # STAGE 1: Broad retrieval (k=100)
        logger.info(f"  Stage 1: Broad retrieval (k={self.retrieval_k})")
        search_results = self.vector_store.similarity_search_with_score(
            query, k=self.retrieval_k
        )
        candidates = [
            {
                "content": doc.page_content,
                "embedding_score": float(score),
                **doc.metadata
            }
            for doc, score in search_results
        ]
        logger.info(f"    → Retrieved {len(candidates)} candidates")
        
        # STAGE 2: Filtering
        logger.info(f"  Stage 2: Filtering")
        filtered_docs = self.filter_layer.apply_filters(candidates)
        filter_rate = 1 - (len(filtered_docs) / len(candidates))
        logger.info(
            f"    → {len(candidates)} → {len(filtered_docs)} docs "
            f"({filter_rate*100:.1f}% filtered)"
        )
        self.metrics["avg_filtering_rate"] = filter_rate
        
        if not filtered_docs:
            logger.warning("    ⚠️  All candidates filtered! Returning top-5 from embedding.")
            return candidates[:5]
        
        # STAGE 3: Reranking
        logger.info(f"  Stage 3: Reranking")
        reranked_docs = self.reranker.rerank(query, filtered_docs)
        
        # STAGE 4: Selection (top-k)
        logger.info(f"  Stage 4: Selection (top-{self.top_k})")
        final_docs = reranked_docs[:self.top_k]
        
        # Update metrics
        if final_docs:
            self.metrics["avg_reranker_score"] = np.mean([
                doc.get("rerank_score", 0) for doc in final_docs
            ])
        self.metrics["queries_processed"] += 1
        
        logger.info(f"  ✓ Retrieval complete. Avg score: "
                   f"{self.metrics['avg_reranker_score']:.3f}")
        
        return final_docs
    
    def retrieve_with_fallback(self, query: str) -> List[Dict]:
        """
        Execute retrieval with graceful fallback on reranker failure.
        """
        try:
            return self.retrieve(query)
        except Exception as e:
            logger.error(f"Retrieval failed: {e}. Using embedding-only ranking.")
            # Fallback: Return top-k from embedding search
            search_results = self.vector_store.similarity_search_with_score(
                query, k=self.top_k
            )
            return [
                {
                    "content": doc.page_content,
                    "embedding_score": float(score),
                    "rerank_score": None,  # Fallback
                    **doc.metadata
                }
                for doc, score in search_results
            ]
    
    def generate(self, query: str) -> str:
        """
        Retrieve documents and generate answer.
        
        Args:
            query: User question
            
        Returns:
            Generated answer from LLM
        """
        # Multi-stage retrieval
        docs = self.retrieve(query)
        
        # Assemble context
        context_parts = []
        for i, doc in enumerate(docs, 1):
            score_info = ""
            if "rerank_score" in doc and doc["rerank_score"] is not None:
                score_info = f" [confidence: {doc['rerank_score']:.2f}]"
            
            part = (
                f"[{i}] {doc['content'][:500]}"
                f"{score_info}"
            )
            context_parts.append(part)
        
        context = "\n\n".join(context_parts)
        
        # Generate answer
        prompt = f"""You are a helpful assistant answering questions based on provided context.

Instructions:
1. Answer the question using ONLY information from the context
2. If the context doesn't contain relevant information, say: "I don't have enough information to answer this question."
3. Be concise and specific
4. If helpful, cite which context section(s) you used

Context:
{context}

Question: {query}

Answer:"""
        
        response = self.llm.invoke(prompt)
        return response.content


# ============================================================================
# SECTION 4: EXAMPLE USAGE & HELPER FUNCTIONS
# ============================================================================

def create_sample_documents() -> List[Document]:
    """Create sample documents for demonstration."""
    docs_data = [
        {
            "content": "Refund Policy: Digital products are non-refundable after purchase completion. All sales are final.",
            "metadata": {
                "source": "policies.pdf",
                "doc_type": "policy",
                "last_updated": datetime.now().isoformat(),
                "verified": True,
            }
        },
        {
            "content": "Return Authorization: Physical products may be returned within 30 days of purchase. Gift receipts are accepted.",
            "metadata": {
                "source": "returns.pdf",
                "doc_type": "policy",
                "last_updated": datetime.now().isoformat(),
                "verified": True,
            }
        },
        {
            "content": "Digital Goods Return Policy: eBooks, software, and digital downloads cannot be refunded once delivery is complete.",
            "metadata": {
                "source": "faq.md",
                "doc_type": "faq",
                "last_updated": datetime.now().isoformat(),
                "verified": True,
            }
        },
        {
            "content": "Gift Card Terms: Gift cards are non-refundable and have no expiration date. Balance inquiries available at checkout.",
            "metadata": {
                "source": "gift-cards.pdf",
                "doc_type": "policy",
                "last_updated": datetime.now().isoformat(),
                "verified": True,
            }
        },
        {
            "content": "Refund my customers' reviews have been overwhelmingly positive. Check out our 4.9/5 star rating!",
            "metadata": {
                "source": "forum_post.txt",
                "doc_type": "forum",
                "last_updated": (datetime.now() - timedelta(days=365)).isoformat(),
                "verified": False,
            }
        },
        {
            "content": "Payment Methods: We accept credit cards, debit cards, PayPal, Apple Pay, and gift cards at checkout.",
            "metadata": {
                "source": "checkout.md",
                "doc_type": "guide",
                "last_updated": datetime.now().isoformat(),
                "verified": True,
            }
        },
        {
            "content": "Refund code generator script: function generateRefundCode() { return 'REF-' + Math.random(); }",
            "metadata": {
                "source": "scripts/refund_gen.py",
                "doc_type": "code",
                "last_updated": datetime.now().isoformat(),
                "verified": False,
            }
        },
        {
            "content": "Refunding money into an escrow account during dispute resolution. Legal holds apply during investigation.",
            "metadata": {
                "source": "legal.pdf",
                "doc_type": "legal",
                "last_updated": datetime.now().isoformat(),
                "verified": True,
            }
        },
    ]
    
    return [
        Document(page_content=d["content"], metadata=d["metadata"])
        for d in docs_data
    ]


def create_rag_pipeline(
    documents: Optional[List[Document]] = None,
    filter_config: Optional[FilterConfig] = None
) -> MultiStageRAGPipeline:
    """
    Create and initialize a multi-stage RAG pipeline.
    
    Args:
        documents: Documents to index (uses samples if None)
        filter_config: Filtering configuration (uses defaults if None)
        
    Returns:
        Initialized MultiStageRAGPipeline
    """
    if documents is None:
        documents = create_sample_documents()
    
    if filter_config is None:
        filter_config = FilterConfig(
            max_age_days=180,
            allowed_types=["policy", "faq", "guide", "legal"],
            verified_only=True,
        )
    
    # Create vector store
    try:
        embeddings = OpenAIEmbeddings()
    except Exception:
        logger.warning("OpenAI embeddings not available, using Ollama")
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    vector_store = Chroma.from_documents(
        documents,
        embeddings,
        collection_name="rag_pipeline",
    )
    
    # Create pipeline
    pipeline = MultiStageRAGPipeline(
        vector_store=vector_store,
        filter_config=filter_config,
        top_k=5,
        retrieval_k=100,
    )
    
    return pipeline


def demo_comparison():
    """
    Demonstrate the difference between naive and advanced retrieval.
    """
    print("=" * 80)
    print("DEMO: Naive vs. Advanced RAG Retrieval")
    print("=" * 80)
    
    # Create pipeline
    pipeline = create_rag_pipeline()
    query = "What are refund policies for digital goods?"
    
    print(f"\n📝 Query: {query}\n")
    
    # APPROACH 1: Naive (embedding-only)
    print("🟦 NAIVE APPROACH (Embedding search only, k=5):")
    print("-" * 80)
    search_results = pipeline.vector_store.similarity_search_with_score(query, k=5)
    for i, (doc, score) in enumerate(search_results, 1):
        content_preview = doc.page_content[:70].replace("\n", " ")
        print(f"  {i}. [{score:.3f}] {content_preview}...")
        print(f"     Type: {doc.metadata.get('doc_type')}, "
              f"Verified: {doc.metadata.get('verified')}")
    
    # APPROACH 2: Advanced (full pipeline)
    print("\n🟩 ADVANCED APPROACH (Reranking + Filtering):")
    print("-" * 80)
    advanced_results = pipeline.retrieve(query)
    for i, doc in enumerate(advanced_results, 1):
        content_preview = doc['content'][:70].replace("\n", " ")
        print(f"  {i}. [score: {doc.get('rerank_score', 0):.3f}] "
              f"{content_preview}...")
        print(f"     Type: {doc.get('doc_type')}, "
              f"Verified: {doc.get('verified')}")
    
    print("\n✅ Key Differences:")
    print("  • Advanced: Stale/unverified docs removed by filtering")
    print("  • Advanced: Top result reranked higher (confidence score)")
    print("  • Advanced: Noise reduced significantly")
    
    # APPROACH 3: Generation
    print("\n" + "=" * 80)
    print("GENERATION: LLM Answer with Advanced Retrieval")
    print("=" * 80)
    answer = pipeline.generate(query)
    print(f"\n{answer}")
    
    # Metrics
    print("\n" + "=" * 80)
    print("METRICS")
    print("=" * 80)
    for key, value in pipeline.metrics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    demo_comparison()
