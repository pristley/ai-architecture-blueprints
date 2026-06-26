# 🗺️ AI Architecture Blueprints - Agent Map

**Complete Knowledge Graph of the Learning Material**

This document visualizes how all work products, ADRs, and examples are connected and organized.

---

## 📊 Work Product Hierarchy

```mermaid
graph TB
    START["🎯 START HERE<br/>README.md"] 
    ECOSYSTEM["📚 Ecosystem<br/>LANGCHAIN_ECOSYSTEM_MAP.md"]
    ADR12["🏗️ ADR-1.2<br/>Hello World Three Ways"]
    EX12["💻 examples_1_2.py<br/>Working Implementations"]
    ADR21["🏗️ ADR-2.1<br/>Choreography: Event-Driven Agility"]
    CHORE["💻 choreography_hive_mind.py<br/>Hive Mind Implementation"]
    TEST_CHORE["🧪 test_choreography_hive_mind.py<br/>Choreography Tests"]
    WP13["🔬 WP-1.3<br/>Runnable Protocol"]
    EX13["💻 examples_1_3.py<br/>Practical Demonstrations"]
    WP14["📋 WP-1.4<br/>Prompt Engineering as Code"]
    EX14["💻 examples_1_4.py<br/>PromptRegistry Demos"]
    WP15["📈 WP-1.5<br/>Output Parsing for System Integration"]
    WP16["🤖 WP-1.6<br/>Choosing an LLM"]
    WP17["🔍 WP-1.7<br/>Tracing with LangSmith"]
    EX17["💻 examples_1_7.py<br/>Tracing Examples"]
    WP21["💾 WP-2.1<br/>Short-Term vs Long-Term Memory"]
    EX21["💻 examples_2_1.py<br/>Dual-Memory Chatbot Examples"]
    WP22["🤖 WP-2.2<br/>State Management in Agent Loop"]
    EX22["💻 examples_2_2.py<br/>State Machine Agent Examples"]
    AGENTMAP["🗺️ AGENTMAP.md<br/>This Document"]
    
    START -->|Learn about| ECOSYSTEM
    START -->|Choose approach| ADR12
    ADR12 -->|See code| EX12
    START -->|Deep dive| WP13
    WP13 -->|Practice| EX13
    WP13 -->|Builds on| ADR12
    WP13 -->|Enables| WP14
    WP14 -->|Enables| WP15
    WP15 -->|Informs| WP16
    WP14 -->|Practice| EX14
    WP14 -->|Builds on| ADR12
    WP16 -->|Optimizes with| WP17
    WP14 -->|Debugs with| WP17
    WP15 -->|Debugs with| WP17
    WP17 -->|See code| EX17
    WP16 -->|Enables| WP21
    WP15 -->|Extracts facts for| WP21
    WP21 -->|See code| EX21
    WP21 -->|Observes with| WP17
    WP22 -->|See code| EX22
    WP22 -->|Prevents loops in| WP17
    WP22 -->|Coordinates multiple| WP15
    ADR21 -->|See code| CHORE
    CHORE -->|Tested by| TEST_CHORE
    ADR21 -->|Foundation for multi-agent| WP22
    AGENTMAP -->|Shows relationships| START
    AGENTMAP -->|Shows relationships| ADR12
    AGENTMAP -->|Shows relationships| ADR21
    AGENTMAP -->|Shows relationships| WP13
    AGENTMAP -->|Shows relationships| WP14
    AGENTMAP -->|Shows relationships| WP15
    AGENTMAP -->|Shows relationships| WP16
    AGENTMAP -->|Shows relationships| WP17
    AGENTMAP -->|Shows relationships| WP21
    AGENTMAP -->|Shows relationships| WP22
    
    style START fill:#4CAF50,stroke:#2E7D32,color:#fff
    style ECOSYSTEM fill:#2196F3,stroke:#1565C0,color:#fff
    style ADR12 fill:#FF9800,stroke:#E65100,color:#fff
    style EX12 fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style ADR21 fill:#FF9800,stroke:#E65100,color:#fff
    style CHORE fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style TEST_CHORE fill:#4CAF50,stroke:#2E7D32,color:#fff
    style WP13 fill:#FF9800,stroke:#E65100,color:#fff
    style EX13 fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style WP14 fill:#FF9800,stroke:#E65100,color:#fff
    style EX14 fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style WP15 fill:#FF9800,stroke:#E65100,color:#fff
    style WP16 fill:#FF9800,stroke:#E65100,color:#fff
    style WP17 fill:#FF9800,stroke:#E65100,color:#fff
    style EX17 fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style WP21 fill:#FF9800,stroke:#E65100,color:#fff
    style EX21 fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style WP22 fill:#FF9800,stroke:#E65100,color:#fff
    style EX22 fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style AGENTMAP fill:#F44336,stroke:#C62828,color:#fff
```

---

## 📚 Document Overview

### Core Documents

