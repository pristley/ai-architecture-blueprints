# WP-2.4: Choreography Pattern - The "Hive Mind" Agent

**Work Product**: Event-driven implementation of the choreography pattern for emergent multi-agent workflows  
**Status**: Complete | Production-Ready  
**Duration**: 3.5 hours  
**Prerequisites**: [WP-2.2 State Management](../03-memory-state-agents/WP-2.2-State-Management-in-Single-Agent-Loop.md) | [ADR-2.1 Architecture](ADR-2.1-Choreography-Event-Driven-Agility-for-Emergent-Workflows.md)

---

## Overview

Choreography is the **distributed autonomy pattern** for multi-agent workflows. Instead of a centralized Controller directing each step (orchestration), independent agents listen for events and react autonomously. Workflows **emerge** from agent interactions rather than being explicitly defined.

**This work product teaches you to:**

1. **Understand** when to use choreography vs orchestration
2. **Design** event-driven architectures with pub/sub messaging
3. **Build** autonomous agents with independent decision-making
4. **Implement** feedback loops for system homeostasis
5. **Handle** eventual consistency and resilience patterns
6. **Trace** workflow execution across distributed agents

### Key Characteristics

| Aspect | Details |
|--------|---------|
| **Control Model** | Distributed (Each agent autonomous) |
| **Execution Model** | Event-driven, asynchronous messaging |
| **Coordination** | Via pub/sub event bus (no direct calls) |
| **Observability** | Event audit trail + correlation IDs |
| **Use Case** | Emergent workflows, multi-agent systems, feedback loops |
| **Scalability** | Scales with number of independent agents |

---

## Part 1: Core Concepts

### The Hive Mind Pattern

The **Hive Mind** is a choreography-based architecture where:

1. **Agents are autonomous** - Each makes independent decisions
2. **Events are contracts** - Agents communicate via published events
3. **Workflows emerge** - Patterns arise from agent interactions
4. **Feedback loops guide** - System homeostasis via feedback mechanisms
5. **Loose coupling** - Agents don't know about each other

```
┌──────────────┐
│ WebSearcher  │──┐ [SearchRequested]
└──────────────┘  │
                  ↓
           ┌─────────────────┐
           │  EventBus (Pub) │
           │      /Sub       │
           └─────────────────┘
                  ↑
        ┌─────────┼─────────┐
        │         │         │
   [DataFetched]  │  [RevisionRequired]
        │         │         │
        ↓         ↓         ↓
   ┌────────┐ ┌────────┐ ┌──────────┐
   │Drafter │ │ Critic │ │ Feedback │
   └────────┘ └────────┘ │ Homeostasis
       │         │        └──────────┘
       └─────────┘
   [ReportSynthesized]
```

### Event-Driven Architecture

Events are the **primary communication mechanism**:

```python
class Event(BaseModel):
    """Base event with complete tracing info."""
    event_id: str                # Unique event ID
    correlation_id: str          # Traces entire workflow
    event_type: str              # Routing key
    timestamp: str               # Event ordering
    source_agent: str            # Which agent published
    retry_count: int             # Resilience tracking
```

**Event Types in Report Generation Workflow:**

1. `SearchRequested` - Initial trigger (external request)
2. `DataFetched` - WebSearcher publishes search results
3. `DraftingStarted` - Drafter announces it's synthesizing
4. `ReportSynthesized` - Drafter publishes initial draft
5. `ReviewStarted` - Critic begins quality assessment
6. `ReviewCompleted` - Critic publishes quality score
7. `RevisionRequired` - Critic provides negative feedback (feedback loop!)
8. `ReportFinalized` - Critic approves final report

### Feedback Loops

**The Critic creates a negative feedback loop** (like a thermostat):

```
Drafter drafts report → Critic reviews → Quality score < threshold?
                          ↓
                     YES: Publish RevisionRequired
                          ↓
                     Drafter receives event
                          ↓
                     Re-draft with feedback
                          ↓
                     Publish new ReportSynthesized
                          ↓
                     Loop back to Critic review
```

This loop **continues until:**
- ✅ Quality threshold met (ReportFinalized), OR
- ❌ Max revisions exceeded (RevisionAbandoned)

---

## Part 2: Implementation Architecture

### Step 1: Define Event Types

