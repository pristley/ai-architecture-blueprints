# WP-4.5: Human-in-the-Loop (HITL) Checkpoint Architecture

**Work Product Type**: System Design & Interaction Flow  
**Phase**: 4 — Capstone: End-to-End Agentic System  
**Date**: 2026-04-02  
**Status**: ✅ Accepted  

---

## Executive Summary

This document specifies the **checkpoint architecture** where humans enter the autonomous contract analysis loop. We define:

1. **State Machine** — Four distinct states (ANALYZING, PENDING_HUMAN_REVIEW, INCORPORATING_FEEDBACK, COMPLETE)
2. **Decision Triggers** — When contracts are escalated to human review
3. **Human Interface** — What information humans see and actions available
4. **Feedback Integration** — How human decisions flow back into the pipeline
5. **Task 7 Integration** — How HITL fits into the 7-task orchestration

**Philosophy**: Humans are *decision makers*, not data entry clerks. They see the agent's reasoning, confidence, and anomaly evidence. They make binary/multi-choice decisions that improve model performance through feedback loops.

---

## Part 1: State Machine Architecture

### Overview

```mermaid
stateDiagram-v2
    [*] --> ANALYZING: Contract Submitted
    
    ANALYZING --> PENDING_HUMAN_REVIEW: Escalation Threshold Met
    ANALYZING --> COMPLETE: No Human Review Needed
    
    PENDING_HUMAN_REVIEW --> INCORPORATING_FEEDBACK: Human Decision Received
    PENDING_HUMAN_REVIEW --> ESCALATE_LEGAL: Escalation Requested by Human
    
    INCORPORATING_FEEDBACK --> COMPLETE: Feedback Integrated
    INCORPORATING_FEEDBACK --> PENDING_HUMAN_REVIEW: Feedback Rejected; Re-escalated
    
    COMPLETE --> [*]
    ESCALATE_LEGAL --> [*]
    
    note right of ANALYZING
        Tasks 1-6 automated
        Duration: ~10 sec
        Exit: Escalation decision
    end note
    
    note right of PENDING_HUMAN_REVIEW
        Waiting for human action
        Duration: 1 min - 1 hour (SLA)
        Exit: Human decision received
    end note
    
    note right of INCORPORATING_FEEDBACK
        Process feedback
        Re-run affected tasks
        Duration: ~5 sec
        Exit: Updated result
    end note
    
    note right of COMPLETE
        Final result ready
        Stored with audit trail
        Duration: 0 (terminal)
    end note
```

### State Definitions

#### **State 1: ANALYZING**
**Description**: Autonomous agent processes contract through Tasks 1-6 (ingestion, classification, extraction, anomaly detection, summarization, triage).

**Entry Conditions**:
- Contract submitted to system
- Passes input validation (Guardrail 2)

**Exit Conditions**:
- Escalation threshold met → PENDING_HUMAN_REVIEW
- All tasks complete, no escalation → COMPLETE

**Substates** (if detailed):
1. INGESTING (Task 1: ~1 sec)
2. CLASSIFYING (Task 2: ~3 sec)
3. EXTRACTING_CLAUSES (Task 3: ~5 sec)
4. DETECTING_ANOMALIES (Task 4: ~4 sec)
5. SUMMARIZING (Task 5: ~2 sec)
6. TRIAGING (Task 6: ~0.5 sec)

**Data Available**:
- Raw contract text (sanitized, per Guardrail 1)
- Contract type (with confidence)
- Extracted clauses (with evidence quotes)
- Detected anomalies (with risk scores)
- Summary + key findings
- Triage decision (review needed? yes/no)

**Duration**: 10-15 seconds per contract

---

#### **State 2: PENDING_HUMAN_REVIEW**
**Description**: Waiting for human lawyer/reviewer to make a decision on flagged contract.

**Entry Conditions**:
- Any of these triggers:
  1. Confidence below threshold on classification (Guardrail 3)
  2. Evidence validation failed on clauses (Guardrail 4)
  3. Multiple anomalies detected (risk score > threshold)
  4. Triage decision = "requires_human_review" (Task 6)
  5. Type-specific bias detected (Guardrail 9)

**Exit Conditions**:
- Human makes decision (Approve/Reject/Modify/Escalate)
- Timeout reached (SLA violation) → ESCALATE_LEGAL
- System auto-resolves based on fallback logic