| Document | Type | Purpose | Lines | Status |
|----------|------|---------|-------|--------|
| [README.md](README.md) | 📖 Guide | Project overview and navigation | ~800 | ✅ |
| [LANGCHAIN_ECOSYSTEM_MAP.md](LANGCHAIN_ECOSYSTEM_MAP.md) | 📚 Reference | Complete LangChain stack documentation | ~1200 | ✅ |
| [ADR-1.2-Hello-World-Three-Ways.md](ADR-1.2-Hello-World-Three-Ways.md) | 🏗️ Architecture Decision | Chain abstraction comparison and decision flow | ~500 | ✅ |
| [WP-1.3-The-Runnable-Protocol.md](WP-1.3-The-Runnable-Protocol.md) | 🔬 Deep Dive | Runnable protocol explained in 12 parts | ~1100 | ✅ |
| [WP-1.4-Prompt-Engineering-as-Code.md](WP-1.4-Prompt-Engineering-as-Code.md) | 📋 Design Pattern | PromptRegistry pattern: versioning, composition, multi-turn | ~900 | ✅ |
| [WP-1.5-Output-Parsing-for-System-Integration.md](WP-1.5-Output-Parsing-for-System-Integration.md) | 📈 Design Pattern | Structured output, parser repair, and retry strategy | ~300 | ✅ |
| [WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md](WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md) | 🤖 Design Pattern | LLM decision matrix and ADR for production model selection | ~220 | ✅ |
| [WP-1.7-Introduction-to-Tracing-with-LangSmith.md](WP-1.7-Introduction-to-Tracing-with-LangSmith.md) | 🔍 Design Pattern | Observability-first debugging with LangSmith traces | ~740 | ✅ |
| [WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md](WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md) | 💾 Design Pattern | Dual-memory architecture for scalable conversational systems | ~600 | ✅ |
| [WP-2.2-State-Management-in-Single-Agent-Loop.md](WP-2.2-State-Management-in-Single-Agent-Loop.md) | 🤖 Design Pattern | State machine for agent loops with infinite loop prevention | ~850 | ✅ |

### Code Examples

| Document | Type | Purpose | Lines | Status |
|----------|------|---------|-------|--------|
| [examples_1_2.py](examples_1_2.py) | 💻 Code | 3 chain approaches with advanced patterns | ~900 | ✅ |
| [examples_1_3.py](examples_1_3.py) | 💻 Code | 6 Runnable protocol examples with deep comments | ~1500 | ✅ |
| [examples_1_4.py](examples_1_4.py) | 💻 Code | 6 PromptRegistry demos: registry, versioning, composition, testing | ~600 | ✅ |
| [examples_1_7.py](examples_1_7.py) | 💻 Code | 4 LangSmith tracing examples with observability patterns | ~603 | ✅ |
| [examples_2_1.py](examples_2_1.py) | 💻 Code | 3 Dual-memory chatbot examples with fact extraction | ~750 | ✅ |
| [examples_2_2.py](examples_2_2.py) | 💻 Code | 3 State machine agent examples with loop detection | ~900 | ✅ |
| [choreography_hive_mind.py](choreography_hive_mind.py) | 💻 Code | Event-driven choreography pattern: EventBus, agents, feedback loops | ~1200 | ✅ |

### Test Examples

| Document | Type | Purpose | Lines | Status |
|----------|------|---------|-------|--------|
| [tests/test_choreography_hive_mind.py](tests/test_choreography_hive_mind.py) | 🧪 Tests | Comprehensive choreography pattern tests: events, bus, agents, workflows | ~800 | ✅ |

### Meta Documents

| Document | Type | Purpose |
|----------|------|---------|
| [AGENTMAP.md](AGENTMAP.md) | 🗺️ Map | This file - shows relationships and navigation |

---

## 🔗 Document Relationships

### ADR-1.2 Relationships

```
ADR-1.2: "Hello World" Three Ways
│
├─→ Depends on
│   └─ LANGCHAIN_ECOSYSTEM_MAP.md (context about LangChain components)
│
├─→ References
│   └─ README.md (overview)
│
├─→ Provides code examples to
│   └─ examples_1_2.py
│
└─→ Foundation for
    └─ WP-1.3 (teaches what approaches exist, WP-1.3 explains how they work)
```

### WP-1.3 Relationships

```
WP-1.3: The Runnable Protocol
│
├─→ Depends on
│   ├─ ADR-1.2 (understanding which approach to use)
│   └─ LANGCHAIN_ECOSYSTEM_MAP.md (context about components)
│
├─→ References
│   └─ README.md (overview)
│
├─→ Provides code examples to
│   └─ examples_1_3.py
│
└─→ Explains
    └─ How RunnableSequence (from ADR-1.2) actually works
```

### WP-1.4 Relationships

```
WP-1.4: Prompt Engineering as Code
│
├─→ Depends on
│   ├─ WP-1.3 (ChatPromptTemplate IS a Runnable - composition via pipe operator)
│   └─ ADR-1.2 (Prompts plug into LCEL chains - the chosen chain abstraction)
│
├─→ References
│   └─ README.md (overview)
│
├─→ Provides code examples to
│   └─ examples_1_4.py
│
└─→ Introduces patterns for
    ├─ PromptRegistry (versioned prompt management)
    ├─ MessagesPlaceholder (multi-turn conversation)
    ├─ Prompt composition (base + specialist)
    └─ Prompt unit testing (structure validation without LLM)
```

### WP-1.5 Relationships

```
WP-1.5: Output Parsing for System Integration
│
├─→ Depends on
│   ├─ WP-1.3 (structured parsing fits naturally into Runnable pipelines)
│   ├─ WP-1.4 (prompt outputs should be explicit contracts)
│   └─ ADR-1.2 (choose the right chain abstraction before adding parsing)
│
├─→ References
│   └─ README.md (overview)
│
├─→ Provides code examples to
│   └─ downstream invoice extraction and integration pipelines
│
└─→ Introduces patterns for
      ├─ Pydantic schema contracts
      ├─ Native structured model output
      ├─ OutputFixingParser repair
      └─ RetryWithErrorOutputParser retries
```

   ### WP-1.6 Relationships

   ```
   WP-1.6: Choosing an LLM - A Decision Matrix
   │
   ├─→ Depends on
   │   ├─ WP-1.5 (structured outputs and tool reliability are model-selection constraints)
   │   ├─ WP-1.4 (prompt strategy influences model cost and latency)
   │   └─ ADR-1.2 (orchestration architecture changes model requirements)
   │
   ├─→ References
   │   └─ README.md (overview)
   │
   └─→ Introduces patterns for
      ├─ Weighted model decision matrices
      ├─ Sensitivity analysis by workload priority
      ├─ ADR capture for model selection
      └─ Routed multi-model deployment strategy
   ```

   ### WP-1.7 Relationships

