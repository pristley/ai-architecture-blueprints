"""
Test Suite for WP-2.2: State Management in Single-Agent Loop

Comprehensive tests validating:
1. State object functionality (Pydantic model)
2. State transition validation
3. Infinite loop detection mechanisms
4. Loop guard effectiveness
5. Agent workflow completeness
6. Edge cases and error conditions

Run with: pytest tests/test_wp_2_2.py -v
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples_2_2 import (
    ResearchState,
    LoopGuard,
    ResearchAssistant,
    research_agent_with_state,
)


# ============================================================================
# PART 1: STATE OBJECT TESTS
# ============================================================================

class TestResearchState:
    """Tests for ResearchState Pydantic model."""
    
    def test_state_creation(self):
        """Test creating a new state."""
        state = ResearchState(query="Test query")
        assert state.query == "Test query"
        assert state.state == "IDLE"
        assert state.step_count == 0
        assert state.state_history == []
        assert state.session_id is not None
    
    def test_state_fields(self):
        """Test all state fields are accessible."""
        state = ResearchState(query="Test")
        
        assert isinstance(state.plan, list)
        assert isinstance(state.search_results, dict)
        assert isinstance(state.search_count_by_query, dict)
        assert isinstance(state.citations, list)
        assert isinstance(state.synthesis, str)
    
    def test_state_limits(self):
        """Test that state limits are defined."""
        state = ResearchState(query="Test")
        assert state.MAX_STEPS > 0
        assert state.MAX_CONSECUTIVE_SAME_STATE > 0
        assert state.MAX_SEARCHES_PER_QUERY > 0


# ============================================================================
# PART 2: TRANSITION VALIDATION TESTS
# ============================================================================

class TestStateTransitions:
    """Tests for state transition validation."""
    
    def test_idle_to_planning(self):
        """Test IDLE → PLANNING transition."""
        state = ResearchState(query="Test")
        assert state.can_transition("PLANNING") == True
    
    def test_invalid_transition_from_idle(self):
        """Test that invalid transitions from IDLE are blocked."""
        state = ResearchState(query="Test")
        assert state.can_transition("SEARCHING") == False
        assert state.can_transition("CITING") == False
    
    def test_planning_transitions(self):
        """Test valid transitions from PLANNING."""
        state = ResearchState(query="Test", state="PLANNING")
        assert state.can_transition("PLANNING") == True  # Self-loop
        assert state.can_transition("SEARCHING") == True
        assert state.can_transition("IDLE") == True  # Backward
        assert state.can_transition("CITING") == False  # Invalid
    
    def test_searching_transitions(self):
        """Test valid transitions from SEARCHING."""
        state = ResearchState(query="Test", state="SEARCHING")
        assert state.can_transition("SEARCHING") == True  # Self-loop
        assert state.can_transition("SYNTHESIZING") == True
        assert state.can_transition("IDLE") == True  # Backward
        assert state.can_transition("PLANNING") == False  # Invalid
    
    def test_synthesizing_transitions(self):
        """Test valid transitions from SYNTHESIZING."""
        state = ResearchState(query="Test", state="SYNTHESIZING")
        assert state.can_transition("SYNTHESIZING") == True  # Self-loop
        assert state.can_transition("CITING") == True
        assert state.can_transition("SEARCHING") == True  # Backward
        assert state.can_transition("IDLE") == True  # Backward
        assert state.can_transition("PLANNING") == False  # Invalid
    
    def test_citing_transitions(self):
        """Test valid transitions from CITING."""
        state = ResearchState(query="Test", state="CITING")
        assert state.can_transition("CITING") == True  # Self-loop
        assert state.can_transition("SYNTHESIZING") == True  # Backward
        assert state.can_transition("IDLE") == True  # Backward


# ============================================================================
# PART 3: LOOP DETECTION TESTS
# ============================================================================

class TestLoopDetection:
    """Tests for infinite loop detection."""
    
    def test_step_limit_detection(self):
        """Test detection of exceeded step limit."""
        state = ResearchState(query="Test")
        state.step_count = state.MAX_STEPS + 1
        
        in_loop, reason = state.is_in_infinite_loop()
        assert in_loop == True
        assert "Step limit" in reason
    
    def test_same_state_repeat_detection(self):
        """Test detection of same state repeated excessively."""
        state = ResearchState(query="Test")
        state.state_history = ["SEARCHING"] * (state.MAX_CONSECUTIVE_SAME_STATE + 1)
        
        in_loop, reason = state.is_in_infinite_loop()
        assert in_loop == True
        assert "repeated" in reason.lower()
    
    def test_search_repeat_detection(self):
        """Test detection of same search query repeated excessively."""
        state = ResearchState(query="Test")
        query = "quantum computing"
        state.search_count_by_query[query] = state.MAX_SEARCHES_PER_QUERY + 1
        
        in_loop, reason = state.is_in_infinite_loop()
        assert in_loop == True
        assert query in reason
    
    def test_alternating_pattern_detection(self):
        """Test detection of alternating state pattern."""
        state = ResearchState(query="Test")
        state.state_history = ["PLANNING", "SEARCHING", "PLANNING", "SEARCHING"]
        
        in_loop, reason = state.is_in_infinite_loop()
        assert in_loop == True
        assert "Alternating" in reason or "pattern" in reason.lower()
    
    def test_no_loop_normal_progression(self):
        """Test that normal progression is not flagged as loop."""
        state = ResearchState(query="Test")
        state.state_history = ["IDLE", "PLANNING", "SEARCHING", "SYNTHESIZING"]
        state.step_count = 4
        
        in_loop, reason = state.is_in_infinite_loop()
        assert in_loop == False
    
    def test_no_loop_within_limits(self):
        """Test that valid searches within limits don't trigger loop."""
        state = ResearchState(query="Test")
        state.search_count_by_query = {
            "query1": 3,
            "query2": 2,
        }
        
        in_loop, reason = state.is_in_infinite_loop()
        assert in_loop == False