**Queue Position**: Determined by priority (see WP-4.6)

**Duration**: 1 minute (target) to 1 hour (SLA)

**Monitoring**:
- Time in queue
- Reviewer assignment status
- Escalation flag if timeout approaching

---

#### **State 3: INCORPORATING_FEEDBACK**
**Description**: System processes human feedback and potentially re-analyzes affected sections.

**Entry Conditions**:
- Human decision received from PENDING_HUMAN_REVIEW
- Decision type: Approve, Reject, or Modify

**Processing Logic**:

**Case 1: APPROVE**
- Accept all agent outputs as-is
- Store human feedback in audit trail
- Transition → COMPLETE

**Case 2: REJECT**
- Mark specific clauses/anomalies as incorrect
- Flag for model retraining
- Keep original agent output but mark as "human-rejected"
- Transition → COMPLETE (with rejection annotation)

**Case 3: MODIFY**
- Human provides corrected/alternative extraction
- Replace agent output with human correction
- Store both versions (for comparison + retraining)
- Re-run anomaly detection on corrected clauses
- Transition → COMPLETE or → PENDING_HUMAN_REVIEW (if new anomalies detected)

**Case 4: ESCALATE**
- Mark contract as requiring legal escalation
- Add human reasoning/concerns to audit trail
- Transition → ESCALATE_LEGAL

**Exit Conditions**:
- Feedback processed successfully → COMPLETE
- Feedback creates contradictions → PENDING_HUMAN_REVIEW (re-escalate)
- Escalation requested → ESCALATE_LEGAL

**Duration**: 5-10 seconds

**Audit Trail**:
```json
{
  "human_feedback": {
    "reviewer_id": "lawyer_001",
    "timestamp": "2026-04-02T14:30:00Z",
    "decision": "modify",
    "modifications": [
      {
        "clause_id": "li_001",
        "agent_output": "Liability capped at $1M",
        "human_correction": "Liability capped at $1M for non-critical failures only",
        "reason": "Clause is conditional; agent missed qualifier"
      }
    ],
    "confidence_feedback": "Agent was overconfident on clause extraction (80% vs actual 45%)"
  }
}
```

---

#### **State 4: COMPLETE**
**Description**: Contract analysis finalized and ready for downstream use.

**Entry Conditions**:
- ANALYZING → COMPLETE (no escalation needed)
- INCORPORATING_FEEDBACK → COMPLETE (after feedback processed)

**Exit Conditions** (terminal state):
- No further processing
- Result stored in database with full audit trail
- Ready for legal team consumption or downstream API

**Result Contains**:
- Agent outputs (classification, clauses, anomalies, summary)
- Human feedback (if any)
- Confidence scores (both agent and validated by human)
- Audit trail (who reviewed, when, what changes)
- Recommendation (next steps for legal team)

---

### Special State: ESCALATE_LEGAL

**Entry Conditions**:
- Human clicks "Escalate to Legal Team"
- Or timeout + no human response within SLA

**Processing**:
- Mark contract as requiring expert legal review
- Add context (what the agent found, where it failed, etc.)
- Notify legal team (via WP-4.6 queue system)
- Store in high-priority legal queue

**This is NOT part of HITL loop** — it's for complex cases that need real lawyers.

---

## Part 2: Escalation Triggers

These conditions cause automatic escalation to PENDING_HUMAN_REVIEW:

### 2.1 Confidence-Based Triggers

```python
# tasks/task_6_triage.py

ESCALATION_TRIGGERS = {
    "low_classification_confidence": {
        "threshold": 0.70,  # If contract type confidence < 70%
        "priority": "high",
        "context": "Classification uncertain; agent unsure of contract type"
    },
    "low_extraction_confidence": {
        "threshold": 0.65,  # If clause extraction avg confidence < 65%
        "priority": "medium",
        "context": "Extracted clauses have low confidence scores"
    },
    "low_anomaly_confidence": {
        "threshold": 0.70,  # If anomaly detection confidence < 70%
        "priority": "medium",
        "context": "Agent flagged anomalies but confidence is borderline"
    },
    "evidence_validation_failed": {
        "threshold": "> 10% of clauses",  # If > 10% failed evidence check
        "priority": "high",
        "context": "Agent hallucinating evidence; quotes don't appear in source"
    },
    "confidence_overstatement": {
        "threshold": "deviation > 0.15",  # If confidence score vs actual accuracy deviation > 15%
        "priority": "high",
        "context": "Calibration error; agent overconfident relative to historical accuracy"
    }
}
```

