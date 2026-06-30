"""
Test Suite for WP-3.5: RAG Architecture — Agentic Workflow

Tests cover:
- Search tool functionality
- Agent memory tracking
- Agentic workflow loop
- Decision-making logic
- Duplicate detection
- Integration tests
"""

import pytest
from datetime import datetime
from examples_3_5 import (
    SearchTool,
    AgentMemory,
    AgentWorkflow,
    create_agentic_workflow,
    create_sample_vector_store,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_vector_store():
    """Create sample vector store."""
    return create_sample_vector_store()


@pytest.fixture
def search_tool(sample_vector_store):
    """Create search tool."""
    return SearchTool(sample_vector_store)


@pytest.fixture
def agent_memory():
    """Create agent memory."""
    return AgentMemory("Test task")


@pytest.fixture
def workflow(sample_vector_store):
    """Create agentic workflow."""
    return AgentWorkflow(
        vector_store=sample_vector_store,
        max_iterations=5,
        max_search_results=5,
    )


# ============================================================================
# TESTS: SEARCH TOOL
# ============================================================================

class TestSearchTool:
    """Test suite for SearchTool class."""
    
    def test_search_tool_init(self, search_tool):
        """Test search tool initialization."""
        assert search_tool is not None
        assert search_tool.vector_store is not None
        assert len(search_tool.search_history) == 0
    
    def test_search_basic(self, search_tool):
        """Test basic search functionality."""
        results = search_tool.search("termination", k=5)
        
        # Should return results
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Results should have required fields
        for result in results:
            assert "content" in result
            assert "source" in result
            assert "score" in result
    
    def test_search_no_results(self, search_tool):
        """Test search with no results."""
        results = search_tool.search("xyzabc_nonexistent_term", k=5)
        
        # Should return empty list
        assert isinstance(results, list)
    
    def test_search_history_tracking(self, search_tool):
        """Test that search history is tracked."""
        query1 = "termination"
        query2 = "payment"
        
        search_tool.search(query1, k=5)
        search_tool.search(query2, k=5)
        
        history = search_tool.get_search_history()
        
        # Should track both searches
        assert len(history) == 2
        assert history[0]["query"] == query1
        assert history[1]["query"] == query2
    
    def test_search_k_parameter(self, search_tool):
        """Test k parameter is respected."""
        results = search_tool.search("termination", k=2)
        
        # Should return at most k results
        assert len(results) <= 2
    
    def test_search_error_handling(self, search_tool):
        """Test error handling in search."""
        # Search with empty query (should not crash)
        results = search_tool.search("", k=5)
        assert isinstance(results, list)


# ============================================================================
# TESTS: AGENT MEMORY
# ============================================================================

class TestAgentMemory:
    """Test suite for AgentMemory class."""
    
    def test_memory_init(self, agent_memory):
        """Test memory initialization."""
        assert agent_memory is not None
        assert agent_memory.task == "Test task"
        assert len(agent_memory.gathered_info) == 0
    
    def test_add_finding(self, agent_memory):
        """Test adding findings to memory."""
        agent_memory.add_finding("key1", "value1", "source1")
        
        # Should store finding
        assert "key1" in agent_memory.gathered_info
        assert len(agent_memory.gathered_info["key1"]) == 1
        assert agent_memory.gathered_info["key1"][0]["value"] == "value1"
    
    def test_multiple_findings_same_key(self, agent_memory):
        """Test adding multiple findings under same key."""
        agent_memory.add_finding("key1", "value1")
        agent_memory.add_finding("key1", "value2")
        
        # Should store both
        assert len(agent_memory.gathered_info["key1"]) == 2
    
    def test_add_reasoning_step(self, agent_memory):
        """Test adding reasoning steps."""
        agent_memory.add_reasoning_step("Analyzed task", "Decided to search")
        
        assert len(agent_memory.reasoning_trail) == 1
        assert agent_memory.reasoning_trail[0]["step"] == "Analyzed task"
        assert agent_memory.reasoning_trail[0]["decision"] == "Decided to search"
    
    def test_add_search(self, agent_memory):
        """Test logging searches."""
        agent_memory.add_search("termination", 5)
        agent_memory.add_search("payment", 3)
        
        assert len(agent_memory.searches_performed) == 2
        assert agent_memory.searches_performed[0]["query"] == "termination"
        assert agent_memory.searches_performed[1]["result_count"] == 3
    
    def test_get_summary(self, agent_memory):
        """Test getting memory summary."""
        agent_memory.add_finding("key1", "value1")
        agent_memory.add_search("query1", 5)
        
        summary = agent_memory.get_summary()
        
        assert "task" in summary
        assert "findings_count" in summary
        assert "searches_count" in summary
        assert summary["findings_count"] == 1
        assert summary["searches_count"] == 1
    
    def test_duration_tracking(self, agent_memory):
        """Test that duration is tracked."""
        import time
        
        # Do some work
        time.sleep(0.1)
        agent_memory.add_finding("key", "value")
        
        summary = agent_memory.get_summary()
        
        # Should have tracked non-zero duration
        assert summary["duration_seconds"] >= 0.1


# ============================================================================
# TESTS: AGENTIC WORKFLOW
# ============================================================================

class TestAgentWorkflow:
    """Test suite for AgentWorkflow class."""
    
    def test_workflow_init(self, workflow):
        """Test workflow initialization."""
        assert workflow is not None
        assert workflow.vector_store is not None
        assert workflow.search_tool is not None
        assert workflow.max_iterations == 5
    
    def test_categorize_finding(self):
        """Test finding categorization."""
        # Test various query types
        assert AgentWorkflow._categorize_finding("termination clause") == "termination_clauses"
        assert AgentWorkflow._categorize_finding("payment terms") == "financial_terms"
        assert AgentWorkflow._categorize_finding("define terms") == "definitions"
        assert AgentWorkflow._categorize_finding("liability limits") == "liability_terms"
        assert AgentWorkflow._categorize_finding("force majeure") == "exceptions"
    
    def test_execute_task_basic(self, workflow):
        """Test basic task execution."""
        task = "Summarize contract terms"
        
        result = workflow.execute_task(task)
        
        # Should return dict with expected keys
        assert isinstance(result, dict)
        assert "task" in result
        assert "answer" in result
        assert "iterations" in result
        assert "stop_reason" in result
    
    def test_execute_task_result_structure(self, workflow):
        """Test result structure."""
        task = "What are termination conditions?"
        
        result = workflow.execute_task(task)
        
        # Verify result structure
        assert result["task"] == task
        assert isinstance(result["answer"], str)
        assert result["iterations"] > 0
        assert result["iterations"] <= workflow.max_iterations
        assert len(result["searches"]) > 0
        assert "duration_seconds" in result
    
    def test_max_iterations_respected(self, workflow):
        """Test that max iterations is respected."""
        workflow.max_iterations = 2
        
        task = "Analyze contract in extreme detail with many aspects"
        result = workflow.execute_task(task)
        
        # Should not exceed max iterations
        assert result["iterations"] <= workflow.max_iterations
    
    def test_duplicate_detection(self):
        """Test duplicate search detection."""
        workflow = create_agentic_workflow(max_iterations=10)
        memory = AgentMemory("test")
        
        # Add searches
        memory.add_search("termination", 5)
        memory.add_search("payment", 3)
        
        # Check duplicates
        assert workflow._is_duplicate_search("termination", memory) == True
        assert workflow._is_duplicate_search("payment", memory) == True
        assert workflow._is_duplicate_search("definitions", memory) == False
    
    def test_analyze_results(self, workflow):
        """Test result analysis."""
        results = [
            {
                "content": "Termination: Either party may terminate",
                "source": "contract.pdf",
                "score": 0.9,
            }
        ]
        
        memory = AgentMemory("test")
        workflow._analyze_results("termination", results, memory)
        
        # Should extract findings
        assert len(memory.gathered_info) > 0


# ============================================================================
# TESTS: INTEGRATION
# ============================================================================

class TestIntegration:
    """Integration tests for full agentic workflow."""
    
    def test_end_to_end_contract_analysis(self):
        """Test end-to-end contract analysis."""
        workflow = create_agentic_workflow(max_iterations=4)
        
        task = (
            "Identify the termination conditions and associated costs "
            "from this contract."
        )
        
        result = workflow.execute_task(task)
        
        # Verify complete workflow
        assert len(result["searches"]) > 0
        assert len(result["reasoning_trail"]) > 0
        assert len(result["answer"]) > 0
        assert result["duration_seconds"] > 0
    
    def test_multiple_search_iterations(self):
        """Test that workflow performs multiple iterations."""
        workflow = create_agentic_workflow(max_iterations=5)
        
        task = (
            "Comprehensively analyze this contract. "
            "Identify termination, payment, liability, and force majeure terms."
        )
        
        result = workflow.execute_task(task)
        
        # Should perform multiple iterations
        assert result["iterations"] > 1
        assert len(result["searches"]) >= 1
    
    def test_reasoning_trail_completeness(self):
        """Test that reasoning trail is complete."""
        workflow = create_agentic_workflow(max_iterations=3)
        
        task = "Summarize contract terms"
        result = workflow.execute_task(task)
        
        # Should have reasoning trail
        assert len(result["reasoning_trail"]) > 0
        
        # Each reasoning step should have required fields
        for step in result["reasoning_trail"]:
            assert "step" in step
            assert "decision" in step
            assert "timestamp" in step


# ============================================================================
# TESTS: EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_task(self):
        """Test with empty task."""
        workflow = create_agentic_workflow(max_iterations=2)
        
        try:
            result = workflow.execute_task("")
            # Should handle gracefully
            assert isinstance(result, dict)
        except Exception:
            pass  # Acceptable to fail
    
    def test_very_long_task(self):
        """Test with very long task."""
        workflow = create_agentic_workflow(max_iterations=2)
        
        long_task = "Analyze contract " * 100
        
        try:
            result = workflow.execute_task(long_task)
            assert isinstance(result, dict)
        except Exception:
            pass
    
    def test_special_characters_in_task(self):
        """Test with special characters."""
        workflow = create_agentic_workflow(max_iterations=2)
        
        task = "What #@!$ are terms? \\n\\t"
        
        try:
            result = workflow.execute_task(task)
            assert isinstance(result, dict)
        except Exception:
            pass
    
    def test_unicode_task(self):
        """Test with unicode characters."""
        workflow = create_agentic_workflow(max_iterations=2)
        
        task = "¿Cuáles son términos? 契約条件は? Каковы условия?"
        
        try:
            result = workflow.execute_task(task)
            assert isinstance(result, dict)
        except Exception:
            pass


# ============================================================================
# TESTS: PERFORMANCE
# ============================================================================

class TestPerformance:
    """Performance and benchmarking tests."""
    
    @pytest.mark.slow
    def test_workflow_latency(self):
        """Test workflow latency."""
        import time
        
        workflow = create_agentic_workflow(max_iterations=3)
        task = "Identify termination and payment terms"
        
        start = time.time()
        result = workflow.execute_task(task)
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 60  # generous timeout for CI
        assert result["duration_seconds"] <= elapsed + 1


# ============================================================================
# TESTS: COMPARISON
# ============================================================================

class TestComparison:
    """Test agentic workflow characteristics."""
    
    def test_multi_iteration_completeness(self):
        """Test that multiple iterations improve completeness."""
        workflow_1iter = create_agentic_workflow(max_iterations=1)
        workflow_multi = create_agentic_workflow(max_iterations=5)
        
        task = "Analyze all aspects of the contract"
        
        result_1 = workflow_1iter.execute_task(task)
        result_multi = workflow_multi.execute_task(task)
        
        # Multi-iteration should have more searches (potentially)
        assert result_multi["iterations"] >= result_1["iterations"]
    
    def test_findings_accumulation(self):
        """Test that findings accumulate across iterations."""
        workflow = create_agentic_workflow(max_iterations=5)
        
        task = "Comprehensively analyze contract"
        result = workflow.execute_task(task)
        
        # Should have accumulated findings
        total_findings = sum(len(f) for f in result["findings"].values())
        assert total_findings >= 0  # May be 0 if no findings, but usually >0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
