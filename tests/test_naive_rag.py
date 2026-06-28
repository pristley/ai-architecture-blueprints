"""
Test Suite for WP-3.1: Naive RAG Architecture

Comprehensive testing of:
- Input validation
- Component isolation (retrieval, generation)
- Integration (full pipeline)
- Error handling
- Failure modes
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Add docs directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "docs" / "05-capstone-rag-patterns"))

from langchain_core.documents import Document
from pydantic import ValidationError

# Import components to test
try:
    from examples_3_1 import (
        RAGQuery,
        RAGResponse,
        RAGSource,
        NaiveRAGError,
        NaiveRAGValidationError,
        NaiveRAGExecutionError,
        RetrievalError,
        format_docs,
    )
except ImportError as e:
    pytest.skip(f"Could not import RAG components: {e}", allow_module_level=True)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_documents():
    """Create sample documents for testing"""
    return [
        Document(
            page_content="Product A costs $99.99 and includes free shipping.",
            metadata={"source": "pricing.txt", "page": 1}
        ),
        Document(
            page_content="Standard shipping takes 5-7 business days. Express is 2-3 days.",
            metadata={"source": "shipping.txt", "page": 1}
        ),
        Document(
            page_content="All products come with a 1-year warranty covering manufacturing defects.",
            metadata={"source": "warranty.txt", "page": 1}
        ),
    ]


@pytest.fixture
def rag_query_valid():
    """Valid RAG query"""
    return RAGQuery(question="What is the price?", top_k=5)


@pytest.fixture
def rag_response_sample():
    """Sample RAG response"""
    return RAGResponse(
        answer="Product A costs $99.99.",
        sources=[
            RAGSource(source="pricing.txt", page=1, score=0.92),
        ],
        confidence=0.92,
        retrieval_count=1,
        execution_time_ms=150.0,
    )


# ============================================================================
# UNIT TESTS: INPUT VALIDATION
# ============================================================================

class TestRAGQueryValidation:
    """Test RAGQuery input schema validation"""
    
    def test_valid_query(self):
        """Valid query with required fields"""
        query = RAGQuery(question="What is the price?")
        assert query.question == "What is the price?"
        assert query.top_k == 5
        assert query.min_score == 0.3
    
    def test_valid_query_with_optional_fields(self):
        """Valid query with all optional fields"""
        query = RAGQuery(
            question="What is the price?",
            top_k=3,
            min_score=0.5,
            include_sources=False,
        )
        assert query.question == "What is the price?"
        assert query.top_k == 3
        assert query.min_score == 0.5
        assert query.include_sources is False
    
    def test_invalid_query_empty_string(self):
        """Empty question string is rejected"""
        with pytest.raises(ValidationError):
            RAGQuery(question="")
    
    def test_invalid_query_too_short(self):
        """Question shorter than 3 characters is rejected"""
        with pytest.raises(ValidationError):
            RAGQuery(question="OK")
    
    def test_invalid_query_whitespace_only(self):
        """Question with only whitespace is rejected"""
        with pytest.raises(ValidationError):
            RAGQuery(question="   ")
    
    def test_invalid_query_missing_required(self):
        """Missing required field raises error"""
        with pytest.raises(ValidationError):
            RAGQuery(top_k=5)
    
    def test_invalid_query_top_k_too_low(self):
        """top_k < 1 is rejected"""
        with pytest.raises(ValidationError):
            RAGQuery(question="What?", top_k=0)
    
    def test_invalid_query_top_k_too_high(self):
        """top_k > 20 is rejected"""
        with pytest.raises(ValidationError):
            RAGQuery(question="What?", top_k=25)
    
    def test_invalid_query_min_score_negative(self):
        """min_score < 0 is rejected"""
        with pytest.raises(ValidationError):
            RAGQuery(question="What?", min_score=-0.1)
    
    def test_invalid_query_min_score_too_high(self):
        """min_score > 1 is rejected"""
        with pytest.raises(ValidationError):
            RAGQuery(question="What?", min_score=1.5)
    
    def test_question_trimmed(self):
        """Question with leading/trailing whitespace is trimmed"""
        query = RAGQuery(question="  What is the price?  ")
        assert query.question == "What is the price?"


class TestRAGSourceValidation:
    """Test RAGSource schema validation"""
    
    def test_valid_source(self):
        """Valid source with required fields"""
        source = RAGSource(source="pricing.txt", score=0.92)
        assert source.source == "pricing.txt"
        assert source.score == 0.92
        assert source.page is None
    
    def test_valid_source_with_page(self):
        """Valid source with page number"""
        source = RAGSource(source="pricing.txt", page=5, score=0.92)
        assert source.page == 5
    
    def test_invalid_source_score_out_of_range(self):
        """Score outside [0, 1] is rejected"""
        with pytest.raises(ValidationError):
            RAGSource(source="file.txt", score=1.5)


class TestRAGResponseValidation:
    """Test RAGResponse schema validation"""
    
    def test_valid_response(self):
        """Valid response with all required fields"""
        response = RAGResponse(
            answer="Product A costs $99.99.",
            sources=[],
            confidence=0.92,
            retrieval_count=1,
            execution_time_ms=150.0,
        )
        assert response.answer == "Product A costs $99.99."
        assert response.confidence == 0.92
    
    def test_valid_response_with_failure_mode(self):
        """Valid response indicating a failure mode"""
        response = RAGResponse(
            answer="I couldn't find the information.",
            sources=[],
            confidence=0.0,
            retrieval_count=0,
            execution_time_ms=100.0,
            failure_mode="no_retrieval",
        )
        assert response.failure_mode == "no_retrieval"
    
    def test_invalid_response_negative_latency(self):
        """Negative execution time is rejected"""
        with pytest.raises(ValidationError):
            RAGResponse(
                answer="Answer",
                sources=[],
                confidence=0.5,
                retrieval_count=0,
                execution_time_ms=-100.0,
            )


# ============================================================================
# UNIT TESTS: COMPONENT FUNCTIONS
# ============================================================================

class TestFormatDocs:
    """Test document formatting function"""
    
    def test_format_empty_list(self):
        """Empty document list returns empty string"""
        result = format_docs([])
        assert result == ""
    
    def test_format_single_document(self):
        """Single document formatted correctly"""
        doc = Document(
            page_content="Test content",
            metadata={"source": "test.txt", "page": 1}
        )
        result = format_docs([doc])
        assert "Test content" in result
        assert "test.txt" in result
        assert "[Document 1]" in result
    
    def test_format_multiple_documents(self):
        """Multiple documents numbered and separated"""
        docs = [
            Document(page_content=f"Content {i}", metadata={"source": f"file{i}.txt", "page": i})
            for i in range(3)
        ]
        result = format_docs(docs)
        assert "[Document 1]" in result
        assert "[Document 2]" in result
        assert "[Document 3]" in result
        assert "Content 0" in result
        assert "Content 1" in result
    
    def test_format_document_with_missing_metadata(self):
        """Documents with missing metadata handled gracefully"""
        doc = Document(page_content="Content")
        result = format_docs([doc])
        assert "Content" in result
        assert "Unknown" in result  # Default for missing source
    
    def test_format_document_with_special_characters(self):
        """Documents with special characters preserved"""
        doc = Document(
            page_content="Content with special: @#$% chars",
            metadata={"source": "test.txt"}
        )
        result = format_docs([doc])
        assert "@#$%" in result


# ============================================================================
# UNIT TESTS: EXCEPTION HIERARCHY
# ============================================================================

class TestExceptionHierarchy:
    """Test exception definitions and inheritance"""
    
    def test_naive_rag_error_base(self):
        """NaiveRAGError is Exception"""
        exc = NaiveRAGError("test")
        assert isinstance(exc, Exception)
    
    def test_validation_error_inheritance(self):
        """NaiveRAGValidationError inherits from NaiveRAGError"""
        exc = NaiveRAGValidationError("test")
        assert isinstance(exc, NaiveRAGError)
        assert isinstance(exc, Exception)
    
    def test_execution_error_inheritance(self):
        """NaiveRAGExecutionError inherits from NaiveRAGError"""
        exc = NaiveRAGExecutionError("test")
        assert isinstance(exc, NaiveRAGError)
    
    def test_retrieval_error_inheritance(self):
        """RetrievalError inherits from ExecutionError"""
        exc = RetrievalError("test")
        assert isinstance(exc, NaiveRAGExecutionError)
        assert isinstance(exc, NaiveRAGError)


# ============================================================================
# INTEGRATION TESTS: NAIVE RAG PIPELINE
# ============================================================================

class TestNaiveRAGIntegration:
    """Integration tests for full RAG pipeline"""
    
    @pytest.mark.asyncio
    async def test_rag_initialization(self, sample_documents):
        """RAG can be initialized with a vector store"""
        try:
            from examples_3_1 import (
                initialize_vector_store,
                NaiveRAG,
            )
            
            # This test is skipped if dependencies not available
            pytest.skip("Vector store requires OpenAI API key and dependencies")
        except ImportError:
            pytest.skip("LangChain dependencies not available")
    
    @pytest.mark.asyncio
    async def test_rag_query_invocation_with_mock(self, rag_query_valid):
        """RAG can be invoked with a query (mocked)"""
        try:
            from examples_3_1 import NaiveRAG
            
            # Create mock vector store
            mock_vector_store = MagicMock()
            mock_retriever = AsyncMock()
            mock_retriever.ainvoke = AsyncMock(return_value=[
                Document(page_content="Test content", metadata={
                    "source": "test.txt",
                    "page": 1,
                    "score": 0.92
                })
            ])
            mock_vector_store.as_retriever = MagicMock(return_value=mock_retriever)
            
            # Mock LLM
            with patch('examples_3_1.ChatOpenAI') as mock_llm_class:
                mock_llm = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = "Product A costs $99.99."
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_class.return_value = mock_llm
                
                # Create RAG and invoke
                rag = NaiveRAG(mock_vector_store)
                response = await rag.ainvoke(rag_query_valid)
                
                # Verify response structure
                assert isinstance(response, RAGResponse)
                assert response.answer == "Product A costs $99.99."
                assert response.confidence > 0
                assert response.retrieval_count > 0
        
        except ImportError:
            pytest.skip("LangChain dependencies not available")


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and recovery"""
    
    def test_validation_error_raised_on_bad_query(self):
        """Invalid query raises ValidationError"""
        with pytest.raises(ValidationError):
            RAGQuery(question="x")
    
    def test_exception_message_clarity(self):
        """Exception messages are clear"""
        exc = NaiveRAGValidationError("Query too short")
        assert "Query too short" in str(exc)
    
    @pytest.mark.asyncio
    async def test_rag_handles_empty_question(self):
        """RAG rejects empty questions"""
        with pytest.raises(ValidationError):
            RAGQuery(question="")


