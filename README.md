# ai-architecture-blueprints

**Systems-first engineering for production-ready, agentic AI.**

A repository of Architecture Decision Records (ADRs), design patterns, and evaluation frameworks for building scalable, reliable enterprise AI systems. These blueprints combine LangChain ecosystem components with real-world implementation patterns and trade-off analysis.

---

## 🎯 Core Principles

- **Observability**: Measurable systems with full tracing and monitoring (LangSmith integration)
- **Defensive Design**: Graceful recovery through error handling, retries, and fallbacks
- **Trade-off Analysis**: Explicit evaluation of latency, cost, accuracy, and flexibility
- **HITL**: Strategic human-in-the-loop decision points for safety and control
- **Composability**: Modular, reusable components that scale from prototypes to production

---

## 📚 Documentation Structure

### Ecosystem & Framework Guides

#### [LangChain Ecosystem Map](LANGCHAIN_ECOSYSTEM_MAP.md)
Comprehensive guide covering the full LangChain stack:
- **langchain-core** - Foundation layer with core abstractions (Runnable, BaseLanguageModel, Tool, etc.)
- **langchain-community** - Integration hub with 200+ integrations (LLMs, vector stores, tools)
- **LangGraph** - Orchestration engine for stateful, agentic workflows with loops and HITL
- **LangServe** - Deployment layer for REST API generation and scaling
- **LangSmith** - Observability and evaluation platform for monitoring and quality assurance

Includes:
- Component responsibilities and when to use each
- Integration patterns and decision matrices
- Architecture diagrams and data flow visualizations
- Production deployment strategies

---

## 🏗️ Architecture Decision Records (ADRs)

### ADR-1.2: Chain Types - When to Use Direct LLM, SimpleSequentialChain, or RunnableSequence/LCEL

**Status**: Accepted  
**Work Product**: 1.2 - "Hello World" Three Ways  

Comprehensive comparison and practical guidance for choosing the right chain abstraction:

#### Problem Context
As LLM applications grow from single prompts to multi-step workflows, developers must decide how to orchestrate chains of operations. Each approach has different trade-offs in traceability, verbosity, flexibility, and production readiness.

#### Three Approaches Evaluated

| Approach | Best For | Key Trade-offs |
|----------|----------|-----------------|
| **Direct LLM Call** | Quick experiments, learning, single-step tasks | Manual control but no abstraction, requires custom logging for observability |
| **SimpleSequentialChain** | Legacy code, simple linear pipelines | Basic chain abstraction but string-only, linear flow, deprecated |
| **RunnableSequence + LCEL** | Production systems, team projects, complex workflows | Full composability, automatic LangSmith integration, supports streaming/batching |

#### Comparison Dimensions

The ADR provides detailed analysis across 8 dimensions:
1. **Traceability** - How visible is execution (manual vs automatic logging)
2. **Verbosity** - How much code required for implementation
3. **Flexibility** - Ability to add branching, error handling, parallel execution
4. **Debugging** - Tools and ease of troubleshooting
5. **Performance** - Optimization opportunities (batching, streaming, caching)
6. **LangSmith Integration** - Observability capabilities
7. **LangServe Deployment** - REST API generation support
8. **Production Readiness** - Suitability for enterprise systems

#### Key Recommendation

**Default to RunnableSequence + LCEL for all new production work:**
- ✅ Declarative composition via pipe operator (`prompt | llm | output_parser`)
- ✅ Automatic LangSmith tracing and monitoring
- ✅ Native LangServe REST API support
- ✅ Built-in streaming, batching, async, caching
- ✅ Full type safety and component introspection
- ✅ Composable with LangGraph for agentic workflows

**Use Direct LLM Calls for:**
- Quick prototyping and exploration
- Jupyter notebook experiments
- Learning LLM fundamentals

**Do NOT use SimpleSequentialChain for new code:**
- Deprecated in favor of RunnableSequence
- Only maintain existing legacy implementations

#### Real-World Scenarios

1. **Production Document Summarizer (Team Project)**
   - Multi-step: Load → Extract → Summarize → Format
   - Requires monitoring and REST API deployment
   - **Recommendation**: RunnableSequence + LCEL

2. **Solo Notebook Experimentation**
   - Quick iteration on prompts
   - No production requirements
   - **Recommendation**: Direct LLM Call

3. **Legacy SimpleSequentialChain Migration**
   - Existing codebase with LLMChain
   - Need to add conditional logic
   - **Recommendation**: Migrate to RunnableSequence

#### Learning Path

1. **Week 1**: Direct LLM calls (ChatOpenAI, invoke())
2. **Week 2**: Runnables basics (prompt | llm composition)
3. **Week 3**: Advanced patterns (streaming, batching, callbacks)
4. **Week 4**: Production (LangServe deployment + LangSmith monitoring)

**Full Documentation**: See [ADR-1.2-Hello-World-Three-Ways.md](ADR-1.2-Hello-World-Three-Ways.md)

---

## � Work Product 1.3: The `Runnable` Protocol - Deep Dive into the Engine

**Status**: Complete  
**Work Product**: 1.3 - Deep Dive: Understanding the Foundation  