```
WP-1.7: Introduction to Tracing with LangSmith
│
├─→ Depends on
│   ├─ WP-1.3 (understanding Runnable chain structure)
│   ├─ WP-1.4 (traces show prompt optimization impact)
│   ├─ WP-1.5 (traces show parser performance and failures)
│   └─ WP-1.6 (traces compare model performance)
│
├─→ Enables optimization of
│   ├─ WP-1.4 (see prompt token impact on cost/latency)
│   ├─ WP-1.5 (debug parsing failures, measure overhead)
│   └─ WP-1.6 (measure real-world model performance)
│
├─→ References
│   ├─ README.md (overview)
│   ├─ LangSmith (https://smith.langchain.com)
│   └─ LangChain Tracing Docs
│
└─→ Introduces patterns for
   ├─ Automatic chain instrumentation
   ├─ Token-level observability
   ├─ Latency breakdown analysis
   ├─ Cost tracking per request
   ├─ A/B testing with trace comparison
   ├─ Adaptive production sampling (10% random + 100% errors)
   └─ ADR for tracing strategy
```

### WP-2.1 Relationships

```
WP-2.1: Short-Term vs. Long-Term Memory
│
├─→ Depends on
│   ├─ WP-1.3 (understanding Runnable composability for memory pipelines)
│   ├─ WP-1.5 (structured fact extraction for long-term storage)
│   ├─ WP-1.6 (choosing models that support streaming for memory operations)
│   └─ WP-1.7 (observing memory health, token usage, and performance)
│
├─→ Enables patterns for
│   ├─ Bounded token usage in multi-turn conversations
│   ├─ Persistent context across sessions
│   ├─ Semantic search over conversation history
│   └─ Production memory scaling
│
├─→ References
│   ├─ README.md (overview)
│   ├─ LANGCHAIN_ECOSYSTEM_MAP.md (vector store options)
│   └─ Production deployment patterns
│
└─→ Introduces patterns for
   ├─ Separation of concerns (short vs. long-term)
   ├─ Token bounding with sliding windows
   ├─ Semantic summarization and extraction
   ├─ Memory health monitoring
   ├─ Session lifecycle management
   ├─ Production vector store integration
   └─ Cost optimization through predictable token usage
```

### Examples Relationships

```
examples_1_2.py: Implementations of Three Approaches
├─→ Demonstrates
│   ├─ Direct LLM Call (Approach 1)
│   ├─ SimpleSequentialChain (Approach 2)
│   └─ RunnableSequence + LCEL (Approach 3)
│
└─→ Shows patterns like
    ├─ Streaming
    ├─ Batching
    ├─ Callbacks
    └─ Composition

examples_1_3.py: Runnable Protocol Deep Dive
├─→ Demonstrates
│   ├─ invoke() - Synchronous single
│   ├─ batch() - Parallel multiple
│   ├─ stream() - Incremental output
│   ├─ ainvoke() - Asynchronous single
│   ├─ Custom Runnables
│   ├─ DAG Composition
│   ├─ Execution Tracing
│   ├─ Conditional Routing
│   └─ Performance Optimization
│
└─→ Complements
    └─ WP-1.3-The-Runnable-Protocol.md (theory + practice)
```

examples_1_4.py: PromptRegistry Demonstrations
├─→ Demonstrates
│   ├─ PromptRegistry (named, versioned prompts)
│   ├─ Prompt composition (base + specialist)
│   ├─ Multi-turn conversations
│   ├─ Prompt unit testing
│   ├─ Chat history management
│   └─ Dynamic routing by prompt version
│
└─→ Shows patterns like
    ├─ Versioning
    ├─ Composition
    ├─ Testing
    └─ Observability
```

examples_1_7.py: LangSmith Tracing Demonstrations
├─→ Demonstrates
│   ├─ Enabling tracing with environment variables
│   ├─ Understanding trace structure and components
│   ├─ Comparing chains using trace metrics
│   ├─ Debugging failures through trace analysis
│   ├─ Token counting and cost calculation
│   └─ Latency breakdown (TTFT, generation time)
│
└─→ Shows patterns like
    ├─ Automatic instrumentation
    ├─ Metric extraction
    ├─ A/B testing with traces
    ├─ Production sampling strategy
    └─ Error debugging
```

examples_2_1.py: Dual-Memory Chatbot Demonstrations
├─→ Demonstrates
│   ├─ Short-term memory with bounded buffer (deque)
│   ├─ Long-term memory with semantic extraction
│   ├─ Dual-memory orchestration (DualMemoryChatbot)
│   ├─ Token usage patterns and cost bounding
│   ├─ Memory health monitoring and statistics
│   └─ Multi-turn conversations with fact extraction
│
└─→ Shows patterns like
    ├─ Separation of concerns
    ├─ Token awareness
    ├─ Semantic understanding
    ├─ Production monitoring
    ├─ Session management
    └─ Cost optimization
