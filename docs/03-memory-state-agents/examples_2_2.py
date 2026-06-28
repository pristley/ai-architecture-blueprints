"""
State Management in Single-Agent Loops: Working Examples

This module demonstrates a complete state machine for a research assistant agent.
Includes:
1. State object (Pydantic model) with validation and loop detection
2. Loop guard with multiple detection mechanisms
3. Research assistant with state-aware tools
4. Main agent loop with state management
5. Three complete runnable examples

Example 1: Happy path - research completes successfully
Example 2: Loop detection - agent gets stuck in planning
Example 3: State inspection - debugging and observability

Usage:
    python examples_2_2.py
    # Output: Three scenarios showing state management and loop prevention
"""

from pydantic import BaseModel, Field
from typing import Literal
from dataclasses import dataclass
from datetime import datetime
import uuid
import json


# ============================================================================
# PART 1: STATE OBJECT
# ============================================================================

class ResearchState(BaseModel):
    """
    Core state object for research assistant agent.
    
    Responsibilities:
    - Track current phase (IDLE, PLANNING, SEARCHING, SYNTHESIZING, CITING)
    - Accumulate results as agent progresses
    - Validate state transitions
    - Detect infinite loops
    - Provide observability into agent execution
    """
    
    # Identity
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    
    # Current phase
    state: Literal["IDLE", "PLANNING", "SEARCHING", "SYNTHESIZING", "CITING"] = "IDLE"
    
    # Phase-specific data (evolves as you progress)
    plan: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)
    search_results: dict[str, list[str]] = Field(default_factory=dict)
    synthesis: str = ""
    citations: list[dict] = Field(default_factory=list)
    
    # Loop control and observability
    step_count: int = 0
    state_history: list[str] = Field(default_factory=list)
    search_count_by_query: dict[str, int] = Field(default_factory=dict)
    actions_log: list[str] = Field(default_factory=list)
    
    # Limits (prevents infinite loops)
    MAX_STEPS: int = 20
    MAX_CONSECUTIVE_SAME_STATE: int = 10  # Allow multiple searches in SEARCHING state
    MAX_SEARCHES_PER_QUERY: int = 5
    
    def can_transition(self, target_state: str) -> bool:
        """
        Validate if transition from current state to target is allowed.
        
        Returns:
            bool: True if transition is valid, False otherwise.
        """
        valid_transitions = {
            "IDLE": ["PLANNING"],
            "PLANNING": ["PLANNING", "SEARCHING", "IDLE"],
            "SEARCHING": ["SEARCHING", "SYNTHESIZING", "IDLE"],
            "SYNTHESIZING": ["SYNTHESIZING", "CITING", "SEARCHING", "IDLE"],
            "CITING": ["CITING", "SYNTHESIZING", "IDLE"],
        }
        return target_state in valid_transitions.get(self.state, [])
    
    def is_in_infinite_loop(self) -> tuple[bool, str]:
        """
        Detect infinite loops using multiple strategies.
        
        Checks:
        1. Step limit exceeded (absolute bound)
        2. Same state repeated N times (stuck in phase)
        3. Same search query executed M times (searching in circles)
        4. Alternating state pattern (A→B→A→B→A)
        
        Returns:
            tuple: (is_looping: bool, reason: str)
        """
        # Check 1: Absolute step limit
        if self.step_count > self.MAX_STEPS:
            return True, f"Step limit {self.MAX_STEPS} exceeded (at {self.step_count})"
        
        # Check 2: Same state repeated too many times
        if len(self.state_history) >= self.MAX_CONSECUTIVE_SAME_STATE:
            recent = self.state_history[-self.MAX_CONSECUTIVE_SAME_STATE:]
            if len(set(recent)) == 1:
                count = len([s for s in self.state_history if s == recent[0]])
                return True, f"State '{recent[0]}' repeated {count}x (max {self.MAX_CONSECUTIVE_SAME_STATE})"
        
        # Check 3: Searching the same query too many times
        for query, count in self.search_count_by_query.items():
            if count > self.MAX_SEARCHES_PER_QUERY:
                return True, f"Query '{query}' searched {count}x (max {self.MAX_SEARCHES_PER_QUERY})"
        
        # Check 4: Alternating state pattern (A→B→A→B)
        if len(self.state_history) >= 4:
            recent = self.state_history[-4:]
            if recent[0] == recent[2] and recent[1] == recent[3]:
                return True, f"Alternating pattern detected: {recent[0]}→{recent[1]}→..."
        
        return False, ""
    
    def record_action(self, target_state: str, action: str) -> bool:
        """
        Record a state transition. Validates transition and checks for loops.
        
        Args:
            target_state: The state to transition to
            action: Description of the action causing transition
        
        Returns:
            bool: True if transition successful, False if invalid or would loop
        """
        # Validate transition
        if not self.can_transition(target_state):
            return False
        
        # Check for loops
        in_loop, reason = self.is_in_infinite_loop()
        if in_loop:
            return False
        
        # Record the transition
        self.state_history.append(self.state)
        self.state = target_state
        self.step_count += 1
        self.actions_log.append(f"Step {self.step_count}: {action}")
        
        return True
    
    def get_state_summary(self) -> dict:
        """Get readable summary of current state."""
        return {
            "session_id": self.session_id,
            "state": self.state,
            "step_count": self.step_count,
            "state_history": " → ".join(self.state_history[-8:]),
            "searches_executed": sum(self.search_count_by_query.values()),
            "results_found": len(self.search_results),
            "synthesis_length": len(self.synthesis),
            "citations_count": len(self.citations),
        }


