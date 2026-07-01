# AI Architecture Blueprints

[![CI/CD Pipeline](https://github.com/pristley/ai-architecture-blueprints/workflows/CI%2FCD%20Pipeline/badge.svg?branch=main)](https://github.com/pristley/ai-architecture-blueprints/actions)
[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](VERSION)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-production-brightgreen.svg)](#)
[![Code Quality](https://img.shields.io/badge/quality-strict_linting-brightgreen.svg)](#)
[![Tests](https://img.shields.io/badge/tests-300+-green.svg)](#)
[![Portfolio](https://img.shields.io/badge/portfolio-25%20artifacts-brightgreen.svg)](#)

**Build production AI systems with proven architectural patterns.**

This repository provides decision records, design patterns, and working implementations for building scalable, observable, and maintainable AI applications using LangChain and LangGraph.

> **🎯 [VIEW PORTFOLIO EXECUTIVE SUMMARY](./docs/reference/PORTFOLIO_EXECUTIVE_SUMMARY.md)** — Complete index of 20 work products, 5 ADRs, key insights, and architecture diagrams.

---

## ✨ Portfolio Highlights

| Metric | Value | Details |
|--------|-------|---------|
| **Work Products** | 20+ | From foundations to production multi-agent systems |
| **Architecture Decisions** | 5 ADRs | Strategic decisions guiding all implementations |
| **Documentation** | 15,000+ lines | Comprehensive guides with decision trees |
| **Code Examples** | 9 implementations | Production-ready with full comments |
| **Test Coverage** | 300+ tests | Validating each pattern and edge case |
| **Performance Gains** | Measured | Naive → Production: 36% latency reduction, 27% quality gain |

**Key Portfolio Assets:**
- 🏗️ **8 Orchestration & Multi-Agent Patterns** (choreography, orchestration, LangGraph, checkpointing)
- 🧠 **3 Memory & State Management Patterns** (dual memory, state machines, event sourcing)
- 📊 **8 RAG Architecture Patterns** (naive baseline, reranking, hierarchical, agentic, evaluation, query router)
- 🤖 **2 Multi-Agent System Patterns** (specialized agents, state coordination)
- 🎯 **5 Strategic Architecture Decisions** (LangChain protocol, choreography vs orchestration, agentic vs one-shot, state management)

---

## 📂 Project Structure

Documentation is organized into **5 learning sections** plus reference materials:

```
📚 docs/
├── 01-foundations/          Learn core abstractions (2.5 hours)
├── 02-production-patterns/  Master production patterns (5 hours)
├── 03-memory-state-agents/  Build scalable conversational systems (4 hours)
├── 04-multi-agent-architectures/  Coordinate multiple agents (10 hours)
├── 05-capstone-rag-patterns/  Deep comparative analysis & portfolio (8-10 hours)
├── reference/               Navigation hubs & reference docs
└── README.md               👈 START HERE
```

---

## 🚀 Quick Start
View Portfolio Executive Summary](./docs/reference/PORTFOLIO_EXECUTIVE_SUMMARY.md)** *(20 work products, 5 ADRs, key insights)*

**→ [Open the Documentation Hub](./docs/README.md)**

### Choose Your Learning Path

| Your Goal | Start Here | Time | Portfolio |
|-----------|-----------|------|-----------|
| See the complete picture | [Portfolio Summary](./docs/reference/PORTFOLIO_EXECUTIVE_SUMMARY.md) | 20 min | All 25 artifacts |
| Understand patterns | [Foundations](./docs/01-foundations/README.md) | 2.5 hrs | ADR-1.2, WP-1.3–1.7 |
| Learn production code | [Production Patterns](./docs/02-production-patterns/README.md) | 5 hrs | WP-1.4–1.7 |
| Build memory-aware agents | [Memory & State](./docs/03-memory-state-agents/README.md) | 4 hrs | WP-2.1–2.2, ADR-3.9 |
| Coordinate multiple agents | [Multi-Agent Systems](./docs/04-multi-agent-architectures/README.md) | 10 hrs | WP-2.3–2.7, WP-3.8, ADR-3.9 |
| Build RAG systems | [Capstone: RAG Patterns](./docs/05-capstone-rag-patterns/README.md) | 8-10 hrs | WP-3.0–3.7, ADR-003 |
| See the big picture | [AGENTMAP Visual](./docs/reference/AGENTMAP.md) | 20 min | Reference |
| Ecosystem reference | [LangChain Docs](./docs/reference/LANGCHAIN_ECOSYSTEM_MAP.md) | 30 min | Reference
| Ecosystem reference | [LangChain Docs](./docs/reference/LANGCHAIN_ECOSYSTEM_MAP.md) | 30 min |

---20 Work Products** (WP) with architecture guides, code, and tests
- **5 Architecture Decision Records** (ADR) for strategic choices
- **9 Code Examples** demonstrating each pattern
- **300+ Test Cases** with comprehensive coverage
- **15,000+ lines** of documentation and code
- **100% Cross-referenced** with verified links
- **Production-tested** patterns and implementatioh pattern
- **30+ Test Suites** with 100+ comprehensive tests
- **~15,000 lines** of documentation and code
- **100% Cross-referenced** with verified links
- **Production-tested** code and patterns

---

## 🏗️ What's Inside

### 📋 [Portfolio Executive Summary](./docs/reference/PORTFOLIO_EXECUTIVE_SUMMARY.md)
**Start here** for a complete overview of all 25 artifacts, key insights, learning paths, and production deployment architecture.

### 🏗️ Section 1: Foundations (2.5 hours)
Learn the core abstractions that underpin all LLM applications.
- ADR-1.2: Which chain abstraction to use
- WP-1.3: Deep dive into the Runnable protocol
- Working code examples

### 🏭 Section 2: Production Patterns (5 hours)
Master the patterns that make systems reliable, observable, and scalable.
- WP-1.4: Prompt management (versioning, composition)
- WP-1.5: Output parsing (reliability, recovery)
- WP-1.6: Model selection (decision matrix)
- WP-1.7: Observability (LangSmith tracing)

### 💾 Section 3: Memory, State & Agents (4 hours)
Build conversational systems with scalable memory and loop prevention.
- WP-2.1: Dual-memory architecture
- WP-2.2: State management and loop detection
- Production implementations and tests

### 🐝 Section 4: Multi-Agent Architectures (11.5 hours)
Coordinate multiple agents using choreography or orchestration.
- ADR-2.1: Choreography (event-driven, emergent)
- ADR-2.2: Orchestration (centralized, deterministic)
- WP-2.3 & WP-2.4: Complete implementations
- WP-2.6: LangGraph framework (60% less boilerplate)
- WP-2.7: Checkpointing & Human-in-the-Loop (guardrails for critical actions)
- WP-3.8: Multi-Agent System Design (Content Creator + QA + Editor + Fact-Check)
- ADR-3.9: State Management Strategies (shared state vs event bus, conflict resolution)

### 🎓 Section 5: Capstone — RAG Patterns & Deep Comparisons (10+ hours)
Transform theoretical knowledge into production RAG systems with deep comparative analysis.
- WP-3.0: Knowledge Architecture (OKF vs traditional databases)
- WP-3.1: RAG Architecture — Naive Baseline (vector stores, semantic search, 5 failure modes)
- WP-3.2: Advanced Retrieval — Reranking & Filtering (accuracy improvement)
- WP-3.3: Hierarchical Indexing — Scale to 100K+ documents
- WP-3.4: Evaluation & Metrics — Measure and debug RAG performance
- WP-3.5: Agentic Workflow — Iterative multi-step search and synthesis
- ADR-003: Agentic RAG Decision Record (when to use vs one-shot)
- WP-3.7: Query Router — Adaptive strategy selection (-36% latency, -28% cost)

### 🏛️ Section 6: Capstone — End-to-End Agentic System (2-3 weeks)
**[Legal Contract Analysis Agent](./legal-contract-agent/)** — Production agentic system for automated legal contract analysis with human-in-the-loop review.

**Key Features**:
- 🏗️ **7-Task Pipeline**: Ingestion → Classification → Clause Extraction → Anomaly Detection → Summarization → Triage → Human Review
- ⚡ **10× Speedup**: Parallel task execution (75s → 15s)
- 🛡️ **10 Guardrails**: Input validation, PII redaction, confidence calibration, rate limiting
- 👤 **Human-in-Loop**: Streamlit UI for legal review with feedback capture
- 📊 **6 Success Metrics**: Recall, precision, F1, hallucination rate, latency, cost
- 🗂️ **45-Contract Ground Truth**: Annotated dataset with 13 detected anomalies

**Architecture**:
- **Orchestration**: LangGraph with checkpointing
- **Tools**: Docling (PDF parsing), Qdrant (vector search), OpenAI GPT-4, Tavily (legal search)
- **UI**: Streamlit multi-page dashboard
- **Notifications**: Slack + Email

**Documentation**: [Capstone Design Docs](./docs/06-capstone-legal-contract-analysis/) | **Code**: [legal-contract-agent](./legal-contract-agent/) | **Guide**: [Implementation Guide](./legal-contract-agent/INDEX.md)

---

## ⚡ Quick Install & Run

```bash
# Clone and install
git clone https://github.com/pristley/ai-architecture-blueprints.git
cd ai-architecture-blueprints
pip install -r requirements.txt

# Run an example
python docs/01-foundations/examples_1_2.py

# Run tests
pytest tests/ -v
```

---

## 📖 Learn More

1. **🎯 Start here**: [Portfolio Executive Summary](./docs/reference/PORTFOLIO_EXECUTIVE_SUMMARY.md) - Complete overview of all 25 artifacts
2. **📚 Full guide**: [Documentation Hub](./docs/README.md) - Detailed learning paths
3. **🗺️ Visual map**: [AGENTMAP](./docs/reference/AGENTMAP.md) - See how everything connects
4. **📋 Status**: [Repository Status](./docs/reference/REPOSITORY_STATUS.md) - Metrics and coverage

---

## 🔗 Repository Links

- **[Full Documentation](./docs/README.md)** - Main entry point
- **[Changelog](./CHANGELOG.md)** - All updates and changes
- **[License](./LICENSE)** - MIT
- **[Status](./docs/reference/REPOSITORY_STATUS.md)** - Project metrics

---

**Ready to start?** 

👉 **[View Portfolio Summary](./docs/reference/PORTFOLIO_EXECUTIVE_SUMMARY.md)** — See all 25 artifacts and key insights (20 min read)

👉 **[Open the Documentation Hub](./docs/README.md)** — Choose a learning path tailored to your goals
