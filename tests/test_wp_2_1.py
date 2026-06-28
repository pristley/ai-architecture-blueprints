"""
Tests for Work Product 2.1: Short-Term vs. Long-Term Memory

These tests verify that:
1. The WP-2.1 document exists and contains key concepts
2. The example code is syntactically correct and importable
3. Key components (DualMemoryChatbot, memory systems) are implemented
4. Memory systems work correctly with integration tests
5. Edge cases are handled properly
"""

import pathlib
import pytest


def test_wp_2_1_document_exists():
    """WP-2.1 document file must exist."""
    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs"
        / "03-memory-state-agents"
        / "WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md"
    )
    assert path.exists(), "WP-2.1 document must exist"


def test_wp_2_1_contains_dual_memory_concept():
    """WP-2.1 must explain the dual-memory pattern."""
    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs"
        / "03-memory-state-agents"
        / "WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md"
    )
    text = path.read_text()

    # Core concepts
    assert "Short-Term Memory" in text, "WP-2.1 must mention short-term memory"
    assert "Long-Term Memory" in text, "WP-2.1 must mention long-term memory"
    assert (
        "ConversationBufferWindowMemory" in text
    ), "WP-2.1 must discuss ConversationBufferWindowMemory"
    assert (
        "ConversationSummaryMemory" in text
    ), "WP-2.1 must discuss ConversationSummaryMemory"


def test_wp_2_1_contains_architecture_diagrams():
    """WP-2.1 must include architecture diagrams."""
    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs"
        / "03-memory-state-agents"
        / "WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md"
    )
    text = path.read_text()

    # Mermaid diagrams
    assert "mermaid" in text, "WP-2.1 must include Mermaid diagrams"
    assert "graph" in text or "flowchart" in text, "WP-2.1 must include visual diagrams"


def test_wp_2_1_contains_separation_of_concerns():
    """WP-2.1 must emphasize separation of concerns."""
    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs"
        / "03-memory-state-agents"
        / "WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md"
    )
    text = path.read_text()

    assert (
        "separation" in text.lower() or "separate" in text.lower()
    ), "WP-2.1 must discuss separation of concerns"
    assert (
        "observable" in text.lower() or "inspect" in text.lower()
    ), "WP-2.1 must discuss observability"


def test_wp_2_1_contains_vector_store_reference():
    """WP-2.1 must mention vector stores for semantic search."""
    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs"
        / "03-memory-state-agents"
        / "WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md"
    )
    text = path.read_text()

    assert "vector" in text.lower(), "WP-2.1 must discuss vector stores"
    assert (
        "semantic" in text.lower() or "similarity" in text.lower()
    ), "WP-2.1 must discuss semantic search"


def test_wp_2_1_contains_token_counting():
    """WP-2.1 must discuss token count bounding."""
    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs"
        / "03-memory-state-agents"
        / "WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md"
    )
    text = path.read_text()

    assert "token" in text.lower(), "WP-2.1 must discuss token counts"
    assert "bound" in text.lower() or "limit" in text.lower(), (
        "WP-2.1 must discuss bounding/limiting resource usage"
    )


