"""
Choreography-Based "Hive Mind" Pattern for Multi-Agent Report Generation

OVERVIEW
════════
This module implements an event-driven, choreography-based architecture
for multi-agent workflows. Unlike orchestration (centralized control),
choreography enables agents to react autonomously to events.

ARCHITECTURE
════════════
Three decoupled agents communicate via an asynchronous event bus:

1. WebSearcher:   Fetches data from external sources
2. Drafter:       Synthesizes findings into coherent reports
3. Critic:        Reviews output and provides feedback

Events flow through a pub/sub pattern:
- Agents publish domain events when work completes
- Subscribers react to events autonomously
- No central orchestrator; workflows emerge from agent interactions

LEARNING OBJECTIVES
═══════════════════
- Understand event-driven architecture patterns
- Compare choreography (distributed) vs. orchestration (centralized)
- Implement asynchronous agent communication with asyncio
- Design feedback loops for system homeostasis
- Build resilient, decoupled multi-agent systems

USAGE EXAMPLE
═════════════
    async def main():
        bus = EventBus()
        searcher = WebSearcher(bus)
        drafter = Drafter(bus)
        critic = Critic(bus)
        
        # Subscribe agents to relevant events
        bus.subscribe("data-fetched", drafter.on_data_fetched)
        bus.subscribe("report-synthesized", critic.on_report_synthesized)
        bus.subscribe("revision-required", drafter.on_revision_required)
        
        # Trigger workflow by requesting search
        await bus.publish(SearchRequested(query="climate change"))
        
        # Run event loop for specified duration
        await asyncio.sleep(5)

REQUIREMENTS
════════════
- Python 3.9+
- pydantic (for event validation and serialization)
- asyncio (built-in)

REFERENCES
══════════
- ADR-2.1: Choreography - Event-Driven Agility for Emergent Workflows
- WP-2.2: State Management in Single-Agent Loop
- Newman, S. (2015). Building Microservices. O'Reilly.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List
from pydantic import BaseModel, Field


# ============================================================================
# EVENT DEFINITIONS (Pydantic Models for validation and serialization)
# ============================================================================

class Event(BaseModel):
    """
    Base event class for all domain events.
    
    All events include:
    - event_id: Unique identifier for this specific event
    - correlation_id: Traces the entire workflow from origin
    - event_type: Semantic event name for routing
    - timestamp: ISO 8601 timestamp for ordering
    - source_agent: Which agent published this event
    - retry_count: Number of delivery attempts (for resilience)
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    source_agent: str
    retry_count: int = 0

    class Config:
        frozen = True  # Events are immutable


class SearchRequested(Event):
    """Initiates a new search workflow."""
    event_type: str = "search-requested"
    query: str
    search_depth: int = 3
    max_results: int = 5


class DataFetched(Event):
    """Published when search results are available."""
    event_type: str = "data-fetched"
    query: str
    results: List[Dict[str, Any]]
    confidence_score: float
    sources_count: int


class DraftingStarted(Event):
    """Published when Drafter begins synthesis."""
    event_type: str = "drafting-started"
    query: str
    data_sources: int


class ReportSynthesized(Event):
    """Published when initial report draft is complete."""
    event_type: str = "report-synthesized"
    query: str
    report_content: str
    draft_quality_score: float
    word_count: int


class ReviewStarted(Event):
    """Published when Critic begins review."""
    event_type: str = "review-started"
    report_id: str
    review_depth: str  # "shallow", "moderate", "thorough"


class ReviewCompleted(Event):
    """Published when Critic completes evaluation."""
    event_type: str = "review-completed"
    report_id: str
    quality_score: float
    issues_found: int
    is_approved: bool


class RevisionRequired(Event):
    """Published by Critic when quality threshold not met (negative feedback)."""
    event_type: str = "revision-required"
    report_id: str
    quality_score: float
    feedback: str
    revision_count: int
    max_revisions: int


class RevisionAbandoned(Event):
    """Published when max revisions exceeded."""
    event_type: str = "revision-abandoned"
    report_id: str
    final_quality_score: float
    reason: str


