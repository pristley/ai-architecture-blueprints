"""
Unit tests for WP-1.7: Introduction to Tracing with LangSmith
"""

import pytest
import os


def test_wp_1_7_exists():
    """WP-1.7 document should exist."""
    assert os.path.exists("WP-1.7-Introduction-to-Tracing-with-LangSmith.md"), \
        "WP-1.7 document not found"


def test_wp_1_7_contains_tracing_concepts():
    """WP-1.7 should cover core LangSmith tracing concepts."""
    with open("WP-1.7-Introduction-to-Tracing-with-LangSmith.md", "r") as f:
        text = f.read()
    
    # Check for key concepts
    concepts = [
        "LangSmith",
        "trace",
        "token",
        "latency",
        "TTFT",
        "observability",
        "debugging",
        "cost",
    ]
    
    for concept in concepts:
        assert concept.lower() in text.lower(), \
            f"WP-1.7 must cover concept: {concept}"
    
    # Check for key sections
    sections = [
        "What is LangSmith",
        "Setting Up LangSmith",
        "Understanding a Trace",
        "Real-World Debugging",
        "Best Practices",
    ]
    
    for section in sections:
        assert section in text, f"WP-1.7 must include section: {section}"


def test_wp_1_7_contains_examples():
    """WP-1.7 should reference practical examples."""
    with open("WP-1.7-Introduction-to-Tracing-with-LangSmith.md", "r") as f:
        text = f.read()
    
    # Should mention examples
    assert "example" in text.lower(), "WP-1.7 should include examples"
    assert "trace" in text.lower(), "WP-1.7 should discuss traces"
    assert "latency" in text.lower() or "performance" in text.lower(), \
        "WP-1.7 should discuss performance debugging"


def test_examples_1_7_exists():
    """Example script for WP-1.7 should exist."""
    assert os.path.exists("examples_1_7.py"), \
        "Example script examples_1_7.py not found"


def test_examples_1_7_contains_tracing_examples():
    """Examples should demonstrate LangSmith tracing."""
    with open("examples_1_7.py", "r") as f:
        text = f.read()
    
    # Check for tracing setup
    assert "LANGSMITH" in text, "Examples should mention LANGSMITH configuration"
    assert "setup_tracing" in text, "Examples should have setup function"
    assert "RunnableConfig" in text, "Examples should use RunnableConfig for traces"
    
    # Check for example functions
    example_funcs = [
        "example_1_basic_tracing",
        "example_2_trace_structure",
        "example_3_debugging_with_traces",
        "example_4_custom_metadata",
    ]
    
    for func in example_funcs:
        assert func in text, f"Examples should include: {func}"


def test_wp_1_7_mentions_observability_first():
    """WP-1.7 should emphasize observability-first mindset."""
    with open("WP-1.7-Introduction-to-Tracing-with-LangSmith.md", "r") as f:
        text = f.read()
    
    assert "observability" in text.lower(), \
        "WP-1.7 must emphasize observability-first mindset"
    assert "debug" in text.lower(), \
        "WP-1.7 should discuss debugging with traces"


def test_wp_1_7_adr_section_exists():
    """WP-1.7 should include an ADR section."""
    with open("WP-1.7-Introduction-to-Tracing-with-LangSmith.md", "r") as f:
        text = f.read()
    
    assert "ADR" in text, "WP-1.7 should include an ADR section"
    assert "decision" in text.lower() or "rationale" in text.lower(), \
        "ADR section should discuss decision rationale"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
