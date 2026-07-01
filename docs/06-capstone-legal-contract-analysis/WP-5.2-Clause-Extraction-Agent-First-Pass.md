# WP-5.2: Clause Extraction Agent (First Pass)

**Work Product**: Core LangGraph-based agent for clause extraction with classification and tool-calling loop  
**Status**: Implementation  
**Duration**: 4-5 hours  
**Prerequisites**: [WP-5.1 PDF Ingestion Tool](WP-5.1-PDF-Ingestion-Preprocessing-Tool.md) | [WP-2.6 LangGraph Intro](../04-multi-agent-architectures/WP-2.6-Introduction-to-LangGraph-for-Stateful-Graphs.md) | Understanding of legal clause types

---

## Executive Summary

This work product implements **Tasks 2-3** of the legal contract analysis pipeline:
- **Task 2**: Classify contract type (NDA, SaaS, License, Employment, etc.)
- **Task 3**: Extract all 12 clause types with confidence scores

**Architecture**: LangGraph StateGraph with classification node → extraction nodes (parallelized)

**Key Features:**
- ✅ Multi-class contract classification (9 types supported)
- ✅ 12 clause types extracted with evidence quotes
- ✅ Confidence scoring (0-100) for each clause
- ✅ Page references and block coordinates for evidence
- ✅ Graceful handling of missing clauses
- ✅ Tool-calling loop for iterative refinement
- ✅ No guardrails yet (baseline before safety hardening)

**Performance**: ~3-5 seconds per contract (Tasks 2-3 only)

---

## Section 1: Clause Types & Extraction Strategy

### 12 Supported Clause Types

| Type | Description | Example Trigger |
|------|-------------|-----------------|
| **Termination** | How/when contract ends | "either party may terminate" |
| **Liability** | Limitation of damages | "total liability shall not exceed" |
| **Indemnification** | Party A protects Party B from losses | "indemnify and hold harmless" |
| **IP Ownership** | Who owns intellectual property | "intellectual property owned by" |
| **Confidentiality** | Keeping information secret | "confidential", "non-disclosure" |
| **Payment Terms** | Invoice, pricing, payment schedule | "net 30", "payment due" |
| **Renewal/Auto-Renewal** | How contract continues | "automatically renew", "term shall renew" |
| **Dispute Resolution** | Escalation, arbitration, litigation | "arbitration", "governing law" |
| **Limitation of Liability** | Cap on damages | "in no event shall" |
| **Warranty** | Guarantees/disclaimers | "as-is", "without warranty" |
| **Force Majeure** | Acts beyond control | "force majeure", "act of god" |
| **Amendment/Modification** | How to change contract | "no modification except in writing" |

### 3-Pass Extraction Strategy

**Pass 1: Keyword Matching**
- Fast regex patterns for high-confidence matches
- Detects obvious clauses (100%+ recall, but ~20% false positives)

**Pass 2: LLM Classification**
- Uses GPT-4 to classify ambiguous sections
- Reduces false positives to <5%
- Validates Pass 1 results

**Pass 3: Evidence Extraction**
- For each detected clause, extract:
  - Direct quote from source text
  - Confidence score (0-100)
  - Page number and block position
  - Summary (1-2 sentences)

### Why This is "First Pass" (No Guardrails Yet)

This agent extracts clauses WITHOUT the 10 guardrails from WP-4.4:
- ❌ No confidence calibration (G3)
- ❌ No evidence validation (G7)
- ❌ No cost monitoring (G10)
- ❌ No timeout/loop protection (G6)

This is the **baseline** to measure against safety improvements. WP-5.3+ will add guardrails incrementally.

---

## Section 2: State Machine & LangGraph Architecture

### State Definition

```python
class ExtractionState(TypedDict):
    """
    State managed by LangGraph throughout extraction.
    
    Flows:
      INIT → CLASSIFICATION → EXTRACTION → COMPLETE
    
    At each node, state is updated and persisted (checkpointing).
    """
    
    # Input (from WP-5.1 PDF ingestion)
    contract_id: str
    raw_text: str
    tables: List[Dict[str, Any]]
    
    # Task 2: Classification results
    contract_type: Optional[str]                # "NDA", "SaaS", etc.
    contract_type_confidence: float             # 0-100
    contract_summary: Optional[str]             # 1-2 sentences
    
    # Task 3: Clause extraction results
    extracted_clauses: Dict[str, ClauseResult]  # {clause_type: result}
    extraction_confidence: float                # Average confidence
    
    # Metadata
    total_extraction_time: float
    node_execution_times: Dict[str, float]
    error: Optional[str]
    
    # For tool-calling loop
    iteration_count: int
    max_iterations: int
    refinement_requests: List[str]
```