While ADR-1.2 teaches you how to USE chains, WP-1.3 teaches you how chains WORK.

### The Core Insight

```
A chain is not a special object—it's a directed acyclic graph (DAG) 
of Runnables connected via the pipe operator.

[Input] → [Runnable A] → [Runnable B] → [Runnable C] → [Output]

Every Runnable supports FOUR execution modes:
  • invoke()  - Single, synchronous
  • batch()   - Multiple inputs, parallel
  • stream()  - Single, streaming chunks  
  • ainvoke() - Single, asynchronous

This unified interface means ANY Runnable composes with ANY other.
```

### What You'll Learn

1. **The Runnable Protocol** - The interface beneath LCEL
   - All four methods and their semantics
   - Why they exist and when to use each
   - How they compose together

2. **Execution Modes Deep Dive**
   - `invoke()` - Blocking, simple, synchronous
   - `batch()` - Parallel execution, rate-aware, efficient
   - `stream()` - Real-time output, token-by-token
   - `ainvoke()` - Non-blocking, async/await, high concurrency

3. **Composition as a Graph**
   - How pipes create DAGs
   - Parallel processing with RunnableParallel
   - Conditional routing with RunnableBranch
   - Composition semantics and how they work

4. **Architecture Diagrams**
   - Simple sequential chains
   - Parallel processing patterns
   - Conditional routing patterns
   - Complete execution models

5. **Implementation Patterns**
   - Building custom Runnables
   - Understanding the contract
   - Performance optimization
   - Error handling and retries

6. **Production Patterns**
   - Caching and memoization
   - Fallbacks and resilience
   - Full execution tracing
   - LangSmith integration

### Key Differences: ADR-1.2 vs WP-1.3

| Aspect | ADR-1.2 | WP-1.3 |
|--------|---------|--------|
| **Focus** | Which pattern to use | How the engine works |
| **Audience** | Practitioners | Architects & Advanced Users |
| **Goal** | Make good design decisions | Understand the architecture |
| **Content** | Comparison, scenarios, examples | Deep dive, diagrams, implementation |
| **Outcomes** | Know when to use RunnableSequence | Know why RunnableSequence works |

### Practical Applications

**Use WP-1.3 to:**
- ✅ Build custom Runnables for your domain
- ✅ Optimize performance with batch() and stream()
- ✅ Debug execution flow through complex DAGs
- ✅ Design systems that scale from prototypes to production
- ✅ Understand why certain patterns work
- ✅ Train your team on LangChain architecture

### Example: Understanding the Difference

**ADR-1.2 tells you:**
> "Use RunnableSequence + LCEL for production systems."

**WP-1.3 shows you:**
> Here's what happens when you call `invoke()`:
> 1. Input passed to Runnable A
> 2. A.invoke() returns intermediate value
> 3. Intermediate passed to Runnable B
> 4. B.invoke() returns output
> 5. LangSmith callback logs the entire path
>
> Here's what happens with `batch([inputs])`:
> 1. Inputs split into chunks
> 2. All chunks sent to A (parallel)
> 3. Results passed to B (parallel)
> 4. Final outputs collected in order
> 5. Full DAG is traced in LangSmith
>
> And here's how to build your own Runnable...

### Document Contents

**WP-1.3-The-Runnable-Protocol.md** (12 KB, comprehensive)

1. Executive Summary
2. What is a Runnable? (the protocol)
3. The Four Execution Modes (detailed)
4. Composition as a Graph
5. Architecture Diagrams (ASCII and conceptual)
6. Implementation Deep Dive
7. Execution Traces and Observability
8. Performance Characteristics
9. Design Patterns (branching, fallbacks, retries, caching)
10. Production Patterns (real-world chatbot example)
11. Key Takeaways
12. Quick Reference

**examples_1_3.py** (6 practical demonstrations)

1. The Four Execution Modes
2. Building Custom Runnables
3. Composition as a DAG
4. Execution Tracing
5. Conditional Routing
6. Batch Performance Comparison

### Quick Start with WP-1.3

```bash
# Read the protocol explanation
cat WP-1.3-The-Runnable-Protocol.md

# Run practical examples
python examples_1_3.py

# Try building your own Runnable
# (See examples_1_3.py for template)
```

**Full Documentation**: See [WP-1.3-The-Runnable-Protocol.md](WP-1.3-The-Runnable-Protocol.md)

---

## �💻 Working Examples

### examples_1_2.py

Complete, runnable implementations demonstrating all three chain approaches:

**Core Functions**:
- `approach_1_direct_llm()` - Manual orchestration with explicit logging
- `approach_2_simple_sequential_chain()` - LLMChain pattern (deprecated)
- `approach_3_runnable_sequence_lcel()` - Production standard with full data passing

**Advanced Demonstrations**:
- `approach_3_streaming()` - Token-by-token streaming for real-time UX
- `approach_3_batching()` - Efficient multi-input processing
- `approach_3_with_callbacks()` - Custom logging via callback system
- `print_comparison_summary()` - Visual side-by-side comparison