# ============================================================================
# PART 4: LOOP GUARD TESTS
# ============================================================================

class TestLoopGuard:
    """Tests for LoopGuard class."""
    
    def test_guard_creation(self):
        """Test creating a loop guard."""
        state = ResearchState(query="Test")
        guard = LoopGuard(state)
        assert guard.state == state
        assert len(guard.checks) == 4
    
    def test_guard_detects_step_limit(self):
        """Test guard detects step limit exceeded."""
        state = ResearchState(query="Test")
        state.step_count = state.MAX_STEPS + 5
        guard = LoopGuard(state)
        
        in_loop, reason = guard.is_looping()
        assert in_loop == True
        assert "step_limit" in reason.lower()
    
    def test_guard_detects_search_repeats(self):
        """Test guard detects search repeats."""
        state = ResearchState(query="Test")
        state.search_count_by_query["keyword"] = state.MAX_SEARCHES_PER_QUERY + 2
        guard = LoopGuard(state)
        
        in_loop, reason = guard.is_looping()
        assert in_loop == True
        assert "search" in reason.lower()
    
    def test_guard_allows_normal_execution(self):
        """Test guard doesn't flag normal execution."""
        state = ResearchState(query="Test")
        state.step_count = 5
        state.state_history = ["IDLE", "PLANNING", "SEARCHING"]
        guard = LoopGuard(state)
        
        in_loop, reason = guard.is_looping()
        assert in_loop == False


# ============================================================================
# PART 5: STATE MUTATION TESTS
# ============================================================================

class TestStateMutation:
    """Tests for state transitions and mutations."""
    
    def test_record_action_successful(self):
        """Test successful action recording."""
        state = ResearchState(query="Test")
        
        result = state.record_action("PLANNING", "start_planning")
        assert result == True
        assert state.state == "PLANNING"
        assert state.step_count == 1
        assert "IDLE" in state.state_history
    
    def test_record_action_invalid_transition(self):
        """Test that invalid transitions are rejected."""
        state = ResearchState(query="Test")
        
        result = state.record_action("SEARCHING", "invalid_transition")
        assert result == False
        assert state.state == "IDLE"  # Unchanged
    
    def test_record_action_detects_loop(self):
        """Test that record_action detects loops."""
        state = ResearchState(query="Test")
        state.step_count = state.MAX_STEPS + 1
        
        result = state.record_action("PLANNING", "would_be_valid_transition")
        assert result == False  # Blocked by loop detection
    
    def test_sequential_transitions(self):
        """Test sequence of valid transitions."""
        state = ResearchState(query="Test")
        
        assert state.record_action("PLANNING", "step1")
        assert state.step_count == 1
        
        assert state.record_action("SEARCHING", "step2")
        assert state.step_count == 2
        
        assert state.record_action("SYNTHESIZING", "step3")
        assert state.step_count == 3
        
        assert state.record_action("CITING", "step4")
        assert state.step_count == 4


# ============================================================================
# PART 6: ASSISTANT TOOL TESTS
# ============================================================================

class TestResearchAssistant:
    """Tests for ResearchAssistant tool calls."""
    
    def test_plan_tool_from_idle(self):
        """Test plan tool works from IDLE state."""
        state = ResearchState(query="What is AI?")
        assistant = ResearchAssistant(state)
        
        result = assistant.plan_tool()
        assert result["success"] == True
        assert "plan" in result
        assert len(result["plan"]) > 0
        assert state.state == "PLANNING"
    
    def test_plan_tool_invalid_state(self):
        """Test plan tool fails from non-IDLE state."""
        state = ResearchState(query="Test", state="SEARCHING")
        assistant = ResearchAssistant(state)
        
        result = assistant.plan_tool()
        assert result["success"] == False
        assert "error" in result
    
    def test_search_tool_from_planning(self):
        """Test search tool works from PLANNING state."""
        state = ResearchState(query="Test", state="PLANNING")
        assistant = ResearchAssistant(state)
        
        result = assistant.search_tool("sample query")
        assert result["success"] == True
        assert "results_count" in result
        assert state.state == "SEARCHING"
    
    def test_search_tool_from_searching(self):
        """Test search tool stays in SEARCHING state."""
        state = ResearchState(query="Test", state="SEARCHING")
        assistant = ResearchAssistant(state)
        
        result = assistant.search_tool("sample query")
        assert result["success"] == True
        assert state.state == "SEARCHING"
    
    def test_synthesize_tool(self):
        """Test synthesize tool transitions to SYNTHESIZING."""
        state = ResearchState(query="Test", state="SEARCHING")
        state.search_results = {"query1": ["result1", "result2"]}
        assistant = ResearchAssistant(state)
        
        result = assistant.synthesize_tool()
        assert result["success"] == True
        assert len(state.synthesis) > 0
        assert state.state == "SYNTHESIZING"
    
    def test_cite_tool(self):
        """Test cite tool transitions to CITING."""
        state = ResearchState(query="Test", state="SYNTHESIZING")
        state.search_results = {"query1": ["result1"], "query2": ["result2"]}
        state.synthesis = "Test synthesis"
        assistant = ResearchAssistant(state)
        
        result = assistant.cite_tool()
        assert result["success"] == True
        assert len(state.citations) > 0
        assert state.state == "CITING"


