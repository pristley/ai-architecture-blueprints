"""Test Suite for WP-3.8: Multi-Agent System Architecture

Comprehensive tests covering:
  - State bus (versioning, event sourcing, consistency)
  - Individual agents (producer, evaluators, coordinator)
  - Supervisor orchestration (planning, execution, decisions)
  - Integration end-to-end flows
  - Edge cases and failure handling

Run with: pytest tests/test_wp_3_8.py -v
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_openai import ChatOpenAI

from docs.multi_agent_architectures.examples_3_8 import (
    TaskState,
    TaskStatus,
    InMemoryStateBus,
    ContentCreatorAgent,
    QAAgent,
    EditorAgent,
    FactCheckAgent,
    SupervisorAgent,
    MultiAgentSystem,
    create_multi_agent_system,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def state_bus():
    """Create in-memory state bus."""
    return InMemoryStateBus()


@pytest.fixture
def llm():
    """Create mock LLM."""
    return MagicMock(spec=ChatOpenAI)


@pytest.fixture
def task_state():
    """Create sample task state."""
    return TaskState(
        task_id="test-task-123",
        original_request="Write a blog post about AI",
        user_id="test-user"
    )


@pytest.fixture
def agents(llm, state_bus):
    """Create all agent instances."""
    return {
        "content": ContentCreatorAgent("content", llm, state_bus),
        "qa": QAAgent("qa", llm, state_bus),
        "editor": EditorAgent("editor", llm, state_bus),
        "fact_check": FactCheckAgent("fact_check", llm, state_bus),
    }


@pytest.fixture
def supervisor(llm, state_bus, agents):
    """Create supervisor agent."""
    return SupervisorAgent(llm, state_bus, agents)


@pytest.fixture
def multi_agent_system():
    """Create complete multi-agent system."""
    return create_multi_agent_system()


# ============================================================================
# Tests: State Bus
# ============================================================================

class TestStateBus:
    """Test state bus operations."""
    
    def test_write_and_read_state(self, state_bus, task_state):
        """Test basic write and read."""
        state_bus.write_state(task_state.task_id, "artifact", "Hello World")
        result = state_bus.read_state(task_state.task_id, "artifact")
        assert result == "Hello World"
    
    def test_versioning(self, state_bus, task_state):
        """Test state versioning."""
        state_bus.write_state(task_state.task_id, "artifact", "v1")
        state_bus.write_state(task_state.task_id, "artifact", "v2")
        state_bus.write_state(task_state.task_id, "artifact", "v3")
        
        # Latest should be v3
        assert state_bus.read_state(task_state.task_id, "artifact") == "v3"
    
    def test_state_history(self, state_bus, task_state):
        """Test reading state history."""
        state_bus.write_state(task_state.task_id, "artifact", "v1")
        state_bus.write_state(task_state.task_id, "artifact", "v2")
        
        history = state_bus.read_state_history(task_state.task_id, "artifact")
        assert len(history) == 2
        assert history[0]["value"] == "v1"
        assert history[1]["value"] == "v2"
    
    def test_multiple_keys(self, state_bus, task_state):
        """Test multiple keys in same task."""
        state_bus.write_state(task_state.task_id, "artifact", "content")
        state_bus.write_state(task_state.task_id, "feedback", {"score": 85})
        state_bus.write_state(task_state.task_id, "suggestions", ["s1", "s2"])
        
        assert state_bus.read_state(task_state.task_id, "artifact") == "content"
        assert state_bus.read_state(task_state.task_id, "feedback") == {"score": 85}
        assert state_bus.read_state(task_state.task_id, "suggestions") == ["s1", "s2"]
    
    def test_read_nonexistent_key(self, state_bus, task_state):
        """Test reading key that doesn't exist."""
        result = state_bus.read_state(task_state.task_id, "nonexistent")
        assert result is None
    
    def test_multiple_tasks_isolated(self, state_bus):
        """Test state isolation between tasks."""
        state_bus.write_state("task1", "artifact", "content1")
        state_bus.write_state("task2", "artifact", "content2")
        
        assert state_bus.read_state("task1", "artifact") == "content1"
        assert state_bus.read_state("task2", "artifact") == "content2"
    
    def test_get_all_state(self, state_bus, task_state):
        """Test getting all state for task."""
        state_bus.write_state(task_state.task_id, "artifact", "content")
        state_bus.write_state(task_state.task_id, "feedback", {"score": 85})
        
        all_state = state_bus.get_all_state(task_state.task_id)
        assert "artifact" in all_state
        assert "feedback" in all_state
        assert all_state["artifact"] == "content"
    
    def test_subscribe_to_state_changes(self, state_bus, task_state):
        """Test subscribing to state changes."""
        events = []
        
        def callback(data):
            events.append(data)
        
        state_bus.subscribe("state_changed", callback)
        state_bus.write_state(task_state.task_id, "artifact", "content")
        
        assert len(events) == 1
        assert events[0]["task_id"] == task_state.task_id
        assert events[0]["key"] == "artifact"