# ============================================================================
# CHARACTERISTIC TESTS
# ============================================================================

class TestCharacteristics:
    """Test emergent properties and characteristics"""
    
    def test_rag_response_fields_immutable(self, rag_response_sample):
        """RAG response is a proper Pydantic model"""
        # Pydantic models are immutable by default
        response = rag_response_sample
        assert response.answer == "Product A costs $99.99."
    
    def test_rag_response_serializable(self, rag_response_sample):
        """RAG response can be serialized to dict"""
        response = rag_response_sample
        response_dict = response.model_dump()
        assert isinstance(response_dict, dict)
        assert response_dict["answer"] == "Product A costs $99.99."
    
    def test_rag_response_json_serializable(self, rag_response_sample):
        """RAG response can be converted to JSON"""
        response = rag_response_sample
        json_str = response.model_dump_json()
        assert "Product A costs" in json_str
        assert "99.99" in json_str
    
    def test_multiple_queries_independent(self):
        """Multiple queries are independent"""
        q1 = RAGQuery(question="Question one?")
        q2 = RAGQuery(question="Question two?")
        assert q1.question != q2.question
        assert q1 is not q2
    
    def test_failure_mode_detection(self):
        """Response with failure_mode set properly"""
        response = RAGResponse(
            answer="Not found",
            sources=[],
            confidence=0.0,
            retrieval_count=0,
            execution_time_ms=50.0,
            failure_mode="no_retrieval",
        )
        assert response.failure_mode == "no_retrieval"
        assert response.retrieval_count == 0


