# ADR-3.9: State Management Strategies for Multi-Agent Systems

**Status:** Accepted  
**Date:** 2026-06-30  
**Context:** Multi-agent RAG systems (WP-3.8) require coordination mechanisms for shared state. How do we handle concurrent updates from multiple agents?

---

## 1. Executive Summary

When multiple agents work concurrently (e.g., ContentCreator + QA + Editor + Fact-Check agents in WP-3.8), they must coordinate around shared state (document artifacts, feedback, scores). This ADR compares two fundamental approaches:

| Dimension | Shared Global State | Event Bus (Pub/Sub) |
|-----------|-------------------|-------------------|
| **Concurrency Model** | Pessimistic locking or optimistic locks | Event sourcing, eventual consistency |
| **Conflict Resolution** | Explicit (acquire lock) | Implicit (canonical event log) |
| **Complexity** | Low setup, high debugging | High setup, low debugging |
| **Consistency Guarantee** | Strong (atomic) | Eventual (causally ordered) |
| **Scalability** | <10 agents (lock contention) | <1000 agents (distributed) |
| **Debugging** | Hard (hidden race conditions) | Easy (replay events) |
| **Failure Recovery** | Lost writes unless persisted | Complete audit trail |

**Recommendation:**
- **Development/Small Scale:** Shared global state with explicit locks (WP-3.8 InMemoryStateBus)
- **Production/Scale:** Event bus with event sourcing (transitioned from WP-3.8)
- **Hybrid (Recommended):** Event bus with local cache + consensus for conflict resolution

---

## 2. Context: The Multi-Agent Coordination Problem

### Scenario: Content Creator & QA System (WP-3.8)

```
Task: Create and review a blog post

Timeline:
  t=0s    Supervisor creates TaskState
  t=0.1s  ContentCreator starts writing
  t=5s    ContentCreator finishes → writes artifact
  t=5.1s  QA Agent reads artifact → starts review
  t=5.2s  Editor Agent reads artifact → starts editing suggestions
  t=5.3s  Fact-Check Agent reads artifact → starts verification
  
  PROBLEM: What if ContentCreator finishes AND QA starts review AT THE SAME TIME?
  - Which version does QA read?
  - What if ContentCreator is still writing?
```

### Concurrent Update Scenario: The Race Condition

```
Time    ContentCreator              Editor                  State
---     ---------------             ------                  -----
t=0     Read artifact (v1)          -                       artifact: v1
t=1     "Add section..."            Read artifact (v1)      artifact: v1
t=2     Write v2 (section added)     -                       artifact: v2
t=3     -                            "Fix grammar..."       artifact: v2
t=4     -                            Write v2' (grammar)     artifact: v2' (CONFLICT!)
t=5     Read artifact (???)         -                       ???

QUESTION: Does t=5 read v2 or v2'? And what happens to ContentCreator's section?
```

---

## 3. Approach 1: Shared Global State (Dictionary-Based)

### Architecture

```
┌─────────────────────────────────────────┐
│  Shared Global State (Dictionary)       │
│  ├─ artifact: "blog post v2"            │
│  ├─ qa_feedback: {...}                  │
│  ├─ editor_suggestions: {...}           │
│  └─ fact_check_results: {...}           │
└──────────┬──────────────────────────────┘
           ↑
    ┌──────┴──────┐
    │ Lock Manager│ (Serializes access)
    └──────┬──────┘
           ↓
    ┌──────────────────────────────────┐
    │ Agent Processes                  │
    ├─ ContentCreator (locked 0-5s)    │
    ├─ QA (locked 5-7s)                │
    ├─ Editor (locked 7-8s)            │
    └─ Fact-Check (locked 8-9s)        │
    └──────────────────────────────────┘
```

### Implementation: Lock-Based Coordination

```python
class SharedGlobalState:
    def __init__(self):
        self.data = {}
        self.locks = {}  # Per-key locks
        self.versions = {}  # Track versions
    
    def write_with_lock(self, task_id, key, value, expected_version=None):
        """Optimistic lock: write only if version matches."""
        with self.locks[key]:
            current_version = self.versions[key]
            
            if expected_version is not None and current_version != expected_version:
                raise ConflictError(f"Version mismatch: expected {expected_version}, got {current_version}")
            
            self.data[key] = value
            self.versions[key] += 1
            return self.versions[key]
```

### Strengths ✅