# ============================================================================
# PART 2: LOOP GUARD
# ============================================================================

class LoopGuard:
    """
    Comprehensive infinite loop detection.
    
    Runs multiple checks and returns first failure reason.
    Enables graceful failure instead of agent hanging.
    """
    
    def __init__(self, state: ResearchState):
        self.state = state
        self.checks = [
            ("step_limit", self.check_step_limit),
            ("same_state_repeat", self.check_same_state_repeat),
            ("search_repeats", self.check_search_repeats),
            ("state_patterns", self.check_state_patterns),
        ]
    
    def check_step_limit(self) -> tuple[bool, str]:
        if self.state.step_count > self.state.MAX_STEPS:
            return True, f"Step limit {self.state.MAX_STEPS} exceeded"
        return False, ""
    
    def check_same_state_repeat(self) -> tuple[bool, str]:
        if len(self.state.state_history) >= 10:
            recent = self.state.state_history[-10:]
            if len(set(recent)) == 1:
                return True, f"Stuck in state '{recent[0]}' for 10+ steps"
        return False, ""
    
    def check_search_repeats(self) -> tuple[bool, str]:
        for query, count in self.state.search_count_by_query.items():
            if count > self.state.MAX_SEARCHES_PER_QUERY:
                return True, f"Query '{query}' searched {count}x (max {self.state.MAX_SEARCHES_PER_QUERY})"
        return False, ""
    
    def check_state_patterns(self) -> tuple[bool, str]:
        if len(self.state.state_history) >= 4:
            recent = self.state.state_history[-4:]
            if recent[0] == recent[2] and recent[1] == recent[3]:
                return True, f"Alternating pattern: {recent[0]}↔{recent[1]}"
        return False, ""
    
    def is_looping(self) -> tuple[bool, str]:
        """Run all checks, return first loop detected."""
        for check_name, check_fn in self.checks:
            is_loop, reason = check_fn()
            if is_loop:
                return True, f"{check_name}: {reason}"
        return False, ""


# ============================================================================
# PART 3: RESEARCH ASSISTANT WITH STATE-AWARE TOOLS
# ============================================================================

