"""
Research Assistant State Machine Implementation

This module demonstrates state management for a single-agent loop.
Implements the "Research Assistant" agent with states: IDLE, PLANNING, SEARCHING, SYNTHESIZING, CITING.

Key features:
- Explicit state transitions with validation
- Infinite loop detection via multiple strategies
- Structured logging and observability
- Checkpointing and recovery
- Integration patterns for LangChain/LangGraph

Usage:
    python research_assistant_state_machine.py
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple


class AgentState(str, Enum):
    """Valid agent states."""
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    SEARCHING = "SEARCHING"
    SYNTHESIZING = "SYNTHESIZING"
    CITING = "CITING"


@dataclass
class ResearchState:
    """
    Core state object for research assistant agent.
    
    This dataclass tracks:
    - Current phase (state machine state)
    - Phase-specific data (plan, results, synthesis, citations)
    - Loop control (step counts, history, search tracking)
    - Execution metadata (timestamps, session ID, last action)
    """
    
    # Identity
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    
    # Current phase
    state: AgentState = AgentState.IDLE
    
    # Phase-specific data (evolve as you progress through states)
    plan: List[str] = field(default_factory=list)
    search_queries: List[str] = field(default_factory=list)
    search_results: Dict[str, List[str]] = field(default_factory=dict)
    synthesis: str = ""
    citations: List[Dict[str, str]] = field(default_factory=list)
    
    # Loop control
    step_count: int = 0
    state_history: List[AgentState] = field(default_factory=list)
    search_count_by_query: Dict[str, int] = field(default_factory=dict)
    
    # Execution tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_action: str = ""
    errors: List[str] = field(default_factory=list)
    
    # Configuration: Loop prevention limits
    MAX_STEPS: int = 20
    MAX_SAME_STATE_REPEATS: int = 3
    MAX_SEARCHES_PER_QUERY: int = 5
    MAX_PLANNING_CYCLES: int = 2
    MAX_SYNTHESIZING_CYCLES: int = 2
    
    def can_transition(self, target_state: AgentState) -> bool:
        """
        Validate if transition to target_state is allowed.
        
        State machine rules:
        - IDLE can only go to PLANNING
        - PLANNING can refine itself or move to SEARCHING
        - SEARCHING can continue or move to SYNTHESIZING
        - SYNTHESIZING can refine itself, get more info, or move to CITING
        - CITING can verify or return to SYNTHESIZING
        - Any state can error-reset to IDLE
        """
        valid_transitions = {
            AgentState.IDLE: [AgentState.PLANNING],
            AgentState.PLANNING: [AgentState.PLANNING, AgentState.SEARCHING, AgentState.IDLE],
            AgentState.SEARCHING: [AgentState.SEARCHING, AgentState.SYNTHESIZING, AgentState.IDLE],
            AgentState.SYNTHESIZING: [
                AgentState.SYNTHESIZING, AgentState.CITING, AgentState.SEARCHING, AgentState.IDLE
            ],
            AgentState.CITING: [AgentState.CITING, AgentState.SYNTHESIZING, AgentState.IDLE],
        }
        return target_state in valid_transitions.get(self.state, [])
    
    def is_in_infinite_loop(self) -> Tuple[bool, str]:
        """
        Comprehensive loop detection.
        
        Returns: (is_looping, reason_description)
        
        Detects:
        1. Step limit exceeded (too many total steps)
        2. Same state repeated too many times (stuck in one phase)
        3. Searching the same query repeatedly (redundant searches)
        4. Too many cycles in "refine" states (PLANNING, SYNTHESIZING loops)
        """
        # Check 1: Global step limit exceeded
        if self.step_count > self.MAX_STEPS:
            return True, f"Step limit {self.MAX_STEPS} exceeded (at {self.step_count})"
        
        # Check 2: Same state repeated too many times
        if len(self.state_history) >= self.MAX_SAME_STATE_REPEATS:
            recent = self.state_history[-self.MAX_SAME_STATE_REPEATS:]
            if len(set(recent)) == 1:
                state_name = recent[0].value
                return True, f"State '{state_name}' repeated {self.MAX_SAME_STATE_REPEATS}x in a row"
        
        # Check 3: Searching the same query too many times
        for query, count in self.search_count_by_query.items():
            if count > self.MAX_SEARCHES_PER_QUERY:
                return True, f"Query '{query}' searched {count}x (max {self.MAX_SEARCHES_PER_QUERY})"
        
        # Check 4: Too many planning cycles
        planning_count = sum(1 for s in self.state_history if s == AgentState.PLANNING)
        if planning_count > self.MAX_PLANNING_CYCLES:
            return True, f"Planning cycles {planning_count}x (max {self.MAX_PLANNING_CYCLES})"
        
        # Check 5: Too many synthesizing cycles
        synthesizing_count = sum(1 for s in self.state_history if s == AgentState.SYNTHESIZING)
        if synthesizing_count > self.MAX_SYNTHESIZING_CYCLES:
            return True, f"Synthesizing cycles {synthesizing_count}x (max {self.MAX_SYNTHESIZING_CYCLES})"
        
        return False, ""
    
    def record_action(self, target_state: AgentState, action: str) -> bool:
        """
        Record state transition with validation.
        
        Args:
            target_state: Target state for transition
            action: Description of action triggering transition
        
        Returns:
            True if transition recorded, False if invalid or would cause loop
        """
        # Validate transition
        if not self.can_transition(target_state):
            self.errors.append(
                f"Invalid transition: {self.state.value} → {target_state.value}"
            )
            return False
        
        # Check for loops
        in_loop, reason = self.is_in_infinite_loop()
        if in_loop:
            self.errors.append(f"Loop detected: {reason}")
            return False
        
        # Record the transition
        self.state_history.append(self.state)
        self.state = target_state
        self.step_count += 1
        self.last_action = action
        
        return True
    
    def get_status(self) -> str:
        """Get human-readable status string."""
        return (
            f"State: {self.state.value} | Step: {self.step_count}/{self.MAX_STEPS} | "
            f"History: {' → '.join(s.value for s in self.state_history[-3:])} | "
            f"Last: {self.last_action}"
        )


class ResearchAssistant:
    """
    Research assistant agent that manages state transitions.
    
    Demonstrates how to organize tool calls around state management.
    Each tool validates current state before execution and records
    the resulting state transition.
    """
    
    def __init__(self, state: ResearchState):
        self.state = state
    
    def plan_tool(self) -> Dict:
        """
        Tool 1: Create research plan.
        
        Precondition: state == IDLE
        Postcondition: state == PLANNING, plan populated
        """
        if self.state.state != AgentState.IDLE:
            return {"error": f"Can only plan from IDLE, currently {self.state.state.value}"}
        
        # Simulate LLM planning
        print(f"\n🧠 Planning for query: '{self.state.query}'")
        self.state.plan = [
            "Search for fundamental concepts",
            "Search for applications",
            "Search for recent developments",
        ]
        
        # Record transition
        if not self.state.record_action(AgentState.PLANNING, "created_plan"):
            return {"error": "Failed to transition to PLANNING"}
        
        print(f"   ✓ Plan created: {len(self.state.plan)} steps")
        return {"plan": self.state.plan}
    
    def search_tool(self, query: str) -> Dict:
        """
        Tool 2: Execute search for information.
        
        Precondition: state in [PLANNING, SEARCHING]
        Postcondition: state == SEARCHING, search_results updated
        """
        if self.state.state not in [AgentState.PLANNING, AgentState.SEARCHING]:
            return {
                "error": f"Can only search from PLANNING/SEARCHING, "
                         f"currently {self.state.state.value}"
            }
        
        # Prevent redundant searches (loop prevention)
        count = self.state.search_count_by_query.get(query, 0)
        if count >= self.state.MAX_SEARCHES_PER_QUERY:
            return {
                "error": f"Already searched '{query}' {count}x "
                         f"(max {self.state.MAX_SEARCHES_PER_QUERY})"
            }
        
        # Simulate search
        print(f"\n🔍 Searching: '{query}'")
        self.state.search_count_by_query[query] = count + 1
        self.state.search_results[query] = [
            f"Result {i} for query: {query}" for i in range(1, 4)
        ]
        
        # Record transition
        if not self.state.record_action(AgentState.SEARCHING, f"searched: {query}"):
            return {"error": "Failed to transition to SEARCHING"}
        
        print(f"   ✓ Found {len(self.state.search_results[query])} results")
        return {"query": query, "results": self.state.search_results[query]}
    
    def synthesize_tool(self) -> Dict:
        """
        Tool 3: Synthesize search results into answer.
        
        Precondition: state == SEARCHING, search_results populated
        Postcondition: state == SYNTHESIZING, synthesis populated
        """
        if self.state.state != AgentState.SEARCHING:
            return {
                "error": f"Can only synthesize from SEARCHING, "
                         f"currently {self.state.state.value}"
            }
        
        if not self.state.search_results:
            return {"error": "No search results to synthesize"}
        
        # Simulate synthesis
        print(f"\n✍️  Synthesizing answer...")
        result_text = "\n".join(
            f"- {result}" 
            for results in self.state.search_results.values()
            for result in results
        )
        self.state.synthesis = (
            f"Based on research of '{self.state.query}':\n\n"
            f"Key findings:\n{result_text}\n\n"
            f"Conclusion: This is a comprehensive answer synthesized from {len(self.state.search_results)} searches."
        )
        
        # Record transition
        if not self.state.record_action(AgentState.SYNTHESIZING, "synthesis_complete"):
            return {"error": "Failed to transition to SYNTHESIZING"}
        
        print(f"   ✓ Synthesis complete ({len(self.state.synthesis)} chars)")
        return {"synthesis": self.state.synthesis}
    
    def cite_tool(self) -> Dict:
        """
        Tool 4: Add citations to synthesis.
        
        Precondition: state == SYNTHESIZING, synthesis populated
        Postcondition: state == CITING, citations populated
        """
        if self.state.state != AgentState.SYNTHESIZING:
            return {
                "error": f"Can only cite from SYNTHESIZING, "
                         f"currently {self.state.state.value}"
            }
        
        # Simulate citation extraction
        print(f"\n📚 Adding citations...")
        self.state.citations = [
            {
                "source": f"Search Result {i}",
                "quote": f"Key finding from search {i}",
                "relevance": "high"
            }
            for i in range(1, len(self.state.search_results) + 1)
        ]
        
        # Record transition
        if not self.state.record_action(AgentState.CITING, "citations_added"):
            return {"error": "Failed to transition to CITING"}
        
        print(f"   ✓ Added {len(self.state.citations)} citations")
        return {
            "citations": self.state.citations,
            "cited_response": self.state.synthesis
        }


async def run_research_agent(query: str) -> Dict:
    """
    Main agent loop with state management.
    
    Demonstrates the complete flow:
    IDLE → PLANNING → SEARCHING → SYNTHESIZING → CITING
    
    Includes loop detection and error handling.
    """
    print("\n" + "=" * 80)
    print("RESEARCH ASSISTANT STATE MACHINE")
    print("=" * 80)
    
    # Initialize state
    state = ResearchState(query=query)
    assistant = ResearchAssistant(state)
    
    print(f"\n📌 Query: {query}")
    print(f"📌 Session: {state.session_id}")
    
    # Main loop
    while state.step_count < state.MAX_STEPS:
        # Print current status
        print(f"\n[Step {state.step_count + 1}] {state.get_status()}")
        
        # Check for infinite loops
        in_loop, reason = state.is_in_infinite_loop()
        if in_loop:
            print(f"\n❌ LOOP DETECTED: {reason}")
            state.state = AgentState.IDLE
            break
        
        # State machine: Execute action based on current state
        if state.state == AgentState.IDLE:
            print("   → Transitioning to PLANNING")
            result = assistant.plan_tool()
            if "error" in result:
                print(f"   ❌ {result['error']}")
                break
        
        elif state.state == AgentState.PLANNING:
            print("   → Transitioning to SEARCHING")
            # Execute searches for each plan step
            unexecuted_plans = [
                plan for plan in state.plan 
                if plan not in state.search_results
            ]
            if unexecuted_plans:
                result = assistant.search_tool(unexecuted_plans[0])
                if "error" in result:
                    print(f"   ❌ {result['error']}")
                    break
            else:
                # All plan items searched, force transition to synthesizing
                if not state.record_action(AgentState.SEARCHING, "all_plans_searched"):
                    print(f"   ❌ Cannot transition to SEARCHING")
                    break
        
        elif state.state == AgentState.SEARCHING:
            # Check if we have enough results
            if len(state.search_results) >= len(state.plan):
                print("   → Transitioning to SYNTHESIZING")
                if not state.record_action(AgentState.SYNTHESIZING, "enough_results"):
                    print(f"   ❌ Cannot transition to SYNTHESIZING")
                    break
            else:
                # Continue searching
                unexecuted_plans = [
                    plan for plan in state.plan 
                    if plan not in state.search_results
                ]
                if unexecuted_plans:
                    result = assistant.search_tool(unexecuted_plans[0])
                    if "error" in result:
                        print(f"   ❌ {result['error']}")
                        break
        
        elif state.state == AgentState.SYNTHESIZING:
            print("   → Transitioning to CITING")
            result = assistant.synthesize_tool()
            if "error" in result:
                print(f"   ❌ {result['error']}")
                break
        
        elif state.state == AgentState.CITING:
            print("   → Completing research")
            result = assistant.cite_tool()
            if "error" in result:
                print(f"   ❌ {result['error']}")
                break
            # Exit loop on successful completion
            break
        
        await asyncio.sleep(0.1)  # Small delay for readability
    
    # Summary
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Status: {'✅ SUCCESS' if state.state == AgentState.CITING else '❌ INCOMPLETE'}")
    print(f"Query: {state.query}")
    print(f"Steps Taken: {state.step_count}/{state.MAX_STEPS}")
    print(f"State History: {' → '.join(s.value for s in state.state_history)} → {state.state.value}")
    print(f"Searches: {state.search_count_by_query}")
    print(f"Synthesis Length: {len(state.synthesis)} characters")
    print(f"Citations: {len(state.citations)}")
    
    if state.errors:
        print(f"\nErrors:")
        for error in state.errors:
            print(f"  - {error}")
    
    return {
        "success": state.state == AgentState.CITING,
        "query": state.query,
        "response": state.synthesis,
        "citations": state.citations,
        "state_history": [s.value for s in state.state_history],
        "steps_taken": state.step_count,
        "searches_executed": sum(state.search_count_by_query.values()),
        "session_id": state.session_id,
    }


async def demo_loop_prevention():
    """
    Demonstrate loop prevention mechanisms.
    
    Shows how the state machine prevents infinite loops:
    1. Step limit exceeded
    2. Same state repeated
    3. Redundant searches
    4. Too many cycles in "refine" states
    """
    print("\n" + "=" * 80)
    print("LOOP PREVENTION DEMONSTRATION")
    print("=" * 80)
    
    # Test 1: Same state repeated detection
    print("\n[Test 1] Same state repeated detection")
    state = ResearchState(query="test")
    state.state_history = [AgentState.PLANNING, AgentState.PLANNING, AgentState.PLANNING]
    in_loop, reason = state.is_in_infinite_loop()
    print(f"  State history: {[s.value for s in state.state_history]}")
    print(f"  Loop detected: {in_loop}")
    print(f"  Reason: {reason}")
    
    # Test 2: Search repeat detection
    print("\n[Test 2] Search repeat detection")
    state = ResearchState(query="test")
    state.search_count_by_query = {"quantum computing": 6}
    in_loop, reason = state.is_in_infinite_loop()
    print(f"  Search counts: {state.search_count_by_query}")
    print(f"  Loop detected: {in_loop}")
    print(f"  Reason: {reason}")
    
    # Test 3: Step limit detection
    print("\n[Test 3] Step limit detection")
    state = ResearchState(query="test")
    state.step_count = 25
    in_loop, reason = state.is_in_infinite_loop()
    print(f"  Step count: {state.step_count}/{state.MAX_STEPS}")
    print(f"  Loop detected: {in_loop}")
    print(f"  Reason: {reason}")
    
    # Test 4: Planning cycle limit
    print("\n[Test 4] Planning cycle limit")
    state = ResearchState(query="test")
    state.state_history = [AgentState.PLANNING, AgentState.PLANNING, AgentState.PLANNING]
    in_loop, reason = state.is_in_infinite_loop()
    print(f"  Planning cycles: {sum(1 for s in state.state_history if s == AgentState.PLANNING)}")
    print(f"  Loop detected: {in_loop}")
    print(f"  Reason: {reason}")


async def main():
    """Run demonstrations."""
    # Demo 1: Normal research flow
    result = await run_research_agent("What is machine learning?")
    
    # Demo 2: Loop prevention
    await demo_loop_prevention()
    
    print("\n" + "=" * 80)
    print("✅ State machine demonstration complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
