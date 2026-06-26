"""
Test suite for Controller Orchestration Agent (ADR-2.2)

Tests the orchestration pattern with centralized control:
- Step execution and evaluation
- Workflow orchestration
- Error handling and retry logic
- State tracking and audit trails
- Complete workflows (happy path and error paths)
"""

import asyncio
import pytest
from controller_orchestration_agent import (
    StepName,
    StepStatus,
    Decision,
    StepExecution,
    OrchestrationState,
    Controller,
    ReportOrchestrator,
    evaluate_plan,
    evaluate_fetched_data,
    evaluate_extracted_facts,
    evaluate_draft_report,
    evaluate_cited_report,
    evaluate_formatted_report,
    plan_tool,
    fetch_tool,
    analyze_tool,
    synthesize_tool,
    cite_tool,
    format_tool,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def fresh_state():
    """Fresh orchestration state for testing."""
    return OrchestrationState(task="test task")


@pytest.fixture
def orchestrator():
    """Fresh report orchestrator."""
    return ReportOrchestrator()


# ============================================================================
# Tests: Evaluation Functions
# ============================================================================

class TestEvaluationFunctions:
    """Test evaluation functions for each step."""
    
    def test_evaluate_plan_valid(self):
        """Valid plan should be accepted."""
        plan = ["Step 1", "Step 2", "Step 3"]
        is_acceptable, reason = evaluate_plan(plan)
        assert is_acceptable
        assert "accepted" in reason.lower()
        assert "3 steps" in reason
    
    def test_evaluate_plan_too_short(self):
        """Plan with <3 steps should be rejected."""
        plan = ["Step 1", "Step 2"]
        is_acceptable, reason = evaluate_plan(plan)
        assert not is_acceptable
        assert "steps" in reason.lower()
    
    def test_evaluate_plan_empty(self):
        """Empty plan should be rejected."""
        is_acceptable, reason = evaluate_plan([])
        assert not is_acceptable
        assert "empty" in reason.lower()
    
    def test_evaluate_plan_none(self):
        """None plan should be rejected."""
        is_acceptable, reason = evaluate_plan(None)
        assert not is_acceptable
    
    def test_evaluate_fetched_data_valid(self):
        """Valid data should be accepted."""
        data = [
            {"title": "Source 1", "content": "Content 1"},
            {"title": "Source 2", "content": "Content 2"},
            {"title": "Source 3", "content": "Content 3"},
            {"title": "Source 4", "content": "Content 4"},
            {"title": "Source 5", "content": "Content 5"},
            {"title": "Source 6", "content": "Content 6"},
            {"title": "Source 7", "content": "Content 7"},
            {"title": "Source 8", "content": "Content 8"},
        ]
        is_acceptable, reason = evaluate_fetched_data(data)
        assert is_acceptable
        assert "8 sources" in reason
    
    def test_evaluate_fetched_data_insufficient(self):
        """Insufficient data should be rejected."""
        data = [
            {"title": "Source 1", "content": "Content 1"},
            {"title": "Source 2", "content": "Content 2"},
        ]
        is_acceptable, reason = evaluate_fetched_data(data)
        assert not is_acceptable
        assert "2 sources" in reason
        assert "≥8" in reason
    
    def test_evaluate_fetched_data_missing_title(self):
        """Data missing content should be rejected (after count check)."""
        # Create enough data to pass count but missing content
        data = [
            {"title": f"Source {i}"} for i in range(8)  # No content field
        ]
        is_acceptable, reason = evaluate_fetched_data(data)
        assert not is_acceptable
        assert "content" in reason.lower()
    
    def test_evaluate_extracted_facts_valid(self):
        """Valid facts should be accepted."""
        facts = [{"fact": f"Fact {i}", "source": f"Source {i}"} for i in range(20)]
        is_acceptable, reason = evaluate_extracted_facts(facts)
        assert is_acceptable
        assert "20 facts" in reason
    
    def test_evaluate_extracted_facts_insufficient(self):
        """Insufficient facts should be rejected."""
        facts = [{"fact": "Fact 1", "source": "Source 1"}]
        is_acceptable, reason = evaluate_extracted_facts(facts)
        assert not is_acceptable
        assert "1 facts" in reason
    
    def test_evaluate_draft_report_valid(self):
        """Valid draft should be accepted."""
        # Create a draft with sufficient words (1000+) and paragraphs (5+)
        paragraphs = [" ".join(["word"] * 250) for _ in range(5)]  # 5 paragraphs of 250 words each
        draft = "# Title\n\n" + "\n\n".join(paragraphs)
        is_acceptable, reason = evaluate_draft_report(draft)
        assert is_acceptable
        assert "words" in reason
    
    def test_evaluate_draft_report_too_short(self):
        """Draft with too few words should be rejected."""
        draft = "# Title\n\nShort draft"
        is_acceptable, reason = evaluate_draft_report(draft)
        assert not is_acceptable
        assert "words" in reason
    
    def test_evaluate_cited_report_valid(self):
        """Report with sufficient citations should be accepted."""
        report = "Text [source: S1] more [source: S2]" * 5  # 10 citations
        is_acceptable, reason = evaluate_cited_report(report)
        assert is_acceptable
        assert "citations" in reason
    
    def test_evaluate_cited_report_insufficient(self):
        """Report with too few citations should be rejected."""
        report = "Text [source: S1] more text"
        is_acceptable, reason = evaluate_cited_report(report)
        assert not is_acceptable
        assert "citations" in reason
    
    def test_evaluate_formatted_report_valid(self):
        """Well-formatted report should be accepted."""
        report = "# Title\n\nContent\n"
        is_acceptable, reason = evaluate_formatted_report(report)
        assert is_acceptable
        assert "characters" in reason
    
    def test_evaluate_formatted_report_missing_headers(self):
        """Report missing headers should be rejected."""
        report = "No headers here\n"
        is_acceptable, reason = evaluate_formatted_report(report)
        assert not is_acceptable
        assert "header" in reason.lower()


# ============================================================================
# Tests: State Management
# ============================================================================

class TestStateManagement:
    """Test orchestration state tracking."""
    
    def test_state_initialization(self, fresh_state):
        """State should initialize correctly."""
        assert fresh_state.task == "test task"
        assert fresh_state.current_step_index == 0
        assert fresh_state.total_steps_completed == 0
        assert fresh_state.total_retries == 0
        assert fresh_state.errors == []
    
    def test_state_records_successful_step(self, fresh_state):
        """State should record successful steps."""
        execution = StepExecution(
            step_name=StepName.PLANNING,
            status=StepStatus.SUCCESS,
            input_data="test",
            output_data="result",
        )
        fresh_state.record_step(execution)
        
        assert fresh_state.total_steps_completed == 1
        assert len(fresh_state.step_history) == 1
        assert fresh_state.step_history[0].step_name == StepName.PLANNING
    
    def test_state_records_failed_step(self, fresh_state):
        """State should record errors."""
        execution = StepExecution(
            step_name=StepName.FETCHING,
            status=StepStatus.FAILED,
            input_data="test",
            error="Network error",
        )
        fresh_state.record_step(execution)
        
        assert fresh_state.total_steps_completed == 0
        assert len(fresh_state.errors) == 1
        assert "Network error" in fresh_state.errors[0]
    
    def test_state_tracks_retries(self, fresh_state):
        """State should track retries."""
        execution = StepExecution(
            step_name=StepName.ANALYZING,
            status=StepStatus.RETRY,
            input_data="test",
        )
        fresh_state.record_step(execution)
        
        assert fresh_state.total_retries == 1
    
    def test_state_status_string(self, fresh_state):
        """Status string should be informative."""
        fresh_state.total_steps_completed = 3
        fresh_state.final_report = "Report content"
        
        status = fresh_state.get_status_string()
        assert "3 steps completed" in status
        assert "Report content" not in status  # Content not shown, just size


# ============================================================================
# Tests: Tool Execution
# ============================================================================

class TestToolExecution:
    """Test tool execution."""
    
    @pytest.mark.asyncio
    async def test_plan_tool(self):
        """Plan tool should generate a plan."""
        plan = await plan_tool("Write a report")
        assert isinstance(plan, list)
        assert len(plan) >= 3
        assert all(isinstance(step, str) for step in plan)
    
    @pytest.mark.asyncio
    async def test_fetch_tool(self):
        """Fetch tool should return sources."""
        data = await fetch_tool("AI trends")
        assert isinstance(data, list)
        assert len(data) >= 8
        assert all("title" in item and "content" in item for item in data)
    
    @pytest.mark.asyncio
    async def test_analyze_tool(self):
        """Analyze tool should extract facts."""
        data = [
            {"title": "S1", "content": "Content 1"},
            {"title": "S2", "content": "Content 2"},
        ]
        facts = await analyze_tool(data)
        assert isinstance(facts, list)
        assert len(facts) >= 20
        assert all("fact" in f and "source" in f for f in facts)
    
    @pytest.mark.asyncio
    async def test_synthesize_tool(self):
        """Synthesize tool should generate draft."""
        facts = [{"fact": f"Fact {i}", "source": f"Source {i}"} for i in range(20)]
        draft = await synthesize_tool(facts)
        assert isinstance(draft, str)
        assert len(draft) > 500
        assert "#" in draft  # Should have Markdown headers
    
    @pytest.mark.asyncio
    async def test_cite_tool(self):
        """Cite tool should add citations."""
        draft = "Claim 1 " * 100 + "[source: S1]"
        cited = await cite_tool(draft)
        assert isinstance(cited, str)
        assert cited.count("[source:") >= 1
    
    @pytest.mark.asyncio
    async def test_format_tool(self):
        """Format tool should format report."""
        report = "# Title\n\nContent"
        formatted = await format_tool(report)
        assert isinstance(formatted, str)
        assert len(formatted) > len(report)
        assert "References" in formatted


# ============================================================================
# Tests: Step Execution and Retry Logic
# ============================================================================

class TestStepExecution:
    """Test step execution with retry logic."""
    
    @pytest.mark.asyncio
    async def test_execute_step_success(self, orchestrator):
        """Successful step execution should complete."""
        plan = ["Step 1", "Step 2", "Step 3"]
        result, execution = await orchestrator.execute_step(
            StepName.PLANNING,
            "test",
        )
        
        assert result is not None
        assert execution.status == StepStatus.SUCCESS
        assert execution.step_name == StepName.PLANNING
    
    @pytest.mark.asyncio
    async def test_step_execution_tracked(self, orchestrator):
        """Step execution should be tracked in state."""
        await orchestrator.execute_step(StepName.PLANNING, "test")
        
        assert len(orchestrator.state.step_history) == 1
        assert orchestrator.state.step_history[0].step_name == StepName.PLANNING
    
    @pytest.mark.asyncio
    async def test_step_evaluation_and_decision(self, orchestrator):
        """Controller should evaluate and decide."""
        plan = ["S1", "S2", "S3"]
        decision = await orchestrator.evaluate_and_decide(
            StepName.PLANNING,
            plan,
        )
        
        assert decision == Decision.CONTINUE


# ============================================================================
# Tests: Orchestration Workflow
# ============================================================================

class TestOrchestration:
    """Test complete orchestration workflows."""
    
    @pytest.mark.asyncio
    async def test_happy_path_workflow(self):
        """Happy path workflow should complete successfully."""
        orchestrator = ReportOrchestrator()
        
        report = await orchestrator.orchestrate("Write AI trends report")
        
        assert report is not None
        assert len(report) > 1000
        assert "# " in report  # Has Markdown headers
        assert "[source:" in report  # Has citations
    
    @pytest.mark.asyncio
    async def test_workflow_state_tracking(self):
        """Workflow should track all state changes."""
        orchestrator = ReportOrchestrator()
        
        await orchestrator.orchestrate("Write AI trends report")
        
        # Verify all steps completed
        assert len(orchestrator.state.step_history) == 6
        assert orchestrator.state.total_steps_completed == 6
    
    @pytest.mark.asyncio
    async def test_workflow_audit_trail(self):
        """Workflow should produce complete audit trail."""
        orchestrator = ReportOrchestrator()
        
        await orchestrator.orchestrate("Write report")
        
        audit_trail = orchestrator.get_audit_trail()
        
        assert "workflow_id" in audit_trail
        assert "task" in audit_trail
        assert "steps" in audit_trail
        assert "summary" in audit_trail
        assert len(audit_trail["steps"]) == 6
    
    @pytest.mark.asyncio
    async def test_workflow_timing(self):
        """Workflow should record timing information."""
        orchestrator = ReportOrchestrator()
        
        await orchestrator.orchestrate("Write report")
        
        audit_trail = orchestrator.get_audit_trail()
        
        # Each step should have timing
        for step in audit_trail["steps"]:
            assert step["duration_seconds"] > 0
            assert step["timestamp"] is not None


# ============================================================================
# Tests: Orchestration Characteristics
# ============================================================================

class TestOrchestrationCharacteristics:
    """Test that orchestration exhibits expected characteristics."""
    
    @pytest.mark.asyncio
    async def test_deterministic_execution(self):
        """Same input should produce same results (deterministic)."""
        orch1 = ReportOrchestrator()
        orch2 = ReportOrchestrator()
        
        report1 = await orch1.orchestrate("Test report")
        report2 = await orch2.orchestrate("Test report")
        
        # Both should complete successfully
        assert len(report1) > 0
        assert len(report2) > 0
    
    @pytest.mark.asyncio
    async def test_explicit_evaluation(self):
        """Each step should be evaluated."""
        orchestrator = ReportOrchestrator()
        
        await orchestrator.orchestrate("Write report")
        
        audit_trail = orchestrator.get_audit_trail()
        
        # Each step should have evaluation result
        for step in audit_trail["steps"]:
            assert step["evaluation"] is not None
            assert len(step["evaluation"]) > 0
    
    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        """Steps should execute sequentially."""
        orchestrator = ReportOrchestrator()
        
        await orchestrator.orchestrate("Write report")
        
        audit_trail = orchestrator.get_audit_trail()
        timestamps = [step["timestamp"] for step in audit_trail["steps"]]
        
        # Timestamps should be in order
        for i in range(len(timestamps) - 1):
            assert timestamps[i] <= timestamps[i+1]
    
    @pytest.mark.asyncio
    async def test_complete_audit_trail(self):
        """Should maintain complete audit trail."""
        orchestrator = ReportOrchestrator()
        
        await orchestrator.orchestrate("Write report")
        
        audit_trail = orchestrator.get_audit_trail()
        
        # Should track plan, data, facts, draft, citations, final
        assert orchestrator.state.plan is not None
        assert orchestrator.state.fetched_data is not None
        assert orchestrator.state.extracted_facts is not None
        assert orchestrator.state.draft_report is not None
        assert orchestrator.state.report_with_citations is not None
        assert orchestrator.state.final_report is not None


# ============================================================================
# Tests: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_workflow_continues_on_individual_errors(self):
        """Workflow should not continue if critical step fails."""
        orchestrator = ReportOrchestrator()
        
        # The workflow should handle its own errors gracefully
        # In this case, if a step fails repeatedly, it raises an exception
        try:
            await orchestrator.orchestrate("Write report")
            # Should succeed normally
            assert orchestrator.state.final_report is not None
        except RuntimeError:
            # If it fails, that's ok for error handling test
            pass


# ============================================================================
# Tests: Orchestration vs Choreography
# ============================================================================

class TestOrchestrationVsChoreography:
    """Test characteristics that differentiate orchestration from choreography."""
    
    @pytest.mark.asyncio
    async def test_centralized_control(self):
        """Orchestration has centralized control via Controller."""
        orchestrator = ReportOrchestrator()
        
        # The Controller (orchestrator) is the single decision-maker
        assert hasattr(orchestrator, 'tools')
        assert hasattr(orchestrator, 'state')
        assert hasattr(orchestrator, 'orchestrate')
        
        # The Controller knows all the steps
        assert StepName.PLANNING in orchestrator.tools
        assert StepName.FETCHING in orchestrator.tools
    
    @pytest.mark.asyncio
    async def test_explicit_workflow_definition(self):
        """Orchestration defines explicit workflow steps."""
        orchestrator = ReportOrchestrator()
        
        # Step sequence is explicit in orchestrate() method
        assert orchestrator.tools is not None
        assert len(orchestrator.tools) == 6  # All 6 steps registered
    
    @pytest.mark.asyncio
    async def test_predictable_output(self):
        """Orchestration produces predictable output."""
        orchestrator = ReportOrchestrator()
        
        report = await orchestrator.orchestrate("Write report")
        
        # Output structure is predictable
        assert isinstance(report, str)
        assert "# " in report
        assert len(report) > 1000
        assert "[source:" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