class ResearchAssistant:
    """
    Research assistant that implements state machine transitions.
    
    Each tool method:
    - Checks current state is valid
    - Performs action
    - Updates state data
    - Records transition
    """
    
    def __init__(self, state: ResearchState):
        self.state = state
    
    def plan_tool(self) -> dict:
        """
        Generate research plan from query.
        
        Transition: IDLE → PLANNING
        """
        if self.state.state != "IDLE":
            return {"success": False, "error": f"Can only plan from IDLE state, not {self.state.state}"}
        
        # Generate plan (mock)
        plan_items = [
            "Search for definition and history",
            "Search for current applications",
            "Search for future research directions",
        ]
        self.state.plan = plan_items
        self.state.search_queries = plan_items
        
        # Record transition
        if not self.state.record_action("PLANNING", "plan_created"):
            return {"success": False, "error": "Cannot transition to PLANNING"}
        
        return {"success": True, "plan": self.state.plan}
    
    def search_tool(self, query: str) -> dict:
        """
        Execute search for a query.
        
        Transition: PLANNING → SEARCHING (first search)
                   SEARCHING → SEARCHING (additional searches)
        """
        # Validate state
        if self.state.state not in ["PLANNING", "SEARCHING"]:
            return {"success": False, "error": f"Cannot search from {self.state.state} state"}
        
        # Track search count
        self.state.search_count_by_query[query] = (
            self.state.search_count_by_query.get(query, 0) + 1
        )
        
        # Execute search (mock)
        results = [
            f"Source 1 about '{query}': Overview and context",
            f"Source 2 about '{query}': Technical details",
            f"Source 3 about '{query}': Practical applications",
        ]
        self.state.search_results[query] = results
        
        # Transition
        target_state = "SEARCHING"
        if not self.state.record_action(target_state, f"searched: '{query}'"):
            return {"success": False, "error": "Cannot transition to SEARCHING"}
        
        return {
            "success": True,
            "query": query,
            "results_count": len(results),
        }
    
    def synthesize_tool(self) -> dict:
        """
        Synthesize search results into comprehensive answer.
        
        Transition: SEARCHING → SYNTHESIZING
        """
        if self.state.state not in ["SEARCHING", "SYNTHESIZING"]:
            return {"success": False, "error": f"Can only synthesize from SEARCHING state, not {self.state.state}"}
        
        # Synthesize (mock)
        synthesis_text = f"""
        Comprehensive answer to "{self.state.query}":
        
        Based on search results from:
        {json.dumps(list(self.state.search_results.keys()), indent=2)}
        
        Key findings:
        1. Definition: {self.state.query} is a fundamental concept
        2. Applications: Used in research, industry, and production
        3. Future: Rapidly evolving with new techniques emerging
        
        This synthesis combines evidence from {len(self.state.search_results)} searches.
        """
        
        self.state.synthesis = synthesis_text
        
        # Transition to SYNTHESIZING if we're not already there
        if self.state.state != "SYNTHESIZING":
            if not self.state.record_action("SYNTHESIZING", "synthesis_complete"):
                return {"success": False, "error": "Cannot transition to SYNTHESIZING"}
        
        return {"success": True, "synthesis_length": len(self.state.synthesis)}
    
    def cite_tool(self) -> dict:
        """
        Add citations to synthesis.
        
        Transition: SYNTHESIZING → CITING
        """
        if self.state.state not in ["SYNTHESIZING", "CITING"]:
            return {"success": False, "error": f"Can only cite from SYNTHESIZING state, not {self.state.state}"}
        
        # Extract citations (mock)
        citations = []
        for i, (query, results) in enumerate(self.state.search_results.items(), 1):
            citations.append({
                "id": i,
                "source": f"Search result for '{query}'",
                "quote": results[0][:50] + "...",
                "relevance": 0.95 - (i * 0.05),
            })
        
        self.state.citations = citations
        
        # Transition to CITING if not already there
        if self.state.state != "CITING":
            if not self.state.record_action("CITING", "citations_added"):
                return {"success": False, "error": "Cannot transition to CITING"}
        
        return {"success": True, "citations_count": len(citations)}


# ============================================================================
# PART 4: MAIN AGENT LOOP WITH STATE MANAGEMENT
# ============================================================================

