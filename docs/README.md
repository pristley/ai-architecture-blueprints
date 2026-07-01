# 📖 AI Architecture Blueprints - Documentation

**Build production AI systems with proven architectural patterns.**

Welcome to the complete documentation for the AI Architecture Blueprints repository. This guide is organized into four learning sections plus reference materials.

---

## 🎯 Quick Start: Choose Your Path

### I want to...

| Goal | Start Here | Time |
|------|-----------|------|
| **Understand which pattern to use** | [Section 1: Foundations](./01-foundations/README.md) | 2.5 hours |
| **Learn production patterns** | [Section 2: Production](./02-production-patterns/README.md) | 5 hours |
| **Build memory-aware agents** | [Section 3: Memory & State](./03-memory-state-agents/README.md) | 4 hours |
| **Coordinate multiple agents** | [Section 4: Multi-Agent](./04-multi-agent-architectures/README.md) | 7 hours |
| **Build RAG systems** | [Section 5: Capstone RAG](./05-capstone-rag-patterns/README.md) | 8 hours |
| **See a production AI system** | [Section 6: Legal Contract Agent](./06-capstone-legal-contract-analysis/README.md) | 2-3 weeks |
| **Choose knowledge architecture** | [WP-3.0: Knowledge Architecture](./05-capstone-rag-patterns/WP-3.0-Knowledge-Architecture-Decisions.md) | 3 hours |
| **See the complete picture** | [AGENTMAP.md](./reference/AGENTMAP.md) | 20 min |
| **Get ecosystem context** | [LANGCHAIN_ECOSYSTEM_MAP.md](./reference/LANGCHAIN_ECOSYSTEM_MAP.md) | 30 min |

---

## 📚 Four Learning Sections

### 🏗️ [Section 1: Foundations](./01-foundations/README.md)
Learn the core abstractions and decision patterns that underpin LangChain architectures.

**Contains:**
- ADR-1.2: Which chain abstraction to use
- WP-1.3: Deep dive into the Runnable protocol
- Working code examples

**Outcome:** Understand the foundations and make architectural decisions with confidence.

---

### 🏭 [Section 2: Production Patterns](./02-production-patterns/README.md)
Master the patterns that make LLM systems reliable, observable, and maintainable at scale.

**Contains:**
- WP-1.4: Prompt management (versioning, composition)
- WP-1.5: Output parsing (reliability, recovery)
- WP-1.6: Model selection (decision matrix)
- WP-1.7: Observability (LangSmith tracing)

**Outcome:** Build production-ready LLM chains with industry best practices.

---

### 💾 [Section 3: Memory, State & Agents](./03-memory-state-agents/README.md)
Build conversational systems with scalable memory and agents that don't infinite loop.

**Contains:**
- WP-2.1: Dual-memory architecture (short-term + long-term)
- WP-2.2: State management (loop prevention)
- Production implementations and tests

**Outcome:** Deploy conversational agents at scale with bounded token usage.

---

### 🐝 [Section 4: Multi-Agent Architectures](./04-multi-agent-architectures/README.md)
Coordinate multiple agents using choreography or orchestration patterns.

**Contains:**
- ADR-2.1: Choreography (event-driven, emergent)
- ADR-2.2: Orchestration (centralized, deterministic)
- WP-2.3: Orchestration implementation
- WP-2.4: Choreography implementation
- WP-2.6: LangGraph framework (60% less boilerplate)

**Outcome:** Make informed decisions about multi-agent coordination and implement at scale.

---

### 🎓 [Section 5: Capstone — RAG & Knowledge Architecture](./05-capstone-rag-patterns/README.md)
Deep dives into retrieval-augmented generation and knowledge representation decisions.

**Contains:**
- WP-3.0: Knowledge architecture decisions (OKF vs traditional, 40-50% cost savings)
- WP-3.1: Naive RAG baseline (foundation for all retrieval systems)
- WP-3.2+: Advanced retrieval, hierarchical indexing, evaluation

**Outcome:** Build production RAG systems and choose the right knowledge architecture for your use case.

---

### 🏛️ [Section 6: Capstone — End-to-End Agentic System](./06-capstone-legal-contract-analysis/README.md)
Production implementation of a legal contract analysis agent using all portfolio patterns.

**Contains:**
- **10 Design Documents** (ADRs, threat models, guardrails)
- **45-Contract Ground Truth Dataset** (annotated with anomalies)
- **Full Python Implementation** (LangGraph, Qdrant, OpenAI)
- **Streamlit UI** (human review dashboard)
- **6 Success Metrics** (evaluation methodology)

**Quick Links:**
- 🔗 **[Implementation Code](../legal-contract-agent/)** — Full source code
- ⏱️ **[Quick Start](../legal-contract-agent/QUICKSTART.md)** — 5-minute setup
- 🗺️ **[Project Index](../legal-contract-agent/INDEX.md)** — Navigation guide

**Outcome:** See a complete end-to-end agentic system in production, integrating RAG, orchestration, memory, multi-agent patterns, human-in-the-loop checkpoints, and guardrails.

---

### [🗺️ AGENTMAP.md](./reference/AGENTMAP.md)
Complete visual map showing:
- How all documents relate
- Learning paths for different goals
- Cross-reference matrix
- Progress checklist

**Use this when:** You're lost, want to see relationships, or need a map.

