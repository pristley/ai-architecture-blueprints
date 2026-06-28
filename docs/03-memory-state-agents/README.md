# 💾 Section 3: Memory, State & Agents

**Build conversational systems with scalable memory and agents that don't infinite loop.**

These patterns address the unique challenges of single-agent systems: managing conversation history at scale, preventing infinite loops, and maintaining coherent state across multiple steps.

---

## 📚 Documents in This Section

| Document | Purpose | Time | Prerequisites |
|----------|---------|------|---|
| [WP-2.1: Memory Architecture](./WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md) | Dual-memory: bounded token usage + semantic persistence | 1.5 hours | [Foundations](../01-foundations/README.md) |
| [WP-2.2: State Management](./WP-2.2-State-Management-in-Single-Agent-Loop.md) | Agent state machines with infinite loop prevention | 1.5 hours | [Foundations](../01-foundations/README.md) |

---

## 💻 Code Examples

| Example | Focus | Time |
|---------|-------|------|
| [examples_2_1.py](./examples_2_1.py) | Dual-memory chatbot with fact extraction | 30 min |
| [examples_2_2.py](./examples_2_2.py) | State machine agent with loop detection | 30 min |
| [research_assistant_state_machine.py](./research_assistant_state_machine.py) | Production-grade research assistant | 45 min |

---

## 🎯 Learning Path (4 hours total)

1. **Memory Architecture** (1.5 hours)
   - Read [WP-2.1](./WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md)
   - Run `examples_2_1.py`

2. **State Management** (1.5 hours)
   - Read [WP-2.2](./WP-2.2-State-Management-in-Single-Agent-Loop.md)
   - Run `examples_2_2.py`

3. **Production Implementation** (1 hour)
   - Study [research_assistant_state_machine.py](./research_assistant_state_machine.py)
   - Review test suite: `../../../tests/test_research_assistant_state_machine.py`

---

## 🔑 Key Concepts

- **Short-term memory**: Last N messages in bounded buffer
- **Long-term memory**: Extracted facts in vector store
- **State machine**: Explicit transitions between agent states
- **Loop detection**: 4 mechanisms to prevent infinite loops
- **Token bounding**: Predictable costs and context windows

---

## ➡️ Next Steps

- **Multi-Agent Systems** → [Section 4: Multi-Agent](../04-multi-agent-architectures/README.md) - Coordinate multiple agents
- **Full Learning Path** → [Back to main docs](../README.md)
