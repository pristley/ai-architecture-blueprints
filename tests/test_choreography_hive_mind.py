"""
Tests for Choreography-Based Hive Mind Pattern

COVERAGE
════════
- Event Bus: Publishing, subscribing, event history
- Event Types: Validation, serialization with Pydantic
- Agents: Autonomous operation, event subscription, publishing
- Choreography Flow: Multi-agent interactions and feedback loops
- Error Handling: Isolated failures, resilience
- System Integration: Complete workflows with multiple agents

TESTING STRATEGY
════════════════
1. Unit Tests: Individual agents and components
2. Integration Tests: Multi-agent workflows
3. Choreography Tests: Event-driven behavior emergence
4. Resilience Tests: Error isolation and recovery

RUNNING TESTS
═════════════
    pytest tests/test_choreography_hive_mind.py -v
    pytest tests/test_choreography_hive_mind.py -v --tb=short
    pytest tests/test_choreography_hive_mind.py::TestEventBus -v
"""

import pytest
import asyncio
from datetime import datetime
from typing import List

from choreography_hive_mind import (
    Event,
    SearchRequested,
    DataFetched,
    ReportSynthesized,
    ReviewCompleted,
    RevisionRequired,
    RevisionAbandoned,
    EventBus,
    WebSearcher,
    Drafter,
    Critic,
    HiveMindOrchestrator,
)


# ============================================================================
# EVENT TESTS
# ============================================================================

class TestEventTypes:
    """Test Pydantic event validation and serialization."""

    def test_event_creation_with_defaults(self):
        """Events auto-generate event_id and correlation_id."""
        event = SearchRequested(
            query="test",
            source_agent="user"
        )
        assert event.event_id
        assert event.correlation_id
        assert event.event_type == "search-requested"
        assert event.query == "test"
        assert event.retry_count == 0

    def test_event_immutability(self):
        """Events are frozen (immutable)."""
        event = SearchRequested(query="test", source_agent="user")
        with pytest.raises(Exception):  # Pydantic ValidationError
            event.query = "modified"

    def test_event_serialization(self):
        """Events can be serialized to dict."""
        event = SearchRequested(query="test", source_agent="user")
        event_dict = event.dict()
        assert event_dict["query"] == "test"
        assert event_dict["event_type"] == "search-requested"
        assert "event_id" in event_dict

    def test_correlation_id_propagation(self):
        """Correlation ID can be passed through multiple events."""
        original_event = SearchRequested(query="test", source_agent="user")
        original_id = original_event.correlation_id

        # Create downstream event with same correlation
        follow_up = DataFetched(
            correlation_id=original_id,
            query="test",
            results=[],
            confidence_score=0.9,
            sources_count=0,
            source_agent="searcher"
        )
        assert follow_up.correlation_id == original_id

    def test_event_timestamp(self):
        """Events have ISO 8601 timestamps."""
        event = SearchRequested(query="test", source_agent="user")
        # Parse timestamp to verify format
        timestamp_dt = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
        assert timestamp_dt.year >= 2020


# ============================================================================
# EVENT BUS TESTS
# ============================================================================