1. **Simple to understand:** Direct variable assignment
2. **Immediate consistency:** Write is immediately visible
3. **Low latency:** No event bus overhead
4. **Easy debugging:** Print the dict and you see state

### Weaknesses ❌

1. **Lock contention:** With N agents, up to N-1 agents wait
2. **Deadlocks:** Possible if agents acquire locks in different order
3. **Lost updates:** If version check fails, agent must retry
4. **No audit trail:** Once overwritten, old values gone
5. **Poor scalability:** Performance degrades with >10 agents
6. **Retry complexity:** Exponential backoff needed for conflicts

### Conflict Resolution Strategy

**Optimistic Locking:**
```
Write(key, value, expected_version):
  if current_version[key] != expected_version:
    raise ConflictError
  else:
    current_version[key] += 1
    return SUCCESS
```

**Problems:**
- Agent must know expected version (requires careful sequencing)
- Conflict forces full retry (no partial merges)
- Performance collapses under high contention

---

## 4. Approach 2: Event Bus (Pub/Sub with Event Sourcing)

### Architecture

```
┌──────────────────────────────────────────────────┐
│  Event Log (Canonical Source of Truth)           │
│  [t=0:   InitTask event]                         │
│  [t=0.1: ContentStarted event]                   │
│  [t=5.0: ArtifactWritten event (v1)]             │
│  [t=5.1: QAStarted event]                        │
│  [t=5.2: EditorStarted event]                    │
│  [t=6.0: FeedbackWritten event]                  │
│  └─ Immutable, replay-able                       │
└─────────────┬──────────────────────────────────┘
              │
    ┌─────────┴─────────┐
    │  Event Bus         │ (Publish all events)
    │  (Redis Pub/Sub)   │
    └─────────┬─────────┘
              │
    ┌─────────┴────────────────────────────┐
    │ Subscribers (Agents)                 │
    ├─ ContentCreator (subscribe)          │
    ├─ QA (subscribe)                      │
    ├─ Editor (subscribe)                  │
    ├─ Fact-Check (subscribe)              │
    └─ StateManager (materialized view)    │
    └──────────────────────────────────────┘

Local Cache (Eventually Consistent View):
  artifact: "blog post v2"          [computed from event log]
  qa_feedback: {...}                [computed from event log]
  editor_suggestions: {...}         [computed from event log]
  fact_check_results: {...}         [computed from event log]
```

### Implementation: Event Sourcing

```python
@dataclass
class Event:
    event_id: str
    timestamp: str
    task_id: str
    agent_id: str
    event_type: str  # "artifact_written", "feedback_added", etc.
    data: Dict[str, Any]
    causality_token: str  # Links to prior event for ordering

class EventBus:
    def __init__(self):
        self.event_log = []  # Immutable append-only log
        self.subscribers = {}
    
    def publish_event(self, event: Event):
        """Append event to log (never overwrite)."""
        # Validate causality
        if event.causality_token:
            if event.causality_token not in self.event_log:
                raise CausalityViolation("Causality token not in log")
        
        self.event_log.append(event)
        self._notify_subscribers(event)
        return event.event_id
    
    def compute_state_at(self, task_id: str, timestamp: str) -> Dict:
        """Reconstruct state at any point in time."""
        events = [e for e in self.event_log 
                  if e.task_id == task_id and e.timestamp <= timestamp]
        
        state = {}
        for event in events:
            # Materialize state by replaying all events in order
            state = self._apply_event(state, event)
        
        return state
```

### Strengths ✅

1. **No lock contention:** Events published without blocking
2. **Complete audit trail:** Replay to any point in time
3. **Debugging:** "Why did this happen?" → read event log
4. **Scalability:** 1000s of agents, no performance degradation
5. **Failure recovery:** Crash? Replay events, recover exact state
6. **Causal ordering:** Explicit causality_token prevents out-of-order updates
7. **Conflict resolution:** Canonical event order determines winner

### Weaknesses ❌

1. **Complexity:** Must implement event replay logic
2. **Eventual consistency:** Local cache lags behind event log (milliseconds)
3. **Storage overhead:** Every update = new event (not just final value)
4. **Garbage collection:** Must prune old events eventually
5. **Snapshot coordination:** Large state requires periodic snapshots
6. **Debugging is verbose:** Event logs can be hundreds of lines

### Conflict Resolution Strategy

