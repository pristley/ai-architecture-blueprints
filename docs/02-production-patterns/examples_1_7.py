"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         WORK PRODUCT 1.7: INTRODUCTION TO TRACING WITH LANGSMITH             ║
║                                                                              ║
║  Practical demonstration of LangSmith tracing for observability and debugging ║
╚══════════════════════════════════════════════════════════════════════════════╝

📚 PURPOSE:
───────────
This module demonstrates LangSmith tracing through practical examples.
You will learn how to enable tracing, understand trace structures,
and use traces to debug and optimize LLM chains.

🎯 LEARNING OBJECTIVES:
───────────────────────
By the end of this example, you will:
  ✓ Understand what LangSmith traces capture
  ✓ Know how to enable tracing in your chains
  ✓ Be able to read and interpret trace outputs
  ✓ Use traces to identify performance bottlenecks
  ✓ Understand token counting and cost tracking
  ✓ Learn to debug chain failures using traces

🔬 EXAMPLES COVERED:
─────────────────────

EXAMPLE 1: Basic Tracing Setup
──────────────────────────────────
Demonstrates: Enabling LangSmith tracing
Focus: Configuration and activation
Output: Automatic trace creation on chain invoke
Key Lesson: One environment variable enables full observability

EXAMPLE 2: Understanding Trace Structure
──────────────────────────────────────────
Demonstrates: Inspecting a trace programmatically
Focus: What information is captured
Output: Token counts, timings, costs
Key Lesson: Traces provide token-level granularity

EXAMPLE 3: Comparing Chains with Traces
──────────────────────────────────────────
Demonstrates: A/B testing using trace data
Focus: Which prompt/model is more efficient?
Output: Side-by-side metric comparison
Key Lesson: Data beats intuition—use traces to decide

EXAMPLE 4: Debugging with Traces
───────────────────────────────────
Demonstrates: Using traces to investigate failures
Focus: Finding where chains break
Output: Root cause analysis
Key Lesson: Traces show exactly what went wrong and where

🔑 KEY CONCEPTS:
────────────────
1. AUTOMATIC TRACING
   Just set environment variables—no code changes needed!
   - LANGSMITH_TRACING=true
   - LANGSMITH_PROJECT=my-project
   - LANGSMITH_API_KEY=...

2. TRACE STRUCTURE
   Every trace captures:
   - Input and output at each step
   - Token counts (prompt and completion)
   - Timing breakdowns (TTFT, generation time)
   - Cost calculations
   - Error details

3. OBSERVABILITY BENEFITS
   - Performance: Know where time is spent
   - Cost: Know exactly what requests cost
   - Debugging: Replay execution step-by-step
   - Optimization: Data-driven improvements

💡 BEST PRACTICES:
──────────────────
• Enable tracing during development to understand your chain
• Use traces to baseline metrics before optimizing
• Trace 10% of production requests for continuous monitoring
• Set up dashboards to track trends over time
• Use traces to compare models/prompts (A/B testing)
• Always trace errors for debugging
• Remember: Tracing adds small overhead—use wisely in production

⚠️  COMMON MISTAKES:
────────────────────
✗ Tracing every single production request (expensive, adds latency)
✗ Not tracing at all (flying blind—can't optimize what you don't see)
✗ Ignoring trace data (collecting without analyzing)
✗ Tracing only errors (you miss the baseline for comparison)
✗ Not using structured metadata (harder to analyze later)

📋 USAGE:
──────────
# Enable tracing first:
export LANGSMITH_API_KEY="your-api-key-from-smith.langchain.com"
export LANGSMITH_PROJECT="my-project"
export LANGSMITH_TRACING="true"

# Run this file:
    python examples_1_7.py

Each example is self-contained and can be run independently.

