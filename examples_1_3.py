"""
Work Product 1.3 Examples: Understanding the Runnable Protocol

This module demonstrates the Runnable interface and how it composes.

LEARNING OBJECTIVES:
════════════════════
- See how invoke(), batch(), stream(), ainvoke() work
- Understand Runnable composition as a DAG
- Build custom Runnables
- Trace execution through the graph
- Optimize for different use cases

EXAMPLES COVERED:
════════════════
1. The Four Execution Modes
   - invoke() - synchronous single call
   - batch() - parallel multiple inputs
   - stream() - incremental output
   - ainvoke() - asynchronous single call

2. Custom Runnables
   - Implement the Runnable protocol
   - Understand the contract
   - Compose with existing chains

3. Execution Tracing
   - See the DAG structure
   - Track execution flow
   - Understand composition semantics

4. Performance Patterns
   - When to use batch()
   - When to use stream()
   - When to use ainvoke()

5. Practical Production Patterns
   - Error handling with fallbacks
   - Conditional routing
   - Caching results
"""

import asyncio
import time
from typing import Any, Iterator, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    Runnable,
    RunnableConfig,
    RunnableLambda,
    RunnableParallel,
    RunnableBranch,
)
from langchain_core.callbacks import BaseCallbackHandler

# ============================================================================
# EXAMPLE 1: The Four Execution Modes
# ============================================================================

