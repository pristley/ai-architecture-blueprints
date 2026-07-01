# ADR-1.2: Chain Types - When to Use Direct LLM, SimpleSequentialChain, or RunnableSequence/LCEL

**Status**: Accepted  
**Date**: 2026  
**Implements**: Work Product 1.2 - "Hello World" Three Ways  

## Context

As LLM applications grow from simple prompts to multi-step workflows, developers must choose how to orchestrate chains of operations. LangChain provides three common patterns, each with different trade-offs and ecosystem positioning. We evaluated them through a simple task: generate a short poem, then summarize it.

This ADR maps to the **langchain-community** and **langchain-core** layers of the [LangChain Ecosystem Map](../reference/LANGCHAIN_ECOSYSTEM_MAP.md), establishing patterns for chain composition that scale from prototyping through production deployment with LangServe and observability with LangSmith.

## Decision

We recommend **selecting the right chain type based on application phase and complexity**:

- **Direct LLM Calls**: For prototyping, single-step tasks, and when explicit Python control is non-negotiable  
- **SimpleSequentialChain**: For simple, deterministic multi-step workflows with linear flow  
- **RunnableSequence + LCEL**: For production systems, complex workflows, and where observability and flexibility matter  

## Comparison Matrix

| Dimension | Direct LLM Call | SimpleSequentialChain | RunnableSequence + LCEL |
|-----------|-----------------|----------------------|------------------------|
| **Traceability** | Explicit but manual (you see each call in Python) | Good (chain objects provide execution hooks) | Excellent (callbacks, introspection, streaming, batching) |
| **Verbosity** | Most verbose (orchestration logic in Python) | Moderate (prompt templates required) | Least verbose (declarative composition via `\|` operator) |
| **Flexibility** | Limited (tight coupling of steps) | Low (string-based pass-through, linear only) | High (composable runnables, branching, parallel) |
| **Debugging** | Straightforward (standard Python debugging) | Moderate (chain objects, some introspection) | Excellent (LangSmith traces, callbacks, .stream().step_by_step) |
| **Performance** | Baseline (sequential API calls) | Baseline (sequential API calls) | Optimizable (batch, stream, cache, parallel) |
| **LangSmith Integration** | Manual logging required | Basic tracing available | Automatic tracing, full visibility |
| **LangServe Deployment** | Possible but verbose | Requires wrapping in Runnable | Native support via `.as_runnable()` |
| **Production Readiness** | Risky (hard to observe at scale) | Fair (static, predictable) | Production-ready (monitoring built-in) |

## When to Use Each (Practical Patterns)

### Direct LLM Call
**Best for:**
- Rapid prototyping and exploration  
- Single-step tasks requiring minimal abstraction  
- Situations where you need explicit Python control  
- Learning or teaching (lowest cognitive overhead)  
- Quick scripts that won't be reused or monitored

**Example:**
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4-mini")

# Step 1: Generate poem
poem_response = llm.invoke("Write a 4-line poem about AI")
poem = poem_response.content

# Step 2: Summarize
summary_response = llm.invoke(f"Summarize this in one sentence: {poem}")
summary = summary_response.content

print(f"Poem:\n{poem}")
print(f"\nSummary: {summary}")
```

**Practical Application:**
- Notebook experiments
- Internal tools for one-time analysis
- Learning LLM fundamentals
- Before formalizing into a chain

**Risks & Limitations:**
- As workflows grow, orchestration logic becomes scattered across Python code
- Observability requires custom logging (harder to trace with LangSmith)
- Difficult to scale: no built-in support for batching, streaming, or parallelism
- Cannot be easily deployed via LangServe
- No type safety or validation between steps
- Makes it hard to test individual steps independently

**When NOT to use:**
- Production systems (requires observability)
- Multi-step workflows (orchestration logic explodes)
- Team projects (hard to maintain or extend)

### SimpleSequentialChain
**Best for:**
- Simple, linear multi-step workflows where output of one step feeds directly into input of next
- When each step's output is a string that becomes the next step's input  
- Teams transitioning from direct LLM calls to chains  
- Low-stakes automations where flexibility isn't critical  
- Workflows that are unlikely to change

**Characteristics:**
- Provides basic chain abstraction (better than raw Python)
- Expects string-based pass-through between steps (output of step N becomes input of step N+1)
- Executes sequentially without branching or conditional logic
- Part of the `langchain` package (deprecated in favor of Runnables)

**Example:**
```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