**Last-Writer-Wins (LWW) with Timestamps:**
```
Scenario: ContentCreator and Editor both write at t=5.2

Event 1: t=5.2, ContentCreator writes artifact v2
Event 2: t=5.2, Editor writes artifact v2'

Resolution: Compare timestamps
  - If Event2.timestamp > Event1.timestamp: use v2'
  - If Event1.timestamp > Event2.timestamp: use v2
  - If equal: use agent_id as tiebreaker (alphabetical)
```

**Causal Consistency (Better):**
```
Event 1: ArtifactWritten (causality_token=null)
Event 2: FeedbackAdded (causality_token=Event1.event_id)
Event 3: EditorSuggestions (causality_token=Event1.event_id)

Resolution: Events 2 and 3 both causally follow Event 1, so order among them is arbitrary
  - Apply Event 1 first (canonical)
  - Then apply Events 2 and 3 in timestamp order
  - Result: deterministic, replay-able
```

**Operational Transform (Advanced):**
```
When two agents edit same section concurrently:
  
  Event 1: ContentCreator.Insert(position=100, text="Section A")
  Event 2: Editor.Insert(position=100, text="Grammar fix")
  
Transform: Adjust positions based on prior edits
  - Event 1: Insert at 100
  - Event 2: Insert at (100 + len("Section A")) = 109
  
Result: Both changes preserved, correct order
```

---

## 5. Detailed Comparison: State Management Approaches

### 5.1 Consistency Models

| Model | Guarantee | Recovery | Complexity |
|-------|-----------|----------|-----------|
| **Strong (Locks)** | Atomic updates | Lost if not persisted | Low |
| **Eventual (Event Bus)** | All replicas converge | Complete audit trail | High |
| **Causal (Event Bus + Tokens)** | Ordered by causality | Full replay | Very High |

### 5.2 Conflict Resolution Algorithms

#### Last-Write-Wins (LWW)

**Algorithm:**
```
conflicted_updates = [update1, update2, ...]
winner = max(conflicted_updates, key=lambda u: u.timestamp)
apply(winner)
```

**Pros:** Simple, deterministic  
**Cons:** Lossy (discards loser), unfair to slower agents

**When to use:** Metadata (timestamps, scores), non-critical fields

#### Operational Transform (OT)

**Algorithm:**
```
def transform(op1, op2):
    """Adjust op2 based on op1's side effects."""
    if op1.position < op2.position:
        # op1 inserted/deleted before op2
        op2.position += len(op1.data)
    return op2

# Concurrent edits
op1 = Insert(position=100, text="A")
op2 = Insert(position=100, text="B")

op1_xf = transform(op1, op1)  # No-op
op2_xf = transform(op1, op2)  # Adjust position
result = op1_xf + op2_xf
```

**Pros:** Preserves both edits, intentional  
**Cons:** Complex to implement, must handle all operation types

**When to use:** Document editing (collaborative), code generation

#### Conflict-Free Replicated Data Type (CRDT)

**Algorithm:**
```
# Each agent assigns globally unique IDs to operations
op1 = OpID(agent=ContentCreator, counter=1)
op2 = OpID(agent=Editor, counter=1)

# Order by: (timestamp, agent_id)
order = sorted([op1, op2])  # Deterministic

# Apply in order: both updates preserved
for op in order:
    apply(op)
```

**Pros:** Automatic conflict resolution, provably consistent  
**Cons:** Requires unique IDs, overhead per operation

**When to use:** Distributed systems (no central arbiter), real-time collab

### 5.3 Performance Characteristics

**Under Concurrent Load (100 agents, 1000 updates/second):**

| Metric | Shared Global State | Event Bus (LWW) | Event Bus (Causal) |
|--------|-------------------|-----------------|-------------------|
| **Write Latency (P50)** | 0.1ms | 1ms | 2ms |
| **Write Latency (P99)** | 50ms (lock wait) | 5ms | 10ms |
| **Throughput (ops/sec)** | 100K (single-threaded) | 1M (no locks) | 500K |
| **Memory (event log)** | 1GB (state only) | 10GB (all events) | 10GB |
| **Read Consistency** | Strong (0ms lag) | Eventual (5-50ms lag) | Causal (5-50ms lag) |
| **Recovery Time** | None (live) | 100ms (replay 10K events) | 500ms |

---

## 6. Conflict Scenarios in WP-3.8: Real-World Examples

### Scenario 1: Concurrent Section Edits