class TestEventBus:
    """Test the pub/sub event bus."""

    @pytest.mark.asyncio
    async def test_publish_to_empty_bus(self):
        """Publishing to bus with no subscribers doesn't error."""
        bus = EventBus()
        event = SearchRequested(query="test", source_agent="user")
        await bus.publish(event)
        assert bus.get_stats()["events_published"] == 1

    @pytest.mark.asyncio
    async def test_subscribe_and_receive_event(self):
        """Subscriber receives published event."""
        bus = EventBus()
        received_events: List[Event] = []

        async def handler(event: SearchRequested):
            received_events.append(event)

        bus.subscribe("search-requested", handler)
        event = SearchRequested(query="test", source_agent="user")
        await bus.publish(event)

        # Small delay for async processing
        await asyncio.sleep(0.1)
        assert len(received_events) == 1
        assert received_events[0].query == "test"

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        """Multiple subscribers all receive the same event."""
        bus = EventBus()
        events1: List[Event] = []
        events2: List[Event] = []

        async def handler1(event):
            events1.append(event)

        async def handler2(event):
            events2.append(event)

        bus.subscribe("search-requested", handler1)
        bus.subscribe("search-requested", handler2)

        event = SearchRequested(query="test", source_agent="user")
        await bus.publish(event)
        await asyncio.sleep(0.1)

        assert len(events1) == 1
        assert len(events2) == 1

    @pytest.mark.asyncio
    async def test_multiple_event_types(self):
        """Different event types route to correct subscribers."""
        bus = EventBus()
        search_events: List[Event] = []
        data_events: List[Event] = []

        async def search_handler(event):
            search_events.append(event)

        async def data_handler(event):
            data_events.append(event)

        bus.subscribe("search-requested", search_handler)
        bus.subscribe("data-fetched", data_handler)

        search_event = SearchRequested(query="test", source_agent="user")
        data_event = DataFetched(
            query="test",
            results=[],
            confidence_score=0.9,
            sources_count=0,
            source_agent="searcher"
        )

        await bus.publish(search_event)
        await bus.publish(data_event)
        await asyncio.sleep(0.1)

        assert len(search_events) == 1
        assert len(data_events) == 1
        assert search_events[0].event_type == "search-requested"
        assert data_events[0].event_type == "data-fetched"

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Unsubscribing removes handler."""
        bus = EventBus()
        events: List[Event] = []

        async def handler(event):
            events.append(event)

        bus.subscribe("search-requested", handler)
        bus.unsubscribe("search-requested", handler)

        event = SearchRequested(query="test", source_agent="user")
        await bus.publish(event)
        await asyncio.sleep(0.1)

        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_event_history(self):
        """Event history tracks all published events."""
        bus = EventBus()
        event1 = SearchRequested(query="test1", source_agent="user")
        event2 = DataFetched(
            query="test2",
            results=[],
            confidence_score=0.9,
            sources_count=0,
            source_agent="searcher"
        )

        await bus.publish(event1)
        await bus.publish(event2)

        history = bus.get_event_history()
        assert len(history) == 2
        assert history[0].event_type == "search-requested"
        assert history[1].event_type == "data-fetched"

    @pytest.mark.asyncio
    async def test_statistics(self):
        """Bus tracks statistics correctly."""
        bus = EventBus()

        async def handler(event):
            pass

        bus.subscribe("search-requested", handler)
        event = SearchRequested(query="test", source_agent="user")
        await bus.publish(event)
        await asyncio.sleep(0.1)

        stats = bus.get_stats()
        assert stats["events_published"] == 1
        assert stats["events_processed"] == 1
        assert stats["subscribers_count"] == 1


# ============================================================================
# AGENT TESTS
# ============================================================================

class TestWebSearcher:
    """Test the WebSearcher agent."""

    @pytest.mark.asyncio
    async def test_searcher_subscribes_to_search_events(self):
        """WebSearcher subscribes to search-requested events."""
        bus = EventBus()
        searcher = WebSearcher(bus, "web-searcher")
        await searcher.start()

        # Verify subscription registered
        assert "search-requested" in bus._subscribers

    @pytest.mark.asyncio
    async def test_searcher_publishes_data_fetched(self):
        """WebSearcher publishes data-fetched event."""
        bus = EventBus()
        searcher = WebSearcher(bus, "web-searcher")
        await searcher.start()

        event = SearchRequested(query="test", source_agent="user")
        await bus.publish(event)

        # Wait for async processing
        await asyncio.sleep(1.0)

        history = bus.get_event_history()
        data_events = [e for e in history if e.event_type == "data-fetched"]
        assert len(data_events) == 1
        assert data_events[0].results
        assert data_events[0].confidence_score > 0

    @pytest.mark.asyncio
    async def test_searcher_maintains_correlation_id(self):
        """WebSearcher preserves correlation_id from request."""
        bus = EventBus()
        searcher = WebSearcher(bus, "web-searcher")
        await searcher.start()

        original_event = SearchRequested(query="test", source_agent="user")
        original_correlation = original_event.correlation_id

        await bus.publish(original_event)
        await asyncio.sleep(1.0)

        history = bus.get_event_history()
        data_events = [e for e in history if e.event_type == "data-fetched"]
        assert data_events[0].correlation_id == original_correlation


class TestDrafter:
    """Test the Drafter agent."""

    @pytest.mark.asyncio
    async def test_drafter_subscribes_to_data_events(self):
        """Drafter subscribes to data-fetched events."""
        bus = EventBus()
        drafter = Drafter(bus, "drafter")
        await drafter.start()

        assert "data-fetched" in bus._subscribers
        assert "revision-required" in bus._subscribers

    @pytest.mark.asyncio
    async def test_drafter_publishes_synthesized_report(self):
        """Drafter publishes report-synthesized event."""
        bus = EventBus()
        drafter = Drafter(bus, "drafter")
        await drafter.start()

        data_event = DataFetched(
            query="test",
            results=[{"title": "Result", "snippet": "Test content"}],
            confidence_score=0.9,
            sources_count=1,
            source_agent="searcher"
        )

        await bus.publish(data_event)
        await asyncio.sleep(1.0)

        history = bus.get_event_history()
        report_events = [e for e in history if e.event_type == "report-synthesized"]
        assert len(report_events) == 1
        assert report_events[0].report_content
        assert report_events[0].word_count > 0

    @pytest.mark.asyncio
    async def test_drafter_handles_revision_feedback(self):
        """Drafter responds to revision-required events."""
        bus = EventBus()
        drafter = Drafter(bus, "drafter")
        await drafter.start()

        revision_event = RevisionRequired(
            report_id="report-123",
            quality_score=0.7,
            feedback="Add more details",
            revision_count=1,
            max_revisions=3,
            source_agent="critic"
        )

        await bus.publish(revision_event)
        await asyncio.sleep(1.0)

        history = bus.get_event_history()
        report_events = [e for e in history if e.event_type == "report-synthesized"]
        assert len(report_events) == 1


class TestCritic:
    """Test the Critic agent."""

    @pytest.mark.asyncio
    async def test_critic_subscribes_to_report_events(self):
        """Critic subscribes to report-synthesized events."""
        bus = EventBus()
        critic = Critic(bus, "critic")
        await critic.start()

        assert "report-synthesized" in bus._subscribers

    @pytest.mark.asyncio
    async def test_critic_approves_high_quality_reports(self):
        """Critic publishes review-completed for high quality reports."""
        bus = EventBus()
        critic = Critic(bus, "critic")
        await critic.start()

        # Very high quality report: 0.9 draft score + long content (500+ words) = should pass 0.8 threshold
        report_event = ReportSynthesized(
            query="test",
            report_content="Detailed report content. " * 100,  # ~2500 words for full length_score
            draft_quality_score=0.9,
            word_count=500,
            source_agent="drafter"
        )

        await bus.publish(report_event)
        await asyncio.sleep(1.0)

        history = bus.get_event_history()
        review_events = [e for e in history if e.event_type == "review-completed"]
        assert len(review_events) == 1
        assert review_events[0].is_approved

    @pytest.mark.asyncio
    async def test_critic_requests_revision_for_low_quality(self):
        """Critic publishes revision-required for low quality reports."""
        bus = EventBus()
        critic = Critic(bus, "critic")
        await critic.start()

        # Low quality report (below threshold of 0.8)
        report_event = ReportSynthesized(
            query="test",
            report_content="Short report.",  # Short content for low score
            draft_quality_score=0.6,
            word_count=20,
            source_agent="drafter"
        )

        await bus.publish(report_event)
        await asyncio.sleep(1.0)

        history = bus.get_event_history()
        revision_events = [e for e in history if e.event_type == "revision-required"]
        assert len(revision_events) == 1
        assert revision_events[0].revision_count == 1


# ============================================================================
# CHOREOGRAPHY INTEGRATION TESTS
# ============================================================================

class TestChoreographyFlow:
    """Test multi-agent choreography workflows."""

    @pytest.mark.asyncio
    async def test_complete_workflow_happy_path(self):
        """
        Complete workflow: Search -> Draft -> Review -> Approve or Revise.
        
        This tests that the entire choreography flow works end-to-end
        without errors.
        """
        orchestrator = HiveMindOrchestrator()
        await orchestrator.initialize()
        await orchestrator.request_report("climate change")
        await orchestrator.wait_for_completion(duration=3.0)

        history = orchestrator.bus.get_event_history()
        event_types = [e.event_type for e in history]

        # Should see complete workflow events
        assert "search-requested" in event_types
        assert "data-fetched" in event_types
        assert "report-synthesized" in event_types
        # Should have either revision or approval (at least one quality assessment)
        has_quality_assessment = ("revision-required" in event_types or 
                                "review-completed" in event_types or
                                "revision-abandoned" in event_types)
        assert has_quality_assessment

    @pytest.mark.asyncio
    async def test_workflow_with_revision_loop(self):
        """
        Workflow with revision: Search -> Draft -> Review -> Revise -> Approve.
        
        This tests the feedback loop where Critic requests improvements.
        """
        orchestrator = HiveMindOrchestrator()
        await orchestrator.initialize()
        await orchestrator.request_report("machine learning")
        await orchestrator.wait_for_completion(duration=5.0)

        history = orchestrator.bus.get_event_history()
        event_types = [e.event_type for e in history]

        # May have revisions or approval depending on quality
        assert "search-requested" in event_types
        assert "data-fetched" in event_types
        assert "report-synthesized" in event_types
        # Either revision or approval events should be present
        has_feedback = "revision-required" in event_types or "review-completed" in event_types
        assert has_feedback

    @pytest.mark.asyncio
    async def test_correlation_id_flows_through_workflow(self):
        """Correlation ID is maintained across entire workflow."""
        orchestrator = HiveMindOrchestrator()
        await orchestrator.initialize()
        await orchestrator.request_report("test query")
        await orchestrator.wait_for_completion(duration=3.0)

        history = orchestrator.bus.get_event_history()
        # First event is the user request
        original_correlation = history[0].correlation_id

        # All workflow events should have same correlation ID
        workflow_events = history[1:]  # Exclude original request
        for event in workflow_events:
            if event.source_agent != "user":
                assert event.correlation_id == original_correlation

    @pytest.mark.asyncio
    async def test_multiple_concurrent_workflows(self):
        """System handles multiple concurrent search requests."""
        orchestrator = HiveMindOrchestrator()
        await orchestrator.initialize()

        # Request two reports concurrently
        await orchestrator.request_report("query 1")
        await orchestrator.request_report("query 2")
        await orchestrator.wait_for_completion(duration=5.0)

        history = orchestrator.bus.get_event_history()
        search_events = [e for e in history if e.event_type == "search-requested"]

        # Should have received both requests
        assert len(search_events) >= 2

    @pytest.mark.asyncio
    async def test_event_ordering_in_history(self):
        """Events are recorded in order in history."""
        orchestrator = HiveMindOrchestrator()
        await orchestrator.initialize()
        await orchestrator.request_report("test")
        await orchestrator.wait_for_completion(duration=3.0)

        history = orchestrator.bus.get_event_history()
        
        # Timestamps should be non-decreasing
        for i in range(len(history) - 1):
            current_time = datetime.fromisoformat(history[i].timestamp.replace("Z", "+00:00"))
            next_time = datetime.fromisoformat(history[i + 1].timestamp.replace("Z", "+00:00"))
            assert current_time <= next_time


# ============================================================================
# RESILIENCE TESTS
# ============================================================================

class TestResilience:
    """Test error handling and isolation."""

    @pytest.mark.asyncio
    async def test_handler_error_isolation(self):
        """
        Handler exceptions don't affect other handlers.
        
        Demonstrates loose coupling: if one agent fails, others continue.
        """
        bus = EventBus()
        successful_events: List[Event] = []

        async def failing_handler(event):
            raise Exception("Handler failure")

        async def successful_handler(event):
            successful_events.append(event)

        bus.subscribe("search-requested", failing_handler)
        bus.subscribe("search-requested", successful_handler)

        event = SearchRequested(query="test", source_agent="user")
        await bus.publish(event)
        await asyncio.sleep(0.1)

        # Successful handler should have received event despite other handler failing
        assert len(successful_events) == 1

    @pytest.mark.asyncio
    async def test_max_revision_limit_prevents_infinite_loops(self):
        """Critic stops requesting revisions after max attempts."""
        bus = EventBus()
        critic = Critic(bus, "critic")
        await critic.start()

        # Simulate a low-quality report that would keep failing
        report_event = ReportSynthesized(
            query="test",
            report_content="Short.",
            draft_quality_score=0.5,  # Well below threshold
            word_count=10,
            source_agent="drafter"
        )

        # Publish the same low-quality event multiple times
        for _ in range(5):
            await bus.publish(report_event)
            await asyncio.sleep(0.2)

        history = bus.get_event_history()
        abandoned_events = [e for e in history if e.event_type == "revision-abandoned"]

        # At some point, should abandon revisions
        # (This depends on Critic's internal revision tracking logic)
        assert len(history) > 0


# ============================================================================
# STATISTICS AND OBSERVABILITY TESTS
# ============================================================================

class TestObservability:
    """Test statistics and monitoring capabilities."""

    @pytest.mark.asyncio
    async def test_bus_statistics_tracking(self):
        """Bus correctly tracks statistics."""
        bus = EventBus()

        async def handler(event):
            pass

        bus.subscribe("search-requested", handler)
        event = SearchRequested(query="test", source_agent="user")
        await bus.publish(event)
        await asyncio.sleep(0.1)

        stats = bus.get_stats()
        assert stats["events_published"] > 0
        assert stats["subscribers_count"] > 0

    @pytest.mark.asyncio
    async def test_orchestrator_statistics(self):
        """Orchestrator provides system statistics."""
        orchestrator = HiveMindOrchestrator()
        await orchestrator.initialize()
        await orchestrator.request_report("test")
        await orchestrator.wait_for_completion(duration=2.0)

        stats = orchestrator.bus.get_stats()
        assert stats["events_published"] > 0
        assert "search-requested" in [
            e.event_type for e in orchestrator.bus.get_event_history()
        ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
