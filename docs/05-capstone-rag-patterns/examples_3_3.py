"""
Work Product 3.3: RAG Architecture — Hierarchical Indexing

This module demonstrates a production-grade hierarchical multi-layer retrieval system for scaling RAG to 100K+ documents:

Architecture:
- Layer 0: Document-level summaries (100K documents)
- Layer 1: Section-level summaries (500K sections)
- Layer 2: Full text chunks (linked, not indexed)

Example Usage:
    >>> from examples_3_3 import create_hierarchical_pipeline
    >>> pipeline = create_hierarchical_pipeline()
    >>> docs = pipeline.retrieve("How do I handle payment errors?")
    >>> answer = pipeline.generate(query)
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re
import tiktoken

# LangChain
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import Document

# Cross-encoder for reranking
from sentence_transformers import CrossEncoder
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# SECTION 1: DOCUMENT SUMMARIZATION
# ============================================================================

class DocumentSummarizer:
    """Generate extractive summaries at document and section levels."""
    
    def __init__(self):
        """Initialize summarizer with tokenizer."""
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        except:
            # Fallback tokenizer
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))
    
    def extractive_summary(
        self,
        text: str,
        target_ratio: float = 0.3,
        min_sentences: int = 3,
    ) -> str:
        """
        Extract key sentences based on importance heuristics.
        
        Args:
            text: Full text to summarize
            target_ratio: Target fraction of sentences to keep
            min_sentences: Minimum sentences to keep
            
        Returns:
            Summary preserving important sentences in original order
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        
        if not sentences:
            return text[:500]  # Fallback
        
        # Calculate how many sentences to keep
        keep_count = max(min_sentences, int(len(sentences) * target_ratio))
        keep_count = min(keep_count, len(sentences))
        
        # Score sentences by importance
        scores = []
        for i, sent in enumerate(sentences):
            score = self._score_sentence(sent, text, i, len(sentences))
            scores.append((score, i, sent))
        
        # Select top-scoring sentences
        top_sentences = sorted(scores, key=lambda x: x[0], reverse=True)[:keep_count]
        
        # Sort by original position
        top_sentences.sort(key=lambda x: x[1])
        
        # Reconstruct summary
        summary = " ".join([sent for _, _, sent in top_sentences])
        
        return summary
    
    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitter (sentence endings)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Clean up
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    @staticmethod
    def _score_sentence(
        sentence: str,
        full_text: str,
        position: int,
        total_sentences: int,
    ) -> float:
        """
        Score sentence by importance heuristics.
        
        Higher score = more important
        """
        score = 0.0
        
        # Length bias: longer sentences often more informative
        words = sentence.split()
        length_score = min(len(words) / 25.0, 1.0)  # Normalize to ~25 words
        score += length_score * 0.3
        
        # Position bias: first and last sentences important
        if position == 0 or position == total_sentences - 1:
            score += 0.3
        
        # Keyword presence: sentences with certain keywords more important
        important_keywords = [
            "example", "important", "note", "key", "must", "should",
            "error", "warning", "critical", "best practice", "guidelines"
        ]
        keyword_score = sum(
            0.1 for kw in important_keywords
            if kw.lower() in sentence.lower()
        )
        score += min(keyword_score, 0.3)
        
        # Content density: sentences with more information-bearing words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "is", "are"
        }
        content_words = [
            w for w in words
            if w.lower() not in stop_words and len(w) > 3
        ]
        density_score = len(content_words) / max(len(words), 1) if words else 0
        score += density_score * 0.1
        
        return score


# ============================================================================
# SECTION 2: HIERARCHICAL VECTOR STORE
# ============================================================================

@dataclass
class Section:
    """Represents a section of a document."""
    id: str
    title: str
    content: str
    page_num: Optional[int] = None