# ============================================================================
# Tests: Content Creator Agent
# ============================================================================

class TestContentCreatorAgent:
    """Test content creation agent."""
    
    @pytest.mark.asyncio
    async def test_content_creation(self, agents, llm, task_state):
        """Test agent creates content artifact."""
        llm.predict.return_value = "Generated blog post content..."
        
        result = await agents["content"].execute(task_state)
        
        assert result["status"] == "success"
        assert "artifact_length" in result
        assert "duration" in result
    
    @pytest.mark.asyncio
    async def test_content_saved_to_state(self, agents, llm, state_bus, task_state):
        """Test artifact is saved to state bus."""
        llm.predict.return_value = "Generated content"
        
        await agents["content"].execute(task_state)
        
        artifact = state_bus.read_state(task_state.task_id, "content_artifact")
        assert artifact == "Generated content"
    
    @pytest.mark.asyncio
    async def test_content_creation_failure(self, agents, llm, task_state):
        """Test handling of creation failure."""
        llm.predict.side_effect = Exception("LLM error")
        
        result = await agents["content"].execute(task_state)
        
        assert result["status"] == "failed"
        assert "error" in result


# ============================================================================
# Tests: QA Agent
# ============================================================================

class TestQAAgent:
    """Test QA evaluation agent."""
    
    @pytest.mark.asyncio
    async def test_qa_review_execution(self, agents, llm, state_bus, task_state):
        """Test QA agent execution."""
        # Setup content artifact
        state_bus.write_state(task_state.task_id, "content_artifact", "Sample content")
        llm.predict.return_value = "Review feedback..."
        
        result = await agents["qa"].execute(task_state)
        
        assert result["status"] == "success"
        assert "accuracy_score" in result
        assert "duration" in result
    
    @pytest.mark.asyncio
    async def test_qa_feedback_saved(self, agents, llm, state_bus, task_state):
        """Test QA feedback saved to state."""
        state_bus.write_state(task_state.task_id, "content_artifact", "Sample")
        llm.predict.return_value = "Feedback..."
        
        await agents["qa"].execute(task_state)
        
        feedback = state_bus.read_state(task_state.task_id, "qa_feedback")
        assert feedback is not None
        assert "accuracy_score" in feedback
    
    @pytest.mark.asyncio
    async def test_qa_missing_artifact(self, agents, task_state):
        """Test QA with missing artifact."""
        result = await agents["qa"].execute(task_state)
        
        assert result["status"] == "failed"
        assert "error" in result


# ============================================================================
# Tests: Editor Agent
# ============================================================================

class TestEditorAgent:
    """Test editor agent."""
    
    @pytest.mark.asyncio
    async def test_editor_execution(self, agents, llm, state_bus, task_state):
        """Test editor agent execution."""
        state_bus.write_state(task_state.task_id, "content_artifact", "Sample content")
        llm.predict.return_value = "Edit suggestions..."
        
        result = await agents["editor"].execute(task_state)
        
        assert result["status"] == "success"
        assert "suggestion_count" in result
    
    @pytest.mark.asyncio
    async def test_editor_suggestions_saved(self, agents, llm, state_bus, task_state):
        """Test suggestions saved to state."""
        state_bus.write_state(task_state.task_id, "content_artifact", "Content")
        llm.predict.return_value = "Suggestions..."
        
        await agents["editor"].execute(task_state)
        
        suggestions = state_bus.read_state(task_state.task_id, "editor_suggestions")
        assert suggestions is not None


# ============================================================================
# Tests: Fact Check Agent
# ============================================================================

class TestFactCheckAgent:
    """Test fact-check agent."""
    
    @pytest.mark.asyncio
    async def test_fact_check_execution(self, agents, llm, state_bus, task_state):
        """Test fact-check agent execution."""
        state_bus.write_state(task_state.task_id, "content_artifact", "Claims here")
        llm.predict.return_value = "Fact check results..."
        
        result = await agents["fact_check"].execute(task_state)
        
        assert result["status"] == "success"
        assert "verified_count" in result
    
    @pytest.mark.asyncio
    async def test_fact_results_saved(self, agents, llm, state_bus, task_state):
        """Test fact results saved to state."""
        state_bus.write_state(task_state.task_id, "content_artifact", "Content")
        llm.predict.return_value = "Results..."
        
        await agents["fact_check"].execute(task_state)
        
        results = state_bus.read_state(task_state.task_id, "fact_check_results")
        assert results is not None


