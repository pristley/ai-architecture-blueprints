# WP-4.6: Human-in-the-Loop (HITL) Queue & Notification Design

**Work Product Type**: Enterprise System Architecture  
**Phase**: 4 — Capstone: End-to-End Agentic System  
**Date**: 2026-04-02  
**Status**: ✅ Accepted  

---

## Executive Summary

This document specifies the **review queue system** that manages contracts requiring human decision. We define:

1. **Queue Architecture** — Data structure and state management for pending reviews
2. **Prioritization Logic** — How contracts are ordered in the queue
3. **Assignment Strategy** — Which human reviewer gets which contract
4. **Notification System** — How reviewers are alerted to new work
5. **SLA Management** — Timeout handling, escalation, and compliance tracking
6. **Interface Specification** — What queue managers see

**Philosophy**: Reviewers should be *focused and productive*, not overwhelmed. Queue system should surface high-risk contracts first, balance workload fairly, and escalate on SLA breach.

**Scope**: This document defines the **interface** and **business logic**. Implementation details (database choice, message queue type, etc.) are deployment decisions.

---

## Part 1: Queue Architecture

### 1.1 Conceptual Model

```
┌─────────────────────────────────────────────────────────────┐
│ HITL REVIEW QUEUE SYSTEM                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input:  PENDING_HUMAN_REVIEW contracts from Tasks 1-6     │
│            ↓                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ QUEUE MANAGER                                       │   │
│  │  ├─ Queue State (contracts waiting)                 │   │
│  │  ├─ Prioritization Engine                          │   │
│  │  ├─ Assignment Engine                              │   │
│  │  ├─ SLA Tracker                                    │   │
│  │  └─ Notification Handler                           │   │
│  └─────────────────────────────────────────────────────┘   │
│            ↓                                                │
│  Outputs:                                                   │
│  ├─ "Your turn to review: contract_2026_001"             │
│  ├─ "Alert: Contract overdue for review (SLA breach)"    │
│  ├─ "Action: Escalate to legal team"                     │
│  └─ Workload metrics for managers                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Queue Item Data Structure

Every contract awaiting review is represented as a queue item:

```python
# queue/models.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class QueueItemPriority(str, Enum):
    CRITICAL = "critical"    # 0 (highest)
    HIGH = "high"            # 1
    MEDIUM = "medium"        # 2
    LOW = "low"              # 3 (lowest)

class QueueItemStatus(str, Enum):
    PENDING = "pending"            # Waiting to be assigned
    ASSIGNED = "assigned"          # Assigned to reviewer
    IN_REVIEW = "in_review"        # Reviewer actively reviewing
    FEEDBACK_PROVIDED = "feedback" # Reviewer provided feedback
    ESCALATED = "escalated"        # Escalated to legal
    TIMED_OUT = "timed_out"        # SLA expired

@dataclass
class QueueItem:
    """
    A single review task in the queue.
    """
    
    # Identifiers
    queue_id: str                          # Unique queue entry ID
    contract_id: str                       # Link to analysis result
    filename: str                          # Original contract filename
    
    # Metadata from upstream tasks
    contract_type: str                     # NDA, SaaS, License, etc.
    type_confidence: float                 # 0-1
    num_clauses_extracted: int
    num_anomalies_detected: int            # Total anomalies
    num_critical_anomalies: int            # Critical only
    
    # Prioritization factors
    priority: QueueItemPriority
    priority_score: float                  # 0-100 (higher = more urgent)
    escalation_triggers: list[str]         # Why it escalated (see WP-4.5 Section 2)
    
    # Assignments
    assigned_reviewer_id: str = None       # Which human (if assigned)
    assigned_reviewer_name: str = None
    
    # Timing
    created_at: datetime                   # When contract entered queue
    assigned_at: datetime = None           # When assigned to reviewer
    started_review_at: datetime = None     # When reviewer opened it
    sla_target_time: datetime              # When it must be reviewed by
    sla_exceeded_at: datetime = None       # When SLA was first breached
    
    # Status
    status: QueueItemStatus
    
    # Audit trail
    actions: list[dict] = None             # History of state changes
    notes: str = None                      # Manager notes
    
    # Escalation (if triggered)
    escalated_at: datetime = None
    escalation_reason: str = None
