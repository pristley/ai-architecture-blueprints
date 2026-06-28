import pathlib


def test_wp_1_6_exists():
    path = pathlib.Path(__file__).resolve().parent.parent / "docs" / "02-production-patterns" / "WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md"
    assert path.exists(), "WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md must exist"


def test_wp_1_6_contains_model_comparison():
    path = pathlib.Path(__file__).resolve().parent.parent / "docs" / "02-production-patterns" / "WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md"
    text = path.read_text()

    # Original models
    assert "GPT-4o" in text or "gpt-4o" in text, "WP-1.6 must include GPT-4o"
    assert "Claude 3.5 Sonnet" in text, "WP-1.6 must include Claude 3.5 Sonnet"
    assert "Gemini 1.5 Pro" in text, "WP-1.6 must include Gemini 1.5 Pro"
    assert "Mixtral" in text, "WP-1.6 must include Mixtral"
    
    # New models (2026 updates)
    assert "Gemini 3.5" in text, "WP-1.6 must include Gemini 3.5"
    assert "ChatGPT 5.5" in text or "GPT-5.5" in text, "WP-1.6 must include OpenAI ChatGPT 5.5"
    assert "Claude Opus 4.8" in text, "WP-1.6 must include Claude Opus 4.8"
    
    # Required decision axes
    assert "cost" in text.lower(), "WP-1.6 must discuss cost"
    assert "TTFT" in text, "WP-1.6 must include TTFT"
    assert "TPS" in text, "WP-1.6 must include TPS"
    assert "context" in text.lower(), "WP-1.6 must discuss context window"
    assert "tool-calling" in text.lower() or "tool calling" in text.lower(), "WP-1.6 must discuss tool-calling reliability"
    assert "multimodal" in text.lower(), "WP-1.6 must discuss multimodal capability"
    assert "ADR" in text, "WP-1.6 must include an ADR section"
    
    # Decision outcome
    assert "Claude Opus 4.8" in text, "WP-1.6 ADR must recommend a model choice"