### [📚 LANGCHAIN_ECOSYSTEM_MAP.md](./reference/LANGCHAIN_ECOSYSTEM_MAP.md)
Full reference documentation on:
- LangChain components and architecture
- Integration patterns
- Deployment options
- Ecosystem overview

**Use this when:** You need technical details about components.

---

## 🎓 Suggested Learning Paths

### Path 1: "Show Me the Basics" (2.5 hours)
1. [Foundations](./01-foundations/README.md) - Understand patterns
2. Run the code examples
3. **You'll know:** Which pattern to choose

### Path 2: "I Want Production Code" (5 hours)
1. [Foundations](./01-foundations/README.md)
2. [Production Patterns](./02-production-patterns/README.md)
3. **You'll know:** How to build production LLM chains

### Path 3: "Show Me Everything" (20 hours)
All four sections in order, reading deeply and running all examples.
**You'll know:** How to architect any AI system.

### Path 4: "Multi-Agent Systems" (10 hours)
1. [Foundations](./01-foundations/README.md)
2. [Memory & State](./03-memory-state-agents/README.md)
3. [Multi-Agent Architectures](./04-multi-agent-architectures/README.md)
**You'll know:** How to build coordinated multi-agent systems.

### Path 5: "RAG & Knowledge Systems" (11 hours)
1. [Foundations](./01-foundations/README.md)
2. [Production Patterns](./02-production-patterns/README.md)
3. [Section 5: RAG & Capstone](./05-capstone-rag-patterns/README.md) - Start with WP-3.0 for architecture decisions
**You'll know:** How to design and build production RAG systems.

---

## 📊 Repository Statistics

- **5 Learning Sections** with 13+ work products
- **9 Code Examples** with 30+ test suites (100+ tests)
- **~20,000 lines** of documentation and code
- **100% Cross-referenced** - all links verified
- **Production-ready** - all code tested and working

---

## ✅ Design Principles

All patterns in this repository follow five core principles:

1. **Observability First** - Instrument every component, trace end-to-end
2. **Composability by Design** - Small units, standardized interfaces
3. **Explicit Trade-offs** - Document why you chose approach X over Y
4. **Defensive Implementation** - Error handling, retries, fail loudly
5. **Production Readiness** - Design for scale from day one

---

## 🚀 Get Started

**First time here?** Start with [Section 1: Foundations](./01-foundations/README.md)

**Want specific answers?** Check [AGENTMAP.md](./reference/AGENTMAP.md) for quick lookups

**Need help navigating?** See [Reference](./reference/README.md) materials

---

## 📝 Document Index

| # | Document | Type | Time |
|---|----------|------|------|
| 1 | [ADR-1.2](./01-foundations/ADR-1.2-Hello-World-Three-Ways.md) | Decision | 30 min |
| 2 | [WP-1.3](./01-foundations/WP-1.3-The-Runnable-Protocol.md) | Guide | 2 hours |
| 3 | [WP-1.4](./02-production-patterns/WP-1.4-Prompt-Engineering-as-Code.md) | Pattern | 1.5 hours |
| 4 | [WP-1.5](./02-production-patterns/WP-1.5-Output-Parsing-for-System-Integration.md) | Pattern | 45 min |
| 5 | [WP-1.6](./02-production-patterns/WP-1.6-Choosing-an-LLM-A-Decision-Matrix.md) | Matrix | 1 hour |
| 6 | [WP-1.7](./02-production-patterns/WP-1.7-Introduction-to-Tracing-with-LangSmith.md) | Guide | 1.5 hours |
| 7 | [WP-2.1](./03-memory-state-agents/WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md) | Pattern | 1.5 hours |
| 8 | [WP-2.2](./03-memory-state-agents/WP-2.2-State-Management-in-Single-Agent-Loop.md) | Pattern | 1.5 hours |
| 9 | [ADR-2.1](./04-multi-agent-architectures/ADR-2.1-Choreography-Event-Driven-Agility-for-Emergent-Workflows.md) | Decision | 1 hour |
| 10 | [ADR-2.2](./04-multi-agent-architectures/ADR-2.2-Orchestration-Centralized-Control.md) | Decision | 1 hour |
| 11 | [WP-2.3](./04-multi-agent-architectures/WP-2.3-Orchestration-Pattern.md) | Pattern | 1.5 hours |
| 12 | [WP-2.4](./04-multi-agent-architectures/WP-2.4-Choreography-Pattern.md) | Pattern | 1.5 hours |
| 13 | [WP-2.6](./04-multi-agent-architectures/WP-2.6-Introduction-to-LangGraph-for-Stateful-Graphs.md) | Guide | 2.5 hours |

---

## 🔗 Repository Links

- **Main Repository**: [GitHub](https://github.com/pristley/ai-architecture-blueprints)
- **Status**: [REPOSITORY_STATUS.md](./reference/REPOSITORY_STATUS.md)
- **Changes**: [CHANGELOG.md](../CHANGELOG.md)
- **License**: [MIT](../LICENSE)

---

## 💡 Tips for Success

1. **Start with ADRs (Architecture Decision Records)** - These provide decision frameworks
2. **Read work products in order** - Each builds on previous concepts
3. **Run every code example** - Hands-on learning reinforces concepts
4. **Refer to AGENTMAP when lost** - It's your navigation compass
5. **Use references for lookups** - LANGCHAIN_ECOSYSTEM_MAP is your technical index

---

**Ready to start?** Pick a section above and dive in! 🚀