### 2.2 Anomaly-Based Triggers

```python
ANOMALY_ESCALATION = {
    "critical_anomalies": {
        "threshold": "> 0",  # Any critical anomaly detected
        "priority": "critical",
        "context": "Contract has high-risk clause; needs immediate review"
    },
    "multiple_high_anomalies": {
        "threshold": ">= 3",  # 3+ high-risk anomalies
        "priority": "high",
        "context": "Multiple red flags; contract may be unfavorable"
    },
    "conflicting_findings": {
        "threshold": "anomaly contradicts summary",
        "priority": "high",
        "context": "Agent flagged anomaly but summary doesn't mention risk; inconsistency"
    }
}
```

### 2.3 Data Quality Triggers

```python
DATA_QUALITY_ESCALATION = {
    "corrupted_input": {
        "trigger": "Input validation failed despite passing Guardrail 2",
        "priority": "critical",
        "action": "Escalate to legal with warning"
    },
    "missing_critical_sections": {
        "trigger": "Key sections missing (e.g., termination clause in employment contract)",
        "priority": "high",
        "action": "Flag as incomplete; ask human to verify original"
    },
    "duplicate_contract": {
        "trigger": "Contract hash matches existing analyzed contract",
        "priority": "low",
        "action": "Reuse previous analysis; escalate if human feedback was provided last time"
    }
}
```

### 2.4 Business Logic Triggers

```python
BUSINESS_ESCALATION = {
    "type_not_in_whitelist": {
        "trigger": "Contract type = UNKNOWN; doesn't match 9 known types",
        "priority": "high",
        "action": "Ask human to classify or provide new type definition"
    },
    "outside_scope": {
        "trigger": "Contract is in SKIP category (e.g., regulatory disclosure)",
        "priority": "medium",
        "action": "Confirm with human before skipping analysis"
    }
}
```

### Summary: Escalation Decision Tree

```
Is ANALYZING state complete?
├─ NO → Stay in ANALYZING
└─ YES → Check escalation triggers:
   ├─ Classification confidence < 70%? → ESCALATE
   ├─ Extraction confidence < 65% AND > 10% clauses? → ESCALATE
   ├─ Evidence validation failed on > 10% clauses? → ESCALATE
   ├─ Any CRITICAL anomalies detected? → ESCALATE
   ├─ 3+ HIGH anomalies detected? → ESCALATE
   ├─ Triage task flagged "review_required = True"? → ESCALATE
   ├─ Type-specific bias detected (per Guardrail 9)? → ESCALATE
   └─ None of above → COMPLETE (no human review)
```

---

## Part 3: Human Interface Specification

### 3.1 Information Displayed

When a contract is PENDING_HUMAN_REVIEW, humans see this interface:

```
╔════════════════════════════════════════════════════════════════════════════╗
║ HUMAN REVIEW INTERFACE — Legal Contract Analysis                           ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║ CONTRACT INFO                                                              ║
│ ├─ ID: contract_2024_001                                                  ║
│ ├─ Name: NDA_AcmeCorp_2026-04-02.pdf                                      ║
│ ├─ Type: NDA (Confidence: 78%)          ⚠ Moderate confidence              ║
│ ├─ Pages: 3                                                               ║
│ ├─ Submitted: 2026-04-02 14:15 UTC                                        ║
│ └─ Time in Queue: 8 minutes 32 seconds                                    ║
║                                                                            ║
║ AGENT'S ANALYSIS SUMMARY                                                  ║
│ ├─ Key Clause Categories:                                                ║
│ │  ├─ Termination: Found 2 clauses (Confidence: 82%)                     ║
│ │  ├─ Confidentiality: Found 3 clauses (Confidence: 91%)                 ║
│ │  └─ Indemnification: Found 1 clause (Confidence: 65%) ⚠ LOW             ║
│ │                                                                         ║
│ ├─ Detected Anomalies:                                                   ║
│ │  ├─ [HIGH] Unlimited Liability (Confidence: 88%)                       ║
│ │  │  Evidence: "Licensor shall be liable for any damages..."            ║
│ │  │  Risk: Unusual for NDAs; typically capped                          ║
│ │  │                                                                     ║
│ │  ├─ [MEDIUM] Perpetual Confidentiality Obligation (Confidence: 79%)   ║
│ │  │  Evidence: "...shall remain confidential in perpetuity"            ║
│ │  │  Risk: Uncommon; most expire after 3-5 years                       ║
│ │  │                                                                     ║
│ │  └─ [LOW] Unilateral Termination (Confidence: 62%) ⚠ LOW              ║
│ │     Evidence: "Party A may terminate at any time..."                  ║
│ │     Risk: One-sided; unusual unless Party A is dominantparty          ║
│ │                                                                         ║
│ └─ Summary: Contract contains 2 uncommon clauses that may benefit from    ║
│    legal review before signing.                                         ║
║                                                                            ║
║ AGENT'S REASONING TRACE (Expandable)                                     ║
│ ├─ [Task 1] Ingestion: Extracted 3 pages, 2,847 words                   ║
│ ├─ [Task 2] Classification:                                              ║
│ │  ├─ Considered types: NDA (78%), ServiceAgr (15%), License (7%)       ║
│ │  ├─ Reasoning: "Multiple mentions of 'confidential information' and   ║
│ │  │             'non-disclosure' indicate NDA. Lower score due to     ║
│ │  │             unusual liability clauses."                            ║
│ │  └─ Decision: NDA                                                      ║
│ │                                                                         ║
│ ├─ [Task 3] Clause Extraction:                                           ║
│ │  ├─ Found 6 clauses total                                             ║
│ │  ├─ Confidence distribution: 65% (1), 79% (1), 82% (2), 91% (2)      ║
│ │  └─ Note: 1 indemnification clause has low confidence (65%)           ║
│ │                                                                         ║
│ └─ [Task 4] Anomaly Detection:                                           ║
│    ├─ Ran 4 parallel anomaly detectors                                  ║
│    ├─ Unlimited_liability detector: HIGH confidence (88%)               ║
│    ├─ Perpetual_term detector: MEDIUM confidence (79%)                 ║
│    └─ Unilateral_termination: LOW confidence (62%)                      ║
║                                                                            ║
║ WHY THIS ESCALATED                                                       ║
│ ├─ Reason 1: Indemnification clause confidence below 70% threshold      ║
│ ├─ Reason 2: CRITICAL anomaly detected (unlimited liability)            ║
│ └─ Reason 3: Agent requests human judgment on unusual contract          ║
║                                                                            ║
║ ─────────────────────────────────────────────────────────────────────    ║
║ HUMAN ACTIONS                                                            ║
│                                                                            ║
│ [ ✓ APPROVE ]     Accept agent's analysis as-is                          ║
│                   → Marks contract COMPLETE                              ║
│                                                                            ║
│ [ ✗ REJECT ]      Agent analysis is wrong                                ║
│                   → Requires detailed feedback (see below)               ║
│                                                                            ║
│ [ ✏ MODIFY ]      Agent is partially right; I'll provide corrections     ║
│                   → Allows inline editing of clauses + anomalies        ║
│                                                                            ║
│ [ ⬆ ESCALATE ]    This needs real legal team attention                  ║
│                   → Marks contract for legal escalation                 ║
│                                                                            ║
│ [ ❓ SKIP ]       This contract is out of scope                          ║
│                   → Skip analysis; mark as not applicable               ║
║                                                                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║ [DETAILED FEEDBACK FORM] (Only shown if REJECT or MODIFY selected)       ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║ CLAUSE CORRECTIONS                                                       ║
│ Clause: indemnification_001                                              ║
│ Agent Found: "Each party indemnifies the other against third-party..."  ║
│ Issue: ○ Hallucinated  ○ Missed context  ○ Wrong interpretation        ║
│ What it should be:                                                      ║
│ [________________________________________________________________________]║
│                                                                            ║
║ ANOMALY FEEDBACK                                                         ║
│ Anomaly: unlimited_liability                                            ║
│ Agent's Confidence: 88%                                                 ║
│ Your Assessment:                                                        ║
│ ○ Agent is correct; this IS a real risk                               ║
│ ○ Agent is wrong; this is normal for this contract type               ║
│ ○ Partially correct; the risk exists but is mitigated by...           ║
│ Details: [_________________________________________________________]     ║
│                                                                            ║
║ GENERAL COMMENTS                                                         ║
│ [________________________________________________________________________]║
│ [________________________________________________________________________]║
│                                                                            ║
║ [ SUBMIT FEEDBACK ]  [ CANCEL ]                                         ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### 3.2 Information Components

#### **Contract Header**
- **ID**: Unique identifier for this analysis
- **Name**: Original filename
- **Type & Confidence**: What the agent thinks it is, with confidence score
- **Metadata**: Page count, submission time, queue position
- **Status**: Current state in the machine

#### **Analysis Summary** (2-3 paragraphs)
- What the agent found at a high level
- Key clauses extracted (with counts)
- Anomalies detected (severity + confidence)
- Overall recommendation

#### **Anomalies Table** (Detailed)
```
| Risk Level | Anomaly Name | Agent Confidence | Evidence Quote | Risk Description | Recommendation |
|------------|--------------|------------------|-----------------|-----------------|-----------------|
| HIGH      | Unlimited Liability | 88% | "Licensor shall be liable for any damages..." | No cap on damages exposure | Flag for negotiation |
| MEDIUM    | Perpetual Confidentiality | 79% | "...shall remain confidential in perpetuity" | Unusual; most expire 3-5 yrs | Consider modification |
| LOW       | Unilateral Termination | 62% | "Party A may terminate at any time..." | One-sided; requires context | Review party roles |
```

#### **Extracted Clauses** (Expandable)
For each detected clause:
- Clause ID
- Type (termination, liability, etc.)
- Agent-extracted text
- Agent confidence (0-100%)
- Page reference
- "[EXPAND]" button to see full context

#### **Agent's Reasoning Trace**
- Task 1-6 execution summary
- LLM prompts (optional, for debugging)
- Classification alternatives considered
- Confidence calibration info
- Why each anomaly was flagged

#### **Escalation Reason**
- Bullet list of why this went to human review
- Specific thresholds triggered
- Guardrails invoked

---

### 3.3 Human Actions

#### **Action 1: APPROVE**
```
Human clicks "✓ APPROVE"
↓
System records:
  - reviewer_id
  - timestamp
  - decision: "approve"
  - confidence_in_approval: [1-5 scale optional]
