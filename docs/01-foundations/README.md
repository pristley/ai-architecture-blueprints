# 🏗️ Section 1: Foundations

**Learn the core abstractions that underpin LangChain architectures.**

This section establishes the conceptual and technical foundations. You'll understand which patterns to choose and why they matter, then dive deep into how LangChain's Runnable protocol works underneath.

---

## 📚 Documents in This Section

| Document | Purpose | Time | Prerequisites |
|----------|---------|------|---|
| [ADR-1.2: Chain Abstractions](./ADR-1.2-Hello-World-Three-Ways.md) | Understand three approaches to building LLM chains and decide which to use | 30 min | None |
| [WP-1.3: The Runnable Protocol](./WP-1.3-The-Runnable-Protocol.md) | Deep dive into how LangChain executes chains with the Runnable abstraction | 2 hours | ADR-1.2 |

---

## 💻 Code Examples

| Example | Focus | Time |
|---------|-------|------|
| [examples_1_2.py](./examples_1_2.py) | Three chain approaches side-by-side | 30 min |
| [examples_1_3.py](./examples_1_3.py) | Runnable protocol: invoke, batch, stream, ainvoke | 45 min |

---

## 🎯 Learning Path (2.5 hours total)

1. **Start here**: Read [ADR-1.2](./ADR-1.2-Hello-World-Three-Ways.md) (30 min)
   - Understand the three approaches
   - Know when to use each pattern
   - Make your first architectural decision

2. **Deep dive**: Read [WP-1.3](./WP-1.3-The-Runnable-Protocol.md) (2 hours)
   - Protocol semantics and execution modes
   - How composition creates DAGs
   - Performance optimization patterns

3. **Practice**: Run code examples
   - `python examples_1_2.py` (10 min)
   - `python examples_1_3.py` (20 min)

---

## ➡️ Next Steps

Once you understand these foundations:
- **Production Patterns** → [Section 2: Production Patterns](../02-production-patterns/README.md) - Learn advanced patterns for scale
- **Full Learning Path** → [Back to main docs](../README.md)