📖 REFERENCES:
───────────────
- WP-1.7-Introduction-to-Tracing-with-LangSmith.md (full documentation)
- WP-1.3-The-Runnable-Protocol.md (chain structure)
- WP-1.4-Prompt-Engineering-as-Code.md (prompt optimization with traces)
- WP-1.5-Output-Parsing-for-System-Integration.md (debugging parsing with traces)
- LangSmith Documentation: https://docs.smith.langchain.com
"""

import os
from datetime import datetime

# Import LangChain components
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableConfig

# ============================================================================
# SETUP: Configuration for LangSmith Tracing
# ============================================================================

def setup_tracing(project_name: str = "ai-architecture-blueprints"):
    """
    Configure LangSmith tracing.
    
    For this to work, you need:
    1. Create a LangSmith account: https://smith.langchain.com
    2. Get API key from Settings → API Keys
    3. Set environment variables:
       export LANGSMITH_API_KEY="your-api-key"
       export LANGSMITH_PROJECT="my-project"
       export LANGSMITH_TRACING="true"
    """
    api_key = os.environ.get("LANGSMITH_API_KEY")
    
    if not api_key:
        print("\n⚠️  WARNING: LangSmith API key not set!")
        print("\nTo enable tracing, set environment variables:")
        print("  export LANGSMITH_API_KEY='your-api-key'")
        print("  export LANGSMITH_PROJECT='ai-architecture-blueprints'")
        print("  export LANGSMITH_TRACING='true'")
        print("\nGet your API key at: https://smith.langchain.com/settings/api-keys")
        print("\nRunning examples without tracing... (output will not be sent to LangSmith)")
        return False
    
    os.environ["LANGSMITH_PROJECT"] = project_name
    os.environ["LANGSMITH_TRACING"] = "true"
    print(f"\n✅ LangSmith tracing enabled for project: {project_name}")
    return True


# ============================================================================
# EXAMPLE 1: Basic Tracing - Automatic Token and Cost Tracking
# ============================================================================

def example_1_basic_tracing():
    """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║                    EXAMPLE 1: BASIC TRACING SETUP                      ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    GOAL:
    ─────
    Run a simple chain with LangSmith tracing enabled.
    The trace will automatically capture:
    - Prompt tokens and cost
    - Completion tokens and cost
    - TTFT (time-to-first-token)
    - Total duration
    - All errors (if any)
    
    WHAT HAPPENS:
    ──────────────
    1. Create a prompt template
    2. Create an LLM model
    3. Compose them into a chain
    4. Invoke the chain (automatically traced if LANGSMITH_TRACING=true)
    5. Open https://smith.langchain.com to see the trace
    
    KEY INSIGHT:
    ─────────────
    No changes to your code! Just set environment variables.
    LangChain automatically instruments every Runnable.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Tracing - Automatic Token and Cost Tracking")
    print("="*70)
    
    # Create a simple chain: prompt → LLM
    prompt = ChatPromptTemplate.from_template(
        "You are a helpful assistant. Answer this question: {question}"
    )
    model = ChatOpenAI(model="gpt-4-mini", temperature=0.7)
    chain = prompt | model
    
    # Invoke with explicit run configuration
    # (This metadata will appear in the trace)
    config = RunnableConfig(
        run_name="example_1_basic_tracing",
        tags=["example", "basic", "tracing"],
        metadata={
            "example": "1",
            "description": "Simple chain with automatic tracing",
            "timestamp": datetime.now().isoformat(),
        }
    )
    
    print("\n🔍 Invoking chain with LangSmith tracing enabled...")
    print("   (Check https://smith.langchain.com to see the trace)")
    
    try:
        result = chain.invoke(
            {"question": "What is the capital of France?"},
            config=config
        )
        print("\n✅ Chain invoked successfully!")
        print(f"\n📤 Response:\n{result.content}")
        print("\n💡 What LangSmith captured:")
        print("   • Prompt tokens and cost")
        print("   • Completion tokens and cost")
        print("   • TTFT (time-to-first-token)")
        print("   • Total duration")
        print("   • All metadata you provided")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n   This usually means OPENAI_API_KEY is not set.")
        print("   Set it: export OPENAI_API_KEY='sk-...'")