class HierarchicalVectorStore:
    """
    Multi-layer vector store for hierarchical retrieval.
    
    Layers:
    - Layer 0: Document summaries (100K documents max)
    - Layer 1: Section summaries (500K sections max)
    - Layer 2: Full text chunks (linked, not indexed)
    """
    
    def __init__(self, use_ollama: bool = False):
        """Initialize vector stores and embeddings."""
        try:
            embeddings = OpenAIEmbeddings()
        except Exception:
            logger.warning("OpenAI embeddings unavailable, using Ollama")
            from langchain_community.embeddings import OllamaEmbeddings
            embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        # Layer 0: Document-level summaries
        self.layer_0 = Chroma(
            collection_name="rag_layer_0_docs",
            embedding_function=embeddings,
        )
        
        # Layer 1: Section-level summaries
        self.layer_1 = Chroma(
            collection_name="rag_layer_1_sections",
            embedding_function=embeddings,
        )
        
        # Layer 2: Full text chunks (stored in hash map, not indexed)
        self.layer_2_map = {}  # section_id → List[chunk_dict]
        
        # Metadata store
        self.doc_metadata = {}  # doc_id → {title, author, date, ...}
        
        self.summarizer = DocumentSummarizer()
        logger.info("Initialized hierarchical vector store")
    
    def ingest_document(
        self,
        doc_id: str,
        title: str,
        full_text: str,
        sections: List[Section],
        metadata: Optional[Dict] = None,
    ):
        """
        Ingest a document into the hierarchy.
        
        Args:
            doc_id: Unique document ID
            title: Document title
            full_text: Full document text
            sections: List of Section objects
            metadata: Additional metadata (author, date, etc)
        """
        logger.info(f"Ingesting document: {title} ({doc_id})")
        
        # Store document metadata
        self.doc_metadata[doc_id] = {
            "title": title,
            "doc_id": doc_id,
            **(metadata or {})
        }
        
        # Layer 0: Create and store document summary
        doc_summary = self.summarizer.extractive_summary(
            full_text,
            target_ratio=0.2,  # Keep 20% for document-level
            min_sentences=5,
        )
        
        doc_0 = Document(
            page_content=doc_summary,
            metadata={
                "level": 0,
                "doc_id": doc_id,
                "title": title,
                "type": "document_summary",
                "token_count": self.summarizer.count_tokens(doc_summary),
            }
        )
        self.layer_0.add_documents([doc_0])
        logger.debug(f"  Added Layer 0 (doc summary: {doc_0.metadata['token_count']} tokens)")
        
        # Layer 1 + 2: Process sections
        section_summaries = []
        
        for section in sections:
            section_id = f"{doc_id}#{section.id}"
            
            # Layer 1: Create section summary
            section_summary = self.summarizer.extractive_summary(
                section.content,
                target_ratio=0.4,  # Keep 40% for section-level
                min_sentences=3,
            )
            
            doc_1 = Document(
                page_content=section_summary,
                metadata={
                    "level": 1,
                    "doc_id": doc_id,
                    "section_id": section.id,
                    "section_title": section.title,
                    "type": "section_summary",
                    "page_num": section.page_num,
                    "token_count": self.summarizer.count_tokens(section_summary),
                }
            )
            section_summaries.append(doc_1)
            
            # Layer 2: Store full chunks (linked, not indexed)
            chunks = self._create_chunks(section.content, section_id)
            self.layer_2_map[section_id] = chunks
        
        # Batch add Layer 1 documents
        if section_summaries:
            self.layer_1.add_documents(section_summaries)
            logger.debug(f"  Added Layer 1 ({len(section_summaries)} section summaries)")
            logger.debug(f"  Added Layer 2 ({sum(len(self.layer_2_map[k]) for k in self.layer_2_map if k.startswith(doc_id))} chunks)")
    
    def _create_chunks(
        self,
        text: str,
        section_id: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> List[Dict]:
        """
        Create overlapping chunks from section text.
        
        Args:
            text: Section text
            section_id: Parent section ID
            chunk_size: Size of each chunk in tokens
            overlap: Overlap between chunks in tokens
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        tokens = self.summarizer.tokenizer.encode(text)
        
        step = chunk_size - overlap
        for i in range(0, len(tokens), step):
            end = min(i + chunk_size, len(tokens))
            chunk_tokens = tokens[i:end]
            chunk_text = self.summarizer.tokenizer.decode(chunk_tokens)
            
            chunks.append({
                "section_id": section_id,
                "index": len(chunks),
                "content": chunk_text,
                "token_count": len(chunk_tokens),
                "start_token": i,
                "end_token": end,
            })
        
        return chunks
    
    def retrieve_hierarchical(
        self,
        query: str,
        k_0: int = 20,    # Documents to find at Layer 0
        k_1: int = 10,    # Sections per doc at Layer 1
        k_2: int = 5,     # Chunks per section at Layer 2
    ) -> List[Dict]:
        """
        Execute hierarchical retrieval across three layers.
        
        Returns:
            List of full text chunks with metadata
        """
        results = []
        
        logger.info(f"Hierarchical retrieval for: {query[:50]}...")
        
        # Stage 1: Layer 0 — Find relevant documents
        logger.debug(f"  Stage 1: Layer 0 search (k={k_0})")
        layer_0_results = self.layer_0.similarity_search_with_score(query, k=k_0)
        
        doc_ids = {}  # doc_id → max_score
        for doc, score in layer_0_results:
            doc_id = doc.metadata["doc_id"]
            doc_ids[doc_id] = max(doc_ids.get(doc_id, 0), score)
        
        logger.debug(f"    Found {len(doc_ids)} relevant documents")
        
        # Stage 2: Layer 1 — Find relevant sections
        logger.debug(f"  Stage 2: Layer 1 search (k={len(doc_ids) * k_1})")
        layer_1_results = self.layer_1.similarity_search_with_score(
            query,
            k=min(len(doc_ids) * k_1, 500),  # Limit to avoid explosion
        )
        
        section_ids = {}  # section_id → max_score
        for doc, score in layer_1_results:
            section_id = doc.metadata["section_id"]
            section_ids[section_id] = max(section_ids.get(section_id, 0), score)
        
        logger.debug(f"    Found {len(section_ids)} relevant sections")
        
        # Stage 3: Layer 2 — Get full text chunks
        logger.debug(f"  Stage 3: Layer 2 retrieval (k={k_2} per section)")
        for section_id in list(section_ids.keys())[:50]:  # Limit to top 50
            if section_id in self.layer_2_map:
                chunks = self.layer_2_map[section_id]
                # Get up to k_2 chunks per section
                for chunk in chunks[:k_2]:
                    results.append({
                        "content": chunk["content"],
                        "section_id": section_id,
                        "chunk_index": chunk["index"],
                        "layer_1_score": section_ids.get(section_id, 0),
                        "token_count": chunk["token_count"],
                    })
        
        logger.debug(f"    Retrieved {len(results)} total chunks")
        
        return results


# ============================================================================
# SECTION 3: HIERARCHICAL RAG PIPELINE
# ============================================================================

class HierarchicalRAGPipeline:
    """
    Complete hierarchical RAG system with reranking and generation.
    """
    
    def __init__(
        self,
        vector_store: HierarchicalVectorStore,
        reranker_model: str = "cross-encoder/qnli-distilroberta-base",
        top_k: int = 5,
        use_reranking: bool = True,
    ):
        """Initialize pipeline."""
        self.vector_store = vector_store
        self.reranker_model = reranker_model
        self.top_k = top_k
        self.use_reranking = use_reranking
        self.llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
        
        if use_reranking:
            self.reranker = CrossEncoder(reranker_model)
        else:
            self.reranker = None
        
        # Metrics
        self.metrics = {
            "queries_processed": 0,
            "avg_retrieval_chunks": 0,
            "avg_rerank_score": 0,
        }
    
    def retrieve(
        self,
        query: str,
        k_0: int = 20,
        k_1: int = 10,
        k_2: int = 5,
    ) -> List[Dict]:
        """
        Execute hierarchical retrieval with optional reranking.
        
        Args:
            query: User query
            k_0: Documents to find
            k_1: Sections per document
            k_2: Chunks per section
            
        Returns:
            Top-k chunks ranked by quality
        """
        logger.info(f"Pipeline retrieval: {query[:50]}...")
        
        # Hierarchical retrieval
        candidates = self.vector_store.retrieve_hierarchical(query, k_0, k_1, k_2)
        
        if not candidates:
            logger.warning("No candidates found in hierarchical retrieval")
            return []
        
        logger.info(f"Retrieved {len(candidates)} candidate chunks")
        
        # Optional: Rerank for final quality
        if self.use_reranking and self.reranker:
            logger.debug("Reranking candidates...")
            pairs = [[query, doc["content"]] for doc in candidates]
            scores = self.reranker.predict(pairs)
            
            # Attach scores
            for doc, score in zip(candidates, scores):
                doc["rerank_score"] = float(score)
            
            # Sort by rerank score
            candidates = sorted(
                candidates,
                key=lambda x: x.get("rerank_score", 0),
                reverse=True
            )
            
            avg_score = np.mean([c.get("rerank_score", 0) for c in candidates])
            logger.debug(f"Avg rerank score: {avg_score:.3f}")
        
        # Select top-k
        final_results = candidates[:self.top_k]
        
        # Update metrics
        self.metrics["queries_processed"] += 1
        self.metrics["avg_retrieval_chunks"] = len(candidates)
        if final_results:
            self.metrics["avg_rerank_score"] = np.mean([
                r.get("rerank_score", 0) for r in final_results
            ])
        
        logger.info(f"Selected {len(final_results)} top chunks for context")
        
        return final_results
    
    def generate(self, query: str) -> str:
        """
        Retrieve documents and generate answer.
        
        Args:
            query: User question
            
        Returns:
            Generated answer from LLM
        """
        # Retrieve
        docs = self.retrieve(query)
        
        # Assemble context
        context_parts = []
        for i, doc in enumerate(docs, 1):
            score_str = ""
            if "rerank_score" in doc:
                score_str = f" [confidence: {doc['rerank_score']:.2f}]"
            
            context_parts.append(
                f"[{i}] {doc['content'][:400]}{score_str}"
            )
        
        context = "\n\n".join(context_parts)
        
        # Generate answer
        prompt = f"""Answer the question using ONLY the provided context.

Context:
{context}

Question: {query}

Answer:"""
        
        response = self.llm.invoke(prompt)
        return response.content


# ============================================================================
# SECTION 4: EXAMPLE USAGE & HELPERS
# ============================================================================

def create_sample_documents() -> Tuple[List[str], List[str], List[List[Section]]]:
    """Create sample documents for demonstration."""
    
    docs_data = [
        {
            "id": "payments_guide",
            "title": "Payment Processing Integration Guide",
            "sections": [
                Section(
                    id="1.0",
                    title="Authentication & Setup",
                    content="""
                    Setting up payment authentication is critical for security.
                    You must use OAuth 2.0 for all API communications.
                    
                    Step 1: Generate API credentials
                    - Access your merchant dashboard
                    - Navigate to Settings → API Keys
                    - Generate public and private keys
                    - Store private key securely (never commit to version control)
                    
                    Step 2: Configure webhook endpoints
                    - Webhook URL must be HTTPS only
                    - Must respond with 2xx status within 30 seconds
                    - Sign all requests with X-Signature header
                    
                    Best practice: Use separate keys for development and production.
                    """
                ),
                Section(
                    id="2.0",
                    title="Error Handling & Recovery",
                    content="""
                    Understanding error codes is essential for robust payment systems.
                    
                    Error Code 1001: Insufficient Funds
                    - Temporary error, retry with exponential backoff
                    - User message: "Please ensure sufficient funds available"
                    - Retry strategy: Immediate retry (3x), then wait 24 hours
                    
                    Error Code 1002: Card Declined
                    - Possible network timeout, immediate retry recommended
                    - User message: "Transaction declined. Please try again."
                    - Retry strategy: Immediate retry (2x)
                    
                    Error Code 1003: Rate Limit Exceeded
                    - Too many requests in short time period
                    - Retry strategy: Exponential backoff starting at 5 seconds
                    - Max retries: 3 times
                    
                    Error Code 2001: Invalid API Key
                    - Configuration error, do not retry
                    - User message: "System configuration error"
                    - Action: Check credentials immediately
                    
                    General best practice: Always implement exponential backoff
                    with jitter to avoid thundering herd problem.
                    """
                ),
                Section(
                    id="3.0",
                    title="Webhook Processing",
                    content="""
                    Webhooks provide real-time payment status updates.
                    
                    Webhook Security:
                    - All webhook signatures must be verified
                    - Use HMAC-SHA256 for signature generation
                    - Headers: X-Signature (signature), X-Timestamp (unix timestamp)
                    - Reject webhooks older than 5 minutes
                    
                    Webhook Retry Logic:
                    - Failed webhooks are retried with exponential backoff
                    - Retries: Every 5 minutes for first hour
                    - Retries: Every hour for next 24 hours
                    - After 24 hours: Move to dead letter queue
                    
                    Idempotency is critical:
                    - Process same webhook_id only once
                    - Store webhook_id with timestamp in database
                    - Return 200 OK immediately (async processing)
                    
                    Example webhook payload:
                    {
                        "webhook_id": "wh_abc123",
                        "event": "payment.success",
                        "timestamp": 1625097600,
                        "data": {"transaction_id": "txn_xyz789"}
                    }
                    """
                ),
            ]
        },
        {
            "id": "api_reference",
            "title": "Payment API Reference",
            "sections": [
                Section(
                    id="1.0",
                    title="Endpoints Overview",
                    content="""
                    The Payment API provides REST endpoints for processing transactions.
                    
                    Base URL: https://api.payments.example.com/v2
                    
                    Core Endpoints:
                    - POST /transactions - Create new transaction
                    - GET /transactions/{id} - Get transaction status
                    - POST /refunds - Issue refund
                    - GET /webhooks - List webhooks
                    - POST /webhooks - Register webhook
                    
                    Rate Limits:
                    - Standard tier: 1000 requests/minute
                    - Premium tier: 5000 requests/minute
                    - Enterprise: Custom limits
                    
                    Authentication: Bearer token in Authorization header
                    """
                ),
                Section(
                    id="2.0",
                    title="Create Transaction Endpoint",
                    content="""
                    POST /transactions
                    
                    Request payload:
                    {
                        "amount": 1999,  // In cents
                        "currency": "USD",
                        "card_token": "tok_abc123",
                        "customer_id": "cust_xyz789",
                        "idempotency_key": "req_unique_id"
                    }
                    
                    Response (success):
                    {
                        "transaction_id": "txn_success001",
                        "status": "success",
                        "timestamp": 1625097600,
                        "amount": 1999,
                        "currency": "USD"
                    }
                    
                    Response (error):
                    {
                        "error_code": "1001",
                        "error_message": "Insufficient funds",
                        "transaction_id": "txn_failed001"
                    }
                    
                    Important: Use idempotency_key to prevent duplicate charges.
                    If you don't receive response, retry with same key.
                    """
                ),
            ]
        },
    ]
    
    doc_ids = []
    doc_titles = []
    doc_sections = []
    
    for doc in docs_data:
        doc_ids.append(doc["id"])
        doc_titles.append(doc["title"])
        doc_sections.append(doc["sections"])
    
    return doc_ids, doc_titles, doc_sections


def create_hierarchical_pipeline(
    sample_docs: bool = True,
) -> HierarchicalRAGPipeline:
    """
    Create and initialize a hierarchical RAG pipeline.
    
    Args:
        sample_docs: Whether to ingest sample documents
        
    Returns:
        Initialized HierarchicalRAGPipeline
    """
    # Create vector store
    vector_store = HierarchicalVectorStore()
    
    # Ingest sample documents
    if sample_docs:
        doc_ids, doc_titles, doc_sections_list = create_sample_documents()
        
        for doc_id, title, sections in zip(doc_ids, doc_titles, doc_sections_list):
            # Reconstruct full text from sections
            full_text = "\n\n".join([
                f"{section.title}\n{section.content}"
                for section in sections
            ])
            
            vector_store.ingest_document(
                doc_id=doc_id,
                title=title,
                full_text=full_text,
                sections=sections,
            )
    
    # Create pipeline
    pipeline = HierarchicalRAGPipeline(
        vector_store=vector_store,
        top_k=5,
        use_reranking=True,
    )
    
    return pipeline


def demo_hierarchical_retrieval():
    """Demonstrate hierarchical retrieval system."""
    print("=" * 80)
    print("DEMO: Hierarchical RAG Retrieval")
    print("=" * 80)
    
    pipeline = create_hierarchical_pipeline()
    
    query = "How do I handle payment processing errors?"
    print(f"\n📝 Query: {query}\n")
    
    # Execute retrieval
    docs = pipeline.retrieve(query, k_0=20, k_1=10, k_2=5)
    
    print("📚 Retrieved Context (Top 5 chunks):")
    print("-" * 80)
    for i, doc in enumerate(docs, 1):
        score_info = f"[score: {doc.get('rerank_score', 0):.3f}]"
        content_preview = doc['content'][:150].replace("\n", " ") + "..."
        print(f"{i}. {score_info} {content_preview}")
    
    # Generate answer
    print("\n🤖 Generated Answer:")
    print("-" * 80)
    answer = pipeline.generate(query)
    print(answer)
    
    # Metrics
    print("\n📊 Metrics:")
    print("-" * 80)
    for key, value in pipeline.metrics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    demo_hierarchical_retrieval()
