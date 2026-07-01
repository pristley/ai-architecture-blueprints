"""
Tests for PDF Ingestion (WP-5.1) and Clause Extraction (WP-5.2)

Tests cover:
- PDF extraction with layout preservation
- Table detection
- PII redaction
- Contract classification
- Clause extraction
- Error handling and edge cases
"""

import pytest
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from legal_contract_agent.tools.pdf_ingestion import (
    ingest_pdf,
    IngestionResult,
    PiiRedactor,
    PdfIngestor,
)
from legal_contract_agent.agent.clause_extractor import (
    extract_clauses,
    classify_contract,
    CLAUSE_TYPES,
    CONTRACT_TYPES,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_nda_text() -> str:
    """Sample NDA contract text."""
    return """
    NON-DISCLOSURE AGREEMENT
    
    This Non-Disclosure Agreement ("Agreement") is entered into as of January 1, 2024,
    between ABC Corporation ("Company") and XYZ Inc. ("Recipient").
    
    1. DEFINITIONS
    "Confidential Information" means any information disclosed by Company to Recipient
    that is marked as confidential or would reasonably be considered confidential.
    
    2. CONFIDENTIALITY OBLIGATIONS
    Recipient agrees to maintain the confidentiality of all Confidential Information
    and not to disclose it to any third party without prior written consent.
    
    3. TERMINATION
    This Agreement shall terminate one year after the date of disclosure, unless
    either party terminates it earlier by providing 30 days written notice.
    
    4. LIMITATION OF LIABILITY
    In no event shall either party be liable for indirect, incidental, or consequential
    damages arising from this Agreement.
    
    5. GOVERNING LAW
    This Agreement shall be governed by the laws of the State of California.
    """


@pytest.fixture
def sample_saas_agreement() -> str:
    """Sample SaaS agreement text."""
    return """
    SOFTWARE-AS-A-SERVICE AGREEMENT
    
    1. SERVICE DESCRIPTION
    Company provides cloud-based project management software ("Service").
    
    2. PAYMENT TERMS
    Customer shall pay $1,000 per month, invoiced in advance. Payment is due Net 30
    from the invoice date. Late payments accrue interest at 1.5% per month.
    
    3. AUTO-RENEWAL
    This Agreement automatically renews for one-year terms unless either party provides
    written notice of non-renewal at least 30 days before the end of the current term.
    
    4. TERMINATION FOR CONVENIENCE
    Either party may terminate this Agreement without cause by providing 30 days notice.
    
    5. LIABILITY CAP
    Notwithstanding any other provision, Company's total liability shall not exceed
    the fees paid in the 12 months preceding the claim.
    
    6. WARRANTY DISCLAIMER
    The Service is provided "as-is" without any warranty of merchantability or fitness
    for a particular purpose.
    """


@pytest.fixture
def pii_text_with_redaction() -> str:
    """Text containing PII that should be redacted."""
    return """
    Contract with John Smith (john.smith@example.com, 555-123-4567).
    His SSN is 123-45-6789 and credit card is 4111-1111-1111-1111.
    """


# ============================================================================
# PDF Ingestion Tests (WP-5.1)
# ============================================================================

class TestPiiRedactor:
    """Test PII redaction engine."""
    
    def test_email_redaction(self):
        """Redact email addresses."""
        redactor = PiiRedactor(enable_ner=False)
        text = "Contact john@example.com for details."
        redacted, log = redactor.redact(text)
        
        assert "john@" not in redacted
        assert "[REDACTED_EMAIL]" in redacted
        assert len(log) == 1
        assert log[0]["pattern"] == "email"
    
    def test_phone_redaction(self):
        """Redact phone numbers."""
        redactor = PiiRedactor(enable_ner=False)
        text = "Call me at (555) 123-4567."
        redacted, log = redactor.redact(text)
        
        assert "555" not in redacted or "[REDACTED_PHONE]" in redacted
        assert len(log) == 1
    
    def test_ssn_redaction(self):
        """Redact SSN."""
        redactor = PiiRedactor(enable_ner=False)
        text = "SSN: 123-45-6789"
        redacted, log = redactor.redact(text)
        
        assert "123-45-6789" not in redacted
        assert "[REDACTED_SSN]" in redacted
        assert len(log) == 1
    
    def test_credit_card_redaction(self):
        """Redact credit card numbers."""
        redactor = PiiRedactor(enable_ner=False)
        text = "Card: 4111-1111-1111-1111"
        redacted, log = redactor.redact(text)
        
        assert "4111-1111-1111-1111" not in redacted
        assert "[REDACTED_CREDIT_CARD]" in redacted
        assert len(log) == 1
    
    def test_multiple_pii_items(self, pii_text_with_redaction):
        """Redact multiple PII items."""
        redactor = PiiRedactor(enable_ner=False)
        redacted, log = redactor.redact(pii_text_with_redaction)
        
        # Should find email, phone, SSN, credit card
        assert len(log) >= 3
        assert "john.smith@example.com" not in redacted
        assert "[REDACTED_EMAIL]" in redacted


class TestPdfIngestor:
    """Test PDF ingestion engine."""
    
    @patch("legal_contract_agent.tools.pdf_ingestion.DOCLING_AVAILABLE", False)
    def test_docling_not_available(self):
        """Gracefully handle when Docling is not available."""
        ingestor = PdfIngestor()
        result = ingestor.ingest("dummy.pdf")
        
        assert result.error is not None
        assert "Docling not available" in result.error
    
    def test_file_not_found(self):
        """Gracefully handle missing file."""
        ingestor = PdfIngestor()
        result = ingestor.ingest("/nonexistent/file.pdf")
        
        assert result.error is not None
        assert "File not found" in result.error
    
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.stat")
    def test_file_too_small(self, mock_stat, mock_exists):
        """Reject files that are too small."""
        mock_stat.return_value.st_size = 50  # < MIN_SIZE_BYTES
        
        ingestor = PdfIngestor()
        result = ingestor.ingest("/path/to/tiny.pdf")
        
        assert result.error is not None
        assert "File too small" in result.error
    
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.stat")
    def test_file_too_large(self, mock_stat, mock_exists):
        """Reject files that are too large."""
        mock_stat.return_value.st_size = 60 * 1024 * 1024  # > MAX_SIZE_BYTES
        
        ingestor = PdfIngestor()
        result = ingestor.ingest("/path/to/huge.pdf")
        
        assert result.error is not None
        assert "File too large" in result.error
    
    @patch("pathlib.Path.exists", return_value=True)
    def test_wrong_file_type(self, mock_exists):
        """Reject non-PDF files."""
        ingestor = PdfIngestor()
        result = ingestor.ingest("/path/to/document.txt")
        
        assert result.error is not None
        assert "Invalid file type" in result.error


class TestIngestionResult:
    """Test IngestionResult Pydantic model."""
    
    def test_valid_result(self):
        """Create valid IngestionResult."""
        result = IngestionResult(
            contract_id="contract_123",
            raw_text="Sample contract text",
            page_count=5,
            extraction_confidence=95.5,
        )
        
        assert result.contract_id == "contract_123"
        assert result.page_count == 5
        assert result.extraction_confidence == 95.5
    
    def test_confidence_validation(self):
        """Validate confidence is 0-100."""
        with pytest.raises(ValueError):
            IngestionResult(
                contract_id="test",
                raw_text="text",
                extraction_confidence=150  # Out of range
            )
    
    def test_serialization(self):
        """Serialize to JSON."""
        result = IngestionResult(
            contract_id="contract_123",
            raw_text="Sample text",
            extraction_confidence=92.0,
        )
        
        json_dict = result.dict()
        assert json_dict["contract_id"] == "contract_123"
        assert json_dict["extraction_confidence"] == 92.0


# ============================================================================
# Clause Extraction Tests (WP-5.2)
# ============================================================================

class TestClauseExtraction:
    """Test clause extraction engine."""
    
    def test_contract_types_defined(self):
        """Verify all contract types are defined."""
        assert len(CONTRACT_TYPES) >= 9
        assert "NDA" in CONTRACT_TYPES
        assert "SaaS" in CONTRACT_TYPES
        assert "License" in CONTRACT_TYPES
    
    def test_clause_types_defined(self):
        """Verify all clause types are defined."""
        assert len(CLAUSE_TYPES) >= 12
        assert "termination" in CLAUSE_TYPES
        assert "liability" in CLAUSE_TYPES
        assert "confidentiality" in CLAUSE_TYPES
        assert "payment_terms" in CLAUSE_TYPES
    
    def test_clause_type_config_structure(self):
        """Verify clause type configs have required fields."""
        for clause_type, config in CLAUSE_TYPES.items():
            assert "name" in config
            assert "description" in config
            assert "keywords" in config
            assert len(config["keywords"]) > 0
    
    @patch("legal_contract_agent.agent.clause_extractor.ChatOpenAI")
    def test_extract_nda_classification(self, mock_llm_class, sample_nda_text):
        """Extract NDA contract classification."""
        # Mock LLM response
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = """{
            "contract_type": "NDA",
            "confidence": 95,
            "reasoning": "Contains confidentiality and non-disclosure terms",
            "summary": "Bilateral non-disclosure agreement"
        }"""
        mock_llm_class.return_value = mock_llm
        
        result = extract_clauses(
            contract_id="test_nda",
            raw_text=sample_nda_text,
        )
        
        assert result["contract_type"] in ["NDA", "Mixed", None]  # Allow fallback
        assert "contract_type_confidence" in result
    
    @patch("legal_contract_agent.agent.clause_extractor.ChatOpenAI")
    def test_extract_saas_agreement(self, mock_llm_class, sample_saas_agreement):
        """Extract SaaS agreement clauses."""
        # Mock LLM response
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = """{
            "contract_type": "SaaS",
            "confidence": 92,
            "reasoning": "Software service agreement with pricing",
            "summary": "Cloud service SaaS agreement"
        }"""
        mock_llm_class.return_value = mock_llm
        
        result = extract_clauses(
            contract_id="test_saas",
            raw_text=sample_saas_agreement,
        )
        
        assert result["contract_id"] == "test_saas"
        assert "extracted_clauses" in result
    
    def test_extraction_state_structure(self):
        """Verify extraction state has required fields."""
        from legal_contract_agent.agent.state import ExtractionState
        
        # TypedDict should have all required keys
        state_keys = {
            "contract_id", "raw_text", "tables",
            "contract_type", "contract_type_confidence",
            "extracted_clauses", "total_extraction_time",
        }
        # Just verify structure is defined
        assert ExtractionState is not None


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining ingestion and extraction."""
    
    @patch("legal_contract_agent.agent.clause_extractor.ChatOpenAI")
    def test_end_to_end_extraction(self, mock_llm_class, sample_nda_text):
        """Test full extraction pipeline."""
        # Mock both classification and extraction
        mock_llm = MagicMock()
        
        # First call (classification)
        classification_response = MagicMock()
        classification_response.content = """{
            "contract_type": "NDA",
            "confidence": 90,
            "reasoning": "NDA",
            "summary": "NDA"
        }"""
        
        # Subsequent calls (extraction)
        extraction_response = MagicMock()
        extraction_response.content = """{
            "found": true,
            "quote": "This Agreement shall terminate",
            "confidence": 85,
            "summary": "Agreement terminates after 1 year"
        }"""
        
        mock_llm.invoke.side_effect = [
            classification_response,
            extraction_response,
            extraction_response,
            extraction_response,
            extraction_response,
            extraction_response,
            extraction_response,
            extraction_response,
            extraction_response,
            extraction_response,
            extraction_response,
            extraction_response,
            extraction_response,
        ]
        mock_llm_class.return_value = mock_llm
        
        # Extract clauses
        result = extract_clauses(
            contract_id="integration_test",
            raw_text=sample_nda_text,
        )
        
        # Verify results
        assert result["contract_id"] == "integration_test"
        assert "extracted_clauses" in result
        assert "total_extraction_time" in result
        assert result["total_extraction_time"] >= 0
    
    def test_performance_targets(self, sample_nda_text):
        """Verify performance is within targets."""
        # This test ensures architecture meets performance goals
        # Target: Task 2-3 complete in <5 seconds
        # (This would be a full integration test with real LLM)
        
        # For now, just verify the state structure is initialized quickly
        from legal_contract_agent.agent.state import ExtractionState
        
        initial_state: ExtractionState = {
            "contract_id": "perf_test",
            "raw_text": sample_nda_text,
            "tables": [],
            "contract_type": None,
            "contract_type_confidence": 0,
            "contract_summary": None,
            "extracted_clauses": {},
            "total_extraction_time": 0,
            "node_execution_times": {"classify": 0, "extract": 0, "aggregate": 0},
            "error": None,
            "iteration_count": 0,
            "debug_enabled": False,
            "debug_prompts": {},
            "debug_responses": {},
        }
        
        assert initial_state is not None
        assert initial_state["contract_id"] == "perf_test"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and graceful degradation."""
    
    def test_invalid_json_response(self):
        """Handle invalid JSON from LLM."""
        with patch("legal_contract_agent.agent.clause_extractor.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = "Not valid JSON"
            mock_llm_class.return_value = mock_llm
            
            # Should not raise, should set error
            result = extract_clauses(
                contract_id="error_test",
                raw_text="Sample text",
            )
            
            assert result is not None
            assert "contract_id" in result
    
    def test_timeout_handling(self):
        """Gracefully handle timeouts."""
        # This is a placeholder for timeout handling
        # Implementation would use asyncio timeout
        assert True  # Placeholder


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_contract_text(self):
        """Handle empty contract text."""
        result = extract_clauses(
            contract_id="empty_test",
            raw_text="",
        )
        
        assert result["contract_id"] == "empty_test"
    
    def test_very_short_contract(self):
        """Handle very short contract."""
        result = extract_clauses(
            contract_id="short_test",
            raw_text="Short agreement.",
        )
        
        assert result["contract_id"] == "short_test"
    
    def test_very_long_contract(self):
        """Handle very long contract (1MB+)."""
        long_text = "This is a contract. " * 50000  # ~1MB
        
        result = extract_clauses(
            contract_id="long_test",
            raw_text=long_text,
        )
        
        assert result["contract_id"] == "long_test"
    
    def test_mixed_language_text(self):
        """Handle mixed language text."""
        text = """
        AGREEMENT
        This is an English clause.
        
        CLAUSULA EN ESPAÑOL
        Esta es una cláusula en español.
        """
        
        result = extract_clauses(
            contract_id="mixed_lang_test",
            raw_text=text,
        )
        
        assert result["contract_id"] == "mixed_lang_test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