# ============================================================================
# EXAMPLE 2: Understanding Trace Structure
# ============================================================================

def example_2_trace_structure():
    """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║               EXAMPLE 2: UNDERSTANDING TRACE STRUCTURE                 ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    GOAL:
    ─────
    Understand what information is captured in a trace.
    
    TRACE CAPTURES:
    ────────────────
    • Input: Exact input sent to each component
    • Output: Exact output from each component
    • Tokens: Prompt and completion token counts
    • Cost: Calculated from token counts
    • Timing: TTFT, generation time, total duration
    • Metadata: Tags, run name, custom metadata
    
    HOW TO READ A TRACE:
    ─────────────────────
    1. Open https://smith.langchain.com/projects/your-project/
    2. Click on the most recent trace
    3. Expand each "span" to see details
    4. Look for:
       - TTFT (time-to-first-token): How fast was response?
       - Token counts: How much did it cost?
       - Errors: Did something go wrong?
    
    EXAMPLE TRACE STRUCTURE:
    ────────────────────────
    Root Span: chain_name
    ├─ Span 1: prompt (ChatPromptTemplate)
    │  ├─ Input: {"question": "..."}
    │  ├─ Output: "You are a helpful assistant..."
    │  └─ Duration: 2ms (formatting is fast!)
    │
    ├─ Span 2: llm_call (ChatOpenAI)
    │  ├─ Input tokens: 45
    │  ├─ Output tokens: 23
    │  ├─ Cost: $0.00089
    │  ├─ TTFT: 145ms (time to first token)
    │  ├─ Total duration: 280ms
    │  └─ Output: "Paris is the capital of France..."
    │
    └─ Final Output: Message(content="Paris...")
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Understanding Trace Structure")
    print("="*70)
    
    # Run a chain that clearly shows structure
    classification_prompt = ChatPromptTemplate.from_template(
        """Classify the following question into one of: BILLING, TECHNICAL, GENERAL
        
Question: {question}