### Graph Structure

```
                    START
                      │
                      ▼
            ┌─────────────────┐
            │  CLASSIFY NODE  │ (Task 2)
            │                 │
            │ Input: raw_text │
            │ Output: type    │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  EXTRACT NODE   │ (Task 3)
            │                 │
            │ Input: raw_text │
            │ + type          │
            │ Output: clauses │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ AGGREGATE NODE  │
            │                 │
            │ Merge results   │
            │ Compute metrics │
            └────────┬────────┘
                     │
                     ▼
                   END
```

### Nodes

#### Node 1: `classify_contract`
```python
def classify_contract(state: ExtractionState) -> Dict[str, Any]:
    """
    Classify contract type using LLM.
    
    Input: state.raw_text (from PDF ingestion)
    
    Output:
        contract_type: One of {NDA, SaaS, License, Employment, 
                              Supply, Partnership, Lease, Maintenance, Mixed}
        contract_type_confidence: 0-100 confidence score
        contract_summary: 1-2 sentence summary
    
    Implementation:
        1. Prompt GPT-4 with:
           - Full contract text (or first 2000 tokens)
           - List of 9 contract types
           - Few-shot examples (3 examples per type)
        2. Parse structured JSON response
        3. Validate against known types
        4. Return classification + confidence
    
    Latency: ~2 seconds
    Cost: ~0.05 cents per contract
    """
```

#### Node 2: `extract_clauses`
```python
def extract_clauses(state: ExtractionState) -> Dict[str, Any]:
    """
    Extract all 12 clause types from contract text.
    
    Input:
        state.raw_text: Full contract
        state.contract_type: Classification from Node 1
    
    Output:
        extracted_clauses: {
            "termination": ClauseResult(...),
            "liability": ClauseResult(...),
            ...12 total
        }
        extraction_confidence: Average confidence across all clauses
    
    Implementation (3-pass strategy):
        Pass 1: Keyword matching (fast, ~20% false positives)
        Pass 2: LLM validation of ambiguous cases
        Pass 3: Evidence extraction for all detected clauses
    
    Parallelization: 
        - Extract up to 12 clause types in parallel (12 LLM calls)
        - Latency: ~3-4 seconds (not 36+ seconds sequential)
        - Cost: ~0.30 cents per contract
    
    Special handling:
        - Missing clauses: Return with confidence=0
        - Conflicting clauses: Mark all candidates, let downstream task decide
    """
```

#### Node 3: `aggregate_results`
```python
def aggregate_results(state: ExtractionState) -> Dict[str, Any]:
    """
    Merge classification + extraction results.
    
    Compute:
        - Overall extraction_confidence (average of clause confidences)
        - Node execution times (for performance tracking)
        - Error flags (if any clause failed to extract)
    
    Output: Complete ExtractionState ready for Task 4 (anomaly detection)
    """
```

### ClauseResult Data Model

```python
@dataclass
class ClauseResult:
    """
    Result of extracting a single clause type.
    
    Attributes:
        clause_type: "termination", "liability", etc.
        present: True if clause exists in contract
        confidence: 0-100, how certain we are
        evidence_quote: Exact text from contract (max 500 chars)
        page_number: Which page this appears on
        block_position: (start_char, end_char) in raw_text for retrieval
        summary: 1-2 sentence interpretation
        tags: Optional metadata {"severity": "high", "risk": "unlimited_liability"}
    """
```

---

## Section 3: Implementation

### File Structure