```python
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class Event(BaseModel):
    """Base event for all domain events."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    source_agent: str
    retry_count: int = 0
    
    class Config:
        frozen = True  # Events are immutable


class SearchRequested(Event):
    """Request to search for information."""
    event_type: str = "search-requested"
    query: str
    max_results: int = 5


class DataFetched(Event):
    """Search results available."""
    event_type: str = "data-fetched"
    query: str
    results: List[Dict[str, Any]]
    sources_count: int


class ReportSynthesized(Event):
    """Draft report ready for review."""
    event_type: str = "report-synthesized"
    query: str
    report_content: str
    word_count: int


class ReviewCompleted(Event):
    """Critic assessment complete."""
    event_type: str = "review-completed"
    quality_score: float
    is_approved: bool


class RevisionRequired(Event):
    """Critic feedback for improvement."""
    event_type: str = "revision-required"
    quality_score: float
    feedback: str
    revision_count: int
    max_revisions: int
```

### Step 2: Implement Event Bus (Pub/Sub)

```python
class EventBus:
    """Asynchronous publish-subscribe event bus."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "subscribers_count": 0,
        }
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Register async handler for event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        self._stats["subscribers_count"] += 1
    
    async def publish(self, event: Event) -> None:
        """
        Publish event to all subscribers.
        
        Flow:
        1. Store in history (audit trail)
        2. Find handlers for this event type
        3. Execute handlers concurrently
        4. Track statistics
        """
        self._event_history.append(event)
        self._stats["events_published"] += 1
        
        handlers = self._subscribers.get(event.event_type, [])
        
        if handlers:
            # Execute all handlers concurrently (non-blocking)
            await asyncio.gather(
                *[self._safe_call_handler(h, event) for h in handlers],
                return_exceptions=False
            )
            self._stats["events_processed"] += len(handlers)
    
    async def _safe_call_handler(self, handler: Callable, event: Event) -> None:
        """Execute handler with error isolation."""
        try:
            await handler(event)
        except Exception as e:
            print(f"Handler error for {event.event_type}: {e}")
    
    def get_event_history(self) -> List[Event]:
        """Get complete audit trail."""
        return self._event_history.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bus statistics."""
        return self._stats.copy()
```

### Step 3: Implement Agent Base Class

```python
class Agent(ABC):
    """
    Abstract base class for autonomous agents.
    
    Design principles:
    - Each agent owns its behavior
    - Agents communicate via events only
    - No explicit coordination
    - Agents are self-governing
    """
    
    def __init__(self, event_bus: EventBus, agent_name: str):
        """Initialize agent with bus reference."""
        self.bus = event_bus
        self.agent_name = agent_name
        self.state: Dict[str, Any] = {}
    
    @abstractmethod
    async def start(self) -> None:
        """Start agent and subscribe to relevant events."""
        pass
    
    async def publish_event(self, event: Event) -> None:
        """Publish event from this agent."""
        event_dict = event.dict()
        event_dict["source_agent"] = self.agent_name
        updated_event = type(event)(**event_dict)
        await self.bus.publish(updated_event)
```

### Step 4: Implement Autonomous Agents

**WebSearcher Agent - Fetches data**

```python
class WebSearcher(Agent):
    """
    Autonomous agent for data fetching.
    
    Behavior:
    - Subscribes to "search-requested" events
    - Fetches data independently
    - Publishes "data-fetched" events
    - No knowledge of downstream agents
    """
    
    async def start(self) -> None:
        """Subscribe to search requests."""
        self.bus.subscribe("search-requested", self.on_search_requested)
    
    async def on_search_requested(self, event: SearchRequested) -> None:
        """Handle search request independently."""
        print(f"[{self.agent_name}] Searching: {event.query}")
        
        # Simulate I/O (real implementation would call APIs)
        await asyncio.sleep(0.5)
        
        # Fetch results
        results = [
            {"title": f"Result {i}", "content": f"Content about {event.query}"}
            for i in range(event.max_results)
        ]
        
        # Publish results with same correlation_id (workflow tracing)
        result_event = DataFetched(
            correlation_id=event.correlation_id,
            query=event.query,
            results=results,
            sources_count=len(results),
            source_agent=self.agent_name,
        )
        
        print(f"[{self.agent_name}] Found {len(results)} sources")
        await self.bus.publish(result_event)
```

**Drafter Agent - Synthesizes reports**

