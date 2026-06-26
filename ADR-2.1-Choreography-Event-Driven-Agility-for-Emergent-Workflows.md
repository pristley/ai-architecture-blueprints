# ADR-2.1: Choreography: Event-Driven Agility for Emergent Workflows

## Status
**ACCEPTED** — Adopted as the architectural pattern for multi-agent report generation systems.

---

## Context

### Problem Statement
The previous **Orchestration-based** pattern centralized control of agent workflows through a master coordinator. While this provided explicit sequencing and immediate error visibility, it introduced critical architectural constraints:

1. **Tight Coupling**: Agents depend on the orchestrator's existence and availability
2. **Scalability Bottleneck**: The orchestrator becomes a performance ceiling as agent count grows
3. **Brittleness**: Orchestrator failure cascades to all dependent agents
4. **Reduced Autonomy**: Agents cannot act independently or respond to domain-specific triggers
5. **Observability Paradox**: Centralized control masks distributed system dynamics

### System Evolution Requirements
The organization now requires:
- **Rapid workflow composition** without orchestrator modification
- **Emergent behavior** where agents collaborate through domain events, not directives
- **Independent agent scaling** without re-architecting coordination logic
- **Resilience through decoupling** where agent failures remain isolated
- **Self-organizing adaptation** where feedback mechanisms enable system homeostasis

### Reference Architecture: The "Hive Mind" System
Three autonomous agents interact through an asynchronous pub/sub event bus:

```
┌─────────────────┐
│   Web Searcher  │ ──→ [Data Fetched]
└─────────────────┘
        │
        ↓
┌──────────────────────┐
│  Event Bus (Pub/Sub) │
└──────────────────────┘
        ↑
        │ [Synthesis Ready]
┌─────────────────┐
│     Drafter     │ ──→ [Report Ready]
└─────────────────┘
        │
        ↑ [Feedback + Critique]
┌─────────────────┐
│     Critic      │ ←── [Assessment Complete]
└─────────────────┘
```

### Systems Thinking Context
This system operates as a **dissipative structure** with:
- **Input flux**: Raw data from the web
- **Work**: Synthesis and critical evaluation
- **Output flux**: Validated, feedback-informed reports
- **Feedback loop**: Critic's assessment re-enters the system, enabling learning and adaptation

---

## Decision

### Adopt Choreography-Based Architecture

We adopt **choreography** as the primary coordination pattern for multi-agent workflows. Agents will:

1. **Publish domain events** when work completes (e.g., "data-fetched", "report-synthesized")
2. **Subscribe to relevant events** and respond autonomously
3. **Manage their own state** without external orchestration
4. **Encapsulate decision logic** within agent boundaries
5. **Communicate via immutable event payloads** carrying sufficient context for downstream processing

### Key Architectural Principles

#### 1. Event-Driven Autonomy
Each agent operates as an **independent entity** with:
- **Local decision authority**: Agents decide when and how to process events
- **Asynchronous responsiveness**: Event handling decouples from request-response coupling
- **Reduced command surface**: No external directives; only event notifications

**Contrast with Orchestration**:
```
ORCHESTRATION:  Orchestrator → Agent (command)
                Agent → Orchestrator (response)
                [Orchestrator owns control flow]

CHOREOGRAPHY:   Agent A → Event Bus (publishes: "work-done")
                Event Bus → Agent B (subscribes)
                Agent B → Event Bus (publishes: "next-work-done")
                [Agents own their decision logic]
```

#### 2. Loose Coupling Through Event Abstraction
Agents interact through **event contracts**, not direct method calls:

- **Producer independence**: Web Searcher doesn't know or care who consumes "data-fetched" events
- **Consumer variability**: Multiple subscribers can process data-fetched events without affecting the Searcher
- **Version evolution**: Event schemas can evolve with graceful degradation if fields are additive
- **New workflow composition**: New agents join the ecosystem by subscribing to existing events

#### 3. Emergent Behavior Through Feedback Loops
The Critic agent embodies a **negative feedback mechanism** that enables homeostasis:

```
Feedback Loop Structure:
┌───────────────────────────────────────────┐
│ System Goal: High-Quality Reports         │
└───────────────────────────────────────────┘
            ↓
┌───────────────────────────────────────────┐
│ Desired State: Quality Threshold Met      │
└───────────────────────────────────────────┘
            ↓
┌───────────────────────────────────────────┐
│ Sensor (Critic): Evaluates Report Quality│
└───────────────────────────────────────────┘
            ↓
┌───────────────────────────────────────────┐
│ Deviation Detected: Quality < Threshold  │
└───────────────────────────────────────────┘
            ↓
┌───────────────────────────────────────────┐
│ Corrective Action: Re-search or Re-draft │
│ (Critic publishes "revision-required")   │
└───────────────────────────────────────────┘
            ↓
┌───────────────────────────────────────────┐
│ Web Searcher/Drafter React to Event      │
│ System Returns to Desired State           │
└───────────────────────────────────────────┘
```

This creates a **self-regulating system** without centralized control:
- The Critic doesn't command re-work; it signals deviation
- Searcher/Drafter autonomously decide to act on that signal
- The system reaches equilibrium through distributed decision-making
- Emergent quality levels arise from agent interaction, not design specification

#### 4. Second-Order Effects: The Observability Reversal

**Counterintuitive consequence**: Choreography initially appears less observable than orchestration.

**First-order effect**: 
- Orchestration provides explicit, audit-able control flow
- Choreography distributes logic across agents; control flow emerges implicitly

**Second-order effects** (and their resolution):

| Effect | Orchestration | Choreography | Implication |
|--------|---------------|--------------|-------------|
| **Tracing** | Linear, explicit call stack | Non-linear, event-driven causality | Requires distributed tracing infrastructure (e.g., correlation IDs in events) |
| **Failure Propagation** | Predictable; orchestrator centralizes error handling | Emergent; agents fail independently | Resilience ↑; debugging complexity ↑; requires per-agent health checks |
| **Workflow Visibility** | Static; orchestrator owns "happy path" | Dynamic; workflows compose at runtime | Enables adaptive workflows; requires event stream replay for audit trails |
| **Latency Characteristics** | Synchronous request-response (predictable) | Asynchronous (variable, queued) | Trade: latency predictability ↔ throughput elasticity |
| **System Coupling** | High (agents → orchestrator) | Low (agents → event contracts) | Enables independent scaling; introduces eventual consistency requirements |

**Critical insight**: Choreography doesn't reduce observability—it **redistributes** it. Observability shifts from "orchestrator sees all" to "each agent knows its state, system state emerges from event audit logs."

---

## Consequences

### Advantages

#### 1. **Scalability Without Redesign**
- Agents scale independently; event bus remains the bottleneck (not a specific orchestrator instance)
- Adding agents doesn't require orchestrator modification
- Pub/sub systems (e.g., Kafka, RabbitMQ, Redis Streams) proven at massive scale

#### 2. **Resilience Through Isolation**
- Agent failure doesn't cascade; the event bus continues operating
- Failed agents can recover asynchronously without timing out orchestrators
- Dead-letter queues enable explicit handling of repeated failures
- Timeout-based backpressure replaces orchestrator-enforced constraints

#### 3. **Autonomy Enables Adaptation**
- Agents can implement sophisticated local heuristics (e.g., Critic might retry failed analyses before escalating)
- New workflow patterns emerge without code changes (e.g., parallel re-searches, staged refinement)
- Agents respond to domain signals, not external commands

#### 4. **Reduced Deployment Coupling**
- Orchestrator updates no longer block agent deployments
- Agents can be updated, restarted, or scaled without coordinating with central authority
- Blue-green deployments become feasible for entire agent cohorts

#### 5. **Event Bus as First-Class Audit Trail**
- All system state changes flow through the event bus
- Complete workflow history is reconstructable from event logs
- Event replay enables debugging, auditing, and root-cause analysis

### Disadvantages

#### 1. **Operational Complexity**
- Choreography requires robust event bus infrastructure (high availability, durability, ordering guarantees)
- Debugging distributed, asynchronous workflows is fundamentally harder than tracing synchronous calls
- Tool maturity varies; not all organizations have mature event streaming platforms

#### 2. **Eventual Consistency Overhead**
- Agents may process stale events or duplicate events in failure scenarios
- Idempotency becomes a **mandatory** design requirement, not optional
- Handling out-of-order events requires explicit state management in agents