def research_agent_with_state(query: str, verbose: bool = True) -> dict:
    """
    Main agent loop with state machine.
    
    Flow:
    1. IDLE: Initialize state
    2. PLANNING: Create research plan
    3. SEARCHING: Execute searches from plan
    4. SYNTHESIZING: Combine results
    5. CITING: Add citations
    
    Args:
        query: Research question
        verbose: Print state transitions
    
    Returns:
        dict: Final response with success status, synthesis, citations, and stats
    """
    
    # Initialize state
    state = ResearchState(query=query)
    assistant = ResearchAssistant(state)
    guard = LoopGuard(state)
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"🤖 Research Agent Starting")
        print(f"{'='*70}")
        print(f"Query: {query}")
        print(f"Session: {state.session_id}")
    
    # Main loop
    while state.step_count < state.MAX_STEPS:
        # Check for loops
        in_loop, reason = guard.is_looping()
        if in_loop:
            if verbose:
                print(f"\n❌ Loop detected: {reason}")
            state.state = "IDLE"
            break
        
        # Print current state
        if verbose:
            summary = state.get_state_summary()
            print(f"\n📍 Step {summary['step_count']}: {state.state}")
        
        # State machine: Execute based on current state
        if state.state == "IDLE":
            result = assistant.plan_tool()
            if verbose and result["success"]:
                print(f"   ✓ Created plan: {len(result['plan'])} steps")
        
        elif state.state == "PLANNING":
            # Find unsearched plan item
            unsearched = [q for q in state.search_queries if q not in state.search_results]
            if unsearched:
                result = assistant.search_tool(unsearched[0])
                if verbose and result["success"]:
                    print(f"   ✓ Searched: {result['query']} ({result['results_count']} results)")
            else:
                # All plan items searched, force transition to searching
                state.state = "SEARCHING"
                if verbose:
                    print(f"   ✓ All queries planned, moving to SEARCHING")
        
        elif state.state == "SEARCHING":
            # Check if we have enough results
            unsearched = [q for q in state.search_queries if q not in state.search_results]
            if unsearched:
                result = assistant.search_tool(unsearched[0])
                if verbose and result["success"]:
                    print(f"   ✓ Searched: {result['query']} ({result['results_count']} results)")
            else:
                # All searches done, move to synthesis
                if verbose:
                    print(f"   ✓ All searches complete, moving to SYNTHESIZING")
                # Call synthesize which handles the state transition
                result = assistant.synthesize_tool()
                if verbose and result["success"]:
                    print(f"   ✓ Synthesis complete ({result['synthesis_length']} chars)")
                elif verbose:
                    print(f"   ✗ Synthesis failed: {result.get('error', 'Unknown error')}")
        
        elif state.state == "SYNTHESIZING":
            # If not synthesized yet, do it now
            if not state.synthesis:
                result = assistant.synthesize_tool()
                if verbose and result["success"]:
                    print(f"   ✓ Synthesis complete ({result['synthesis_length']} chars)")
                elif verbose:
                    print(f"   ✗ Synthesis failed: {result.get('error', 'Unknown error')}")
            else:
                # Move to citations
                state.state = "CITING"
                if verbose:
                    print(f"   ✓ Synthesis done, moving to CITING")
        
        elif state.state == "CITING":
            result = assistant.cite_tool()
            if verbose and result["success"]:
                print(f"   ✓ Citations added ({result['citations_count']} sources)")
                break  # Done!
            elif verbose:
                print(f"   ✗ Citations failed: {result.get('error', 'Unknown error')}")
    
    # Final result
    success = state.state == "CITING" and len(state.citations) > 0
    
    if verbose:
        print(f"\n{'='*70}")
        if success:
            print(f"✅ Research Complete!")
        else:
            print(f"⚠️  Research Incomplete (state: {state.state})")
        print(f"{'='*70}")
        print(f"Steps: {state.step_count}/{state.MAX_STEPS}")
        print(f"State history: {' → '.join(state.state_history)}")
        print(f"Searches: {json.dumps(state.search_count_by_query, indent=2)}")
    
    return {
        "success": success,
        "query": query,
        "state_final": state.state,
        "synthesis": state.synthesis[:200] + "..." if state.synthesis else "",
        "citations": state.citations,
        "stats": {
            "steps_taken": state.step_count,
            "state_history": state.state_history,
            "searches_executed": sum(state.search_count_by_query.values()),
            "session_id": state.session_id,
        }
    }