```

### 1.3 Queue State Example

```json
{
  "queue_state": {
    "timestamp": "2026-04-02T14:30:00Z",
    "total_items": 47,
    "breakdown": {
      "pending": 12,
      "assigned": 15,
      "in_review": 8,
      "feedback_provided": 10,
      "escalated": 2
    }
  },
  "critical_priority": [
    {
      "queue_id": "q_2026_0001",
      "contract_id": "contract_2026_001",
      "filename": "NDA_AcmeCorp_2026-04-02.pdf",
      "contract_type": "NDA",
      "priority": "critical",
      "priority_score": 95,
      "escalation_triggers": [
        "critical_anomaly_detected",
        "evidence_validation_failed"
      ],
      "created_at": "2026-04-02T14:15:00Z",
      "sla_target_time": "2026-04-02T14:20:00Z",
      "status": "pending",
      "time_in_queue_seconds": 900
    },
    {
      "queue_id": "q_2026_0002",
      "contract_id": "contract_2026_002",
      "filename": "ServiceAgreement_2026-04-02.pdf",
      "contract_type": "SaaS",
      "priority": "critical",
      "priority_score": 88,
      "escalation_triggers": [
        "confidence_overstatement"
      ],
      "assigned_reviewer_id": "lawyer_001",
      "status": "in_review",
      "time_in_queue_seconds": 450
    }
  ],
  "high_priority": [ /* ... */ ],
  "medium_priority": [ /* ... */ ],
  "low_priority": [ /* ... */ ]
}
```

---

## Part 2: Prioritization Logic

### 2.1 Priority Scoring Algorithm

Every queue item receives a **priority score** (0-100) based on multiple factors:

```python
# queue/prioritization.py

class PriorityCalculator:
    """
    Calculate priority score for each queue item.
    """
    
    # Weights for different factors (must sum to 100)
    WEIGHTS = {
        "risk_level": 0.40,              # 40% — Severity of detected issues
        "confidence_uncertainty": 0.20,  # 20% — How uncertain is the agent?
        "time_in_queue": 0.15,           # 15% — How long waiting?
        "contract_type_frequency": 0.10, # 10% — Is this type common?
        "evidence_quality": 0.10,        # 10% — How reliable is evidence?
        "reviewer_expertise": 0.05,      # 5%  — Does expert reviewer exist?
    }
    
    @staticmethod
    def calculate_priority_score(queue_item: QueueItem) -> float:
        """
        Compute priority score (0-100).
        Higher = more urgent.
        """
        
        # Factor 1: Risk Level (40%)
        # If critical anomalies, highest priority
        risk_score = 0.0
        if queue_item.num_critical_anomalies > 0:
            risk_score = 100.0  # Critical = max priority
        elif queue_item.num_anomalies_detected >= 3:
            risk_score = 70.0   # Multiple anomalies = high
        elif queue_item.num_anomalies_detected >= 1:
            risk_score = 50.0   # Single anomaly = moderate
        else:
            risk_score = 20.0   # No anomalies = low
        
        # Factor 2: Confidence Uncertainty (20%)
        # If agent is uncertain, humans should review faster
        uncertainty_score = 0.0
        confidence_uncertainty = 1.0 - queue_item.type_confidence
        uncertainty_score = confidence_uncertainty * 100  # 0-100 scale
        
        # Factor 3: Time in Queue (15%)
        # Older items get higher priority (FIFO fairness)
        time_in_queue = (datetime.now() - queue_item.created_at).total_seconds()
        time_score = min(time_in_queue / 300.0, 1.0) * 100  # Normalize to 5 minutes
        
        # Factor 4: Contract Type Frequency (10%)
        # Rare contract types might need priority (unusual = risky)
        type_frequency = get_type_frequency(queue_item.contract_type)  # 0-1, 1 = common
        type_score = (1.0 - type_frequency) * 100  # Inverse: rare = higher priority
        
        # Factor 5: Evidence Quality (10%)
        # If lots of evidence validation failures, needs priority
        evidence_quality_score = 0.0
        total_clauses = queue_item.num_clauses_extracted
        if total_clauses > 0:
            # Assume 10% of clauses failed evidence validation (from Guardrail 4)
            evidence_quality_score = (1.0 - 0.10) * 100  # 90% passed
        
        # Factor 6: Reviewer Expertise (5%)
        # Boost priority if no expert available (harder to find reviewer)
        expertise_score = 0.0
        available_experts = count_available_experts_for_type(queue_item.contract_type)
        if available_experts == 0:
            expertise_score = 100.0  # No expert available = urgent
        elif available_experts <= 2:
            expertise_score = 50.0   # Few experts = moderate urgency
        else:
            expertise_score = 10.0   # Many experts available = lower priority
        
        # Combine weighted scores
        priority_score = (
            PriorityCalculator.WEIGHTS["risk_level"] * risk_score +
            PriorityCalculator.WEIGHTS["confidence_uncertainty"] * uncertainty_score +
            PriorityCalculator.WEIGHTS["time_in_queue"] * time_score +
            PriorityCalculator.WEIGHTS["contract_type_frequency"] * type_score +
            PriorityCalculator.WEIGHTS["evidence_quality"] * evidence_quality_score +
            PriorityCalculator.WEIGHTS["reviewer_expertise"] * expertise_score
        )
        
        return priority_score
    
    @staticmethod
    def score_to_priority_level(score: float) -> QueueItemPriority:
        """Convert numeric score to priority level."""
        if score >= 80:
            return QueueItemPriority.CRITICAL
        elif score >= 60:
            return QueueItemPriority.HIGH
        elif score >= 40:
            return QueueItemPriority.MEDIUM
        else:
            return QueueItemPriority.LOW
