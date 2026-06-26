# ADR-2.1: Choreography: Event-Driven Agility for Emergent Workflows

**Status**: ACCEPTED — Use choreography as the primary coordination pattern for multi-agent workflows.

---

## TL;DR

Use choreography when you need agents to work independently without a central coordinator. Agents publish events (e.g., "data-fetched") and subscribe to events they care about. This approach scales better than orchestration and recovers faster from failures, but requires more operational maturity.

**Choose choreography if you have**:
- Multiple independent agents that need to scale separately
- Tolerance for eventual consistency (results converge, not instant)
- Investment in observability infrastructure (distributed tracing)

**Choose orchestration if you need**:
- Simple, centralized control flow that's easy to understand
- Hard real-time latency guarantees
- Immediate error detection and handling

---

## Decision

**Adopt choreography-based coordination for multi-agent workflows.**

Agents interact through an asynchronous event bus (pub/sub model). Each agent:
1. Publishes domain events when work completes ("data-fetched", "report-synthesized", "review-completed")
2. Subscribes to events relevant to its work
3. Handles events independently, making its own decisions
4. Manages its own state without external direction

**Example flow**:
```
WebSearcher publishes:  "data-fetched" 
                             ↓
                      Event Bus (pub/sub)
                             ↓
Drafter subscribes, receives "data-fetched", publishes: "report-synthesized"
                             ↓
Critic subscribes, receives "report-synthesized", publishes: "review-completed"
                             ↓
Drafter subscribes, receives "review-completed"
```

---

## Why This Decision

### Problem with Orchestration

The orchestration pattern (where a central coordinator directs all agents) creates three pain points as workflows grow:

1. **Single point of failure**: If the orchestrator fails, the entire workflow fails
2. **Scaling bottleneck**: The orchestrator becomes the performance ceiling; you can't simply add more agents
3. **Tight coupling**: Agents depend on the orchestrator for scheduling; changes to one agent require orchestrator updates

### Choreography Solves These Problems

**1. Resilience**: Agents fail independently. If the Critic agent fails, the WebSearcher and Drafter continue working. Failed agents recover asynchronously without timing out the entire system.

**2. Scalability**: Add agents without modifying existing agents. New agents simply subscribe to existing events. The event bus (Kafka, RabbitMQ, Redis) remains the only bottleneck, and these systems scale to millions of events per second.

**3. Autonomy**: Agents decide locally how to respond to events. The Drafter doesn't ask permission to draft; it sees "data-fetched" and drafts. The Critic doesn't wait for a command; it sees "report-synthesized" and critiques.

### How Feedback Loops Enable Self-Regulation

Choreography enables natural feedback loops that regulate system behavior without central control:

```
System Goal: High-Quality Reports
    ↓
Critic evaluates report quality
    ↓
Quality below threshold?  Yes → Publish "revision-required"
    ↓
Drafter sees "revision-required", re-drafts
    ↓
Process repeats until quality threshold met or max revisions exceeded
```

No orchestrator says "re-draft." The Drafter autonomously chooses to respond to the Critic's signal. This creates a **self-regulating system** where quality improvement emerges from agent interactions, not central mandates.

**Key insight**: Choreography doesn't eliminate feedback loops; it distributes them. Each agent implements its own response logic.

---

## How to Implement

### Event Bus Requirements

Use a pub/sub system that provides:
- **Durability**: Events persist so late-joining subscribers don't miss work
- **Ordering**: Events within a partition maintain order (Kafka partitions, Redis Streams, RabbitMQ queues)
- **Replayability**: You can replay event history for debugging and auditing

**Options**:
- **Local development**: Redis Streams, RabbitMQ, or in-memory EventBus (see `choreography_hive_mind.py`)
- **Production**: Kafka (highest throughput), RabbitMQ (high reliability), or managed services (AWS SQS+SNS, GCP Pub/Sub)

### Event Payload Schema

