# AI Architecture Blueprints

[![CI/CD Pipeline](https://github.com/pristley/ai-architecture-blueprints/workflows/AI%20Architecture%20Blueprints%20CI%2FCD/badge.svg?branch=main)](https://github.com/pristley/ai-architecture-blueprints/actions)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](VERSION)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-latest-orange.svg)](https://github.com/langchain-ai/langchain)
[![Documentation](https://img.shields.io/badge/docs-latest-success.svg)](https://pristley.github.io/ai-architecture-blueprints)
[![Status](https://img.shields.io/badge/status-production-brightgreen.svg)](#)

**Production-Ready Design Patterns for LLM Systems**

A comprehensive guide to building scalable, observable, and maintainable AI systems using LangChain. This repository contains architecture decision records, design patterns, and proven implementations for enterprise-grade AI applications.

---

## 📊 Repository Status

| Metric | Value |
|--------|-------|
| **Version** | [1.0.0](VERSION) |
| **Status** | ✅ Production-Ready |
| **Python** | 3.9+ |
| **License** | [MIT](LICENSE) |
| **Documentation** | [8,500+ lines](AGENTMAP.md#document-statistics) |
| **CI/CD** | 4-job pipeline, 52s deployment |
| **Examples** | 15+ working demonstrations |
| **Unit Tests** | 6/6 passing |
| **Last Updated** | 2026-06-24 |

See [CHANGELOG.md](CHANGELOG.md) for release history.

---

## ⭐ Highlights

- 🏗️ **Architecture-First Design** - 8-dimension comparison matrix for making informed decisions
- 🎯 **Production Patterns** - Real-world strategies for reliability, observability, and scaling
- 📚 **Complete Documentation** - From fundamentals to advanced patterns with 15+ examples
- ⚡ **Fast Iteration** - Automated CI/CD pipeline with instant GitHub Pages deployment
- 🧪 **Tested & Proven** - All examples validated with 6+ unit tests and 100% syntax pass rate
- 🔗 **Full Ecosystem** - Reference guide for entire LangChain stack (core, community, services)
- 🤖 **Modern DevOps** - GitHub Actions automation with auto-documentation updates
- 📖 **Visual Navigation** - Knowledge graph with Mermaid diagrams for quick orientation

---

## Table of Contents

1. [Overview](#overview)
2. [Design Philosophy](#design-philosophy)
3. [Getting Started](#getting-started)
4. [Documentation](#documentation)
5. [Technical Architecture](#technical-architecture)
6. [Implementation Patterns](#implementation-patterns)
7. [Learning Path](#learning-path)
8. [Setup & Configuration](#setup--configuration)

---

## Overview

### Purpose

This repository addresses the core challenge of building production AI systems: **how to compose unreliable components (LLMs, APIs) into reliable, observable, scalable systems.**

We provide:
- **Architectural decisions** backed by trade-off analysis
- **Reference implementations** with complete observability
- **Design patterns** proven in production
- **Ecosystem guidance** for the LangChain stack

### What You'll Get

| Goal | Document | Time |
|------|----------|------|
| **Understand which pattern to use** | [ADR-1.2](#adr-12-chain-abstractions) | 30 min |
| **See working implementations** | [examples_1_2.py](#examples) | 30 min |
| **Master the architecture** | [WP-1.3](#wp-13-runnable-protocol) | 2 hours |
| **Manage prompts in production** | [WP-1.4](#wp-14-prompt-engineering-as-code) | 90 min |
| **Parse structured output safely** | [WP-1.5](#wp-15-output-parsing-for-system-integration) | 45 min |
| **Navigate the full ecosystem** | [AGENTMAP.md](#agentmap-visual-navigation) | 20 min |
| **Reference component stack** | [LANGCHAIN_ECOSYSTEM_MAP.md](#langchain-ecosystem) | 45 min |

---

## Design Philosophy

### Five Core Principles

**1. Observability First**
- Every component reports what it's doing
- Full execution traces for debugging
- Automatic monitoring with LangSmith
- Performance metrics at every stage

**2. Composability by Design**
- Small, single-purpose units
- Standardized interfaces (Runnables)
- Compose from simple to complex
- No monolithic chains

**3. Explicit Trade-offs**
- Evaluate every pattern across: latency, cost, accuracy, flexibility
- Document why you chose approach X over Y
- Make trade-offs visible in code
- Review periodically as requirements change

**4. Defensive Implementation**
- Error handling at component boundaries
- Retry policies and fallbacks
- Graceful degradation
- Never silent failures

**5. Production Readiness**
- Design for scale from day one
- Async/await as standard
- Batch processing for throughput
- Streaming for latency

---

## Getting Started

### Quick Navigation

**Lost? Start here:**
- 🗺️ **Full map** → [AGENTMAP.md](AGENTMAP.md) - Visual graph of all documents
- 🚀 **Fast track (30 min)** → [ADR-1.2](#adr-12-chain-abstractions) - Which pattern to use
- 📚 **Deep dive (2 hours)** → [WP-1.3](#wp-13-runnable-protocol) - How it works
- 📈 **Typed extraction (45 min)** → [WP-1.5](#wp-15-output-parsing-for-system-integration) - Parse and recover structured output
- 🏭 **Production (1 hour)** → See [Setup & Configuration](#setup--configuration)

### Installation

```bash
# Core LangChain
pip install langchain langchain-core langchain-openai

# Optional: for REST APIs
pip install langserve

# Optional: for production monitoring
pip install langsmith
```

### First Example

```bash
# See three chain abstractions in action
python examples_1_2.py

# Output: Three approaches to the same task, with observability comparison
```

---

## Documentation

### AGENTMAP: Visual Navigation

**[AGENTMAP.md](AGENTMAP.md)** is your visual guide showing:
- All documents and how they relate
- Multiple learning paths based on your goal
- Cross-reference matrix for quick answers
- Mastery checklist to track progress

**Use this when you need to:**
- Understand how documents connect
- Find the right starting point
- Navigate between related topics
- Check your understanding

---

### ADR-1.2: Chain Abstractions

**[ADR-1.2-Hello-World-Three-Ways.md](ADR-1.2-Hello-World-Three-Ways.md)** answers: *"Which pattern should I use?"*

#### Problem

As applications grow from single prompts to multi-step workflows, you must choose how to orchestrate operations. Each approach has different trade-offs in:
- Observability (how visible is execution?)
- Flexibility (can I add branching/parallelism?)
- Performance (can I optimize with batching/streaming?)
- Maintainability (how obvious is the code?)

#### Three Approaches Evaluated

| Approach | When | Trade-offs |
|----------|------|-----------|
| **Direct LLM Call** | Learning, experiments | Full control, zero abstraction, no observability |
| **SimpleSequentialChain** | Legacy code | Some abstraction, string-only, deprecated |
| **RunnableSequence + LCEL** | Production | Full composability, auto tracing, streaming/batching |

#### Recommendation

**Use RunnableSequence + LCEL for all new work:**
```python
chain = (
    ChatPromptTemplate.from_template("...") 
    | ChatOpenAI() 
    | StrOutputParser()
)
# Automatically: async, streaming, batching, tracing, deployable
```

**Why?**
- ✅ Automatic LangSmith integration
- ✅ Declarative syntax (pipe operator)
- ✅ Composable (works with RunnableParallel, RunnableBranch, etc.)
- ✅ Native REST API via LangServe
- ✅ Built-in batch(), stream(), ainvoke()
- ✅ Full debugging and introspection

#### Contains

- 8-dimension comparison matrix
- Real-world scenarios and recommendations
- Learning path (4-week progression)
- Decision flow diagram
- Production checklist

---

### WP-1.3: Runnable Protocol

**[WP-1.3-The-Runnable-Protocol.md](WP-1.3-The-Runnable-Protocol.md)** answers: *"How does LangChain actually work?"*

#### The Core Insight

```
A chain is a directed acyclic graph (DAG) of Runnables.

input → [Runnable] → [Runnable] → [Runnable] → output

Every Runnable has 4 execution modes:
  invoke(x)    → single sync call
  batch(xs)    → multiple parallel calls
  stream(x)    → chunks as they arrive
  ainvoke(x)   → single async call
```

#### Why This Matters

Once you understand that a "chain" is just a graph of Runnables with a standard interface, you can:
- Build custom components (database lookups, APIs, ML models)
- Compose them seamlessly
- Get parallelism and streaming for free
- Debug execution flows
- Optimize performance
- Build anything

#### Contains

- Protocol definition and semantics
- Deep dive on all 4 execution modes
- How composition creates DAGs
- Implementing custom Runnables
- Performance optimization patterns
- Production deployment patterns

#### Practice Examples

**[examples_1_3.py](examples_1_3.py)** provides hands-on demonstrations:

1. **The Four Execution Modes** - See invoke, batch, stream, ainvoke work
2. **Custom Runnable** - Build your own Runnable from scratch
3. **DAG Composition** - See how pipes create parallel execution
4. **Execution Tracing** - Understand the full execution flow
5. **Conditional Routing** - Route to different handlers based on input
6. **Batch Performance** - Why batch() is 10-100x faster

Each example includes detailed comments explaining WHY, not just WHAT.

---

### WP-1.4: Prompt Engineering as Code

**[WP-1.4-Prompt-Engineering-as-Code.md](WP-1.4-Prompt-Engineering-as-Code.md)** answers: *"How do I manage prompts at scale?"*

#### The Problem

Prompts are not strings. They are executable configuration that encodes business logic. When prompts live as hard-coded strings:
- No versioning (can't A/B test or roll back)
- No reuse (copy-paste drift across 12 files)
- No composition (each specialist re-declares base rules)
- No testability (only way to test is to call the LLM)
- Multi-turn chaos (conversation history appended ad hoc)

#### The Pattern

```python
# Treat prompts like code: named, versioned, composable
registry = PromptRegistry()
registry.register(
    name="customer_support",
    template=ChatPromptTemplate.from_messages([
        ("system", "You are a {role} at {company}..."),
        MessagesPlaceholder("history"),  # multi-turn slot
        ("human", "{input}"),
    ]),
    version="v1.1",
    description="Added escalation protocol",
    author="cx-team",
)

# Get any version by name
prompt = registry.get("customer_support")           # latest
prompt = registry.get("customer_support", "v1.0")  # specific

# Compose: base rules + domain specialist
combined = registry.compose("base_assistant", "customer_support")
```

#### Contains

- The PromptRegistry implementation (complete, production-ready)
- Semantic versioning strategy for prompts (MAJOR/MINOR/PATCH)
- Composition patterns (base + specialist layers)
- ConversationAgent with history windowing
- History management strategies (fixed window, token budget, summarize)
- Unit testing prompts without calling an LLM
- A/B testing and hot-reload for production

#### Practice Examples

**[examples_1_4.py](examples_1_4.py)** provides 6 working demonstrations:

1. **ChatPromptTemplate vs f-strings** - Why the abstraction matters
2. **PromptRegistry** - Build, register, get, inspect
3. **Versioning and deprecation** - Full lifecycle in practice
4. **Composition** - Two-layer and three-layer prompt composition
5. **ConversationAgent** - Multi-turn with MessagesPlaceholder and history windowing
6. **Prompt unit testing** - Structural tests that run without any API call

---

### WP-1.5: Output Parsing for System Integration

**[WP-1.5-Output-Parsing-for-System-Integration.md](WP-1.5-Output-Parsing-for-System-Integration.md)** answers: *"How do I turn model text into reliable typed data?"*

#### The Problem

Production systems need typed outputs, not loosely formatted text. If the model returns malformed JSON, missing fields, or inconsistent totals, the integration boundary breaks.

#### The Pattern

- Define a strict Pydantic schema as the contract.
- Prefer native structured output from the model when available.
- Repair close-but-invalid output with `OutputFixingParser`.
- Retry with the validation error using `RetryWithErrorOutputParser`.
- Escalate the remaining failures to human review.

#### Why It Matters

- The downstream system receives a typed object instead of a string blob.
- Validation happens at the boundary instead of inside business logic.
- Recovery is explicit and bounded.
- Schema drift becomes visible instead of silently corrupting data.

#### Repository Use Case

This pattern is designed for invoice extraction, document ingestion, and any system integration that depends on reliable structured output.

---

**[LANGCHAIN_ECOSYSTEM_MAP.md](LANGCHAIN_ECOSYSTEM_MAP.md)** maps the entire LangChain ecosystem:

**Core Layers:**
- **langchain-core** - Runnables, prompts, LLMs (foundation)
- **langchain-community** - 200+ integrations (vector stores, tools, LLMs)
- **LangGraph** - Stateful workflows, agents, loops
- **LangServe** - REST API generation and deployment
- **LangSmith** - Observability, evaluation, experimentation

**Includes:**
- Component responsibilities
- When to use each
- Integration patterns
- Architecture diagrams
- Deployment strategies

---

## Technical Architecture

### System Design Principles

#### 1. Composition Over Configuration

Don't configure a "chain" object. **Compose** simple units:

```python
# Good: Simple, composable units
prompt = ChatPromptTemplate.from_template("...")
model = ChatOpenAI(model="gpt-4")
output = StrOutputParser()

chain = prompt | model | output  # Declarative composition
```

```python
# Avoid: Monolithic, hard to extend
chain = LLMChain(
    llm=model,
    prompt=prompt,
    # ... 20 more parameters
)
```

#### 2. Async by Default

All Runnables support async natively:

```python
# Single request, async
result = await chain.ainvoke({"input": "..."})

# Multiple requests, async + parallel
results = await asyncio.gather(*[
    chain.ainvoke({"input": item})
    for item in items
])
```

#### 3. Observability Everywhere

```python
from langchain.callbacks import StdOutCallbackHandler

# Every invoke automatically traces
result = chain.invoke(
    {"input": "..."},
    config={"callbacks": [StdOutCallbackHandler()]}
)
```

#### 4. Performance Tiers

Choose execution mode based on requirements:

| Mode | Use Case | Characteristic |
|------|----------|-----------------|
| `invoke()` | Single requests, <1s needed | Simple, blocking |
| `batch()` | Data processing, throughput | Parallel, respects rate limits |
| `stream()` | User-facing UIs | Fast first token |
| `ainvoke()` | Web servers, high concurrency | Non-blocking, scalable |

---

## Implementation Patterns

### Pattern 1: Sequential Composition

```python
# Simple pipe: input → A → B → C → output
chain = component_a | component_b | component_c

result = chain.invoke(input_data)
```

### Pattern 2: Parallel Processing

```python
from langchain_core.runnables import RunnableParallel

parallel = RunnableParallel(
    analysis=summarizer,      # Branch 1
    keywords=extractor,       # Branch 2
    sentiment=classifier,     # Branch 3
)

# All three execute in parallel
result = parallel.invoke(document)
# → {"analysis": "...", "keywords": [...], "sentiment": "..."}
```

### Pattern 3: Conditional Routing

```python
from langchain_core.runnables import RunnableBranch

router = RunnableBranch(
    (is_math_question, math_solver),
    (is_code_question, code_solver),
    general_solver,  # default
)

result = router.invoke({"question": "..."})
```

### Pattern 4: Streaming for Real-Time

```python
# Stream tokens as they arrive (lower perceived latency)
for chunk in chain.stream({"input": "..."}):
    print(chunk.content, end="", flush=True)
```

### Pattern 5: Production Observability

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGSMITH_API_KEY"] = "your-key"

# All subsequent invocations automatically trace to LangSmith
result = chain.invoke({"input": "..."})
# → Visible in LangSmith dashboard with full execution trace
```

---

## Learning Path

### Level 1: Foundations (2 hours)

**Goal:** Know which pattern to use

1. Read [README (this file)](#overview)
2. Read [ADR-1.2](#adr-12-chain-abstractions) - 30 min
3. Run `python examples_1_2.py` - 30 min
4. Review recommendation for your use case

**Outcome:** Confident choosing between approaches

### Level 2: Understanding (4 hours)

**Goal:** Understand how LangChain works

1. Read [LANGCHAIN_ECOSYSTEM_MAP.md](#langchain-ecosystem)
2. Read [WP-1.3](#wp-13-runnable-protocol) - Parts 1-5
3. Run `python examples_1_3.py` - All examples
4. Review [examples_1_3.py code](#examples)

**Outcome:** Can build custom Runnables, optimize for performance

### Level 3: Prompt Mastery (2 hours)

**Goal:** Manage prompts as production engineering artifacts

1. Read [WP-1.4](#wp-14-prompt-engineering-as-code)
2. Run `python examples_1_4.py` - All 6 examples
3. Build a PromptRegistry for your project
4. Write structural unit tests for your prompts

**Outcome:** Versioned, composable, testable prompts for any agent

### Level 4: Full Production (4 hours)

**Goal:** Build complete production AI systems

1. Finish [WP-1.3](#wp-13-runnable-protocol) - Parts 6-12
2. Build custom Runnable for your domain
3. Compose with other components
4. Set up observability with LangSmith
5. Deploy with LangServe

**Outcome:** Ready to build enterprise AI systems

---

## Setup & Configuration

### Prerequisites

- Python 3.9+
- OpenAI API key (for ChatOpenAI)
- Optional: LangSmith API key (for production)

### Installation

```bash
# Required
pip install langchain langchain-core langchain-openai

# Recommended for production
pip install langserve langsmith
```

### Enable Production Observability

```bash
# Set environment variables
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT="my-project-name"
export LANGSMITH_API_KEY="your-api-key"

# Now run your code - everything traces to LangSmith
python my_chain.py
```

### Deploy as REST API

```python
# api.py
from fastapi import FastAPI
from langserve import add_routes

app = FastAPI()
add_routes(app, my_chain, path="/chain")

# Run: uvicorn api:app --reload
# Then: curl -X POST http://localhost:8000/chain/invoke \
#       -H "Content-Type: application/json" \
#       -d '{"input": "..."}'
```

---

## Repository Contents

| Document | Type | Purpose | When to Read |
|----------|------|---------|--------------|
| [AGENTMAP.md](AGENTMAP.md) | Navigation | Visual map, learning paths, cross-references | When lost or starting |
| [ADR-1.2-Hello-World-Three-Ways.md](ADR-1.2-Hello-World-Three-Ways.md) | Decision Record | Chain abstraction comparison | Before building anything |
| [examples_1_2.py](examples_1_2.py) | Code | Working implementations of 3 approaches | After reading ADR-1.2 |
| [WP-1.3-The-Runnable-Protocol.md](WP-1.3-The-Runnable-Protocol.md) | Deep Dive | How Runnables work, patterns, optimization | To understand architecture |
| [examples_1_3.py](examples_1_3.py) | Code | 6 Runnable protocol demonstrations | After reading WP-1.3 |
| [WP-1.4-Prompt-Engineering-as-Code.md](WP-1.4-Prompt-Engineering-as-Code.md) | Design Pattern | PromptRegistry: versioning, composition, multi-turn | For production prompt management |
| [examples_1_4.py](examples_1_4.py) | Code | 6 PromptRegistry demos with unit tests | After reading WP-1.4 |
| [WP-1.5-Output-Parsing-for-System-Integration.md](WP-1.5-Output-Parsing-for-System-Integration.md) | Design Pattern | Structured output, parser repair, retry strategy | For typed downstream integrations |
| [LANGCHAIN_ECOSYSTEM_MAP.md](LANGCHAIN_ECOSYSTEM_MAP.md) | Reference | Complete LangChain stack | For component decisions |
| [README.md](README.md) | Overview | This file | Starting point |

---

## Key Takeaways

### Design Insights

1. **Runnables are the core abstraction** - Everything in LangChain is a Runnable with invoke/batch/stream/ainvoke
2. **Composition is power** - Combine simple units to build complexity
3. **Observability is essential** - Trace every execution in production
4. **Performance matters** - Choose execution mode based on use case
5. **Async is native** - All Runnables support async without extra work

### Architectural Patterns

1. **Chains are DAGs, not sequences** - Understand them as graphs of connected components
2. **Separate concerns** - One Runnable = one responsibility
3. **Compose declaratively** - Use pipe operator for readability
4. **Optimize per tier** - invoke() for single, batch() for throughput, stream() for UX
5. **Monitor everything** - LangSmith integration is automatic

### Production Best Practices

1. **Default to RunnableSequence + LCEL** - For 95% of new code
2. **Always enable LangSmith** - Non-negotiable for debugging
3. **Use batch() for N items** - Never loop with invoke()
4. **Stream for interactive UX** - Lower perceived latency
5. **Error handling at boundaries** - Don't silently fail
6. **Version every prompt** - Register with name, version, and description
7. **Test prompt structure** - Unit test templates before integration testing behavior

---

## Questions & References

### Common Questions

**Which pattern should I use?**
→ See [ADR-1.2](#adr-12-chain-abstractions) decision matrix

**How do I build a custom component?**
→ See [WP-1.3](#wp-13-runnable-protocol) Part 5 + examples_1_3.py Example 2

**How do I optimize for throughput?**
→ See [WP-1.3](#wp-13-runnable-protocol) Part 7 + examples_1_3.py Example 6

**How do I deploy to production?**
→ See [LANGCHAIN_ECOSYSTEM_MAP.md](#langchain-ecosystem) LangServe section

**How do I manage prompts across a team?**
→ See [WP-1.4](#wp-14-prompt-engineering-as-code) PromptRegistry pattern

**How do I build a multi-turn conversational agent?**
→ See [WP-1.4](#wp-14-prompt-engineering-as-code) Part 6 + examples_1_4.py Example 5

**How do I parse model output safely?**
→ See [WP-1.5](#wp-15-output-parsing-for-system-integration) parser recovery strategy

**I'm lost, where do I start?**
→ See [AGENTMAP.md](AGENTMAP.md)

### External References

- **LangChain Docs:** https://python.langchain.com
- **LangSmith:** https://smith.langchain.com
- **LangGraph:** https://langchain-ai.github.io/langgraph
- **LangServe:** https://github.com/langchain-ai/langserve

---

## Next Steps

1. **Pick your starting point** using [AGENTMAP.md](AGENTMAP.md)
2. **Read the relevant ADR or deep dive**
3. **Run the examples** and experiment
4. **Build something real** with your use case
5. **Enable observability** from day one
6. **Deploy to production** with confidence

---

**Version:** 1.0 | **Status:** Production Ready | **Last Updated:** 2024