# ============================================================================
# PART 7: INTEGRATION TESTS
# ============================================================================

class TestAgentIntegration:
    """Integration tests for complete agent workflow."""
    
    def test_happy_path_workflow(self):
        """Test complete successful workflow."""
        result = research_agent_with_state("What is AI?", verbose=False)
        
        assert result["success"] == True
        assert result["state_final"] == "CITING"
        assert len(result["citations"]) > 0
        assert len(result["synthesis"]) > 0
        assert result["stats"]["steps_taken"] > 0
    
    def test_workflow_includes_all_phases(self):
        """Test that workflow touches all states."""
        result = research_agent_with_state("Test query", verbose=False)
        
        state_history = result["stats"]["state_history"]
        assert "IDLE" in state_history
        assert "PLANNING" in state_history
        assert "SEARCHING" in state_history
        assert "SYNTHESIZING" in state_history
    
    def test_workflow_within_step_limit(self):
        """Test that workflow completes within step limit."""
        result = research_agent_with_state("Test query", verbose=False)
        
        steps = result["stats"]["steps_taken"]
        assert steps <= 20  # MAX_STEPS
    
    def test_searches_executed(self):
        """Test that searches are actually executed."""
        result = research_agent_with_state("Test query", verbose=False)
        
        searches = result["stats"]["searches_executed"]
        assert searches > 0
    
    def test_session_tracking(self):
        """Test that session IDs are unique."""
        result1 = research_agent_with_state("Query 1", verbose=False)
        result2 = research_agent_with_state("Query 2", verbose=False)
        
        session1 = result1["stats"]["session_id"]
        session2 = result2["stats"]["session_id"]
        assert session1 != session2


# ============================================================================
# PART 8: EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_empty_query(self):
        """Test handling of empty query."""
        state = ResearchState(query="")
        assert state.query == ""
        assert state.state == "IDLE"
    
    def test_state_summary(self):
        """Test state summary generation."""
        state = ResearchState(query="Test")
        summary = state.get_state_summary()
        
        assert "session_id" in summary
        assert "state" in summary
        assert "step_count" in summary
    
    def test_multiple_searches_same_query(self):
        """Test tracking multiple searches of the same query."""
        state = ResearchState(query="Test")
        state.search_count_by_query["query"] = 2
        
        assert state.search_count_by_query["query"] == 2
        in_loop, _ = state.is_in_infinite_loop()
        assert in_loop == False
    
    def test_large_synthesis(self):
        """Test handling of large synthesis text."""
        state = ResearchState(query="Test", state="SYNTHESIZING")
        state.synthesis = "x" * 10000
        
        assert len(state.synthesis) == 10000
        summary = state.get_state_summary()
        assert summary["synthesis_length"] == 10000


# ============================================================================
# PART 9: DOCUMENT VALIDATION TESTS
# ============================================================================

class TestDocumentStructure:
    """Tests for WP-2.2 document structure and completeness."""
    
    def test_document_exists(self):
        """Test that WP-2.2 markdown document exists."""
        doc_path = "WP-2.2-State-Management-in-Single-Agent-Loop.md"
        assert os.path.exists(doc_path)
    
    def test_document_has_content(self):
        """Test that document has substantial content."""
        doc_path = "WP-2.2-State-Management-in-Single-Agent-Loop.md"
        with open(doc_path) as f:
            content = f.read()
        
        assert len(content) > 5000  # Substantial content
        assert "Executive Summary" in content or "Part 1" in content
    
    def test_examples_file_exists(self):
        """Test that examples_2_2.py exists."""
        assert os.path.exists("examples_2_2.py")
    
    def test_examples_importable(self):
        """Test that examples can be imported."""
        from examples_2_2 import (
            ResearchState,
            LoopGuard,
            ResearchAssistant,
            research_agent_with_state,
        )
        assert ResearchState is not None
        assert LoopGuard is not None
        assert ResearchAssistant is not None
        assert research_agent_with_state is not None


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
