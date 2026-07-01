# WP-4.2: Task Decomposition & Execution Model — Legal Contract Analysis

**Work Product Type**: Architecture & Design Document  
**Phase**: 4 — Capstone: End-to-End Agentic System  
**Date**: 2026-04-01  
**Status**: ✅ Accepted  

---

## Executive Summary

This document decomposes the Legal Contract Clause Analysis capstone into **7 granular subtasks**, identifies **3 dependency chains**, and specifies **which steps are parallelizable**. The result is a **LangGraph orchestration graph** that demonstrates:
- Sequential dependencies (PDF load → classify type)
- Parallel processing (extract clauses in parallel)
- Conditional branching (risk level → escalate to human review)
- Checkpointing (save state between steps for human intervention)

**Diagram**: A dependency graph showing all tasks, parallelization points, and human handoff.

---

## The 7 Subtasks

### Task 1: Document Ingestion & Text Extraction (Sequential)

**Purpose**: Convert raw PDF/text contract into clean, parseable text.

**Inputs**:
- PDF file or raw text document
- Contract metadata (filename, source URL, received date)

**Outputs**:
- `IngestionResult`:
  - `raw_text`: Full contract text
  - `num_pages`: Detected page count
  - `confidence`: "high" (text) or "low" (OCR'd PDF)
  - `warnings`: ["text extraction incomplete", "OCR confidence < 80%"]

**Constraints**:
- **No parallelization**: Must complete before any downstream task
- **Dependency**: Blocks all subsequent tasks (critical path start)
- **Fallback**: If PDF OCR confidence < 80%, escalate to human with warning

**Implementation Notes**:
- Use PyPDF2 or pdfplumber for PDF extraction
- Run basic cleanup (remove headers/footers, normalize whitespace)
- Detect page boundaries (important for liability clause extraction)

**Error Handling**:
- Corrupted PDF → Return error, skip contract
- Scanned-only PDF (no OCR) → Flag for manual upload
- Encrypted PDF → Request password or skip

**Estimated Complexity**: ⭐⭐ (simple; proven libraries)

---

### Task 2: Contract Type Classification (Sequential, Downstream of 1)

**Purpose**: Predict the contract type (NDA, SaaS, License, etc.) to guide downstream extraction logic.

**Inputs**:
- `raw_text` from Task 1
- Few-shot examples (3–5 sample contracts per type from ground truth)

**Outputs**:
- `ClassificationResult`:
  - `contract_type`: One of {NDA, SaaS, License, Employment, Supply, Lease, Partnership, Maintenance, Purchase, Other}
  - `type_confidence`: 0.0–1.0 (LLM's self-reported confidence)
  - `reasoning`: Brief explanation (e.g., "Multiple SaaS-specific clauses detected (uptime SLA, subscription renewal, customer data)")
  - `alternative_types`: List of runner-up types with scores

**Constraints**:
- **No parallelization**: Depends on Task 1; needed before Task 3 (adaptive clause extraction)
- **Must complete before**: Clause extraction (Task 3) may use type to focus extraction
- **Failure mode**: If confidence < 0.5, default to "Other" and proceed with generic extraction

**Implementation Notes**:
- Use GPT-4 with structured output (Pydantic `ContractType` enum)
- Few-shot prompt: "Here are 3 NDAs. Here are 3 SaaS agreements. Classify this one."
- Evaluate against ground truth (50 contracts): target ≥ 90% accuracy

**Error Handling**:
- Ambiguous contract (e.g., "NDA + employment clause") → Report top 2 types; flag for human review
- Out-of-distribution contract → Classification confidence < 0.3; escalate

**Estimated Complexity**: ⭐⭐⭐ (medium; requires good prompt engineering)

---

### Task 3: Clause Extraction (Parallelizable, Downstream of 2)

**Purpose**: Identify and extract key contractual clauses (termination, liability, indemnification, etc.).

**Inputs**:
- `raw_text` from Task 1
- `contract_type` from Task 2 (used for adaptive extraction focus)
- Clause extraction schema (Pydantic `ContractClause` definitions)
- Per-type clause templates (e.g., "SaaS contracts always have payment terms; focus there")

**Outputs**:
- `ClauseExtractionResult`:
  - `clauses`: List of `ContractClause` objects:
    - `clause_type`: Detected clause category (termination, liability, etc.)
    - `text`: Full clause text
    - `start_page`, `end_page`: Location in document
    - `confidence`: 0.0–1.0
  - `missing_clauses`: List of clause types NOT found (e.g., "No indemnity clause detected")
  - `warnings`: ["Termination clause spans 3 pages"; "Liability language ambiguous"]

**Constraints**:
- **Parallelizable internally**: Can extract different clause types in parallel (e.g., "Find all termination clauses" + "Find all liability clauses" in parallel)
- **Sequential dependency**: Must wait for Task 2 (classification) to guide extraction strategy
- **Must complete before**: Task 4 (anomaly detection) + Task 5 (summarization)

**Implementation Notes**:
- Use LLM-powered clause extractor with type-specific prompts:
  - NDA → Focus on confidentiality, term, return-of-info clauses
  - SaaS → Focus on payment, uptime, termination, liability
  - License → Focus on scope, assignment, warranty, IP ownership
- Return full text (not just summaries) for later anomaly analysis
- Include page numbers for document navigation

**Evaluation**:
- Compare extracted clauses vs. ground truth annotations (50 contracts)
- Target: ≥ 85% recall (find most important clauses), ≥ 80% precision (minimal false positives)

**Error Handling**:
- If no clauses found (blank contract?), flag for human review
- If clause text too long (>2000 chars), truncate with warning and continue

**Estimated Complexity**: ⭐⭐⭐⭐ (high; LLM extraction + validation)

---

### Task 4: Anomaly Detection & Risk Flagging (Parallelizable, Downstream of 3)

**Purpose**: Identify risky language patterns in extracted clauses (unlimited liability, one-sided termination, automatic renewal traps, etc.).

**Inputs**:
- Extracted `clauses` from Task 3
- Anomaly detection rules/patterns (Pydantic `AnomalyType` enum)
- Risk scoring framework (which anomalies → HIGH risk vs. MEDIUM risk)

**Outputs**:
- `AnomalyDetectionResult`:
  - `anomalies`: List of `AnomalyFlag` objects:
    - `anomaly_type`: Type of risky pattern (unlimited_liability, one_sided, etc.)
    - `risk_level`: Severity (LOW, MEDIUM, HIGH, CRITICAL)
    - `description`: Human-readable explanation
    - `evidence`: Exact quote from clause
    - `recommendation`: Suggested action ("Negotiate cap", "Add mutual termination", etc.)
  - `risk_summary`: Aggregated risk score (0–100; 0=safe, 100=extreme risk)
  - `requires_escalation`: Boolean; if any CRITICAL flags, true

**Constraints**:
- **Parallelizable**: Can run independent anomaly detectors in parallel:
  - Detector 1: Check for unlimited liability
  - Detector 2: Check for one-sided termination
  - Detector 3: Check for auto-renewal traps
  - Detector 4: Check for broad indemnity
  - (Each runs independently on same clause set)
- **Sequential dependency**: Must wait for Task 3 (need extracted clauses)
- **Must complete before**: Task 5 (summarization needs to include flagged risks)

**Implementation Notes**:
- Hybrid approach:
  - **Rule-based**: Keyword matching (e.g., "unlimited liability" OR "without limitation" → Flag unlimited_liability)
  - **LLM-based**: Semantic analysis (e.g., "Does this termination right belong only to one party?" → LLM evaluates)
- Severity scoring:
  - CRITICAL: Unlimited liability, waiver of legal rights, material unilateral termination
  - HIGH: One-sided clauses, undefined scope, auto-renewal without clear opt-out
  - MEDIUM: Escalating penalties, unusual term lengths, broad indemnity
  - LOW: Standard language, minor asymmetries

**Evaluation**:
- Compare flagged anomalies vs. ground truth (50 contracts)
- Target: ≥ 85% recall (catch risky clauses), ≥ 75% precision (minimize false alarms)

**Error Handling**:
- If anomaly detection fails, log warning and continue (don't block summarization)
- Confidence scores: If < 0.6, mark as "uncertain" and include in summary for human review

**Estimated Complexity**: ⭐⭐⭐⭐ (high; requires hybrid rule/LLM approach)

---

### Task 5: Contract Summary Generation (Sequential, Downstream of 3 & 4)

**Purpose**: Generate executive summary highlighting key obligations, rights, and risks for legal review.

**Inputs**:
- Extracted `clauses` from Task 3
- Flagged `anomalies` from Task 4
- `contract_type` from Task 2 (for type-specific summarization)

**Outputs**:
- `ContractAnalysisSummary`:
  - `summary`: 2–3 sentence plain-English summary (e.g., "SaaS agreement for platform access; 3-year term with auto-renewal; $50K annual fee. Key risks: no liability cap, auto-renewal with ambiguous termination notice.")
  - `key_obligations`: List of main duties per party (e.g., ["Provider: 99.5% uptime SLA", "Customer: Annual payment"])
  - `key_rights`: List of main benefits per party (e.g., ["Customer: Can terminate with 90 days' notice"])
  - `key_risks`: Top 3–5 risks (e.g., ["Unlimited liability", "Auto-renewal trap"])

**Constraints**:
- **Sequential**: Depends on Tasks 3 & 4 (need clauses + anomalies)
- **Not parallelizable**: Single task; must wait for both inputs
- **Must complete before**: Task 6 (review triage decision)

**Implementation Notes**:
- Use LLM (GPT-4) with structured output (Pydantic `ContractAnalysisSummary`)
- Prompt template:
  ```
  Contract Type: {type}
  
  Extracted Clauses:
  - Termination: {termination_clause.text[:500]}
  - Liability: {liability_clause.text[:500]}
  - [etc.]
  
  Detected Anomalies:
  - Unlimited Liability (CRITICAL)
  - One-Sided Termination (HIGH)
  - [etc.]
  
  Summarize this contract in 2–3 sentences for a busy CFO/Legal Director.
  Highlight key obligations, rights, and top 3–5 risks.
  ```
- Keep summaries jargon-free and actionable

**Evaluation**:
- Human review: Does summary capture key points?
- ROUGE scores: How similar to human-written summaries?

**Error Handling**:
- If summarization fails, fall back to bullet-point format from clauses/anomalies

**Estimated Complexity**: ⭐⭐⭐ (medium; LLM text generation)

---

### Task 6: Review Triage & Escalation Decision (Sequential, Downstream of 4 & 5)

**Purpose**: Determine if this contract requires human legal review or can be auto-approved.

**Inputs**:
- Anomalies and risk scores from Task 4
- Summary from Task 5
- Company policy thresholds (e.g., "Any CRITICAL anomaly → escalate", "HIGH risk contracts go to senior legal")

**Outputs**:
- `TriageDecision`:
  - `requires_legal_review`: Boolean; if true, contract is escalated
  - `review_priority`: Enum {"low", "normal", "high", "urgent"}
  - `review_reason`: Explanation (e.g., "CRITICAL: Unlimited liability")
  - `suggested_reviewer`: Role ("paralegal", "junior attorney", "senior attorney", "general counsel")
  - `estimated_review_time`: Estimate in minutes (based on complexity)

**Constraints**:
- **Sequential**: Depends on Tasks 4 & 5 (need anomalies + summary)
- **Not parallelizable**: Single decision point
- **Checkpoint**: This is a natural **human-in-the-loop** checkpoint:
  - Auto-approved contracts (no review needed) → Fast path to executed-contracts archive
  - Flagged contracts → Route to Slack/email queue for legal team
  - High-priority → Dashboard alert

**Implementation Notes**:
- Triage rules (configurable per company):
  ```
  if any anomaly.risk_level == "CRITICAL":
      requires_review = True
      priority = "urgent"
      suggested_reviewer = "general_counsel"
  elif any anomaly.risk_level == "HIGH":
      requires_review = True
      priority = "high"
      suggested_reviewer = "senior_attorney"
  elif len(anomalies) > 3 and any anomaly.risk_level == "MEDIUM":
      requires_review = True
      priority = "normal"
      suggested_reviewer = "junior_attorney"
  else:
      requires_review = False
  ```
- Estimated review time: Heuristic based on anomaly count/severity and contract length
- Save decision to database for audit trail

**Error Handling**:
- If anomaly detection was uncertain (low confidence), default to escalate (safe mode)

**Estimated Complexity**: ⭐⭐ (simple; rule-based triage)

---

### Task 7: Human Review & Feedback Loop (Interactive, Downstream of 6)

**Purpose**: Lawyer reviews flagged contracts, provides feedback, and validates/corrects model outputs.

**Inputs**:
- Full `ContractAnalysisResult` from prior tasks
- Rendered UI with:
  - Executive summary
  - Extracted clauses (highlighted, with page numbers)
  - Flagged anomalies (with evidence quotes)
  - Triage recommendation

**Outputs**:
- `HumanReviewFeedback`:
  - `contract_id`: Which contract was reviewed
  - `human_validation`:
    - `type_correct`: Was the contract type classification right?
    - `clauses_missed`: Did the model miss any key clauses?
    - `clauses_incorrect`: Did the model misclassify any clause?
    - `anomalies_correct`: Were the flagged anomalies legitimate?
    - `anomalies_missed`: Did the model miss any risky language?
    - `triage_recommendation_correct`: Should this contract have been escalated?
  - `human_override`:
    - `revised_summary`: Any edits to the summary?
    - `additional_risks`: Any risks the model missed?
    - `business_context`: E.g., "We accepted unlimited liability because [reason]"
  - `model_improvement_signal`: Feedback to improve the LLM prompts

**Constraints**:
- **Not automatable**: Requires human domain expertise (licensed attorney or law graduate)
- **Checkpoint**: This is where the model learns; feedback is used to improve prompts
- **Parallelizable**: Multiple lawyers can review different contracts simultaneously
- **Optional**: Some contracts may be auto-approved and skip review

**Implementation Notes**:
- Streamlit/FastAPI UI for lawyer review:
  - Left panel: Original PDF/contract text (scrollable)
  - Right panel: Model outputs (summary, clauses, anomalies)
  - Action buttons: "Approve", "Reject", "Needs revision", "Flag for escalation"
  - Comment field: Capture rationale
- Feedback storage: Save to database for ML training / prompt refinement
- Closure tracking: When lawyer approves, mark contract as "reviewed" with timestamp

**Error Handling**:
- Reviewer disconnects → Save progress in database; allow resumption
- Reviewer override conflicts with model → Log for analysis; adjust triage thresholds

**Estimated Complexity**: ⭐⭐⭐⭐ (high; requires interactive UI + feedback capture)

---

## Dependency Graph

```
┌────────────────────────────────────────────────────────────────────────────┐
│ CONTRACT ANALYSIS PIPELINE - DEPENDENCY GRAPH                               │
└────────────────────────────────────────────────────────────────────────────┘

        INPUT: PDF/Raw Contract
              │
              ▼
    ┌─────────────────────┐
    │ Task 1: Ingestion   │  (Sequential, Critical Path Start)
    │ - Extract text      │  ⏱️ ~1 sec per contract
    │ - Detect pages      │  
    │ - Check confidence  │
    └─────────────────────┘
              │
              ▼
    ┌─────────────────────────────────┐
    │ Task 2: Classification          │  (Sequential, Depends on 1)
    │ - Predict contract type (NDA,   │  ⏱️ ~3 sec per contract
    │   SaaS, License, etc.)          │
    │ - Confidence scoring            │
    └─────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ Task 3: Clause Extraction (PARALLEL EXECUTION WITHIN TASK) │
    │ ────────────────────────────────────────────────────────── │
    │ Detector 3a: Termination Clauses                            │
    │ Detector 3b: Liability Clauses                              │
    │ Detector 3c: Indemnification Clauses                        │
    │ Detector 3d: Payment Terms                                  │
    │ Detector 3e: IP Ownership                                   │
    │ [All run in parallel; merge results at end]                │
    │ Depends on Task 2 for type-guided extraction                │
    │ ⏱️ ~5 sec per contract (parallel)                           │
    └─────────────────────────────────────────────────────────────┘
              │
              ├─────────────────────────────────────┐
              │                                     │
              ▼                                     ▼
    ┌──────────────────────────┐      ┌──────────────────────────────┐
    │ Task 4: Anomaly          │      │ Task 5: Summarization        │
    │ Detection (PARALLEL)     │      │ (Sequential, Depends on 3&4) │
    │ ──────────────────────   │      │ ────────────────────────────│
    │ Detector 4a: Liability   │      │ - Generate executive summary │
    │ Detector 4b: One-sided   │      │ - Highlight risks            │
    │ Detector 4c: Auto-renew  │      │ - Key obligations/rights     │
    │ Detector 4d: Indemnity   │      │ ⏱️ ~2 sec per contract      │
    │ [All run in parallel]    │      └──────────────────────────────┘
    │ Depends on Task 3        │                │
    │ ⏱️ ~4 sec per contract   │                │
    │ (parallel)               │                │
    └──────────────────────────┘                │
              │                                 │
              └─────────────────────┬───────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │ Task 6: Triage Decision       │
                    │ ────────────────────────────  │
                    │ - Requires legal review?      │
                    │ - Set priority                │
                    │ - Suggest reviewer            │
                    │ ⏱️ ~0.5 sec per contract     │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    │                                │
         (No Review)▼                                ▼(Requires Review)
    ┌──────────────────────┐          ┌──────────────────────────────────┐
    │ Auto-Approved Path   │          │ Task 7: Human Review & Feedback  │
    │ ───────────────────  │          │ ─────────────────────────────    │
    │ - Archive contract   │          │ - Lawyer reviews in UI           │
    │ - Update status DB   │          │ - Validates/corrects output     │
    │ - Send notification  │          │ - Provides feedback signals     │
    └──────────────────────┘          │ - [INTERACTIVE/CHECKPOINT]      │
              │                       │ ⏱️ 5-30 min per contract        │
              │                       │    (human-dependent)             │
              └───────────────────────┴──────────────────────────────────┘
                                    │
                                    ▼
                            ┌────────────────┐
                            │ OUTPUT: Final  │
                            │ Reviewed Result│
                            │ (sent to DB)   │
                            └────────────────┘
```

---

## Parallelization Strategy

### **Intra-Task Parallelization** (Within a single task)

| Task | Parallelizable Subtasks | Implementation |
|------|-------------------------|-----------------|
| **Task 3: Clause Extraction** | Extract termination + liability + indemnity clauses in parallel | 5–10 independent LLM calls (one per clause type) |
| **Task 4: Anomaly Detection** | Check unlimited liability + one-sided terms + auto-renewal traps in parallel | 4–6 independent anomaly detectors (rule + LLM-based) |
| **Task 7: Human Review** | Multiple lawyers review different contracts simultaneously | Distributed UI (Streamlit + database) |

**Speedup Estimate**:
- Sequential (one clause extractor): 10 sec → Parallel (5 extractors): 2 sec (5× speedup)
- Sequential (anomalies): 8 sec → Parallel (4 detectors): 2 sec (4× speedup)

### **Inter-Task Parallelization** (Multiple contracts in parallel)

```
Batch Processing:
50 contracts → Process in batches of 5–10

Time Estimate (Sequential):
- 50 contracts × 15 sec/contract ≈ 750 sec ≈ 12.5 minutes

Time Estimate (Batch Parallel, 10 workers):
- 50 contracts / 10 workers × 15 sec ≈ 75 sec ≈ 1.25 minutes
- Speedup: ~10×
```

**Implementation**:
- Task queue (Celery, Ray, or AWS Lambda)
- Batch processing: Process 10 contracts in parallel via LangGraph RemoteRunnable or async tasks
- Wait at Task 6 triage (bottleneck): Depends on manual review (variable latency)

---

## Critical Path & Bottlenecks

### Critical Path (Longest Sequential Chain)

```
Task 1 → Task 2 → Task 3 → Task 4 & 5 (parallel) → Task 6 → Task 7 (human)
 1 sec    3 sec    5 sec    4 + 2 sec = 6 sec      0.5 sec   5-30 min
─────────────────────────────────────────────────────────────────────────
TOTAL: ~15 sec (automated) + 5-30 min (human review) = HUMAN-DOMINATED
```

### Bottlenecks

1. **Human Review (Task 7)**: 
   - Automated tasks: 15 sec total
   - Human review: 5–30 minutes per contract
   - **Mitigation**: Batch-triage to parallelize (multiple lawyers)

2. **LLM Rate Limits** (if using API):
   - If using GPT-4, rate limits may throttle parallel calls
   - **Mitigation**: Use batch API; cache few-shot examples; pre-compute common patterns

3. **Clause Extraction Quality** (Task 3):
   - If clauses poorly extracted, all downstream tasks suffer
   - **Mitigation**: High confidence threshold; escalate uncertain extractions to human

---

## Checkpointing & Resumability

### Checkpoints (Save intermediate state)

1. **After Task 1 (Ingestion)**: Save extracted text to database
   - Benefit: Can re-run Tasks 2–7 without re-processing PDF
   
2. **After Task 2 (Classification)**: Save contract type + confidence
   - Benefit: Adaptive extraction strategies in Task 3
   
3. **After Task 3 (Clause Extraction)**: Save all extracted clauses
   - Benefit: Can retry anomaly detection with new rules without re-extracting
   
4. **After Task 6 (Triage)**: Save triage decision + routing decision
   - Benefit: Track which contracts are pending human review vs. auto-approved
   
5. **After Task 7 (Human Review)**: Save lawyer feedback + overrides
   - Benefit: Build training dataset for model improvement; enable reprocessing

### Resumability

```python
# Pseudocode: Resume from checkpoint
def process_contract_with_checkpoints(contract_id):
    # Check if already in DB
    result = db.get_analysis_result(contract_id)
    
    if not result.ingestion_complete:
        result = ingest_document(contract_id)
        db.save(result)
    
    if not result.classification_complete:
        result = classify_contract(result)
        db.save(result)
    
    if not result.clauses_extracted:
        result = extract_clauses(result)
        db.save(result)
    
    # ... continue through remaining tasks
    
    return result
```

---

## Evaluation Framework

### Per-Task Metrics

| Task | Evaluation Metric | Target | Data Source |
|------|-------------------|--------|-------------|
| **1: Ingestion** | Text extraction rate (% contracts with >90% text confidence) | ≥ 95% | Ground truth: manual inspection of 10 contracts |
| **2: Classification** | Accuracy (correct contract type) | ≥ 90% | Ground truth: 50 contracts with labeled types |
| **3: Clause Extraction** | Precision, Recall, F1 per clause type | ≥ 80% P, ≥ 85% R | Ground truth: expert-annotated clauses (50 contracts) |
| **4: Anomaly Detection** | Precision, Recall, F1 per anomaly type | ≥ 75% P, ≥ 85% R | Ground truth: expert-flagged anomalies (50 contracts) |
| **5: Summarization** | ROUGE-L (summary similarity) + Human rating | ≥ 0.50 ROUGE-L | Manual human evaluation (10 contracts) |
| **6: Triage** | Accuracy on review/no-review decision | ≥ 85% | Ground truth: expert review determination (50 contracts) |
| **7: Human Feedback** | Inter-annotator agreement (κ Cohen's kappa) | ≥ 0.7 | Multiple lawyers review same contract |

### End-to-End Metrics

- **Time to triage**: From PDF to triage decision (human review needed? yes/no)
  - Target: < 20 sec automated; < 5 min with human review
  
- **Cost per contract**: (LLM API costs + infrastructure + human review time)
  - Target: < $50 per contract (vs. $500–$2000 lawyer review)
  
- **Accuracy on business outcome**: Do predicted risky clauses correlate with future disputes?
  - Tracked over time (longer-term success measure)

---

## Implementation Roadmap

### Phase 1: Core Pipeline (Weeks 1–2)
- [ ] Tasks 1–6 implemented (automated path)
- [ ] Ground truth dataset of 50 contracts
- [ ] Unit tests for each task
- [ ] Evaluation harness

### Phase 2: Human-in-Loop (Week 3)
- [ ] Task 7 UI (Streamlit for lawyer review)
- [ ] Feedback capture + database storage
- [ ] Resume-from-checkpoint infrastructure

### Phase 3: Optimization & Scaling (Week 4)
- [ ] Parallel batch processing (LangGraph RemoteRunnable)
- [ ] Prompt refinement based on Task 7 feedback
- [ ] Performance tuning (reduce LLM latency, improve accuracy)

### Phase 4: Evaluation & Deployment (Week 5)
- [ ] Full evaluation against ground truth (all 50 contracts)
- [ ] Metric reporting (precision, recall, cost, time)
- [ ] Lessons learned document

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| **LLM hallucination in clause extraction** | High | Poor downstream results | Require evidence quotes; few-shot examples; schema validation |
| **Human review bottleneck** | High | Can't scale beyond ~10 contracts/day | Parallelized UI; feedback loop to improve triage |
| **Ambiguous clauses** (hard to classify) | Medium | Uncertainty in anomaly detection | Flag low-confidence clauses for escalation |
| **Scope creep** (add more contract types) | Medium | Timeline overrun | Fix at 10 types; defer additional types |
| **PDF parsing failures** | Low | Skip contracts; lose evaluation data | Fallback to manual upload; OCR validation |

---

## Success Criteria

- ✅ All 7 tasks implemented and integrated
- ✅ End-to-end pipeline processes 50 contracts in < 15 minutes (automated)
- ✅ Clause extraction F1 ≥ 80%
- ✅ Anomaly detection recall ≥ 85% (catch risky clauses)
- ✅ Triage accuracy ≥ 85%
- ✅ Human review UI functional and tested with 3+ lawyers
- ✅ Ground truth evaluation complete; metrics documented
- ✅ Architectural document (this WP) complete and reviewed

---

## References

- WP-2.3: Orchestration Pattern (LangGraph task sequencing)
- WP-2.6: LangGraph for Stateful Graphs (state management across tasks)
- WP-2.7: Checkpointing and Human-in-the-Loop (checkpoint architecture)
- WP-3.4: Evaluation Framework (metric definitions)
- Contract Analysis Schema (Pydantic models)
- Ground Truth Dataset (50 contracts with annotations)

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-01  
**Author**: Architecture Portfolio  
**Status**: ✅ Approved for Implementation
