# AI Architecture Blueprints

[![CI/CD Pipeline](https://github.com/pristley/ai-architecture-blueprints/workflows/CI%2FCD%20Pipeline/badge.svg?branch=main)](https://github.com/pristley/ai-architecture-blueprints/actions)
[![Version](https://img.shields.io/badge/version-1.2.1-blue.svg)](VERSION)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-production-brightgreen.svg)](#)
[![Code Quality](https://img.shields.io/badge/quality-strict_linting-brightgreen.svg)](#)
[![Tests](https://img.shields.io/badge/tests-30+-green.svg)](#)

**Build production AI systems with proven architectural patterns.**

This repository provides decision records, design patterns, and working implementations for building scalable, observable, and maintainable AI applications using LangChain and LangGraph.

---

## 📂 Project Structure

Documentation is organized into **4 learning sections** plus reference materials:

```
📚 docs/
├── 01-foundations/          Learn core abstractions (2.5 hours)
├── 02-production-patterns/  Master production patterns (5 hours)
├── 03-memory-state-agents/  Build scalable conversational systems (4 hours)
├── 04-multi-agent-architectures/  Coordinate multiple agents (7 hours)
├── reference/               Navigation hubs & reference docs
└── README.md               👈 START HERE
```

---

## 🚀 Quick Start

**→ [Open the Documentation Hub](./docs/README.md)**

### Choose Your Learning Path

| Your Goal | Start Here | Time |
|-----------|-----------|------|
| Understand patterns | [Foundations](./docs/01-foundations/README.md) | 2.5 hrs |
| Learn production code | [Production Patterns](./docs/02-production-patterns/README.md) | 5 hrs |
| Build memory-aware agents | [Memory & State](./docs/03-memory-state-agents/README.md) | 4 hrs |
| Coordinate multiple agents | [Multi-Agent Systems](./docs/04-multi-agent-architectures/README.md) | 10 hrs |
| See the big picture | [AGENTMAP Visual](./docs/reference/AGENTMAP.md) | 20 min |
| Ecosystem reference | [LangChain Docs](./docs/reference/LANGCHAIN_ECOSYSTEM_MAP.md) | 30 min |

---

## 📊 Repository at a Glance

- **12+ Work Products** (WP) and Architecture Decision Records (ADR)
- **9 Code Examples** demonstrating each pattern
- **30+ Test Suites** with 100+ comprehensive tests
- **~15,000 lines** of documentation and code
- **100% Cross-referenced** with verified links
- **Production-tested** code and patterns

---

## 🏗️ What's Inside

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

### 🐝 Section 4: Multi-Agent Architectures (10 hours)
Coordinate multiple agents using choreography or orchestration.
- ADR-2.1: Choreography (event-driven, emergent)
- ADR-2.2: Orchestration (centralized, deterministic)
- WP-2.3 & WP-2.4: Complete implementations
- WP-2.6: LangGraph framework (60% less boilerplate)
- WP-2.7: Checkpointing & Human-in-the-Loop (guardrails for critical actions)

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

1. **Start here**: [Documentation Hub](./docs/README.md)
2. **Visual map**: [AGENTMAP](./docs/reference/AGENTMAP.md) - See how everything connects
3. **Get help**: Check [docs/README.md](./docs/README.md) for detailed learning paths

---

## 🔗 Repository Links

- **[Full Documentation](./docs/README.md)** - Main entry point
- **[Changelog](./CHANGELOG.md)** - All updates and changes
- **[License](./LICENSE)** - MIT
- **[Status](./docs/reference/REPOSITORY_STATUS.md)** - Project metrics

---

**Ready to start?** 👉 **[Open the Documentation Hub](./docs/README.md)**