#### 3. **Emergent Behavior Unpredictability**
- Workflows are not fully determined until runtime; testing all compositions is exponential
- Performance emergents may surprise (e.g., feedback loops causing unexpected re-work cycles)
- Deadlocks or livelocks can arise from event loop interactions (rare but possible)

#### 4. **Latency Unpredictability**
- No guaranteed processing time; events queue in the bus
- Tail latencies increase due to asynchronous processing and potential retries
- Suitable for throughput-oriented workloads; less suitable for low-latency hard-deadline systems

#### 5. **Monitoring and Alerting Burden**
- Requires correlation ID propagation across events to trace workflows
- Missing correlation data makes debugging impossible
- Requires investment in distributed tracing (e.g., OpenTelemetry, Jaeger)

---

## Trade-offs Analysis

### Coupling vs. Observability
- **Orchestration**: Tight coupling enables global observability (orchestrator sees all transitions)
- **Choreography**: Loose coupling distributes observability (each agent sees its own state; system state reconstructed from event logs)
- **Resolution**: Implement structured event logging with correlation IDs; use distributed tracing to reconstruct workflows

### Consistency vs. Availability
- **Orchestration**: Strong consistency (orchestrator enforces ordering); reduced availability (orchestrator is critical)
- **Choreography**: Eventual consistency (agents eventually converge); higher availability (failures isolated)
- **Resolution**: Embrace eventual consistency; design agents with idempotency and conflict resolution

### Simplicity vs. Flexibility
- **Orchestration**: Simple control flow definition (orchestrator is explicit); rigid workflow composition (changes require orchestrator updates)
- **Choreography**: Complex control flow emergence (implicit in subscriptions); flexible workflow composition (new subscriptions enable new patterns)
- **Resolution**: Accept complexity; invest in event schema versioning, contract testing, and runbook documentation

---

## Implementation Guidelines

### Event Payload Design
Events MUST include:
```json
{
  "event_id": "uuid",                    // Unique event identifier
  "correlation_id": "uuid",              // Links to originating request
  "event_type": "data-fetched",          // Semantic event type
  "timestamp": "2026-06-26T10:30:00Z",   // ISO 8601 timestamp
  "source_agent": "web-searcher",        // Origin agent identifier
  "payload": {                           // Domain data
    "query": "climate change mitigation",
    "results": [...],
    "confidence_score": 0.87
  },
  "metadata": {                          // Operational context
    "schema_version": "1.0",
    "retry_count": 0
  }
}
```

### Agent State Management
Agents must:
1. **Store correlation_id** to associate downstream outputs with originating requests
2. **Track event_id** to detect and discard duplicate processing
3. **Implement idempotent handlers** for all event subscriptions
4. **Fail gracefully** if payloads contain unexpected fields or missing required data

### Feedback Loop Configuration
The Critic agent implements a **bounded feedback loop** to prevent infinite re-work:

```python
# Pseudocode for Critic's revision decision logic
def evaluate_report(report: Report) -> Event:
    quality_score = assess_quality(report)
    
    if quality_score >= QUALITY_THRESHOLD:
        return Event(
            event_type="report-approved",
            source_agent="critic",
            payload={"quality_score": quality_score}
        )
    elif report.revision_count < MAX_REVISIONS:
        return Event(
            event_type="revision-required",
            source_agent="critic",
            payload={
                "feedback": get_critique(report),
                "revision_count": report.revision_count + 1
            }
        )
    else:
        return Event(
            event_type="revision-abandoned",
            source_agent="critic",
            payload={
                "final_quality_score": quality_score,
                "reason": "max_revisions_exceeded"
            }
        )
```

### Monitoring & Observability
Implement:
1. **Correlation ID tracking** across all services (inject into logs, metrics, traces)
2. **Event flow dashboards** showing event volumes, latencies, error rates per event type
3. **Agent health checks** that verify subscription processing and detect stuck agents
4. **Dead-letter queue monitoring** that alerts on repeated failures
5. **Event audit logs** persisted long-term for compliance and forensics

---

