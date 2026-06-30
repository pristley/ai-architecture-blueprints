# 🐝 Section 4: Multi-Agent Architectures

**Coordinate multiple agents: choose between choreography and orchestration, then implement at scale.**

This section covers two fundamental patterns for multi-agent systems: choreography (event-driven, emergent) and orchestration (centralized, deterministic). Includes ADRs, pattern guides, and the LangGraph framework for stateful graphs.

---

## 📚 Documents in This Section

| Document | Purpose | Time | Prerequisites |
|----------|---------|------|---|
| [ADR-2.1: Choreography Pattern](./ADR-2.1-Choreography-Event-Driven-Agility-for-Emergent-Workflows.md) | Event-driven agents: autonomous, emergent, loosely coupled | 1 hour | [Foundations](../01-foundations/README.md) |
| [ADR-2.2: Orchestration Pattern](./ADR-2.2-Orchestration-Centralized-Control.md) | Centralized control: deterministic, auditable, fully traceable | 1 hour | [Foundations](../01-foundations/README.md) |
| [WP-2.3: Orchestration Implementation](./WP-2.3-Orchestration-Pattern.md) | Build deterministic 6-step workflows with evaluation gates | 1.5 hours | [ADR-2.2](./ADR-2.2-Orchestration-Centralized-Control.md) |
| [WP-2.4: Choreography Implementation](./WP-2.4-Choreography-Pattern.md) | Build event-driven hive mind agents with feedback loops | 1.5 hours | [ADR-2.1](./ADR-2.1-Choreography-Event-Driven-Agility-for-Emergent-Workflows.md) |
| [WP-2.6: LangGraph Framework](./WP-2.6-Introduction-to-LangGraph-for-Stateful-Graphs.md) | Reimplementation with LangGraph: 60% less boilerplate | 2.5 hours | [WP-2.3](./WP-2.3-Orchestration-Pattern.md) |
| [WP-3.8: Designing Multi-Agent Systems](./WP-3.8-Designing-Multi-Agent-Systems.md) | Phase 2: Specialized multi-agent orchestration with shared state bus (C4 container model) | 2 hours | [WP-2.3](./WP-2.3-Orchestration-Pattern.md), [WP-3.5](../05-capstone-rag-patterns/) |

---

## 💻 Code Examples

| Example | Focus | Time | Status |
|---------|-------|------|--------|
| [choreography_hive_mind.py](./choreography_hive_mind.py) | Event-driven agents with EventBus | 45 min | ✅ |
| [controller_orchestration_agent.py](./controller_orchestration_agent.py) | Centralized controller with 6-step workflow | 45 min | ✅ |
| [examples_2_6.py](./examples_2_6.py) | LangGraph StateGraph orchestrator | 30 min | ✅ |
| [examples_3_8.py](./examples_3_8.py) | Phase 2: Multi-agent Content Creator & QA system with versioned state bus | 45 min | ✅ |

---

## 🎯 Learning Path (7 hours total)

### Decision Path: Which Pattern? (2 hours)
1. Read [ADR-2.1: Choreography](./ADR-2.1-Choreography-Event-Driven-Agility-for-Emergent-Workflows.md) (1 hour)
2. Read [ADR-2.2: Orchestration](./ADR-2.2-Orchestration-Centralized-Control.md) (1 hour)
3. **Decision**: Use orchestration for deterministic workflows, choreography for emergent behaviors

### Orchestration Path (3 hours)
1. Study [WP-2.3](./WP-2.3-Orchestration-Pattern.md) (1.5 hours)
2. Study [controller_orchestration_agent.py](./controller_orchestration_agent.py) (45 min)
3. (Optional) [WP-2.6: LangGraph](./WP-2.6-Introduction-to-LangGraph-for-Stateful-Graphs.md) (2.5 hours) - Same workflow, less code

### Choreography Path (3 hours)
1. Study [WP-2.4](./WP-2.4-Choreography-Pattern.md) (1.5 hours)
2. Study [choreography_hive_mind.py](./choreography_hive_mind.py) (45 min)
3. Design your own event-driven system

### Phase 2: Advanced Multi-Agent Patterns (2 hours)
1. Study [WP-3.8: Multi-Agent System Design](./WP-3.8-Designing-Multi-Agent-Systems.md) (1.5 hours)
   - Specialized agent taxonomy (producer, evaluators, coordinator)
   - Shared state management with versioning and event sourcing
   - Supervisor orchestration patterns
   - C4 container architecture
2. Study [examples_3_8.py](./examples_3_8.py) - Content Creator & QA system (30 min)

---

## 📊 Orchestration vs Choreography

| Dimension | Orchestration | Choreography |
|-----------|---------------|--------------|
| **Control** | Centralized controller | Distributed agents |
| **Workflow** | Deterministic, linear | Emergent, event-driven |
| **Auditability** | Full trace of every step | Message-level visibility |
| **Flexibility** | Rigid, hard to change | Adaptive, self-organizing |
| **Complexity** | Simpler to understand | Harder to debug |
| **Best For** | Reports, approvals, ETL | Collaboration, exploration |

---

## 🔗 Test Suites

- `../../../tests/test_controller_orchestration.py` - 41 tests for orchestration
- `../../../tests/test_choreography_hive_mind.py` - ~800 lines of choreography tests
- `../../../tests/test_langgraph_orchestration.py` - 30 tests for LangGraph framework
- `../../../tests/test_wp_3_8.py` - 62+ tests for multi-agent system (Phase 2)

---

## ➡️ Next Steps

- **Full Learning Path** → [Back to main docs](../README.md)
- **Reference Materials** → [Reference Section](../reference/README.md)