```

### 2.2 Priority Level Examples

| Risk | Confidence | Time in Queue | Priority | Example |
|------|------------|--------------|----------|---------|
| CRITICAL anomaly (unlimited liability) | 88% | 2 min | **CRITICAL** (95) | NDA with dangerous clause |
| MEDIUM anomaly | 65% | 15 min | **HIGH** (72) | SaaS with unclear termination |
| LOW anomaly (auto-renews) | 40% (low confidence) | 45 min | **MEDIUM** (55) | License agreement, agent unsure |
| No anomalies | 92% (high confidence) | 5 min | **LOW** (25) | Standard supply contract |

### 2.3 Dynamic Re-prioritization

Priorities are **recalculated** periodically:

```python
# queue/prioritization.py

def recalculate_queue_priorities(queue: list[QueueItem]) -> list[QueueItem]:
    """
    Re-sort queue based on current state.
    Called every 5 minutes OR when new item enters queue.
    """
    
    # Update priority scores
    for item in queue:
        # Time in queue increases priority
        # (items waiting longer get bumped up)
        item.priority_score = PriorityCalculator.calculate_priority_score(item)
        item.priority = PriorityCalculator.score_to_priority_level(item.priority_score)
    
    # Re-sort by priority
    sorted_queue = sorted(
        queue,
        key=lambda item: (
            -item.priority.value,    # Sort by priority level (descending)
            item.created_at          # Then by creation time (FIFO for same priority)
        )
    )
    
    return sorted_queue
```

---

## Part 3: Assignment Strategy

### 3.1 Reviewer Model

```python
# queue/reviewers.py

@dataclass
class Reviewer:
    """
    A human lawyer/reviewer in the system.
    """
    reviewer_id: str
    name: str
    email: str
    
    # Expertise
    expertise_types: list[str]    # ["NDA", "SaaS", "License"]
    expertise_level: str           # "expert", "intermediate", "novice"
    
    # Workload
    current_assignments: int       # How many contracts assigned to them
    max_concurrent_assignments: int = 5  # Can review up to 5 simultaneously
    
    # Status
    is_online: bool
    is_on_break: bool
    last_action_time: datetime = None
    idle_time_seconds: int = 0
    
    # SLA tracking
    avg_review_time_seconds: float = None
    sla_compliance_rate: float = None  # % of contracts reviewed within SLA
    feedback_quality_rating: float = None  # 1-5 stars from managers
    
    # Availability
    shift_start: datetime = None
    shift_end: datetime = None
    
    def is_available(self) -> bool:
        """Can this reviewer take on more work?"""
        now = datetime.now()
        return (
            self.is_online and
            not self.is_on_break and
            self.current_assignments < self.max_concurrent_assignments and
            now >= self.shift_start and
            now <= self.shift_end
        )
    
    def can_review(self, contract_type: str) -> bool:
        """Can this reviewer handle this contract type?"""
        return contract_type in self.expertise_types
```

### 3.2 Assignment Algorithm

When a new contract enters the queue, assign it to the best available reviewer:

```python
# queue/assignment.py

