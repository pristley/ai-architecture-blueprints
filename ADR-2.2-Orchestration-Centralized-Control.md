# ADR-2.2: Orchestration - Centralized Control for Deterministic Workflows

**Status**: Active | **Version**: 1.0 | **Date**: 2024

---

## TL;DR

**Use Orchestration when you need predictable, repeatable workflows with centralized control.** A Controller agent explicitly plans tasks, executes steps sequentially, evaluates results, and makes branching decisions. This pattern trades flexibility for predictability and is ideal for well-defined processes: report generation, data pipelines, multi-step form processing.

**When to use**:
- ✅ Task is well-defined (clear inputs, outputs, steps)
- ✅ You need reproducible results and audit trails
- ✅ Debugging and monitoring are critical
- ✅ Workflow is mostly sequential

**When NOT to use**:
- ❌ Task is emergent or adaptive (choreography is better)
- ❌ You need autonomous, loosely-coupled agents
- ❌ Failure in one step should not halt entire system
- ❌ Workflow is dynamic or discovery-based

---

## The Decision

**Orchestration** is a pattern where a single **Controller** agent:

1. **Plans** the entire workflow explicitly (e.g., "Generate report: Fetch data → Analyze → Synthesize → Format → Publish")
2. **Executes** tools sequentially with state management
3. **Evaluates** each step's output (success? retry? refine? skip?)
4. **Decides** the next action based on evaluation
5. **Tracks** everything for observability and replay

The Controller is the **single source of truth** for:
- What steps have been taken
- Why each step succeeded or failed
- What comes next
- When to stop or retry

```
┌─────────────────────────────────────────────────────────────┐
│           CONTROLLER AGENT (Orchestrator)                   │
│                                                             │
│  Plan: [Fetch Data] → [Analyze] → [Synthesize] → [Format] │
│  State: {step, attempt, results, errors, timestamp}        │
│  Logic: Evaluate(result) → Decide(next_action)             │
└─────────────────────────────────────────────────────────────┘
                    ↓        ↓        ↓        ↓
            ┌──────────────────────────────────────┐
            │      Tools (Stateless Workers)       │
            │  • Fetch  • Analyze  • Synthesize    │
            │  • Format • Validate • Publish       │
            └──────────────────────────────────────┘
```

---

## Context: Why Orchestration?

### The Problem We're Solving

Multi-step tasks need:
- **Predictability**: Same input → Same output (reproducible)
- **Auditability**: "What happened at step 3? Why did it fail?"
- **Observability**: Progress tracking, step times, error locations
- **Control**: "Skip step 2, jump to step 4" or "Retry with different parameters"
- **Rollback**: "Revert to step X and continue"

Choreography (ADR-2.1) solves **adaptability** but sacrifices **predictability**. Orchestration inverts this trade-off.

### Example Workflow: "Write AI Trends Report"

**Orchestration approach:**

```
Step 1: Plan
  → Explicit plan: "Analyze 3 topics (ML, LLMs, Ethics), write 2000-word report"
  
Step 2: Fetch Research Data
  → Search for recent papers and news
  → Evaluate: Did we get 15+ sources? → Yes, continue
  
Step 3: Extract Key Points
  → Parse each source into facts + citations
  → Evaluate: Do we have enough facts? → No, search again
  
Step 4: Synthesize Draft
  → Write structured draft using key points
  → Evaluate: Is draft >1500 words? → No, request more analysis
  
Step 5: Add Citations
  → Link each claim to source
  → Evaluate: All claims cited? → Yes, continue
  
Step 6: Format & Publish
  → Final polish, PDF export
  → SUCCESS: Report ready
```