```
Task: Editing a blog post (12 sections, 2000 words)

Agents working in parallel:
  - ContentCreator: Writing initial draft (all sections)
  - Editor: Proofreading Section 1-4
  - QA: Reviewing technical accuracy Section 5-8
  - Fact-Check: Verifying claims Section 9-12

Conflict:
  t=5.2s: ContentCreator finishes Section 3, writes to state
  t=5.2s: Editor finishes Section 3 proofreading, writes feedback
  
  Question: Which value is correct?
  Answer (Shared State): Lock-based → One waits, then other proceeds
  Answer (Event Bus): Both events logged → compute merged view
```

**Shared Global State Resolution:**
```python
# ContentCreator holds lock from t=5.0 to t=5.2
artifact_lock.acquire()
artifact = artifact + "Section 3 content"
artifact_lock.release()

# Editor tries at t=5.2, but lock just released
editor_lock.acquire()
qa_feedback["Section 3"] = "Grammar issue on line 42"
editor_lock.release()

# Result: Sequential, no conflict
```

**Event Bus Resolution:**
```python
# t=5.2: ContentCreator publishes ArtifactWritten event
event_log.append(Event(
    event_type="artifact_written",
    agent_id="ContentCreator",
    timestamp="t=5.2",
    data={"section": 3, "text": "Section 3 content"}
))

# t=5.2: Editor publishes FeedbackAdded event
event_log.append(Event(
    event_type="feedback_added",
    agent_id="Editor",
    timestamp="t=5.2",
    data={"section": 3, "feedback": "Grammar issue..."}
))

# Compute state: Both events are ordered by (timestamp, agent_id)
# Result: artifact[3] = "Section 3 content", feedback[3] = "Grammar..."
```

---

### Scenario 2: Supervisory Override During Execution

```
Scenario: QA Agent identifies critical issue mid-evaluation

Timeline:
  t=0s    Supervisor launches QA Agent
  t=3.5s  QA Agent: "Found major accuracy issue"
  t=3.5s  Supervisor: "Stop! Revert to ContentCreator for revision"
  
  Question: How do we rollback the evaluation?
```

**Shared Global State (Simple):**
```python
# Supervisor has reference to state dict
state = {
    "artifact": "blog post",
    "qa_feedback": {...}  # Partially written
}

# Supervisor wants to rollback
state = checkpoint_backup  # Restore from saved checkpoint
# Pro: Simple
# Con: Lost all QA progress if we revert too far
```

**Event Bus (Event Sourcing):**
```python
# Compute state at t=3.4s (before QA found issue)
state_before = compute_state_at(task_id, "t=3.4s")

# Apply events up to that point
state_rolled_back = replay_events_until(task_id, "t=3.4s")

# Continue from there (QA can retry)
# Pro: Granular control, can pause/resume
# Con: Must implement checkpoint/resume logic
```

---

### Scenario 3: Duplicate Agent Execution (Fault Tolerance)

```
Scenario: Network partition causes QA Agent to execute twice

Timeline:
  t=5s    QA Agent: "Starting review"
  t=6s    QA Agent: "Submitting feedback"
  t=7s    (Network partition - submission lost)
  t=8s    QA Agent retries: "Submitting feedback" (again)
  
  Question: Do we have duplicate feedback or merged?
```

**Shared Global State (Problematic):**
```python
# First submission
state["qa_feedback"] = feedback_v1

# Network partition, retried
state["qa_feedback"] = feedback_v1  # DUPLICATE!

# Con: No deduplication, must handle manually
```

**Event Bus (Automatic Deduplication):**
```python
# First submission
event_log.append(Event(
    event_id="qa-feedback-001",
    data=feedback_v1
))

# Retry
event_log.append(Event(
    event_id="qa-feedback-001",  # Same ID (idempotent)
    data=feedback_v1
))

# Event bus recognizes duplicate by event_id
# Applies only once to materialized view
# Pro: Automatic deduplication
```

---

## 7. Conflict Resolution Decision Tree

```
Start: Agent A and Agent B both write to same key at ~same time

├─ Are they writing the SAME value?
│  ├─ YES: No conflict (idempotent), apply once
│  └─ NO: Conflict detected
│
├─ Is a merge possible?
│  ├─ YES (e.g., two different sections): Merge (OT/CRDT)
│  ├─ NO (e.g., two versions of same section)
│  │  ├─ Is one clearly stale? (version number)
│  │  │  ├─ YES: Use fresher (LWW)
│  │  │  └─ NO: Can't decide automatically
│  │  │     ├─ User manual resolution (stall)
│  │  │     ├─ Automatic (pick by agent_id)
│  │  │     └─ Supervisor review (retry loop)
```