class AssignmentEngine:
    """
    Decide which reviewer gets assigned to which contract.
    """
    
    @staticmethod
    def assign_contract(
        queue_item: QueueItem,
        available_reviewers: list[Reviewer]
    ) -> Reviewer:
        """
        Select best reviewer for this contract.
        
        Returns:
            Best matching reviewer (or None if no suitable reviewer available)
        """
        
        # Filter 1: Can they review this type?
        capable_reviewers = [
            r for r in available_reviewers
            if r.can_review(queue_item.contract_type)
        ]
        
        if not capable_reviewers:
            return None  # No suitable reviewer available
        
        # Filter 2: Are they available?
        available = [r for r in capable_reviewers if r.is_available()]
        
        if not available:
            return None  # Everyone is busy
        
        # Score each reviewer by fit
        scores = {}
        for reviewer in available:
            score = AssignmentEngine._score_reviewer_fit(queue_item, reviewer)
            scores[reviewer.reviewer_id] = score
        
        # Select highest-scoring reviewer
        best_reviewer_id = max(scores, key=scores.get)
        best_reviewer = next(r for r in available if r.reviewer_id == best_reviewer_id)
        
        return best_reviewer
    
    @staticmethod
    def _score_reviewer_fit(queue_item: QueueItem, reviewer: Reviewer) -> float:
        """
        Score how well this reviewer fits this contract.
        Higher score = better fit.
        """
        score = 0.0
        
        # Factor 1: Expertise match (40%)
        if reviewer.expertise_level == "expert":
            expertise_score = 100.0
        elif reviewer.expertise_level == "intermediate":
            expertise_score = 70.0
        else:  # novice
            expertise_score = 40.0
        score += 0.40 * expertise_score
        
        # Factor 2: Workload balance (30%)
        # Assign to person with fewer concurrent tasks
        utilization = reviewer.current_assignments / reviewer.max_concurrent_assignments
        workload_score = (1.0 - utilization) * 100  # Lower utilization = higher score
        score += 0.30 * workload_score
        
        # Factor 3: SLA compliance history (20%)
        # Assign to person who meets SLAs consistently
        if reviewer.sla_compliance_rate:
            sla_score = reviewer.sla_compliance_rate * 100
        else:
            sla_score = 50.0  # Unknown = neutral
        score += 0.20 * sla_score
        
        # Factor 4: Contract complexity (10%)
        # Assign complex contracts to high-performers
        complexity = queue_item.priority_score / 100.0  # 0-1
        quality_bonus = reviewer.feedback_quality_rating if reviewer.feedback_quality_rating else 3.0
        complexity_score = (complexity * quality_bonus) * 20  # Scale to 0-100
        score += 0.10 * min(complexity_score, 100.0)
        
        return score
```

### 3.3 Assignment Examples

| Contract Type | Reviewer | Expertise | Workload | SLA Rate | Decision |
|---------------|----------|-----------|----------|----------|----------|
| NDA (CRITICAL) | Sarah Chen | Expert | 2/5 | 98% | ✅ Assign |
| NDA (CRITICAL) | John Smith | Intermediate | 5/5 | 85% | ❌ Too busy |
| SaaS (HIGH) | Maria Garcia | Expert | 3/5 | 95% | ✅ Assign |
| License (MEDIUM) | Tom Brown | Novice | 1/5 | 60% | ⚠ Assign with monitoring |

---

## Part 4: SLA Management

### 4.1 SLA Definition

```python
# queue/sla.py

class SLAConfig:
    """
    Service Level Agreement for review tasks.
    """
    
    # Time limits (in seconds)
    TARGET_REVIEW_TIME = 300           # Ideal: 5 minutes
    MAX_REVIEW_TIME = 3600             # Absolute max: 1 hour
    ESCALATION_WARNING_TIME = 2700     # Warn at 45 minutes
    
    # Priority-specific SLAs
    SLA_BY_PRIORITY = {
        "critical": 300,   # 5 minutes
        "high": 600,       # 10 minutes
        "medium": 1200,    # 20 minutes
        "low": 3600,       # 1 hour
    }
```

### 4.2 SLA Tracking

Track when each contract was:
1. **Created** (entered queue)
2. **Assigned** (assigned to reviewer)
3. **Started** (reviewer opened it)
4. **Completed** (reviewer submitted feedback)

```python
# queue/sla.py