Every step has clear:
- **Input** (what we're processing)
- **Logic** (what the tool does)
- **Output** (result)
- **Evaluation** (is it acceptable?)
- **Decision** (continue? retry? branch? fail?)

---

## Pros: Why Choose Orchestration?

### 1. Predictability & Reproducibility

**Orchestration is deterministic.** Given the same input, you get the same output and execution path.

```python
# Run 1: Report on "AI trends"
# → Fetch → Analyze → Synthesize → Format
# Result: 2100-word report with 18 citations

# Run 2: Report on "AI trends" (same input)
# → Fetch → Analyze → Synthesize → Format
# Result: 2100-word report with 18 citations (IDENTICAL)
```

**Choreography** might produce different outputs because agents react to events in a different order.

✓ **Benefit**: Testing, validation, and regression detection become trivial

---

### 2. Complete Audit Trail

Every decision is logged explicitly:

```
Step 1: PLANNING
  - plan_text: "Fetch data → Analyze → Write → Format"
  - timestamp: 2024-06-26 14:23:45
  - status: SUCCESS

Step 2: FETCHING_DATA
  - queries: ["AI machine learning trends 2024", ...]
  - results_count: 24
  - timestamp: 2024-06-26 14:23:52
  - duration: 7s
  - status: SUCCESS

Step 3: ANALYZING
  - input_count: 24
  - output_facts: 156
  - timestamp: 2024-06-26 14:24:10
  - duration: 18s
  - status: SUCCESS
  
  → Evaluation: "156 facts from 24 sources → ratio 6.5:1 → ACCEPTABLE"
  → Decision: "Proceed to synthesize"

Step 4: SYNTHESIZING
  - ...
```

✓ **Benefit**: Full observability — you see exactly what the system did and why

---

### 3. Easier Debugging & Error Recovery

When something fails, you know exactly where:

```
FAILURE at Step 3 (ANALYZING)
  - Error: "Insufficient facts extracted (only 8 facts)"
  - Expected: ≥20 facts
  - Last successful step: Step 2 (24 sources fetched)
  
Recovery options:
  a) Retry Step 3 with different parameters
  b) Rerun Steps 2-3 with expanded search
  c) Skip to Step 4 with partial data
  d) Abort and report failure with context
```

In choreography, agents react autonomously — harder to trace causality.

✓ **Benefit**: Debugging is systematic, not detective work

---

### 4. Strong Guarantees & Validation

The Controller can enforce invariants at each step:

```python
@controller.step(name="fetch_data")
def fetch_data(query):
    results = search_tool(query)
    
    # Validate before proceeding
    assert len(results) >= MIN_RESULTS, f"Got {len(results)}, need ≥{MIN_RESULTS}"
    assert all(has_timestamp(r) for r in results), "Missing timestamps"
    assert all(has_source(r) for r in results), "Missing sources"
    
    return results  # Only reached if all assertions pass
```

✓ **Benefit**: Catch issues early, fail loudly, never silently degrade

---

### 5. Easy to Explain & Teach

Orchestration is intuitive — like a recipe:

1. **Preheat** (validate inputs)
2. **Mix dry ingredients** (fetch data)
3. **Combine wet ingredients** (analyze)
4. **Mix together** (synthesize)
5. **Bake** (format)
6. **Serve** (publish)

Each step is explicit and sequential. Stakeholders understand it immediately.

✓ **Benefit**: Faster onboarding, better stakeholder communication

---

## Cons: Limitations of Orchestration

### 1. Inflexibility & Rigidity

Once the workflow is defined, it's hard to adapt:

```python
# Original plan: Fetch → Analyze → Synthesize → Format

# What if new requirement arrives mid-execution:
# "Use French language for key terms"?
# → Options:
#   a) Restart entire workflow
#   b) Modify plan mid-execution (risky, might break state)
#   c) Add French post-processing (workaround, not elegant)
```

Choreography agents would **naturally adapt** — they react to events. Orchestration requires **explicit code changes**.

✗ **Problem**: Workflows become brittle under changing requirements

---

### 2. Single Point of Failure

The Controller is the bottleneck:

```
If Controller fails:
  - Entire workflow halts
  - In-progress steps orphaned
  - No agent can recover independently
  - Requires manual intervention to restart

If Choreography agent fails:
  - Other agents continue
  - Event remains in bus
  - System eventually detects missing response
  - Recovery is automatic (retry, timeout)
```

✗ **Problem**: Low fault tolerance for distributed systems

---

### 3. Tight Coupling

The Controller knows everything about every tool:

```python
class Controller:
    async def orchestrate(self, task):
        plan = await self.plan_tool(task)        # Step 1 logic
        data = await self.fetch_tool(plan)       # Step 2 logic
        facts = await self.analyze_tool(data)    # Step 3 logic
        
        # The Controller is tightly coupled to each tool's:
        # - Interface (what params? what format?)
        # - Semantics (what does "analyze" mean?)
        # - Failure modes (what errors can it raise?)
```

Adding a new step or tool requires **modifying the Controller** — no way to extend without touching core logic.

In choreography, you just emit a new event type and let agents decide if they care.

✗ **Problem**: Adding features requires modifying working code

---

### 4. Scaling Issues

Orchestration doesn't scale to many parallel tasks:

```
Orchestration:
  Task 1 → Controller → [Fetch] → [Analyze] → [Synthesize] (35 seconds)
  Task 2 → Controller → waiting...
  Task 3 → Controller → waiting...
  Task 4 → Controller → waiting...
```

One Controller = one task at a time = bottleneck.

Choreography scales naturally:
```
Choreography:
  Task 1 → WebSearcher reads event, processes
  Task 2 → Analyzer reads event, processes
  Task 3 → Synthesizer reads event, processes
  
  All running **concurrently** via async event bus.
```

✗ **Problem**: Limited throughput, poor scalability

---

### 5. Loss of Emergent Behaviors

Orchestration is **rigid by design**. You specify exactly what to do.

Choreography is **adaptive by design**. Agents respond to circumstances:

```
Choreography example:
  Drafter writes poor report
  → Critic flags quality issue
  → SearchAgent launches more research
  → Analyzer extracts different insights
  → Drafter re-writes with new perspective
  → Workflow adapts dynamically
```

With Orchestration:
```
Orchestration example:
  Drafter writes poor report
  → Critic flags quality issue
  → ??? What do we do?
  → Option: Restart workflow (lose prior work)
  → Option: Patch Controller code mid-execution (risky)
  → Option: Accept poor output (defeat the purpose)
```

✗ **Problem**: Cannot adapt to unexpected situations

---

## Decision Matrix: Orchestration vs. Choreography

| Criterion | Orchestration | Choreography |
|-----------|---------------|--------------|
| **Predictability** | ✅ Deterministic | ⚠️ Emergent |
| **Flexibility** | ⚠️ Rigid | ✅ Adaptive |
| **Debugging** | ✅ Clear causality | ⚠️ Distributed causality |
| **Scalability** | ⚠️ Single-point bottleneck | ✅ Parallel agents |
| **Fault Tolerance** | ⚠️ Centralized risk | ✅ Isolated failures |
| **Observability** | ✅ Complete audit trail | ⚠️ Implicit interactions |
| **Time to Market** | ✅ Fast (known workflow) | ⚠️ Slow (design feedback loops) |
| **Learning & Adaptation** | ⚠️ Requires code changes | ✅ Agents learn naturally |

### When to Choose Orchestration

✅ Use Orchestration when:

1. **Workflow is well-defined** — You know the exact steps before starting
2. **Results must be reproducible** — Same input must produce same output
3. **Debugging is critical** — You need complete audit trails
4. **Throughput is low** — Few concurrent tasks
5. **Requirements are stable** — Workflow rarely changes
6. **Compliance matters** — Auditors need clear decision records

**Examples:**
- Report generation pipelines
- Data ETL workflows
- Form processing (multi-step)
- Document classification & routing
- Invoice processing with human escalation

### When to Choose Choreography

✅ Use Choreography when:

1. **Problem is complex or emergent** — You can't predict exact steps
2. **Autonomy matters** — Agents should react independently
3. **Scalability is critical** — Many concurrent workflows
4. **Fault tolerance is essential** — Failures must be isolated
5. **Requirements are uncertain** — Workflow evolves based on data
6. **Learning matters** — System should adapt over time

**Examples:**
- Multi-agent research teams
- Customer service (routing, escalation, resolution)
- Content moderation (human + AI agents collaborating)
- Real-time bidding platforms
- Crisis management systems

---

## Design Patterns for Orchestration

### Pattern 1: Sequential Pipeline

Simplest case — steps execute in order:

```python
class ReportOrchestrator(Controller):
    async def orchestrate(self, topic):
        return (
            await self.step("plan", topic)
            .then(lambda plan: self.step("fetch", plan))
            .then(lambda data: self.step("analyze", data))
            .then(lambda facts: self.step("synthesize", facts))
            .then(lambda draft: self.step("cite", draft))
            .then(lambda report: self.step("format", report))
        )
```

---

### Pattern 2: Conditional Branching

Evaluate output and take different paths:

```python
async def orchestrate(self, task):
    plan = await self.step("plan", task)
    
    # Branch based on plan complexity
    if plan.complexity > HIGH:
        data = await self.step("fetch_extensive", task)
    else:
        data = await self.step("fetch_basic", task)
    
    facts = await self.step("analyze", data)
    
    # Branch based on facts quality
    if len(facts) < MINIMUM_FACTS:
        facts = await self.step("expand_search", task)
    
    return await self.step("synthesize", facts)
```

---

### Pattern 3: Retry with Backoff

Evaluate failures and retry intelligently:

```python
async def orchestrate(self, task):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = await self.step("fetch", task)
            
            # Evaluate success
            if len(result) >= MIN_REQUIRED:
                return result
            else:
                raise ValueError(f"Insufficient results: {len(result)}")
                
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                await asyncio.sleep(wait_time)
            else:
                raise  # Final attempt failed, give up
```

---

### Pattern 4: Checkpoint & Restore

Save state for recovery and replay:

```python
class PersistentController(Controller):
    async def orchestrate(self, task, checkpoint_id=None):
        state = await self.load_checkpoint(checkpoint_id) if checkpoint_id else {}
        
        for step_name in self.workflow_steps:
            if step_name in state:
                continue  # Skip completed steps
            
            result = await self.step(step_name, state.get(step_name + "_input"))
            state[step_name] = result
            
            await self.save_checkpoint(checkpoint_id, state)
        
        return state
```

---

## Implementation Patterns

### The Controller Class Structure

```python
class Controller:
    def __init__(self, tools: Dict[str, Callable]):
        self.tools = tools
        self.state = {}
        self.history = []
    
    async def step(
        self,
        name: str,
        input_data: Any,
        evaluate_fn: Callable[[Any], bool] = None,
    ) -> Any:
        """Execute one step and evaluate result."""
        
        # Execute
        result = await self.tools[name](input_data)
        
        # Evaluate (if provided)
        if evaluate_fn and not evaluate_fn(result):
            raise StepEvaluationError(f"Step {name} evaluation failed")
        
        # Record
        self.history.append({
            "step": name,
            "input": input_data,
            "output": result,
            "timestamp": datetime.now(),
            "status": "success"
        })
        
        self.state[name] = result
        return result
    
    async def orchestrate(self, task: str) -> Dict:
        """Main orchestration loop — override in subclasses."""
        raise NotImplementedError
```

---

## Comparison with Choreography (ADR-2.1)

| Aspect | Orchestration (This ADR) | Choreography (ADR-2.1) |
|--------|-------------------------|------------------------|
| **Control Flow** | Explicit (if-then-else) | Implicit (event-driven) |
| **Agent Autonomy** | Low (Controller decides) | High (agents decide) |
| **Coupling** | Tight (Controller knows all) | Loose (agents know events) |
| **Failure Mode** | Cascading (Controller fails) | Isolated (agent fails alone) |
| **Debuggability** | High (linear trace) | Medium (event correlation) |
| **Scalability** | Low (bottleneck) | High (parallel) |
| **Adaptation** | Requires code change | Natural (emergent) |
| **Predictability** | High (deterministic) | Low (emergent) |

**The fundamental trade-off:**
- **Orchestration**: Control & Predictability at cost of Flexibility
- **Choreography**: Flexibility & Adaptation at cost of Predictability

Choose based on your problem's nature:
- **Well-defined problem** → Orchestration
- **Emergent problem** → Choreography

---

## Production Patterns

### 1. Observability: Logging & Tracing

```python
class ObservableController(Controller):
    async def step(self, name, input_data):
        logger.info(f"Starting step: {name}")
        start_time = time.time()
        
        try:
            result = await self.tools[name](input_data)
            duration = time.time() - start_time
            
            logger.info(f"Step {name} completed in {duration}s")
            tracer.record_span(
                name=name,
                duration=duration,
                status="success"
            )
            
            return result
        except Exception as e:
            logger.error(f"Step {name} failed: {e}")
            tracer.record_span(
                name=name,
                duration=time.time() - start_time,
                status="error",
                error=str(e)
            )
            raise
```

### 2. Resilience: Circuit Breaker

```python
class ResilientController(Controller):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.circuit_breaker = {}
    
    async def step(self, name, input_data):
        if self.circuit_breaker.get(name, {}).get("open"):
            raise CircuitBreakerOpenError(f"Step {name} is open")
        
        try:
            return await super().step(name, input_data)
        except Exception as e:
            self.circuit_breaker[name] = {"open": True}
            raise
```

### 3. Monitoring: Metrics

```python
class MetricsController(Controller):
    async def step(self, name, input_data):
        result = await super().step(name, input_data)
        
        metrics.record_counter(
            f"orchestration.step.{name}.success"
        )
        metrics.record_histogram(
            f"orchestration.step.{name}.duration",
            time.time() - self.history[-1]["timestamp"]
        )
        
        return result
```

---

## References

- **ADR-2.1**: Choreography: Event-Driven Agility (contrasting pattern)
- **WP-2.2**: State Management in Single-Agent Loop (state tracking)
- **WP-1.7**: Tracing with LangSmith (observability)
- **LangGraph**: Official implementation patterns
- **Temporal**: Workflow orchestration patterns
- **Apache Airflow**: DAG-based orchestration design

---

## Related Patterns

- **Saga Pattern**: Long-running transaction with compensating actions
- **State Machine**: Explicit state transitions (WP-2.2)
- **Pipeline Pattern**: Sequential processing (similar to orchestration)
- **Pub/Sub Pattern**: Choreography's complement (ADR-2.1)

---

## Conclusion

**Orchestration is the right choice when you value control, predictability, and observability over flexibility and scalability.**

Use it for:
- Well-defined workflows with clear steps
- High-compliance scenarios requiring audit trails
- Debugging-critical systems
- Low-throughput, high-reliability scenarios

Don't use it for:
- Emergent or adaptive workflows
- High-throughput, scalability-critical systems
- Complex multi-agent coordination
- Systems that need to learn and adapt

**Next step**: See `controller_orchestration_agent.py` for a complete implementation of a Report Generator orchestrator.