**Features**:
- LangSmith tracing setup (environment variable configuration)
- Callback system examples for custom observability
- RunnableParallel for intermediate data passing
- Error handling patterns

**Usage**:
```bash
python examples_1_2.py  # Run all demonstrations
```

The script shows:
1. Generated poetry as output (demonstrates LLM capability)
2. Observability metrics for each approach
3. Comparison summary table
4. Recommendations for production use

---

## 🔧 Technical Setup

### Prerequisites
- Python 3.9+
- OpenAI API key (for ChatOpenAI model)
- Optional: LangSmith API key (for production monitoring)

### Installation

```bash
# Install LangChain ecosystem
pip install langchain langchain-openai langchain-core

# Optional: For LangServe REST API deployment
pip install langserve

# Optional: For production monitoring
pip install langsmith
```

### Configuration

#### Enable LangSmith Tracing (Optional but Recommended)

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT="my-project"
export LANGSMITH_API_KEY="your-api-key"
```

Then any RunnableSequence chain automatically traces to LangSmith:
```python
# All steps are automatically logged to LangSmith dashboard
result = chain.invoke({"input": "..."})
```

#### Deploy with LangServe

```python
from fastapi import FastAPI
from langserve import add_routes

app = FastAPI()
add_routes(app, my_chain, path="/my-chain")

# Automatically exposes:
# POST /my-chain/invoke
# POST /my-chain/batch
# GET /my-chain/stream
# GET /my-chain/openapi.json
```

---

## 📊 Key Files

| File | Purpose | Size |
|------|---------|------|
| [ADR-1.2-Hello-World-Three-Ways.md](ADR-1.2-Hello-World-Three-Ways.md) | Complete chain type analysis with examples, scenarios, decision flow | 17 KB, 495 lines |
| [examples_1_2.py](examples_1_2.py) | Working implementations of all 3 approaches with advanced patterns | 16.5 KB, 441 lines |
| [WP-1.3-The-Runnable-Protocol.md](WP-1.3-The-Runnable-Protocol.md) | Deep dive into Runnable interface, execution modes, composition, architecture | 12 KB, comprehensive |
| [examples_1_3.py](examples_1_3.py) | Practical demonstrations of Runnable protocol with custom implementations | 6 KB, 6 examples |
| [LANGCHAIN_ECOSYSTEM_MAP.md](LANGCHAIN_ECOSYSTEM_MAP.md) | Complete LangChain stack documentation and integration patterns | - |
| [README.md](README.md) | This file - project overview and guide | - |

---

## 🎓 Learning Outcomes

After studying these blueprints, you'll understand:

✅ **Chain Abstraction Levels**
- Tradeoffs between explicit Python control and declarative composition
- When to use each pattern based on project phase and complexity
- How to evaluate new frameworks using the same criteria

✅ **LangChain Ecosystem**
- Roles of langchain-core, langchain-community, LangGraph, LangServe, LangSmith
- How components integrate (core abstractions → integrations → orchestration → deployment → observability)
- Production patterns for each layer

✅ **Production-Ready AI Systems**
- Automatic tracing with LangSmith for debugging and quality assurance
- REST API deployment with LangServe for scaling
- Callback systems for custom observability
- Streaming and batching for performance optimization

✅ **Real-World Decision Making**
- How to analyze trade-offs explicitly (latency, cost, accuracy, flexibility)
- Scenario-based recommendations for different contexts
- Migration paths from prototypes to production

---

## 🚀 Quick Start

### 1. Run Examples

```bash
python examples_1_2.py
```

Output shows:
- Poem generation from LLM
- Summarization of poem
- Observability comparison across approaches
- Production recommendation

### 2. Review ADR

```bash
cat ADR-1.2-Hello-World-Three-Ways.md
```

Key sections:
- Comparison matrix (8 dimensions)
- Practical examples for each approach
- Real-world scenarios
- Decision flow diagram
- Learning path

### 3. Study Ecosystem

```bash
cat LANGCHAIN_ECOSYSTEM_MAP.md
```

Deep dive into:
- Component responsibilities
- Integration patterns
- Architecture diagrams
- When to use each component

---

## 📖 Next Steps

1. **Understand the Trade-offs**: Review ADR-1.2 comparison matrix
2. **See Working Code**: Run examples_1_2.py
3. **Learn the Ecosystem**: Study LANGCHAIN_ECOSYSTEM_MAP.md
4. **Apply to Your Project**:
   - Use RunnableSequence + LCEL for new code
   - Enable LangSmith for production monitoring
   - Deploy with LangServe for REST APIs
5. **Build Complex Workflows**: Combine with LangGraph for agentic loops

---

## 📝 Contributing

These blueprints are living documentation. As you apply these patterns:
- Document lessons learned
- Share edge cases and solutions
- Propose improvements to ADRs
- Add new patterns as they emerge

---

## 📄 License & Attribution

This repository documents best practices for production-ready, agentic AI systems using the LangChain ecosystem.

**Key References**:
- LangChain Documentation: https://python.langchain.com
- LangSmith: https://smith.langchain.com
- LangGraph: https://langchain-ai.github.io/langgraph
- LangServe: https://github.com/langchain-ai/langserve
