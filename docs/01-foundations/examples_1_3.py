"""
╔══════════════════════════════════════════════════════════════════════════════╗
║            WORK PRODUCT 1.3: THE RUNNABLE PROTOCOL - EXAMPLES                ║
║                                                                              ║
║  Complete, practical demonstrations of the Runnable interface in LangChain   ║
╚══════════════════════════════════════════════════════════════════════════════╝

📚 PURPOSE:
───────────
This module demonstrates the Runnable protocol through six hands-on examples.
You will see how the four execution modes work, how Runnables compose into DAGs,
and how to build production patterns.

🎯 LEARNING OBJECTIVES:
───────────────────────
By the end of these examples, you will:
  ✓ Understand the four execution modes (invoke, batch, stream, ainvoke)
  ✓ Know when to use each mode
  ✓ See how Runnables compose into directed acyclic graphs (DAGs)
  ✓ Build custom Runnables from scratch
  ✓ Trace execution flow through complex chains
  ✓ Optimize performance using batch() and stream()
  ✓ Implement conditional routing with RunnableBranch
  ✓ Understand the contract that makes all Runnables composable

🔬 EXAMPLES COVERED:
─────────────────────

EXAMPLE 1: The Four Execution Modes
────────────────────────────────────
Demonstrates: invoke(), batch(), stream(), ainvoke()
Focus: Understanding execution characteristics
Output: Timing comparisons, result formats
Key Lesson: Same chain, different execution modes, different performance

EXAMPLE 2: Custom Runnables
──────────────────────────────
Demonstrates: Building a Runnable from scratch
Focus: Understanding the protocol contract
Output: Custom TimedRunnable class, composition
Key Lesson: Runnables are simple—just 4 methods

EXAMPLE 3: Composition as a DAG
──────────────────────────────────
Demonstrates: RunnableParallel, branching, merging
Focus: How pipes create graphs
Output: Parallel execution diagram, batch composition
Key Lesson: Complex workflows = simple components + composition

EXAMPLE 4: Execution Tracing
────────────────────────────────
Demonstrates: Custom callbacks, execution flow
Focus: Observability and debugging
Output: Trace of chain execution step-by-step
Key Lesson: Every Runnable reports execution to callbacks

EXAMPLE 5: Conditional Routing
────────────────────────────────
Demonstrates: RunnableBranch, routing logic
Focus: Conditional execution patterns
Output: Different code paths for different inputs
Key Lesson: Complex routing logic is still a Runnable

EXAMPLE 6: Batch Performance Comparison
─────────────────────────────────────────
Demonstrates: Serial invoke() vs parallel batch()
Focus: Performance optimization
Output: Timing comparison, speedup calculation
Key Lesson: batch() is dramatically faster for N items

🔑 KEY CONCEPTS:
────────────────
1. RUNNABLE PROTOCOL
   Every Runnable implements four methods:
   - invoke(input) → output              [sync single]
   - batch(inputs) → [output]            [sync parallel]
   - stream(input) → Iterator[output]    [sync streaming]
   - ainvoke(input) → output             [async single]

2. COMPOSITION
   Runnables connect via pipe operator:
   chain = runnable_a | runnable_b | runnable_c
   
   This creates a DAG, not a string!

3. EQUIVALENCE
   All four modes return the SAME RESULT,
   but with different execution characteristics.

💡 BEST PRACTICES:
──────────────────
• Use invoke() for single requests or simple scripts
• Use batch() when processing multiple items
• Use stream() for interactive UX (web apps, chatbots)
• Use ainvoke() in async contexts (FastAPI, async frameworks)
• Compose Runnables instead of writing monolithic functions
• Always use batch() > serial invoke() loop for performance

⚠️  COMMON MISTAKES:
────────────────────
✗ Using invoke() in a loop for N items (use batch() instead!)
✗ Blocking the event loop with invoke() in async code (use ainvoke())
✗ Not streaming when you need real-time UX (stream() is faster to first token)
✗ Building monolithic chains instead of composable Runnables
✗ Not understanding that composition creates a DAG (it's not sequential!)

📋 USAGE:
──────────
Run this file:
    python examples_1_3.py

Each example is self-contained and can be modified for learning.
Read the comments carefully—they explain the WHY, not just the WHAT.

📖 REFERENCES:
───────────────
- WP-1.3-The-Runnable-Protocol.md (full documentation)
- ADR-1.2-Hello-World-Three-Ways.md (when to use what)
- LangChain source: langchain-core/runnables/base.py
"""