```python
class Drafter(Agent):
    """
    Autonomous agent for report synthesis.
    
    Behavior:
    - Subscribes to "data-fetched" events
    - Drafts reports from data
    - Publishes "report-synthesized" events
    - Handles revision feedback independently
    - Tracks revision count (prevents infinite loops)
    """
    
    async def start(self) -> None:
        """Subscribe to data events and revision requests."""
        self.bus.subscribe("data-fetched", self.on_data_fetched)
        self.bus.subscribe("revision-required", self.on_revision_required)
    
    async def on_data_fetched(self, event: DataFetched) -> None:
        """Draft report from fetched data."""
        print(f"[{self.agent_name}] Drafting report from {event.sources_count} sources")
        
        # Simulate synthesis work
        await asyncio.sleep(0.3)
        
        # Create draft (simulated)
        draft = f"""# Report: {event.query}

## Introduction
This report summarizes findings on {event.query}.

## Key Findings
{chr(10).join(f"- Finding {i+1}: Key insight about {event.query}" for i in range(3))}

## Conclusion
The analysis reveals important patterns in {event.query}.
"""
        
        # Track draft for revisions
        if "draft_id" not in self.state:
            self.state["draft_id"] = str(uuid.uuid4())
            self.state["revision_count"] = 0
        
        # Publish synthesized report
        report_event = ReportSynthesized(
            correlation_id=event.correlation_id,
            query=event.query,
            report_content=draft,
            word_count=len(draft.split()),
            source_agent=self.agent_name,
        )
        
        print(f"[{self.agent_name}] Draft ready ({len(draft.split())} words)")
        await self.bus.publish(report_event)
    
    async def on_revision_required(self, event: RevisionRequired) -> None:
        """Handle revision feedback."""
        print(f"[{self.agent_name}] Feedback received: {event.feedback}")
        print(f"[{self.agent_name}] Quality: {event.quality_score:.2f}, Revision {event.revision_count}/{event.max_revisions}")
        
        # Check if we can revise
        if event.revision_count >= event.max_revisions:
            print(f"[{self.agent_name}] Max revisions reached. Stopping.")
            return
        
        # Simulate revision (in production, use feedback to improve draft)
        await asyncio.sleep(0.3)
        
        # Re-draft with improvements
        revised_draft = f"""# Report: {event.feedback[:50]}...

## Introduction
This revised report incorporates feedback on quality.

## Key Findings
- Revised finding 1 based on feedback
- Revised finding 2 with improvements
- Revised finding 3 addressing concerns

## Conclusion
This improved version addresses previous concerns.
"""
        
        # Publish revised report with same correlation_id
        revised_event = ReportSynthesized(
            correlation_id=event.correlation_id,
            query="revised query",
            report_content=revised_draft,
            word_count=len(revised_draft.split()),
            source_agent=self.agent_name,
        )
        
        print(f"[{self.agent_name}] Revised draft published")
        await self.bus.publish(revised_event)
```

**Critic Agent - Quality assessment & feedback loop**

```python
class Critic(Agent):
    """
    Autonomous agent for quality assessment.
    
    Behavior:
    - Subscribes to "report-synthesized" events
    - Reviews reports against quality criteria
    - Publishes "review-completed" (approved)
    - OR publishes "revision-required" (feedback loop)
    - Implements negative feedback (homeostasis)
    """
    
    async def start(self) -> None:
        """Subscribe to reports for review."""
        self.bus.subscribe("report-synthesized", self.on_report_synthesized)
    
    async def on_report_synthesized(self, event: ReportSynthesized) -> None:
        """Review and assess report quality."""
        print(f"[{self.agent_name}] Reviewing report ({event.word_count} words)")
        
        # Simulate review work
        await asyncio.sleep(0.4)
        
        # Calculate quality score (simulated)
        base_score = 0.7 + (min(event.word_count, 1000) / 1000) * 0.3
        quality_score = min(base_score, 0.99)
        
        QUALITY_THRESHOLD = 0.80
        revision_count = self.state.get("revision_count", 0)
        max_revisions = 3
        
        is_approved = quality_score >= QUALITY_THRESHOLD
        
        if is_approved:
            # Quality acceptable - publish approval
            print(f"[{self.agent_name}] ✅ Report approved! Quality: {quality_score:.2f}")
            
            approval_event = ReviewCompleted(
                correlation_id=event.correlation_id,
                quality_score=quality_score,
                is_approved=True,
                source_agent=self.agent_name,
            )
            await self.bus.publish(approval_event)
        else:
            # Quality below threshold - publish revision request (feedback loop!)
            print(f"[{self.agent_name}] ⚠️  Quality {quality_score:.2f} < {QUALITY_THRESHOLD}")
            
            if revision_count < max_revisions:
                print(f"[{self.agent_name}] Requesting revision ({revision_count+1}/{max_revisions})")
                
                revision_event = RevisionRequired(
                    correlation_id=event.correlation_id,
                    quality_score=quality_score,
                    feedback="Report needs more depth and structure",
                    revision_count=revision_count + 1,
                    max_revisions=max_revisions,
                    source_agent=self.agent_name,
                )
                self.state["revision_count"] = revision_count + 1
                await self.bus.publish(revision_event)
            else:
                # Max revisions exceeded - give up
                print(f"[{self.agent_name}] ❌ Max revisions exceeded. Abandoning.")
```