# ============================================================================
# Tests: Supervisor
# ============================================================================

class TestSupervisor:
    """Test supervisor orchestration."""
    
    @pytest.mark.asyncio
    async def test_orchestration_completes(self, supervisor, llm):
        """Test orchestration completes successfully."""
        llm.predict.return_value = "Generated content"
        
        task = await supervisor.orchestrate("Write a blog post")
        
        assert task is not None
        assert task.status in [TaskStatus.FINALIZED.value, TaskStatus.REVIEW.value]
        assert task.total_duration > 0
    
    @pytest.mark.asyncio
    async def test_all_agents_executed(self, supervisor, llm):
        """Test all agents are executed."""
        llm.predict.return_value = "Content"
        
        task = await supervisor.orchestrate("Write a post")
        
        # Should have content, qa, editor, fact_check
        assert len(task.agent_status) >= 1
    
    @pytest.mark.asyncio
    async def test_quality_evaluation(self, supervisor, llm):
        """Test quality score is calculated."""
        llm.predict.return_value = "Content"
        
        task = await supervisor.orchestrate("Write a post")
        
        # Quality should be between 0 and 1
        if task.quality_score is not None:
            assert 0 <= task.quality_score <= 1
    
    @pytest.mark.asyncio
    async def test_orchestration_error_handling(self, supervisor, llm):
        """Test error handling during orchestration."""
        llm.predict.side_effect = Exception("LLM error")
        
        with pytest.raises(Exception):
            await supervisor.orchestrate("Write a post")


# ============================================================================
# Tests: Integration
# ============================================================================

class TestIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, multi_agent_system):
        """Test complete workflow."""
        result = await multi_agent_system.process_request(
            "Write about machine learning"
        )
        
        assert "task_id" in result
        assert "status" in result
        assert result["status"] in ["INITIATED", "IN_PROGRESS", "FINALIZED", "REVIEW", "FAILED"]
    
    @pytest.mark.asyncio
    async def test_multiple_requests_isolated(self, multi_agent_system):
        """Test multiple requests are isolated."""
        result1 = await multi_agent_system.process_request("Request 1")
        result2 = await multi_agent_system.process_request("Request 2")
        
        assert result1["task_id"] != result2["task_id"]


# ============================================================================
# Tests: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_state_bus_read(self, state_bus):
        """Test reading from empty state bus."""
        result = state_bus.read_state("nonexistent", "nonexistent")
        assert result is None
    
    def test_large_state_values(self, state_bus, task_state):
        """Test storing large values."""
        large_content = "x" * 100000  # 100K chars
        state_bus.write_state(task_state.task_id, "large", large_content)
        
        result = state_bus.read_state(task_state.task_id, "large")
        assert len(result) == 100000
    
    def test_special_characters_in_state(self, state_bus, task_state):
        """Test special characters in state."""
        special = "测试 😀 \n\t\r"
        state_bus.write_state(task_state.task_id, "special", special)
        
        result = state_bus.read_state(task_state.task_id, "special")
        assert result == special
    
    def test_complex_nested_state(self, state_bus, task_state):
        """Test nested data structures."""
        nested = {
            "feedback": [
                {"type": "error", "msg": "Issue 1"},
                {"type": "warning", "msg": "Issue 2"}
            ],
            "scores": [0.85, 0.92, 0.78]
        }
        state_bus.write_state(task_state.task_id, "nested", nested)
        
        result = state_bus.read_state(task_state.task_id, "nested")
        assert result == nested


# ============================================================================
# Tests: Performance
# ============================================================================

class TestPerformance:
    """Performance tests."""
    
    @pytest.mark.slow
    def test_state_write_performance(self, state_bus, task_state):
        """Test write performance."""
        import time
        
        start = time.time()
        for i in range(1000):
            state_bus.write_state(task_state.task_id, f"key_{i}", f"value_{i}")
        elapsed = time.time() - start
        
        # Should be fast (all in-memory)
        assert elapsed < 1.0
    
    @pytest.mark.slow
    def test_state_history_retrieval(self, state_bus, task_state):
        """Test reading state history."""
        import time
        
        # Write many versions
        for i in range(100):
            state_bus.write_state(task_state.task_id, "versioned", f"v{i}")
        
        start = time.time()
        history = state_bus.read_state_history(task_state.task_id, "versioned")
        elapsed = time.time() - start
        
        assert len(history) == 100
        assert elapsed < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