import asyncio
import time
from typing import Iterator, Optional, List
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
    ╔════════════════════════════════════════════════════════════════════════╗
    ║                    EXAMPLE 1: FOUR EXECUTION MODES                     ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    GOAL:
    ─────
    Demonstrate all four execution modes of the Runnable protocol:
      invoke()    → single input, synchronous, blocking
      batch()     → multiple inputs, synchronous, parallel
      stream()    → single input, synchronous, streaming chunks
      ainvoke()   → single input, asynchronous, non-blocking
    
    KEY INSIGHT:
    ────────────
    All four modes produce the SAME OUTPUT, but with different characteristics:
    • invoke(): Simple, blocking, good for scripts
    • batch(): Fast, parallel, good for processing N items
    • stream(): Real-time, good for interactive UX
    • ainvoke(): Non-blocking, good for web apps (FastAPI, etc.)
    
    CRITICAL LEARNING:
    ──────────────────
    • invoke() is NOT always correct—choose based on context!
    • batch() is faster than invoke() loop for N items
    • stream() has lower perceived latency (first token ASAP)
    • ainvoke() doesn't block other tasks in event loop
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: The Four Execution Modes")
    print("="*70)
    
    # ─────────────────────────────────────────────────────────────────
    # SETUP: Build a simple chain
    # ─────────────────────────────────────────────────────────────────
    # A chain is: [prompt template] | [LLM model]
    # The pipe operator (|) creates a composition, not a sequence!
    
    prompt = ChatPromptTemplate.from_template(
        "Write a one-sentence definition of: {concept}"
    )
    model = ChatOpenAI(model="gpt-4-mini")
    
    # This chain is a Runnable that:
    # 1. Takes a dict {"concept": str}
    # 2. Formats it into a prompt
    # 3. Sends it to the LLM
    # 4. Returns the LLM's response
    chain = prompt | model
    
    # ─────────────────────────────────────────────────────────────────
    # MODE 1: invoke() - Single, Synchronous, Blocking
    # ─────────────────────────────────────────────────────────────────
    # Use when: One-off request, simple script, need result immediately
    # Performance: Blocks until complete, simple to understand
    # Tradeoff: Can't process multiple items efficiently
    
    print("\n1️⃣  invoke() - Single, Synchronous, Blocking")
    print("-" * 70)
    print("   📌 Behavior: Code waits for result (blocking)")
    print("   📌 Use case: Simple, one-off requests")
    print("   📌 Best for: Scripts, synchronous contexts")
    print("   📌 Speed: Slow for N items (use batch() instead!)")
    
    start = time.time()
    result = chain.invoke({"concept": "machine learning"})
    elapsed = time.time() - start
    
    print(f"   ✓ Result: {result.content[:60]}...")
    print(f"   ⏱️  Time: {elapsed:.2f}s")
    
    # ─────────────────────────────────────────────────────────────────
    # MODE 2: batch() - Multiple, Parallel
    # ─────────────────────────────────────────────────────────────────
    # Use when: Multiple items to process, need good throughput
    # Performance: Parallel execution, respects rate limits
    # Tradeoff: Must have all inputs upfront, slightly more complex
    # IMPORTANT: This is N times faster than invoke() loop!
    
    print("\n2️⃣  batch() - Multiple, Parallel")
    print("-" * 70)
    print("   📌 Behavior: Multiple inputs processed in parallel")
    print("   📌 Use case: Batch jobs, data processing")
    print("   📌 Best for: Processing N items efficiently")
    print("   📌 Speed: ~N times faster than invoke() loop!")
    
    concepts = ["AI", "machine learning", "neural networks"]
    
    start = time.time()
    results = chain.batch([{"concept": c} for c in concepts])
    elapsed = time.time() - start
    
    print(f"   ✓ Processed {len(results)} items")
    # Calculate what serial time would be (approximation)
    print(f"   ⏱️  Parallel time: {elapsed:.2f}s")
    print(f"   ℹ️  Serial would be: ~{len(results) * elapsed:.2f}s")
    for concept, result in zip(concepts, results):
        print(f"     - {concept}: {result.content[:40]}...")
    
    # ─────────────────────────────────────────────────────────────────
    # MODE 3: stream() - Single, Streaming
    # ─────────────────────────────────────────────────────────────────
    # Use when: Need real-time output, interactive experience
    # Performance: First token arrives ASAP, rest follow
    # Tradeoff: More complex to handle, need to deal with chunks
    # BEST FOR: Web UIs, chatbots, interactive apps
    
    print("\n3️⃣  stream() - Single, Streaming")
    print("-" * 70)
    print("   📌 Behavior: Output arrives as chunks (e.g., token by token)")
    print("   📌 Use case: Real-time UX, interactive apps")
    print("   📌 Best for: Web UIs, chatbots")
    print("   📌 Speed: First chunk ASAP (perceived latency is lower)")
    
    print("   Output: ", end="", flush=True)
    start = time.time()
    for chunk in chain.stream({"concept": "quantum computing"}):
        # The chunk is the output from the LLM
        # For ChatOpenAI, it's an AIMessage with .content
        if hasattr(chunk, 'content'):
            print(chunk.content, end="", flush=True)
    elapsed = time.time() - start
    
    print(f"\n   ⏱️  Time: {elapsed:.2f}s (but user sees first token in ~0.1s)")
    
    # ─────────────────────────────────────────────────────────────────
    # MODE 4: ainvoke() - Single, Asynchronous
    # ─────────────────────────────────────────────────────────────────
    # Use when: In async context (FastAPI, async functions)
    # Performance: Non-blocking, event loop can run other tasks
    # Tradeoff: Must be in async function, need await
    # MUST USE: In FastAPI endpoints, async Python applications
    
    print("\n4️⃣  ainvoke() - Single, Asynchronous")
    print("-" * 70)
    print("   📌 Behavior: Non-blocking (event loop cooperates)")
    print("   📌 Use case: Web apps (FastAPI), high concurrency")
    print("   📌 Best for: Async Python contexts")
    print("   📌 Speed: Same as invoke(), but doesn't block event loop")
    
    async def async_example():
        # Inside async function, we can use await
        start = time.time()
        result = await chain.ainvoke({"concept": "deep learning"})
        elapsed = time.time() - start
        
        print(f"   ✓ Result: {result.content[:60]}...")
        print(f"   ⏱️  Time: {elapsed:.2f}s")
        print("   ℹ️  Event loop was not blocked (other tasks could run)")
    
    # Run the async function
    asyncio.run(async_example())
    
    # ─────────────────────────────────────────────────────────────────
    # SUMMARY TABLE
    # ─────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("SUMMARY: When to Use Each Mode")
    print("="*70)
    print("""
    ┌──────────┬──────────┬──────────┬─────────────┬──────────────────┐
    │ Mode     │ Inputs   │ Blocking │ Performance │ Best For         │
    ├──────────┼──────────┼──────────┼─────────────┼──────────────────┤
    │ invoke   │ 1        │ Yes      │ Slow for N  │ Scripts, simple  │
    │ batch    │ N        │ Yes      │ Fast (N×)   │ Data processing  │
    │ stream   │ 1        │ Yes      │ Fast 1st    │ Real-time UX     │
    │ ainvoke  │ 1        │ No       │ Same/slow   │ Async contexts   │
    └──────────┴──────────┴──────────┴─────────────┴──────────────────┘
    
    KEY DECISION RULE:
    ──────────────────
    1. Do you have N items to process? → Use batch()
    2. Do you need real-time output?   → Use stream()
    3. Are you in async context?       → Use ainvoke()
    4. Otherwise?                      → Use invoke()
    """)


# ============================================================================
# EXAMPLE 2: Custom Runnable (Understanding the Contract)
# ============================================================================