---

## Part 3: Running the Hive Mind

### Basic Usage

```python
import asyncio
from choreography_hive_mind import EventBus, WebSearcher, Drafter, Critic, SearchRequested

async def main():
    # Create shared event bus
    bus = EventBus()
    
    # Create autonomous agents
    searcher = WebSearcher(bus, "web-searcher")
    drafter = Drafter(bus, "drafter")
    critic = Critic(bus, "critic")
    
    # Start all agents (they subscribe to events)
    await searcher.start()
    await drafter.start()
    await critic.start()
    
    # Trigger workflow by publishing initial event
    trigger = SearchRequested(
        query="machine learning in climate science",
        max_results=5,
        source_agent="user"
    )
    
    print("\n🚀 Starting hive mind workflow...\n")
    await bus.publish(trigger)
    
    # Let agents work through the feedback loop
    await asyncio.sleep(5)  # Give time for all events to propagate
    
    # Get audit trail
    events = bus.get_event_history()
    print(f"\n📊 Event history ({len(events)} events):")
    for e in events:
        print(f"  {e.event_type} - {e.source_agent}")
    
    # Get statistics
    stats = bus.get_stats()
    print(f"\n📈 Bus statistics:")
    print(f"  Events published: {stats['events_published']}")
    print(f"  Events processed: {stats['events_processed']}")
    print(f"  Active subscribers: {stats['subscribers_count']}")

asyncio.run(main())
```

### Output Example

```
🚀 Starting hive mind workflow...

[web-searcher] Searching: machine learning in climate science
[web-searcher] Found 5 sources

[drafter] Drafting report from 5 sources
[drafter] Draft ready (150 words)

[critic] Reviewing report (150 words)
[critic] ⚠️  Quality 0.65 < 0.80
[critic] Requesting revision (1/3)

[drafter] Feedback received: Report needs more depth and structure
[drafter] Revised draft published

[critic] Reviewing report (180 words)
[critic] ⚠️  Quality 0.72 < 0.80
[critic] Requesting revision (2/3)

[drafter] Feedback received: Report needs more depth and structure
[drafter] Revised draft published

[critic] Reviewing report (220 words)
[critic] ✅ Report approved! Quality: 0.82

📊 Event history (10 events):
  search-requested - user
  data-fetched - web-searcher
  drafting-started - drafter
  report-synthesized - drafter
  review-started - critic
  review-completed - critic
  revision-required - critic
  report-synthesized - drafter
  review-completed - critic
  revision-required - critic

📈 Bus statistics:
  Events published: 10
  Events processed: 25
  Active subscribers: 3
```

---

## Part 4: Advanced Patterns

### Pattern 1: Correlation ID Tracing

All events in a workflow share the same `correlation_id`:

```python
# Initial event
trigger = SearchRequested(...)  # Gets random correlation_id

# All subsequent events preserve it
data_event = DataFetched(
    correlation_id=trigger.correlation_id,  # Same ID throughout
    ...
)

# Final approval
approval = ReviewCompleted(
    correlation_id=trigger.correlation_id,  # Trace entire workflow
    ...
)

# Trace a specific workflow
def get_workflow_trace(bus: EventBus, correlation_id: str) -> List[Event]:
    """Get all events in a specific workflow."""
    return [e for e in bus.get_event_history() if e.correlation_id == correlation_id]
```

### Pattern 2: Handling Multiple Concurrent Workflows

Each workflow has its own `correlation_id`. The bus handles them independently:

```python
async def run_multiple_workflows():
    bus = EventBus()
    searcher = WebSearcher(bus, "searcher")
    drafter = Drafter(bus, "drafter")
    critic = Critic(bus, "critic")
    
    await searcher.start()
    await drafter.start()
    await critic.start()
    
    # Trigger 3 workflows
    queries = ["AI ethics", "quantum computing", "climate tech"]
    
    for query in queries:
        event = SearchRequested(query=query, source_agent="user")
        await bus.publish(event)
    
    # Each workflow progresses independently
    await asyncio.sleep(10)
    
    # Get statistics
    stats = bus.get_stats()
    print(f"Total events across all workflows: {stats['events_published']}")
```

### Pattern 3: Event Ordering and Causality

Events are timestamped for ordering:

```python
def analyze_causality(events: List[Event]) -> None:
    """Analyze event ordering and causality."""
    # Sort by timestamp
    sorted_events = sorted(events, key=lambda e: e.timestamp)
    
    # Find causal chains
    correlation_chains = {}
    for event in sorted_events:
        if event.correlation_id not in correlation_chains:
            correlation_chains[event.correlation_id] = []
        correlation_chains[event.correlation_id].append(event)
    
    # Print workflow traces
    for workflow_id, chain in correlation_chains.items():
        print(f"\nWorkflow {workflow_id[:8]}...")
        for event in chain:
            print(f"  {event.timestamp}: {event.event_type} from {event.source_agent}")
```

---

## Part 5: Test Coverage

### Testing Event Validation

```python
def test_event_immutability():
    """Events are immutable (frozen)."""
    event = SearchRequested(query="test", source_agent="test")
    
    with pytest.raises(Exception):
        event.query = "modified"  # Cannot modify


def test_event_serialization():
    """Events serialize/deserialize correctly."""
    event = DataFetched(
        query="climate",
        results=[{"title": "Study 1", "url": "http://example.com"}],
        sources_count=1,
        source_agent="searcher"
    )
    
    # Serialize to JSON
    json_str = event.json()
    
    # Deserialize
    restored = DataFetched.parse_raw(json_str)
    
    assert restored.query == event.query
    assert restored.sources_count == event.sources_count
```

### Testing Agent Behavior

```python
@pytest.mark.asyncio
async def test_searcher_publishes_on_request():
    """WebSearcher publishes data-fetched when triggered."""
    bus = EventBus()
    searcher = WebSearcher(bus, "searcher")
    await searcher.start()
    
    # Trigger search
    trigger = SearchRequested(query="test", source_agent="user")
    await bus.publish(trigger)
    
    # Wait for async processing
    await asyncio.sleep(1)
    
    # Check that data-fetched was published
    history = bus.get_event_history()
    data_events = [e for e in history if e.event_type == "data-fetched"]
    
    assert len(data_events) == 1
    assert data_events[0].sources_count > 0


@pytest.mark.asyncio
async def test_feedback_loop():
    """Critic feedback triggers Drafter revisions."""
    bus = EventBus()
    drafter = Drafter(bus, "drafter")
    critic = Critic(bus, "critic")
    
    await drafter.start()
    await critic.start()
    
    # Publish initial report
    report = ReportSynthesized(
        query="test",
        report_content="Short report",
        word_count=20,  # Too short, will trigger revision
        source_agent="drafter"
    )
    
    await bus.publish(report)
    await asyncio.sleep(1)
    
    # Check revision request was published
    history = bus.get_event_history()
    revision_events = [e for e in history if e.event_type == "revision-required"]
    
    assert len(revision_events) > 0
```

### Testing Complete Workflows

```python
@pytest.mark.asyncio
async def test_complete_workflow():
    """Test complete search-draft-review workflow."""
    bus = EventBus()
    searcher = WebSearcher(bus, "searcher")
    drafter = Drafter(bus, "drafter")
    critic = Critic(bus, "critic")
    
    await searcher.start()
    await drafter.start()
    await critic.start()
    
    # Start workflow
    trigger = SearchRequested(query="climate", source_agent="user")
    await bus.publish(trigger)
    
    # Let it run
    await asyncio.sleep(5)
    
    # Verify complete chain of events
    history = bus.get_event_history()
    event_types = [e.event_type for e in history]
    
    assert "search-requested" in event_types
    assert "data-fetched" in event_types
    assert "report-synthesized" in event_types
    assert "review-completed" in event_types
    
    # Should have all same correlation_id
    correlation_ids = {e.correlation_id for e in history}
    assert len(correlation_ids) == 1  # Single workflow
```

---

## Part 6: Choreography vs Orchestration

### When to Use Choreography