```

### WP-2.2 Relationships

```
WP-2.2: State Management in Single-Agent Loop
│
├─→ Depends on
│   ├─ WP-1.3 (understanding Runnable DAG composition for agent tools)
│   ├─ WP-1.5 (validating structured state transitions)
│   ├─ WP-1.6 (choosing models for agent decision-making)
│   └─ WP-1.7 (observing agent execution and debugging loops)
│
├─→ Prevents infinite loops in
│   ├─ Research agents (planning → searching → synthesis → citations)
│   ├─ Routing agents (condition → routing → action → loop back?)
│   ├─ Hierarchical agents (parent → delegated tasks → parent)
│   └─ Multi-step workflows
│
├─→ Coordinates patterns for
│   ├─ Tool calls with state validation
│   ├─ Transition guards (can_transition checks)
│   ├─ Loop detection (multiple mechanisms)
│   └─ State checkpointing (recovery)
│
├─→ References
│   ├─ README.md (overview)
│   ├─ LangGraph (graph-based agent execution)
│   └─ LangSmith (tracing agent execution)
│
└─→ Introduces patterns for
   ├─ Explicit state machines (5+ states)
   ├─ Typed transitions (valid paths only)
   ├─ Multi-mechanism loop detection (step count, repeats, alternating)
   ├─ State history tracking for debugging
   ├─ Tool call orchestration
   ├─ Session lifecycle management
   └─ Production agent observability
```

examples_2_2.py: State Machine Agent Demonstrations
├─→ Demonstrates
│   ├─ ResearchState Pydantic model with validation
│   ├─ State transition validation (can_transition)
│   ├─ Infinite loop detection (4 mechanisms)
│   ├─ LoopGuard class for comprehensive checking
│   ├─ ResearchAssistant with state-aware tools
│   ├─ Main agent loop with state management
│   └─ Happy path workflow (IDLE → PLANNING → SEARCHING → SYNTHESIZING → CITING)
│
└─→ Shows patterns like
    ├─ Pydantic models for state
    ├─ Explicit transitions
    ├─ Step budgets
    ├─ Tool-level state validation
    ├─ Loop detection
    ├─ State inspection for debugging
    └─ Production monitoring
```

### ADR-2.1 Relationships

```
ADR-2.1: Choreography: Event-Driven Agility for Emergent Workflows
│
├─→ Contrasts with
│   ├─ ADR-1.2 (orchestration vs. choreography approaches)
│   └─ WP-2.2 (centralized control vs. distributed agent autonomy)
│
├─→ Depends on
│   ├─ Systems thinking framework (feedback loops, emergent behavior)
│   ├─ Event-driven architecture patterns
│   └─ Asynchronous distributed systems theory
│
├─→ Provides code examples to
│   └─ choreography_hive_mind.py
│
├─→ Introduces patterns for
│   ├─ Event-driven pub/sub architecture
│   ├─ Autonomous agent design (no centralized control)
│   ├─ Feedback loops for system homeostasis
│   ├─ Second-order effects analysis
│   ├─ Eventual consistency vs. strong consistency tradeoffs
│   ├─ Observability through distributed tracing (correlation IDs)
│   ├─ Resilience through decoupling and isolation
│   └─ Emergent workflow composition
│
└─→ Enables multi-agent systems with
    ├─ Independent agent scaling
    ├─ Failure isolation (agent failure doesn't cascade)
    ├─ Dynamic workflow composition
    ├─ Self-organizing adaptation
    └─ Production-ready observability
```

### choreography_hive_mind.py: Event-Driven Hive Mind Implementation

```
choreography_hive_mind.py: Multi-Agent Report Generation via Choreography
│
├─→ Demonstrates
│   ├─ EventBus (pub/sub infrastructure with asyncio)
│   ├─ Event types (Pydantic models for validation)
│   ├─ Agent base class and autonomous behavior
│   ├─ WebSearcher agent (data fetching)
│   ├─ Drafter agent (synthesis with revision feedback)
│   ├─ Critic agent (quality assessment and homeostasis)
│   ├─ Feedback loops (Critic→Drafter→Searcher)
│   ├─ Correlation IDs for distributed tracing
│   └─ Event audit trails for observability
│
├─→ Implements patterns like
│   ├─ Loose coupling (agents interact via events, not direct calls)
│   ├─ Asynchronous event propagation (fire-and-forget semantics)
│   ├─ Error isolation (handler failures don't affect other subscribers)
│   ├─ Bounded feedback loops (max revision limits prevent infinite loops)
│   ├─ Event ordering and sequencing
│   ├─ Workflow state tracking without central orchestrator
│   └─ Distributed tracing with correlation IDs
│
├─→ Runs complete workflow
│   ├─ SearchRequested → DataFetched → ReportSynthesized
│   ├─ ReviewCompleted (approved) OR RevisionRequired (feedback loop)
│   ├─ Revision loop: RevisionRequired → ReportSynthesized → ReviewCompleted
│   └─ ReportFinalized or RevisionAbandoned (max revisions)
│
└─→ Complements
    ├─ ADR-2.1 (theory of choreography patterns)
    ├─ WP-2.2 (agent state management with events)
    └─ tests/test_choreography_hive_mind.py (comprehensive test coverage)
```

### tests/test_choreography_hive_mind.py: Choreography Test Suite

