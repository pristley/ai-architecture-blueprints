import pathlib


def test_adr_1_2_exists():
    path = pathlib.Path(__file__).resolve().parent.parent / "ADR-1.2-Hello-World-Three-Ways.md"
    assert path.exists(), "ADR-1.2-Hello-World-Three-Ways.md must exist"


def test_adr_1_2_contains_comparison_dimensions():
    path = pathlib.Path(__file__).resolve().parent.parent / "ADR-1.2-Hello-World-Three-Ways.md"
    text = path.read_text()
    assert "Traceability" in text, "ADR must discuss traceability"
    assert "Verbosity" in text, "ADR must discuss verbosity"
    assert "Flexibility" in text, "ADR must discuss flexibility"
    assert "direct LLM call" in text or "Basic LLM call" in text, "ADR must mention direct LLM call"
    assert "SimpleSequentialChain" in text, "ADR must mention SimpleSequentialChain"
    assert "RunnableSequence" in text, "ADR must mention RunnableSequence"
