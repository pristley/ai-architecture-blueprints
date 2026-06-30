"""Test Suite for WP-3.9: State Management Strategies

Comprehensive tests for:
  - Shared Global State (locks, optimistic locking, conflicts)
  - Event Bus (event sourcing, deduplication, causal consistency)
  - Conflict resolution (LWW, FWW, OT)
  - Concurrent scenarios

Run with: pytest tests/test_wp_3_9.py -v
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, MagicMock

from docs.multi_agent_architectures.examples_3_9 import (
    SharedGlobalStateManager,
    EventBusManager,
    ConflictResolver,
    Event,
    ConflictError,
    ConcurrentUpdateScenario,
    VersionedValue,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def shared_state():
    """Create shared global state manager."""
    return SharedGlobalStateManager()


@pytest.fixture
def event_bus():
    """Create event bus manager."""
    return EventBusManager(conflict_resolution="last_write_wins")


@pytest.fixture
def sample_event():
    """Create sample event."""
    return Event(
        event_id="test-event-1",
        timestamp=datetime.now().isoformat(),
        task_id="task1",
        agent_id="Agent1",
        event_type="state_written",
        key="artifact",
        value="test value"
    )


# ============================================================================
# Tests: Shared Global State Manager
# ============================================================================

class TestSharedGlobalStateManager:
    """Test shared global state with locks."""
    
    def test_write_and_read(self, shared_state):
        """Test basic write and read."""
        version = shared_state.write_state("task1", "key1", "value1", agent_id="Agent1")
        result = shared_state.read_state("task1", "key1")
        
        assert result.value == "value1"
        assert result.version == 1
        assert result.agent_id == "Agent1"
    
    def test_version_increment(self, shared_state):
        """Test version increments on each write."""
        v1 = shared_state.write_state("task1", "key1", "value1", agent_id="A1")
        v2 = shared_state.write_state("task1", "key1", "value2", agent_id="A2")
        v3 = shared_state.write_state("task1", "key1", "value3", agent_id="A3")
        
        assert v1 == 1
        assert v2 == 2
        assert v3 == 3
    
    def test_optimistic_lock_success(self, shared_state):
        """Test optimistic lock when version matches."""
        v1 = shared_state.write_state("task1", "key1", "value1", agent_id="A1")
        
        # Correct version
        v2 = shared_state.write_state(
            "task1", "key1", "value2", 
            expected_version=v1,
            agent_id="A2"
        )
        assert v2 == 2
    
    def test_optimistic_lock_failure(self, shared_state):
        """Test optimistic lock when version mismatches."""
        shared_state.write_state("task1", "key1", "value1", agent_id="A1")
        
        # Wrong version
        with pytest.raises(ConflictError):
            shared_state.write_state(
                "task1", "key1", "value2",
                expected_version=99,  # Wrong!
                agent_id="A2"
            )
    
    def test_compare_and_swap_success(self, shared_state):
        """Test CAS operation when value matches."""
        shared_state.write_state("task1", "key1", "initial", agent_id="A1")
        
        result = shared_state.compare_and_swap(
            "task1", "key1", "initial", "new_value", agent_id="A2"
        )
        
        assert result is True
        assert shared_state.read_state("task1", "key1").value == "new_value"
    
    def test_compare_and_swap_failure(self, shared_state):
        """Test CAS operation when value doesn't match."""
        shared_state.write_state("task1", "key1", "initial", agent_id="A1")
        
        result = shared_state.compare_and_swap(
            "task1", "key1", "wrong", "new_value", agent_id="A2"
        )
        
        assert result is False
        assert shared_state.read_state("task1", "key1").value == "initial"
    
    def test_multiple_tasks_isolated(self, shared_state):
        """Test state isolation between tasks."""
        shared_state.write_state("task1", "key1", "value1", agent_id="A1")
        shared_state.write_state("task2", "key1", "value2", agent_id="A2")
        
        v1 = shared_state.read_state("task1", "key1").value
        v2 = shared_state.read_state("task2", "key1").value
        
        assert v1 == "value1"
        assert v2 == "value2"
    
    def test_get_all_state(self, shared_state):
        """Test getting all state for a task."""
        shared_state.write_state("task1", "key1", "value1", agent_id="A1")
        shared_state.write_state("task1", "key2", "value2", agent_id="A1")
        shared_state.write_state("task1", "key3", "value3", agent_id="A1")
        
        all_state = shared_state.get_all_state("task1")
        
        assert len(all_state) == 3
        assert all_state["key1"] == "value1"
        assert all_state["key2"] == "value2"
        assert all_state["key3"] == "value3"
    
    def test_read_nonexistent_key(self, shared_state):
        """Test reading key that doesn't exist."""
        result = shared_state.read_state("task1", "nonexistent")
        assert result is None
    
    def test_thread_safety(self, shared_state):
        """Test thread-safe concurrent writes."""
        import threading
        
        results = []
        
        def write_from_thread(thread_id):
            for i in range(10):
                version = shared_state.write_state(
                    "task1", "counter", i,
                    agent_id=f"Thread-{thread_id}"
                )
                results.append(version)
        
        threads = [threading.Thread(target=write_from_thread, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 30 writes with incremented versions
        assert len(results) == 30
        assert len(set(results)) == 30  # All unique versions


# ============================================================================
# Tests: Event Bus Manager
# ============================================================================

class TestEventBusManager:
    """Test event bus with event sourcing."""
    
    def test_publish_event(self, event_bus, sample_event):
        """Test publishing an event."""
        event_id = event_bus.publish_event(sample_event)
        
        assert event_id == sample_event.event_id
        assert len(event_bus.event_log) == 1
    
    def test_materialized_view(self, event_bus, sample_event):
        """Test materialized state is updated on publish."""
        event_bus.publish_event(sample_event)
        
        state = event_bus.read_state("task1", "artifact")
        assert state == "test value"
    
    def test_event_history(self, event_bus):
        """Test retrieving event history."""
        events = [
            Event("e1", datetime.now().isoformat(), "task1", "A1", 
                  "state_written", "key1", "v1"),
            Event("e2", datetime.now().isoformat(), "task1", "A2",
                  "state_written", "key1", "v2"),
            Event("e3", datetime.now().isoformat(), "task1", "A3",
                  "state_written", "key1", "v3"),
        ]
        
        for e in events:
            event_bus.publish_event(e)
        
        history = event_bus.get_event_history("task1", "key1")
        assert len(history) == 3
    
    def test_deduplication(self, event_bus):
        """Test duplicate event deduplication."""
        event = Event(
            event_id="duplicate-event",
            timestamp=datetime.now().isoformat(),
            task_id="task1",
            agent_id="A1",
            event_type="state_written",
            key="key1",
            value="value1"
        )
        
        # Publish twice
        event_bus.publish_event(event)
        event_bus.publish_event(event)
        
        # Should only have 1 in log
        assert len(event_bus.event_log) == 1
    
    def test_last_write_wins(self, event_bus):
        """Test LWW conflict resolution."""
        # Two agents write to same key
        event1 = Event("e1", "2026-06-30T10:00:01", "task1", "A1",
                      "state_written", "key1", "value_A")
        event2 = Event("e2", "2026-06-30T10:00:02", "task1", "A2",
                      "state_written", "key1", "value_B")
        
        event_bus.publish_event(event1)
        event_bus.publish_event(event2)
        
        # LWW: later timestamp wins
        state = event_bus.read_state("task1", "key1")
        assert state == "value_B"
    
    def test_replay_events(self, event_bus):
        """Test replaying events to reconstruct state."""
        events = [
            Event("e1", "2026-06-30T10:00:00", "task1", "A1",
                  "state_written", "key1", "v1"),
            Event("e2", "2026-06-30T10:00:01", "task1", "A1",
                  "state_written", "key2", "v2"),
            Event("e3", "2026-06-30T10:00:02", "task1", "A1",
                  "state_written", "key1", "v1_updated"),
        ]
        
        for e in events:
            event_bus.publish_event(e)
        
        # Replay
        state = event_bus.replay_events_for_task("task1")
        
        assert state["key1"] == "v1_updated"
        assert state["key2"] == "v2"
    
    def test_state_at_time(self, event_bus):
        """Test reconstructing state at specific timestamp."""
        events = [
            Event("e1", "2026-06-30T10:00:00", "task1", "A1",
                  "state_written", "key1", "v1"),
            Event("e2", "2026-06-30T10:00:02", "task1", "A1",
                  "state_written", "key1", "v2"),
            Event("e3", "2026-06-30T10:00:04", "task1", "A1",
                  "state_written", "key1", "v3"),
        ]
        
        for e in events:
            event_bus.publish_event(e)
        
        # Get state at t=02
        state_at_02 = event_bus.compute_state_at_time("task1", "2026-06-30T10:00:02")
        assert state_at_02["key1"] == "v2"
        
        # Get state at t=01 (between v1 and v2)
        state_at_01 = event_bus.compute_state_at_time("task1", "2026-06-30T10:00:01")
        assert state_at_01["key1"] == "v1"
    
    def test_event_subscribers(self, event_bus):
        """Test subscribing to events."""
        received_events = []
        
        def callback(event):
            received_events.append(event)
        
        event_bus.subscribe("state_written", callback)
        
        event = Event("e1", datetime.now().isoformat(), "task1", "A1",
                     "state_written", "key1", "value1")
        event_bus.publish_event(event)
        
        assert len(received_events) == 1
        assert received_events[0].key == "key1"
    
    def test_causality_tracking(self, event_bus):
        """Test causality token tracking."""
        event1 = Event(
            event_id="e1",
            timestamp=datetime.now().isoformat(),
            task_id="task1",
            agent_id="A1",
            event_type="state_written",
            key="artifact",
            value="v1",
            causality_token=None
        )
        
        event2 = Event(
            event_id="e2",
            timestamp=datetime.now().isoformat(),
            task_id="task1",
            agent_id="A2",
            event_type="state_written",
            key="feedback",
            value="reviewed",
            causality_token="e1"  # Depends on e1
        )
        
        event_bus.publish_event(event1)
        event_bus.publish_event(event2)
        
        # e2's causality_token should be updated
        assert event_bus.causality_tokens["task1"] == "e2"


# ============================================================================
# Tests: Conflict Resolution
# ============================================================================

class TestConflictResolver:
    """Test conflict resolution strategies."""
    
    def test_last_write_wins(self):
        """Test LWW resolution."""
        updates = [
            {"timestamp": "2026-06-30T10:00:00", "value": "A"},
            {"timestamp": "2026-06-30T10:00:02", "value": "B"},
            {"timestamp": "2026-06-30T10:00:01", "value": "C"},
        ]
        
        winner = ConflictResolver.last_write_wins(updates)
        assert winner["value"] == "B"
    
    def test_first_write_wins(self):
        """Test FWW resolution."""
        updates = [
            {"timestamp": "2026-06-30T10:00:02", "value": "A"},
            {"timestamp": "2026-06-30T10:00:00", "value": "B"},
            {"timestamp": "2026-06-30T10:00:01", "value": "C"},
        ]
        
        winner = ConflictResolver.first_write_wins(updates)
        assert winner["value"] == "B"
    
    def test_merge_non_overlapping(self):
        """Test merging non-overlapping updates."""
        updates = [
            {"key1": "value1", "timestamp": "2026-06-30T10:00:00"},
            {"key2": "value2", "timestamp": "2026-06-30T10:00:01"},
            {"key3": "value3", "timestamp": "2026-06-30T10:00:02"},
        ]
        
        merged = ConflictResolver.merge_non_overlapping(updates)
        
        assert "key1" in merged
        assert "key2" in merged
        assert "key3" in merged


# ============================================================================
# Tests: Concurrent Scenarios
# ============================================================================

class TestConcurrentScenarios:
    """Test concurrent update scenarios."""
    
    @pytest.mark.asyncio
    async def test_scenario_shared_state_conflict(self):
        """Test conflict in shared state scenario."""
        state = SharedGlobalStateManager()
        
        async def agent_a():
            state.write_state("task1", "key1", "A", agent_id="A")
        
        async def agent_b():
            await asyncio.sleep(0.001)
            state.write_state("task1", "key1", "B", agent_id="B")
        
        await asyncio.gather(agent_a(), agent_b())
        
        result = state.read_state("task1", "key1")
        assert result.value in ["A", "B"]
        assert result.version == 2
    
    @pytest.mark.asyncio
    async def test_scenario_event_bus_no_locks(self):
        """Test event bus handles concurrent writes without locks."""
        bus = EventBusManager()
        
        async def agent_a():
            event = Event("e1", datetime.now().isoformat(), "task1", "A",
                         "state_written", "key1", "A")
            bus.publish_event(event)
        
        async def agent_b():
            await asyncio.sleep(0.0001)
            event = Event("e2", datetime.now().isoformat(), "task1", "B",
                         "state_written", "key1", "B")
            bus.publish_event(event)
        
        await asyncio.gather(agent_a(), agent_b())
        
        # Both events in log
        assert len(bus.event_log) == 2


# ============================================================================
# Tests: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_state(self, shared_state):
        """Test reading from empty state."""
        result = shared_state.read_state("nonexistent", "nonexistent")
        assert result is None
    
    def test_large_values(self, shared_state):
        """Test storing large values."""
        large_value = "x" * 1000000  # 1MB
        shared_state.write_state("task1", "large", large_value)
        
        result = shared_state.read_state("task1", "large")
        assert len(result.value) == 1000000
    
    def test_special_characters(self, shared_state):
        """Test special characters in values."""
        special_value = "测试 😀 \n\t\r 💻"
        shared_state.write_state("task1", "special", special_value)
        
        result = shared_state.read_state("task1", "special")
        assert result.value == special_value
    
    def test_event_bus_empty_log(self, event_bus):
        """Test event bus operations on empty log."""
        history = event_bus.get_event_history("nonexistent")
        assert len(history) == 0
    
    def test_event_bus_state_at_future_time(self, event_bus):
        """Test state at time in future."""
        event = Event("e1", "2026-06-30T10:00:00", "task1", "A",
                     "state_written", "key1", "v1")
        event_bus.publish_event(event)
        
        # Query at future time
        state = event_bus.compute_state_at_time("task1", "2030-01-01T00:00:00")
        
        # Should include the event
        assert state["key1"] == "v1"


# ============================================================================
# Tests: Performance
# ============================================================================

class TestPerformance:
    """Performance tests."""
    
    @pytest.mark.slow
    def test_shared_state_write_throughput(self, shared_state):
        """Test write throughput for shared state."""
        import time
        
        start = time.time()
        for i in range(1000):
            shared_state.write_state("task1", f"key_{i}", f"value_{i}")
        elapsed = time.time() - start
        
        # Should be fast (all in-memory)
        assert elapsed < 1.0
        assert len(shared_state.get_all_state("task1")) == 1000
    
    @pytest.mark.slow
    def test_event_bus_throughput(self, event_bus):
        """Test event publishing throughput."""
        import time
        
        start = time.time()
        for i in range(1000):
            event = Event(
                event_id=f"e{i}",
                timestamp=datetime.now().isoformat(),
                task_id="task1",
                agent_id="A1",
                event_type="state_written",
                key="key1",
                value=f"v{i}"
            )
            event_bus.publish_event(event)
        elapsed = time.time() - start
        
        # Should be reasonably fast
        assert elapsed < 2.0
        assert len(event_bus.event_log) == 1000
    
    @pytest.mark.slow
    def test_event_replay_performance(self, event_bus):
        """Test event replay performance."""
        import time
        
        # Publish many events
        for i in range(1000):
            event = Event(
                event_id=f"e{i}",
                timestamp=datetime.now().isoformat(),
                task_id="task1",
                agent_id="A1",
                event_type="state_written",
                key=f"key_{i % 10}",
                value=f"v{i}"
            )
            event_bus.publish_event(event)
        
        # Time replay
        start = time.time()
        state = event_bus.replay_events_for_task("task1")
        elapsed = time.time() - start
        
        # Should be fast
        assert elapsed < 0.5
        assert len(state) == 10  # 10 unique keys


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
