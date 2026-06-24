import pathlib


def test_wp_1_5_exists():
    path = pathlib.Path(__file__).resolve().parent.parent / "WP-1.5-Output-Parsing-for-System-Integration.md"
    assert path.exists(), "WP-1.5-Output-Parsing-for-System-Integration.md must exist"


def test_wp_1_5_contains_schema_and_parser_strategy():
    path = pathlib.Path(__file__).resolve().parent.parent / "WP-1.5-Output-Parsing-for-System-Integration.md"
    text = path.read_text()

    assert "ExtractedInvoice" in text, "WP-1.5 must define the ExtractedInvoice schema"
    assert "vendor_name" in text or "vendor" in text, "WP-1.5 must define a vendor field"
    assert "invoice_date" in text, "WP-1.5 must define an invoice date field"
    assert "line_items" in text, "WP-1.5 must define line items"
    assert "OutputFixingParser" in text, "WP-1.5 must explain OutputFixingParser"
    assert "RetryWithErrorOutputParser" in text, "WP-1.5 must explain RetryWithErrorOutputParser"
    assert "structured output" in text.lower(), "WP-1.5 must discuss structured output"
    assert "GPT-4o" in text or "gpt-4o" in text, "WP-1.5 must mention GPT-4o structured output"