def test_example_2_1_file_exists():
    """examples_2_1.py must exist."""
    path = (
        pathlib.Path(__file__).resolve().parent.parent / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    assert path.exists(), "examples_2_1.py must exist"


def test_example_2_1_is_importable():
    """examples_2_1.py must be syntactically correct and importable."""
    import sys
    import importlib.util

    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    spec = importlib.util.spec_from_file_location("examples_2_1", path)
    module = importlib.util.module_from_spec(spec)

    # Should not raise an exception
    spec.loader.exec_module(module)


def test_example_2_1_has_dual_memory_chatbot():
    """examples_2_1.py must define DualMemoryChatbot class."""
    import sys
    import importlib.util

    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    spec = importlib.util.spec_from_file_location("examples_2_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(
        module, "DualMemoryChatbot"
    ), "examples_2_1.py must define DualMemoryChatbot class"

    # Check key methods exist
    DualMemoryChatbot = getattr(module, "DualMemoryChatbot")
    assert hasattr(
        DualMemoryChatbot, "__init__"
    ), "DualMemoryChatbot must have __init__"
    assert hasattr(
        DualMemoryChatbot, "chat"
    ), "DualMemoryChatbot must have chat method"
    assert hasattr(
        DualMemoryChatbot, "get_stats"
    ), "DualMemoryChatbot must have get_stats method"


def test_example_2_1_has_examples():
    """examples_2_1.py must define example functions."""
    import sys
    import importlib.util

    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    spec = importlib.util.spec_from_file_location("examples_2_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(
        module, "example_1_dual_memory_conversation"
    ), "examples_2_1.py must define example_1_dual_memory_conversation"
    assert hasattr(
        module, "example_2_memory_separation"
    ), "examples_2_1.py must define example_2_memory_separation"
    assert hasattr(
        module, "example_3_observability"
    ), "examples_2_1.py must define example_3_observability"


def test_dual_memory_chatbot_initialization():
    """DualMemoryChatbot must initialize both memory systems."""
    import sys
    import importlib.util

    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    spec = importlib.util.spec_from_file_location("examples_2_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    DualMemoryChatbot = getattr(module, "DualMemoryChatbot")

    # Test initialization (may fail if OpenAI API key not set, which is okay)
    try:
        bot = DualMemoryChatbot(model="gpt-4o", buffer_k=5)
        
        # Check that both memories are initialized
        assert hasattr(
            bot, "short_term_memory"
        ), "Bot must have short_term_memory"
        assert hasattr(
            bot, "long_term_memory"
        ), "Bot must have long_term_memory"
        
        # Check that stats can be retrieved
        stats = bot.get_stats()
        assert "turn_count" in stats, "Stats must include turn_count"
        assert "short_term_message_count" in stats, "Stats must include short_term_message_count"
        
    except Exception as e:
        # Skip if OpenAI API is not available
        if "openai" in str(e).lower() or "api" in str(e).lower():
            pytest.skip("OpenAI API not available")
        else:
            raise


def test_wp_2_1_memory_architecture_described():
    """WP-2.1 must describe the complete memory architecture."""
    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs"
        / "03-memory-state-agents"
        / "WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md"
    )
    text = path.read_text()

    # Should describe the purpose of each memory
    assert "immediate context" in text.lower(), "Must describe short-term purpose"
    assert "extracted" in text.lower() or "semantic" in text.lower(), (
        "Must describe long-term extraction"
    )

    # Should explain design decisions
    assert "window" in text.lower(), "Must mention buffer window concept"
    assert "summarize" in text.lower(), "Must mention summarization"


def test_wp_2_1_includes_trade_offs():
    """WP-2.1 must discuss trade-offs and design decisions."""
    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs"
        / "03-memory-state-agents"
        / "WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md"
    )
    text = path.read_text()

    assert "trade" in text.lower() or "cost" in text.lower(), (
        "WP-2.1 must discuss trade-offs"
    )
    assert "decision" in text.lower(), "WP-2.1 must provide decision guidance"


def test_wp_2_1_includes_production_patterns():
    """WP-2.1 must discuss production considerations."""
    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs"
        / "03-memory-state-agents"
        / "WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md"
    )
    text = path.read_text()

    # Should discuss production concerns
    assert (
        "production" in text.lower() or "monitor" in text.lower()
        or "observ" in text.lower()
    ), "WP-2.1 must address production concerns"


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS - Test DualMemoryChatbot end-to-end functionality
# ═══════════════════════════════════════════════════════════════════════════════


