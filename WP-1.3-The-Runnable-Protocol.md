# The `Runnable` Protocol: LangChain's Central Abstraction

**Work Product**: 1.3 - Deep Dive: Understanding the Foundation  
**Status**: Complete  
**Date**: 2024  
**Audience**: Engineers who want to understand LangChain's architecture, not just use LCEL  

---

## Executive Summary

The **`Runnable` protocol** is the engine of LangChain. Everything—prompts, language models, chains, tools—is a `Runnable`. Understanding this abstraction is the difference between using a framework and building with it.

This document dissects:
- **What** a Runnable is and why it matters
- **How** the four core methods (`invoke`, `batch`, `stream`, `ainvoke`) work
- **Why** composition creates a directed graph of Runnables
- **When** to compose vs. extend vs. customize
- **Architecture patterns** that scale from prototypes to production

**Key Insight**: A chain is not a special object. A chain is simply a graph of Runnables connected via the pipe operator. Understanding this changes how you architect AI systems.

---

## Part 1: What is a `Runnable`?

### The Protocol

```python
from langchain_core.runnables import Runnable

# Every Runnable implements:
class Runnable(Protocol):
    """A unit of computation that can be invoked, batched, streamed, or run asynchronously."""
    
    def invoke(self, input: Any, config: Optional[RunnableConfig] = None) -> Any:
        """Execute a single input synchronously.
        
        Returns: Output of the computation
        Raises: Exceptions from the computation or input validation
        """
        ...
    
    async def ainvoke(self, input: Any, config: Optional[RunnableConfig] = None) -> Any:
        """Execute a single input asynchronously (non-blocking).
        
        Returns: Output of the computation
        Semantics: Same result as invoke(), but doesn't block the event loop
        """
        ...
    
    def batch(self, inputs: List[Any], config: Optional[RunnableConfig] = None) -> List[Any]:
        """Execute multiple inputs efficiently in parallel.
        
        Returns: List of outputs (same order as inputs)
        Benefit: Respects rate limits, reuses connections, better throughput
        """
        ...
    
    def stream(self, input: Any, config: Optional[RunnableConfig] = None) -> Iterator[Any]:
        """Stream output chunks as they arrive.
        
        Yields: Chunks of the output (e.g., tokens from LLM)
        Benefit: Real-time output, lower perceived latency, lower memory usage
        """
        ...
```

### The Core Principle

**A `Runnable` is a unit of computation with four execution modes**:

1. **`invoke(input)`** — Single, synchronous call
2. **`batch(inputs)`** — Multiple inputs, synchronous (respects rate limits)
3. **`stream(input)`** — Single input, streaming chunks
4. **`ainvoke(input)`** — Single input, asynchronous (non-blocking)

Every implementation provides **all four**, but the core method is `invoke()`. The others are derived or optimized based on the implementation.

### Why This Matters

This unified interface means:
- ✅ **Composability**: Any Runnable can connect to any other Runnable
- ✅ **Consistency**: Same methods everywhere (prompts, models, chains, tools)
- ✅ **Flexibility**: Switch implementations without changing code
- ✅ **Scalability**: Batch and stream automatically without rewriting logic
- ✅ **Observability**: Same tracing hooks for all Runnables

---

## Part 2: The Four Execution Modes

### 1. `invoke()` — Synchronous Execution

**Purpose**: Execute once, wait for result.

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_template("Explain {concept} briefly")
model = ChatOpenAI(model="gpt-4-mini")

# invoke() - single, synchronous call
result = prompt.invoke({"concept": "machine learning"})
print(result)
# Output: ChatPromptValue(text="Explain machine learning briefly")

result = model.invoke(result)
print(result.content)
# Output: "Machine learning is a subset of AI where..."
```

**Characteristics**:
- **Blocking**: Code waits until completion
- **Simple**: Easy to understand and debug
- **Immediate**: No scheduling or callbacks
- **Default**: Most code uses this

**When to use**:
- Synchronous contexts (FastAPI endpoint, script)
- One-off computations
- Debugging

---

### 2. `batch()` — Efficient Parallel Execution

**Purpose**: Execute multiple inputs without serial loops.

```python
# ❌ SERIAL (slow, wasteful)
results = []
for topic in ["AI", "ML", "DL"]:
    result = model.invoke(prompt.invoke({"concept": topic}))
    results.append(result)