---

## 8. Decision: Shared State vs Event Bus

### 8.1 When to Use Shared Global State

**Criteria:**
- ✅ <10 agents
- ✅ Contention is rare (agents work on different sections)
- ✅ Consistency is critical (atomic updates required)
- ✅ Simplicity is priority (startup time)
- ✅ Development/testing environment

**Configuration:**
```python
state_manager = SharedGlobalStateManager(
    consistency="optimistic_locking",
    conflict_resolution="retry_with_backoff"
)
```

**Example Deployment:**
- Development laptops: Shared state (WP-3.8 InMemoryStateBus)
- Small-scale services: Shared state + Redis atomic operations
- Single-machine RAG: Shared state with threading locks

### 8.2 When to Use Event Bus

**Criteria:**
- ✅ >10 agents
- ✅ Distributed across multiple machines
- ✅ Audit trail is critical (compliance, debugging)
- ✅ Failure recovery must be automatic
- ✅ Production environment

**Configuration:**
```python
event_bus = EventBusManager(
    backend="redis",  # Or Kafka
    conflict_resolution="last_write_wins",
    deduplication="event_id_based",
    snapshot_interval=10000  # Events
)
```

**Example Deployment:**
- Production multi-agent systems (100+ agents)
- Distributed RAG across multiple regions
- Mission-critical systems (legal, medical, finance)

### 8.3 Hybrid Approach (Recommended)

**Architecture:**
```
Event Bus (Source of Truth)
    ├─ Append-only event log (Redis Streams, Kafka)
    ├─ Snapshot every 10K events
    └─ Publish events to subscribers
    
Local Cache per Agent
    ├─ Materialized view of state
    ├─ TTL-based expiration
    └─ Subscribes to event bus
    
Conflict Resolution
    ├─ Last-Write-Wins by default
    ├─ OT for document edits
    └─ Supervisor override if needed
```

**Rationale:**
- Event bus ensures consistency at scale
- Local caches reduce latency (no remote queries)
- Conflict resolution handles edge cases
- Audit trail for debugging

---

## 9. Implementation Recommendations

### Phase 1: Development (WP-3.8 Current State)

**Use:** Shared Global State (InMemoryStateBus)
- ✅ Working, proven in tests
- ✅ Simple debugging
- ✅ Suitable for <5 agents

**Code:**
```python
class InMemoryStateBus(StateBus):
    def __init__(self):
        self.state = {}
        self.lock = threading.RLock()  # Re-entrant lock
    
    def write_state(self, task_id, key, value):
        with self.lock:
            self.state[task_id][key] = value
```

### Phase 2: Scale (2-3 months)

**Transition:** Shared Global State → Event Bus (with consensus)

**1. Add Event Logging:**
```python
class EventLoggingStateBus(StateBus):
    def __init__(self, event_log):
        self.state = {}
        self.event_log = event_log
    
    def write_state(self, task_id, key, value):
        with self.lock:
            event = Event(
                event_id=uuid.uuid4(),
                timestamp=now(),
                task_id=task_id,
                key=key,
                data=value
            )
            self.event_log.append(event)
            self.state[task_id][key] = value
```

**2. Add Event Replay:**
```python
def recover_state_from_events(task_id):
    """Reconstruct state from event log."""
    state = {}
    for event in filter_events(task_id):
        state[event.key] = event.data
    return state
```

**3. Add Deduplication:**
```python
class DeduplicatingEventBus(EventBus):
    def publish_event(self, event):
        if event.event_id in self.seen_ids:
            return  # Skip duplicate
        self.event_log.append(event)
        self.seen_ids.add(event.event_id)
```

### Phase 3: Production (3-6 months)

**Deploy:** Full Event Bus with Redis/Kafka

**Architecture:**
```
Agent 1 ───\
Agent 2 ────→ Event Bus (Redis Streams) ─→ State Manager
Agent 3 ───/          ↓
              Subscribing Agents (local cache)
              
Agent X crashed?
  → Recover from event log
  → Replay events
  → Rejoin cluster
```

---

## 10. Testing Strategy for Conflict Resolution

### Test Case 1: Concurrent Writes (Same Key)

