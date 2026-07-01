# WP-4.1: Domain Selection ADR — Legal Contract Clause Analysis

**Work Product Type**: Architecture Decision Record (ADR)  
**Phase**: 4 — Capstone: End-to-End Agentic System  
**Date**: 2026-04-01  
**Status**: ✅ Accepted  
**Replaces**: [None]  

---

## Executive Summary

This ADR justifies the selection of **Legal Contract Clause Analysis** as the capstone domain for this portfolio. We evaluate it against three axes: **(1) clear success/failure criteria, (2) high real-world impact and friction, (3) requires human judgment for edge cases**. We show why this domain outperforms three rejected alternatives: financial reconciliation, medical record summarization, and customer support ticket routing.

**Recommendation**: Proceed with Legal Contract Clause Analysis as the capstone problem. Its combination of high friction, measurable success criteria, and inherent need for human-in-the-loop makes it an excellent vehicle for demonstrating all prior portfolio concepts (RAG, orchestration, choreography, checkpointing, memory, agents).

---

## Problem Statement

Capstone projects must:
- Demonstrate end-to-end agentic AI system design
- Integrate all prior portfolio concepts (foundations, memory, multi-agent orchestration, RAG)
- Have clear, measurable success/failure criteria
- Reflect real-world friction and impact
- Require human judgment (not solvable by pure automation)

This ADR selects the narrowest, most tractable domain that satisfies all constraints.

---

## Domain Selection Criteria

### Axis 1: Clear Success/Failure Criteria

**Why it matters**: Without measurable criteria, we can't evaluate our system. The capstone must produce concrete outputs we can validate against ground truth.

**Our Baseline Requirement**: The domain must support:
- Objective classification tasks (e.g., "Is this an NDA?")
- Structured extraction (e.g., "Extract all liability caps")
- Binary risk flags (e.g., "Does this require legal review?")
- Human validation (comparison against expert annotations)

**Scoring Rubric**:
- ⭐⭐⭐⭐⭐ (5/5): Domain has public benchmarks, expert ground truth, and numerical metrics
- ⭐⭐⭐⭐ (4/5): Domain measurable but requires custom annotation
- ⭐⭐⭐ (3/5): Domain has partial metrics; some subjective components
- ⭐⭐ (2/5): Mostly subjective; hard to evaluate
- ⭐ (1/5): No clear success criteria

---

## Candidate Domains

### ✅ SELECTED: Legal Contract Clause Analysis

**Domain Description**:
Extract and classify key clauses (termination, liability, indemnification) from commercial contracts. Detect risky language patterns (unlimited liability, one-sided termination, automatic renewal traps). Flag for human legal review.

**Clear Success/Failure Criteria** ⭐⭐⭐⭐⭐:
- **Type Classification**: Did the model correctly classify contract type (NDA, SaaS, License, etc.)? → Accuracy metric
- **Clause Extraction**: Did the model find all key clauses? → Precision / Recall / F1
- **Anomaly Detection**: Did the model catch risky language that experts flagged? → Precision / Recall / F1
- **Review Triage**: Did the model correctly determine if legal review needed? → Accuracy
- **Ground Truth Available**: We can hire paralegals/law students to annotate a small corpus (50–100 contracts)

**Why Measurable**:
- Each task has binary/categorical outputs (e.g., "is this NDA?" → yes/no)
- Lawyer annotations provide gold standard for evaluation
- Industry standards exist (e.g., contract review SLAs, risk classification frameworks)

**Real-World Impact & Friction** ⭐⭐⭐⭐⭐:
- **Pain Point**: Contract review consumes 20–40 hours per deal (M&A, vendor onboarding, partnership)
- **Cost**: $500–$2000 per contract (lawyer time)
- **Friction**: Repetitive manual work; high error rate due to fatigue; inconsistent standards
- **Market**: $2B+ legal AI market; major players include LexisNexis, Thomson Reuters, Kira Systems
- **Real Urgency**: Companies have 100s–1000s of vendors; can't afford full lawyer review for all

**Requires Human Judgment** ⭐⭐⭐⭐⭐:
- **Edge Cases Abound**: 
  - "Is a 60-day notice period unusual?" (Depends on contract type, industry, context)
  - "Is this liability cap reasonable?" (Depends on deal size, risk profile, precedent)
  - "Does this clause cross legal/policy line?" (Needs human judgment)
- **Not Automatable**: Can't simply hardcode "if liability_cap > $X then flag"; every company has different thresholds
- **Human-in-Loop Essential**: ML model triages; human lawyer makes final call

---

### ❌ REJECTED: Financial Reconciliation

**Domain**: Match/reconcile transactions across accounting ledgers (GL, AR, AP). Flag discrepancies.

**Why Rejected**:

| Axis | Score | Reason |
|------|-------|--------|
| **Success Criteria** | ⭐⭐⭐⭐⭐ | Perfect—binary match/no-match. Industry has standard metrics. ✅ |
| **Real-World Impact** | ⭐⭐⭐ | Needed by finance teams, but: (1) Often outsourced to offshore teams, (2) Narrower market than legal. |
| **Human Judgment** | ⭐ | **Critical Gap**: Most reconciliation is rule-based (amount + date + GL code matching). Rules can be hardcoded. Once edge cases arise, solution is often: "escalate to accountant." Little iterative learning. ❌ |

**Verdict**: Too narrow + low need for sophisticated human judgment. Would reduce capstone to simple matching + rule escalation.

---

### ❌ REJECTED: Medical Record Summarization

**Domain**: Read patient discharge summaries (PDF/text). Extract diagnosis, medications, follow-up instructions. Summarize in structured format for handoff.

**Why Rejected**:

| Axis | Score | Reason |
|------|-------|--------|
| **Success Criteria** | ⭐⭐⭐ | Partial: Can measure if key medications/diagnoses extracted (F1). But summarization quality is subjective. Needs ROUGE/human-rated evaluation. ✅~❌ |
| **Real-World Impact** | ⭐⭐⭐⭐⭐ | Healthcare ≈ $1T+ market. Clinical handoff errors kill people. ✅ |
| **Human Judgment** | ⭐⭐⭐⭐ | Clinicians must validate summaries. But often: (1) Structured data (meds) is objective, (2) Free-text summaries are subjective. Hard to build ground truth. |

**Verdict**: High impact + human judgment, but: (1) **Regulatory/privacy burden** (HIPAA, de-identification), (2) **Hard to acquire datasets** (small private hospitals), (3) **Subjective evaluation** makes capstone less teachable.

---

### ❌ REJECTED: Customer Support Ticket Routing

**Domain**: Read incoming support tickets. Classify by issue type (billing, technical, feature request). Route to correct team. Predict resolution time.

**Why Rejected**:

| Axis | Score | Reason |
|------|-------|--------|
| **Success Criteria** | ⭐⭐⭐⭐ | Routing = multiclass classification. Easy to measure. ✅ |
| **Real-World Impact** | ⭐⭐⭐ | Common problem, but: Many companies already use Zendesk/intercom rules. Issue less acute. |
| **Human Judgment** | ⭐⭐ | **Critical Gap**: Most tickets classifiable by keyword rules + historical data. Edge cases (e.g., "I like your product but wish X") are rare. System can work with 80% accuracy with minimal human involvement. ❌ |

**Verdict**: Measurable but low friction + low need for human judgment. Doesn't exercise portfolio concepts (especially human-in-loop checkpointing, memory, multi-agent orchestration).

---

## Comparative Table

| **Axis** | **Contract Analysis** | **Financial Reconciliation** | **Medical Summarization** | **Support Routing** |
|----------|---------------------|--------------------------|------------------------|-------------------|
| **Clear Criteria** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Real Impact** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Human Judgment** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Portfolio Fit** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| ****TOTAL** | **⭐⭐⭐⭐⭐** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

**WINNER**: Legal Contract Clause Analysis (4.75 / 5.0)

---

## Why Legal Contract Analysis is the Best Fit

### 1. Clear Success/Failure ✅

**Concrete Deliverables**:
- 50 annotated contracts with ground truth (contract type, extracted clauses, anomalies, review flag)
- Evaluation metrics: clause extraction F1, anomaly detection precision/recall, review triage accuracy
- Public baseline: We can compare against industry APIs (Kira Systems, Westlaw AI)

**Measurable Trajectory**:
- Baseline: Simple regex + keyword rules → 50% F1
- Phase 1: Prompt-based extraction (GPT-4 + Pydantic schema) → 75% F1
- Phase 2: RAG + few-shot → 82% F1
- Phase 3: Multi-agent orchestration + memory → 88% F1

---

### 2. High Real-World Impact ✅

**Industry Pain Points**:
- M&A / Financing: Review 100s of vendor contracts before deal close. Lawyers bottleneck. Cost: $50K–$500K per deal.
- Procurement: Every vendor agreement differs. Manual clause review delays purchase orders. Friction: 2–4 weeks per contract.
- Compliance: Need to audit old contracts for GDPR, SOC2, new regulations. Cost: $100K+ for dedicated legal staff.

**Our Competitive Advantage**:
- Agnostic: Works across contract types (NDAs, SaaS, purchase, employment)
- Explainable: Flags specific risky language (vs. black-box decision)
- Tunable: Can set risk thresholds per company policy

---

### 3. Requires Human Judgment ✅

**Why Automation Alone Fails**:
1. **Context-Dependent Anomalies**: 
   - "No liability cap" is critical for a $10M software deal but tolerable for $10K t-shirt printing
   - "Automatic renewal" is a red flag for consumers but normal for vendor relationships
