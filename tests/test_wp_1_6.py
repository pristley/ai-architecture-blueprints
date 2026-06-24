import pathlib


def test_wp_1_6_exists():
    path = pathlib.Path(__file__).resolve().parent.parent / "WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md"
    assert path.exists(), "WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md must exist"


def test_wp_1_6_contains_required_decision_axes_and_models():
    path = pathlib.Path(__file__).resolve().parent.parent / "WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md"
    text = path.read_text()

    assert "GPT-4o" in text or "gpt-4o" in text, "WP-1.6 must include GPT-4o"
    assert "Claude 3.5 Sonnet" in text, "WP-1.6 must include Claude 3.5 Sonnet"
    assert "Gemini 1.5 Pro" in text, "WP-1.6 must include Gemini 1.5 Pro"
    assert "Mixtral" in text, "WP-1.6 must include Mixtral"
    assert "cost" in text.lower(), "WP-1.6 must discuss cost"
    assert "TTFT" in text, "WP-1.6 must include TTFT"
    assert "TPS" in text, "WP-1.6 must include TPS"
    assert "context" in text.lower(), "WP-1.6 must discuss context window"
    assert "tool-calling" in text.lower() or "tool calling" in text.lower(), "WP-1.6 must discuss tool-calling reliability"
    assert "multimodal" in text.lower(), "WP-1.6 must discuss multimodal capability"
    assert "ADR" in text, "WP-1.6 must include an ADR section"