Respond with ONLY the classification word."""
    )
    
    model = ChatOpenAI(model="gpt-4-mini", temperature=0)
    chain = classification_prompt | model
    
    config = RunnableConfig(
        run_name="example_2_trace_structure",
        tags=["example", "structure"],
        metadata={
            "example": "2",
            "description": "Shows trace structure clearly",
        }
    )
    
    print("\n🔍 Running classification chain...")
    try:
        result = chain.invoke(
            {"question": "Why is my bill so high?"},
            config=config
        )
        classification = result.content.strip()
        print(f"\n✅ Classification: {classification}")
        
        print("\n📊 What the trace captured:")
        print("   Root Span: classification_chain")
        print("   ├─ Span 1: format_prompt (ChatPromptTemplate)")
        print("   │  └─ Duration: ~1-2ms (very fast!)")
        print("   ├─ Span 2: llm_call (ChatOpenAI)")
        print("   │  ├─ Input tokens: ~30")
        print("   │  ├─ Output tokens: ~1")
        print("   │  ├─ TTFT: ~100-200ms")
        print("   │  └─ Cost: ~$0.00005")
        print("   └─ Final output: \"BILLING\"")
        
        print("\n💡 Key observations:")
        print("   • Prompt formatting is negligible (<2ms)")
        print("   • LLM call dominates duration")
        print("   • Small output = low cost")
        print("   • Total cost per request is tiny!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


# ============================================================================
# EXAMPLE 3: Debugging with Traces (Comparing Approaches)
# ============================================================================

def example_3_debugging_with_traces():
    """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║              EXAMPLE 3: DEBUGGING WITH TRACES                          ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    GOAL:
    ─────
    Use trace comparison to find performance issues.
    
    SCENARIO:
    ──────────
    You have a customer support chain that sometimes is slow.
    How do you debug? Use traces!
    
    TRACE ANALYSIS:
    ────────────────
    1. Slow response detected
    2. Open trace in LangSmith
    3. Look at timeline:
       - Is TTFT high? → OpenAI is slow (retry, or use fallback model)
       - Is token generation slow? → Check prompt size (reduce tokens)
       - Is parsing slow? → Optimize parser or use structured output
    
    EXAMPLE HYPOTHESIS:
    ─────────────────────
    "My support chain takes 3 seconds, but should be <2 seconds."
    
    Trace shows:
    - LLM call #1: 2.1s (70% of time) ← PROBLEM!
       └─ TTFT: 800ms (high! OpenAI is busy)
       └─ Token generation: 1.3s
    - Parsing: 45ms (fast)
    - LLM call #2: 0.8s (27% of time)
    
    Solution: Use faster model (GPT-4-mini) or reduce prompt size
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Debugging with Traces")
    print("="*70)
    
    # Build a more complex chain: classify + respond
    classification_prompt = ChatPromptTemplate.from_template(
        """Classify the customer inquiry:
        
Inquiry: {inquiry}

Respond with JSON: {{"category": "...", "urgency": "..."}}"""
    )
    
    response_prompt = ChatPromptTemplate.from_template(
        """You are a helpful support agent. The customer's issue is {category}.
        
Their inquiry: {inquiry}

Respond helpfully and concisely."""
    )
    
    model = ChatOpenAI(model="gpt-4-mini", temperature=0.7)
    parser = JsonOutputParser()
    
    # Chain: format prompt → classify → parse → format response → answer
    chain = (
        classification_prompt
        | model
        | parser
        | (lambda x: {"category": x["category"], "inquiry": "{inquiry}"})
        | response_prompt
        | model
    )
    
    config = RunnableConfig(
        run_name="example_3_complex_chain",
        tags=["example", "debugging"],
        metadata={
            "example": "3",
            "description": "Complex chain with multiple steps",
        }
    )
    
    print("\n🔍 Running multi-step support chain...")
    try:
        result = chain.invoke(
            {"inquiry": "My order is late and I need it tomorrow!"},
            config=config
        )
        print("\n✅ Response generated successfully!")
        print(f"\n📤 Response:\n{result.content}")
        
        print("\n📊 Trace breakdown (what LangSmith captured):")
        print("   Root Span: support_chain")
        print("   ├─ Span 1: format_classification_prompt")
        print("   │  └─ Duration: 1ms")
        print("   ├─ Span 2: classify_model (LLM)")
        print("   │  ├─ Prompt tokens: ~50")
        print("   │  ├─ Completion tokens: ~30")
        print("   │  ├─ TTFT: ~150ms")
        print("   │  └─ Duration: ~400ms")
        print("   ├─ Span 3: parse_json")
        print("   │  └─ Duration: 2ms (fast!)")
        print("   ├─ Span 4: format_response_prompt")
        print("   │  └─ Duration: 1ms")
        print("   ├─ Span 5: response_model (LLM)")
        print("   │  ├─ Prompt tokens: ~80")
        print("   │  ├─ Completion tokens: ~45")
        print("   │  ├─ TTFT: ~160ms")
        print("   │  └─ Duration: ~600ms")
        print("   └─ Total: ~1,200ms")
        
        print("\n💡 Debugging insights from trace:")
        print("   ✓ Both LLM calls dominate (400ms + 600ms = 1s)")
        print("   ✓ Parsing is negligible (2ms)")
        print("   ✓ Formatting is negligible (2ms)")
        print("   ⚠️  TTFT is high (150-160ms) - consider retry logic")
        print("   💡 Total latency is acceptable for async operations")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


# ============================================================================
# EXAMPLE 4: Custom Tracing with Metadata
# ============================================================================