class ReportFinalized(Event):
    """Published when report reaches final approval."""
    event_type: str = "report-finalized"
    report_id: str
    final_content: str
    final_quality_score: float
    total_revisions: int
    processing_time_seconds: float


# ============================================================================
# EVENT BUS (Pub/Sub Infrastructure)
# ============================================================================

class EventBus:
    """
    Asynchronous publish-subscribe event bus for agent communication.
    
    Core capabilities:
    - publish(event): Broadcast event to all subscribers
    - subscribe(event_type, handler): Register async handler for events
    - unsubscribe(event_type, handler): Remove handler
    - get_stats(): Retrieve bus statistics for monitoring
    
    Design principles:
    - Non-blocking: All operations use async/await
    - Type-safe: Events validated with Pydantic
    - Observable: Tracks event flow for debugging
    - Resilient: Retries and error handling built-in
    """

    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "subscribers_count": 0,
        }

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Register an async handler for a specific event type.
        
        Args:
            event_type: Event type to subscribe to (e.g., "data-fetched")
            handler: Async callable(event) -> None
        
        Example:
            async def on_data(event: DataFetched):
                print(f"Got data: {event.results}")
            
            bus.subscribe("data-fetched", on_data)
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        self._stats["subscribers_count"] += 1

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Remove a handler from subscribers."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
            self._stats["subscribers_count"] -= 1

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Flow:
        1. Store event in history (audit trail)
        2. Find all handlers for this event type
        3. Execute handlers concurrently with asyncio.gather
        4. Track statistics
        
        Args:
            event: Pydantic event instance
        
        Note:
            Events are published fire-and-forget. Subscribers process
            asynchronously and independently.
        """
        self._event_history.append(event)
        self._stats["events_published"] += 1

        # Get handlers for this event type
        handlers = self._subscribers.get(event.event_type, [])

        if handlers:
            # Execute all handlers concurrently
            try:
                await asyncio.gather(
                    *[self._safe_call_handler(handler, event) for handler in handlers],
                    return_exceptions=False
                )
                self._stats["events_processed"] += len(handlers)
            except Exception as e:
                self._stats["events_failed"] += 1
                print(f"Error publishing event {event.event_type}: {e}")

    async def _safe_call_handler(self, handler: Callable, event: Event) -> None:
        """
        Safely call an event handler with error isolation.
        
        If a handler fails, the error is logged but doesn't affect
        other handlers (isolation principle).
        """
        try:
            await handler(event)
        except Exception as e:
            self._stats["events_failed"] += 1
            print(f"Handler error for {event.event_type}: {e}")

    def get_event_history(self) -> List[Event]:
        """Retrieve complete audit trail of all events."""
        return self._event_history.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get bus statistics for monitoring."""
        return self._stats.copy()


# ============================================================================
# AGENT BASE CLASS
# ============================================================================

class Agent(ABC):
    """
    Abstract base class for autonomous agents.
    
    Design:
    - Agents subscribe to events they care about
    - Agents publish events when work completes
    - Agents manage their own state
    - No external control; agents are self-governing
    
    Lifecycle:
    1. Agent instantiated with reference to event bus
    2. Agent subscribes to relevant event types
    3. Agent awaits events from the bus
    4. Agent reacts to events by doing work
    5. Agent publishes results as new events
    """

    def __init__(self, event_bus: EventBus, agent_name: str):
        """
        Initialize an autonomous agent.
        
        Args:
            event_bus: Reference to the shared event bus
            agent_name: Unique identifier for this agent (e.g., "web-searcher")
        """
        self.bus = event_bus
        self.agent_name = agent_name
        self.state: Dict[str, Any] = {}

    @abstractmethod
    async def start(self) -> None:
        """
        Start the agent and subscribe to relevant events.
        
        Subclasses implement this to register handlers.
        """
        pass

    async def publish_event(self, event: Event) -> None:
        """
        Publish an event from this agent.
        
        Updates source_agent field before publishing.
        """
        # Use dict() to copy and update the event
        event_dict = event.dict()
        event_dict["source_agent"] = self.agent_name
        updated_event = type(event)(**event_dict)
        await self.bus.publish(updated_event)