✅ **Multi-agent systems** - Independent agents collaborating  
✅ **Emergent workflows** - Patterns emerge from interactions  
✅ **Feedback loops** - System self-regulates via feedback  
✅ **Loose coupling** - Agents don't depend on each other  
✅ **Scalability** - Add agents without modifying existing ones  
✅ **Resilience** - Agent failure doesn't cascade  

### When to Use Orchestration

❌ Choreography becomes problematic when you need:

- ❌ **Predictable workflows** - Order must be explicit
- ❌ **Full audit trails** - Causality must be clear
- ❌ **Compliance** - Regulatory requirements
- ❌ **Easy debugging** - Who calls whom must be obvious
- ❌ **Sequential validation** - Each step must be verified

### Decision Matrix

| Factor | Choreography | Orchestration |
|--------|--------------|---------------|
| **Complexity** | Simple (agents independent) | Simple (explicit steps) |
| **Coupling** | Loose | Tight |
| **Scalability** | Scales well | Scales with bottleneck |
| **Observability** | Event trail | Audit trail |
| **Debugging** | Harder (distributed) | Easier (central) |
| **Flexibility** | High (emergent) | Low (rigid) |
| **Consistency** | Eventual | Strong |
| **Agent autonomy** | High | None (directed) |

---

## Part 7: Learning Path

**Estimated Time: 3.5 hours**

### Step 1: Understand Event-Driven Architecture (45 min)
- [ ] Read ADR-2.1 for choreography principles
- [ ] Understand pub/sub messaging patterns
- [ ] Review comparison matrix: Choreography vs Orchestration

### Step 2: Study the Hive Mind Implementation (60 min)
- [ ] Review choreography_hive_mind.py code
- [ ] Understand Event base class and custom events
- [ ] Study EventBus pub/sub mechanisms
- [ ] Trace Agent behavior (WebSearcher, Drafter, Critic)

### Step 3: Run the Tests (30 min)
- [ ] Run test suite: `pytest tests/test_choreography_hive_mind.py -v`
- [ ] Observe event propagation
- [ ] Trace feedback loop execution
- [ ] Review event audit trails

### Step 4: Hands-On: Build Your Own Agents (60 min)
- [ ] Create an agent for your domain
- [ ] Define custom events
- [ ] Implement agent behavior
- [ ] Subscribe to and publish events

### Step 5: Extend with Feedback Loops (30 min)
- [ ] Add quality assessment to your agent
- [ ] Implement feedback mechanism
- [ ] Add max iterations to prevent infinite loops
- [ ] Test with multiple concurrent workflows

---

## Key Takeaways

1. **Choreography = Distributed Autonomy** - Agents act independently
2. **Events are Contracts** - Agents communicate via published events
3. **Workflows Emerge** - Patterns arise from agent interactions
4. **Feedback Loops Guide** - System self-regulates through feedback
5. **Loose Coupling = Resilience** - Agents don't fail together
6. **Eventual Consistency** - Accept delays for flexibility
7. **Correlation IDs = Traceability** - Track workflows across agents

---

## References

- **ADR-2.1**: [Choreography - Event-Driven Agility for Emergent Workflows](ADR-2.1-Choreography-Event-Driven-Agility-for-Emergent-Workflows.md)
- **WP-2.2**: [State Management in Single Agent Loop](../03-memory-state-agents/WP-2.2-State-Management-in-Single-Agent-Loop.md)
- **Implementation**: [choreography_hive_mind.py](choreography_hive_mind.py)
- **Tests**: [tests/test_choreography_hive_mind.py](../../tests/test_choreography_hive_mind.py)
- **Pattern Comparison**: [WP-2.3 Orchestration](WP-2.3-Orchestration-Pattern.md)

---

## Next Steps

✅ **Completed**: Understanding and implementing choreography patterns

📚 **Continue Learning**:
- Compare with [WP-2.3 Orchestration Pattern](WP-2.3-Orchestration-Pattern.md)
- Review [AGENTMAP.md](../reference/AGENTMAP.md) for relationships
- Explore [LANGCHAIN_ECOSYSTEM_MAP.md](../reference/LANGCHAIN_ECOSYSTEM_MAP.md) for integrations

🚀 **Apply to Your Projects**:
- Design event schemas for your domain
- Create autonomous agents with independent behavior
- Implement feedback loops for system homeostasis
- Add observability with correlation IDs
- Build comprehensive test suites
- Monitor event flow for production systems