```
tests/test_choreography_hive_mind.py: Comprehensive Choreography Pattern Tests
│
├─→ Test Coverage
│   ├─ EventTypes (validation, serialization, immutability)
│   ├─ EventBus (pub/sub, subscribing, publishing, history)
│   ├─ WebSearcher (data fetching, event publishing)
│   ├─ Drafter (synthesis, revision handling, feedback integration)
│   ├─ Critic (quality assessment, approval logic, feedback generation)
│   ├─ Choreography workflow (happy path, revision loops, multi-query)
│   ├─ Resilience (error isolation, max revision limits)
│   └─ Observability (statistics, event tracking)
│
├─→ Test Categories
│   ├─ Unit Tests
│   │   ├─ Event creation and validation (Pydantic)
│   │   ├─ Event immutability and serialization
│   │   ├─ EventBus pub/sub mechanics
│   │   └─ Individual agent behavior
│   ├─ Integration Tests
│   │   ├─ Multi-agent workflow coordination
│   │   ├─ Feedback loop execution
│   │   ├─ Correlation ID propagation
│   │   └─ Concurrent workflow handling
│   ├─ Resilience Tests
│   │   ├─ Handler error isolation
│   │   └─ Max revision limit enforcement
│   └─ Observability Tests
│       ├─ Statistics tracking
│       └─ Event history recording
│
├─→ Example Test Scenarios
│   ├─ Complete workflow happy path (Search → Draft → Approve)
│   ├─ Workflow with revision loop (Search → Draft → Revise → Approve)
│   ├─ Multiple concurrent workflows
│   ├─ Correlation ID flow through entire workflow
│   └─ Handler failure isolation (error in one subscriber doesn't affect others)
│
└─→ Validates patterns like
    ├─ Agent autonomy (agents react to events independently)
    ├─ Choreography emergence (workflows emerge from agent interactions)
    ├─ Feedback loops (Critic signals drive Drafter re-work)
    ├─ Decoupling benefits (agents don't know each other)
    └─ System resilience (failures remain isolated)
```

---

## 🎓 Learning Paths

### Path 1: "Just Show Me What to Do" (2 hours)

```
1. README.md (15 min)
   ↓
2. ADR-1.2-Hello-World-Three-Ways.md (30 min)
   ↓
3. examples_1_2.py (30 min)
   ↓
4. Quick reference and build
```

**Outcome**: Know which chain abstraction to use in production

---

### Path 4: "Prompt Engineering for Production" (3 hours)

```
1. README.md (15 min)
   ↓
2. ADR-1.2 (know the chosen chain abstraction - 20 min)
   ↓
3. WP-1.4-Prompt-Engineering-as-Code.md (60 min)
   ↓
4. examples_1_4.py (all 6 examples - 45 min)
   ↓
5. Build PromptRegistry for your own project (30 min)
```

**Outcome**: Manage prompts as versioned, composable, testable code artifacts

---

### Path 5: "Typed Output for Production" (3 hours)

```
1. README.md (15 min)
   ↓
2. WP-1.5-Output-Parsing-for-System-Integration.md (45 min)
   ↓
3. Review the Pydantic schema and recovery flow (30 min)
   ↓
4. Apply the pattern to your own extraction task (60 min)
   ↓
5. Add validation metrics and a dead-letter path (30 min)
```

**Outcome**: Turn LLM text into reliable typed data for downstream systems

---

### Path 6: "Model Selection for Production" (2.5 hours)

```
1. README.md (15 min)
   ↓
2. WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md (60 min)
   ↓
3. Review weighted scoring and sensitivity analysis (30 min)
   ↓
4. Apply decision matrix to your use case (45 min)
```

**Outcome**: Make informed model selection decisions with architectural trade-offs and sensitivity analysis

---

### Path 7: "Debug and Optimize with Observability" (2 hours)

```
1. README.md (15 min)
   ↓
2. WP-1.7-Introduction-to-Tracing-with-LangSmith.md (45 min)
   ↓
3. examples_1_7.py (all 4 examples - 45 min)
   ↓
4. Set up LangSmith API key and trace your own chain (15 min)
```

**Outcome**: Use observability to debug failures and optimize cost/latency with real data

---

### Path 2: "I Want to Understand" (6 hours)

```
1. README.md (15 min)
   ↓
2. LANGCHAIN_ECOSYSTEM_MAP.md (45 min)
   ↓
3. ADR-1.2-Hello-World-Three-Ways.md (30 min)
   ↓
4. examples_1_2.py (30 min)
   ↓
5. WP-1.3-The-Runnable-Protocol.md (2 hours)
   ↓
6. examples_1_3.py (1 hour)
   ↓
7. Build own custom Runnable (30 min)
```

**Outcome**: Deep understanding of LangChain's core architecture

---

### Path 3: "Production Systems" (5 hours)

```
1. README.md (15 min)
   ↓
2. ADR-1.2 (Quick skim for decision - 15 min)
   ↓
3. LANGCHAIN_ECOSYSTEM_MAP.md (Focus on deployment - 30 min)
   ↓
4. examples_1_2.py (Focus on streaming, batching, callbacks - 1 hour)
   ↓
5. WP-1.3-The-Runnable-Protocol.md (Focus on performance - 1 hour)
   ↓
6. examples_1_3.py (Focus on Example 6: batch performance - 30 min)
   ↓
7. WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md (Model selection - 45 min)
   ↓
8. Design and build production system
```

**Outcome**: Ready to build production-grade LLM systems with informed model selection

---

### Path 8: "Multi-Agent Choreography for Emergent Workflows" (4 hours)

```
1. README.md (15 min)
   ↓
2. ADR-2.1-Choreography-Event-Driven-Agility-for-Emergent-Workflows.md (1 hour)
   ↓
3. choreography_hive_mind.py (study code structure - 1 hour)
   ↓
4. tests/test_choreography_hive_mind.py (understand test patterns - 45 min)
   ↓
5. Run choreography_hive_mind.py and tests locally (15 min)
   ↓
6. Adapt pattern to your multi-agent use case (45 min)
```