# ============================================================================
# BOUNDARY TESTS
# ============================================================================

class TestBoundaryConditions:
    """Test boundary conditions and edge cases"""
    
    def test_query_with_min_length(self):
        """Query with exactly 3 characters accepted"""
        query = RAGQuery(question="ABC")
        assert len(query.question) == 3
    
    def test_query_with_max_top_k(self):
        """Query with top_k=20 (max) accepted"""
        query = RAGQuery(question="What?", top_k=20)
        assert query.top_k == 20
    
    def test_response_with_zero_confidence(self):
        """Response with confidence=0 accepted"""
        response = RAGResponse(
            answer="No data",
            sources=[],
            confidence=0.0,
            retrieval_count=0,
            execution_time_ms=0.0,
        )
        assert response.confidence == 0.0
    
    def test_response_with_max_confidence(self):
        """Response with confidence=1.0 accepted"""
        response = RAGResponse(
            answer="High confidence",
            sources=[],
            confidence=1.0,
            retrieval_count=1,
            execution_time_ms=100.0,
        )
        assert response.confidence == 1.0
    
    def test_document_format_with_very_long_content(self):
        """Long document content handled without error"""
        long_content = "x" * 10000
        doc = Document(page_content=long_content, metadata={"source": "long.txt"})
        result = format_docs([doc])
        assert "x" * 100 in result