# ✅ PARALLEL (fast, efficient)
inputs = [{"concept": t} for t in ["AI", "ML", "DL"]]
chain = prompt | model
results = chain.batch(inputs)  # All three run in parallel
```

**How it works**:
1. Collect multiple inputs
2. Execute in parallel (respecting rate limits)
3. Return results in same order as inputs

**Implementation details**:
```python
# What batch() does internally:
def batch(self, inputs: List[Any], config: RunnableConfig = None) -> List[Any]:
    """
    1. Check if custom batch implementation exists
    2. If yes: use it (optimized for this Runnable)
    3. If no: fall back to parallel invoke() calls
    """
    # Example: ChatOpenAI has custom batch() that:
    # - Batches API requests
    # - Respects rate limits
    # - Reuses HTTP connections
    # - Returns results in order
```

**Benefits**:
- 🚀 **Throughput**: Process N items in ~1/N time vs. N serial calls
- 💾 **Connection reuse**: One connection pool for all inputs
- 🛡️ **Rate limit aware**: Automatically respects API limits
- 📊 **Cost efficient**: Fewer overhead calls

**When to use**:
- Processing multiple documents/items
- Batch jobs (overnight processing)
- Data pipelines
- Performance optimization

---

### 3. `stream()` — Incremental Output

**Purpose**: Receive output chunks as they arrive.

```python
# Without streaming: Wait for complete response
result = model.invoke(prompt.invoke({"concept": "quantum computing"}))
print(result.content)  # All at once after 2-3 seconds

# With streaming: See tokens as they appear
for chunk in model.stream(prompt.invoke({"concept": "quantum computing"})):
    print(chunk.content, end="", flush=True)
    # Output: "Quantum" (0.1s) "computing" (0.2s) "is" (0.3s) ...
```

**How it works**:
1. LLM generates tokens one at a time
2. Each token yielded immediately
3. Client processes chunks as they arrive
4. No buffering of entire response

**Semantics**:
```python
# stream() returns an Iterator[Any]
# Each chunk can be:
for chunk in chain.stream(input):
    # - Partial content (e.g., AIMessageChunk)
    # - Dictionary with partial data
    # - Any type the Runnable yields
    
    # Common pattern:
    if hasattr(chunk, 'content'):
        print(chunk.content, end="", flush=True)
```

**Implementation complexity**:
```python
# For Runnable A | Runnable B:

# A doesn't stream, B does:
#   stream() → invoke A → stream B
#
# A streams, B doesn't:
#   stream() → stream A → invoke B on each chunk
#
# Both stream:
#   stream() → stream A → stream B (token level)
#   Result: Full token-level streaming through entire chain

# Chain composition handles this automatically!
```

**When to use**:
- Chatbot UIs (Slack, Discord, web)
- Real-time dashboards
- Perceived latency reduction
- Long-form content (articles, code)
- Mobile/slow networks

---

### 4. `ainvoke()` — Asynchronous Execution

**Purpose**: Non-blocking execution (don't freeze event loop).

```python
import asyncio

# ❌ Blocking (freezes event loop)
async def bad_handler():
    result = model.invoke(prompt.invoke({"concept": "AI"}))
    # During invoke(), event loop is blocked
    # Can't handle other requests!

# ✅ Non-blocking (cooperative)
async def good_handler():
    result = await model.ainvoke(
        await prompt.ainvoke({"concept": "AI"})
    )
    # During ainvoke(), event loop can handle other requests
    # Better concurrency

# In FastAPI:
@app.post("/explain")
async def explain(concept: str):
    result = await (prompt | model).ainvoke({"concept": concept})
    return {"explanation": result.content}

# Handle 1000 concurrent requests efficiently!
```

**Composition with async**:
```python
# Runnables compose naturally in async:
chain = prompt | model | output_parser