**Outcome**: Build autonomous multi-agent systems with event-driven choreography instead of orchestration

**Prerequisites**: Path 1 (basic understanding) or Path 3 (production systems knowledge)

**Topics Covered**:
- Event-driven architecture vs. orchestration
- Autonomous agent design with pub/sub
- Feedback loops for system homeostasis
- Distributed tracing with correlation IDs
- Resilience through decoupling
- Emergent workflow composition
- Second-order effects analysis

---

## 📖 Content Map

### Conceptual Layers

```
Layer 1: Foundation (What is LangChain?)
├─ README.md
└─ LANGCHAIN_ECOSYSTEM_MAP.md

Layer 2: Decision (Which pattern to use?)
├─ ADR-1.2-Hello-World-Three-Ways.md
└─ examples_1_2.py

Layer 3: Understanding (How does it work?)
├─ WP-1.3-The-Runnable-Protocol.md
└─ examples_1_3.py

Layer 4: Navigation (How is it all connected?)
└─ AGENTMAP.md (you are here)

Layer 5: Model Selection (Which model to use?)
├─ WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md
├─ Weighted scoring framework
└─ Production ADR template
```

---

## 🎯 Key Concepts Roadmap

```
                          LANGCHAIN ECOSYSTEM
                                 ↓
                    ┌────────────┴────────────┐
                    ↓                         ↓
            LANGCHAIN-CORE              LANGCHAIN-COMMUNITY
            (Runnables, etc)            (Integrations)
                    ↓                         ↓
            ADR-1.2 DECISION         Chain Selection
            (Which pattern?)              ↓
                    ↓              examples_1_2.py
              3 Approaches         (See them work)
                    ↓
            WP-1.3 DEEP DIVE
            (How they work)
                    ↓
            examples_1_3.py
            (Runnable protocol)
                    ↓
            PRODUCTION PATTERNS
            (Real-world systems)
```

---

## 🔍 Cross-Reference Matrix

### Which document answers...?

| Question | Document | Section |
|----------|----------|---------|
| What is LangChain? | README.md | Core Principles |
| What components exist? | LANGCHAIN_ECOSYSTEM_MAP.md | Complete section |
| Which chain to use? | ADR-1.2 | Decision flow |
| How to implement chains? | examples_1_2.py | All functions |
| What is Runnable protocol? | WP-1.3 | Part 1 |
| When to use invoke/batch/stream/ainvoke? | WP-1.3 + examples_1_3.py | Parts 2 + Example 1 |
| How to build custom Runnable? | WP-1.3 + examples_1_3.py | Part 5 + Example 2 |
| How to compose Runnables? | WP-1.3 + examples_1_3.py | Part 3 + Example 3 |
| How to trace execution? | examples_1_3.py | Example 4 |
| How to route conditionally? | examples_1_3.py | Example 5 |
| Why is batch() important? | examples_1_3.py | Example 6 |
| How do I parse structured output safely? | WP-1.5 | Schema + recovery strategy |
| How to choose a production model? | WP-1.6 | Decision matrix & scoring |
| How do I compare model trade-offs? | WP-1.6 | Architect axes comparison |
| What is tool-calling reliability? | WP-1.6 | Model evaluation criteria |
| How to do sensitivity analysis? | WP-1.6 | Impact analysis section |
| How to deploy? | LANGCHAIN_ECOSYSTEM_MAP.md | LangServe section |

---

## 📊 Content Density Matrix

```
Conceptual Difficulty vs Code Complexity

                              HIGH CODE
                              DENSITY
                                ↑
                                │
                    examples_1_2.py │ examples_1_3.py
                                │
                 LANGCHAIN_ECOSYSTEM_MAP │
                                │
                         ADR-1.2 │
                                │
                         README  │ WP-1.3
                                │
                    ← LOW ────────┴────── HIGH →
                         CONCEPTUAL
                         DIFFICULTY
```

---

## 🚀 Quick Navigation by Use Case