def example_4_custom_metadata():
    """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║           EXAMPLE 4: CUSTOM TRACING WITH METADATA                      ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    GOAL:
    ─────
    Add custom metadata to traces for better analysis.
    
    WHY CUSTOM METADATA:
    ─────────────────────
    • User ID: Track performance per user
    • Request ID: Correlate with application logs
    • Model: Know which model was used for A/B testing
    • Latency SLA: Flag violations
    • Feature flags: Track which features were enabled
    
    METADATA EXAMPLE:
    ──────────────────
    {
        "user_id": "CUST-12345",
        "request_id": "REQ-789",
        "model": "gpt-4-mini",
        "latency_sla_ms": 2000,
        "feature_flags": ["structured_output", "prompt_caching"],
    }
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Custom Tracing with Metadata")
    print("="*70)
    
    prompt = ChatPromptTemplate.from_template(
        "Answer briefly: {question}"
    )
    model = ChatOpenAI(model="gpt-4-mini", temperature=0.5)
    chain = prompt | model
    
    # Add rich metadata for production debugging
    user_id = "CUST-12345"
    request_id = "REQ-789"
    
    config = RunnableConfig(
        run_name="customer_query",
        tags=["production", "customer-support"],
        metadata={
            "user_id": user_id,
            "request_id": request_id,
            "model": "gpt-4-mini",
            "latency_sla_ms": 2000,
            "feature_flags": ["structured_output"],
            "region": "us-east-1",
            "timestamp": datetime.now().isoformat(),
        }
    )
    
    print(f"\n🔍 Running chain for user {user_id}, request {request_id}...")
    try:
        result = chain.invoke(
            {"question": "What's the weather in Paris?"},
            config=config
        )
        print("\n✅ Request processed successfully!")
        print(f"\n📤 Response:\n{result.content}")
        
        print("\n📊 Metadata saved to trace:")
        print(f"   • User ID: {user_id}")
        print(f"   • Request ID: {request_id}")
        print("   • Model: gpt-4-mini")
        print("   • Latency SLA: 2000ms")
        print("   • Feature flags: structured_output")
        
        print("\n💡 Now you can filter/analyze traces by:")
        print("   • Traces for user CUST-12345")
        print("   • Traces for request REQ-789")
        print("   • Traces using gpt-4-mini")
        print("   • Traces violating SLA")
        print("   • Traces with feature_flags=structured_output")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


# ============================================================================
# MAIN: Run All Examples
# ============================================================================

def main():
    """Run all tracing examples."""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*10 + "WP-1.7: INTRODUCTION TO TRACING WITH LANGSMITH" + " "*12 + "║")
    print("║" + " "*15 + "Practical Examples and Demonstrations" + " "*17 + "║")
    print("╚" + "="*68 + "╝")
    
    # Setup tracing
    tracing_enabled = setup_tracing()
    
    if not tracing_enabled:
        print("\n⚠️  LangSmith tracing is disabled.")
        print("Examples will run but traces won't be sent to smith.langchain.com")
    
    # Run examples
    try:
        example_1_basic_tracing()
        example_2_trace_structure()
        example_3_debugging_with_traces()
        example_4_custom_metadata()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running examples: {e}")
        print("\nCommon issues:")
        print("  • OPENAI_API_KEY not set")
        print("  • OpenAI API quota exceeded")
        print("  • Network connectivity issue")
    
    print("\n" + "="*70)
    print("✅ Examples complete!")
    print("="*70)
    print("\nNext steps:")
    print("1. Enable tracing: set LANGSMITH_API_KEY and LANGSMITH_TRACING=true")
    print("2. View traces: open https://smith.langchain.com")
    print("3. Analyze: Look at token counts, timing, costs")
    print("4. Optimize: Use trace insights to improve your chains")
    print("\nFor details, see: WP-1.7-Introduction-to-Tracing-with-LangSmith.md")
    print()


if __name__ == "__main__":
    main()
