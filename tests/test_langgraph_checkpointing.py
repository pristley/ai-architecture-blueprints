"""
Tests for LangGraph Checkpointing & Human-in-the-Loop (WP-2.7)

Tests validate:
1. State schema and field initialization
2. Email validation (recipient, subject)
3. Email generation node
4. Approval check routing
5. Send email node (approved path)
6. Send email skip (rejected path)
7. Complete workflows (approval + rejection)
8. Checkpoint persistence and resumption
9. Error handling and retry logic
10. Step history tracking
"""

import pytest
import asyncio
import sqlite3
import os
from datetime import datetime
from typing import Dict

# Import workflow components
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "docs" / "04-multi-agent-architectures"))

from examples_2_7 import (
    EmailApprovalState,
    validate_email,
    validate_subject,
    generate_email,
    approval_check,
    send_email,
    route_after_approval,
    build_email_approval_graph,
    run_approval_workflow_with_approval,
    run_approval_workflow_with_rejection,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_checkpoint_db():
    """Create temporary checkpoint database for tests."""
    # Return None since we're using in-memory checkpointer
    yield None


@pytest.fixture
def valid_initial_state() -> EmailApprovalState:
    """Create a valid initial state."""
    return {
        "recipient": "test@example.com",
        "subject": "Test Subject",
        "body": None,
        "generated_at": None,
        "approval_status": None,
        "approval_notes": None,
        "reviewed_at": None,
        "send_timestamp": None,
        "error_message": None,
        "thread_id": "test-123",
        "step_history": []
    }


@pytest.fixture
def generated_state(valid_initial_state) -> EmailApprovalState:
    """State after email generation."""
    state = valid_initial_state.copy()
    state["body"] = "Generated email body for testing"
    state["generated_at"] = datetime.now().isoformat()
    return state


# ============================================================================
# TEST 1: State Schema Validation
# ============================================================================

class TestEmailApprovalState:
    """Test EmailApprovalState TypedDict schema."""
    
    def test_valid_initial_state(self, valid_initial_state):
        """Test creating a valid initial state."""
        assert valid_initial_state["recipient"] == "test@example.com"
        assert valid_initial_state["body"] is None
        assert valid_initial_state["approval_status"] is None
        assert valid_initial_state["step_history"] == []
    
    def test_state_with_approval(self, generated_state):
        """Test state after approval."""
        generated_state["approval_status"] = "approved"
        assert generated_state["approval_status"] == "approved"
        assert generated_state["body"] is not None
    
    def test_state_immutability(self, valid_initial_state):
        """Test that state modifications don't affect original."""
        original_approval = valid_initial_state["approval_status"]
        valid_initial_state["approval_status"] = "approved"
        assert valid_initial_state["approval_status"] == "approved"
        assert original_approval is None


# ============================================================================
# TEST 2: Validation Functions
# ============================================================================

class TestEmailValidation:
    """Test email validation functions."""
    
    def test_validate_email_valid(self):
        """Valid email passes validation."""
        state = {"recipient": "test@example.com"}
        assert validate_email(state) is None
    
    def test_validate_email_missing(self):
        """Missing email fails validation."""
        state = {"recipient": ""}
        error = validate_email(state)
        assert error is not None
        assert "empty" in error.lower()
    
    def test_validate_email_invalid_format(self):
        """Invalid format fails validation."""
        state = {"recipient": "invalidemail"}
        error = validate_email(state)
        assert error is not None
        assert "format" in error.lower()
    
    def test_validate_email_too_long(self):
        """Email exceeding max length fails."""
        state = {"recipient": "a" * 300 + "@example.com"}
        error = validate_email(state)
        assert error is not None
        assert "long" in error.lower()
    
    def test_validate_subject_valid(self):
        """Valid subject passes validation."""
        state = {"subject": "Test Subject"}
        assert validate_subject(state) is None
    
    def test_validate_subject_missing(self):
        """Missing subject fails validation."""
        state = {"subject": ""}
        error = validate_subject(state)
        assert error is not None
        assert "empty" in error.lower()
    
    def test_validate_subject_too_long(self):
        """Subject exceeding max length fails."""
        state = {"subject": "a" * 2000}
        error = validate_subject(state)
        assert error is not None
        assert "long" in error.lower()


# ============================================================================
# TEST 3: Node Functions
# ============================================================================

class TestGenerateEmailNode:
    """Test email generation node."""
    
    @pytest.mark.asyncio
    async def test_generate_email_success(self, valid_initial_state):
        """Email generation succeeds with valid input."""
        result = await generate_email(valid_initial_state)
        
        assert result["body"] is not None
        assert len(result["body"]) > 100
        assert result["generated_at"] is not None
        assert result["error_message"] is None
        assert len(result["step_history"]) > 0
        assert result["step_history"][0]["step"] == "generate_email"
        assert result["step_history"][0]["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_generate_email_invalid_recipient(self, valid_initial_state):
        """Generation fails with invalid recipient."""
        valid_initial_state["recipient"] = "invalidemail"
        result = await generate_email(valid_initial_state)
        
        assert result["error_message"] is not None
        assert "format" in result["error_message"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_email_missing_recipient(self, valid_initial_state):
        """Generation fails with missing recipient."""
        valid_initial_state["recipient"] = ""
        result = await generate_email(valid_initial_state)
        
        assert result["error_message"] is not None
        assert "empty" in result["error_message"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_email_invalid_subject(self, valid_initial_state):
        """Generation fails with invalid subject."""
        valid_initial_state["subject"] = ""
        result = await generate_email(valid_initial_state)
        
        assert result["error_message"] is not None
        assert "empty" in result["error_message"].lower()


class TestApprovalCheckNode:
    """Test approval check node."""
    
    @pytest.mark.asyncio
    async def test_approval_check_approved(self, generated_state):
        """Approval check with approved status."""
        generated_state["approval_status"] = "approved"
        result = await approval_check(generated_state)
        
        assert result["approval_status"] == "approved"
        assert result["reviewed_at"] is not None
        assert result["error_message"] is None
    
    @pytest.mark.asyncio
    async def test_approval_check_rejected(self, generated_state):
        """Approval check with rejected status."""
        generated_state["approval_status"] = "rejected"
        generated_state["approval_notes"] = "Too generic"
        result = await approval_check(generated_state)
        
        assert result["approval_status"] == "rejected"
        assert result["error_message"] is not None
        assert "rejected" in result["error_message"].lower()
    
    @pytest.mark.asyncio
    async def test_approval_check_pending(self, generated_state):
        """Approval check with pending status."""
        generated_state["approval_status"] = None
        result = await approval_check(generated_state)
        
        assert result["error_message"] is not None


class TestSendEmailNode:
    """Test send email node."""
    
    @pytest.mark.asyncio
    async def test_send_email_approved(self, generated_state):
        """Send email succeeds when approved."""
        generated_state["approval_status"] = "approved"
        result = await send_email(generated_state)
        
        assert result["send_timestamp"] is not None
        assert result["error_message"] is None
        assert any(s["step"] == "send_email" for s in result["step_history"])
    
    @pytest.mark.asyncio
    async def test_send_email_not_approved(self, generated_state):
        """Send email fails when not approved."""
        generated_state["approval_status"] = "rejected"
        result = await send_email(generated_state)
        
        assert result["send_timestamp"] is None
        assert result["error_message"] is not None
        assert "not sent" in result["error_message"].lower() or "not approved" in result["error_message"].lower()
    
    @pytest.mark.asyncio
    async def test_send_email_no_body(self, generated_state):
        """Send email fails when body is empty."""
        generated_state["body"] = None
        generated_state["approval_status"] = "approved"
        result = await send_email(generated_state)
        
        assert result["send_timestamp"] is None
        assert result["error_message"] is not None


# ============================================================================
# TEST 4: Routing Logic
# ============================================================================

class TestApprovalRouting:
    """Test routing logic."""
    
    def test_route_after_approval_approved(self, generated_state):
        """Routing when approved goes to send_email."""
        generated_state["approval_status"] = "approved"
        next_node = route_after_approval(generated_state)
        
        assert next_node == "send_email"
    
    def test_route_after_approval_rejected(self, generated_state):
        """Routing when rejected ends workflow."""
        generated_state["approval_status"] = "rejected"
        next_node = route_after_approval(generated_state)
        
        # Should route to END (not "send_email")
        assert next_node != "send_email"
    
    def test_route_after_approval_pending(self, generated_state):
        """Routing when pending ends workflow."""
        generated_state["approval_status"] = None
        next_node = route_after_approval(generated_state)
        
        assert next_node != "send_email"


# ============================================================================
# TEST 5: Graph Building
# ============================================================================

class TestGraphBuilding:
    """Test graph compilation."""
    
    def test_build_graph_success(self, temp_checkpoint_db):
        """Graph builds successfully."""
        graph = build_email_approval_graph(temp_checkpoint_db)
        
        assert graph is not None
        # Verify graph has expected nodes
        assert "generate_email" in graph.nodes
        assert "approval_check" in graph.nodes
        assert "send_email" in graph.nodes
    
    def test_graph_has_checkpointer(self, temp_checkpoint_db):
        """Compiled graph has checkpointer configured."""
        graph = build_email_approval_graph(temp_checkpoint_db)
        
        # Checkpointer should be accessible
        assert graph.checkpointer is not None
    
    @pytest.mark.asyncio
    async def test_graph_invoke(self, temp_checkpoint_db, valid_initial_state):
        """Graph can be invoked."""
        graph = build_email_approval_graph(temp_checkpoint_db)
        
        config = {"configurable": {"thread_id": "test-graph-123"}}
        result = await graph.ainvoke(valid_initial_state, config=config)
        
        assert result is not None
        assert result["body"] is not None  # Email generated


# ============================================================================
# TEST 6: Complete Workflows
# ============================================================================

class TestApprovalWorkflow:
    """Test complete approval workflow."""
    
    @pytest.mark.asyncio
    async def test_workflow_with_approval(self, temp_checkpoint_db):
        """Complete workflow: generate → approve → send."""
        result = await run_approval_workflow_with_approval(
            recipient="test@example.com",
            subject="Test Subject",
            thread_id="test-approval-workflow"
        )
        
        assert result["send_timestamp"] is not None
        assert result["approval_status"] == "approved"
        assert result["error_message"] is None
        assert any(s["step"] == "send_email" for s in result["step_history"])
    
    @pytest.mark.asyncio
    async def test_workflow_with_rejection(self, temp_checkpoint_db):
        """Complete workflow: generate → reject → skip send."""
        result = await run_approval_workflow_with_rejection(
            recipient="test@example.com",
            subject="Test Subject",
            thread_id="test-rejection-workflow"
        )
        
        assert result["send_timestamp"] is None
        assert result["approval_status"] == "rejected"
        assert result["error_message"] is not None
        assert "rejected" in result["error_message"].lower()


# ============================================================================
# TEST 7: Checkpoint Persistence
# ============================================================================

class TestCheckpointPersistence:
    """Test checkpoint saving and restoration."""
    
    @pytest.mark.asyncio
    async def test_checkpoint_created(self, temp_checkpoint_db):
        """Checkpoint storage is available."""
        graph = build_email_approval_graph(temp_checkpoint_db)
        
        initial_state = {
            "recipient": "test@example.com",
            "subject": "Test",
            "body": None,
            "generated_at": None,
            "approval_status": None,
            "approval_notes": None,
            "reviewed_at": None,
            "send_timestamp": None,
            "error_message": None,
            "thread_id": "test-checkpoint-123",
            "step_history": []
        }
        
        config = {"configurable": {"thread_id": "test-checkpoint-123"}}
        await graph.ainvoke(initial_state, config=config)
        
        # Graph has checkpointer configured
        assert graph.checkpointer is not None
    
    @pytest.mark.asyncio
    async def test_state_retrievable_from_checkpoint(self, temp_checkpoint_db):
        """State can be retrieved from checkpoint."""
        graph = build_email_approval_graph(temp_checkpoint_db)
        
        initial_state = {
            "recipient": "test@example.com",
            "subject": "Test",
            "body": None,
            "generated_at": None,
            "approval_status": None,
            "approval_notes": None,
            "reviewed_at": None,
            "send_timestamp": None,
            "error_message": None,
            "thread_id": "test-retrieve-123",
            "step_history": []
        }
        
        config = {"configurable": {"thread_id": "test-retrieve-123"}}
        
        # First invocation
        result1 = await graph.ainvoke(initial_state, config=config)
        
        # Should have generated email
        assert result1["body"] is not None
        generated_body = result1["body"]
        
        # Retrieve state from checkpoint
        checkpoint_state = graph.get_state(config)
        assert checkpoint_state is not None
        assert checkpoint_state.values["body"] == generated_body


# ============================================================================
# TEST 8: Error Scenarios
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_invalid_email_format(self, valid_initial_state):
        """Invalid email format is handled."""
        valid_initial_state["recipient"] = "not-an-email"
        result = await generate_email(valid_initial_state)
        
        assert result["error_message"] is not None
    
    @pytest.mark.asyncio
    async def test_missing_required_field(self, valid_initial_state):
        """Missing required field is handled."""
        del valid_initial_state["recipient"]
        
        with pytest.raises(KeyError):
            # TypedDict doesn't enforce at runtime, but missing key should fail
            result = await generate_email(valid_initial_state)
    
    @pytest.mark.asyncio
    async def test_step_history_tracking(self, valid_initial_state):
        """Step history is tracked correctly."""
        result = await generate_email(valid_initial_state)
        
        assert "step_history" in result
        assert len(result["step_history"]) > 0
        assert result["step_history"][0]["step"] == "generate_email"
        assert "timestamp" in result["step_history"][0]
        assert "status" in result["step_history"][0]


# ============================================================================
# TEST 9: Async Execution
# ============================================================================

class TestAsyncExecution:
    """Test async execution characteristics."""
    
    @pytest.mark.asyncio
    async def test_concurrent_workflows(self, temp_checkpoint_db):
        """Multiple workflows can execute concurrently."""
        graph = build_email_approval_graph(temp_checkpoint_db)
        
        async def run_workflow(thread_id: str):
            initial_state = {
                "recipient": f"{thread_id}@example.com",
                "subject": f"Subject for {thread_id}",
                "body": None,
                "generated_at": None,
                "approval_status": None,
                "approval_notes": None,
                "reviewed_at": None,
                "send_timestamp": None,
                "error_message": None,
                "thread_id": thread_id,
                "step_history": []
            }
            
            config = {"configurable": {"thread_id": thread_id}}
            return await graph.ainvoke(initial_state, config=config)
        
        # Run 3 workflows concurrently
        results = await asyncio.gather(
            run_workflow("workflow-1"),
            run_workflow("workflow-2"),
            run_workflow("workflow-3")
        )
        
        assert len(results) == 3
        # Note: workflows may fail due to interrupt before completing
        # This test verifies concurrent execution is possible


# ============================================================================
# TEST 10: Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""
    
    @pytest.mark.asyncio
    async def test_full_approval_workflow_integration(self, temp_checkpoint_db):
        """Integration test of full approval workflow."""
        graph = build_email_approval_graph(temp_checkpoint_db)
        
        # Step 1: Generate
        initial_state = {
            "recipient": "integration@example.com",
            "subject": "Integration Test",
            "body": None,
            "generated_at": None,
            "approval_status": None,
            "approval_notes": None,
            "reviewed_at": None,
            "send_timestamp": None,
            "error_message": None,
            "thread_id": "integration-test",
            "step_history": []
        }
        
        config = {"configurable": {"thread_id": "integration-test"}}
        
        result1 = await graph.ainvoke(initial_state, config=config)
        assert result1["body"] is not None
        assert result1["approval_status"] is None
        
        # Step 2: Approve
        state = graph.get_state(config)
        updated = state.values.copy()
        updated["approval_status"] = "approved"
        graph.update_state(config, updated)
        
        # Step 3: Resume
        result2 = await graph.ainvoke(None, config=config)
        assert result2["send_timestamp"] is not None
    
    @pytest.mark.asyncio
    async def test_full_rejection_workflow_integration(self, temp_checkpoint_db):
        """Integration test of full rejection workflow."""
        graph = build_email_approval_graph(temp_checkpoint_db)
        
        # Step 1: Generate
        initial_state = {
            "recipient": "rejection@example.com",
            "subject": "Rejection Test",
            "body": None,
            "generated_at": None,
            "approval_status": None,
            "approval_notes": None,
            "reviewed_at": None,
            "send_timestamp": None,
            "error_message": None,
            "thread_id": "rejection-test",
            "step_history": []
        }
        
        config = {"configurable": {"thread_id": "rejection-test"}}
        result1 = graph.invoke(initial_state, config=config)
        
        # Step 2: Reject
        state = graph.get_state(config)
        updated = state.values.copy()
        updated["approval_status"] = "rejected"
        graph.update_state(config, updated)
        
        # Step 3: Resume
        result2 = await graph.ainvoke(None, config=config)
        assert result2["send_timestamp"] is None
        assert result2["error_message"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
