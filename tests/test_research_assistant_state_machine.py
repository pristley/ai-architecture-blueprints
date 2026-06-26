"""
Test suite for Research Assistant State Machine.

Tests cover:
- State transitions (valid and invalid)
- Infinite loop detection (all mechanisms)
- Tool execution with state management
- Complete research workflows
- Error handling and recovery
"""

import pytest
from datetime import datetime
from research_assistant_state_machine import (
    AgentState,
    ResearchState,
    ResearchAssistant,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def fresh_state():
    """Create a fresh ResearchState for testing."""
    return ResearchState(query="test query")


@pytest.fixture
def fresh_assistant(fresh_state):
    """Create a fresh ResearchAssistant for testing."""
    return ResearchAssistant(fresh_state)


# ============================================================================
# STATE MACHINE: VALID TRANSITIONS
# ============================================================================

class TestValidTransitions:
    """Test that valid state transitions are allowed."""
    
    def test_idle_to_planning(self, fresh_state):
        """IDLE should transition to PLANNING."""
        assert fresh_state.can_transition(AgentState.PLANNING)
    
    def test_idle_invalid_transitions(self, fresh_state):
        """IDLE should not transition to SEARCHING/SYNTHESIZING/CITING."""
        assert not fresh_state.can_transition(AgentState.SEARCHING)
        assert not fresh_state.can_transition(AgentState.SYNTHESIZING)
        assert not fresh_state.can_transition(AgentState.CITING)
    
    def test_planning_can_refine(self, fresh_state):
        """PLANNING should allow self-loop for refinement."""
        fresh_state.state = AgentState.PLANNING
        assert fresh_state.can_transition(AgentState.PLANNING)
    
    def test_planning_to_searching(self, fresh_state):
        """PLANNING should transition to SEARCHING."""
        fresh_state.state = AgentState.PLANNING
        assert fresh_state.can_transition(AgentState.SEARCHING)
    
    def test_planning_to_idle_on_error(self, fresh_state):
        """PLANNING should transition to IDLE on error."""
        fresh_state.state = AgentState.PLANNING
        assert fresh_state.can_transition(AgentState.IDLE)
    
    def test_searching_can_continue(self, fresh_state):
        """SEARCHING should allow self-loop."""
        fresh_state.state = AgentState.SEARCHING
        assert fresh_state.can_transition(AgentState.SEARCHING)
    
    def test_searching_to_synthesizing(self, fresh_state):
        """SEARCHING should transition to SYNTHESIZING."""
        fresh_state.state = AgentState.SEARCHING
        assert fresh_state.can_transition(AgentState.SYNTHESIZING)
    
    def test_synthesizing_can_refine(self, fresh_state):
        """SYNTHESIZING should allow self-loop for refinement."""
        fresh_state.state = AgentState.SYNTHESIZING
        assert fresh_state.can_transition(AgentState.SYNTHESIZING)
    
    def test_synthesizing_to_citing(self, fresh_state):
        """SYNTHESIZING should transition to CITING."""
        fresh_state.state = AgentState.SYNTHESIZING
        assert fresh_state.can_transition(AgentState.CITING)
    
    def test_synthesizing_back_to_searching(self, fresh_state):
        """SYNTHESIZING should allow backward transition to SEARCHING for more info."""
        fresh_state.state = AgentState.SYNTHESIZING
        assert fresh_state.can_transition(AgentState.SEARCHING)
    
    def test_citing_can_verify(self, fresh_state):
        """CITING should allow self-loop for verification."""
        fresh_state.state = AgentState.CITING
        assert fresh_state.can_transition(AgentState.CITING)
    
    def test_citing_back_to_synthesizing(self, fresh_state):
        """CITING should allow backward transition if citations missing."""
        fresh_state.state = AgentState.CITING
        assert fresh_state.can_transition(AgentState.SYNTHESIZING)


# ============================================================================
# LOOP DETECTION: STEP LIMIT
# ============================================================================

class TestLoopDetectionStepLimit:
    """Test step limit loop detection."""
    
    def test_step_limit_not_exceeded(self, fresh_state):
        """Should not detect loop when steps are below limit."""
        fresh_state.step_count = fresh_state.MAX_STEPS - 1
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert not in_loop
    
    def test_step_limit_at_boundary(self, fresh_state):
        """Should not detect loop exactly at limit."""
        fresh_state.step_count = fresh_state.MAX_STEPS
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert not in_loop
    
    def test_step_limit_exceeded(self, fresh_state):
        """Should detect loop when steps exceed limit."""
        fresh_state.step_count = fresh_state.MAX_STEPS + 1
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert in_loop
        assert "Step limit" in reason


# ============================================================================
# LOOP DETECTION: SAME STATE REPEAT
# ============================================================================

class TestLoopDetectionSameStateRepeat:
    """Test same-state repetition loop detection."""
    
    def test_no_repeat_detected_with_short_history(self, fresh_state):
        """Should not detect repeat with less than MAX_SAME_STATE_REPEATS items."""
        fresh_state.state_history = [AgentState.PLANNING]
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert not in_loop
    
    def test_no_repeat_different_states(self, fresh_state):
        """Should not detect repeat when states differ."""
        fresh_state.state_history = [
            AgentState.PLANNING,
            AgentState.SEARCHING,
            AgentState.PLANNING,
        ]
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert not in_loop
    
    def test_repeat_detected_same_state_3x(self, fresh_state):
        """Should detect repeat when same state appears 3+ times in a row."""
        fresh_state.state_history = [
            AgentState.PLANNING,
            AgentState.PLANNING,
            AgentState.PLANNING,
        ]
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert in_loop
        assert "repeated" in reason.lower()
    
    def test_repeat_detected_searching_3x(self, fresh_state):
        """Should detect repeat in SEARCHING state."""
        fresh_state.state = AgentState.SEARCHING
        fresh_state.state_history = [
            AgentState.SEARCHING,
            AgentState.SEARCHING,
            AgentState.SEARCHING,
        ]
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert in_loop
        assert "SEARCHING" in reason


# ============================================================================
# LOOP DETECTION: SEARCH REPEATS
# ============================================================================

class TestLoopDetectionSearchRepeats:
    """Test redundant search detection."""
    
    def test_no_loop_new_searches(self, fresh_state):
        """Should not detect loop with reasonable search counts."""
        fresh_state.search_count_by_query = {
            "topic 1": 1,
            "topic 2": 2,
            "topic 3": 1,
        }
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert not in_loop
    
    def test_no_loop_at_max_search_limit(self, fresh_state):
        """Should not detect loop exactly at search limit."""
        fresh_state.search_count_by_query = {
            "topic 1": fresh_state.MAX_SEARCHES_PER_QUERY
        }
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert not in_loop
    
    def test_loop_detected_search_exceeds_limit(self, fresh_state):
        """Should detect loop when search count exceeds limit."""
        fresh_state.search_count_by_query = {
            "quantum computing": fresh_state.MAX_SEARCHES_PER_QUERY + 1
        }
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert in_loop
        assert "quantum computing" in reason
        assert "searched" in reason.lower()
    
    def test_loop_detected_multiple_queries_exceed_limit(self, fresh_state):
        """Should detect loop for any query exceeding limit."""
        fresh_state.search_count_by_query = {
            "topic 1": 2,
            "topic 2": 10,  # Exceeds limit
            "topic 3": 1,
        }
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert in_loop
        assert "topic 2" in reason


# ============================================================================
# LOOP DETECTION: PLANNING CYCLES
# ============================================================================

class TestLoopDetectionPlanningCycles:
    """Test planning cycle limit detection."""
    
    def test_no_loop_within_planning_limit(self, fresh_state):
        """Should not detect loop within planning cycle limit."""
        fresh_state.state_history = [AgentState.PLANNING, AgentState.PLANNING]
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert not in_loop
    
    def test_loop_detected_planning_exceeds_limit(self, fresh_state):
        """Should detect loop when planning cycles exceed limit."""
        # Create history with more planning cycles than allowed
        fresh_state.state_history = [
            AgentState.PLANNING,
            AgentState.PLANNING,
            AgentState.PLANNING,  # Exceeds MAX_PLANNING_CYCLES
        ]
        in_loop, reason = fresh_state.is_in_infinite_loop()
        assert in_loop
        assert "PLANNING" in reason


# ============================================================================
# STATE TRANSITIONS: Recording
# ============================================================================

class TestStateTransitionRecording:
    """Test that state transitions are properly recorded."""
    
    def test_record_valid_transition(self, fresh_state):
        """Should record valid transition."""
        initial_steps = fresh_state.step_count
        success = fresh_state.record_action(AgentState.PLANNING, "started planning")
        
        assert success
        assert fresh_state.state == AgentState.PLANNING
        assert fresh_state.step_count == initial_steps + 1
        assert fresh_state.last_action == "started planning"
        assert AgentState.IDLE in fresh_state.state_history
    
    def test_reject_invalid_transition(self, fresh_state):
        """Should reject invalid transition."""
        success = fresh_state.record_action(AgentState.SEARCHING, "invalid action")
        
        assert not success
        assert fresh_state.state == AgentState.IDLE
        assert len(fresh_state.errors) > 0
    
    def test_reject_transition_if_looping(self, fresh_state):
        """Should reject transition if would cause loop."""
        # Set up loop condition
        fresh_state.step_count = fresh_state.MAX_STEPS + 1
        
        success = fresh_state.record_action(AgentState.PLANNING, "action")
        
        assert not success
        assert fresh_state.state == AgentState.IDLE
        assert len(fresh_state.errors) > 0


# ============================================================================
# TOOLS: PLAN TOOL
# ============================================================================

class TestPlanTool:
    """Test plan_tool execution."""
    
    def test_plan_from_idle(self, fresh_assistant):
        """Should create plan from IDLE state."""
        result = fresh_assistant.plan_tool()
        
        assert "error" not in result
        assert len(fresh_assistant.state.plan) > 0
        assert fresh_assistant.state.state == AgentState.PLANNING
    
    def test_plan_from_non_idle_fails(self, fresh_assistant):
        """Should fail to plan from non-IDLE state."""
        fresh_assistant.state.state = AgentState.PLANNING
        
        result = fresh_assistant.plan_tool()
        
        assert "error" in result
        assert fresh_assistant.state.state == AgentState.PLANNING


# ============================================================================
# TOOLS: SEARCH TOOL
# ============================================================================

class TestSearchTool:
    """Test search_tool execution."""
    
    def test_search_from_planning(self, fresh_assistant):
        """Should search from PLANNING state."""
        fresh_assistant.state.state = AgentState.PLANNING
        
        result = fresh_assistant.search_tool("test query")
        
        assert "error" not in result
        assert fresh_assistant.state.state == AgentState.SEARCHING
        assert "test query" in fresh_assistant.state.search_results
    
    def test_search_duplicate_limit_prevention(self, fresh_assistant):
        """Should prevent searching the same query more than limit."""
        fresh_assistant.state.state = AgentState.SEARCHING
        fresh_assistant.state.search_count_by_query["test"] = (
            fresh_assistant.state.MAX_SEARCHES_PER_QUERY
        )
        
        result = fresh_assistant.search_tool("test")
        
        assert "error" in result
        assert "Already searched" in result["error"]
    
    def test_search_from_invalid_state_fails(self, fresh_assistant):
        """Should fail to search from IDLE state."""
        fresh_assistant.state.state = AgentState.IDLE
        
        result = fresh_assistant.search_tool("test query")
        
        assert "error" in result


# ============================================================================
# TOOLS: SYNTHESIS TOOL
# ============================================================================

class TestSynthesizeTool:
    """Test synthesize_tool execution."""
    
    def test_synthesize_from_searching(self, fresh_assistant):
        """Should synthesize from SEARCHING state."""
        fresh_assistant.state.state = AgentState.SEARCHING
        fresh_assistant.state.search_results = {
            "topic": ["Result 1", "Result 2"]
        }
        
        result = fresh_assistant.synthesize_tool()
        
        assert "error" not in result
        assert fresh_assistant.state.state == AgentState.SYNTHESIZING
        assert len(fresh_assistant.state.synthesis) > 0
    
    def test_synthesize_requires_results(self, fresh_assistant):
        """Should fail to synthesize without search results."""
        fresh_assistant.state.state = AgentState.SEARCHING
        fresh_assistant.state.search_results = {}
        
        result = fresh_assistant.synthesize_tool()
        
        assert "error" in result


# ============================================================================
# TOOLS: CITATION TOOL
# ============================================================================

class TestCiteTool:
    """Test cite_tool execution."""
    
    def test_cite_from_synthesizing(self, fresh_assistant):
        """Should add citations from SYNTHESIZING state."""
        fresh_assistant.state.state = AgentState.SYNTHESIZING
        fresh_assistant.state.synthesis = "This is a synthesis."
        fresh_assistant.state.search_results = {"topic": ["Result 1"]}
        
        result = fresh_assistant.cite_tool()
        
        assert "error" not in result
        assert fresh_assistant.state.state == AgentState.CITING
        assert len(fresh_assistant.state.citations) > 0
    
    def test_cite_from_invalid_state_fails(self, fresh_assistant):
        """Should fail to cite from non-SYNTHESIZING state."""
        fresh_assistant.state.state = AgentState.SEARCHING
        
        result = fresh_assistant.cite_tool()
        
        assert "error" in result


# ============================================================================
# COMPLETE WORKFLOWS
# ============================================================================

class TestCompleteWorkflows:
    """Test complete research workflows."""
    
    def test_happy_path_workflow(self, fresh_assistant):
        """Should complete full IDLE→PLANNING→SEARCHING→SYNTHESIZING→CITING."""
        # Step 1: Plan
        result = fresh_assistant.plan_tool()
        assert "error" not in result
        assert fresh_assistant.state.state == AgentState.PLANNING
        
        # Step 2: Search
        result = fresh_assistant.search_tool("research topic")
        assert "error" not in result
        assert fresh_assistant.state.state == AgentState.SEARCHING
        
        # Step 3: Synthesize
        result = fresh_assistant.synthesize_tool()
        assert "error" not in result
        assert fresh_assistant.state.state == AgentState.SYNTHESIZING
        
        # Step 4: Cite
        result = fresh_assistant.cite_tool()
        assert "error" not in result
        assert fresh_assistant.state.state == AgentState.CITING
        
        # Verify complete state
        assert fresh_assistant.state.step_count == 4
        assert len(fresh_assistant.state.citations) > 0
    
    def test_workflow_stops_on_error(self, fresh_assistant):
        """Should stop workflow if error occurs."""
        # Try to plan twice (should fail second time)
        result1 = fresh_assistant.plan_tool()
        assert "error" not in result1
        
        result2 = fresh_assistant.plan_tool()
        assert "error" in result2


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_query(self):
        """Should handle empty query."""
        state = ResearchState(query="")
        assert state.query == ""
        assert state.state == AgentState.IDLE
    
    def test_very_long_query(self):
        """Should handle very long query."""
        long_query = "x" * 10000
        state = ResearchState(query=long_query)
        assert state.query == long_query
    
    def test_session_id_uniqueness(self):
        """Should generate unique session IDs."""
        state1 = ResearchState(query="test")
        state2 = ResearchState(query="test")
        assert state1.session_id != state2.session_id
    
    def test_get_status_string(self, fresh_state):
        """Should generate readable status string."""
        status = fresh_state.get_status()
        assert "State" in status
        assert "Step" in status
        assert "IDLE" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