def example_1_four_modes():
    """
    Demonstrate invoke(), batch(), stream(), ainvoke().
    
    GOAL: See the same chain executed four different ways
          and understand when to use each.
    
    KEY INSIGHT: All four modes produce the same RESULT,
                 but with different execution characteristics.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: The Four Execution Modes")
    print("="*70)
    
    # Build a simple chain
    prompt = ChatPromptTemplate.from_template(
        "Write a one-sentence definition of: {concept}"
    )
    model = ChatOpenAI(model="gpt-4-mini")
    chain = prompt | model
    
    # ─────────────────────────────────────────────────────────────────
    # MODE 1: invoke() - Single, Synchronous
    # ─────────────────────────────────────────────────────────────────
    print("\n1️⃣  invoke() - Single, Synchronous")
    print("-" * 70)
    print("   Timing: Waits for result (blocking)")
    print("   Use case: Simple, one-off requests")
    
    start = time.time()
    result = chain.invoke({"concept": "machine learning"})
    elapsed = time.time() - start
    
    print(f"   ✓ Result: {result.content[:60]}...")
    print(f"   ⏱️  Time: {elapsed:.2f}s")
    
    # ─────────────────────────────────────────────────────────────────
    # MODE 2: batch() - Multiple, Parallel
    # ─────────────────────────────────────────────────────────────────
    print("\n2️⃣  batch() - Multiple, Parallel")
    print("-" * 70)
    print("   Timing: Parallel execution (non-blocking)")
    print("   Use case: Multiple items, high throughput")
    
    concepts = ["AI", "machine learning", "neural networks"]
    
    start = time.time()
    results = chain.batch([{"concept": c} for c in concepts])
    elapsed = time.time() - start
    
    print(f"   ✓ Processed {len(results)} items")
    print(f"   ⏱️  Time: {elapsed:.2f}s (vs {len(results) * elapsed:.2f}s serial)")
    for concept, result in zip(concepts, results):
        print(f"     - {concept}: {result.content[:40]}...")
    
    # ─────────────────────────────────────────────────────────────────
    # MODE 3: stream() - Single, Streaming
    # ─────────────────────────────────────────────────────────────────
    print("\n3️⃣  stream() - Single, Streaming")
    print("-" * 70)
    print("   Timing: Immediate first token, rest follow")
    print("   Use case: Real-time UX, interactive apps")
    
    print("   Output: ", end="", flush=True)
    start = time.time()
    for chunk in chain.stream({"concept": "quantum computing"}):
        if hasattr(chunk, 'content'):
            print(chunk.content, end="", flush=True)
    elapsed = time.time() - start
    
    print(f"\n   ⏱️  Time: {elapsed:.2f}s (perceived latency lower)")
    
    # ─────────────────────────────────────────────────────────────────
    # MODE 4: ainvoke() - Single, Asynchronous
    # ─────────────────────────────────────────────────────────────────
    print("\n4️⃣  ainvoke() - Single, Asynchronous")
    print("-" * 70)
    print("   Timing: Non-blocking (event loop cooperates)")
    print("   Use case: Web apps (FastAPI), high concurrency")
    
    async def async_example():
        start = time.time()
        result = await chain.ainvoke({"concept": "deep learning"})
        elapsed = time.time() - start
        
        print(f"   ✓ Result: {result.content[:60]}...")
        print(f"   ⏱️  Time: {elapsed:.2f}s")
        print(f"   ℹ️  Event loop did not block (other tasks could run)")
    
    asyncio.run(async_example())


# ============================================================================
# EXAMPLE 2: Custom Runnable (Understanding the Contract)
# ============================================================================

def example_2_custom_runnable():
    """
    Build a custom Runnable from scratch.
    
    GOAL: Understand what a Runnable is by implementing one.
    
    KEY INSIGHT: A Runnable is just an object with four methods.
                 The contract is simple but powerful.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Custom Runnable")
    print("="*70)
    
    class TimedRunnable(Runnable):
        """
        A simple custom Runnable that multiplies input by a factor.
        
        This demonstrates:
        - Required methods (invoke)
        - Optional optimized methods (batch, stream)
        - Composition with other Runnables
        """
        
        def __init__(self, factor: float = 2.0, name: str = "Multiplier"):
            super().__init__()
            self.factor = factor
            self.name = name
        
        def invoke(self, input: float, config: Optional[RunnableConfig] = None) -> float:
            """Core synchronous method."""
            return input * self.factor
        
        def batch(self, inputs: List[float], config: Optional[RunnableConfig] = None) -> List[float]:
            """Optimized batch (not necessary, but good for performance)."""
            return [self.invoke(x, config) for x in inputs]
        
        def stream(self, input: float, config: Optional[RunnableConfig] = None) -> Iterator[float]:
            """Stream mode (yields once for this simple operation)."""
            yield self.invoke(input, config)
        
        async def ainvoke(self, input: float, config: Optional[RunnableConfig] = None) -> float:
            """Async mode (wraps sync implementation)."""
            return self.invoke(input, config)
    
    # Usage
    print("\n📊 Custom Runnable Demonstration:")
    print("-" * 70)
    
    doubler = TimedRunnable(factor=2.0, name="Doubler")
    tripler = TimedRunnable(factor=3.0, name="Tripler")
    
    # Single execution
    result = doubler.invoke(5)
    print(f"doubler.invoke(5) = {result}")  # 10
    
    # Batch execution
    results = doubler.batch([1, 2, 3, 4, 5])
    print(f"doubler.batch([1,2,3,4,5]) = {results}")  # [2,4,6,8,10]
    
    # Streaming
    print(f"doubler.stream(7) = ", end="")
    for chunk in doubler.stream(7):
        print(chunk, end=" ")
    print()  # 14
    
    # Composition with other Runnables
    print("\n🔗 Composition (custom | builtin):")
    print("-" * 70)
    
    # Create a chain: doubler | tripler
    chain = doubler | tripler
    
    print(f"chain.invoke(5) = {chain.invoke(5)}")  # 5 * 2 * 3 = 30
    print(f"chain.batch([1,2,3]) = {chain.batch([1,2,3])}")  # [6, 12, 18]
    
    print("\n✅ Key insight:")
    print("   - Custom Runnable is just 4 methods")
    print("   - Composes naturally with other Runnables")
    print("   - Enables infinite chain complexity from simple units")


# ============================================================================
# EXAMPLE 3: Composition as a DAG
# ============================================================================