# All three can run asynchronously:
result = await chain.ainvoke({"concept": "..."})

# No async/await boilerplate needed!
# LangChain handles the async composition internally
```

**When to use**:
- Web applications (FastAPI, Django)
- High-concurrency scenarios
- Microservices
- Event-driven architectures

---

## Part 3: Composition as a Graph

### The Pipe Operator Creates a Graph

```python
# Simple composition
chain = prompt | model

# This is NOT a string of operations
# This IS a Directed Acyclic Graph (DAG):

#   [Input] → [Prompt Runnable] → [Model Runnable] → [Output]
```

### Graph Example: Complex Workflow

```python
from langchain_core.runnables import RunnableParallel, RunnableBranch

# Step 1: Route based on input
router = RunnableBranch(
    (lambda x: "technical" in x["query"].lower(), technical_chain),
    (lambda x: "creative" in x["query"].lower(), creative_chain),
    general_chain  # default
)

# Step 2: Parallel processing
parallel = RunnableParallel(
    answer=router,
    sources=retriever,
    confidence=confidence_scorer
)

# Step 3: Final formatting
formatter = ChatPromptTemplate.from_template(
    "Answer: {answer}\nSources: {sources}\nConfidence: {confidence}"
)

# Compose the DAG
full_workflow = parallel | formatter | model

# Visualized as a graph:
#
#   Input Query
#       ↓
#   [Router] ← Decision point
#   /   |   \
#  /    |    \
# Tech  Gen  Creative
#  \    |    /
#   \   |   /
#    [Parallel]
#    /  |  \
# Answer Sources Confidence
#    \  |  /
#     [Dict]
#       ↓
#    [Formatter]
#       ↓
#     [Model]
#       ↓
#    Output
```

### Graph Properties

Each Runnable in a graph:
- **Has inputs**: Types/structure of data it accepts
- **Has outputs**: Types/structure it produces
- **Composes**: Output of one → Input of next
- **Executes**: In order during invoke/batch/stream
- **Traces**: Each node appears in execution traces

```python
# Introspect the graph
chain = prompt | model | output_parser

# Get the structure
print(chain.schema())
# {
#   "type": "object",
#   "properties": {
#     "concept": {"type": "string"}
#   }
# }

# Get visualization
chain.get_graph().draw_mermaid()
# Shows the DAG visually in Mermaid format
```

---

## Part 4: Architecture Diagrams

### Diagram 1: Simple Chain (Sequential DAG)

```
INPUT: {"topic": "quantum computing"}
  ↓
┌─────────────────────────────────────┐
│   ChatPromptTemplate Runnable       │
│   Input: {"topic": str}             │
│   Output: ChatPromptValue           │
│                                     │
│   (Renders template with variables) │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│   ChatOpenAI Runnable               │
│   Input: ChatPromptValue            │
│   Output: AIMessage                 │
│                                     │
│   (Calls LLM API, returns response) │
└─────────────────────────────────────┘
  ↓
OUTPUT: AIMessage(content="...")
```

### Diagram 2: Parallel Processing (DAG with Multiple Paths)

```
INPUT: {"documents": [...], "query": "..."}
  ↓
┌─────────────────────────────────────┐
│   RunnableParallel                  │
│   Runs all branches simultaneously   │
└─────────────────────────────────────┘
  ↙        ↓        ↘
  
[Branch 1]    [Branch 2]    [Branch 3]
  ↓              ↓              ↓
Retriever    Embedder      Ranker
  ↓              ↓              ↓
Chunks        Vectors       Scores
  ↓              ↓              ↓
  └─────────────┬────────────┘
                ↓
         (Results merged)
                ↓
         {"chunks": [...],
          "vectors": [...],
          "scores": [...]}
                ↓
          [Formatter Runnable]
                ↓
            Final Output
```

### Diagram 3: Conditional Routing (DAG with Decision Point)

```
INPUT: {"text": "...", "language": "..."}
  ↓