class SLATracker:
    """
    Monitor SLA compliance for each queue item.
    """
    
    @staticmethod
    def get_sla_status(item: QueueItem) -> dict:
        """Get current SLA status for a queue item."""
        now = datetime.now()
        time_in_queue = (now - item.created_at).total_seconds()
        
        sla_target = SLAConfig.SLA_BY_PRIORITY[item.priority.value]
        time_until_sla = sla_target - time_in_queue
        
        return {
            "time_in_queue": time_in_queue,
            "sla_target": sla_target,
            "time_until_sla": time_until_sla,
            "sla_breached": time_until_sla < 0,
            "sla_percent_used": time_in_queue / sla_target,
            "status": (
                "🟢 OK" if time_until_sla > 300 else
                "🟡 WARNING" if time_until_sla > 0 else
                "🔴 BREACHED"
            )
        }
    
    @staticmethod
    def handle_sla_breach(item: QueueItem):
        """
        Called when SLA is first breached.
        """
        item.sla_exceeded_at = datetime.now()
        
        # Action 1: Notify reviewer
        send_urgent_notification(
            item.assigned_reviewer_id,
            f"⚠️ SLA BREACHED: Contract {item.contract_id} "
            f"overdue for {(datetime.now() - item.sla_target_time).total_seconds():.0f} seconds"
        )
        
        # Action 2: Escalate if still not completed after 30 min
        if (datetime.now() - item.sla_exceeded_at).total_seconds() > 1800:
            escalate_to_legal_team(item)
```

### 4.3 Auto-Escalation on SLA Breach

If no human response within SLA + grace period:

```python
# queue/sla.py

def handle_sla_timeout(item: QueueItem):
    """
    Handle contract when SLA is exceeded and not completed.
    Called by background job every 5 minutes.
    """
    
    time_since_breach = (datetime.now() - item.sla_exceeded_at).total_seconds()
    grace_period = 600  # 10 minute grace period after SLA breach
    
    if time_since_breach > grace_period:
        
        # Option 1: Auto-complete with agent's analysis
        if item.priority == QueueItemPriority.LOW:
            # Low priority = auto-approve agent's work
            complete_with_agent_output(item)
        
        # Option 2: Escalate to legal team (urgent contracts)
        elif item.priority in [QueueItemPriority.CRITICAL, QueueItemPriority.HIGH]:
            escalate_to_legal_team(
                item,
                reason="SLA timeout: automatic escalation"
            )
        
        # Option 3: Reassign to different reviewer
        else:  # MEDIUM priority
            new_reviewer = find_alternative_reviewer(item)
            if new_reviewer:
                reassign_to_reviewer(item, new_reviewer)
            else:
                escalate_to_legal_team(item)
```

---

## Part 5: Notification System

### 5.1 Notification Types

```python
# queue/notifications.py

class NotificationType(str, Enum):
    """Types of notifications sent to reviewers."""
    
    # Assignment notifications
    NEW_ASSIGNMENT = "new_assignment"           # "You have a new contract to review"
    REASSIGNMENT = "reassignment"               # "Contract reassigned to you"
    
    # Urgency notifications
    SLA_WARNING = "sla_warning"                 # "This contract needs review soon"
    SLA_BREACHED = "sla_breached"              # "URGENT: Contract overdue for review"
    
    # Action notifications
    FEEDBACK_RECEIVED = "feedback_received"     # "Your feedback was processed"
    ESCALATION_APPROVED = "escalation_approved" # "You escalated to legal; confirmed"
    
    # Status notifications
    QUEUE_CLEARED = "queue_cleared"            # "Your queue is now empty"
    END_OF_SHIFT = "end_of_shift"              # "Your shift ends in 15 minutes"
```

### 5.2 Notification Channels

Notifications sent via multiple channels (email, Slack, in-app):

```python
# queue/notifications.py

class NotificationChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    IN_APP = "in_app"

@dataclass
class Notification:
    """A notification to send to a reviewer."""
    
    notification_id: str
    reviewer_id: str
    notification_type: NotificationType
    title: str
    message: str
    priority: str  # "urgent", "normal", "low"
    contract_id: str = None  # Link to contract if applicable
    
    # Delivery
    channels: list[NotificationChannel]
    created_at: datetime = datetime.now()
    sent_at: datetime = None
    read_at: datetime = None
    
    # Action (if user needs to click something)
    action_url: str = None  # e.g., "/review/contract_2026_001"
    
    # Retry logic
    retry_count: int = 0
    max_retries: int = 3
    last_retry_at: datetime = None