Every event must include:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440111",
  "event_type": "data-fetched",
  "timestamp": "2026-06-26T10:30:00Z",
  "source_agent": "web-searcher",
  "payload": {
    "query": "climate change mitigation",
    "results": [...]
  }
}
```

**Why these fields**:
- `correlation_id`: Link all events in a workflow together for distributed tracing
- `event_id`: Detect duplicate processing (if an agent processes the same event twice)
- `source_agent`: Understand what published this event
- `timestamp`: Reconstruct event ordering for debugging

### Agent Implementation Pattern

```python
class MyAgent:
    def __init__(self, event_bus):
        self.bus = event_bus
        self.name = "my-agent"
    
    async def start(self):
        # Subscribe to events this agent cares about
        self.bus.subscribe("event-i-care-about", self.handle_event)
    
    async def handle_event(self, event):
        # Process the event
        result = self.do_work(event)
        
        # Publish the result
        await self.bus.publish(Event(
            event_type="work-complete",
            source_agent=self.name,
            correlation_id=event.correlation_id,
            payload=result
        ))
    
    def do_work(self, event):
        # Your business logic here
        return {"status": "complete"}
```

### Preventing Infinite Loops

Choreography with feedback loops can theoretically create infinite re-work. Prevent this with:

1. **Max revision counter**: Stop retrying after N attempts
```python
if event.revision_count >= MAX_REVISIONS:
    publish("revision-abandoned", reason="max_revisions_exceeded")
    return
```

2. **Quality threshold exit**: Stop if quality meets threshold
```python
if assess_quality(report) >= QUALITY_THRESHOLD:
    publish("report-approved")
    return
```

3. **Idempotency**: Process the same event safely multiple times
```python
# Each event has a unique event_id
if self.has_processed(event.event_id):
    return  # Don't re-process duplicates
```

See [choreography_hive_mind.py](choreography_hive_mind.py) for a complete working example.

---

## Trade-offs

### Scalability vs. Observability

| Aspect | Orchestration | Choreography |
|--------|---------------|--------------|
| **Visibility** | Orchestrator sees all state changes | Each agent knows its state; system state reconstructed from event logs |
| **Debug complexity** | Simple: follow orchestrator logic | Complex: trace events across agents |
| **Tracing** | Linear call stack | Distributed tracing (correlation IDs required) |

**Resolution**: Invest in distributed tracing infrastructure. Use OpenTelemetry or Jaeger to link events by correlation_id.

### Consistency vs. Availability

| Aspect | Orchestration | Choreography |
|--------|---------------|--------------|
| **Consistency** | Strong (orchestrator enforces order) | Eventual (agents converge over time) |
| **Availability** | Lower (orchestrator failure stops everything) | Higher (failures isolated) |

**Resolution**: Design agents to be idempotent. Assume events arrive out-of-order or duplicate. Test failure scenarios explicitly.

### Simplicity vs. Flexibility

| Aspect | Orchestration | Choreography |
|--------|---------------|--------------|
| **Understanding** | Explicit control flow | Implicit control flow (emerges at runtime) |
| **Modification** | Change orchestrator to add workflows | Add subscriptions to enable new patterns |

**Resolution**: Document your event contracts. Use schema registries. Test event flow with property-based testing.

---

## When to Use Choreography

**Use choreography when**:
- You have 3+ independent agents that scale at different rates
- Agents sometimes fail; you need to recover without restarting everything
- New workflow patterns emerge and you can't predict all compositions upfront
- You have a robust event bus (Kafka, RabbitMQ, managed pub/sub)

**Use orchestration when**:
- You have a single coordinator and a few agents
- You need real-time, predictable latencies
- You prefer explicit control flow over emergent behavior
- Your event bus is unreliable or unmaintained

---

## Background: Choreography vs. Orchestration

This section provides deeper context for those unfamiliar with choreography patterns.

### Orchestration: "Director" Model

In orchestration, a central coordinator (like a film director) directs agents:

```
┌──────────────────┐
│  Orchestrator    │ → "WebSearcher, search climate data"
└──────────────────┘
        ↑
        │ "Done searching"
   ┌────┴────┐
   │          │