# ============================================================================
# AGENT IMPLEMENTATIONS
# ============================================================================

class WebSearcher(Agent):
    """
    Autonomous agent responsible for fetching external data.
    
    Behavior:
    - Subscribes to "search-requested" events
    - Fetches data from external sources (simulated)
    - Publishes "data-fetched" events with results
    - Tracks confidence in results
    
    This agent demonstrates:
    - Independent event subscription
    - Simulated external I/O
    - Result enrichment with metadata (confidence, source count)
    """

    async def start(self) -> None:
        """Subscribe to search requests."""
        self.bus.subscribe("search-requested", self.on_search_requested)

    async def on_search_requested(self, event: SearchRequested) -> None:
        """
        Handle search request event.
        
        Simulates fetching data from external source.
        In production, this would call real APIs.
        """
        print(f"[{self.agent_name}] Processing search: {event.query}")

        # Simulate I/O delay (represents API call)
        await asyncio.sleep(0.5)

        # Simulate fetching data
        results = self._fetch_results(event.query, event.max_results)
        confidence = 0.85

        # Publish results event with same correlation_id
        result_event = DataFetched(
            correlation_id=event.correlation_id,
            query=event.query,
            results=results,
            confidence_score=confidence,
            sources_count=len(results),
            source_agent=self.agent_name,
        )

        print(f"[{self.agent_name}] Found {len(results)} results")
        await self.bus.publish(result_event)

    def _fetch_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Simulate fetching search results.
        
        In production, this would query search APIs (Google, Bing, etc.)
        """
        results = []
        for i in range(min(max_results, 3)):
            results.append({
                "title": f"Result {i+1}: {query}",
                "url": f"https://example.com/result-{i+1}",
                "snippet": f"Relevant information about {query}. " * 3,
                "relevance_score": 0.9 - (i * 0.1),
            })
        return results


class Drafter(Agent):
    """
    Autonomous agent responsible for synthesis and report generation.
    
    Behavior:
    - Subscribes to "data-fetched" and "revision-required" events
    - Synthesizes data into coherent reports
    - Publishes "report-synthesized" events
    - Handles revisions by re-drafting with feedback
    - Tracks revision count to prevent infinite loops
    - Stops responding when max revisions reached
    
    This agent demonstrates:
    - Multiple event subscriptions
    - State management (tracking revisions)
    - Feedback loop response (revisions)
    - Bounded iteration (max revisions)
    """

    async def start(self) -> None:
        """Subscribe to data and revision events."""
        self.bus.subscribe("data-fetched", self.on_data_fetched)
        self.bus.subscribe("revision-required", self.on_revision_required)

    async def on_data_fetched(self, event: DataFetched) -> None:
        """
        Handle data-fetched event.
        
        Begins drafting process using fetched data.
        """
        print(f"[{self.agent_name}] Received data: {event.sources_count} sources")

        # Simulate synthesis work
        await asyncio.sleep(0.7)

        report_content = self._synthesize_report(event)
        draft_quality = 0.75  # Initial quality score

        # Publish report
        synthesized_event = ReportSynthesized(
            correlation_id=event.correlation_id,
            query=event.query,
            report_content=report_content,
            draft_quality_score=draft_quality,
            word_count=len(report_content.split()),
            source_agent=self.agent_name,
        )

        print(f"[{self.agent_name}] Drafted report ({synthesized_event.word_count} words)")
        await self.bus.publish(synthesized_event)

    async def on_revision_required(self, event: RevisionRequired) -> None:
        """
        Handle revision-required event (negative feedback).
        
        Only responds if revision_count is still within max_revisions.
        This prevents infinite loops by respecting the bounded iteration.
        """
        # Check if we should respond to this revision request
        if event.revision_count >= event.max_revisions:
            # Max revisions already reached, don't respond
            print(f"[{self.agent_name}] Max revisions ({event.max_revisions}) reached, ignoring revision request")
            return

        print(f"[{self.agent_name}] Revision required: {event.feedback}")
        print(f"[{self.agent_name}] Revision {event.revision_count} of {event.max_revisions}")

        # Simulate re-drafting with feedback
        await asyncio.sleep(0.6)

        improved_report = self._improve_report(event.feedback)
        improved_quality = event.quality_score + 0.08  # Quality improves with iteration

        # Publish revised report
        revised_event = ReportSynthesized(
            correlation_id=event.correlation_id,
            query=event.report_id,
            report_content=improved_report,
            draft_quality_score=improved_quality,
            word_count=len(improved_report.split()),
            source_agent=self.agent_name,
        )

        print(f"[{self.agent_name}] Re-drafted report (quality: {improved_quality:.2f})")
        await self.bus.publish(revised_event)

    def _synthesize_report(self, event: DataFetched) -> str:
        """Simulate report synthesis from data."""
        snippets = [r["snippet"] for r in event.results]
        combined = "\n\n".join(snippets)
        # Add substantive content to meet word count threshold
        report = f"""Report on {event.query}

