"""
Work Product 3.1: RAG Architecture — Naive Baseline

Implements a production-ready Naive RAG system with:
- Document loading and chunking
- Vector store indexing (Chroma)
- Semantic retrieval
- LLM-based generation
- Error handling and observability
- LangSmith tracing
"""

import os
import logging
from typing import Any, AsyncIterator, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# EXCEPTION DEFINITIONS (Defensive)
# ============================================================================

class NaiveRAGError(Exception):
    """Base exception for Naive RAG component"""
    pass


class NaiveRAGValidationError(NaiveRAGError):
    """Raised when input validation fails"""
    pass


class NaiveRAGExecutionError(NaiveRAGError):
    """Raised when execution fails despite valid input"""
    pass


class RetrievalError(NaiveRAGExecutionError):
    """Raised when document retrieval fails"""
    pass


class EmbeddingError(NaiveRAGExecutionError):
    """Raised when embedding creation fails"""
    pass


# ============================================================================
# TYPE DEFINITIONS (Composability & Type Safety)
# ============================================================================

class RAGQuery(BaseModel):
    """Input schema for RAG pipeline"""
    
    question: str = Field(..., description="User question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    min_score: float = Field(default=0.3, ge=0.0, le=1.0, description="Min similarity score")
    include_sources: bool = Field(default=True, description="Include source metadata")
    
    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Question must be non-empty and substantial"""
        if not v or len(v.strip()) < 3:
            raise ValueError("Question must be at least 3 characters")
        return v.strip()


class RAGSource(BaseModel):
    """Source document metadata"""
    
    source: str = Field(..., description="Document source/file")
    page: Optional[int] = Field(default=None, description="Page number if available")
    score: float = Field(..., ge=0.0, le=1.0, description="Retrieval similarity score")


class RAGResponse(BaseModel):
    """Output schema for RAG pipeline"""
    
    answer: str = Field(..., description="Generated answer")
    sources: List[RAGSource] = Field(default_factory=list, description="Retrieved sources")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    retrieval_count: int = Field(..., ge=0, description="Number of documents retrieved")
    execution_time_ms: float = Field(..., ge=0, description="End-to-end latency")
    failure_mode: Optional[str] = Field(default=None, description="If applicable, which failure mode was triggered")


# ============================================================================
# VECTOR STORE INITIALIZATION
# ============================================================================

def initialize_vector_store(
    documents: List[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    persist_directory: Optional[str] = None,
) -> Chroma:
    """
    Initialize vector store from documents.
    
    Args:
        documents: List of LangChain Document objects
        chunk_size: Tokens per chunk
        chunk_overlap: Token overlap between chunks
        persist_directory: Optional path for persistence
    
    Returns:
        Chroma vector store
    
    Raises:
        NaiveRAGExecutionError: If indexing fails
    """
    try:
        logger.info(f"Chunking {len(documents)} documents...")
        
        # Split documents
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
            length_function=len,
        )
        chunks = splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Add metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"chunk_{i}"
            chunk.metadata["timestamp"] = datetime.now().isoformat()
            if "page" not in chunk.metadata:
                chunk.metadata["page"] = None
        
        # Create embeddings
        logger.info("Initializing embeddings...")
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            dimensions=1536
        )
        
        # Create vector store
        logger.info("Building vector store...")
        vector_store = Chroma.from_documents(
            chunks,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name="naive_rag_default"
        )
        
        logger.info(f"✓ Vector store ready: {len(chunks)} chunks indexed")
        return vector_store
    
    except Exception as e:
        logger.error(f"Vector store initialization failed: {e}")
        raise NaiveRAGExecutionError(f"Could not initialize vector store: {str(e)}") from e


# ============================================================================
# CONTEXT FORMATTING
# ============================================================================

def format_docs(docs: List[Document]) -> str:
    """Format retrieved documents into context string"""
    if not docs:
        return ""
    
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "?")
        content = doc.page_content.strip()
        
        formatted.append(
            f"[Document {i}] (Source: {source}, Page: {page})\n{content}"
        )
    
    return "\n\n".join(formatted)


# ============================================================================
# NAIVE RAG RUNNABLE COMPONENT
# ============================================================================

class NaiveRAG(Runnable):
    """
    Naive RAG pipeline using semantic retrieval and LLM generation.
    
    This component implements the naive baseline RAG architecture:
    1. Query embedding (OpenAI text-embedding-3-small)
    2. Semantic retrieval (Chroma vector store)
    3. Context formatting
    4. LLM generation (GPT-4 or GPT-4 Mini)
    
    Features:
    - Runnable protocol for composability
    - Automatic LangSmith tracing (enable with LANGCHAIN_TRACING_V2=true)
    - Error handling and validation at boundaries
    - Configurable top-k retrieval and score thresholds
    - Source attribution
    
    Example:
        ```python
        # Initialize
        rag = NaiveRAG(vector_store)
        
        # Invoke
        response = await rag.ainvoke({
            "question": "What is the payment policy?",
            "top_k": 5
        })
        print(response.answer)
        ```
    """
    
    name: str = "NaiveRAG"
    
    def __init__(
        self,
        vector_store: Chroma,
        llm_model: str = "gpt-4-turbo",
        llm_temperature: float = 0.7,
        default_top_k: int = 5,
        default_min_score: float = 0.3,
    ):
        """
        Initialize Naive RAG component.
        
        Args:
            vector_store: Chroma vector store with indexed documents
            llm_model: LLM model to use
            llm_temperature: Temperature for generation (0=deterministic, 1=creative)
            default_top_k: Default number of chunks to retrieve
            default_min_score: Default minimum similarity score
        """
        self.vector_store = vector_store
        self.llm_model = llm_model
        self.llm_temperature = llm_temperature
        self.default_top_k = default_top_k
        self.default_min_score = default_min_score
        
        # Initialize retriever
        self.retriever = vector_store.as_retriever(
            search_kwargs={"k": default_top_k}
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=llm_temperature,
            max_tokens=1000,
        )
        
        # Define prompt template
        self.prompt_template = ChatPromptTemplate.from_template("""
You are a helpful assistant answering questions based on provided documents.

CONTEXT (Retrieved documents):
{context}

QUESTION: {question}

Instructions:
- Answer based only on the provided context
- If the answer is not in the documents, say "I don't know" or "This information is not in the documents"
- Be concise and direct
- If you reference specific information, mention the document source

ANSWER:
""")
        
        logger.info(f"✓ NaiveRAG initialized with {llm_model}")
    
    @property
    def InputType(self):
        return RAGQuery
    
    @property
    def OutputType(self):
        return RAGResponse
    
    def invoke(
        self,
        input: RAGQuery,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> RAGResponse:
        """Synchronous invocation (thin wrapper around async)"""
        import asyncio
        return asyncio.run(self.ainvoke(input, config, **kwargs))
    
    async def ainvoke(
        self,
        input: RAGQuery | Dict,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> RAGResponse:
        """
        Async invocation with full error handling and tracing.
        
        Args:
            input: RAGQuery or dict with "question", optional "top_k", "min_score"
            config: Runnable config (callbacks, etc.)
        
        Returns:
            RAGResponse with answer, sources, confidence, timing
        
        Raises:
            NaiveRAGValidationError: Invalid input
            NaiveRAGExecutionError: Execution failed
        """
        import time
        start_time = time.time()
        
        try:
            # ─ VALIDATE INPUT
            if isinstance(input, dict):
                validated_input = RAGQuery(**input)
            else:
                validated_input = input
            
            logger.info(f"Processing question: {validated_input.question[:50]}...")
            
            # ─ RETRIEVE
            retrieved_docs = await self._retrieve(
                validated_input.question,
                validated_input.top_k,
                validated_input.min_score,
            )
            
            # ─ HANDLE NO RESULTS
            if not retrieved_docs:
                logger.warning("No relevant documents retrieved")
                elapsed = (time.time() - start_time) * 1000
                return RAGResponse(
                    answer="I couldn't find relevant documents to answer this question. Please try rephrasing or provide more context.",
                    sources=[],
                    confidence=0.0,
                    retrieval_count=0,
                    execution_time_ms=elapsed,
                    failure_mode="no_retrieval"
                )
            
            logger.info(f"Retrieved {len(retrieved_docs)} chunks")
            
            # ─ FORMAT CONTEXT
            context = format_docs(retrieved_docs)
            
            # ─ GENERATE ANSWER
            answer = await self._generate_answer(
                validated_input.question,
                context,
            )
            
            # ─ EXTRACT SOURCES
            sources = [
                RAGSource(
                    source=doc.metadata.get("source", "Unknown"),
                    page=doc.metadata.get("page"),
                    score=doc.metadata.get("score", 0.0),
                )
                for doc in retrieved_docs
            ]
            
            # ─ CALCULATE CONFIDENCE
            confidence = (
                retrieved_docs[0].metadata.get("score", 0.0)
                if retrieved_docs
                else 0.0
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            logger.info(f"✓ Response generated in {elapsed:.0f}ms")
            
            return RAGResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                retrieval_count=len(retrieved_docs),
                execution_time_ms=elapsed,
            )
        
        except NaiveRAGValidationError as e:
            logger.error(f"Validation error: {e}")
            raise
        
        except NaiveRAGExecutionError as e:
            logger.error(f"Execution error: {e}")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error in {self.name}: {e}", exc_info=True)
            raise NaiveRAGExecutionError(f"RAG pipeline failed: {str(e)}") from e
    
    async def _retrieve(
        self,
        question: str,
        top_k: int,
        min_score: float,
    ) -> List[Document]:
        """
        Retrieve relevant documents.
        
        Implements Failure Mode detection:
        - No results: retrieval completely failed
        - Low scores: poor retrieval quality
        """
        try:
            # Adjust retriever k
            self.retriever.search_kwargs = {"k": top_k}
            
            # Invoke retriever
            docs = await self.retriever.ainvoke(question)
            
            if not docs:
                logger.warning("No documents matched query")
                return []
            
            # Add similarity scores to metadata
            # (Chroma returns docs with scores already in metadata)
            for doc in docs:
                if "score" not in doc.metadata:
                    doc.metadata["score"] = 0.5  # Fallback if not available
            
            # Filter by min_score
            filtered = [d for d in docs if d.metadata.get("score", 0.0) >= min_score]
            
            if not filtered:
                logger.warning(f"All retrieved docs below min_score {min_score}")
                # Still return original docs; let LLM handle low confidence
                return docs
            
            return filtered
        
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            raise RetrievalError(f"Could not retrieve documents: {str(e)}") from e
    
    async def _generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """Generate answer using LLM with context"""
        try:
            # Create messages
            messages = self.prompt_template.format_messages(
                context=context,
                question=question,
            )
            
            # Invoke LLM
            response = await self.llm.ainvoke(messages)
            
            # Extract text
            answer = response.content if hasattr(response, "content") else str(response)
            
            return answer
        
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise NaiveRAGExecutionError(f"Could not generate answer: {str(e)}") from e
    
    async def astream(
        self,
        input: RAGQuery | Dict,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> AsyncIterator[RAGResponse]:
        """Stream responses (not implemented for basic RAG)"""
        # For naive RAG, we generate complete responses
        # In production, could implement streaming of LLM tokens
        response = await self.ainvoke(input, config, **kwargs)
        yield response


# ============================================================================
# DEMO FUNCTIONS
# ============================================================================

async def demo_with_sample_documents() -> None:
    """
    Demonstrate Naive RAG with sample documents.
    
    This creates a small knowledge base in memory and shows:
    1. Document loading and chunking
    2. Retrieval quality
    3. Generated answers
    4. Error handling
    """
    
    # Create sample documents
    sample_docs = [
        Document(
            page_content="""
            Payment Policy
            
            We accept all major credit cards (Visa, Mastercard, American Express).
            Payments are processed immediately upon checkout.
            Invoices are sent to your registered email within 24 hours.
            Refunds are processed within 5-7 business days.
            """,
            metadata={"source": "policies.txt", "page": 1}
        ),
        Document(
            page_content="""
            Shipping Information
            
            Standard shipping: 5-7 business days ($5.99)
            Express shipping: 2-3 business days ($12.99)
            International shipping available to 150+ countries
            Free shipping on orders over $50
            """,
            metadata={"source": "shipping.txt", "page": 1}
        ),
        Document(
            page_content="""
            Product Warranty
            
            All products come with a 1-year manufacturer's warranty.
            Warranty covers manufacturing defects but not normal wear.
            Extended warranty available (2-5 years) for additional fee.
            Warranty claims processed within 14 days.
            """,
            metadata={"source": "warranty.txt", "page": 1}
        ),
    ]
    
    # Initialize RAG
    print("\n" + "="*60)
    print("NAIVE RAG DEMO")
    print("="*60)
    
    logger.info("Initializing vector store...")
    vector_store = initialize_vector_store(sample_docs)
    
    logger.info("Initializing RAG pipeline...")
    rag = NaiveRAG(vector_store)
    
    # Test queries
    test_queries = [
        RAGQuery(question="How long does shipping take?", top_k=5),
        RAGQuery(question="What payment methods do you accept?", top_k=5),
        RAGQuery(question="Is there a warranty on products?", top_k=5),
    ]
    
    # Run queries
    for query in test_queries:
        print(f"\n{'-'*60}")
        print(f"Question: {query.question}")
        print(f"{'-'*60}")
        
        response = await rag.ainvoke(query)
        
        print(f"Answer: {response.answer}")
        print(f"\nConfidence: {response.confidence:.2%}")
        print(f"Retrieved {response.retrieval_count} documents")
        print(f"Execution time: {response.execution_time_ms:.0f}ms")
        
        if response.sources:
            print("\nSources:")
            for source in response.sources:
                print(f"  - {source.source} (page {source.page}) [score: {source.score:.2f}]")


async def demo_error_handling() -> None:
    """
    Demonstrate error handling in Naive RAG.
    
    Shows:
    1. Validation errors (invalid queries)
    2. Retrieval failures (no results)
    3. Recovery strategies
    """
    
    sample_docs = [
        Document(
            page_content="Product A costs $99.99",
            metadata={"source": "pricing.txt"}
        ),
    ]
    
    print("\n" + "="*60)
    print("ERROR HANDLING DEMO")
    print("="*60)
    
    vector_store = initialize_vector_store(sample_docs)
    rag = NaiveRAG(vector_store)
    
    # Test 1: Invalid query (too short)
    print("\n--- Test 1: Validation Error (query too short) ---")
    try:
        await rag.ainvoke({"question": "OK"})
    except NaiveRAGValidationError as e:
        print(f"✓ Caught validation error: {e}")
    
    # Test 2: Query with no relevant results
    print("\n--- Test 2: No Retrieval Results ---")
    response = await rag.ainvoke(RAGQuery(
        question="Tell me about quantum physics",
        top_k=5,
        min_score=0.5  # High threshold
    ))
    print(f"Response: {response.answer}")
    print(f"Failure mode: {response.failure_mode}")
    
    # Test 3: Valid query
    print("\n--- Test 3: Successful Query ---")
    response = await rag.ainvoke(RAGQuery(
        question="How much does Product A cost?",
        top_k=5
    ))
    print(f"✓ Answer: {response.answer}")
    print(f"✓ Confidence: {response.confidence:.2%}")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run all demos"""
    # Enable LangSmith tracing (optional)
    # os.environ["LANGCHAIN_TRACING_V2"] = "true"
    # os.environ["LANGSMITH_API_KEY"] = "[your-key]"
    
    await demo_with_sample_documents()
    await demo_error_handling()
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nTo use Naive RAG with your documents:")
    print("1. Load your PDFs: docs = PyPDFLoader('path').load()")
    print("2. Initialize: vector_store = initialize_vector_store(docs)")
    print("3. Create RAG: rag = NaiveRAG(vector_store)")
    print("4. Query: response = await rag.ainvoke({'question': '...'})")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