┌──────────────────────────────────────┐
│   RunnableBranch (Router)            │
│   Examines input                     │
│   Routes to appropriate chain        │
└──────────────────────────────────────┘
  ↙           ↓           ↘
  
if lang=="en"  if lang=="es"  else (fr)
  ↓               ↓              ↓
English Chain  Spanish Chain  French Chain
  ↓               ↓              ↓
[Process]      [Process]      [Process]
  ↓               ↓              ↓
  └───────────────┼──────────────┘
                  ↓
            Final Output
```

### Diagram 4: Complete Execution Model

```
                    [Input]
                       ↓
              ┌────────────────┐
              │ Runnable Graph │
              │  [A] → [B]→[C] │
              └────────────────┘
                       ↓
         ┌─────────────┼─────────────┐
         ↓             ↓             ↓
      invoke()      batch()       stream()
      (Single)     (Multiple)    (Chunks)
         ↓             ↓             ↓
    Synchronous   Parallel+      Iterator
    (Blocking)    Concurrent      (Async)
         ↓             ↓             ↓
      Execute A   Execute A's  Stream A's
        A→B→C     batch, then  output,
                  B's batch,   pipe to B
                  then C's
                       ↓
              [Output (same type)]

Note: All four modes produce the SAME RESULT,
      but with different execution characteristics
```

---

## Part 5: Implementation Deep Dive

### Custom Runnable: Understanding the Contract

```python
from langchain_core.runnables import RunnableBase
from typing import Any, Optional, List, Iterator

class MyCustomRunnable(RunnableBase):
    """A custom Runnable that demonstrates the protocol."""
    
    def __init__(self, multiplier: int = 2):
        super().__init__()
        self.multiplier = multiplier
    
    # REQUIRED: Core method
    def invoke(self, input: int, config: Optional[RunnableConfig] = None) -> int:
        """
        Synchronous execution.
        
        This is the core method.
        All others are derived from this.
        """
        return input * self.multiplier
    
    # OPTIONAL: Optimized implementations
    def batch(self, inputs: List[int], config: Optional[RunnableConfig] = None) -> List[int]:
        """
        Efficient batch processing.
        
        Custom implementation lets us:
        - Avoid creating list of invoke calls
        - Optimize for the operation (e.g., vectorize)
        - Respect rate limits
        """
        # Simple implementation: just call invoke()
        # (LangChain provides this default)
        return [self.invoke(input, config) for input in inputs]
    
    def stream(self, input: int, config: Optional[RunnableConfig] = None) -> Iterator[int]:
        """
        Stream output incrementally.
        
        For this simple operation, we yield once.
        For LLM, this would yield tokens.
        """
        yield self.invoke(input, config)
    
    async def ainvoke(self, input: int, config: Optional[RunnableConfig] = None) -> int:
        """
        Async version.
        
        For I/O-bound operations, this would use async/await.
        """
        # Simple operation is synchronous
        # In real code, might do: await some_async_call()
        return self.invoke(input, config)
    
    # OPTIONAL: Schema for input validation
    @property
    def input_schema(self):
        """Define input type for validation and docs."""
        from pydantic import BaseModel, Field
        
        class InputSchema(BaseModel):
            value: int = Field(..., description="The number to multiply")
        
        return InputSchema

# Usage
doubler = MyCustomRunnable(multiplier=2)

result = doubler.invoke(5)  # 10
results = doubler.batch([1, 2, 3])  # [2, 4, 6]

# Compose naturally
chain = prompt | model | doubler
result = chain.invoke({"concept": "..."})
```

### Composition Implementation: How Pipe Works

```python
# When you do: chain = A | B | C