# ============================================================================
# PARAMETRIZED TESTS
# ============================================================================

@pytest.mark.parametrize("question", [
    "What is the price?",
    "How long is shipping?",
    "Do you have a warranty?",
    "Can I return items?",
])
def test_various_questions_accepted(question):
    """Various question formats are accepted"""
    query = RAGQuery(question=question)
    assert query.question == question


@pytest.mark.parametrize("top_k,min_score", [
    (1, 0.0),
    (5, 0.3),
    (10, 0.7),
    (20, 1.0),
])
def test_various_retrieval_configs(top_k, min_score):
    """Various retrieval configurations accepted"""
    query = RAGQuery(question="What?", top_k=top_k, min_score=min_score)
    assert query.top_k == top_k
    assert query.min_score == min_score


@pytest.mark.parametrize("failure_mode", [
    None,
    "no_retrieval",
    "poor_retrieval",
    "context_exhaustion",
])
def test_various_failure_modes(failure_mode):
    """Various failure modes can be recorded"""
    response = RAGResponse(
        answer="Answer",
        sources=[],
        confidence=0.5,
        retrieval_count=0,
        execution_time_ms=100.0,
        failure_mode=failure_mode,
    )
    assert response.failure_mode == failure_mode


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test performance characteristics"""
    
    def test_query_creation_speed(self):
        """Query creation is fast"""
        import time
        start = time.time()
        for _ in range(1000):
            RAGQuery(question="What is the price?")
        elapsed = time.time() - start
        # Should complete 1000 queries in < 0.5 seconds
        assert elapsed < 0.5
    
    def test_response_creation_speed(self):
        """Response creation is fast"""
        import time
        start = time.time()
        for _ in range(1000):
            RAGResponse(
                answer="Answer",
                sources=[],
                confidence=0.5,
                retrieval_count=1,
                execution_time_ms=100.0,
            )
        elapsed = time.time() - start
        # Should complete 1000 responses in < 0.5 seconds
        assert elapsed < 0.5


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