```
legal-contract-agent/
├── src/agent/
│   ├── __init__.py
│   ├── state.py                      # ExtractionState, ClauseResult models
│   ├── clause_extractor.py           # Main implementation (~500 lines)
│   │   ├─ ClassifyNode
│   │   ├─ ExtractNode
│   │   ├─ AggregateNode
│   │   └─ build_extraction_graph()  # Graph constructor
│   │
│   └── prompts/
│       ├─ classify_contract.txt     # Few-shot classification prompt
│       └─ extract_clauses.txt       # Few-shot extraction prompt
│
└── tests/
    └── test_clause_extractor.py     # ~100+ unit tests
        ├─ test_classify_nda
        ├─ test_classify_saas
        ├─ test_extract_termination
        ├─ test_extract_all_types
        ├─ test_parallelization
        ├─ test_missing_clauses
        ├─ test_confidence_scoring
        └─ test_end_to_end_extraction
```

### Core API

```python
def extract_clauses(
    contract_id: str,
    raw_text: str,
    contract_type: Optional[str] = None,
    debug: bool = False
) -> ExtractionResult:
    """
    Extract clauses from contract text.
    
    Args:
        contract_id: UUID from WP-5.1 ingestion
        raw_text: Full contract text (layout-preserved from Docling)
        contract_type: Pre-classified type (skips Node 1 if provided)
        debug: If True, return node execution times & prompts for analysis
    
    Returns:
        ExtractionResult with extracted_clauses, confidence, execution_times
    
    Orchestration:
        - Uses LangGraph StateGraph
        - Checkpointing: State saved after each node (resume on failure)
        - Streaming: Can yield intermediate results in real-time
    
    Example:
        >>> result = extract_clauses(
        ...     contract_id="contract_20240701_abc123",
        ...     raw_text="SOFTWARE LICENSE AGREEMENT..."
        ... )
        >>> for clause_type, clause_result in result.extracted_clauses.items():
        ...     print(f"{clause_type}: {clause_result.confidence}%")
        ...     print(f"Evidence: {clause_result.evidence_quote[:100]}...")
    """
```

### Sample Prompts

#### Classify Contract Prompt
```
You are a legal contract classifier. Given a contract, identify its primary type.

Types:
1. NDA (Non-Disclosure Agreement)
2. SaaS (Software-as-a-Service)
3. License (Software or Content License)
4. Employment (Employment Agreement)
5. Supply (Supply Agreement)
6. Partnership (Partnership Agreement)
7. Lease (Real Estate or Equipment Lease)
8. Maintenance (Software/Hardware Maintenance)
9. Mixed (Multiple types; specify primary)

Examples:
[Few-shot examples]

Contract Text:
---
{CONTRACT_TEXT}
---

Respond in JSON:
{
    "contract_type": "NDA",
    "confidence": 95,
    "reasoning": "...",
    "summary": "..."
}
```

#### Extract Clauses Prompt
```
Extract the following clause from the contract. Return the exact quote, 
location, and confidence score.

Clause Type: {CLAUSE_TYPE}
Definition: {DEFINITION}

Contract Type: {CONTRACT_TYPE}
Contract Text:
---
{CONTRACT_TEXT}
---

Respond in JSON:
{
    "found": true,
    "quote": "...",
    "page": 3,
    "char_position": [1234, 1567],
    "confidence": 92,
    "summary": "...",
    "tags": {}
}
```

---

## Section 4: Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Orchestration | LangGraph StateGraph | State machine is natural fit; checkpointing saves cost |
| Parallelization | 12 clause extraction tasks in parallel | Reduces 36s sequential to 3-4s |
| Confidence scoring | LLM-provided (not calibrated) | Baseline for guardrail G3 improvement |
| Evidence extraction | Exact text quotes with char positions | Enables guardrail G7 (Evidence Validation) |
| Contract types | 9 types (expandable) | Covers 95%+ of enterprise contracts |
| Clause types | 12 types (expandable) | Covers all major risk vectors |

---

## Section 5: Testing Strategy

### Unit Tests (50+ tests)

```python
def test_classify_nda():
    """Classify simple NDA correctly."""
    text = "This Non-Disclosure Agreement..."
    result = classify_contract("test_1", text)
    assert result.contract_type == "NDA"
    assert result.contract_type_confidence >= 90

def test_extract_termination_clause():
    """Extract termination clause with evidence."""
    result = extract_clauses_single(
        text="...",
        clause_type="termination"
    )
    assert result["found"] == True
    assert len(result["quote"]) > 20
    assert result["confidence"] >= 70

def test_parallelization():
    """All 12 clauses extracted in <5 seconds."""
    start = time.time()
    result = extract_clauses("test_2", LONG_CONTRACT_TEXT)
    elapsed = time.time() - start
    assert elapsed < 5.0
    assert len(result.extracted_clauses) == 12

def test_missing_clause():
    """Missing clauses return with confidence=0."""
    result = extract_clauses("test_3", SIMPLE_AGREEMENT_TEXT)
    for clause in result.extracted_clauses.values():
        if not clause.present:
            assert clause.confidence == 0
```