```

### 5.3 Notification Delivery Logic

```python
# queue/notifications.py

class NotificationManager:
    """
    Manage notification delivery to reviewers.
    """
    
    @staticmethod
    def send_assignment_notification(item: QueueItem, reviewer: Reviewer):
        """Notify reviewer they have a new contract to review."""
        
        notification = Notification(
            notification_id=f"n_{uuid.uuid4()}",
            reviewer_id=reviewer.reviewer_id,
            notification_type=NotificationType.NEW_ASSIGNMENT,
            title=f"New Review: {item.filename}",
            message=(
                f"You have a new contract to review: {item.filename}\n"
                f"Type: {item.contract_type}\n"
                f"Anomalies: {item.num_anomalies_detected}\n"
                f"Priority: {item.priority.value.upper()}"
            ),
            priority="urgent" if item.priority == QueueItemPriority.CRITICAL else "normal",
            contract_id=item.contract_id,
            channels=[
                NotificationChannel.IN_APP,
                NotificationChannel.EMAIL
            ],
            action_url=f"/review/{item.contract_id}"
        )
        
        NotificationManager._dispatch(notification)
    
    @staticmethod
    def send_sla_warning(item: QueueItem):
        """Notify reviewer SLA is approaching."""
        
        time_remaining = (item.sla_target_time - datetime.now()).total_seconds()
        
        notification = Notification(
            notification_id=f"n_{uuid.uuid4()}",
            reviewer_id=item.assigned_reviewer_id,
            notification_type=NotificationType.SLA_WARNING,
            title="⏰ SLA Warning",
            message=(
                f"Contract {item.filename} is due for review in "
                f"{time_remaining // 60:.0f} minutes.\n"
                f"Please complete your review to meet SLA."
            ),
            priority="urgent",
            contract_id=item.contract_id,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            action_url=f"/review/{item.contract_id}"
        )
        
        NotificationManager._dispatch(notification)
    
    @staticmethod
    def _dispatch(notification: Notification):
        """Send notification via all configured channels."""
        for channel in notification.channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    send_email(notification)
                elif channel == NotificationChannel.SLACK:
                    send_slack_message(notification)
                elif channel == NotificationChannel.SMS:
                    send_sms(notification)
                elif channel == NotificationChannel.IN_APP:
                    store_in_app_notification(notification)
                
                notification.sent_at = datetime.now()
            
            except Exception as e:
                # Retry on failure
                notification.retry_count += 1
                if notification.retry_count < notification.max_retries:
                    # Retry in 5 minutes
                    schedule_retry(notification, delay_seconds=300)
```

### 5.4 Notification Examples

```
🔴 NEW ASSIGNMENT (CRITICAL)
From: HITL Queue System
To: sarah.chen@company.com

Subject: URGENT: New Contract for Review — NDA_AcmeCorp_2026-04-02.pdf

Body:
You have a critical contract to review:
  - File: NDA_AcmeCorp_2026-04-02.pdf
  - Type: NDA
  - Risk: Unlimited Liability clause detected (HIGH)
  - Agent Confidence: 88%
  - SLA: Review within 5 minutes

[REVIEW NOW] button → /review/contract_2026_001

---

🟡 SLA WARNING
From: HITL Queue System
To: john.smith@company.com

Subject: ⏰ Contract Overdue for Review (4 min remaining)

Body:
Contract ServiceAgreement_2026-04-02.pdf is due for review in 4 minutes.
Please complete your feedback to meet the SLA.