## Risks and Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Event bus becomes bottleneck** | HIGH | Implement partitioning/sharding strategy; scale consumers independently |
| **Feedback loops cause runaway re-work** | HIGH | Enforce bounded retry counters; implement exponential backoff; circuit breakers for Critic |
| **Duplicate event processing** | HIGH | Mandate idempotent handlers; use event deduplication windows in consumers |
| **Correlation data lost in failures** | MEDIUM | Require correlation_id in all event payloads; reject events missing this field |
| **Workflow deadlock from event dependencies** | MEDIUM | Design event subscriptions to avoid circular dependencies; use timeouts to break deadlocks |
| **Testing coverage gaps** | MEDIUM | Invest in event simulation frameworks; use property-based testing for emergent behavior |

---

## Alignment with System Thinking Principles

### Feedback Loops as Regulatory Mechanism
The Critic agent embodies **negative feedback**—it senses deviation from the quality setpoint and initiates corrective action. This creates a **goal-oriented system** without centralized goals enforcement:
- The system "wants" high-quality reports (distributed preference)
- The Critic senses quality gaps and signals the need for correction
- Searcher/Drafter respond autonomously, driving the system toward equilibrium

### Leverage Points (Per Donella Meadows)
1. **Feedback loop gain** (HIGH leverage): Increase Critic's sensitivity to quality issues
2. **Information flow** (MEDIUM leverage): Ensure agents have sufficient context in events
3. **System structure** (LOW leverage): Changing event bus implementation requires major refactoring

### Emergent Properties
- **Global coherence** emerges from local agent interactions
- **Workflow patterns** arise without specification (e.g., agents naturally implement staged refinement)
- **Resilience** emerges from decoupling (failures remain isolated)
- **Adaptability** emerges from loose coupling (new agents integrate seamlessly)

---

## Related Decisions

- **ADR-1.2**: "Hello World: Three Ways" — Establishes baseline agent communication patterns
- **WP-1.3**: "The Runnable Protocol" — Defines how agents encapsulate executable logic
- **WP-2.1**: "Short-Term vs. Long-Term Memory: A Working Model" — Agent state management strategy

---

## References

- **Distributed Systems Literature**:
  - Newman, S. (2015). *Building Microservices*. O'Reilly. — Choreography vs. Orchestration comparison
  - Fowler, M., & Lewis, J. (2014). "Microservices." Retrieved from martinfowler.com — Event-driven architecture patterns

- **Systems Thinking**:
  - Meadows, D. H. (2008). *Thinking in Systems: A Primer*. Chelsea Green. — Feedback loops, leverage points, emergent behavior
  - Sterman, J. D. (2000). *Business Dynamics*. McGraw-Hill. — System dynamics, stock-and-flow models

- **Event-Driven Architecture**:
  - Kafka Documentation. "Publish-Subscribe Semantics." — Durability and replay guarantees
  - AWS. "Event-Driven Architecture" Pattern. — Cloud-native event system design

---

## Appendix: Choreography vs. Orchestration Comparison Matrix

| Dimension | Orchestration | Choreography |
|-----------|---------------|--------------|
| **Control Model** | Centralized (orchestrator) | Distributed (agents) |
| **Coupling** | High (agents → orchestrator) | Low (agents → events) |
| **Failure Isolation** | Cascading (orchestrator failure → all agents) | Isolated (agent failure → subscribers retry) |
| **Scalability** | Limited by orchestrator throughput | Scales with pub/sub infrastructure |
| **Workflow Composition** | Static (requires orchestrator update) | Dynamic (new subscriptions enable new workflows) |
| **Observability** | Centralized view (orchestrator logs) | Distributed (event audit trail + correlation IDs) |
| **Latency Predictability** | High (synchronous) | Low (asynchronous, queued) |
| **Throughput** | Limited by orchestrator latency | Unbounded (asynchronous) |
| **Consistency Model** | Strong (orchestrator enforces ordering) | Eventual (agents converge) |
| **Failure Recovery** | Orchestrator-driven rollback | Event replay + idempotent handlers |
| **Operational Burden** | Lower (single point of control) | Higher (distributed debugging required) |
| **Tool Maturity** | Mature (workflow engines, BPMN tooling) | Maturing (event streaming platforms) |

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-26 | ACCEPTED | Choreography pattern selected to enable agent autonomy, resilience, and emergent workflow composition. Operational complexity and eventual consistency tradeoffs accepted as investments in scalability and adaptability. |

---

**Document Version**: 1.0  
**Last Updated**: 2026-06-26  
**Author**: Staff Software Architect  
**Review Status**: Pending Stakeholder Review