def example_2_custom_runnable():
    """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║                      EXAMPLE 2: CUSTOM RUNNABLE                        ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    GOAL:
    ─────
    Build a Runnable from scratch to understand the protocol contract.
    This is THE MOST IMPORTANT EXAMPLE—it shows what a Runnable really is.
    
    KEY INSIGHT:
    ────────────
    A Runnable is just an object with four methods:
      invoke(input) → output
      batch(inputs) → [output]
      stream(input) → Iterator[output]
      ainvoke(input) → output
    
    That's it! No magic, no complexity.
    
    WHY THIS MATTERS:
    ─────────────────
    Once you understand the contract, you can:
    • Build custom domain-specific Runnables
    • Compose them seamlessly with existing LangChain components
    • Build infinitely complex systems from simple units
    • Optimize performance by implementing custom batch/stream logic
    
    LEARNING OBJECTIVES:
    ────────────────────
    1. See the minimal interface required
    2. Understand how methods can be derived from invoke()
    3. See composition with standard LangChain Runnables
    4. Understand that complexity emerges from composition
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Custom Runnable (Understanding the Contract)")
    print("="*70)
    
    # ─────────────────────────────────────────────────────────────────
    # PART A: Define a Custom Runnable
    # ─────────────────────────────────────────────────────────────────
    
    class TimedRunnable(Runnable):
        """
        A simple custom Runnable that multiplies input by a factor.
        
        This demonstrates:
        ✓ Required methods (invoke)
        ✓ Optional optimized methods (batch, stream, ainvoke)
        ✓ How to make custom Runnables composable
        
        CONTRACT:
        ──────────
        Every Runnable must implement:
          invoke(input, config=None) → output
        
        And may optimize:
          batch(inputs, config=None) → [output]
          stream(input, config=None) → Iterator[output]
          ainvoke(input, config=None) → output
        
        If you don't implement the optional methods,
        the base class provides default implementations (usually from invoke()).
        """
        
        def __init__(self, factor: float = 2.0, name: str = "Multiplier"):
            """
            Initialize the Runnable.
            
            Args:
                factor: Multiplication factor (default 2.0)
                name: Name for debugging/logging (default "Multiplier")
            
            Notes:
                - Always call super().__init__()
                - Use this for configuration, not execution
            """
            super().__init__()
            self.factor = factor
            self.name = name
        
        def invoke(self, input: float, config: Optional[RunnableConfig] = None) -> float:
            """
            Core synchronous execution method (REQUIRED).
            
            This is the ONLY method you MUST implement.
            All other methods can be derived from this.
            
            Args:
                input: The input value (a float in this example)
                config: Optional configuration (passed by framework)
            
            Returns:
                output: The computed result (float)
            
            Notes:
                - Must be synchronous (no async/await)
                - Should not block event loop (that's what ainvoke is for)
                - Exceptions are passed up to caller
            """
            # In this simple example: multiply input by factor
            return input * self.factor
        
        def batch(self, inputs: List[float], config: Optional[RunnableConfig] = None) -> List[float]:
            """
            Batch execution (OPTIONAL but RECOMMENDED).
            
            This is optional, but implementing it allows optimization.
            For example, ChatOpenAI.batch() batches API calls instead of 
            making N separate requests.
            
            Args:
                inputs: List of input values
                config: Optional configuration
            
            Returns:
                outputs: List of results (same order as inputs)
            
            Notes:
                - Results MUST be in same order as inputs
                - Can be optimized for your specific Runnable
                - Default implementation: just calls invoke() for each
            """
            # Simple implementation: invoke for each input
            # A real implementation might batch API calls, use vectorization, etc.
            return [self.invoke(x, config) for x in inputs]
        
        def stream(self, input: float, config: Optional[RunnableConfig] = None) -> Iterator[float]:
            """
            Streaming execution (OPTIONAL).
            
            This is useful when your computation produces incremental output.
            For example, LLM.stream() yields tokens as they arrive.
            
            Args:
                input: The input value
                config: Optional configuration
            
            Yields:
                Chunks of output (in our case, just one float)
            
            Notes:
                - Yields chunks of output
                - For our simple multiplier, just one yield
                - For LLMs, would yield token by token
            """
            # This simple example yields once, but imagine an LLM yielding tokens
            yield self.invoke(input, config)
        
        async def ainvoke(self, input: float, config: Optional[RunnableConfig] = None) -> float:
            """
            Asynchronous execution (OPTIONAL).
            
            Use this when you need async/await.
            For example, making async HTTP requests without blocking.
            
            Args:
                input: The input value
                config: Optional configuration
            
            Returns:
                output: The computed result
            
            Notes:
                - Use async/await syntax
                - Doesn't block the event loop
                - Must return the same result as invoke()
            """
            # Our simple example just wraps invoke()
            # A real async version would do async I/O here
            return self.invoke(input, config)
    
    # ─────────────────────────────────────────────────────────────────
    # PART B: Use the Custom Runnable
    # ─────────────────────────────────────────────────────────────────
    
    print("\n📊 Custom Runnable Demonstration:")
    print("-" * 70)
    
    # Create instances
    doubler = TimedRunnable(factor=2.0, name="Doubler")
    tripler = TimedRunnable(factor=3.0, name="Tripler")
    
    print("\n1️⃣  Single Execution (invoke)")
    print("   doubler.invoke(5) = ", end="")
    result = doubler.invoke(5)
    print(result)  # 10
    print("   ✓ Result is 5 * 2.0 = 10")
    
    print("\n2️⃣  Batch Execution (batch)")
    print("   doubler.batch([1, 2, 3, 4, 5]) = ", end="")
    results = doubler.batch([1, 2, 3, 4, 5])
    print(results)  # [2, 4, 6, 8, 10]
    print("   ✓ All inputs processed in parallel conceptually")
    
    print("\n3️⃣  Streaming Execution (stream)")
    print("   doubler.stream(7) yields: ", end="")
    for chunk in doubler.stream(7):
        print(chunk, end=" ")  # 14
    print("\n   ✓ Streaming useful when output comes incrementally")
    
    # ─────────────────────────────────────────────────────────────────
    # PART C: Composition (Custom Runnable with Custom Runnable)
    # ─────────────────────────────────────────────────────────────────
    
    print("\n\n🔗 Composition: Custom Runnable | Custom Runnable")
    print("-" * 70)
    print("   This is the magic of Runnables!")
    print("   Any Runnable can compose with any other Runnable")
    print("   No special code needed—just use the pipe operator!\n")
    
    # Create a chain: doubler | tripler
    # This means: first multiply by 2, then by 3
    chain = doubler | tripler
    
    print("   chain = doubler | tripler")
    print("   When we call chain.invoke(5):")
    print("     1. doubler.invoke(5) = 10")
    print("     2. tripler.invoke(10) = 30")
    print("     3. Result: 30\n")
    
    result = chain.invoke(5)
    print(f"   ✓ chain.invoke(5) = {result}")
    
    results = chain.batch([1, 2, 3])
    print(f"   ✓ chain.batch([1,2,3]) = {results}")
    print("      (Each input goes through: *2, then *3)")
    
    # ─────────────────────────────────────────────────────────────────
    # SUMMARY & KEY INSIGHTS
    # ─────────────────────────────────────────────────────────────────
    
    print("\n" + "="*70)
    print("✅ KEY INSIGHTS FROM THIS EXAMPLE")
    print("="*70)
    print("""
    1. RUNNABLE CONTRACT
       A Runnable is just an object with 4 methods.
       That's it. No magic.
    
    2. COMPOSITION WORKS AUTOMATICALLY
       Custom | Custom | Builtin | Builtin
       All of them work together without glue code!
    
    3. SIMPLE UNITS → INFINITE COMPLEXITY
       Two simple multipliers can be chained.
       Prompt | Model | OutputParser | Runnable | ...
       Each adds one capability, unlimited combinations.
    
    4. YOUR OWN DOMAIN LOGIC
       You can wrap your code in a Runnable:
       • Database lookups
       • API calls
       • ML model inference
       • Custom computations
       • Then compose with LangChain components
    
    5. THIS IS EVERYTHING LANGCHAIN USES
       ChatOpenAI is a Runnable
       ChatPromptTemplate is a Runnable
       LLMChain is a Runnable
       RunnableParallel is a Runnable
       RunnableBranch is a Runnable
       YOUR custom class is a Runnable
       
       That uniformity is what makes LangChain powerful.
    
    EXERCISE FOR YOU:
    ──────────────────
    1. Modify TimedRunnable to add a name that gets printed
    2. Create a Runnable that calls a real API (e.g., HTTP GET)
    3. Chain it with ChatOpenAI
    4. See what happens!
    """)


# ============================================================================
# EXAMPLE 3: Composition as a DAG
# ============================================================================

def example_3_dag_composition():
    """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║                 EXAMPLE 3: COMPOSITION AS A DAG                        ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    GOAL:
    ─────
    Understand that pipes create directed acyclic graphs, not sequences.
    
    KEY INSIGHT:
    ────────────
    chain = A | B | C  is NOT a sequential pipeline
    It's a GRAPH where:
      - Data flows from A to B to C
      - But each unit can have internal structure
      - RunnableParallel branches execution
      - RunnableBranch routes execution
      - Results merge back together
    
    WHY THIS MATTERS:
    ─────────────────
    Understanding DAGs helps you:
    • Design parallel processing workflows
    • Compose complex logic from simple pieces
    • Debug execution flow
    • Optimize performance (parallel branches)
    
    THE METAPHOR:
    ─────────────
    Sequential: A → B → C (one path, linear)
    DAG:        A → (B, C in parallel) → Merge (fork and join)
    
    LangChain chains are DAGs, not sequences!
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Composition as a DAG (Directed Acyclic Graph)")
    print("="*70)
    
    # ─────────────────────────────────────────────────────────────────
    # PART A: Build the Components
    # ─────────────────────────────────────────────────────────────────
    
    # Two simple formatting functions wrapped as Runnables
    format_name = RunnableLambda(lambda x: f"Topic: {x['topic']}")
    format_query = RunnableLambda(lambda x: f"Query: {x['query']}")
    
    # Parallel processing: both run at the same time
    # RunnableParallel creates a fork in the DAG
    parallel = RunnableParallel(
        name_formatted=format_name,      # Branch 1: format the topic
        query_formatted=format_query,     # Branch 2: format the query
    )
    
    # Merge the results back together
    merge = RunnableLambda(lambda x: f"{x['name_formatted']} | {x['query_formatted']}")
    
    # Full workflow: input → parallel (branches) → merge
    workflow = parallel | merge
    
    # ─────────────────────────────────────────────────────────────────
    # PART B: Visualize the DAG
    # ─────────────────────────────────────────────────────────────────
    
    print("\n📊 Workflow Structure (DAG Visualization):")
    print("-" * 70)
    print("""
    INPUT: {"topic": "AI", "query": "what is"}
       ↓
    ┌──────────────────────────────┐
    │   RunnableParallel (fork)    │
    └──────────────────────────────┘
       ↙                         ↖
    
    ┌─────────────────┐    ┌──────────────────┐
    │  format_name    │    │  format_query    │
    │ (Branch 1)      │    │ (Branch 2)       │
    │ Topic: AI       │    │ Query: what is   │
    └─────────────────┘    └──────────────────┘
    
       ↘                         ↙
    
    ┌──────────────────────────────┐
    │        Merge Results         │
    │ "Topic: AI | Query: what is" │
    └──────────────────────────────┘
       ↓
    OUTPUT: "Topic: AI | Query: what is"
    
    KEY POINTS:
    ───────────
    1. Two branches execute INDEPENDENTLY (could be parallel)
    2. Results are collected in a dict {name_formatted, query_formatted}
    3. Merge function receives that dict as input
    4. Final output is the merged string
    5. This is NOT a sequence, it's a DAG!
    """)
    
    # ─────────────────────────────────────────────────────────────────
    # PART C: Execute the Workflow
    # ─────────────────────────────────────────────────────────────────
    
    input_data = {"topic": "AI", "query": "what is"}
    
    # Single execution
    print("\n1️⃣  Single Execution (invoke):")
    print("   Input: ", input_data)
    result = workflow.invoke(input_data)
    print(f"   Output: {result}")
    print("   ✓ One input processed through the DAG")
    
    # Batch execution
    print("\n2️⃣  Batch Execution (batch):")
    inputs = [
        {"topic": "AI", "query": "what is"},
        {"topic": "ML", "query": "definition"},
    ]
    print("   Inputs:")
    for i, inp in enumerate(inputs):
        print(f"     {i+1}. {inp}")
    
    results = workflow.batch(inputs)
    print("   Outputs:")
    for i, r in enumerate(results):
        print(f"     {i+1}. {r}")
    print("   ✓ Both inputs processed through DAG (in parallel)")
    
    # ─────────────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────────────
    
    print("\n" + "="*70)
    print("✅ KEY INSIGHTS: DAG Composition")
    print("="*70)
    print("""
    1. PIPES CREATE GRAPHS, NOT SEQUENCES
       A | B | C is NOT strictly sequential
       RunnableParallel creates branches
       RunnableBranch creates conditional paths
    
    2. PARALLEL EXECUTION
       Both branches in RunnableParallel execute
       (Could be actual parallelism or logical separation)
       Results collected and passed to next stage
    
    3. FORK AND JOIN
       Fork: Input splits to multiple branches
       Join: Results from branches merge
       This pattern is fundamental to complex workflows
    
    4. COMPOSABLE STRUCTURE
       Each piece (format_name, format_query, merge) is reusable
       They don't know about each other
       They only know their input/output interface
       This is why Runnables scale so well
    
    5. REAL WORLD EXAMPLES
       • Parallel data processing
       • Fan-out/fan-in patterns
       • Multi-step question answering (branches explore different angles)
       • Ensemble methods (branches vote or combine)
    
    USE THIS PATTERN WHEN:
    ─────────────────────
    • You need parallel processing
    • You want to combine multiple sources
    • You're computing multiple features
    • You need fan-out/fan-in semantics
    """)


# ============================================================================
# EXAMPLE 4: Execution Tracing
# ============================================================================

def example_4_tracing():
    """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║                   EXAMPLE 4: EXECUTION TRACING                         ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    GOAL:
    ─────
    See execution flow through the Runnable graph step-by-step.
    Understand how callbacks provide visibility into what's happening.
    
    KEY INSIGHT:
    ────────────
    Every Runnable in the DAG reports what it's doing via callbacks.
    This is how LangSmith (observability tool) works.
    
    WHY THIS MATTERS:
    ─────────────────
    • Debugging: See where things go wrong
    • Performance: Measure which steps are slow
    • Monitoring: Track what your system is doing
    • Compliance: Log inputs/outputs for auditing
    
    HOW IT WORKS:
    ──────────────
    1. Create a Callback subclass (responds to execution events)
    2. Register callbacks in RunnableConfig
    3. Execute the chain
    4. Callbacks are invoked at each step
    5. You see exactly what's happening!
    
    CALLBACK EVENTS:
    ────────────────
    • on_chain_start: Chain execution begins
    • on_chain_end: Chain execution completes
    • on_llm_start: LLM is called
    • on_llm_end: LLM returns result
    • on_chain_error: Error occurred in chain
    • And many more for different components
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Execution Tracing with Callbacks")
    print("="*70)
    
    # ─────────────────────────────────────────────────────────────────
    # Define Custom Callback Handler
    # ─────────────────────────────────────────────────────────────────
    # A callback handler is invoked at different points in execution
    # Inherit from BaseCallbackHandler and override methods for events
    
    class TraceCallback(BaseCallbackHandler):
        """
        Custom callback that prints execution trace.
        
        This callback is invoked at key points during chain execution:
        • on_chain_start: When a chain begins
        • on_chain_end: When a chain completes
        • on_llm_start: Before calling an LLM
        • on_llm_end: After LLM returns
        • on_chain_error: If an error occurs
        
        This allows you to:
        • Log all activity
        • Measure performance
        • Debug what's happening
        • Monitor production systems
        """
        
        def on_chain_start(self, serialized, inputs, **kwargs):
            """
            Called when a Runnable (chain) starts execution.
            
            Args:
                serialized: Dict with component metadata
                inputs: The input data passed to the Runnable
                **kwargs: Additional context
            
            Note: This is called for ANY Runnable, not just LLMs
            """
            # Extract the component name (e.g., "ChatPromptTemplate", "ChatOpenAI")
            chain_type = serialized.get("id", ["unknown"])[-1]
            print(f"  ▶️  START: {chain_type}")
            print(f"      Input: {str(inputs)[:100]}...")
        
        def on_chain_end(self, outputs, **kwargs):
            """
            Called when a Runnable completes execution.
            
            Args:
                outputs: The output produced by the Runnable
                **kwargs: Additional context
            """
            print("  ◀️  END")
            print(f"      Output type: {type(outputs).__name__}")
        
        def on_llm_start(self, serialized, prompts, **kwargs):
            """
            Called before the LLM is invoked.
            
            Args:
                serialized: LLM metadata
                prompts: List of prompts being sent to LLM
                **kwargs: Additional context
            
            Note: This is specific to LLM calls, won't fire for other components
            """
            print(f"    🤖 LLM START: {serialized.get('id', ['unknown'])[-1]}")
            print(f"       Prompts: {len(prompts)} message(s)")
        
        def on_llm_end(self, response, **kwargs):
            """
            Called after the LLM returns its response.
            
            Args:
                response: The LLMResult containing outputs and metadata
                **kwargs: Additional context
            
            Includes token usage, model info, etc.
            """
            # Extract token usage if available
            tokens = response.llm_output.get("token_usage", {}) if response.llm_output else {}
            total = tokens.get('total_tokens', '?')
            print(f"    ✅ LLM DONE: {total} total tokens used")
    
    # ─────────────────────────────────────────────────────────────────
    # Build and Execute with Tracing
    # ─────────────────────────────────────────────────────────────────
    
    print("\n1️⃣  Building Chain:")
    print("   chain = ChatPromptTemplate | ChatOpenAI")
    
    prompt = ChatPromptTemplate.from_template("Explain {concept} in one sentence")
    model = ChatOpenAI(model="gpt-4-mini")
    chain = prompt | model
    
    print("\n2️⃣  Executing with Tracing:")
    print("-" * 70)
    
    # Execute with tracing callback
    config = RunnableConfig(callbacks=[TraceCallback()])
    result = chain.invoke(
        {"concept": "quantum computing"},
        config=config
    )
    
    # ─────────────────────────────────────────────────────────────────
    # Show Results
    # ─────────────────────────────────────────────────────────────────
    
    print("\n3️⃣  Final Result:")
    print("-" * 70)
    print(f"Output: {result.content[:100]}...")
    
    # ─────────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────────
    
    print("\n" + "="*70)
    print("✅ KEY INSIGHTS: Execution Tracing")
    print("="*70)
    print("""
    1. OBSERVABILITY IS BUILT-IN
       Every Runnable supports callbacks
       Same interface everywhere
       Consistent visibility across systems
    
    2. EVENTS TELL THE STORY
       on_chain_start: Execution begins
       on_chain_end: Execution completes
       on_llm_start: LLM is about to be called
       on_llm_end: LLM has returned
       Each tells you something important
    
    3. TOKEN COUNTING
       on_llm_end gives you token usage
       Critical for tracking costs
       Also for performance optimization
    
    4. DEBUGGING MADE EASY
       See exactly what's happening
       at each step of execution
       Much better than print statements!
    
    5. PRODUCTION MONITORING
       LangSmith uses this mechanism
       Captures full execution traces
       Enables performance analysis
       Supports prompt engineering experiments
    
    6. MULTIPLE CALLBACKS
       You can register multiple callbacks
       They all receive all events
       Use callbacks for: logging, metrics, debugging, compliance
    
    REAL WORLD USAGE:
    ────────────────
    • Logging all inputs/outputs for compliance
    • Measuring latency at each step
    • Counting tokens for billing
    • Debugging production issues
    • A/B testing different prompts
    • Monitoring system health
    """)
    
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
    ╔════════════════════════════════════════════════════════════════════════╗
    ║               EXAMPLE 5: CONDITIONAL ROUTING                           ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    GOAL:
    ─────
    Route execution to different chains based on input analysis.
    Implement conditional logic in Runnable DAGs.
    
    KEY INSIGHT:
    ────────────
    RunnableBranch is a Runnable that examines input and chooses a path.
    It's another way to compose Runnables, just like pipes!
    
    WHY THIS MATTERS:
    ─────────────────
    • Route different question types to different handlers
    • Implement question classification
    • Optimize by choosing the best tool for the job
    • Build smart agents that adapt to input
    
    ARCHITECTURE:
    ──────────────
    Input → Analyze → Choose path → Execute → Output
    
    Example:
    - "solve 2+2" → Math handler
    - "write Python" → Code handler
    - "what is AI" → General handler
    
    HOW RUNNABLE BRANCH WORKS:
    ──────────────────────────
    1. Receives input
    2. Evaluates condition functions in order
    3. Takes FIRST path where condition is true
    4. Falls back to default if no conditions match
    5. Returns output from the chosen path
    
    LIKE AN IF-ELIF-ELSE CHAIN:
    ───────────────────────────
    if is_math(input):
        return math_chain.invoke(input)
    elif is_code(input):
        return code_chain.invoke(input)
    else:
        return general_chain.invoke(input)
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Conditional Routing with RunnableBranch")
    print("="*70)
    
    # ─────────────────────────────────────────────────────────────────
    # PART A: Define Routing Predicates
    # ─────────────────────────────────────────────────────────────────
    # A predicate is a function that returns True/False
    # RunnableBranch evaluates predicates in order
    # Executes the chain for the FIRST TRUE predicate
    
    def is_math(x):
        """Check if input is a math question."""
        return "math" in x.get("query", "").lower() or \
               "calculate" in x.get("query", "").lower() or \
               any(op in x.get("query", "") for op in ["+", "-", "*", "/"])
    
    def is_code(x):
        """Check if input is a code request."""
        return "code" in x.get("query", "").lower() or \
               "write" in x.get("query", "").lower() or \
               any(lang in x.get("query", "").lower() for lang in ["python", "javascript", "java"])
    
    # ─────────────────────────────────────────────────────────────────
    # PART B: Define Specialized Chains
    # ─────────────────────────────────────────────────────────────────
    # Each chain is specialized for its domain
    # In reality, these would call real tools, not just print
    
    math_chain = RunnableLambda(
        lambda x: f"[🔢 MATH HANDLER]: Computing solution for '{x['query']}'"
    )
    
    code_chain = RunnableLambda(
        lambda x: f"[💻 CODE HANDLER]: Writing code for '{x['query']}'"
    )
    
    general_chain = RunnableLambda(
        lambda x: f"[💬 GENERAL HANDLER]: Explaining '{x['query']}'"
    )
    
    # ─────────────────────────────────────────────────────────────────
    # PART C: Create Router
    # ─────────────────────────────────────────────────────────────────
    # RunnableBranch takes a list of (predicate, runnable) tuples
    # Plus a default runnable for no match
    
    print("\n1️⃣  Defining Router Logic:")
    print("   Router will:")
    print("     1. Check if query contains 'math' or operators → math_chain")
    print("     2. Check if query contains 'code' → code_chain")
    print("     3. Otherwise → general_chain")
    
    router = RunnableBranch(
        (is_math, math_chain),      # First condition: if is_math, use math_chain
        (is_code, code_chain),      # Second condition: if is_code, use code_chain
        general_chain,              # Default: if no conditions match, use general_chain
    )
    
    # ─────────────────────────────────────────────────────────────────
    # PART D: Test Router with Different Inputs
    # ─────────────────────────────────────────────────────────────────
    
    print("\n2️⃣  Testing Router with Different Queries:")
    print("-" * 70)
    
    test_queries = [
        {"query": "solve the math problem 2+2"},
        {"query": "write python code for hello world"},
        {"query": "what is artificial intelligence"},
        {"query": "calculate 10 * 5"},
        {"query": "show me javascript"},
    ]
    
    for q in test_queries:
        result = router.invoke(q)
        # Determine which branch was taken
        if "[🔢" in result:
            branch = "MATH"
        elif "[💻" in result:
            branch = "CODE"
        else:
            branch = "GENERAL"
        
        print(f"  Input:  {q['query']:<40}")
        print(f"  Branch: {branch} → {result}\n")
    
    # ─────────────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────────────
    
    print("\n" + "="*70)
    print("✅ KEY INSIGHTS: Conditional Routing")
    print("="*70)
    print("""
    1. RUNNABLE BRANCH IS JUST A RUNNABLE
       It implements the 4 methods like any other Runnable
       Can be composed with | operator
       Scales from simple routing to complex workflows
    
    2. PREDICATES ARE SIMPLE FUNCTIONS
       Just return True/False based on input
       Evaluated in order
       First match wins
    
    3. EFFICIENT ROUTING
       Don't execute all chains, only the matching one
       Save compute by routing to optimal handler
       Each handler can be specialized
    
    4. REAL WORLD APPLICATIONS
       Question classification (math vs coding vs general)
       Intent detection (user wants to schedule vs summarize vs search)
       Error handling (retry vs escalate vs fail)
       A/B testing (route 50% to new strategy, 50% to old)
    
    5. COMBINING WITH OTHER PATTERNS
       Can use RunnableBranch inside RunnableParallel
       Can nest RunnableBranch for complex logic
       Can chain with prompts and models
    
    6. EXTENDING THE PATTERN
       Instead of simple predicates, use:
       • LLM-based classification ("Is this a math question?")
       • Semantic similarity (embed input, find closest category)
       • Regex patterns or heuristics
       • Machine learning models
    
    EXERCISE FOR YOU:
    ──────────────────
    1. Add a programming language detector
    2. Use ChatOpenAI to classify instead of predicates
    3. Create a chain that routes to specialized handlers
    4. Measure which branch gets called most often
    """)
    print("   All implemented as Runnables in a DAG")


# ============================================================================
# EXAMPLE 6: Batch Performance Comparison
# ============================================================================

def example_6_batch_performance():
    """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║           EXAMPLE 6: BATCH PERFORMANCE COMPARISON                      ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    GOAL:
    ─────
    Demonstrate the dramatic performance improvement of batch() over loops.
    Understand why batch() is critical for production systems.
    
    KEY INSIGHT:
    ────────────
    
    ❌ WRONG:  for item in items:
                   result = chain.invoke(item)
    
    ✅ RIGHT:  results = chain.batch(items)
    
    The difference is HUGE: batch() is often 10x-100x faster!
    
    WHY:
    ─────
    1. invoke() makes separate API calls
       - Connection overhead per call
       - Rate limit per call
       - Sequential, one after another
    
    2. batch() batches API calls
       - Reuse connection
       - Batch rate limit handling
       - Parallel execution
       - Smart batching under the hood
    
    REAL NUMBERS:
    ──────────────
    Processing 100 items:
    • invoke() loop:  ~50 seconds (0.5s each)
    • batch():        ~5 seconds (5s for all)
    
    That's 10x faster! For 1000 items? 100x!
    
    LESSON:
    ────────
    ALWAYS use batch() when you have N items to process.
    It's not optional, it's mandatory for performance.
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Batch Performance Comparison")
    print("="*70)
    
    print("\n⚠️  CRITICAL LESSON FOR PRODUCTION SYSTEMS:")
    print("   Never loop with invoke() when batch() is available!")
    print("   batch() is 10-100x faster for N items")
    print("="*70)
    
    # Build a simple chain
    prompt = ChatPromptTemplate.from_template("Give one fact about {topic}:")
    model = ChatOpenAI(model="gpt-4-mini")
    chain = prompt | model
    
    # Topics to process
    topics = ["python", "javascript", "golang", "rust"]
    
    # ─────────────────────────────────────────────────────────────────
    # APPROACH 1: Serial invoke() in a loop
    # ─────────────────────────────────────────────────────────────────
    # THIS IS SLOW! One call after another.
    # Each topic waits for previous to complete.
    
    print("\n1️⃣  APPROACH 1: Serial with invoke() loop")
    print("    (❌ This is slow!)")
    print("-" * 70)
    print("   Code: for topic in topics:")
    print("           result = chain.invoke({'topic': topic})")
    print()
    
    start = time.time()
    results_serial = []
    for topic in topics:
        print(f"      Processing '{topic}'...", end=" ", flush=True)
        result = chain.invoke({"topic": topic})
        results_serial.append(result)
        elapsed = time.time() - start
        print(f"✓ ({elapsed:.1f}s so far)")
    
    serial_time = time.time() - start
    
    print(f"\n   Total Time: {serial_time:.2f}s")
    print(f"   Per item:  {serial_time/len(topics):.2f}s")
    print("   Method:    Sequential (one after another)")
    
    # ─────────────────────────────────────────────────────────────────
    # APPROACH 2: Parallel batch()
    # ─────────────────────────────────────────────────────────────────
    # THIS IS FAST! All items processed in parallel.
    # Batch handles rate limits and connection pooling.
    
    print("\n2️⃣  APPROACH 2: Parallel with batch()")
    print("    (✅ This is fast!)")
    print("-" * 70)
    print("   Code: results = chain.batch(")
    print("       [{'topic': t} for t in topics]")
    print("   )")
    print()
    
    print(f"      Processing {len(topics)} items in parallel...")
    start = time.time()
    chain.batch([{"topic": t} for t in topics])
    batch_time = time.time() - start
    
    print(f"   Total Time: {batch_time:.2f}s")
    print(f"   Per item:  {batch_time/len(topics):.2f}s")
    print("   Method:    Parallel (all at once)")
    
    # ─────────────────────────────────────────────────────────────────
    # COMPARISON AND ANALYSIS
    # ─────────────────────────────────────────────────────────────────
    
    print("\n" + "="*70)
    print("📊 PERFORMANCE COMPARISON")
    print("="*70)
    
    print(f"""
    ┌────────────────┬──────────┬─────────────┬────────────┐
    │ Approach       │ Total    │ Per Item    │ Method     │
    ├────────────────┼──────────┼─────────────┼────────────┤
    │ invoke() loop  │ {serial_time:>6.2f}s  │ {serial_time/len(topics):>9.2f}s   │ Sequential │
    │ batch()        │ {batch_time:>6.2f}s  │ {batch_time/len(topics):>9.2f}s   │ Parallel   │
    └────────────────┴──────────┴─────────────┴────────────┘
    
    ⚡ SPEEDUP: {serial_time/batch_time:.1f}x faster with batch()
    
    📈 SCALING:
       For N=10:    {10 * serial_time / (10 * batch_time):.1f}x faster
       For N=100:   {100 * serial_time / (100 * batch_time):.1f}x faster
       For N=1000:  {1000 * serial_time / (1000 * batch_time):.1f}x faster
    
    💡 KEY INSIGHT:
       batch() time scales MUCH better than invoke() loop.
       invoke() = O(N) → N items = N × time_per_item
       batch()  = O(1-logN) → N items ≈ constant time
    
    🎯 DECISION RULE:
       Always measure with batch() on realistic data sizes.
       Never assume serial is good enough.
       Test with your actual API and latencies.
    """)
    
    # ─────────────────────────────────────────────────────────────────
    # SUMMARY & LESSONS
    # ─────────────────────────────────────────────────────────────────
    
    print("="*70)
    print("✅ KEY INSIGHTS: Why batch() is Essential")
    print("="*70)
    print("""
    1. CONNECTION REUSE
       invoke() loop: New HTTP connection for each item
       batch(): One connection for all items
       Result: ~10-100x faster
    
    2. RATE LIMIT HANDLING
       invoke() loop: Hit rate limit N times
       batch(): Smart batching respects global limits
       Result: Better throughput, fewer errors
    
    3. PARALLEL EXECUTION
       invoke() loop: Sequential (must wait for each)
       batch(): Parallel (all at once, or smart batching)
       Result: Much faster time to completion
    
    4. OVERHEAD AMORTIZATION
       invoke() loop: Network overhead × N
       batch(): Network overhead × 1 (for all)
       Result: Much better efficiency
    
    5. PRODUCTION IS DIFFERENT FROM EXPERIMENTS
       Experiment: "Processing 1 item at a time is fine"
       Production: "Need to process 1,000 items per minute"
       Solution: Use batch() ALWAYS
    
    6. SCALABILITY BARRIER
       Without batch(): You're limited by serial execution
       With batch(): You can handle 10-100x more load
       This is a HARD requirement for any production system
    
    REAL WORLD EXAMPLE:
    ──────────────────
    Task: Embed 10,000 documents
    
    invoke() loop:
    • Time: 10,000 × 0.5s = 5,000s = 83 minutes
    • Cost: High (connection overhead)
    
    batch():
    • Time: 50s = Less than 1 minute
    • Cost: Low (efficient batching)
    
    Difference: 83 minutes vs 1 minute = 83x faster!
    
    TAKEAWAY:
    ─────────
    Use batch() for any processing pipeline.
    It's not just an optimization, it's a requirement.
    Make it a habit: batch() first, invoke() only for single items.
    """)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "WORK PRODUCT 1.3: RUNNABLE PROTOCOL EXAMPLES" + " " * 9 + "║")
    print("║" + " " * 68 + "║")
    print("║  These 6 hands-on examples teach you everything about Runnables" + " " * 3 + "║")
    print("╚" + "═" * 68 + "╝")
    print("█" * 70 + "\n")
    
    print("📚 EXAMPLES COVERED:")
    print("  1️⃣  The Four Execution Modes (invoke, batch, stream, ainvoke)")
    print("  2️⃣  Custom Runnables (implementing the protocol)")
    print("  3️⃣  Composition as a DAG (pipes create graphs)")
    print("  4️⃣  Execution Tracing (callbacks and observability)")
    print("  5️⃣  Conditional Routing (RunnableBranch for logic)")
    print("  6️⃣  Batch Performance (why batch() is essential)")
    
    print("\n🎯 LEARNING PATH:")
    print("  → Examples 1-2: Understand the protocol")
    print("  → Examples 3-5: Learn composition patterns")
    print("  → Example 6: Understand production optimization")
    print("  → Read WP-1.3-The-Runnable-Protocol.md for deep dive")
    
    print("\n" + "="*70 + "\n")
    
    try:
        # Run examples in sequence
        example_1_four_modes()
        example_2_custom_runnable()
        example_3_dag_composition()
        example_4_tracing()
        example_5_conditional_routing()
        example_6_batch_performance()
        
        # Final summary
        print("\n" + "█" * 70)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("█" * 70)
        
        print("""
📖 NEXT STEPS:
──────────────

1. UNDERSTAND THE PROTOCOL
   □ Re-read each example's docstring
   □ Understand why each method exists
   □ Know when to use each execution mode

2. DEEPEN YOUR KNOWLEDGE
   □ Read WP-1.3-The-Runnable-Protocol.md (full documentation)
   □ Explore LangChain source: langchain-core/runnables/base.py
   □ Look at real implementations in langchain

3. BUILD YOUR OWN
   □ Create a custom Runnable for your domain
   □ Compose it with built-in LangChain components
   □ Test all four execution modes
   □ Measure performance with batch()

4. APPLY IN PRACTICE
   □ Use batch() for any data processing
   □ Use stream() for interactive UIs
   □ Use ainvoke() in FastAPI endpoints
   □ Chain Runnables instead of monolithic functions

5. OPTIMIZE PRODUCTION
   □ Always measure performance
   □ Profile your chains with callbacks
   □ Use LangSmith for observability
   □ Implement error handling and retries

🎓 KEY TAKEAWAYS:
──────────────────
• Runnables are simple: just 4 methods
• Composition is powerful: create complexity from simplicity
• Performance matters: always use batch() for N items
• Observability is built-in: callbacks everywhere
• You can extend: custom Runnables fit seamlessly

💡 MOST IMPORTANT LESSON:
──────────────────────────
When you understand that a chain is just a graph of Runnables,
everything makes sense. You can build anything.

Happy building! 🚀
        """)
        
    except KeyboardInterrupt:
        print("\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