llm = ChatOpenAI(model="gpt-4-mini")

# Chain 1: Generate poem
poem_prompt = ChatPromptTemplate.from_template(
    "Write a 4-line poem about {topic}"
)
poem_chain = LLMChain(llm=llm, prompt=poem_prompt)

# Chain 2: Summarize
summary_prompt = ChatPromptTemplate.from_template(
    "Summarize this in one sentence: {text}"
)
summary_chain = LLMChain(llm=llm, prompt=summary_prompt)

# Manual sequencing
poem = poem_chain.run(topic="artificial intelligence")
summary = summary_chain.run(text=poem)

print(f"Poem:\n{poem}")
print(f"\nSummary: {summary}")
```

**Practical Application:**
- Document summarization pipelines (read → extract → summarize)
- Content generation workflows (outline → draft → edit)
- Simple classification chains (parse → classify → format)

**Ecosystem Positioning:**
- Part of `langchain-community` (not langchain-core)
- Provides basic tracing hooks that LangSmith can capture
- Can be wrapped for LangServe, but requires additional conversion

**Risks & Limitations:**
- Limited to linear flows; difficult to extend when requirements change
- String-based output only (loses typed data between steps)
- No support for branching, parallel execution, or conditional routing
- Verbosity increases if you need conditional logic or error handling
- Deprecated in favor of RunnableSequence; new code should use Runnables
- Cannot easily re-use intermediate results
- Harder to test individual steps

**When NOT to use:**
- Production systems (use RunnableSequence instead)
- Complex workflows (use LangGraph for agentic loops)
- When you need typed data passing (use Runnables)
- When observability with LangSmith is important

### RunnableSequence + LCEL
**Best for:**
- Production systems requiring observability and debugging  
- Complex workflows with conditional logic, retries, or parallel branches  
- Applications using LangSmith for monitoring and evaluation  
- Teams building reusable, composable components  
- When streaming, batching, or async execution is required  
- Deployment via LangServe as REST APIs

**Characteristics:**
- Composable via operators: `chain = prompt | model | output_parser`  
- Full type safety and introspection  
- Built-in support for callbacks, streaming, batching, caching  
- Integrates seamlessly with LangSmith and LangGraph  
- Native support for `.invoke()`, `.batch()`, `.stream()`, `.astream()`
- Runnables are the core abstraction in `langchain-core`

**Example - Simple LCEL Chain:**
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4-mini")

# Define prompts
poem_prompt = ChatPromptTemplate.from_template(
    "Write a 4-line poem about {topic}"
)

summary_prompt = ChatPromptTemplate.from_template(
    "Summarize this in one sentence:\n{poem}"
)

# Compose chain using pipe operator
poem_chain = poem_prompt | llm

# This is the key: LCEL handles intermediate data passing
full_chain = (
    {"poem": poem_chain, "topic": lambda x: x["topic"]}
    | summary_prompt
    | llm
)

# Invoke
result = full_chain.invoke({"topic": "artificial intelligence"})
print(f"Summary: {result.content}")
```

**Example - Runnable with Tracing & Callbacks:**
```python
import os
from langsmith.run_trees import RunTree

# Enable LangSmith tracing (set env vars first)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "poem-summarizer"

# Chain automatically traced in LangSmith
result = full_chain.invoke({"topic": "artificial intelligence"})

# Or use callbacks for custom logging
from langchain_core.callbacks import StdOutCallbackHandler

result = full_chain.invoke(
    {"topic": "artificial intelligence"},
    config={"callbacks": [StdOutCallbackHandler()]}
)
```

**Example - Streaming Output:**
```python
# Stream response token-by-token (great for UX)
for chunk in full_chain.stream({"topic": "artificial intelligence"}):
    if hasattr(chunk, 'content'):
        print(chunk.content, end="", flush=True)
```

