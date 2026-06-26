# AI Architecture Blueprints

[![CI/CD Pipeline](https://github.com/pristley/ai-architecture-blueprints/workflows/AI%20Architecture%20Blueprints%20CI%2FCD/badge.svg?branch=main)](https://github.com/pristley/ai-architecture-blueprints/actions)
[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](VERSION)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-production-brightgreen.svg)](#)

**Build production AI systems with proven architectural patterns.** This guide provides decision records, design patterns, and working implementations for building scalable, observable, and maintainable AI applications using LangChain.

---

## What This Guide Covers

Use this guide to:
- **Choose the right pattern** for your AI workflow (30 minutes)
- **Build observable systems** with complete tracing and debugging capabilities (2 hours)
- **Implement multi-agent architectures** using event-driven choreography (2 hours)
- **Deploy at scale** with production-ready patterns, memory systems, and state management (varies)

**Status**: 1.1.0 | Python 3.9+ | MIT License | 191 tests passing | [Release history](CHANGELOG.md)

---

## Get Started

**New here?** Choose your path:

| Your Goal | Start Here | Time |
|-----------|-----------|------|
| I need to pick a pattern for my workflow | [ADR-1.2: Chain Abstractions](ADR-1.2-Hello-World-Three-Ways.md) | 30 min |
| I want working code examples | [examples_1_2.py](examples_1_2.py) - then [AGENTMAP.md](AGENTMAP.md) | 30 min |
| I need to understand LangChain architecture | [WP-1.3: Runnable Protocol](WP-1.3-The-Runnable-Protocol.md) | 2 hours |
| I need structured output from LLMs | [WP-1.5: Output Parsing](WP-1.5-Output-Parsing-for-System-Integration.md) | 45 min |
| I want multi-agent systems | [ADR-2.1: Choreography](ADR-2.1-Choreography-Event-Driven-Agility-for-Emergent-Workflows.md) | 2 hours |
| I need deterministic orchestrated workflows | [WP-2.3: Orchestration Pattern](WP-2.3-Orchestration-Pattern.md) + [ADR-2.2](ADR-2.2-Orchestration-Centralized-Control.md) | 3.5 hours |
| I need emergent multi-agent workflows | [WP-2.4: Choreography Pattern](WP-2.4-Choreography-Pattern.md) + [ADR-2.1](ADR-2.1-Choreography-Event-Driven-Agility-for-Emergent-Workflows.md) | 3.5 hours |
| I need to manage state in agents | [WP-2.2: State Management](WP-2.2-State-Management-in-Single-Agent-Loop.md) + [research_assistant_state_machine.py](research_assistant_state_machine.py) | 1.5 hours |
| I need help debugging | [WP-1.7: Tracing with LangSmith](WP-1.7-Introduction-to-Tracing-with-LangSmith.md) | 60 min |
| I want a visual map | [AGENTMAP: Knowledge Graph](AGENTMAP.md) | 15 min |

---

## Design Principles

We follow these five principles in all patterns and implementations:

**1. Observability First** — Instrument every component. Trace execution end-to-end. Monitor performance at each stage.

**2. Composability by Design** — Build small, single-purpose units with standardized interfaces. Compose from simple to complex.

**3. Explicit Trade-offs** — Evaluate every pattern across latency, cost, accuracy, and flexibility. Document your choices.

**4. Defensive Implementation** — Handle errors at component boundaries. Provide retries and fallbacks. Fail loudly, never silently.

**5. Production Readiness** — Design for scale from day one. Use async/await. Support batching and streaming.

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
- � **Deep dive** → [WP-1.3](#wp-13-runnable-protocol) - How it works
- 📈 **Typed extraction (45 min)** → [WP-1.5](#wp-15-output-parsing-for-system-integration) - Parse and recover structured output
- 🤖 **Model selection (45 min)** → [WP-1.6](#wp-16-choosing-an-llm---a-decision-matrix) - Pick the best model with a weighted matrix
- 🔍 **Observability (60 min)** → [WP-1.7](#wp-17-tracing-with-langsmith) - Debug with LangSmith tracing
- 💾 **Memory systems (90 min)** → [WP-2.1](#wp-21-short-term-vs-long-term-memory) - Build scalable conversational memory
- 🏭 **Agent state (1 hour)** → [WP-2.2](#wp-22-state-management-in-single-agent-loop) - Prevent infinite loops
- 🐝 **Multi-agent choreography (3.5 hours)** → [WP-2.4](#wp-24-choreography-pattern---the-hive-mind-agent) - Event-driven autonomous agents with feedback loops
- ⚙️ **Orchestrated workflows (3.5 hours)** → [WP-2.3](#wp-23-orchestration-pattern---the-controller-agent) - Build deterministic orchestrators
- 🎯 **Orchestration architecture** → [ADR-2.2](#adr-22-orchestration---centralized-control-for-deterministic-workflows) - Decision framework
- 📦 **Production setup** → See [Setup & Configuration](#setup--configuration)

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

### WP-1.6: Choosing an LLM - A Decision Matrix

**[WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md](WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md)** answers: *"How do I choose the right model for a production architecture?"*

#### The Problem

Model selection is a systems decision, not just a benchmark result. Architects must balance token economics, latency, context needs, tool-calling reliability, and multimodal support. The 2026 LLM landscape includes diverse options with different trade-offs.

#### The Pattern

- Compare 7+ candidate models (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, Mixtral, Gemini 3.5, ChatGPT 5.5, Claude Opus 4.8) on shared operational axes.
- Use explicit weighting aligned to workload priorities.
- Run sensitivity analysis to see when the recommendation changes.
- Record the outcome as a short ADR with tiered routing strategy and production guardrails.

#### Repository Use Case

This work product provides a comprehensive decision matrix comparing 7 models across architect-critical dimensions (cost, latency, context, tool-calling reliability, multimodal capability). The 2026 update identifies **Claude Opus 4.8 as the primary recommendation** for high-volume support, delivering:
- 50%+ cost savings vs GPT-4o (2.5x cheaper input tokens)
- Industry-leading context window (300k) for complex case reasoning
- Strong tool-calling reliability (4.6/5.0)
- Tiered multi-model routing for latency-sensitive and budget-optimized paths

Includes ADR with production guardrails, monitoring strategy, and sensitivity analysis showing when competing models become optimal.

---

### WP-1.7: Tracing with LangSmith

**[WP-1.7-Introduction-to-Tracing-with-LangSmith.md](WP-1.7-Introduction-to-Tracing-with-LangSmith.md)** answers: *"How do I debug and optimize my LLM chains?"*

#### The Problem

LLM systems are opaque. When a chain is slow or expensive, you don't know if the problem is:
- Network latency to the LLM provider?
- LLM inference time?
- Token overhead in prompts?
- Parsing overhead in output processing?
- A custom Runnable doing expensive computation?

#### The Pattern

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGSMITH_API_KEY"] = "your-key"

# Every invoke() automatically creates a trace
result = chain.invoke({"input": "..."})
# → View in LangSmith dashboard with full execution breakdown
```

Traces capture:
- **Input/Output** at each step
- **Token counts** (prompt and completion tokens)
- **Timing** (TTFT, generation time, total latency)
- **Cost** calculated from tokens and model
- **Metadata** for production context
- **Errors** with full context for debugging

#### Repository Use Case

This work product provides:
- Observability-first debugging strategy
- Step-by-step LangSmith trace interpretation
- Token usage and cost analysis patterns
- Real-world debugging scenarios:
  * High latency identification and fix
  * Cost reduction through trace analysis
  * Parsing failure debugging
- Production tracing best practices:
  * 100% tracing in development
  * 10% sampling + 100% errors in production
  * Custom metadata for production context
- ADR: Adaptive tracing strategy for production
- Integration with WP-1.4 (prompt optimization) and WP-1.5 (output parsing)

#### Practice Examples

**[examples_1_7.py](examples_1_7.py)** provides 4 practical demonstrations:
1. **Basic Tracing Setup** - Enable LangSmith with one environment variable
2. **Understanding Trace Structure** - What information is captured and how to interpret it
3. **Comparing Chains with Traces** - A/B testing using real trace data
4. **Debugging with Traces** - Finding and fixing failures using trace analysis

Each example includes:
- How to enable tracing
- How to read trace output
- How to extract metrics (tokens, latency, cost)
- How to use traces for optimization decisions

---

### WP-2.1: Short-Term vs. Long-Term Memory

**[WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md](WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md)** answers: *"How do I build conversational AI systems that scale?"*

#### The Problem

Conversational systems face a fundamental tension:
- Keep all messages → token count grows unbounded → exceeds context window and costs explode
- Discard history → bot forgets preferences, context, and reasoning
- Store everything in summaries → lose granularity and recent context

#### The Solution: Dual-Memory Architecture

**Separate memory into two complementary streams:**

| Memory Type | Strategy | Characteristics |
|------------|----------|-----------------|
| **Short-Term** | Last N messages in buffer | Bounded tokens, immediate context, per-session |
| **Long-Term** | Extracted facts in vector store | Semantic meaning, unbounded but compressed, persistent |

```python
from examples_2_1 import DualMemoryChatbot

# Initialize with both memory systems
bot = DualMemoryChatbot(model="gpt-4o", buffer_k=10)

# Chat updates both memories automatically
response = bot.chat("I'm an engineer from Toronto who loves hiking")

# Short-term: remembers this message
# Long-term: extracts and stores: [Toronto, engineer, hiking]
```

#### Repository Use Case

This work product provides:
- Complete dual-memory pattern architecture
- Short-term memory: ConversationBufferWindowMemory (bounded sliding window)
- Long-term memory: ConversationSummaryMemory + vector store integration
- Separation of concerns for observability
- Implementation checklist (5 phases: planning, implementation, integration, observability, optimization)
- Troubleshooting FAQ for common issues
- Production patterns: monitoring memory health, resetting sessions, exporting state
- Integration with WP-1.5 (structured fact extraction) and WP-1.7 (observability)

#### Practice Examples

**[examples_2_1.py](examples_2_1.py)** provides 3 complete demonstrations:
1. **Dual-Memory Chatbot Architecture** - Full conversation with both memory systems in action
2. **Memory Separation & Token Bounding** - Side-by-side comparison showing predictable cost
3. **Observability and Debugging** - Inspect memory state, collect statistics, monitor health

Each example includes:
- Memory initialization and configuration
- Conversation simulation with fact extraction
- Memory inspection and statistics
- Production monitoring patterns

---

### WP-2.2: State Management in Single-Agent Loop

**[WP-2.2-State-Management-in-Single-Agent-Loop.md](WP-2.2-State-Management-in-Single-Agent-Loop.md)** answers: *"How do I build agents that don't infinite loop?"*

#### The Problem

Agent loops are powerful but chaotic:
- You don't know what state the agent is in
- Self-loops happen without visibility (planning → planning → planning...)
- Same tool gets called repeatedly (search same query 6x)
- You hit rate limits and burn tokens before catching it

#### The Solution: Explicit State Machine

```python
state = ResearchState(query="...", state="IDLE")
state.state_history = ["IDLE", "PLANNING", "SEARCHING", ...]
state.record_action("SYNTHESIZING", "action_taken")  # Validates + transitions
```

**With a state machine you get:**
- Clear transitions (IDLE → PLANNING → SEARCHING → SYNTHESIZING → CITING)
- Loop detection (step count, state repeats, alternating patterns)
- State inspection for debugging
- Predictable execution flow

#### Repository Use Case

This work product provides:
- State machine architecture with 5 phases
- State transition diagram showing all valid paths
- Pydantic state model with validation
- Loop guard with 4 detection mechanisms
- ResearchAssistant class showing state-aware tool calls
- Integration patterns with LangGraph
- Production observability (checkpointing, metrics, tracing)

#### Practice Examples

**[examples_2_2.py](examples_2_2.py)** provides 3 complete demonstrations:
1. **Happy Path** - Successful research workflow with state transitions
2. **Loop Detection** - Four different infinite loop scenarios and how guard catches them
3. **State Inspection** - Debugging with state snapshots at each step

Each example includes:
- State object creation and manipulation
- Tool calls with state transitions
- Loop guard evaluation
- State history tracking
- Observability patterns

---

### ADR-2.1: Choreography - Event-Driven Agility for Emergent Workflows

**[ADR-2.1-Choreography-Event-Driven-Agility-for-Emergent-Workflows.md](ADR-2.1-Choreography-Event-Driven-Agility-for-Emergent-Workflows.md)** answers: *"How do I coordinate multiple agents without a central orchestrator?"*

#### The Problem

Traditional orchestration centralizes control: a master coordinator tells agents what to do. This creates:
- Tight coupling (agents depend on orchestrator)
- Bottleneck scaling (orchestrator throughput limits all agents)
- Cascading failures (orchestrator down = system down)
- Reduced autonomy (agents can't react independently)

#### The Solution: Choreography with Event-Driven Architecture

```
┌──────────────┐
│   Searcher   │ ──→ [data-fetched event]
└──────────────┘
        │
        ↓
┌──────────────────────┐
│  Event Bus (Pub/Sub) │
└──────────────────────┘
        ↑
        │ [report-synthesized event]
┌──────────────┐
│    Drafter   │ ──→ [revision-required feedback]
└──────────────┘
        ↑
        │ [quality assessment]
┌──────────────┐
│    Critic    │ ←── Feedback Loop: Quality Homeostasis
└──────────────┘
```

**With choreography you get:**
- **Loose coupling** - Agents interact via event contracts, not direct calls
- **Independent scaling** - Add agents without modifying others
- **Resilience** - Agent failure remains isolated
- **Emergent behavior** - Workflows compose dynamically from agent subscriptions
- **Self-organizing** - Feedback loops enable system adaptation without centralized control

#### Architecture Patterns

The ADR includes systems thinking analysis:

- **Feedback Loops**: The Critic agent implements negative feedback (like a thermostat) that drives the system toward quality equilibrium
- **Second-Order Effects**: Analyzes how decoupling affects observability, latency, and consistency
- **Emergent Workflows**: Shows how multi-agent patterns emerge from local event subscriptions
- **Resilience Through Isolation**: Demonstrates how cascading failures become contained failures

#### Choreography vs. Orchestration Comparison Matrix

| Dimension | Orchestration | Choreography |
|-----------|---------------|--------------|
| **Coupling** | High (agents → orchestrator) | Low (agents → events) |
| **Scaling** | Limited by orchestrator | Scales with pub/sub |
| **Resilience** | Cascading (orchestrator failure) | Isolated (agent-level) |
| **Workflow Composition** | Static (orchestrator owns it) | Dynamic (subscriptions enable new patterns) |
| **Observability** | Centralized (orchestrator view) | Distributed (event audit trail + correlation IDs) |
| **Consistency Model** | Strong (orchestrator enforces) | Eventual (agents converge) |
| **Operational Burden** | Lower (single control point) | Higher (distributed debugging) |

#### Implementation Patterns

The ADR provides:
- Event payload design with correlation IDs for distributed tracing
- Agent state management for tracking workflow progress
- Bounded feedback loops (max revision limits) preventing infinite loops
- Dead-letter queue handling for repeated failures
- Monitoring strategy using event flow dashboards

#### Repository Implementation

**[choreography_hive_mind.py](choreography_hive_mind.py)** is a complete, production-ready Hive Mind system:

```python
# Initialize event bus
bus = EventBus()

# Create autonomous agents that subscribe to events
searcher = WebSearcher(bus, "web-searcher")
drafter = Drafter(bus, "drafter")
critic = Critic(bus, "critic")

# Start agents (they register subscriptions)
await searcher.start()  # Subscribes to "search-requested"
await drafter.start()   # Subscribes to "data-fetched", "revision-required"
await critic.start()    # Subscribes to "report-synthesized"

# Trigger workflow by publishing an event
await bus.publish(SearchRequested(query="climate change"))

# Agents react autonomously; no orchestrator tells them what to do
```

**Key Components:**

1. **EventBus** - Asynchronous pub/sub infrastructure
   - Publish/subscribe with asyncio
   - Event history tracking (audit trail)
   - Statistics for monitoring

2. **Event Types** (Pydantic models)
   - `SearchRequested`, `DataFetched`
   - `ReportSynthesized`, `ReviewCompleted`
   - `RevisionRequired`, `RevisionAbandoned`
   - All include correlation_id for distributed tracing

3. **Autonomous Agents**
   - `WebSearcher` - Fetches data independently
   - `Drafter` - Synthesizes reports and handles revisions
   - `Critic` - Assesses quality and provides feedback
   - Each manages own state; no external control

4. **Feedback Loops**
   - Critic publishes `RevisionRequired` when quality is low
   - Drafter subscribes and re-drafts with feedback
   - System reaches equilibrium through repeated cycles
   - Max revision limits prevent infinite loops

#### Complete Test Coverage

**[tests/test_choreography_hive_mind.py](tests/test_choreography_hive_mind.py)** provides comprehensive testing:

- **Event tests** - Pydantic validation, immutability, serialization
- **EventBus tests** - Publishing, subscribing, event history
- **Agent tests** - Independent behavior, event publishing
- **Integration tests** - Multi-agent workflows, feedback loops
- **Resilience tests** - Error isolation, max revision limits
- **Observability tests** - Statistics and audit trails

Coverage includes:
- Happy path workflows (Search → Draft → Approve)
- Revision loops (Draft → Feedback → Revise → Approve)
- Concurrent workflows (multiple queries simultaneously)
- Correlation ID propagation (trace entire workflow)
- Error isolation (handler failures don't cascade)

#### Use Cases

**Ideal for:**
- Multi-stage report generation (search, synthesis, review, refinement)
- Complex workflows requiring feedback loops
- Systems needing independent agent scaling
- Scenarios where failure isolation is critical
- Production systems demanding high observability

**Example workflow:**
```
Query → Search Web → Fetch Data → Draft Report → Review Quality
                                          ↓
                          Feedback Loop (if below quality threshold)
                                          ↓
                              Re-fetch data or re-draft
                                          ↓
                          Quality threshold met → Finalize
```

#### Learning Path

To master choreography-based patterns:

1. Read ADR-2.1 for architectural concepts (1 hour)
2. Study choreography_hive_mind.py implementation (1 hour)
3. Run the tests and observe agent interactions (30 min)
4. Modify the pattern for your use case (1 hour)

See [AGENTMAP.md](AGENTMAP.md#path-8-multi-agent-choreography-for-emergent-workflows) for the complete "Multi-Agent Choreography" learning path.

---

### ADR-2.2: Orchestration - Centralized Control for Deterministic Workflows

**[ADR-2.2-Orchestration-Centralized-Control.md](ADR-2.2-Orchestration-Centralized-Control.md)** answers: *"How do I ensure predictable, fully-auditable multi-step workflows?"*

#### The Problem

When you need deterministic execution with complete auditability, choreography's distributed autonomy creates challenges:
- Hard to predict execution order (agents react independently)
- Difficult to enforce constraints (no centralized validation)
- Complex debugging (workflow emerges from event subscriptions)
- Weak guarantees (eventual consistency, not strong guarantees)

#### The Solution: Orchestration with Centralized Control

```
Controller (Centralized Decision-Maker)
│
├─→ [Step 1: Plan]
│   ├─→ Validate output (≥3 steps)
│   ├─→ Decision: CONTINUE or RETRY
│   └─→ Record: timing, evaluation, decision
│
├─→ [Step 2: Fetch Data]
│   ├─→ Validate output (≥8 sources)
│   ├─→ Decision: CONTINUE or RETRY
│   └─→ Record: complete audit
│
└─→ [Step 3-6: Continue with complete control and visibility]
    ├─→ Analyze, Synthesize, Cite, Format
    ├─→ Each step evaluated before next
    └─→ Full execution trace available
```

**With orchestration you get:**
- **Predictability** - Exact execution order known upfront
- **Complete Audit Trail** - Every decision recorded with timing
- **Strong Guarantees** - Each step validated before progression
- **Reproducibility** - Same input always produces same output
- **Easier Debugging** - Clear causality chain from start to finish

#### Architecture Patterns

The ADR includes a comprehensive comparison:

- **Sequential Pipeline** - Linear progression through steps
- **Conditional Branching** - Controller decides next step based on evaluation
- **Retry with Backoff** - Graceful failure handling with exponential backoff
- **Checkpoint & Restore** - Workflow recovery from failures

#### Orchestration vs. Choreography Comparison Matrix

| Dimension | Orchestration | Choreography |
|-----------|---------------|--------------|
| **Control** | Centralized (controller) | Distributed (agents) |
| **Predictability** | High (order known) | Low (emergent) |
| **Auditability** | Complete (full trace) | Distributed (events) |
| **Flexibility** | Lower (rigid workflows) | Higher (adaptive) |
| **Fault Tolerance** | Single point of failure | Resilient isolation |
| **Time to Debug** | Fast (clear causality) | Slow (trace across agents) |
| **Scalability** | Limited by controller | Scales with agents |
| **Operational Burden** | Lower (centralized) | Higher (distributed) |

#### Implementation Patterns

The ADR provides:
- Tool registration pattern (register_tool, register_evaluator)
- Step execution with retry logic and exponential backoff
- Evaluation gates ensuring output quality before progression
- Complete state tracking with timing instrumentation
- Decision tracking (CONTINUE, RETRY, BRANCH, SKIP, ABORT)
- JSON serializable audit trails for observability

#### Repository Implementation

**[controller_orchestration_agent.py](controller_orchestration_agent.py)** is a complete, production-ready orchestration system:

```python
# Create controller
orchestrator = ReportOrchestrator()

# Register tools and evaluators (for report generation workflow)
orchestrator.register_tool(StepName.PLANNING, plan_tool)
orchestrator.register_evaluator(StepName.PLANNING, evaluate_plan)
# ... (register remaining 5 steps)

# Execute deterministic workflow
report = await orchestrator.orchestrate("Write AI trends report")

# Complete audit trail available
print(orchestrator.state.step_history)  # All steps with timings
print(json.dumps(audit_trail))          # Full workflow trace
```

**Key Components:**

1. **Controller Base Class** - Abstract orchestration controller
   - Tool and evaluator registration
   - Step execution with retry logic
   - State management and history tracking

2. **OrchestrationState** - Complete workflow state
   - Data at each stage (plan, fetched_data, facts, reports)
   - Step history with timing and evaluation
   - Error tracking and statistics

3. **ReportOrchestrator** - Concrete implementation
   - 6-step report generation: Plan → Fetch → Analyze → Synthesize → Cite → Format
   - Each step has specific evaluator (≥3 steps, ≥8 sources, etc)
   - Retry logic with exponential backoff (configurable per step)

4. **Evaluation Gates**
   - plan_tool: Requires ≥3 steps
   - fetch_tool: Requires ≥8 sources with title+content
   - analyze_tool: Requires ≥20 facts with source
   - synthesize_tool: Requires ≥1000 words, ≥5 paragraphs
   - cite_tool: Requires ≥10 citations
   - format_tool: Requires headers + proper termination

#### Complete Test Coverage

**[tests/test_controller_orchestration.py](tests/test_controller_orchestration.py)** provides comprehensive testing:

- **Evaluation tests** (13) - Each evaluator function
- **State management tests** (5) - State tracking and history
- **Tool execution tests** (6) - Individual tool behavior
- **Step execution tests** (3) - Single step with retry
- **Workflow tests** (4) - Complete orchestration
- **Characteristic tests** (4) - Determinism, sequencing, audit trails
- **Error handling tests** (1) - Error continuation
- **Pattern comparison tests** (3) - Orchestration vs choreography

Coverage includes:
- Happy path workflows (all 6 steps succeed)
- Step evaluation (valid vs invalid output)
- State recording (timing, decision, result tracking)
- Deterministic verification (multiple runs identical)
- Audit trail generation (JSON serialization)

#### Use Cases

**Ideal for:**
- Report generation workflows (multi-step, validated at each stage)
- Data pipelines with quality gates
- Compliance-heavy workflows (full audit trail required)
- Reproducible experiments (deterministic execution)
- Systems where predictability matters more than adaptability

**Example workflow:**
```
Define Plan → Fetch Data (validate) → Extract Facts (validate) 
  → Draft Report (validate) → Add Citations (validate) → Format → Deliver
     ↑ Each step is evaluated before proceeding
     ↑ Complete timing and decision recorded
     ↑ Reproducible (same input = same output)
```

#### Learning Path

To master orchestration patterns:

1. Read ADR-2.2 for architectural concepts (1 hour)
2. Study controller_orchestration_agent.py implementation (1 hour)
3. Run the tests and observe orchestration in action (30 min)
4. Adapt the pattern for your workflow (15 min)

See [AGENTMAP.md](AGENTMAP.md#path-9-orchestrated-deterministic-workflows) for the complete "Orchestrated Deterministic Workflows" learning path.

---

### WP-2.3: Orchestration Pattern - The "Controller" Agent

**[WP-2.3-Orchestration-Pattern.md](WP-2.3-Orchestration-Pattern.md)** teaches you: *"How do I implement deterministic, auditable workflows with evaluation gates?"*

**WP-2.3 is a hands-on guide** to implementing the orchestration pattern. While ADR-2.2 explains *why* orchestration is valuable, WP-2.3 teaches you *how to build* robust orchestrators for your specific workflows.

#### What You'll Learn

- **Understand the Controller Pattern**: Centralized decision-making for multi-step workflows
- **Build Evaluation Gates**: Validate step outputs before progression
- **Implement Retry Logic**: Gracefully handle transient failures
- **Design for Observability**: Complete audit trails with JSON serialization
- **Create Extensible Orchestrators**: Base Controller class for domain-specific workflows

#### Key Concepts

```python
# 1. Define steps and evaluation gates
class StepName(str, Enum):
    PLANNING = "PLANNING"
    FETCHING = "FETCHING"
    ANALYZING = "ANALYZING"
    SYNTHESIZING = "SYNTHESIZING"

# 2. Create evaluation functions (quality gates)
def evaluate_plan(plan: Optional[List[str]]) -> Tuple[bool, str]:
    if not plan or len(plan) < 3:
        return False, f"Plan has {len(plan)} steps, need ≥3"
    return True, f"Plan accepted: {len(plan)} steps"

# 3. Register tools and evaluators in Controller
orchestrator = ReportOrchestrator()
orchestrator.register_tool(StepName.PLANNING, plan_tool)
orchestrator.register_evaluator(StepName.PLANNING, evaluate_plan)

# 4. Execute workflow with complete tracking
report = await orchestrator.orchestrate("Write a report on AI trends")

# 5. Get audit trail
audit_trail = orchestrator.get_audit_trail()
# Includes: steps executed, timings, evaluations, decisions, errors
```

#### The Complete Pattern

```
Controller (Centralized Decision-Maker)
│
├─→ [Step 1: Plan]
│   ├─→ Execute plan_tool()
│   ├─→ Evaluate output (≥3 steps)
│   ├─→ Record timing, decision, result
│   └─→ CONTINUE to Step 2 OR RETRY
│
├─→ [Step 2: Fetch Data]
│   ├─→ Execute fetch_tool()
│   ├─→ Evaluate output (≥8 sources with title+content)
│   ├─→ Record timing, decision, result
│   └─→ CONTINUE to Step 3 OR RETRY
│
├─→ [Step 3+: Continue with evaluation and tracking]
│
└─→ Return final result + complete audit trail
    (workflow_id, timings, decisions, errors, JSON serialization)
```

#### Implementation Example: 6-Step Report Orchestrator

The included [controller_orchestration_agent.py](controller_orchestration_agent.py) demonstrates:

- **Plan** (controller generates 6-step plan)
- **Fetch** (controller executes search for 9 data sources)
- **Analyze** (controller extracts 22 facts from sources)
- **Synthesize** (controller drafts 1250+ word report)
- **Cite** (controller adds 15+ citations)
- **Format** (controller finalizes with References section)

Each step is evaluated before the next begins. If evaluation fails, the step is retried with exponential backoff.

#### Complete Test Coverage

**[tests/test_controller_orchestration.py](tests/test_controller_orchestration.py)** includes 41 tests:

- **Evaluation tests** (13) - All evaluator functions
- **State management tests** (5) - State tracking and history
- **Tool execution tests** (6) - Individual tool behavior
- **Step execution tests** (3) - Retry logic and evaluation
- **Workflow tests** (4) - Complete orchestration
- **Characteristics tests** (4) - Determinism, sequencing, audit trails
- **Pattern tests** (3) - Orchestration vs choreography

#### Learning Path (3.5 hours)

1. **Understand ADR-2.2** (1 hour) - Know the architectural principles
2. **Study WP-2.3 implementation** (1 hour) - Learn the concrete patterns
3. **Review controller_orchestration_agent.py** (45 min) - See complete code
4. **Run tests and observe** (30 min) - Trace through execution
5. **Build your own orchestrator** (1 hour) - Adapt for your domain

#### When to Use WP-2.3 Patterns

**Use orchestration when you need:**
- ✅ Predictable, reproducible workflows
- ✅ Validation gates at each step
- ✅ Complete audit trails for compliance
- ✅ Deterministic execution (same input → same output)
- ✅ Clear debugging (causality chain)

**Use choreography instead when:**
- ❌ You need emergent behavior from agent interactions
- ❌ You have 1000s of independent agents
- ❌ External events trigger workflows
- ❌ Decoupling matters more than predictability

---

### WP-2.4: Choreography Pattern - The "Hive Mind" Agent

**[WP-2.4-Choreography-Pattern.md](WP-2.4-Choreography-Pattern.md)** teaches you: *"How do I build event-driven multi-agent systems with emergent workflows?"*

**WP-2.4 is a hands-on guide** to implementing the choreography pattern. While ADR-2.1 explains *why* choreography is valuable, WP-2.4 teaches you *how to build* autonomous agents that collaborate via events.

#### What You'll Learn

- **Event-Driven Architecture**: Design with pub/sub messaging
- **Build Autonomous Agents**: Agents make independent decisions
- **Implement Feedback Loops**: System self-regulates toward goals
- **Trace Distributed Workflows**: Correlation IDs across agents
- **Handle Eventual Consistency**: Accept delays for flexibility

#### Key Concepts

```python
# 1. Define domain events
class SearchRequested(Event):
    query: str
    max_results: int

class DataFetched(Event):
    query: str
    results: List[Dict]

class RevisionRequired(Event):
    quality_score: float
    feedback: str
    revision_count: int

# 2. Create EventBus for pub/sub
bus = EventBus()

# 3. Define autonomous agents
class WebSearcher(Agent):
    async def start(self):
        self.bus.subscribe("search-requested", self.on_search_requested)
    
    async def on_search_requested(self, event):
        # Fetch data independently
        results = await fetch_from_web(event.query)
        # Publish results
        await self.publish_event(DataFetched(...))

# 4. Agents coordinate via events (not direct calls!)
searcher = WebSearcher(bus, "searcher")
drafter = Drafter(bus, "drafter")
critic = Critic(bus, "critic")

await searcher.start()
await drafter.start()
await critic.start()

# 5. Trigger workflow
trigger = SearchRequested(query="AI trends", source_agent="user")
await bus.publish(trigger)  # Workflow emerges!
```

#### The Complete Pattern

```
WebSearcher (Autonomous Agent 1)
│
├─→ Subscribes to: "search-requested"
├─→ When event arrives:
│   ├─→ Fetches data independently
│   └─→ Publishes "data-fetched"
│
Drafter (Autonomous Agent 2)
│
├─→ Subscribes to: "data-fetched" + "revision-required"
├─→ When data-fetched:
│   ├─→ Drafts report
│   └─→ Publishes "report-synthesized"
├─→ When revision-required:
│   ├─→ Improves draft with feedback
│   └─→ Publishes "report-synthesized" (revised)
│
Critic (Autonomous Agent 3) - Feedback Loop
│
├─→ Subscribes to: "report-synthesized"
├─→ When report arrives:
│   ├─→ Evaluates quality
│   ├─→ Quality ≥ threshold?
│   │   ├─→ YES: Publish "report-finalized" ✅
│   │   └─→ NO: Publish "revision-required" (feedback loop!)
│   └─→ Max revisions exceeded?
│       └─→ Publish "revision-abandoned" ❌

EventBus (Shared Infrastructure)
│
├─→ Manages subscriptions
├─→ Routes events to handlers
├─→ Maintains audit trail
└─→ Tracks correlation_ids
```

#### Implementation Example: Report Generation Hive Mind

The included [choreography_hive_mind.py](choreography_hive_mind.py) demonstrates:

- **WebSearcher Agent** - Fetches data when requested
- **Drafter Agent** - Synthesizes reports with feedback awareness
- **Critic Agent** - Reviews quality and provides feedback
- **Feedback Loop** - Drafter responds to Critic feedback
- **Correlation Tracking** - All events share workflow ID

Workflow emerges from event interactions: SearchRequested → DataFetched → ReportSynthesized → ReviewCompleted → [RevisionRequired | ReportFinalized]

#### Complete Test Coverage

**[tests/test_choreography_hive_mind.py](tests/test_choreography_hive_mind.py)** includes comprehensive tests:

- **Event validation tests** - Pydantic serialization and immutability
- **EventBus tests** - Pub/sub mechanics and history
- **Individual agent tests** - WebSearcher, Drafter, Critic behavior
- **Multi-agent workflow tests** - Complete workflows with feedback
- **Feedback loop tests** - Revision iteration and max revision handling
- **Resilience tests** - Error isolation between agents
- **Observability tests** - Event audit trails and statistics

#### Learning Path (3.5 hours)

1. **Understand ADR-2.1** (1 hour) - Know the architectural principles
2. **Study WP-2.4 implementation** (1 hour) - Learn the concrete patterns
3. **Review choreography_hive_mind.py** (45 min) - See complete code
4. **Run tests and observe** (30 min) - Trace through async execution
5. **Build your own agents** (1 hour) - Create domain-specific choreography

#### When to Use WP-2.4 Patterns

**Use choreography when you need:**
- ✅ Emergent behavior from autonomous agents
- ✅ Loosely coupled agents (don't depend on each other)
- ✅ Feedback loops and self-regulation
- ✅ Scaling to 100s of independent agents
- ✅ Handling external events dynamically

**Use orchestration instead when:**
- ❌ You need predictable workflows
- ❌ You require complete audit trails
- ❌ Regulatory compliance demands explicit control
- ❌ Debugging causality must be obvious
- ❌ Few agents (< 10) with clear sequence

#### Choreography vs Orchestration: Decision Matrix

| Factor | Choreography | Orchestration |
|--------|--------------|---------------|
| **Control** | Distributed (agents autonomous) | Centralized (Controller directs) |
| **Complexity** | Low until you have 100s agents | Low until you have 10+ steps |
| **Observability** | Event audit trail | Workflow audit trail |
| **Debugging** | Harder (distributed) | Easier (central) |
| **Scaling** | Scales to 1000s agents | Bottleneck at Controller |
| **Consistency** | Eventual | Strong |
| **Coupling** | Loose (event-based) | Tight (direct calls) |
| **Best For** | Emergent workflows | Deterministic workflows |

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

### Level 4: Production Observability (2 hours)

**Goal:** Debug and optimize with complete visibility

1. Read [WP-1.7](#wp-17-tracing-with-langsmith)
2. Run `python examples_1_7.py` - All 4 examples
3. Set up LangSmith API key and connect your chains
4. Capture traces and analyze token usage/latency
5. Use traces to compare and optimize components

**Outcome:** Data-driven optimization and confident debugging

### Level 5: Full Production (4 hours)

**Goal:** Build complete production AI systems

1. Finish [WP-1.3](#wp-13-runnable-protocol) - Parts 6-12
2. Build custom Runnable for your domain
3. Compose with other components
4. Set up adaptive sampling strategy (10% random + 100% errors)
5. Deploy with LangServe and production observability

**Outcome:** Ready to build enterprise AI systems with production monitoring

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
| [WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md](WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md) | Design Pattern | Model decision matrix, 2026 landscape, routing strategy | For production model selection |
| [WP-1.7-Introduction-to-Tracing-with-LangSmith.md](WP-1.7-Introduction-to-Tracing-with-LangSmith.md) | Design Pattern | Observability, tracing, debugging, optimization | For production monitoring and debugging |
| [examples_1_7.py](examples_1_7.py) | Code | 4 LangSmith tracing demonstrations | After reading WP-1.7 |
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