def example_3_dag_composition():
    """
    See how composition creates a directed acyclic graph (DAG).
    
    GOAL: Understand that chains are not strings—they're DAGs.
    
    KEY INSIGHT: Complex workflows are just graphs of simple Runnables.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Composition as a DAG")
    print("="*70)
    
    # Simple components
    format_name = RunnableLambda(lambda x: f"Topic: {x['topic']}")
    format_query = RunnableLambda(lambda x: f"Query: {x['query']}")
    
    # Parallel processing (RunnableParallel)
    parallel = RunnableParallel(
        name_formatted=format_name,
        query_formatted=format_query,
    )
    
    # Merge results
    merge = RunnableLambda(lambda x: f"{x['name_formatted']} | {x['query_formatted']}")
    
    # Full workflow
    workflow = parallel | merge
    
    print("\n📊 Workflow Structure:")
    print("-" * 70)
    print("""
    Input: {"topic": "AI", "query": "what is"}
       ↓
    [Parallel]
    /        \\
   format_name  format_query
   /            \\
   Topic: AI    Query: what is
    \\          /
     [Merge]
        ↓
    Output: "Topic: AI | Query: what is"
    """)
    
    # Execute
    input_data = {"topic": "AI", "query": "what is"}
    
    # Single execution
    result = workflow.invoke(input_data)
    print(f"\n✓ invoke() → {result}")
    
    # Batch (parallel works at batch level too)
    inputs = [
        {"topic": "AI", "query": "what is"},
        {"topic": "ML", "query": "definition"},
    ]
    results = workflow.batch(inputs)
    print(f"\n✓ batch() →")
    for r in results:
        print(f"   {r}")


# ============================================================================
# EXAMPLE 4: Execution Tracing
# ============================================================================

def example_4_tracing():
    """
    See execution flow through the Runnable graph.
    
    GOAL: Understand how tracing works and what information is captured.
    
    KEY INSIGHT: Every Runnable in the DAG can be traced independently.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Execution Tracing")
    print("="*70)
    
    # Custom callback to trace execution
    class TraceCallback(BaseCallbackHandler):
        """Print trace of execution."""
        
        def on_chain_start(self, serialized, inputs, **kwargs):
            chain_type = serialized.get("id", ["unknown"])[-1]
            print(f"  ▶️  START: {chain_type}")
        
        def on_chain_end(self, outputs, **kwargs):
            print(f"  ◀️  END")
        
        def on_llm_start(self, serialized, prompts, **kwargs):
            print(f"    🤖 LLM CALL")
        
        def on_llm_end(self, response, **kwargs):
            tokens = response.llm_output.get("token_usage", {})
            print(f"    ✅ LLM DONE (tokens: {tokens.get('total_tokens', '?')})")
    
    # Build chain
    prompt = ChatPromptTemplate.from_template("Explain {concept}")
    model = ChatOpenAI(model="gpt-4-mini")
    chain = prompt | model
    
    # Execute with tracing
    print("\n📋 Execution Trace:")
    print("-" * 70)
    
    config = RunnableConfig(callbacks=[TraceCallback()])
    result = chain.invoke(
        {"concept": "quantum computing"},
        config=config
    )
    
    print(f"\n✓ Final output: {result.content[:50]}...")


# ============================================================================
# EXAMPLE 5: Conditional Routing (RunnableBranch)
# ============================================================================