# Python calls: A.__or__(B), which returns:
class RunnableSequence(RunnableBase):
    """A sequence of Runnables connected via pipe."""
    
    def __init__(self, first: Runnable, last: Runnable):
        self.first = first
        self.last = last
    
    def invoke(self, input: Any, config: RunnableConfig = None) -> Any:
        """Invoke first, pass output to last."""
        intermediate = self.first.invoke(input, config)
        return self.last.invoke(intermediate, config)
    
    def batch(self, inputs: List[Any], config: RunnableConfig = None) -> List[Any]:
        """Batch through first, then batch through last."""
        intermediates = self.first.batch(inputs, config)
        return self.last.batch(intermediates, config)
    
    def stream(self, input: Any, config: RunnableConfig = None) -> Iterator[Any]:
        """Stream through first, pass each chunk to last."""
        for chunk in self.first.stream(input, config):
            yield from self.last.stream(chunk, config)
    
    async def ainvoke(self, input: Any, config: RunnableConfig = None) -> Any:
        """Await first, then await last."""
        intermediate = await self.first.ainvoke(input, config)
        return await self.last.ainvoke(intermediate, config)
```

---

## Part 6: Execution Traces and Observability

### How Tracing Works with Runnables

Every Runnable supports callbacks:

```python
from langchain_core.callbacks import BaseCallbackHandler

class TracingCallback(BaseCallbackHandler):
    """Custom callback to trace execution."""
    
    def on_chain_start(self, serialized, inputs, **kwargs):
        chain_name = serialized.get("id", ["unknown"])[-1]
        print(f"▶️  Start: {chain_name}")
    
    def on_chain_end(self, outputs, **kwargs):
        print(f"◀️  End: {outputs}")

# Execute with tracing
chain = prompt | model
result = chain.invoke(
    {"concept": "quantum"},
    config={"callbacks": [TracingCallback()]}
)

# Output:
# ▶️  Start: ChatPromptTemplate
# ◀️  End: ChatPromptValue(...)
# ▶️  Start: ChatOpenAI
# ◀️  End: AIMessage(...)
```

### LangSmith Integration (Automatic)

```python
import os

# Enable LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGSMITH_API_KEY"] = "..."

# Every invoke() now traces to LangSmith:
# - Shows the DAG structure
# - Records input/output
# - Tracks latency
# - Captures token usage
# - Integrates with other callbacks

result = chain.invoke({"concept": "quantum"})
# ✅ Trace appears in LangSmith dashboard
```

---

## Part 7: Performance Characteristics

### Execution Model Comparison

```
┌─────────────────────────────────────────────────────────────┐
│           EXECUTION MODE COMPARISON                        │
├──────────┬──────────┬──────────┬──────────┬────────────────┤
│ Mode     │ Blocking │ Parallel │ Streaming│ Use Case      │
├──────────┼──────────┼──────────┼──────────┼────────────────┤
│ invoke() │ Yes      │ No       │ No       │ Simple logic  │
│ batch()  │ Yes      │ Yes      │ No       │ Batch jobs    │
│ stream() │ Yes      │ No       │ Yes      │ UX/real-time  │
│ ainvoke()│ No       │ No       │ No       │ Async/web app │
└──────────┴──────────┴──────────┴──────────┴────────────────┘

THROUGHPUT (N inputs, 1 sec latency per call):

1. Sequential invoke() in loop:
   for x in inputs:
       invoke(x)
   Time: N seconds ❌

2. batch():
   batch(inputs)
   Time: ~1 second ✅ (parallelized)

3. stream():
   for chunk in stream(input):
       print(chunk)
   Time: ~1 second + display ✅ (streaming tokens)

4. ainvoke() in loop with asyncio:
   async for task in [ainvoke(x) for x in inputs]:
       await task
   Time: ~1 second ✅ (concurrent)
```

### Optimization Guidelines

```
✓ DO:
  • Use batch() for N items → single invoke() call
  • Use stream() for real-time UI
  • Use ainvoke() in async contexts (FastAPI)
  • Compose Runnables instead of chaining manually

✗ DON'T:
  • Loop invoke() for multiple items (use batch())
  • Use await with synchronous invoke()
  • Block event loop with invoke() in FastAPI (use ainvoke())
  • Create new chain objects repeatedly (reuse instances)
```

---

## Part 8: Design Patterns

### Pattern 1: Branching (Conditional Routing)

```python
from langchain_core.runnables import RunnableBranch