[REVIEW NOW] button → /review/contract_2026_002
```

---

## Part 6: Queue Dashboard & Manager Interface

### 6.1 Queue Manager View

```
╔════════════════════════════════════════════════════════════════════════════╗
║ QUEUE MANAGER DASHBOARD                                                   ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║ QUEUE STATUS (as of 2026-04-02 14:30:00 UTC)                             ║
│                                                                            ║
│ ┌─ PENDING (12)     ┌─ IN REVIEW (8)    ┌─ ESCALATED (2)                ║
│ │  🔴 CRITICAL (4)  │  Sarah Chen (2)   │  NDA_AcmeCorp   04:15 PM      ║
│ │  🟠 HIGH (5)      │  John Smith (3)   │  SaaS_BigCo     03:52 PM      ║
│ │  🟡 MEDIUM (2)    │  Maria Garcia (2) └────────────────────            ║
│ │  🟢 LOW (1)       │  Tom Brown (1)                                      ║
│ └───────────────────└────────────────────                                 ║
│                                                                            ║
│ AVG TIME IN QUEUE: 12 min 30 sec  |  SLA COMPLIANCE: 94%  |  BACKLOG: OK  ║
║                                                                            ║
├────────────────────────────────────────────────────────────────────────────┤
║ CRITICAL PRIORITY QUEUE (Top 5)                                          ║
├────┬──────────────────┬──────────┬──────────┬──────────┬─────────────────┤
║ # │ Contract         │ Type │ Assigned │ In Queue │ SLA Status     ║
├────┼──────────────────┼──────────┼──────────┼──────────┼─────────────────┤
║ 1  │ NDA_AcmeCorp     │ NDA  │ Unassigned│ 8m 30s   │ 🔴 BREACHED    ║
║    │ contract_2024_001│      │ (⚠ Urgent)│          │ SLA: 5 min ago ║
║    │                  │      │           │          │ [ASSIGN NOW]   ║
├────┼──────────────────┼──────────┼──────────┼──────────┼─────────────────┤
║ 2  │ ServiceAgreement │ SaaS │ John Smith│ 6m 15s   │ 🟡 WARNING    ║
║    │ contract_2024_002│      │ (Started 3│          │ SLA: 4 min left║
║    │                  │      │  min ago) │          │ [NUDGE]        ║
├────┼──────────────────┼──────────┼──────────┼──────────┼─────────────────┤
║ 3  │ License_Softw   │ Lic  │ Sarah Chen│ 4m 45s   │ 🟢 OK         ║
║    │ contract_2024_003│      │ (Assigned)│          │ SLA: 15 min   ║
║    │                  │      │           │          │ [WATCH]        ║
└────┴──────────────────┴──────────┴──────────┴──────────┴─────────────────┘
║                                                                            ║
├────────────────────────────────────────────────────────────────────────────┤
║ REVIEWER WORKLOAD & PERFORMANCE                                          ║
├───────────┬──────────┬──────────┬──────────┬──────────┬──────────────────┤
║ Reviewer  │ Assigned │ Capacity │ Avg Time │ SLA Rate │ Quality Rating  ║
├───────────┼──────────┼──────────┼──────────┼──────────┼──────────────────┤
║ Sarah     │ 2/5      │ 60%      │ 8 min    │ 98%      │ ⭐⭐⭐⭐⭐ (4.9)   ║
║ John      │ 3/5      │ 60%      │ 9 min    │ 92%      │ ⭐⭐⭐⭐ (4.1)    ║
║ Maria     │ 2/5      │ 40%      │ 7 min    │ 95%      │ ⭐⭐⭐⭐⭐ (4.8)   ║
║ Tom       │ 1/5      │ 20%      │ 12 min   │ 85%      │ ⭐⭐⭐ (3.5)     ║
╚═══════════╧══════════╧══════════╧══════════╧══════════╧══════════════════╝

ACTIONS AVAILABLE
├─ [ASSIGN NOW] — Manually assign contract to available reviewer
├─ [REASSIGN] — Move contract to different reviewer
├─ [ESCALATE] — Move to legal team (high priority)
├─ [SKIP] — Remove from queue (out of scope)
├─ [PAUSE QUEUE] — Temporarily stop new assignments
└─ [ALERTS] — Configure SLA thresholds & escalation
```

### 6.2 Manager Actions

```python
# queue/manager_actions.py