def example_5_conditional_routing():
    """
    Route execution based on input (RunnableBranch).
    
    GOAL: See how to implement conditional logic in Runnable DAGs.
    
    KEY INSIGHT: Branching is a Runnable too—it composes naturally.
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Conditional Routing")
    print("="*70)
    
    # Define branches
    def is_math(x):
        return "math" in x.get("query", "").lower()
    
    def is_code(x):
        return "code" in x.get("query", "").lower()
    
    # Create specialized chains (simplified)
    math_chain = RunnableLambda(
        lambda x: f"[MATH ANSWER]: Calculating {x['query']}"
    )
    code_chain = RunnableLambda(
        lambda x: f"[CODE ANSWER]: Writing code for {x['query']}"
    )
    general_chain = RunnableLambda(
        lambda x: f"[GENERAL ANSWER]: Explaining {x['query']}"
    )
    
    # Create router
    router = RunnableBranch(
        (is_math, math_chain),
        (is_code, code_chain),
        general_chain,  # default
    )
    
    # Test different inputs
    print("\n🔀 Routing Examples:")
    print("-" * 70)
    
    test_queries = [
        {"query": "solve the math problem"},
        {"query": "write python code"},
        {"query": "what is AI"},
    ]
    
    for q in test_queries:
        result = router.invoke(q)
        print(f"  Query: {q['query']:<30} → {result}")
    
    print("\n✅ Key insight:")
    print("   Router examines input and chooses appropriate chain")
    print("   Different code paths for different inputs")
    print("   All implemented as Runnables in a DAG")


# ============================================================================
# EXAMPLE 6: Batch Performance Comparison
# ============================================================================

def example_6_batch_performance():
    """
    Compare performance: serial invoke() vs batch().
    
    GOAL: See the performance benefit of batch() mode.
    
    KEY INSIGHT: batch() is dramatically faster for N items.
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Batch Performance Comparison")
    print("="*70)
    
    prompt = ChatPromptTemplate.from_template("Quick fact about {topic}:")
    model = ChatOpenAI(model="gpt-4-mini")
    chain = prompt | model
    
    topics = ["python", "javascript", "golang", "rust"]
    
    # ─────────────────────────────────────────────────────────────────
    # Method 1: Serial invoke() in loop
    # ─────────────────────────────────────────────────────────────────
    print("\n1️⃣  Serial: loop with invoke()")
    print("-" * 70)
    
    start = time.time()
    results_serial = []
    for topic in topics:
        result = chain.invoke({"topic": topic})
        results_serial.append(result)
    serial_time = time.time() - start
    
    print(f"   ⏱️  Time: {serial_time:.2f}s ({serial_time/len(topics):.2f}s per item)")
    
    # ─────────────────────────────────────────────────────────────────
    # Method 2: Parallel batch()
    # ─────────────────────────────────────────────────────────────────
    print("\n2️⃣  Parallel: batch()")
    print("-" * 70)
    
    start = time.time()
    results_batch = chain.batch([{"topic": t} for t in topics])
    batch_time = time.time() - start
    
    print(f"   ⏱️  Time: {batch_time:.2f}s ({batch_time/len(topics):.2f}s per item)")
    
    # Comparison
    print("\n📊 Comparison:")
    print("-" * 70)
    print(f"   Serial time: {serial_time:.2f}s")
    print(f"   Batch time:  {batch_time:.2f}s")
    print(f"   Speedup:     {serial_time/batch_time:.1f}x faster with batch()")
    print(f"\n   💡 Lesson: Use batch() for N items!")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("WORK PRODUCT 1.3 EXAMPLES: The Runnable Protocol")
    print("█" * 70)
    
    print("\nThese examples demonstrate:")
    print("  1. The four execution modes (invoke, batch, stream, ainvoke)")
    print("  2. Building custom Runnables")
    print("  3. Composition as a DAG")
    print("  4. Execution tracing")
    print("  5. Conditional routing")
    print("  6. Batch performance")
    
    try:
        # Run examples
        example_1_four_modes()
        example_2_custom_runnable()
        example_3_dag_composition()
        example_4_tracing()
        example_5_conditional_routing()
        example_6_batch_performance()
        
        print("\n" + "█" * 70)
        print("✅ All examples completed successfully!")
        print("█" * 70)
        print("\nNext Steps:")
        print("  - Read WP-1.3-The-Runnable-Protocol.md for deep dive")
        print("  - Review LangChain source: langchain-core/runnables/base.py")
        print("  - Build your own custom Runnable")
        print("  - Use batch() and stream() in your applications")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