**Example - Batch Processing:**
```python
# Process multiple inputs efficiently
topics = ["AI", "Machine Learning", "Neural Networks"]
results = full_chain.batch([
    {"topic": t} for t in topics
])

for topic, result in zip(topics, results):
    print(f"{topic}: {result.content}")
```

**Example - LangServe Deployment:**
```python
# Deploy as REST API in seconds
from fastapi import FastAPI
from langserve import add_routes

app = FastAPI(title="Poem Summarizer")
add_routes(app, full_chain, path="/summarize")

# Now available at:
# POST /summarize/invoke
# POST /summarize/batch
# GET /summarize/stream?topic=...
# GET /summarize/openapi.json (auto-generated API docs)
```

**Practical Applications:**
- **RAG systems**: Document retrieval → context passing → LLM response
- **Multi-step reasoning**: Plan → Execute → Reflect → Iterate
- **Parallel processing**: Fetch from multiple sources in parallel, then combine
- **Error handling & retries**: Built-in error handling with fallback chains
- **Content moderation**: Input validation → Processing → Output filtering
- **Production APIs**: Chain becomes a microservice via LangServe

**Ecosystem Positioning:**
- Core abstraction from `langchain-core` (stable, minimal dependencies)
- Integrates with all `langchain-community` components
- Native integration with **LangSmith** (automatic tracing)
- Deployable with **LangServe** (REST API generation)
- Can be orchestrated by **LangGraph** for agentic workflows

**LangSmith Integration (Automatic):**
```python
# Just set env variables; everything is traced
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# LangSmith captures:
# ✅ Input/output of each step
# ✅ Latency of each LLM call
# ✅ Token usage and cost
# ✅ Error traces and debugging info
# ✅ Full callback hooks for custom logging

# View in LangSmith dashboard:
# - Execution traces (see each step)
# - Performance metrics (latency, cost)
# - Error analysis (what failed and why)
```

**Advantages:**
- **Simplest to reason about**: Declarative composition (what, not how)
- **Most flexible**: Easy to add branching, error handling, caching
- **Best for testing**: Each Runnable is independently testable
- **Scales well**: Built-in support for streaming, batching, parallelism
- **Future-proof**: Core abstraction, not deprecated

**Risks & Limitations:**
- Steeper learning curve initially (need to understand Runnable interface)
- LCEL composition syntax takes practice to master
- Less suitable for extremely simple one-off scripts (overkill)
- Requires understanding of async/await for advanced use cases

**When to use:**
✅ Any production system  
✅ Multi-step workflows  
✅ Team projects  
✅ When observability matters  
✅ When deploying via LangServe  
✅ When building components for reuse  

## Consequences

1. **Prototyping**: Start with Direct LLM Calls for speed. Migrate to Runnable chains as workflows mature.  
2. **Architecture**: Avoid mixing patterns in the same codebase; choose one strategy and standardize.  
3. **Observability**: Production systems must use Runnables + LCEL to enable tracing, debugging, and monitoring.  
4. **Team Velocity**: Short-term cost of learning LCEL/Runnable is offset by long-term reduction in debugging and iteration cycles.  

---

## Decision Flow: Which Pattern to Use?

```
Start here: What's your use case?

├─ Notebook / Quick Experiment?
│  └─→ Use Direct LLM Call
│      (Get answers fast, no boilerplate)
│
├─ Simple 2-3 step string pipeline?
│  ├─ Will this grow/change?
│  │  ├─ No → SimpleSequentialChain (rarely, legacy only)
│  │  └─ Yes → RunnableSequence + LCEL
│  │
│  └─ Legacy codebase?
│     └─ SimpleSequentialChain
│
└─ Production system / Team project / Complex workflow?
   └─→ RunnableSequence + LCEL
       (Observability, testability, deployment)
```

---

## Real-World Scenarios

### Scenario 1: You're Building a Document Summarization Tool (Team Project)

