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

## 💻 Working Examples

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