[WebSearcher] [Drafter]
```

The orchestrator:
- Makes all scheduling decisions
- Waits for agent responses synchronously
- Sees the entire workflow state
- Represents the single point of failure

### Choreography: "Improvisation" Model

In choreography, agents are like musicians in an ensemble—they watch for cues (events) and respond:

```
    Event Bus
   ┌───────────┐
   │ Pub / Sub │
   └───────────┘
   /     |      \
[WS]  [Dr]  [Cr]  ← Agents subscribe and respond
```

Each agent:
- Watches for events it cares about
- Decides independently how to respond
- Publishes events for others to consume
- No central authority

### Systems Thinking: Feedback

Choreography enables **negative feedback loops**—the technical term for self-regulation:

1. **Desired state**: High-quality reports
2. **Measurement**: Critic evaluates quality
3. **Deviation detected**: Quality below threshold
4. **Corrective action**: Critic publishes "revision-required"
5. **Response**: Drafter sees signal, re-drafts
6. **Convergence**: System returns to desired state

This is how thermostats work (measure temperature, signal heater), how supply chains work (measure inventory, order more), and how immune systems work. Choreography allows you to implement these patterns in software without a central "brain" making all decisions.

---

## Implementation Differences

### Event Payload (Choreography)

```json
{
  "event_type": "data-fetched",
  "correlation_id": "workflow-123",
  "payload": {"results": [...]}
}
```

Each agent independently subscribes and decides to act.

### Direct Call (Orchestration)

```python
data = orchestrator.call_web_searcher(query)
report = orchestrator.call_drafter(data)
review = orchestrator.call_critic(report)
```

The orchestrator coordinates every call.

### Key Difference

In choreography, **agents are autonomous**. They see events and decide to act. In orchestration, **agents are reactive**. They only act when the orchestrator tells them to.

---

## Monitoring Choreography Workflows

### Correlation ID Propagation

Every event must carry the correlation_id from the originating request. This allows you to trace the entire workflow:

```
User requests: "Report on climate change" → correlation_id: abc123

Event 1: "search-requested" (correlation_id: abc123)
Event 2: "data-fetched" (correlation_id: abc123)
Event 3: "report-synthesized" (correlation_id: abc123)
Event 4: "review-completed" (correlation_id: abc123)

Query all events with correlation_id: abc123 to reconstruct the full workflow
```

### Event Audit Trail

Preserve all events in your event bus. Use this for:
- **Debugging**: Replay events to reproduce failures
- **Auditing**: Full workflow history for compliance
- **Analytics**: Understand which workflows succeed, which fail, why

---

## Real-World Example

See [choreography_hive_mind.py](choreography_hive_mind.py) for a complete working implementation with:
- Three autonomous agents (WebSearcher, Drafter, Critic)
- Event bus with pub/sub
- Bounded feedback loops
- Distributed tracing with correlation IDs
- Complete test suite (30 tests, 100% passing)

Run the example:
```bash
python choreography_hive_mind.py
```

---

## References

- [Designing Microservices Using CQRS and Event Sourcing](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs) (Microsoft) — How large-scale systems use events
- [Saga Pattern](https://microservices.io/patterns/data/saga.html) — Distributed coordination without orchestrators
- [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) (Martin Fowler) — Event audit trails for systems
- [Donella Meadows: Leverage Points](https://donellameadows.org/dancing-with-systems/) — Systems thinking framework

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

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-26 | ACCEPTED | Choreography pattern selected to enable agent autonomy, resilience, and emergent workflow composition. Operational complexity and eventual consistency tradeoffs accepted as investments in scalability and adaptability. |

---

**Document Version**: 1.0  
**Last Updated**: 2026-06-26  
**Author**: Staff Software Architect  
**Review Status**: Pending Stakeholder Review