### Integration Tests

- E2E: Ingest PDF (WP-5.1) → Extract clauses (WP-5.2)
- Against ground truth dataset (10 annotated contracts from WP-4.8)
- Measure recall, precision, F1 for each clause type

### Adversarial Tests

- Conflicting clauses (different termination conditions in different sections)
- Misleading language ("This clause does NOT apply..." → confuse LLM)
- Minimal contracts (1 page, only core clauses)
- Complex contracts (50+ pages, many subsections)

---

## Section 6: Baseline Metrics (No Guardrails)

These are measured against ground truth dataset (WP-4.8, 10 annotated contracts):

| Metric | Target | Notes |
|--------|--------|-------|
| **Classification Accuracy** | 85%+ | Across 9 contract types |
| **Clause Extraction Recall** | 75%+ | Find clause if present |
| **Clause Extraction Precision** | 80%+ | Avoid false positives |
| **Confidence Calibration** | ±10% | If we say 90%, true rate ~80-100% |
| **Latency** | <5 seconds | Tasks 2-3 combined |
| **Cost** | <$0.50/contract | At GPT-4 pricing (~$0.03/1K tokens) |

**These will improve with guardrails:**
- G3 (Confidence Calibration) → Recalibrate scores vs ground truth
- G7 (Evidence Validation) → Verify quotes exactly match source
- G8 (Validation Checkpoints) → Re-run extraction if confidence < 70%

---

## Section 7: Error Handling

### Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| LLM timeout | No response after 10s | Return "extraction_failed" |
| Malformed JSON response | JSON parse error | Fallback to keyword extraction |
| Too short text (<100 chars) | Length check | Return all clauses with confidence=0 |
| Rate limit hit | 429 HTTP error | Exponential backoff (1s, 2s, 4s, 8s) |
| Invalid clause type | Not in 12 supported | Skip gracefully |

### Graceful Degradation

- If LLM extraction fails for clause type X: Fall back to keyword-only
- If classification fails: Default to "Mixed" type
- If error occurs: Still return partial results + error message

---

## Section 8: Observability & Debugging

### Instrumentation

```python
# Each node logs:
# - Start/end time
# - Input size (tokens)
# - Output validity
# - LLM model used
# - Token usage (input + output)

# Example output:
logger.info({
    "event": "node_executed",
    "node": "extract_clauses",
    "contract_id": "...",
    "duration_seconds": 3.2,
    "input_tokens": 5000,
    "output_tokens": 1200,
    "error": None,
})
```

### Debug Mode

```python
# Enable detailed tracing:
result = extract_clauses(
    contract_id="...",
    raw_text="...",
    debug=True  # Returns node execution times + prompts
)

# Output includes:
{
    "extracted_clauses": {...},
    "debug": {
        "classify_contract_time": 2.1,
        "classify_contract_prompt": "...",
        "classify_contract_response": "...",
        "extract_clauses_time": 3.4,
        ...
    }
}
```

---

## Section 9: Next Steps

### This WP (5.2): ✅ Baseline clause extraction

### WP-5.3: Anomaly Detection Agent
- Detect 9 risk types (unlimited liability, auto-renewal, etc.)
- Uses extracted clauses as input
- Confidence-weighted risk scoring

### WP-5.4: Safety Guardrails Hardening
- Implement G3, G7, G8 for extraction task
- Recalibrate confidence scores
- Evidence validation loop

### WP-5.5: HITL Integration
- Send high-risk contracts to human queue
- Reviewer can approve/reject/modify
- Feedback loop to improve model

---

## References

- **WP-5.1**: PDF Ingestion & Preprocessing Tool (input data)
- **WP-2.6**: LangGraph Introduction (state machine framework)
- **WP-4.2**: Task Decomposition (7-task pipeline overview)
- **WP-4.8**: Ground Truth Dataset (10 annotated contracts for testing)
- **ADR-2.2**: Orchestration Pattern (why LangGraph for this task)