# Define branches
is_coding = lambda x: "code" in x.get("query", "").lower()
is_math = lambda x: "math" in x.get("query", "").lower()

branches = [
    (is_coding, coding_chain),
    (is_math, math_chain),
]

router = RunnableBranch(*branches, default_chain)

# Usage
result = router.invoke({"query": "write a function"})
# → Uses coding_chain
```

### Pattern 2: Fallbacks (Error Handling)

```python
from langchain_core.runnables import RunnableWithFallbacks

# Try primary, fall back to secondary
chain_with_fallback = primary_model.with_fallbacks([
    secondary_model,
    tertiary_model,
])

# If primary fails, tries secondary, then tertiary
result = chain_with_fallback.invoke(input)
```

### Pattern 3: Retries (Resilience)

```python
from langchain.callbacks.manager import Retrying

# Built-in retry logic
chain_with_retry = chain.with_retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)

result = chain_with_retry.invoke(input)
```

### Pattern 4: Caching (Performance)

```python
# Cache results (in-memory, Redis, etc.)
cached_chain = chain.with_cache(InMemoryCache())

# First call: runs computation
result1 = cached_chain.invoke({"input": "quantum"})

# Second call: returns cached result
result2 = cached_chain.invoke({"input": "quantum"})
# ✅ Instant!
```

---

## Part 9: The Runnable Interface in Production

### Example: Building a Production Chatbot

```python
from fastapi import FastAPI, BackgroundTasks
from langchain_core.runnables import RunnableConfig

app = FastAPI()

# Build the Runnable chain
class ChatBot:
    def __init__(self):
        self.chain = (
            history_prompt
            | retriever
            | context_processor
            | llm
            | output_formatter
        )
        self.memory = ConversationMemory()
    
    async def chat(self, user_message: str) -> str:
        """Single-turn async response (for web)."""
        history = self.memory.get_history()
        
        config = RunnableConfig(
            callbacks=[LangSmithCallback()],  # Tracing
            metadata={"user_id": user_id},
        )
        
        result = await self.chain.ainvoke(
            {"message": user_message, "history": history},
            config=config,
        )
        
        self.memory.add(user_message, result)
        return result
    
    async def chat_stream(self, user_message: str):
        """Streaming response (for UX)."""
        # ainvoke + astream for true async streaming
        async for chunk in self.chain.astream(
            {"message": user_message},
            config=RunnableConfig(callbacks=[...])
        ):
            yield chunk.content

# FastAPI routes
chatbot = ChatBot()

@app.post("/chat")
async def chat(message: str):
    response = await chatbot.chat(message)
    return {"response": response}

@app.get("/chat-stream")
async def chat_stream(message: str):
    return StreamingResponse(
        chatbot.chat_stream(message),
        media_type="text/event-stream"
    )

# Batch processing (background job)
@app.post("/batch-analyze")
def batch_analyze(documents: List[str], background_tasks: BackgroundTasks):
    async def process_batch():
        results = await self.chain.abatch(
            [{"text": d} for d in documents],
            config={"max_concurrency": 5}
        )
        # Save results
    
    background_tasks.add_task(process_batch)
    return {"status": "processing"}
```

### Execution Timeline: Runnable in Production

```
HTTP Request arrives
    ↓
FastAPI route handler
    ↓
ainvoke(input, config)
    ↓
    ├─ LangSmith callback fires (start event)
    ├─ Chain executes (A | B | C)
    │   ├─ A.ainvoke() (retriever)
    │   ├─ B.ainvoke() (llm)
    │   └─ C.ainvoke() (formatter)
    └─ LangSmith callback fires (end event)
    ↓
Result returned to client
    ↓
LangSmith dashboard shows:
  - Full execution trace
  - Latency of each step
  - Token usage
  - Input/output
  - Any errors
```

---

## Part 10: Comparison with Other Frameworks

### Runnable vs. Traditional Approaches

```
Traditional Framework:
  for doc in documents:
      result = process(doc)       # Manual loop
      results.append(result)
  # No automatic batching, tracing, or streaming