Executive Summary
═════════════════
This comprehensive report analyzes key findings related to {event.query}.
The research is based on {event.sources_count} authoritative sources.

Findings
════════
{combined}

Analysis
════════
Based on the data collected, we can draw several important conclusions.
The evidence strongly supports the following observations:
1. Primary finding with detailed explanation and context
2. Secondary finding with supporting evidence and implications
3. Tertiary finding with broader significance and applications

Recommendations
═══════════════
Based on this analysis, we recommend the following actions:
- Action one with specific implementation details
- Action two with expected outcomes
- Action three with success metrics

Conclusion
═════════
This report has examined {event.query} from multiple angles.
The research demonstrates clear patterns and actionable insights.
Further investigation is recommended in specific domains.
"""
        return report

    def _improve_report(self, feedback: str) -> str:
        """Simulate improving report based on feedback."""
        improved = f"""Revised Report: Incorporating Critical Feedback

Executive Summary (Revised)
═══════════════════════════
This updated report addresses critical feedback received.
Feedback addressed: {feedback}

Enhanced Analysis
═════════════════
The following sections have been significantly expanded with additional sources and deeper analysis:

New Findings from Additional Research
─────────────────────────────────────
After incorporating {feedback.lower()}, we conducted additional research.
This revealed additional patterns and insights not previously captured.
The new evidence substantially strengthens our previous conclusions.

Detailed Evidence Review
───────────────────────
Each claim is now supported by multiple independent sources.
Cross-validation confirms consistency across different research methodologies.
The evidence base is now significantly more robust and comprehensive.

Updated Recommendations
──────────────────────
With this additional analysis, we can now provide more specific recommendations:
1. Refined action with additional supporting evidence
2. Enhanced strategy with measurable success criteria  
3. New initiative based on expanded research