↓
State transition: PENDING_HUMAN_REVIEW → INCORPORATING_FEEDBACK → COMPLETE
↓
Result: Contract marked as "human-approved"
```

#### **Action 2: REJECT**
```
Human clicks "✗ REJECT"
↓
Modal opens: "Why do you reject this analysis?"
  Options:
  - "Classification is wrong (should be different type)"
  - "Some clauses are hallucinated (don't exist in source)"
  - "Anomalies detected are false alarms"
  - "Analysis missed critical clauses/risks"
  - "Other reason"
  
  Required: Detailed feedback text
↓
System records rejection with feedback
↓
State transition: PENDING_HUMAN_REVIEW → INCORPORATING_FEEDBACK → COMPLETE
  (or PENDING_HUMAN_REVIEW if feedback contradicts contract text)
↓
Result: Contract marked as "human-rejected"; feedback stored for retraining
```

#### **Action 3: MODIFY**
```
Human clicks "✏ MODIFY"
↓
Interface enters EDIT MODE:
  - Inline editing on extracted clauses
  - Can delete/add clauses
  - Can override confidence scores
  - Can correct anomaly interpretations
  - Add comments on modifications
↓
Example modification:
  Clause: "Indemnification" (Agent's version)
  Agent Found: "Each party indemnifies..."
  Human Correction: "Each party indemnifies except for own gross negligence..."
  Comment: "Agent missed the exception clause on line 47"
↓
System records all modifications + reasoning
↓
State transition: PENDING_HUMAN_REVIEW → INCORPORATING_FEEDBACK
  (Re-run anomaly detection on corrected clauses)
  → COMPLETE or PENDING_HUMAN_REVIEW (if new anomalies found)
↓
Result: Contract contains both agent + human versions (for audit trail)
```

#### **Action 4: ESCALATE**
```
Human clicks "⬆ ESCALATE"
↓
Modal opens: "Escalate to Legal Team"
  Reason options:
  - "Requires legal expertise beyond AI"
  - "Ambiguous/complex contract type"
  - "High-risk clauses need legal judgment"
  - "Contract may be unfavorable; negotiate recommended"
  
  Required: Comments for legal team
↓
System records escalation with context
↓
State transition: PENDING_HUMAN_REVIEW → ESCALATE_LEGAL
↓
Action: Contract routed to high-priority legal queue (WP-4.6)
↓
Result: Legal team gets contract + agent's analysis + human's escalation reason
```

#### **Action 5: SKIP**
```
Human clicks "❓ SKIP"
↓
Modal opens: "Why skip this contract?"
  Options:
  - "Out of scope (not a standard contract type)"
  - "Already analyzed before"
  - "Requires original document review (PDF corrupted)"
  - "Other"
↓
System records skip decision
↓
State transition: PENDING_HUMAN_REVIEW → COMPLETE (with "skipped" flag)
↓
Result: Contract archived without further processing
```

---

## Part 4: Feedback Integration Flow

### 4.1 MODIFY Action Detailed Flow

```
HUMAN MODIFICATION
    ↓
┌─────────────────────────────────────────┐
│ Parse human corrections                 │
│  - Clause corrections                   │
│  - Confidence adjustments               │
│  - Anomaly re-assessments               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Validate modifications against source   │
│  - Verify corrected text exists         │
│  - Check for logical consistency        │
│  - Flag contradictions                  │
└─────────────────────────────────────────┘
    ↓ (If validation passes)
┌─────────────────────────────────────────┐
│ Update internal state                   │
│  - Replace agent clauses with corrected │
│  - Update confidence scores             │
│  - Re-run Anomaly Detection on new text │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Re-run Task 4 (Anomaly Detection)       │
│  on corrected clauses                   │
│  - May find NEW anomalies               │
│  - May remove previously flagged ones   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Decision: Do results require new review?│
│  - If new anomalies found → ESCALATE   │
│  - If all clear → COMPLETE             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Store audit trail                       │
│  - Original agent output                │
│  - Human corrections                    │
│  - Re-run results                       │
│  - Timestamps + reviewer ID             │
└─────────────────────────────────────────┘
    ↓
COMPLETE (or back to PENDING_HUMAN_REVIEW)
```

### 4.2 Audit Trail Structure

Every contract stores complete history:

```json
{
  "contract_id": "contract_2024_001",
  "analysis_version": 2,
  "state_history": [
    {
      "timestamp": "2026-04-02T14:15:00Z",
      "state": "ANALYZING",
      "duration_seconds": 12,
      "task_results": {
        "classification": { "type": "NDA", "confidence": 0.78 },
        "extraction": { "clauses_found": 6, "avg_confidence": 0.79 },
        "anomalies": [
          { "type": "unlimited_liability", "confidence": 0.88, "risk": "HIGH" }
        ]
      }
    },
    {
      "timestamp": "2026-04-02T14:15:12Z",
      "state": "PENDING_HUMAN_REVIEW",
      "escalation_triggers": [
        "indemnification_confidence_low",
        "critical_anomaly_detected"
      ],
      "priority": "high"
    },
    {
      "timestamp": "2026-04-02T14:21:44Z",
      "state": "INCORPORATING_FEEDBACK",
      "human_decision": "modify",
      "reviewer_id": "lawyer_001",
      "reviewer_name": "Sarah Chen",
      "modifications": [
        {
          "clause_id": "indemnification_001",
          "agent_text": "Each party indemnifies the other...",
          "human_correction": "Each party indemnifies except for own gross negligence...",
          "reason": "Missed exception clause on line 47"
        }
      ],
      "re_analysis_triggered": true
    },
    {
      "timestamp": "2026-04-02T14:21:49Z",
      "state": "COMPLETE",
      "final_result": {
        "type": "NDA",
        "confidence": 0.78,
        "clauses": 7,
        "anomalies": 2,
        "human_approved": true,
        "modifications_applied": 1
      }
    }
  ],
  "metadata": {
    "submitted_by": "legal_team_api",
    "filename": "NDA_AcmeCorp_2026-04-02.pdf",
    "total_duration_seconds": 45,
    "interactions": 1,
    "final_confidence": "high"
  }
}
```

---

## Part 5: Edge Cases & Error Handling

### 5.1 What if Human Feedback Contradicts Source?

**Scenario**: Human says "This clause doesn't exist" but agent clearly quoted it from page 2.

**Resolution**:
1. System runs evidence validation (Guardrail 4) on human's correction
2. If evidence fails, system flags as "human override without evidence"
3. Accept human feedback anyway (lawyers > AI) but mark as contradiction
4. Store both versions in audit trail
5. Flag for model retraining investigation

**State Transition**: 
```
PENDING_HUMAN_REVIEW 
  → INCORPORATING_FEEDBACK (process modification)
  → FLAG_CONTRADICTION
  → COMPLETE (with warning)
```

### 5.2 What if Human Action Times Out?

**Scenario**: Contract in PENDING_HUMAN_REVIEW for > 1 hour (SLA), no human decision yet.

**Handled by WP-4.6** (Queue & Notification), but state machine response:

```
PENDING_HUMAN_REVIEW (time_in_state > SLA)
  → Issue escalation notification (WP-4.6)
  → Wait another 30 minutes
  → If still no response:
     ├─ Option 1: Auto-complete with agent's analysis
     ├─ Option 2: Escalate to legal team (ESCALATE_LEGAL)
     └─ Option 3: Notify queue manager (WP-4.6)
```

### 5.3 What if Modification Creates Contradiction?

**Scenario**: Human modifies clause in way that creates logical contradiction with another clause.

**Resolution**:
1. During INCORPORATING_FEEDBACK, perform logical validation
2. If contradiction detected, flag it to human
3. Offer two choices:
   - Accept contradiction (mark as "human override")
   - Go back to PENDING_HUMAN_REVIEW to fix
4. If acceptance, store contradiction in metadata

### 5.4 What if Agent Rejects Human Feedback?

**Not applicable.** Humans always win. If human feedback is provided, it overrides agent outputs unconditionally.

---

## Part 6: Integration with Task 7 (Human Review)

From WP-4.2, Task 7 is defined as:

```
Task 7: Human Review & Feedback Loop
├─ Input: Contract + analysis (from Tasks 1-6)
├─ Processing: Human reviewer examines contract + agent's work
├─ Output: Feedback + decision (approve/reject/modify)
├─ Duration: 5-30 minutes per contract
├─ Parallelization: Up to N humans reviewing different contracts simultaneously
├─ Checkpoint: Critical checkpoint for error recovery
```

**HITL Architecture (WP-4.5) specifies:**
- **How Task 7 is triggered**: Escalation conditions (Section 2)
- **What humans see**: Interface specification (Section 3.1-3.2)
- **What humans decide**: Actions available (Section 3.3)
- **How feedback flows**: Re-integration logic (Section 4)

**Queue Management (WP-4.6) specifies:**
- **Who reviews**: Assignment rules
- **When they review**: Prioritization logic
- **SLA & timeout handling**: Escalation on non-response

---

## Part 7: Metrics & Monitoring

### 7.1 HITL Performance Metrics

Track these metrics to understand human review efficiency:

```python
# metrics/hitl_metrics.py

class HITLMetrics:
    
    # Time-based metrics
    avg_time_in_pending = None          # Average time PENDING_HUMAN_REVIEW
    avg_time_in_incorporating = None    # Average time INCORPORATING_FEEDBACK
    sla_breach_rate = None              # % contracts exceeding SLA
    
    # Decision metrics
    approve_rate = None                 # % contracts approved without changes
    reject_rate = None                  # % contracts rejected
    modify_rate = None                  # % contracts modified
    escalate_rate = None                # % escalated to legal
    
    # Quality metrics
    human_catch_rate = None             # % of agent errors caught by human
    false_positive_rate = None          # % of agent's "anomalies" human said were wrong
    false_negative_rate = None          # % of agent's "no anomalies" human found issues
    
    # Feedback quality
    modification_specificity = None     # Average # of clauses modified per feedback
    feedback_verbosity = None           # Average characters in human comments
    
    # Workload metrics
    contracts_per_reviewer = None       # How many contracts each human reviews
    avg_reviewer_utilization = None     # % of time reviewers are active
    concurrent_reviewers_needed = None  # To meet target SLA
```

### 7.2 Dashboards for Monitoring

**For System Operators**:
- Queue depth (# contracts waiting for review)
- Time in queue (median/95th percentile)
- SLA compliance (% meeting target review time)
- Reviewer availability (# online, utilization)

**For Legal Team**:
- Cases reviewed today
- Decision breakdown (approve/reject/modify/escalate)
- Most common feedback patterns
- Confidence calibration (is agent overconfident?)

**For ML Team**:
- What triggers human review most often?
- Which contract types need most review?
- Where is agent hallucinating?
- Feedback patterns for retraining data

---

## Part 8: Configuration & Customization

### 8.1 Escalation Thresholds (Tunable)

```yaml
# config/hitl_config.yaml

escalation:
  confidence_thresholds:
    classification_min: 0.70      # Required confidence for contract type
    extraction_min: 0.65          # Required confidence for clause extraction
    anomaly_min: 0.70             # Required confidence for anomalies
    
  evidence_validation:
    max_failed_pct: 0.10          # If > 10% of evidence fails, escalate
    
  anomaly_triggers:
    critical_threshold: 1         # Any critical = escalate
    high_threshold: 3             # 3+ high-risk = escalate
    medium_threshold: 5           # 5+ medium-risk = escalate (disabled by default)
    
  business_logic:
    require_review_on_unknown_type: true
    require_review_on_out_of_scope: false

sla:
  target_review_time_seconds: 300           # Target: 5 minutes
  max_review_time_seconds: 3600             # Max: 1 hour before escalation
  escalation_warning_seconds: 2700          # Warn after 45 minutes
```

### 8.2 Customizable Interface Elements

```python
# config/ui_customization.py

UI_CONFIG = {
    "show_reasoning_trace": True,           # Show agent's thinking?
    "show_confidence_scores": True,         # Show 0-100 confidence?
    "show_all_considered_types": False,     # Show classification alternatives?
    
    "actions_available": [
        "approve",                          # Always available
        "reject",                           # Always available
        "modify",                           # Always available
        "escalate",                         # Always available
        "skip",                             # Optional
    ],
    
    "default_action": "modify",             # Which button is highlighted?
    
    "max_contracts_per_session": 10,        # Batch size for reviewer
    "auto_advance": True,                   # Auto-load next contract after decision?
}
```

---

## Part 9: Security & Access Control

### 9.1 Access Levels

```
ROLE: Reviewer
  ├─ Can: View contracts in their queue
  ├─ Can: Make decisions (approve/reject/modify/escalate)
  ├─ Can: See reasoning trace + confidence scores
  ├─ Cannot: Modify escalation rules
  ├─ Cannot: See other reviewers' contracts (unless reassigned)
  └─ Audit: All actions logged + timestamped

ROLE: Legal Manager
  ├─ Can: View entire queue + reviewer workload
  ├─ Can: Reassign contracts between reviewers
  ├─ Can: Override decisions if needed (with audit)
  ├─ Can: View escalation statistics
  └─ Cannot: See raw AI model internals

ROLE: System Admin
  ├─ Can: Modify escalation thresholds
  ├─ Can: Configure UI + queue settings
  ├─ Can: Override any decision
  └─ Audit: All changes logged to system log
```

### 9.2 Data Security

- Contract text: Redacted before display (Guardrail 4 — PII Redaction)
- Reviewer feedback: Encrypted at rest
- Audit trail: Immutable (cannot delete historical decisions)
- Session timeout: 15 minutes of inactivity → auto-logout

---

## Success Criteria

✅ **State Machine**
- All 4 states (ANALYZING, PENDING_HUMAN_REVIEW, INCORPORATING_FEEDBACK, COMPLETE) implemented
- Transitions follow defined rules
- No infinite loops

✅ **Escalation Logic**
- At least 5 escalation triggers implemented
- Threshold tuning interface available
- All trigger conditions tested

✅ **Human Interface**
- Shows all required information (clauses, anomalies, confidence, reasoning)
- All 5 actions available (approve/reject/modify/escalate/skip)
- Feedback form captures human's reasoning

✅ **Feedback Integration**
- Modifications processed correctly
- Re-analysis triggered on corrected clauses
- Audit trail captures all versions

✅ **Monitoring**
- HITL metrics dashboard operational
- SLA tracking in place
- Reviewer workload visible to managers

✅ **Testing**
- Unit tests on state machine
- Integration tests on escalation triggers
- User testing with sample reviewers

---

## References

- WP-4.2: Task Decomposition (Task 7 definition)
- WP-4.3: Threat Model (FM-1 through FM-10 context)
- WP-4.4: Guardrail Specification (Guardrails 3, 4, 7, 9 integration)
- WP-4.6: HITL Queue & Notification Design

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-02  
**Author**: Architecture Portfolio  
**Status**: ✅ Approved for Implementation
