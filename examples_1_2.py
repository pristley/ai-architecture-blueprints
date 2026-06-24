"""
Work Product 1.2: "Hello World" Three Ways - Chain Type Implementations

OVERVIEW
════════
This module demonstrates three different approaches to building LLM chains:
1. Direct LLM Call - Minimal abstraction, manual orchestration
2. SimpleSequentialChain - Basic chain abstraction (deprecated)
3. RunnableSequence with LCEL - Modern, production-ready approach

LEARNING OBJECTIVES
═══════════════════
After studying this code, you'll understand:
- How traceability differs across chain abstractions
- Trade-offs between explicit control and declarative composition
- Practical patterns for observability (LangSmith integration)
- Advanced LCEL features: streaming, batching, callbacks

QUICK START
═══════════
Run this file directly to see all three approaches in action:
    python examples_1_2.py

The output will show:
- Generated poem from each approach
- Summary of the poem
- Observability metrics and effort required
- Visual comparison summary

REFERENCES
══════════
- ADR-1.2-Hello-World-Three-Ways.md: Detailed comparison and analysis
- LANGCHAIN_ECOSYSTEM_MAP.md: Full LangChain ecosystem documentation
- LangChain Docs: https://python.langchain.com
- LangSmith: https://smith.langchain.com

AUTHOR NOTES
════════════
This code deliberately shows all three approaches (even deprecated ones)
for educational purposes. In production, always use Approach 3
(RunnableSequence + LCEL).
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.callbacks import StdOutCallbackHandler


# ============================================================================
# INITIALIZATION
# ============================================================================

def _setup_llm():
    """
    Initialize the language model with default parameters.
    
    Uses GPT-4 Mini for cost-effectiveness while maintaining quality.
    Temperature 0.7 provides a balance between creativity and consistency.
    
    Returns:
        ChatOpenAI: Configured language model instance
    
    Requires:
        OPENAI_API_KEY environment variable to be set
    """
    return ChatOpenAI(model="gpt-4-mini", temperature=0.7)


# Initialize model (same across all three approaches)
llm = _setup_llm()

# ============================================================================
# OPTIONAL: LangSmith Configuration
# ============================================================================
# Uncomment below to enable automatic tracing and monitoring.
# Requires: LANGSMITH_API_KEY environment variable
#
# When enabled, ALL chain executions (Approach 3 only) are automatically
# logged to LangSmith dashboard for:
# - Full execution traces with step-by-step visibility
# - Token usage and cost analysis
# - Latency monitoring
# - Error tracking and debugging
#
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_PROJECT"] = "hello-world-three-ways"


# ============================================================================
# APPROACH 1: Direct LLM Call
# ============================================================================
# WHEN TO USE: Prototyping, learning, single-step tasks
# PRODUCTION: NOT RECOMMENDED
# ============================================================================

def approach_1_direct_llm():
    """
    Simplest chain approach: Manual orchestration of LLM calls in Python.
    
    CHARACTERISTICS:
    ────────────────
    - Lowest abstraction overhead (just Python code)
    - Maximum explicit control (you see every step)
    - No built-in composition framework
    - Traceability: Manual (requires custom logging)
    - Verbosity: High (orchestration scattered in Python)
    - Flexibility: Low (steps tightly coupled)
    
    ADVANTAGES:
    ──────────
    ✓ Easy to understand (just Python)
    ✓ Simple to debug (standard Python debugging)
    ✓ Fast to write for quick tests
    ✓ No framework learning curve
    
    DISADVANTAGES:
    ──────────────
    ✗ No automatic observability (must implement custom logging)
    ✗ Hard to scale (no batching, streaming, or async support)
    ✗ Difficult to test (steps not isolated)
    ✗ Not suitable for production (no monitoring)
    ✗ Couple implementation to orchestration logic
    
    OBSERVABILITY:
    ──────────────
    Manual. You must implement:
    - print() statements for step tracking
    - Custom logging to track metrics
    - Manual error handling and reporting
    
    USE CASE:
    ─────────
    Jupyter notebooks, quick experiments, learning LLM fundamentals.
    Once the approach is finalized, migrate to Approach 3 for reuse.
    """
    print("\n" + "="*70)
    print("APPROACH 1: Direct LLM Call")
    print("="*70)
    
    # Step 1: Generate a poem
    print("\n[Step 1] Generating poem...")
    poem_response = llm.invoke("Write a 4-line poem about artificial intelligence")
    poem = poem_response.content
    print(f"✓ Generated poem ({len(poem)} chars)")
    
    # Step 2: Summarize the poem
    print("\n[Step 2] Summarizing poem...")
    summary_response = llm.invoke(f"Summarize this poem in one sentence: {poem}")
    summary = summary_response.content
    print(f"✓ Generated summary ({len(summary)} chars)")
    
    # Manual logging for observability
    print("\n[Observability] Metrics:")
    print(f"  - Poem tokens: {poem_response.response_metadata.get('token_usage', {}).get('prompt_tokens', '?')}")
    print(f"  - Summary model: {summary_response.response_metadata.get('model_name', 'unknown')}")
    
    return {
        "poem": poem,
        "summary": summary,
        "traceability": "Manual - see calls in code, custom logging required",
        "method": "Direct LLM Call",
        "observability_effort": "High - must implement custom logging"
    }


# ============================================================================
# APPROACH 2: SimpleSequentialChain (via LLMChain)
# ============================================================================
# WHEN TO USE: Maintaining legacy code only
# PRODUCTION: NOT RECOMMENDED (deprecated)
# NEW CODE: DO NOT USE - Choose Approach 3 instead
# ============================================================================

def approach_2_simple_sequential_chain():
    """
    Middle ground approach: Uses LLMChain for basic chain abstraction.
    
    WARNING: SimpleSequentialChain and LLMChain are deprecated in favor of
    RunnableSequence with LCEL. This example shows the pattern for reference
    and for maintaining existing codebases.
    
    NOTE: LLMChain import moved here to avoid import errors in modern LangChain.
    This is for demonstration only—use Approach 3 in production.
    """
    # Lazy import of deprecated LLMChain to avoid module errors when not used
    try:
        from langchain.chains import LLMChain
    except ImportError:
        # Fallback for newer LangChain versions that removed this module
        print("\n⚠️  NOTE: LLMChain is not available in this LangChain version.")
        print("    This approach is deprecated. Use Approach 3 (LCEL) instead.")
        return {
            "poem": "(Skipped - LLMChain not available)",
            "summary": "(Skipped - LLMChain not available)",
            "traceability": "N/A - deprecated module",
            "method": "SimpleSequentialChain (LLMChain) - DEPRECATED",
            "observability_effort": "N/A"
        }
    
    """
    
    CHARACTERISTICS:
    ────────────────
    - Provides basic chain abstraction (better than raw Python)
    - Uses string-based output passing (output of step 1 → input of step 2)
    - Linear flow only (no branching or parallel execution)
    - Traceability: Basic (chain objects provide some introspection)
    - Verbosity: Moderate (prompt templates required)
    - Flexibility: Low (string-only, linear constraints)
    
    ADVANTAGES:
    ──────────
    ✓ Better than Approach 1 (basic chain abstraction)
    ✓ Prompt templates provide structure
    ✓ Slightly more testable than Approach 1
    ✓ LangSmith can hook into chain callbacks
    
    DISADVANTAGES:
    ──────────────
    ✗ DEPRECATED - LLMChain will be removed in future versions
    ✗ String-only output passing (loses type safety)
    ✗ No support for branching or conditional logic
    ✗ No async/batch/stream support
    ✗ Cannot pass complex data between steps
    ✗ Difficult to extend when requirements change
    ✗ Manual sequencing still required
    
    MIGRATION PATH:
    ───────────────
    If you have existing LLMChain code:
    
    FROM:
        chain1 = LLMChain(llm=llm, prompt=prompt1)
        chain2 = LLMChain(llm=llm, prompt=prompt2)
        result = chain2.run(text=chain1.run(topic="..."))
    
    TO:
        chain = (prompt1 | llm | prompt2 | llm)
        result = chain.invoke({"topic": "..."})
    
    OBSERVABILITY:
    ──────────────
    Basic. Chain objects expose:
    - Chain type information
    - Input/output through chain interface
    - Limited LangSmith integration (basic hooks only)
    """
    print("\n" + "="*70)
    print("APPROACH 2: SimpleSequentialChain (LLMChain)")
    print("="*70)
    
    # Chain 1: Generate poem
    print("\n[Step 1] Creating poem generation chain...")
    prompt1 = ChatPromptTemplate.from_template(
        "Write a 4-line poem about {topic}"
    )
    chain1 = LLMChain(llm=llm, prompt=prompt1, verbose=False)
    print("✓ Poem chain created")
    
    # Chain 2: Summarize
    print("\n[Step 2] Creating summarization chain...")
    prompt2 = ChatPromptTemplate.from_template(
        "Summarize this in one sentence: {text}"
    )
    chain2 = LLMChain(llm=llm, prompt=prompt2, verbose=False)
    print("✓ Summary chain created")
    
    # Execute chains (manual sequencing)
    print("\n[Execution] Running chains...")
    poem = chain1.run(topic="artificial intelligence")
    print(f"✓ Step 1 complete: Generated poem")
    
    summary = chain2.run(text=poem)
    print(f"✓ Step 2 complete: Generated summary")
    
    print("\n[Observability] Metrics:")
    print(f"  - Chain 1 type: {type(chain1).__name__}")
    print(f"  - Chain 2 type: {type(chain2).__name__}")
    print(f"  - Can trace: Via chain_type attribute")
    
    return {
        "poem": poem,
        "summary": summary,
        "traceability": "Moderate - chain objects provide execution hooks",
        "method": "SimpleSequentialChain (LLMChain)",
        "observability_effort": "Moderate - chains have basic introspection"
    }


# ============================================================================
# APPROACH 3: RunnableSequence with LCEL (Recommended)
# ============================================================================
# WHEN TO USE: ALL new production code
# PRODUCTION: YES - Fully recommended
# LEARNING: Start here for new projects
# ============================================================================

def approach_3_runnable_sequence_lcel():
    """
    Modern, production-ready approach: Composable LCEL chains.
    
    LCEL = LangChain Expression Language
    A declarative, composable syntax for building chains using the pipe
    operator (|) to connect Runnables.
    
    CHARACTERISTICS:
    ────────────────
    - Highest abstraction level (declarative composition)
    - Full control through composition operators (| pipe)
    - Automatic observability (LangSmith tracing)
    - Least verbose (elegant, concise composition)
    - Maximum flexibility (supports all patterns)
    - Production-ready with monitoring built-in
    
    ADVANTAGES:
    ──────────
    ✓ Declarative syntax (what, not how)
    ✓ Type-safe composition with full introspection
    ✓ Automatic LangSmith tracing (set env vars only)
    ✓ Built-in streaming support (token-by-token output)
    ✓ Built-in batching (efficient multi-input processing)
    ✓ Built-in async support (.ainvoke(), .astream(), .abatch())
    ✓ Composable with all langchain-community components
    ✓ Native LangServe support (REST API in seconds)
    ✓ Integrates with LangGraph for agentic workflows
    ✓ Callbacks for custom observability
    ✓ Error handling and retry support
    
    DISADVANTAGES:
    ──────────────
    ✗ Slightly steeper learning curve than Approach 1
    ✗ LCEL syntax takes practice to master
    ✗ Not needed for one-off scripts (overkill)
    
    THE PIPE OPERATOR (|):
    ──────────────────────
    LCEL uses | to compose Runnables:
    
    chain = prompt | llm | output_parser
    
    This creates a Runnable chain where:
    1. Input is passed to prompt
    2. Prompt output goes to llm
    3. LLM output goes to output_parser
    4. Final output is returned
    
    ADVANCED: RunnableParallel and RunnablePassthrough:
    
    # Pass multiple values simultaneously
    chain = {
        "poem": (prompt1 | llm),      # Compute poem
        "topic": RunnablePassthrough() # Keep original input
    }
    
    This creates a dict output that can be used as input to next step.
    
    OBSERVABILITY:
    ──────────────
    Automatic with LangSmith:
    
    1. Set environment variables:
        export LANGCHAIN_TRACING_V2=true
        export LANGCHAIN_PROJECT="my-project"
        export LANGSMITH_API_KEY="..."
    
    2. All chain invocations are automatically traced:
        result = chain.invoke({"topic": "..."})
        # Trace appears in LangSmith dashboard instantly
    
    3. Dashboard shows:
        - Full execution tree (each step)
        - Token usage and costs
        - Latency analysis
        - Error traces
        - Input/output of each step
    
    PRODUCTION FEATURES:
    ────────────────────
    ✓ Streaming: For real-time UI updates
        for chunk in chain.stream({"topic": "..."}):
            print(chunk.content, end="", flush=True)
    
    ✓ Batching: For efficient multi-processing
        results = chain.batch([
            {"topic": "AI"},
            {"topic": "ML"}
        ])
    
    ✓ Callbacks: For custom logging
        result = chain.invoke(
            {"topic": "..."},
            config={"callbacks": [MyCallback()]}
        )
    
    ✓ Deployment: REST API with LangServe
        app = FastAPI()
        add_routes(app, chain, path="/api")
        # Now has /invoke, /batch, /stream endpoints
    """
    print("\n" + "="*70)
    print("APPROACH 3: RunnableSequence with LCEL")
    print("="*70)
    
    # Define prompts as reusable templates
    poem_prompt = ChatPromptTemplate.from_template(
        "Write a 4-line poem about {topic}"
    )
    
    summary_prompt = ChatPromptTemplate.from_template(
        "Summarize this in one sentence:\n{poem}"
    )
    
    # Build poem generation chain
    print("\n[Step 1] Composing poem generation chain...")
    poem_chain = poem_prompt | llm
    print("✓ Poem chain composed (prompt | llm)")
    
    # Build full pipeline with intermediate data passing
    print("\n[Step 2] Composing full pipeline...")
    from langchain_core.runnables import RunnablePassthrough, RunnableParallel
    
    # This approach captures intermediate outputs
    full_chain = (
        RunnableParallel(
            poem=poem_chain,
            topic=RunnablePassthrough()
        )
        | summary_prompt
        | llm
    )
    print("✓ Full pipeline composed with data passing")
    
    # Execute with input
    print("\n[Execution] Running pipeline...")
    result = full_chain.invoke({"topic": "artificial intelligence"})
    print(f"✓ Pipeline executed successfully")
    
    print("\n[Observability] Metrics:")
    print(f"  - Chain type: {type(full_chain).__name__}")
    print(f"  - Supports streaming: Yes")
    print(f"  - Supports batching: Yes")
    print(f"  - Supports async: Yes")
    print(f"  - LangSmith integration: Automatic (set LANGCHAIN_TRACING_V2=true)")
    
    return {
        "summary": result.content,
        "traceability": "Excellent - automatic LangSmith traces",
        "method": "RunnableSequence with LCEL",
        "observability_effort": "Minimal - automatic via env vars",
        "full_chain": full_chain  # Return for other demos
    }


# ============================================================================
# APPROACH 3 ADVANCED FEATURES - STREAMING
# ============================================================================
# LCEL-ONLY Feature: Not available in Approaches 1 or 2
# USE CASE: Real-time UI updates, progressive output
# ============================================================================

def approach_3_streaming():
    """
    Demonstrate token-by-token streaming support in LCEL.
    
    STREAMING OVERVIEW:
    ───────────────────
    Instead of waiting for entire LLM response, stream tokens as they arrive.
    This is essential for interactive applications like chatbots or AI assistants.
    
    ADVANTAGES:
    ──────────
    ✓ Real-time user experience (tokens appear as they generate)
    ✓ Perceived latency is lower (user sees progress immediately)
    ✓ Can cancel mid-stream if needed
    ✓ Lower memory usage (don't buffer entire response)
    ✓ Better for web applications (Server-Sent Events compatible)
    
    USE CASES:
    ──────────
    - Chatbot interfaces (Discord, Slack, web chat)
    - Voice assistant responses (read as they generate)
    - Long-form content generation (show as it writes)
    - Real-time data pipelines (process chunks)
    
    HOW IT WORKS:
    ──────────────
    1. chain.stream(input) returns an iterator
    2. Each iteration yields a chunk (AIMessage or partial response)
    3. Extract chunk.content to get the text
    4. Print immediately for real-time display
    
    EXAMPLE:
    ────────
        for chunk in chain.stream({"input": "..."}):
            if hasattr(chunk, 'content'):
                print(chunk.content, end="", flush=True)
    
    The flush=True ensures text appears immediately without buffering.
    """
    print("\n" + "="*70)
    print("BONUS: Approach 3 - Streaming Support")
    print("="*70)
    
    poem_prompt = ChatPromptTemplate.from_template(
        "Write a 4-line poem about {topic}"
    )
    summary_prompt = ChatPromptTemplate.from_template(
        "Summarize this in one sentence:\n{poem}"
    )
    
    from langchain_core.runnables import RunnableParallel
    full_chain = (
        RunnableParallel(
            poem=poem_prompt | llm,
            topic=RunnableLambda(lambda x: x)
        )
        | summary_prompt
        | llm
    )
    
    print("\n[Streaming] Receiving tokens in real-time:")
    print("-" * 40)
    
    # Stream tokens as they arrive
    for chunk in full_chain.stream({"topic": "quantum computing"}):
        if hasattr(chunk, 'content'):
            print(chunk.content, end="", flush=True)
    
    print("\n" + "-" * 40)
    print("✓ Streaming complete")
    
    return {"method": "Streaming", "note": "Only available in Approach 3"}

# ============================================================================
# APPROACH 3 ADVANCED FEATURES - BATCHING
# ============================================================================
# LCEL-ONLY Feature: Not available in Approaches 1 or 2
# USE CASE: Efficient processing of multiple inputs
# ============================================================================

def approach_3_batching():
    """
    Demonstrate batch processing support in LCEL.
    
    BATCHING OVERVIEW:
    ──────────────────
    Process multiple inputs efficiently in a single operation.
    Useful for data processing, batch jobs, and pipeline parallelism.
    
    ADVANTAGES:
    ──────────
    ✓ Better latency (concurrent execution)
    ✓ Lower overhead (single setup cost, many inputs)
    ✓ Built-in parallelism (no manual threading)
    ✓ Cleaner code (single call instead of loop)
    ✓ Resource efficient (reuse connection pool)
    
    USE CASES:
    ──────────
    - Batch summarization (summarize 100 documents)
    - Data labeling (classify 1000 items)
    - Content generation (generate multiple variants)
    - Analytics pipelines (process logs in bulk)
    - ETL workflows (transform data at scale)
    
    HOW IT WORKS:
    ──────────────
    1. Prepare list of input dictionaries
    2. Call chain.batch(input_list)
    3. Get back list of results (same order as inputs)
    4. Results are computed in parallel (respecting rate limits)
    
    EXAMPLE:
    ────────
        inputs = [
            {"topic": "AI"},
            {"topic": "ML"},
            {"topic": "DL"}
        ]
        results = chain.batch(inputs)
        
        for inp, result in zip(inputs, results):
            print(f"{inp['topic']}: {result.content}")
    
    PERFORMANCE:
    ─────────────
    - Faster than serial invoke() in loop
    - Respects API rate limits automatically
    - Ideal for batch jobs and overnight processing
    - Better cost efficiency (fewer API overhead calls)
    """
    print("\n" + "="*70)
    print("BONUS: Approach 3 - Batching Support")
    print("="*70)
    
    poem_prompt = ChatPromptTemplate.from_template(
        "Write a 4-line poem about {topic}"
    )
    summary_prompt = ChatPromptTemplate.from_template(
        "Summarize this in one sentence:\n{poem}"
    )
    
    from langchain_core.runnables import RunnableParallel
    full_chain = (
        RunnableParallel(
            poem=poem_prompt | llm,
            topic=RunnableLambda(lambda x: x)
        )
        | summary_prompt
        | llm
    )
    
    # Batch multiple requests
    topics = ["artificial intelligence", "quantum computing", "neural networks"]
    
    print(f"\n[Batching] Processing {len(topics)} items...")
    results = full_chain.batch([{"topic": t} for t in topics])
    
    print("\n[Results]:")
    for topic, result in zip(topics, results):
        summary = result.content[:60] + "..." if len(result.content) > 60 else result.content
        print(f"  {topic}: {summary}")
    
    return {"method": "Batching", "items_processed": len(results), "note": "Only available in Approach 3"}



# ============================================================================
# APPROACH 3 ADVANCED FEATURES - CALLBACKS & CUSTOM OBSERVABILITY
# ============================================================================
# LCEL-ONLY Feature: Not available in Approaches 1 or 2
# USE CASE: Custom logging, metrics, debugging
# ============================================================================

def approach_3_with_callbacks():
    """
    Demonstrate callback system for detailed observability in LCEL.
    
    CALLBACKS OVERVIEW:
    ───────────────────
    Callbacks are hooks that execute at various points during chain execution.
    Useful for logging, metrics, debugging, and custom observability.
    
    EXECUTION LIFECYCLE (with callbacks):
    ──────────────────────────────────────
    1. on_llm_start() - Called when LLM is about to be invoked
       └─ Log: model name, prompt, parameters
    
    2. on_llm_new_token() - Called for each token generated
       └─ Log: token, running total latency
    
    3. on_llm_end() - Called when LLM finishes
       └─ Log: total tokens, latency, cost
    
    4. on_chain_start() - Called when chain step starts
       └─ Log: step name, input
    
    5. on_chain_end() - Called when chain step ends
       └─ Log: step name, output
    
    6. on_tool_use() - Called when tool is executed
       └─ Log: tool name, arguments, result
    
    BUILT-IN CALLBACKS:
    ───────────────────
    ✓ StdOutCallbackHandler - Prints all events to stdout
    ✓ FileCallbackHandler - Writes to file
    ✓ LangSmithCallbackHandler - Sends to LangSmith (automatic with env vars)
    ✓ Custom callbacks - Inherit from BaseCallbackHandler
    
    USE CASES:
    ──────────
    - Debug chains by seeing every step
    - Track token usage and costs per step
    - Monitor for errors or unexpected outputs
    - Collect metrics (latency, quality, throughput)
    - Log to external services (Datadog, CloudWatch, etc.)
    - User activity tracking
    - A/B testing metrics
    
    EXAMPLE: Custom Logging Callback
    ─────────────────────────────────
    from langchain_core.callbacks import BaseCallbackHandler
    
    class MyCallback(BaseCallbackHandler):
        def on_llm_start(self, serialized, prompts, **kwargs):
            print(f"🚀 Starting LLM with prompt length: {len(prompts[0])}")
        
        def on_llm_end(self, response, **kwargs):
            tokens = response.llm_output.get('token_usage', {})
            print(f"✅ LLM done. Tokens: {tokens.get('total_tokens', 0)}")
    
    result = chain.invoke(
        {"topic": "..."},
        config={"callbacks": [MyCallback()]}
    )
    
    COMBINING WITH LANGSMITH:
    ──────────────────────────
    LangSmith is automatically used when env vars are set.
    Custom callbacks run in addition to LangSmith logging:
    
        # Both LangSmith AND custom callback fire
        result = chain.invoke(
            {"input": "..."},
            config={"callbacks": [MyCallback()]}
        )
    
    PERFORMANCE NOTE:
    ──────────────────
    Callbacks are lightweight, but multiple callbacks or expensive
    operations inside callbacks can impact latency. Use for monitoring,
    not for transformation logic.
    """
    print("\n" + "="*70)
    print("BONUS: Approach 3 - Callbacks & Observability")
    print("="*70)
    
    poem_prompt = ChatPromptTemplate.from_template(
        "Write a 4-line poem about {topic}"
    )
    summary_prompt = ChatPromptTemplate.from_template(
        "Summarize this in one sentence:\n{poem}"
    )
    
    from langchain_core.runnables import RunnableParallel
    full_chain = (
        RunnableParallel(
            poem=poem_prompt | llm,
            topic=RunnableLambda(lambda x: x)
        )
        | summary_prompt
        | llm
    )
    
    print("\n[Callback Execution] Verbose output:")
    print("-" * 40)
    
    # Execute with callback that prints all events
    result = full_chain.invoke(
        {"topic": "artificial intelligence"},
        config={"callbacks": [StdOutCallbackHandler()]}
    )
    
    print("-" * 40)
    print(f"✓ Final summary: {result.content[:80]}...")
    
    return {"method": "Callbacks", "note": "Detailed visibility into each step"}


# ============================================================================
# COMPARISON & SUMMARY
# ============================================================================

def print_comparison_summary():
    """
    Print a visual summary comparing all three approaches side-by-side.
    
    This table shows:
    - Traceability: How observable is execution?
    - Verbosity: How much code required?
    - Flexibility: How easy to extend?
    - Streaming: Token-by-token output support?
    - Batching: Multi-input processing support?
    - Async: Non-blocking execution?
    
    Use this to make decisions about which approach to use.
    """
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    
    comparison = """
    ┌─────────────────────────────────────────────────────────────────┐
    │                      APPROACH COMPARISON                        │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │ APPROACH 1: Direct LLM Call                                    │
    │   ├─ Traceability: ★☆☆ (Manual)                              │
    │   ├─ Verbosity: ★★★ (Very verbose)                           │
    │   ├─ Flexibility: ★☆☆ (Tightly coupled)                      │
    │   └─ Best for: Quick experiments, single calls                │
    │                                                                 │
    │ APPROACH 2: SimpleSequentialChain (LLMChain)                  │
    │   ├─ Traceability: ★★☆ (Basic hooks)                         │
    │   ├─ Verbosity: ★★☆ (Moderate)                               │
    │   ├─ Flexibility: ★☆☆ (Linear only)                          │
    │   └─ Best for: Simple 2-3 step pipelines (DEPRECATED)        │
    │                                                                 │
    │ APPROACH 3: RunnableSequence + LCEL                           │
    │   ├─ Traceability: ★★★ (Automatic LangSmith)                │
    │   ├─ Verbosity: ★☆☆ (Concise)                               │
    │   ├─ Flexibility: ★★★ (Fully composable)                     │
    │   ├─ Streaming: ✓ (Token-by-token)                           │
    │   ├─ Batching: ✓ (Efficient multi-input)                     │
    │   ├─ Async: ✓ (Built-in)                                     │
    │   └─ Best for: Production, teams, complex workflows           │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    """
    print(comparison)


if __name__ == "__main__":
    """
    MAIN EXECUTION BLOCK
    ════════════════════
    
    This script demonstrates all three chain approaches in sequence.
    Each approach solves the same problem (generate poem, then summarize)
    using different abstractions.
    
    EXECUTION FLOW:
    ───────────────
    1. Approach 1: Direct LLM
       └─ Shows manual orchestration in Python
       └─ Demonstrates observability challenges
    
    2. Approach 2: SimpleSequentialChain
       └─ Shows basic chain abstraction (deprecated)
       └─ Demonstrates string-based passing
    
    3. Approach 3: RunnableSequence + LCEL
       └─ Shows modern production approach
       └─ Demonstrates built-in observability
    
    4. Comparison Summary
       └─ Visual side-by-side comparison
       └─ Helps with decision making
    
    OUTPUT:
    ───────
    For each approach, you'll see:
    - Generated poem (from LLM)
    - Summary of poem
    - Observability metrics
    - Effort required for monitoring
    
    RECOMMENDATIONS:
    ────────────────
    After running this script:
    
    ✓ For new projects: Use Approach 3 (RunnableSequence + LCEL)
    ✓ For learning: Start with Approach 1, graduate to Approach 3
    ✓ For legacy code: Only maintain Approach 2 if needed
    
    NEXT STEPS:
    ───────────
    1. Review the ADR: ADR-1.2-Hello-World-Three-Ways.md
    2. Read ecosystem guide: LANGCHAIN_ECOSYSTEM_MAP.md
    3. Update README: Already includes detailed documentation
    4. Apply to your project: Use RunnableSequence + LCEL
    """
    print("\n" + "█" * 70)
    print("WORK PRODUCT 1.2: 'Hello World' Three Ways")
    print("Comparing Chain Types: Direct LLM, SimpleSequentialChain, RunnableSequence")
    print("█" * 70)
    
    # Run all three approaches
    result1 = approach_1_direct_llm()
    print(f"\n📝 Generated Poem:\n{result1['poem']}\n")
    print(f"📌 Summary: {result1['summary']}\n")
    print(f"📊 Observability: {result1['observability_effort']}")
    
    result2 = approach_2_simple_sequential_chain()
    print(f"\n📝 Generated Poem:\n{result2['poem']}\n")
    print(f"📌 Summary: {result2['summary']}\n")
    print(f"📊 Observability: {result2['observability_effort']}")
    
    result3 = approach_3_runnable_sequence_lcel()
    print(f"\n📌 Summary: {result3['summary']}\n")
    print(f"📊 Observability: {result3['observability_effort']}")
    
    # Print comparison
    print_comparison_summary()
    
    # Optional: Show advanced features (uncomment to run)
    # These demonstrate features only available in Approach 3
    print("\n" + "▌" * 70)
    print("ADVANCED FEATURES (Approach 3 Only)")
    print("▌" * 70)
    
    try:
        print("\nNote: Streaming and Batching demonstrations are commented out")
        print("to reduce API usage. Uncomment below to test:\n")
        
        # approach_3_streaming()
        # approach_3_batching()
        # approach_3_with_callbacks()
        
    except Exception as e:
        print(f"⚠️  Could not run advanced demos: {e}")
    
    print("\n" + "█" * 70)
    print("RECOMMENDATION")
    print("█" * 70)
    print("""
    For new projects: DEFAULT TO APPROACH 3 (RunnableSequence + LCEL)
    
    ✓ Best for production systems
    ✓ Best for team projects
    ✓ Best for observability (LangSmith integration)
    ✓ Best for future flexibility
    ✓ Supports streaming, batching, async
    
    Use Approach 1 for: Quick experiments and learning
    Use Approach 2 for: Maintaining legacy code only (deprecated)
    
    See ADR-1.2-Hello-World-Three-Ways.md for detailed analysis.
    """)