# ============================================================================
# PART 5: RUNNABLE EXAMPLES
# ============================================================================

def example_1_happy_path():
    """
    Example 1: Happy path - research completes successfully.
    
    Shows:
    - Normal state transitions
    - Tool calls updating state
    - Successful completion
    - Final output with citations
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Happy Path - Successful Research")
    print("="*70)
    
    result = research_agent_with_state(
        "What is machine learning?",
        verbose=True
    )
    
    print(f"\nFinal Synthesis (first 200 chars):\n{result['synthesis']}\n")
    print(f"Citations: {len(result['citations'])} sources")
    for citation in result['citations']:
        print(f"  - [{citation['id']}] {citation['source']}")


def example_2_loop_detection():
    """
    Example 2: Loop detection - agent gets stuck.
    
    Demonstrates:
    - Loop guard catching infinite loops
    - Different loop detection mechanisms
    - Graceful failure instead of hang
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Loop Detection - Agent Gets Stuck")
    print("="*70)
    
    # Create a state that would loop
    state = ResearchState(query="Test query")
    
    print("\nScenario 1: Same state repeated 3x (not enough to trigger loop)")
    state.state_history = ["PLANNING", "PLANNING", "PLANNING"]
    in_loop, reason = state.is_in_infinite_loop()
    print(f"  Loop detected: {in_loop}")
    print(f"  Reason: {reason if reason else 'Not detected (need >= 10 consecutive)'}")
    
    print("\nScenario 2: Same search repeated 6x")
    state.search_count_by_query = {"quantum computing": 6}
    in_loop, reason = state.is_in_infinite_loop()
    print(f"  Loop detected: {in_loop}")
    print(f"  Reason: {reason}")
    
    print("\nScenario 3: Step limit exceeded")
    state.step_count = 25
    in_loop, reason = state.is_in_infinite_loop()
    print(f"  Loop detected: {in_loop}")
    print(f"  Reason: {reason}")
    
    print("\nScenario 4: Alternating state pattern (A→B→A→B→...)")
    state.step_count = 5
    state.state_history = ["PLANNING", "SEARCHING", "PLANNING", "SEARCHING"]
    state.search_count_by_query = {}  # Clear search counts
    in_loop, reason = state.is_in_infinite_loop()
    print(f"  Loop detected: {in_loop}")
    print(f"  Reason: {reason if reason else 'Not detected (need to check more conditions)'}")


def example_3_state_inspection():
    """
    Example 3: State inspection and debugging.
    
    Demonstrates:
    - State snapshots at each step
    - State history for debugging
    - Transition validation
    - Observability into agent behavior
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: State Inspection and Debugging")
    print("="*70)
    
    state = ResearchState(query="What is AI?")
    assistant = ResearchAssistant(state)
    
    print("\nInitial State:")
    print(f"  {state.get_state_summary()}")
    
    print("\nStep 1: Plan")
    assistant.plan_tool()
    print(f"  {state.get_state_summary()}")
    print(f"  Actions: {state.actions_log}")
    
    print("\nStep 2: Search")
    assistant.search_tool("Definition")
    print(f"  {state.get_state_summary()}")
    print(f"  Actions: {state.actions_log}")
    
    print("\nStep 3: Synthesize")
    assistant.synthesize_tool()
    print(f"  {state.get_state_summary()}")
    print(f"  Actions: {state.actions_log}")
    
    print("\nStep 4: Cite")
    assistant.cite_tool()
    print(f"  {state.get_state_summary()}")
    print(f"  Actions: {state.actions_log}")
    
    print("\nFull State History:")
    print(f"  Transitions: {' → '.join(state.state_history + [state.state])}")
    print(f"  Total steps: {state.step_count}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("STATE MANAGEMENT IN SINGLE-AGENT LOOPS: WORKING EXAMPLES")
    print("="*70)
    
    # Run all examples
    example_1_happy_path()
    example_2_loop_detection()
    example_3_state_inspection()
    
    print("\n" + "="*70)
    print("✅ All examples completed")
    print("="*70)