LangChain Runnable:
  chain = retriever | processor | formatter
  results = chain.batch(documents)  # Built-in parallelization
  # Automatic tracing, retries, caching
```

### Why Runnable is More Than an Interface

The Runnable protocol is:
1. **Structural** — Defines what methods exist
2. **Semantic** — Defines what they mean (determinism, ordering)
3. **Composable** — Enables pipe operator and DAGs
4. **Observable** — Integrates with tracing systems
5. **Typed** — Input/output schemas for validation

This is not just an interface—it's a computation model.

---

## Part 11: Key Takeaways

### What Makes Runnable Powerful

| Aspect | Why It Matters |
|--------|-----------------|
| **Unified Interface** | Same methods for prompts, models, chains, tools |
| **Composition** | Build complex workflows by connecting simple units |
| **Async Native** | Non-blocking by design, perfect for web apps |
| **Streaming** | Real-time output without major refactoring |
| **Batching** | Automatic parallelization and rate limit handling |
| **Observability** | First-class support for tracing and monitoring |
| **Extensibility** | Custom Runnables fit seamlessly into chains |

### The Mental Model

Think of a LangChain application as:
```
A directed acyclic graph (DAG) of Runnables,
where data flows from input through nodes to output,
with four different execution modes:
  1. invoke() - single, blocking
  2. batch() - multiple, parallel
  3. stream() - single, incremental
  4. ainvoke() - single, async
```

Every application, from prototypes to production systems, uses this same model.

---

## Part 12: Next Steps

### For Deepening Understanding

1. **Read the source**: `langchain-core/runnables/base.py`
   - See how composition actually works
   - Understand the callback system

2. **Build a custom Runnable**:
   - Extend `RunnableBase`
   - Implement core methods
   - Compose with existing chains

3. **Optimize for your use case**:
   - Use `batch()` for throughput
   - Use `stream()` for latency perception
   - Use `ainvoke()` for concurrency

4. **Trace and monitor**:
   - Enable LangSmith
   - Create custom callbacks
   - Profile performance

### Questions to Ask Yourself

When building an AI system:
- "What's my Runnable graph?"
- "Which execution mode fits this use case?"
- "Where should I add custom Runnables?"
- "How do I trace and debug this?"

If you can answer these, you understand LangChain's architecture, not just its syntax.

---

## References

- [LangChain Core Documentation](https://python.langchain.com/docs/api_reference/core/)
- [Runnable Protocol Source](https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/runnables/base.py)
- ADR-1.2: "Hello World" Three Ways (comparison of abstraction levels)
- WP-1.2 Examples: `examples_1_2.py` (practical usage patterns)
- LANGCHAIN_ECOSYSTEM_MAP.md (broader context)

---

## Appendix: Quick Reference

### The Four Methods at a Glance

```python
# Single synchronous
result = runnable.invoke(input)

# Multiple synchronous (parallel)
results = runnable.batch([input1, input2, input3])

# Single streaming
for chunk in runnable.stream(input):
    print(chunk)

# Single asynchronous
result = await runnable.ainvoke(input)
```

### Composition Shortcuts

```python
# Pipe operator
chain = A | B | C

# Parallel
parallel = RunnableParallel(
    task1=chain1,
    task2=chain2,
)

# Conditional
router = RunnableBranch(
    (condition1, chain1),
    (condition2, chain2),
    default_chain,
)

# With error handling
chain_safe = chain.with_fallbacks([fallback1, fallback2])

# With retries
chain_resilient = chain.with_retry(stop=stop_after_attempt(3))
```

### Configuration

```python
config = RunnableConfig(
    callbacks=[MyCallback()],
    metadata={"user_id": "123"},
    run_name="my_run",
    max_concurrency=5,
    tags=["production", "critical"],
)

result = runnable.invoke(input, config=config)
```

---

**End of Document**

This document shows the engine beneath LCEL. Understanding Runnables means you can:
- Design systems that scale
- Debug execution flows
- Optimize for your constraints
- Build production systems with confidence

You're not just using a tool—you're building with it.