def test_dual_memory_chatbot_short_term_buffer_bounded():
    """Short-term memory must maintain a bounded buffer size."""
    import importlib.util

    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    spec = importlib.util.spec_from_file_location("examples_2_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    DualMemoryChatbot = getattr(module, "DualMemoryChatbot")
    bot = DualMemoryChatbot(model="gpt-4o", buffer_k=3)

    # Add more messages than buffer size
    for i in range(10):
        bot.short_term_memory.save_context(
            inputs={"input": f"Message {i}"},
            outputs={"output": f"Response {i}"}
        )

    # Check that buffer is bounded
    recent = bot.short_term_memory.load_memory_variables({})
    messages = recent.get("recent_conversation", [])
    
    # With k=3, we should have at most 6 messages (3 user + 3 assistant)
    assert len(messages) <= 6, "Short-term buffer must respect k parameter"


def test_dual_memory_chatbot_long_term_accumulates():
    """Long-term memory must accumulate facts over time."""
    import importlib.util

    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    spec = importlib.util.spec_from_file_location("examples_2_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    DualMemoryChatbot = getattr(module, "DualMemoryChatbot")
    bot = DualMemoryChatbot(model="gpt-4o", buffer_k=5)

    # Add messages with different facts
    exchanges = [
        ("I am from Toronto", "Interesting city"),
        ("I work as a software engineer", "Great profession"),
        ("I love hiking", "That's a great hobby"),
    ]

    for user_msg, assistant_msg in exchanges:
        bot.long_term_memory.save_context(
            inputs={"input": user_msg},
            outputs={"output": assistant_msg}
        )

    # Check that profile accumulated facts
    profile = bot.long_term_memory.load_memory_variables({})
    profile_text = profile.get("user_profile", "")

    assert "Toronto" in profile_text, "Profile should contain location"
    assert "engineer" in profile_text.lower(), "Profile should contain profession"
    assert "hiking" in profile_text.lower(), "Profile should contain interests"


def test_dual_memory_chatbot_memory_separation():
    """Short-term and long-term memories must remain separate."""
    import importlib.util

    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    spec = importlib.util.spec_from_file_location("examples_2_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    DualMemoryChatbot = getattr(module, "DualMemoryChatbot")
    bot = DualMemoryChatbot(model="gpt-4o", buffer_k=5)

    bot.short_term_memory.save_context(
        inputs={"input": "User message"},
        outputs={"output": "Assistant response"}
    )

    bot.long_term_memory.save_context(
        inputs={"input": "User message"},
        outputs={"output": "Assistant response"}
    )

    # Get both memories
    short_term = bot.short_term_memory.load_memory_variables({})
    long_term = bot.long_term_memory.load_memory_variables({})

    # They should have different keys and structures
    assert "recent_conversation" in short_term
    assert "user_profile" in long_term
    assert short_term != long_term


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASE TESTS - Test boundary conditions and unusual inputs
# ═══════════════════════════════════════════════════════════════════════════════


def test_short_term_memory_empty_buffer():
    """Short-term memory should handle empty state gracefully."""
    import importlib.util

    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    spec = importlib.util.spec_from_file_location("examples_2_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    ConversationBufferWindowMemory = getattr(module, "ConversationBufferWindowMemory")
    memory = ConversationBufferWindowMemory(k=5)

    # Should handle empty buffer
    result = memory.load_memory_variables({})
    messages = result.get("recent_conversation", [])
    assert messages == [], "Empty buffer should return empty list"


def test_short_term_memory_clear():
    """Short-term memory should support clearing."""
    import importlib.util

    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    spec = importlib.util.spec_from_file_location("examples_2_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    ConversationBufferWindowMemory = getattr(module, "ConversationBufferWindowMemory")
    memory = ConversationBufferWindowMemory(k=5)

    # Add messages
    memory.save_context(
        inputs={"input": "Test"}, 
        outputs={"output": "Response"}
    )

    # Clear
    memory.clear()

    # Should be empty
    result = memory.load_memory_variables({})
    messages = result.get("recent_conversation", [])
    assert len(messages) == 0, "Memory should be empty after clear()"


def test_long_term_memory_empty_profile():
    """Long-term memory should handle empty state gracefully."""
    import importlib.util

    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    spec = importlib.util.spec_from_file_location("examples_2_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    ConversationSummaryMemory = getattr(module, "ConversationSummaryMemory")
    memory = ConversationSummaryMemory()

    # Should handle empty profile
    result = memory.load_memory_variables({})
    profile = result.get("user_profile", "")
    assert "No conversations" in profile or profile == "", "Should indicate no profile yet"


def test_dual_memory_chatbot_get_stats():
    """DualMemoryChatbot should provide statistics."""
    import importlib.util

    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    spec = importlib.util.spec_from_file_location("examples_2_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    DualMemoryChatbot = getattr(module, "DualMemoryChatbot")
    bot = DualMemoryChatbot(model="gpt-4o", buffer_k=5)

    stats = bot.get_stats()

    # Check that all expected stats are present
    assert "turn_count" in stats
    assert "elapsed_time" in stats
    assert "short_term_message_count" in stats
    assert "long_term_profile_length" in stats


def test_dual_memory_chatbot_multiple_exchanges():
    """DualMemoryChatbot should handle multiple exchanges correctly."""
    import importlib.util

    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "docs" / "03-memory-state-agents" / "examples_2_1.py"
    )
    spec = importlib.util.spec_from_file_location("examples_2_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    DualMemoryChatbot = getattr(module, "DualMemoryChatbot")
    bot = DualMemoryChatbot(model="gpt-4o", buffer_k=5)

    # Add multiple exchanges
    for i in range(5):
        bot.short_term_memory.save_context(
            inputs={"input": f"User msg {i}"},
            outputs={"output": f"Assistant response {i}"}
        )
        bot.long_term_memory.save_context(
            inputs={"input": f"User msg {i}"},
            outputs={"output": f"Assistant response {i}"}
        )

    # Both memories should have content
    short_term = bot.short_term_memory.load_memory_variables({})
    long_term = bot.long_term_memory.load_memory_variables({})

    assert len(short_term.get("recent_conversation", [])) > 0
    assert len(long_term.get("user_profile", "")) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