Conclusion (Revised)
───────────────────
The revised analysis is substantially more comprehensive and well-founded.
All recommendations now rest on a stronger evidence base.
This represents a significant improvement in report quality and depth.
"""
        return improved


class Critic(Agent):
    """
    Autonomous agent responsible for quality assessment and feedback.
    
    Behavior:
    - Subscribes to "report-synthesized" events
    - Evaluates report quality against thresholds
    - Publishes "review-completed" or "revision-required" events
    - Implements negative feedback loop (Donella Meadows principle)
    - Prevents infinite loops with max_revisions limit
    
    This agent demonstrates:
    - Quality gate implementation
    - Negative feedback loops for homeostasis
    - Bounded recursion (max revisions)
    - Decision logic (approve vs. request revision)
    
    System Theory:
    The Critic implements a thermostat-like homeostasis mechanism:
    - Setpoint: Quality threshold (0.8)
    - Sensor: Quality assessment function
    - Feedback: "revision-required" events
    - Actuators: Drafter and WebSearcher
    """

    QUALITY_THRESHOLD = 0.80
    MAX_REVISIONS = 3

    def __init__(self, event_bus: EventBus, agent_name: str):
        """Initialize Critic with revision tracking."""
        super().__init__(event_bus, agent_name)
        self._revision_counts: Dict[str, int] = {}  # Track revisions per correlation_id

    async def start(self) -> None:
        """Subscribe to synthesized reports."""
        self.bus.subscribe("report-synthesized", self.on_report_synthesized)

    async def on_report_synthesized(self, event: ReportSynthesized) -> None:
        """
        Handle report-synthesized event.
        
        Evaluates quality and decides: approve or request revision?
        This is the feedback loop's decision point.
        """
        print(f"[{self.agent_name}] Reviewing report (quality: {event.draft_quality_score:.2f})")

        # Simulate review work
        await asyncio.sleep(0.4)

        quality_assessment = self._assess_quality(event)
        revision_count = self._get_revision_count(event.correlation_id)

        if quality_assessment >= self.QUALITY_THRESHOLD:
            # Approve: Goal achieved, homeostasis maintained
            review_event = ReviewCompleted(
                correlation_id=event.correlation_id,
                report_id=str(uuid.uuid4()),
                quality_score=quality_assessment,
                issues_found=0,
                is_approved=True,
                source_agent=self.agent_name,
            )
            print(f"[{self.agent_name}] ✓ Report approved (quality: {quality_assessment:.2f})")
            await self.bus.publish(review_event)
            # Clean up tracking for this workflow
            if event.correlation_id in self._revision_counts:
                del self._revision_counts[event.correlation_id]

        elif revision_count < self.MAX_REVISIONS:
            # Request revision: Send negative feedback to trigger improvement
            feedback = self._generate_feedback(quality_assessment)
            new_revision_count = revision_count + 1
            self._revision_counts[event.correlation_id] = new_revision_count
            
            revision_event = RevisionRequired(
                correlation_id=event.correlation_id,
                report_id=str(uuid.uuid4()),
                quality_score=quality_assessment,
                feedback=feedback,
                revision_count=new_revision_count,
                max_revisions=self.MAX_REVISIONS,
                source_agent=self.agent_name,
            )
            print(f"[{self.agent_name}] ✗ Revision required (quality: {quality_assessment:.2f}, revision {new_revision_count}/{self.MAX_REVISIONS})")
            await self.bus.publish(revision_event)

        else:
            # Abandon: Max revisions exceeded, escalate
            abandoned_event = RevisionAbandoned(
                correlation_id=event.correlation_id,
                report_id=str(uuid.uuid4()),
                final_quality_score=quality_assessment,
                reason=f"Max revisions ({self.MAX_REVISIONS}) exceeded",
                source_agent=self.agent_name,
            )
            print(f"[{self.agent_name}] ⚠ Revisions abandoned (quality: {quality_assessment:.2f})")
            await self.bus.publish(abandoned_event)
            # Clean up tracking for this workflow
            if event.correlation_id in self._revision_counts:
                del self._revision_counts[event.correlation_id]

    def _assess_quality(self, event: ReportSynthesized) -> float:
        """
        Assess report quality.
        
        Factors considered:
        - Content length (word count)
        - Source count
        - Draft quality from Drafter
        """
        # Simulate quality scoring algorithm
        length_score = min(event.word_count / 500.0, 1.0)  # 500 words = full score
        base_score = event.draft_quality_score
        combined_quality = (base_score * 0.7) + (length_score * 0.3)
        return combined_quality

    def _get_revision_count(self, correlation_id: str) -> int:
        """Get revision count for this workflow."""
        return self._revision_counts.get(correlation_id, 0)

    def _generate_feedback(self, quality_score: float) -> str:
        """Generate specific feedback based on quality gap."""
        gap = self.QUALITY_THRESHOLD - quality_score
        if gap > 0.15:
            return "Report lacks depth. Provide more detailed analysis with additional sources."
        elif gap > 0.05:
            return "Good effort. Strengthen the conclusion and add more supporting evidence."
        else:
            return "Minor issues remain. Review for clarity and coherence."


# ============================================================================
# ORCHESTRATOR (Workflow Runner)
# ============================================================================

class HiveMindOrchestrator:
    """
    Coordinates the Hive Mind system without controlling agents.
    
    Note: This is NOT orchestration in the traditional sense.
    This class:
    - Initializes the event bus
    - Starts all agents (subscribes them to events)
    - Monitors workflow progress
    - Provides statistics
    
    Actual workflow control emerges from agent interactions.
    """

    def __init__(self):
        """Initialize the orchestrator."""
        self.bus = EventBus()
        self.agents: Dict[str, Agent] = {}

    async def initialize(self) -> None:
        """
        Start all agents and prepare the system.
        
        Each agent subscribes to its relevant events.
        After this, the system is ready to accept requests.
        """
        # Create and start agents
        searcher = WebSearcher(self.bus, "web-searcher")
        drafter = Drafter(self.bus, "drafter")
        critic = Critic(self.bus, "critic")

        self.agents["web-searcher"] = searcher
        self.agents["drafter"] = drafter
        self.agents["critic"] = critic

        # Start each agent (subscriptions)
        await searcher.start()
        await drafter.start()
        await critic.start()

        print("[HiveMind] System initialized with agents:")
        for name in self.agents:
            print(f"  - {name}")

    async def request_report(self, query: str) -> None:
        """
        Request a report to be generated.
        
        Publishes a SearchRequested event, which triggers the workflow.
        Agents react autonomously.
        
        Args:
            query: Search query/topic for the report
        """
        search_event = SearchRequested(
            query=query,
            search_depth=3,
            max_results=5,
            source_agent="user",
        )
        print(f"\n[User] Requesting report: '{query}'")
        await self.bus.publish(search_event)

    async def wait_for_completion(self, duration: float = 10.0) -> None:
        """
        Wait for workflow to complete.
        
        Args:
            duration: Seconds to wait for agents to finish work
        """
        print(f"\n[HiveMind] Waiting {duration}s for workflow completion...")
        await asyncio.sleep(duration)

    def print_event_log(self) -> None:
        """Print audit trail of all events."""
        history = self.bus.get_event_history()
        print("\n" + "=" * 80)
        print("EVENT AUDIT TRAIL")
        print("=" * 80)
        for event in history:
            print(f"[{event.timestamp}] {event.event_type:25} | "
                  f"source={event.source_agent:12} | "
                  f"correlation_id={event.correlation_id[:8]}...")
        print("=" * 80)

    def print_statistics(self) -> None:
        """Print bus statistics."""
        stats = self.bus.get_stats()
        print("\n" + "=" * 80)
        print("SYSTEM STATISTICS")
        print("=" * 80)
        print(f"Events Published:    {stats['events_published']}")
        print(f"Events Processed:    {stats['events_processed']}")
        print(f"Events Failed:       {stats['events_failed']}")
        print(f"Active Subscribers:  {stats['subscribers_count']}")
        print("=" * 80)


# ============================================================================
# DEMONSTRATION
# ============================================================================

async def main():
    """
    Run a complete Hive Mind workflow demonstration.
    
    This shows:
    1. System initialization
    2. Request submission
    3. Event-driven workflow execution
    4. Agent autonomy and choreography
    5. Event audit trail and statistics
    """
    print("\n" + "=" * 80)
    print("CHOREOGRAPHY-BASED HIVE MIND: MULTI-AGENT REPORT GENERATION")
    print("=" * 80)

    # Initialize the system
    orchestrator = HiveMindOrchestrator()
    await orchestrator.initialize()

    # Request multiple reports to show scalability
    queries = [
        "climate change mitigation strategies",
        "machine learning applications in healthcare",
    ]

    for query in queries:
        await orchestrator.request_report(query)
        # Let workflow complete before requesting next one
        await orchestrator.wait_for_completion(duration=5.0)

    # Print results
    orchestrator.print_event_log()
    orchestrator.print_statistics()

    print("\n[HiveMind] Workflow complete!")


if __name__ == "__main__":
    asyncio.run(main())