2. **Precedent-Heavy**:
   - Lawyer says: "This indemnity is too broad" → But needs judgment: too broad vs. what? Prior deals? Industry norms?
3. **Business vs. Legal Trade-offs**:
   - Model: "Flag unlimited liability"
   - CFO: "We'll accept it; vendor won't budge; deal is strategic"
   - Lawyer: "Okay, but document that risk decision"

**Perfect for Human-in-Loop**:
- ML model: Fast triage (50 contracts in minutes)
- Human lawyer: Deep review (focus on flagged contracts only)
- Workflow: LLM extracts → Flags anomalies → Lawyer reviews → Provides feedback → Model improves

---

### 4. Portfolio Integration ✅

Capstone exercise demands using:
- **RAG** (WP-3.x): Retrieve prior similar contracts ("Show me precedent NDAs")
- **Orchestration** (WP-2.3): Sequence tasks (Load → Classify → Extract → Flag → Summarize)
- **Choreography** (WP-2.4): Handle edge cases with event-driven agent coordination
- **Memory** (WP-2.1): Remember contract context across analysis steps; handle long documents
- **Checkpointing** (WP-2.7): Save intermediate state; allow human intervention mid-analysis
- **Multi-Agent** (WP-3.8): Specialized agents (classifier, extractor, risk-flagger, summarizer)
- **Evaluation** (WP-3.4): Measure against ground truth; iterate

**All prior patterns get exercised naturally**.

---

## Implementation Scope

### In Scope (Capstone MVP)
1. **Pydantic schema** for contract analysis (clauses, anomalies, summary)
2. **50 ground truth contracts** with expert annotations (5 per type × 10 types)
3. **LLM-based classifier** (identify contract type)
4. **Clause extractor** (identify liability, termination, indemnity, etc.)
5. **Anomaly detector** (flag risky language)
6. **Risk summarizer** (executive summary + flags for legal review)
7. **Evaluation harness** (compare model output vs. ground truth)
8. **Human review loop** (Streamlit/FastAPI for lawyer validation + feedback)

### Out of Scope
- Full PDF parsing (assume text extraction pre-done)
- Multi-language support
- Real-time deployment (SaaS setup)
- Compliance auditing beyond risk flagging

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Ground truth annotation is slow/expensive | Medium | Blocks evaluation | Limit to 50 contracts; use law student annotators; create template-based shortcuts |
| LLM hallucination in clause extraction | High | False positives/negatives | (1) Use Pydantic schema to enforce structure, (2) Require evidence quotes, (3) Few-shot examples |
| Edge cases confound evaluation | Medium | Metrics misleading | (1) Document edge cases separately, (2) Report per-class metrics (NDA vs. SaaS), (3) Track inter-annotator agreement |
| Scope creep (add more contract types) | High | Timeline overrun | Fix at 10 types × 5 contracts = 50 total; defer additional types to future work |

---

## Decision

**Accepted** ✅

Legal Contract Clause Analysis is chosen as the capstone domain because it:
1. ✅ Has clear, measurable success criteria (clause extraction F1, anomaly detection, review triage accuracy)
2. ✅ Addresses high real-world friction ($2B+ legal AI market; weeks of manual work per deal)
3. ✅ Inherently requires human judgment (context-dependent, precedent-heavy, business trade-offs)
4. ✅ Naturally integrates all prior portfolio concepts (RAG + orchestration + memory + agents)
5. ✅ Narrowed to a tractable MVP scope (50 contracts, 10 types, core clauses only)

---

## Next Steps

1. **WP-4.2**: Task Decomposition Document
   - Break down the capstone into granular subtasks
   - Identify which steps are parallelizable
   - Sequence dependencies

2. **WP-4.3**: Contract Schema & Ground Truth Dataset
   - Pydantic models for clauses, anomalies, evaluation metrics
   - Generate/annotate 50 representative contracts
   - Create JSONL test dataset

3. **WP-4.4–4.6**: Agentic Implementation
   - Classifier agent (contract type)
   - Extractor agent (clauses + anomalies)
   - Orchestration graph (LangGraph)

4. **WP-4.7**: Evaluation & Results
   - Measure precision/recall vs. ground truth
   - Document failure modes
   - Publish metrics and lessons learned

---

## References

- WP-2.3: Orchestration Pattern (LangGraph basics)
- WP-2.4: Choreography Pattern (event-driven coordination)
- WP-2.7: Checkpointing and Human-in-the-Loop
- WP-3.0–3.8: RAG and Multi-Agent Architectures
- ADR-003: Agentic RAG vs. Naive RAG

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-01  
**Author**: Architecture Portfolio  
**Status**: ✅ Approved for Capstone Phase