```python
def test_concurrent_writes_same_key():
    """Both agents write to same key simultaneously."""
    state_manager = EventBusManager()
    
    # Simulate concurrent writes
    future1 = asyncio.create_task(
        state_manager.write_state("task1", "artifact", "version_A")
    )
    future2 = asyncio.create_task(
        state_manager.write_state("task1", "artifact", "version_B")
    )
    
    await asyncio.gather(future1, future2)
    
    # With LWW: one wins, other loses
    # With OT: merged
    # With Causal: ordered by causality
    result = state_manager.read_state("task1", "artifact")
    
    assert result in ["version_A", "version_B", "merged"]
```

### Test Case 2: Delayed Event Delivery

```python
def test_out_of_order_events():
    """Events arrive out of order (network lag)."""
    event_bus = EventBusManager()
    
    # Publish in order
    event1 = Event(timestamp=1000, causality_token=None)
    event2 = Event(timestamp=1001, causality_token=event1.id)
    
    # But arrive in reverse order
    event_bus.publish_event(event2)  # Arrives first
    event_bus.publish_event(event1)  # Arrives second
    
    # Event bus should reorder using causality_token
    state = event_bus.compute_state()
    
    assert state_is_valid(state)  # Correct despite ordering
```

### Test Case 3: Duplicate Submission

```python
def test_duplicate_event_deduplication():
    """Agent retries, sends same event twice."""
    event_bus = EventBusManager()
    
    event = Event(event_id="qa-001", data="feedback")
    
    event_bus.publish_event(event)
    event_bus.publish_event(event)  # Duplicate
    
    # Should apply only once
    state = event_bus.compute_state()
    assert len(state.qa_feedback) == 1  # Not 2
```

---

## 11. Migration Path: WP-3.8 → WP-3.9

### Current State (WP-3.8)
```
InMemoryStateBus (Shared Global State)
  ├─ Single-threaded lock
  ├─ No event log
  ├─ No audit trail
  └─ Suitable for <5 agents
```

### Improved State (WP-3.9)
```
EventBusManager (Event Sourcing + LWW)
  ├─ Event log (append-only)
  ├─ Deduplication (event_id)
  ├─ Audit trail (replay-able)
  ├─ Conflict resolution (LWW)
  └─ Suitable for 10-100 agents
```

### Production State (Phase 2.2+)
```
DistributedEventBus (Redis + Consensus)
  ├─ Redis Streams (event log)
  ├─ Pub/Sub (agent notifications)
  ├─ Snapshots (periodic)
  ├─ Causal consistency
  ├─ CRDT merge semantics
  └─ Suitable for 100-10K agents
```

---

## 12. Recommendations & Approval

### For WP-3.8 (Current Multi-Agent System)

**APPROVED:** Keep InMemoryStateBus (shared global state)
- Rationale: <5 agents in current demo
- Trade-off: Accept potential conflicts (rare in practice)
- Timeline: Upgrade to event bus at Phase 2.2

### For WP-3.9 (This ADR)

**IMPLEMENT:** EventBusManager with event sourcing
- Rationale: Production-ready, handles scale
- Trade-off: More code complexity (worth it)
- Conflicts resolved via: Last-Write-Wins + explicit causality

### For Production (Phase 2.3+)

**DEPLOY:** Redis-backed event bus with consensus
- Rationale: Proven technology, handles distributed systems
- Trade-off: Operational complexity (monitoring, scaling)
- Conflicts resolved via: Causal consistency + CRDT for documents

---

## 13. Appendix: Decision Factors

### Factors Favoring Shared Global State
1. Small number of agents (<10)
2. Rare contention (disjoint sections)
3. Simplicity is critical
4. Immediate consistency required
5. Single machine

### Factors Favoring Event Bus
1. Large number of agents (>10)
2. Frequent contention (same sections)
3. Audit trail needed (compliance)
4. Distributed across machines
5. Failure recovery critical
6. Long-term maintainability

---

## 14. References

- **Event Sourcing Pattern:** Martin Fowler, 2005
- **Conflict-free Replicated Data Types (CRDT):** Shapiro et al., 2011
- **Causal Consistency:** Lamport, 1978 (Vector Clocks)
- **Operational Transform:** Ellis & Gibbs, 1989
- **WP-3.8:** Multi-Agent Systems (current implementation)
- **WP-3.5:** Agentic RAG workflows (predecessor)

---

**Status:** ✅ APPROVED for implementation  
**Next Steps:**
1. Implement EventBusManager (examples_3_9.py)
2. Create comprehensive tests (test_wp_3_9.py)
3. Document conflict resolution strategies
4. Plan Phase 2.2 migration