class QueueManager:
    """
    Operations for queue managers.
    """
    
    @staticmethod
    def manually_assign_contract(item_id: str, reviewer_id: str) -> bool:
        """
        Manager manually assigns a contract to a specific reviewer.
        Override for assignment algorithm.
        """
        item = get_queue_item(item_id)
        reviewer = get_reviewer(reviewer_id)
        
        if not reviewer.is_available():
            raise ValueError(f"Reviewer {reviewer_id} is not available")
        
        item.assigned_reviewer_id = reviewer.reviewer_id
        item.assigned_reviewer_name = reviewer.name
        item.assigned_at = datetime.now()
        item.status = QueueItemStatus.ASSIGNED
        
        # Notify reviewer
        NotificationManager.send_assignment_notification(item, reviewer)
        
        return True
    
    @staticmethod
    def reassign_contract(item_id: str, new_reviewer_id: str) -> bool:
        """Reassign a contract to a different reviewer."""
        item = get_queue_item(item_id)
        new_reviewer = get_reviewer(new_reviewer_id)
        
        old_reviewer_id = item.assigned_reviewer_id
        item.assigned_reviewer_id = new_reviewer_id
        
        # Log action
        log_action(item, f"Reassigned from {old_reviewer_id} to {new_reviewer_id}")
        
        # Notify both
        send_notification(old_reviewer_id, f"Contract reassigned from you")
        NotificationManager.send_assignment_notification(item, new_reviewer)
        
        return True
    
    @staticmethod
    def escalate_contract(item_id: str, reason: str) -> bool:
        """Escalate contract to legal team."""
        item = get_queue_item(item_id)
        item.status = QueueItemStatus.ESCALATED
        item.escalated_at = datetime.now()
        item.escalation_reason = reason
        
        # Notify legal team
        notify_legal_team(item, reason)
        
        return True
```

---

## Part 7: Integration with HITL State Machine (WP-4.5)

The queue system feeds into the HITL state machine:

```
TASKS 1-6 (Automated)
       ↓
       Escalation Triggers Fired? 
       ├─ NO → COMPLETE (no queue entry)
       └─ YES → Enter Queue
               ↓
    QUEUE SYSTEM (WP-4.6)
       ├─ Prioritization
       ├─ Assignment
       ├─ Notification
       └─ SLA Tracking
               ↓
    PENDING_HUMAN_REVIEW (WP-4.5 state)
       ├─ Reviewer receives notification
       ├─ Reviewer opens interface
       └─ Reviewer makes decision
               ↓
    INCORPORATING_FEEDBACK (WP-4.5)
       └─ Process decision, update contract
               ↓
    COMPLETE or ESCALATE_LEGAL
```

---

## Part 8: Configuration

### 8.1 Queue Configuration

```yaml
# config/queue_config.yaml

queue:
  max_queue_size: 1000            # Hard limit on queue size
  recalculation_interval: 300     # Recalculate priorities every 5 min
  
prioritization:
  weights:
    risk_level: 0.40
    confidence_uncertainty: 0.20
    time_in_queue: 0.15
    contract_type_frequency: 0.10
    evidence_quality: 0.10
    reviewer_expertise: 0.05
  
assignment:
  strategy: "best_fit"            # Options: best_fit, round_robin, least_loaded
  prefer_expert: true             # Prefer expert over least-loaded?
  consider_specialty_affinity: true
  
sla:
  critical: 300                   # 5 minutes
  high: 600                       # 10 minutes
  medium: 1200                    # 20 minutes
  low: 3600                       # 1 hour
  
  grace_period_after_breach: 600  # 10 minute grace before escalation
  warning_threshold: 0.75         # Warn at 75% of SLA
  
notifications:
  enabled: true
  channels:
    - email
    - slack
    - in_app
  
  sla_warning_enabled: true
  sla_breached_enabled: true
```

---

## Part 9: Success Criteria

✅ **Queue Architecture**
- Queue item data structure defined
- Supports 1000+ concurrent items
- State transitions clear

✅ **Prioritization**
- Priority scoring algorithm implemented
- Weights configurable
- Examples tested

✅ **Assignment**
- Assignment engine selects best reviewer
- Considers expertise, workload, SLA compliance
- Falls back gracefully when no reviewer available

✅ **SLA Management**
- SLA tracked per contract
- Warnings issued at 75% of SLA
- Auto-escalation on timeout + grace period

✅ **Notifications**
- Multiple channels (email, Slack, SMS, in-app)
- Retry logic on failure
- Notification types well-defined

✅ **Manager Dashboard**
- Real-time queue status
- Manual assignment/reassignment available
- Reviewer workload visible
- Escalation controls available

✅ **Integration**
- Feeds into HITL state machine (WP-4.5)
- Receives escalations from Tasks 1-6
- Outputs assignments to reviewers

---

## References

- WP-4.5: HITL Checkpoint Architecture (state machine definition)
- WP-4.2: Task Decomposition (Task 7 context)
- WP-4.3: Threat Model (FM-1 through FM-10 context)
- WP-4.4: Guardrail Specification (escalation triggers)

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-02  
**Author**: Architecture Portfolio  
**Status**: ✅ Approved for Implementation