### "I'm building a chatbot"
1. Start: [README.md](README.md)
2. Understand pattern: [ADR-1.2](ADR-1.2-Hello-World-Three-Ways.md)
3. See examples: [examples_1_2.py](examples_1_2.py)
4. Streaming: [WP-1.3 Part 2](WP-1.3-The-Runnable-Protocol.md#part-2-the-four-execution-modes)
5. Tracing: [examples_1_3.py Example 4](examples_1_3.py)

### "I'm building a data pipeline"
1. Start: [README.md](README.md)
2. Choose pattern: [ADR-1.2](ADR-1.2-Hello-World-Three-Ways.md)
3. Performance: [examples_1_3.py Example 6](examples_1_3.py)
4. Batch processing: [WP-1.3 Part 2](WP-1.3-The-Runnable-Protocol.md)
5. Deploy: [LANGCHAIN_ECOSYSTEM_MAP.md](LANGCHAIN_ECOSYSTEM_MAP.md)

### "I'm building an agent system"
1. Start: [README.md](README.md)
2. Components: [LANGCHAIN_ECOSYSTEM_MAP.md](LANGCHAIN_ECOSYSTEM_MAP.md)
3. Understand Runnables: [WP-1.3](WP-1.3-The-Runnable-Protocol.md)
4. Custom components: [examples_1_3.py Example 2](examples_1_3.py)
5. Routing: [examples_1_3.py Example 5](examples_1_3.py)

### "I want to understand LangChain"
1. Ecosystem: [LANGCHAIN_ECOSYSTEM_MAP.md](LANGCHAIN_ECOSYSTEM_MAP.md)
2. Decisions: [ADR-1.2](ADR-1.2-Hello-World-Three-Ways.md)
3. Examples: [examples_1_2.py](examples_1_2.py)
4. Deep dive: [WP-1.3](WP-1.3-The-Runnable-Protocol.md)
5. Practice: [examples_1_3.py](examples_1_3.py)

---

## 📈 Progression Timeline

```
Week 1: Foundations
├─ Day 1: README.md (overview)
├─ Day 2: LANGCHAIN_ECOSYSTEM_MAP.md (components)
├─ Day 3: ADR-1.2 (patterns)
└─ Day 4: examples_1_2.py (implementations)

Week 2: Deep Understanding
├─ Day 1: WP-1.3 Parts 1-4 (protocol & execution)
├─ Day 2: WP-1.3 Parts 5-8 (implementation & patterns)
├─ Day 3: WP-1.3 Parts 9-12 (production & references)
└─ Day 4: examples_1_3.py (hands-on practice)

Week 3: Mastery
├─ Day 1: Build custom Runnable
├─ Day 2: Design composition architecture
├─ Day 3: Optimize performance (batch, streaming)
└─ Day 4: Production deployment

Week 4: Architecture
├─ Day 1: WP-1.6 decision matrix (model selection)
├─ Day 2: Output parsing and validation (WP-1.5)
├─ Day 3: Prompt management strategies (WP-1.4)
└─ Day 4: Full system design with all patterns
```

---

## 🔗 Internal Link Map

### From README.md, you can reach:
- 📖 [LANGCHAIN_ECOSYSTEM_MAP.md](LANGCHAIN_ECOSYSTEM_MAP.md) - Full stack documentation
- 📊 [ADR-1.2](ADR-1.2-Hello-World-Three-Ways.md) - Chain abstraction decision
- 💻 [examples_1_2.py](examples_1_2.py) - Working implementations
- 🔬 [WP-1.3](WP-1.3-The-Runnable-Protocol.md) - Runnable protocol deep dive
- 💻 [examples_1_3.py](examples_1_3.py) - Practical demonstrations

### From ADR-1.2, you can reach:
- 📖 [README.md](README.md) - Back to overview
- 📚 [LANGCHAIN_ECOSYSTEM_MAP.md](LANGCHAIN_ECOSYSTEM_MAP.md) - Component reference
- 💻 [examples_1_2.py](examples_1_2.py) - See approaches work
- 🔬 [WP-1.3](WP-1.3-The-Runnable-Protocol.md) - How approaches work underneath

### From WP-1.3, you can reach:
- 📖 [README.md](README.md) - Back to overview
- 🏗️ [ADR-1.2](ADR-1.2-Hello-World-Three-Ways.md) - Prerequisite knowledge
- 💻 [examples_1_3.py](examples_1_3.py) - See concepts in action
- 📚 [LANGCHAIN_ECOSYSTEM_MAP.md](LANGCHAIN_ECOSYSTEM_MAP.md) - Component details

### From examples, you can reach:
- 📖 [README.md](README.md) - Overview
- 🏗️ [ADR-1.2](ADR-1.2-Hello-World-Three-Ways.md) - Context for examples_1_2.py
- 🔬 [WP-1.3](WP-1.3-The-Runnable-Protocol.md) - Theory for examples_1_3.py
- 📋 [WP-1.4](WP-1.4-Prompt-Engineering-as-Code.md) - Theory for examples_1_4.py

### From WP-1.6, you can reach:
- 📖 [README.md](README.md) - Back to overview
- 📈 [WP-1.5](WP-1.5-Output-Parsing-for-System-Integration.md) - Output reliability constraints
- 📋 [WP-1.4](WP-1.4-Prompt-Engineering-as-Code.md) - Prompt strategy impact on costs
- 🏗️ [ADR-1.2](ADR-1.2-Hello-World-Three-Ways.md) - Orchestration architecture effects

---

## 📊 Dependency Graph

```
AGENTMAP.md (shows)
    ↑
    │ references
    │
    ├─────────→ README.md (entry point)
    │               ↓
    │               ├─→ LANGCHAIN_ECOSYSTEM_MAP.md
    │               ├─→ ADR-1.2
    │               └─→ WP-1.3
    │
    ├─────────→ ADR-1.2 (decision)
    │               ├─ depends on: LANGCHAIN_ECOSYSTEM_MAP.md
    │               ├─ provides examples to: examples_1_2.py
    │               └─ foundation for: WP-1.3
    │
    ├─────────→ WP-1.3 (understanding)
    │               ├─ depends on: ADR-1.2
    │               ├─ provides examples to: examples_1_3.py
    │               ├─ references: LANGCHAIN_ECOSYSTEM_MAP.md
    │               └─ explains: How everything works
    │
    ├─────────→ examples_1_2.py (code)
    │               └─ demonstrates: ADR-1.2 approaches
    │
    └─────────→ examples_1_3.py (code)
    │               └─ demonstrates: WP-1.3 concepts
    │
    ├─────────→ WP-1.4 (prompts)
    │               ├─ depends on: ADR-1.2
    │               ├─ references: WP-1.3
    │               └─ provides examples to: examples_1_4.py
    │
    ├─────────→ WP-1.5 (parsing)
    │               ├─ depends on: WP-1.3, WP-1.4
    │               └─ referenced by: WP-1.6
    │
    └─────────→ WP-1.6 (model selection)
                ├─ depends on: WP-1.5, WP-1.4, ADR-1.2
                ├─ provides: Decision framework
                └─ ADR template

LANGCHAIN_ECOSYSTEM_MAP.md (reference)
    ↑
    └─ referenced by all other documents
```

---

## 🎯 Meta-Learning Guide

**This agentmap helps you:**

1. **Understand Context**: See how documents relate to each other
2. **Choose Path**: Pick learning path based on your goals
3. **Find Answers**: Quick lookup for specific topics
4. **Navigate Efficiently**: Jump to relevant sections
5. **Plan Study**: See progression and time estimates
6. **Build Systems**: Understand architecture patterns

**Use this map to:**
- 🔍 Find what you need quickly
- 📚 Plan your learning journey
- 🗺️ Understand the overall architecture
- 🎯 See connections between concepts
- 🚀 Know what to read next

---

## 📝 Document Statistics

| Document | Type | Lines | Sections | Status |
|----------|------|-------|----------|--------|
| README.md | Guide | ~900 | 11 | ✅ Complete |
| LANGCHAIN_ECOSYSTEM_MAP.md | Reference | ~1200 | 15 | ✅ Complete |
| ADR-1.2 | Decision | ~500 | 12 | ✅ Complete |
| WP-1.3 | Deep Dive | ~1100 | 12 | ✅ Complete |
| WP-1.4 | Design Pattern | ~900 | 10 | ✅ Complete |
| WP-1.5 | Design Pattern | ~200 | 8 | ✅ Complete |
| WP-1.6 | Design Pattern | ~220 | 8 | ✅ Complete |
| WP-1.7 | Design Pattern | ~740 | 11 | ✅ Complete |
| examples_1_2.py | Code | ~900 | 7 | ✅ Complete |
| examples_1_3.py | Code | ~1500 | 7 | ✅ Complete |
| examples_1_4.py | Code | ~600 | 6 | ✅ Complete |
| examples_1_7.py | Code | ~603 | 6 | ✅ Complete |
| AGENTMAP.md | Map | ~750 | 18 | ✅ This file |
| **TOTAL** | | **~11,800+** | | ✅ |

**Estimated Learning Time**: 18-24 hours for complete understanding + hands-on practice

---

## 🔄 Feedback Loop

```
Read Documentation
        ↓
Run Examples
        ↓
Try It Yourself
        ↓
Build Something Real
        ↓
Measure Performance
        ↓
Optimize & Iterate
        ↓
Share Learning
        ↓
Back to Read (deeper understanding)
```

---

## 🎓 Mastery Checklist

### Understanding
- [ ] Know what a Runnable is
- [ ] Understand invoke/batch/stream/ainvoke trade-offs
- [ ] Know how pipes create DAGs
- [ ] Can explain Runnable protocol to others

### Implementation
- [ ] Can choose correct chain abstraction
- [ ] Can build custom Runnable
- [ ] Can compose Runnables
- [ ] Can implement streaming UI
- [ ] Can optimize with batching

### Production
- [ ] Can implement error handling
- [ ] Can trace execution with callbacks
- [ ] Can deploy with LangServe
- [ ] Can monitor with LangSmith
- [ ] Can build agentic systems

---

## 📞 Quick Reference

**Need to know how to...**
- Use Runnables? → [WP-1.3 Part 1](WP-1.3-The-Runnable-Protocol.md)
- Choose chain pattern? → [ADR-1.2 Decision Flow](ADR-1.2-Hello-World-Three-Ways.md)
- Build custom component? → [examples_1_3.py Example 2](examples_1_3.py)
- Stream output? → [WP-1.3 Part 2 - stream](WP-1.3-The-Runnable-Protocol.md) + [examples_1_3.py Example 1](examples_1_3.py)
- Batch process? → [examples_1_3.py Example 6](examples_1_3.py)
- Debug execution? → [examples_1_3.py Example 4](examples_1_3.py)
- Route conditionally? → [examples_1_3.py Example 5](examples_1_3.py)
- Manage prompts at scale? → [WP-1.4](WP-1.4-Prompt-Engineering-as-Code.md)
- Choose a model? → [WP-1.6](WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md)
- Deploy to production? → [LANGCHAIN_ECOSYSTEM_MAP.md LangServe](LANGCHAIN_ECOSYSTEM_MAP.md)

---

## 🌟 Pro Tips

1. **Don't read sequentially**: Use this map to jump to what you need
2. **Run examples while reading**: Code + explanation = best learning
3. **Start with use case**: Pick your use case path above
4. **Reference, don't memorize**: This is a reference, not memorization material
5. **Build as you learn**: Each section should inspire something to build
6. **Performance matters**: Example 6 (batch performance) is critical for production
7. **Observability is essential**: Callbacks and tracing are not optional
8. **Composition is powerful**: Master it and you can build anything

---

## 🚀 Next Steps

1. **Pick your learning path** above
2. **Start with the first document**
3. **Follow the links as you go**
4. **Run the examples**
5. **Build something real**
6. **Come back here if lost**

---

**Last Updated**: 2024  
**Total Documentation**: ~6,500 lines of guides, examples, and explanations  
**Estimated Mastery Time**: 15-20 hours  
**Status**: ✅ Complete and production-ready  

Happy learning! 🎓

---

**Repository Statistics** (auto-generated)

- 📄 Documentation: 4,725 lines across 6 files
- 💻 Examples: 3,777 lines across 3 files
- 📊 Total: 8,502 lines
- 🕒 Last updated: 2026-06-24 04:48 UTC