**Requirements:**
- Multi-step: Load → Extract → Summarize → Format
- Must monitor performance (costs, latency, accuracy)
- Need to deploy as API for others to use
- May add user feedback loop later

**Recommendation:** **RunnableSequence + LCEL**

```python
# Load document
loader_runnable = RunnableLambda(load_document)

# Extract relevant sections
extraction_chain = prompt_extract | llm

# Summarize
summary_chain = prompt_summarize | llm

# Format output
formatter = RunnableLambda(format_output)

# Compose all
full_pipeline = (
    loader_runnable
    | extraction_chain
    | (lambda x: {"content": x.content})  # Pass to summary
    | summary_chain
    | formatter
)

# Deploy with LangServe
app = FastAPI()
add_routes(app, full_pipeline, path="/summarize-doc")

# Monitor with LangSmith (set env vars)
# Trace all steps, costs, latency automatically
```

**Why not Direct LLM?** Manual orchestration is a mess with multiple steps. Observability becomes custom logging nightmare at scale.

**Why not SimpleSequentialChain?** Need typed data (extracted sections, metadata). Will need to add conditional logic (retry on failure, approve before sending). SimpleSequentialChain can't do this.

---

### Scenario 2: You're Exploring LLM Behavior in a Jupyter Notebook

**Requirements:**
- Quick experimentation
- Need to see LLM outputs immediately
- Probably won't reuse code
- Learning what works

**Recommendation:** **Direct LLM Call**

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4-mini")

# Try different prompts
poem = llm.invoke("Write a haiku about autumn")
print(poem.content)

# Refine based on output
summary = llm.invoke(f"Make this more concise: {poem.content}")
print(summary.content)

# Experiment with temperature
creative = ChatOpenAI(temperature=0.9).invoke("Write a wild poem")
print(creative.content)
```

**Why use this?** No setup, minimal code, fast iteration. Adding chains would slow you down.

**When to upgrade:** Once you've finalized the approach, formalize it as a Runnable for reuse.

---

### Scenario 3: You Have an Existing Legacy SimpleSequentialChain

**Requirements:**
- Codebase using SimpleSequentialChain
- Need to add conditional logic (retry on failure)
- Want better LangSmith integration

**Recommendation:** **Migrate to RunnableSequence + LCEL**

```python
# Old (SimpleSequentialChain)
from langchain.chains import SimpleSequentialChain, LLMChain

chain1 = LLMChain(llm=llm, prompt=prompt1)
chain2 = LLMChain(llm=llm, prompt=prompt2)
simple_chain = SimpleSequentialChain(chains=[chain1, chain2])

# New (RunnableSequence + LCEL)
chain = prompt1 | llm | prompt2 | llm

# Same functionality, but:
# ✅ Can add conditional logic
# ✅ Better LangSmith tracing
# ✅ Supports streaming, batching
# ✅ Type-safe composition
```

---

## Recommendation

For new projects, **default to RunnableSequence + LCEL**. It has the gentlest learning curve given its power, and grows with your application. Use Direct LLM for quick experiments. **Do not use SimpleSequentialChain for new code** (deprecated in favor of Runnables; only maintain existing instances).

### Learning Path

1. **Week 1**: Learn Direct LLM calls (understand ChatOpenAI, invoke())
2. **Week 2**: Learn Runnables basics (prompt | llm composition)
3. **Week 3**: Advanced: streaming, batching, callbacks
4. **Week 4**: Production: LangServe deployment + LangSmith monitoring

### Quick Start Template

```python
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Enable monitoring (optional but recommended)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "my-project"

llm = ChatOpenAI(model="gpt-4-mini")

# Step 1: Define prompts
prompt1 = ChatPromptTemplate.from_template("...")
prompt2 = ChatPromptTemplate.from_template("...")

# Step 2: Compose chain
chain = prompt1 | llm | prompt2 | llm

# Step 3: Use it
result = chain.invoke({...})

# Step 4 (optional): Deploy
from langserve import add_routes
from fastapi import FastAPI

app = FastAPI()
add_routes(app, chain, path="/my-chain")
```

---

**Reference Implementation:** See `examples_1_2.py` for working code samples of all three approaches.
