# WP-2.7: Checkpointing & Human-in-the-Loop with LangGraph

**Work Product**: Add human approval gates to LangGraph workflows using checkpointers and interrupts  
**Status**: Complete | Production-Ready  
**Duration**: 2-2.5 hours  
**Prerequisites**: [WP-2.6 LangGraph Introduction](WP-2.6-Introduction-to-LangGraph-for-Stateful-Graphs.md) | [WP-2.3 Orchestration Pattern](WP-2.3-Orchestration-Pattern.md)

---

## Overview

In [WP-2.6](WP-2.6-Introduction-to-LangGraph-for-Stateful-Graphs.md), you learned that **LangGraph abstracts state machine infrastructure**, giving you automatic persistence and observability out of the box.

This work product introduces the **critical enterprise requirement** LangGraph was designed to solve: **human approval gates before irreversible actions**.

Imagine a report generation workflow that:
1. Plans content
2. Fetches sources
3. Generates draft
4. **BREAKPOINT**: Waits for human approval before sending to stakeholders
5. Sends finalized report
6. Logs completion

Traditional approaches require you to:
- Stop the workflow mid-execution
- Serialize state to a database
- Poll for human approval
- Resume from the saved state when approved
- Handle divergent paths (approve, reject, modify)

**LangGraph's solution**: Checkpointers + interrupts handle all this for you.

### Key Takeaways

- **The problem**: Human-in-the-loop workflows are complex to implement correctly
- **The solution**: LangGraph checkpointers automatically persist state at breakpoints; the framework handles resumption
- **The pattern**: Declare where breakpoints occur; approval logic is separated from orchestration
- **The benefit**: Guardrails, audit trails, and branching strategies without custom infrastructure

---

## Section 1: The Problem – Enterprise Guardrails

### The Pain Point

Most AI systems operate autonomously: invoke → process → return result. But critical systems need human oversight:

- **Healthcare**: Approval before sending a diagnosis recommendation
- **Finance**: Approval before transferring funds or executing trades
- **Legal**: Approval before sending contracts or settlement agreements
- **Content**: Approval before publishing to external APIs
- **Customer Service**: Escalation to human agent on complex queries

Without checkpointing, implementing this requires:

```python
# Anti-pattern: Manual state serialization
async def workflow_without_checkpointing(task: str) -> str:
    # Step 1: Generate draft
    draft = await generate_draft(task)
    
    # Step 2: MANUAL state save to DB
    session_id = str(uuid.uuid4())
    db.save_session({
        "id": session_id,
        "state": {
            "task": task,
            "draft": draft,
            "status": "pending_approval"
        }
    })
    
    # Step 3: Poll for approval (blocking, wasteful)
    for attempt in range(3600):  # 1-hour poll loop
        approval = db.check_approval(session_id)
        if approval:
            break
        await asyncio.sleep(1)  # Poll every second
    
    # Step 4: Deserialize state manually
    session = db.load_session(session_id)
    draft = session["state"]["draft"]
    
    # Step 5: Send report
    result = await send_report(draft)
    
    # Step 6: MANUAL cleanup
    db.delete_session(session_id)
    
    return result
```

**Problems with this approach:**

1. **Complex state management**: Must manually serialize/deserialize
2. **Inefficient**: Polling wastes resources; blocking coroutines
3. **Error-prone**: Race conditions, forgetting to clean up sessions
4. **No branching**: What if user rejects? No elegant recovery
5. **No audit trail**: Hard to track approval history
6. **Scaling issues**: Database becomes bottleneck; doesn't work in distributed systems

### Real-World Cost

Consider a financial approval system handling 1000 workflows/day:
- **Manual approach**: 1000 coroutines polling every second = 86,400 unnecessary DB queries per day
- **Memory**: Each suspended workflow holds state in memory = 1-10 MB × 1000 = 1-10 GB of wasted RAM
- **Latency**: 1-second polling introduces 0.5-second average latency to approval
- **Bugs**: Edge cases in state serialization cause ~2-3% of workflows to hang or corrupt

**LangGraph solution**: 0 polling, efficient state checkpoints, automatic resumption, built-in audit trail.

### Concrete Example: Workflow without Guardrails

Here's what a *traditional* async workflow looks like—no checkpointing:

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

async def simple_report_workflow(query: str) -> str:
    """
    Traditional workflow: No human approval.
    
    Problem: If this fails after 4 steps, you lose all progress.
    Problem: No way to add human approval between steps.
    """
    llm = ChatOpenAI(model="gpt-4")
    
    # Step 1: Generate plan
    plan_prompt = ChatPromptTemplate.from_template(
        "Create a 3-step plan for: {query}"
    )
    plan_chain = plan_prompt | llm
    plan = await plan_chain.ainvoke({"query": query})
    
    # Step 2: Generate draft report
    draft_prompt = ChatPromptTemplate.from_template(
        "Write a report based on this plan: {plan}"
    )
    draft_chain = draft_prompt | llm
    draft = await draft_chain.ainvoke({"plan": plan})
    
    # Step 3: Refine report
    refine_prompt = ChatPromptTemplate.from_template(
        "Improve this draft with citations: {draft}"
    )
    refine_chain = refine_prompt | llm
    refined = await refine_chain.ainvoke({"draft": draft})
    
    # Step 4: PROBLEM - No approval gate!
    # What if we need human review before sending?
    # No way to pause, save state, and resume here.
    
    # Step 5: Send report (irreversible action!)
    await send_to_stakeholders(refined)
    
    return refined
```

**What's missing**: Between steps 3-4, you need to:
1. Save all state
2. Wait for human approval
3. Resume from checkpoint
4. Handle rejection (revert or branch)

---

## Section 2: Proposed Solution – LangGraph Checkpointer + Interrupts

### High-Level Architecture

LangGraph introduces **three key abstractions**:

```mermaid
graph TD
    Workflow["🕸️ LangGraph Workflow"]
    
    N1["📌 Node<br/>Step 1"]
    N2["📌 Node<br/>Step 2"]
    N3["📌 Node<br/>Step 3"]
    
    Router["🔀 Conditional<br/>Routing"]
    
    Resume["▶️ Resume<br/>Approved"]
    Interrupt["⏸️ Interrupt<br/>Waiting for Human"]
    
    Checkpointer["💾 Checkpointer<br/>State Storage"]
    
    Workflow --> N1
    Workflow --> N2
    Workflow --> N3
    
    N1 --> Router
    N2 --> Router
    N3 --> Router
    
    Router -->|Resume| Resume
    Router -->|Interrupt| Interrupt
    
    Resume --> Checkpointer
    Interrupt --> Checkpointer
    
    style Workflow fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style N1 fill:#e8f5e9
    style N2 fill:#e8f5e9
    style N3 fill:#e8f5e9
    style Router fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style Resume fill:#c8e6c9
    style Interrupt fill:#ffb74d
    style Checkpointer fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
```

**Three Key Concepts:**

1. **Nodes**: Execute a step, return updated state
2. **Edges**: Routing between nodes (conditional or deterministic)
3. **Checkpointer**: Persists state after each node execution, enables interrupts

### Interrupts: The Breakpoint Mechanism

An **interrupt** pauses execution at a specific node and returns control to the user:

```python
# Declare an interrupt before a critical action
graph = StateGraph(State)
graph.add_node("send_email", send_email_node)
graph.add_conditional_edges(
    "generate_draft",
    should_send_email,  # Routes to "send_email" or END
    {"send_email": "send_email", END: END}
)

# Add interrupt at the critical node
graph.add_node(
    "human_approval",
    noop,  # Do nothing, just create a breakpoint
    interrupt_before=["send_email"]  # Pause BEFORE send_email
)
```

When execution reaches the interrupt:
1. State is checkpointed to storage (database, filesystem, etc.)
2. Execution pauses
3. User can review state in the dashboard or API
4. User approves/rejects
5. Workflow resumes from checkpoint

---

## Section 3: The Composable Pattern

### Runnable Interface

LangGraph's `StateGraph` is composable via the Runnable protocol:

```python
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import Runnable, RunnableConfig
from typing_extensions import TypedDict
from typing import Optional

# 1. Define State (TypedDict)
class ApprovalState(TypedDict):
    """State for approval workflow."""
    task: str
    draft: str
    approval_status: Optional[str]  # "pending" | "approved" | "rejected"
    send_result: Optional[str]

# 2. Define Nodes (async functions that update state)
async def generate_draft(state: ApprovalState) -> ApprovalState:
    """Generate a draft (simulated)."""
    state["draft"] = f"Draft for: {state['task']}"
    return state

async def send_report(state: ApprovalState) -> ApprovalState:
    """Send the report (only if approved)."""
    if state.get("approval_status") != "approved":
        state["send_result"] = "Skipped (not approved)"
        return state
    
    state["send_result"] = f"Sent: {state['draft']}"
    return state

# 3. Define Routing Logic
def route_to_approval(state: ApprovalState) -> str:
    """Decide whether to proceed or wait for approval."""
    # This is a conditional edge
    # In real use, this might check approval_status from database
    return "send_report" if state.get("approval_status") == "approved" else "wait_for_approval"

# 4. Build the Graph
def build_approval_graph():
    graph = StateGraph(ApprovalState)
    
    # Add nodes
    graph.add_node("generate_draft", generate_draft)
    graph.add_node("send_report", send_report)
    
    # Add edges
    graph.add_edge(START, "generate_draft")
    graph.add_conditional_edges(
        "generate_draft",
        route_to_approval,
        {"send_report": "send_report", "wait_for_approval": END}
    )
    graph.add_edge("send_report", END)
    
    # Add checkpointer for state persistence
    from langgraph.checkpoint.sqlite import SqliteSaver
    checkpointer = SqliteSaver(conn=":memory:")
    
    # Compile with checkpointer and interrupt configuration
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["send_report"]  # Pause before sending
    )

# 5. Compose into larger workflows
from langchain_core.runnables import RunnableSequence

approval_workflow = build_approval_graph()

# Can be composed: workflow | other_runnable
composed = approval_workflow | some_downstream_processor
```

**Composability Benefits:**

- **Reusable**: The approval workflow is a Runnable, can be used anywhere
- **Chainable**: Compose with other runnables using `|` operator
- **Testable**: Standard Runnable interface, same testing approach as WP-1.3
- **Observable**: LangSmith automatically traces graph execution

### Interface Definition

```python
# Input type
class ApprovalWorkflowInput(BaseModel):
    task: str = Field(..., description="The task to execute with approval")

# Output type
class ApprovalWorkflowOutput(BaseModel):
    task: str
    draft: str
    approval_status: str
    send_result: str
    execution_thread_id: str  # Thread ID for resumption
```

---

## Section 4: Observability & Tracing

### What LangSmith Shows

When you enable LangSmith tracing, each node execution creates a span:

```
Workflow Trace Structure
├─ StateGraph Execution
│  ├─ Node: generate_draft
│  │  ├─ Input: {task: "..."}
│  │  ├─ Output: {draft: "..."}
│  │  └─ Duration: 2.1s
│  │
│  ├─ Node: [INTERRUPT - Waiting for Approval]
│  │  ├─ Status: paused
│  │  ├─ Checkpoint ID: abc123
│  │  └─ Waiting since: 2024-06-28 10:15:00
│  │
│  └─ [User approves via API or dashboard]
│     └─ Resume from checkpoint
│        ├─ Node: send_report
│        │  ├─ Input: {task: "...", draft: "...", approval_status: "approved"}
│        │  ├─ Output: {send_result: "Sent: ..."}
│        │  └─ Duration: 1.2s
│        │
│        └─ End: workflow_complete
```

### Enabling Tracing

```python
import os
from langgraph.checkpoint.sqlite import SqliteSaver

# Enable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGSMITH_API_KEY"] = "your-key"

# Create checkpointer
checkpointer = SqliteSaver(conn=":memory:")

# Build graph with checkpointer
graph = StateGraph(ApprovalState)
# ... add nodes and edges ...
compiled = graph.compile(checkpointer=checkpointer, interrupt_before=["send_report"])

# Execute with tracing enabled
result = compiled.invoke(
    {"task": "Write a report on AI"},
    config={"configurable": {"thread_id": "workflow-123"}}
)
```

Every execution creates a trace visible in LangSmith dashboard showing:
- Timeline of node executions
- State changes at each step
- Interrupt points and how long user took to approve
- Branching decisions (approved vs. rejected paths)

### Custom Metadata

LangGraph automatically captures:
- `thread_id`: Unique identifier for this workflow execution
- `checkpoint_id`: Identifier for the persisted state
- `interrupt_status`: "executing", "paused", or "completed"
- Node execution times and state transitions

---

## Section 5: Implementation Guide

### Step 1: Define State Schema

```python
from typing_extensions import TypedDict
from typing import Optional, List, Dict

class EmailApprovalState(TypedDict):
    """State for email approval workflow."""
    recipient: str
    subject: str
    body: str
    generated_at: str
    approval_status: Optional[str]  # "pending" | "approved" | "rejected"
    approval_notes: Optional[str]  # User feedback
    send_timestamp: Optional[str]
    error_message: Optional[str]
```

### Step 2: Define Node Functions

Each node is an async function that:
- Takes state as input
- Returns updated state
- No side effects until after approval

```python
import asyncio
from datetime import datetime
from typing import Any

async def generate_email(state: EmailApprovalState) -> EmailApprovalState:
    """Generate email content (no sending yet)."""
    # Simulate LLM call
    await asyncio.sleep(0.5)
    
    state["body"] = f"""
    Dear {state['recipient']},
    
    Thank you for reaching out. Based on your inquiry, here's our response:
    [Generated content would go here]
    
    Best regards,
    Customer Service Team
    """
    state["generated_at"] = datetime.now().isoformat()
    
    return state

async def send_email(state: EmailApprovalState) -> EmailApprovalState:
    """Send email only if approved."""
    # Critical: Only execute if approved
    if state.get("approval_status") != "approved":
        state["error_message"] = "Email not sent (not approved)"
        return state
    
    try:
        # Simulate email sending
        await asyncio.sleep(0.2)
        state["send_timestamp"] = datetime.now().isoformat()
        state["error_message"] = None
    except Exception as e:
        state["error_message"] = f"Send failed: {str(e)}"
    
    return state
```

### Step 3: Define Routing Logic

```python
def route_after_generation(state: EmailApprovalState) -> str:
    """
    Route based on approval status.
    
    Returns node name to execute next:
    - "send_email" if approved
    - END if rejected or still pending
    """
    status = state.get("approval_status")
    
    if status == "approved":
        return "send_email"
    elif status == "rejected":
        return "log_rejection"
    else:
        # Status is None (pending) or unknown
        # Interrupt handler will pause here
        return END
```

### Step 4: Build and Compile Graph

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

# Create state machine
graph = StateGraph(EmailApprovalState)

# Add nodes
graph.add_node("generate_email", generate_email)
graph.add_node("send_email", send_email)
graph.add_node("log_rejection", log_rejection)

# Add edges
graph.add_edge(START, "generate_email")
graph.add_conditional_edges(
    "generate_email",
    route_after_generation,
    {
        "send_email": "send_email",
        "log_rejection": "log_rejection",
        END: END
    }
)
graph.add_edge("send_email", END)
graph.add_edge("log_rejection", END)

# Create persistent checkpointer
conn = sqlite3.connect("checkpoints.db")
checkpointer = SqliteSaver(conn=conn)

# Compile with interrupt configuration
workflow = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["send_email"]  # Pause before sending
)
```

### Step 5: Execute and Handle Interrupts

```python
async def run_workflow_with_approval(recipient: str, subject: str) -> Dict[str, Any]:
    """
    Execute workflow with human approval gate.
    
    Returns when workflow completes or pauses at interrupt.
    """
    # Initial state
    initial_state = {
        "recipient": recipient,
        "subject": subject,
        "body": None,
        "generated_at": None,
        "approval_status": None,
        "approval_notes": None,
        "send_timestamp": None,
        "error_message": None,
    }
    
    # Thread ID ties together all executions of this workflow
    thread_id = "email-123"
    config = {
        "configurable": {"thread_id": thread_id}
    }
    
    # FIRST EXECUTION: Generates email, then pauses at interrupt
    print("Step 1: Generating email...")
    result = workflow.invoke(initial_state, config=config)
    
    print(f"Generated: {result['body'][:100]}...")
    print("Workflow paused at send_email interrupt")
    print(f"Checkpoint ID: {config['configurable']['thread_id']}")
    
    # AT THIS POINT: User reviews generated email in UI/dashboard
    # User can approve, reject, or request modifications
    
    # SIMULATE USER APPROVAL
    print("\nStep 2: User approves via dashboard...")
    
    # Get current state from checkpoint
    config_with_values = {
        "configurable": {"thread_id": thread_id}
    }
    current_state = workflow.get_state(config_with_values)
    
    # Update approval status
    current_state.values["approval_status"] = "approved"
    
    # SECOND EXECUTION: Resume from checkpoint, sends email
    print("Step 3: Resuming workflow with approval...")
    final_result = workflow.invoke(
        None,  # None means "resume from checkpoint"
        config=config_with_values
    )
    
    print(f"Email sent at: {final_result['send_timestamp']}")
    return final_result
```

### Step 6: Handle Rejections and Branching

```python
async def run_workflow_with_rejection() -> Dict[str, Any]:
    """Demonstrate rejection workflow."""
    thread_id = "email-456"
    config = {"configurable": {"thread_id": thread_id}}
    
    # FIRST EXECUTION: Generate
    workflow.invoke(
        {
            "recipient": "user@example.com",
            "subject": "Important Update",
            "body": None,
            "approval_status": None,
            "approval_notes": None,
        },
        config=config
    )
    
    # USER REJECTS
    current_state = workflow.get_state(config)
    current_state.values["approval_status"] = "rejected"
    current_state.values["approval_notes"] = "Body too generic, please revise"
    
    # SECOND EXECUTION: Follow rejection path
    result = workflow.invoke(None, config=config)
    print(f"Result: {result['error_message']}")
    
    # NOW: Could modify state and re-submit for approval
    current_state.values["approval_status"] = None  # Reset
    current_state.values["body"] = "[Updated body content]"  # Modify
    
    # THIRD EXECUTION: Resubmit
    result = workflow.invoke(None, config=config)
    print(f"Resubmitted email state: {result['approval_status']}")
```

---

## Section 6: Trade-Off Analysis

| Dimension | LangGraph Checkpointer | Manual DB Serialization | Polling + Queue | No Approval |
|-----------|----------------------|----------------------|-----------------|------------|
| **State Persistence** | Automatic at each node | Manual serialize/deserialize | Requires queue | N/A |
| **Resumption** | One API call | Load from DB + manual deserialization | Dequeue + resume logic | N/A |
| **Approval Latency** | 0 (event-driven) | ~1-3s per poll | Variable (queue dependent) | N/A |
| **Memory Overhead** | Minimal (state on disk) | 1-10 MB per suspended workflow | Minimal | None |
| **Audit Trail** | Built-in (thread history) | Manual logging required | Queue logs | None |
| **Branching Support** | Native (conditional edges) | Custom if/else logic | Manual state updates | N/A |
| **Distributed Systems** | ✓ (DB-backed) | ✓ (DB-backed) | ✓ (Queue-backed) | ✗ |
| **Cost (1000 workflows)** | ~$50/mo (DB) | ~$200/mo (polling costs) | ~$100/mo (queue) | $0 |
| **Implementation Complexity** | Low (framework) | Medium (custom infra) | Medium (queue setup) | Low |
| **Production Readiness** | ✓ | Partial | ✓ | ✗ (no guardrails) |

**When to use each approach:**

- **LangGraph Checkpointer**: Default choice for new workflows; handles 95% of use cases
- **Manual DB Serialization**: Legacy systems; need custom approval logic beyond LangGraph's model
- **Polling + Queue**: Message-driven architectures (Kafka, RabbitMQ); high-throughput scenarios
- **No Approval**: Internal tools; non-critical workflows; low-risk operations

---

## Section 7: Error Handling & Resilience

### Failure Modes

```python
from enum import Enum

class ApprovalFailureMode(Enum):
    """Possible failure scenarios in approval workflow."""
    
    # Input Validation
    INVALID_EMAIL = "Email address validation failed"
    MISSING_RECIPIENT = "Recipient field is empty"
    BODY_TOO_LONG = "Email body exceeds maximum length"
    
    # Execution Failures
    LLM_ERROR = "LLM call failed (API down, rate limited, etc.)"
    CHECKPOINT_ERROR = "Failed to save state to checkpoint storage"
    
    # Approval Failures
    APPROVAL_TIMEOUT = "Approval not received within timeout window"
    INVALID_APPROVAL_STATUS = "Approval status is not 'approved'/'rejected'"
    USER_CANCELLED = "User cancelled the workflow during approval"
    
    # Send Failures
    EMAIL_SERVICE_ERROR = "Email sending service returned error"
    RETRY_EXHAUSTED = "Retry attempts exceeded maximum"
    
    # Recovery
    STATE_CORRUPTED = "Checkpoint state is invalid"
    THREAD_NOT_FOUND = "Thread ID not found in checkpoint storage"
```

### Error Handling Implementation

```python
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def generate_email_safe(state: EmailApprovalState) -> EmailApprovalState:
    """Generate email with comprehensive error handling."""
    try:
        # Validate input
        if not state.get("recipient"):
            state["error_message"] = ApprovalFailureMode.MISSING_RECIPIENT.value
            return state
        
        if len(state.get("body", "")) > 10000:
            state["error_message"] = ApprovalFailureMode.BODY_TOO_LONG.value
            return state
        
        # Execute with retry
        max_retries = 3
        backoff_seconds = 1
        
        for attempt in range(1, max_retries + 1):
            try:
                # Simulate LLM call
                await asyncio.sleep(0.5)
                state["body"] = f"Generated email for {state['recipient']}"
                state["error_message"] = None
                return state
                
            except Exception as e:
                logger.error(f"Attempt {attempt}/{max_retries} failed: {e}")
                
                if attempt < max_retries:
                    # Exponential backoff with jitter
                    wait_time = backoff_seconds * (2 ** (attempt - 1)) + random.uniform(0, 1)
                    await asyncio.sleep(wait_time)
                else:
                    # All retries exhausted
                    state["error_message"] = f"{ApprovalFailureMode.LLM_ERROR.value}: {str(e)}"
                    return state
    
    except Exception as unexpected:
        logger.critical(f"Unexpected error: {unexpected}")
        state["error_message"] = f"Unexpected error: {str(unexpected)}"
        return state

async def send_email_safe(state: EmailApprovalState) -> EmailApprovalState:
    """Send email with retry and graceful degradation."""
    # Check approval first
    if state.get("approval_status") != "approved":
        state["error_message"] = "Approval required before sending"
        return state
    
    max_retries = 3
    
    for attempt in range(1, max_retries + 1):
        try:
            # Simulate send
            await asyncio.sleep(0.2)
            
            # Success
            state["send_timestamp"] = datetime.now().isoformat()
            state["error_message"] = None
            logger.info(f"Email sent successfully to {state['recipient']}")
            return state
            
        except Exception as e:
            logger.error(f"Send attempt {attempt}/{max_retries} failed: {e}")
            
            if attempt == max_retries:
                # All retries exhausted, graceful degradation
                state["error_message"] = f"{ApprovalFailureMode.EMAIL_SERVICE_ERROR.value}: {str(e)}"
                # Option 1: Queue for retry later
                # Option 2: Log for manual review
                # Option 3: Escalate to human
                return state
            
            # Wait before retry (exponential backoff)
            await asyncio.sleep(2 ** attempt)
    
    return state
```

### Timeout and Approval Expiration

```python
import json
from datetime import datetime, timedelta

class ApprovalTimeoutHandler:
    """Handle approval timeouts."""
    
    def __init__(self, timeout_hours: int = 24):
        self.timeout_hours = timeout_hours
    
    async def check_approval_expired(
        self,
        thread_id: str,
        checkpoint_creation_time: datetime
    ) -> bool:
        """Check if approval window has expired."""
        elapsed = datetime.now() - checkpoint_creation_time
        timeout = timedelta(hours=self.timeout_hours)
        
        if elapsed > timeout:
            logger.warning(
                f"Approval for thread {thread_id} expired "
                f"after {elapsed.total_seconds():.0f}s"
            )
            return True
        
        return False
    
    async def handle_timeout(state: EmailApprovalState) -> EmailApprovalState:
        """Handle expired approval window."""
        state["error_message"] = ApprovalFailureMode.APPROVAL_TIMEOUT.value
        state["approval_status"] = "expired"
        return state
```

---

## Section 8: Production Considerations

### Deployment Patterns

**Single-Instance (Development/Small Scale)**
```python
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

# Use local SQLite (not suitable for distributed systems)
conn = sqlite3.connect("checkpoints.db")
checkpointer = SqliteSaver(conn)
```

**Distributed (Production)**
```python
from langgraph.checkpoint.postgres import PostgresSaver

# Use PostgreSQL for multi-instance deployments
checkpointer = PostgresSaver(
    conn_string="postgresql://user:pass@localhost/checkpoints"
)
```

### Monitoring & Alerting

**Key Metrics to Track:**

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class WorkflowMetrics:
    """Metrics for monitoring workflow execution."""
    
    workflow_name: str
    thread_id: str
    
    # Timing metrics
    total_duration_seconds: float
    time_in_interrupt_seconds: float
    node_execution_times: dict  # {node_name: seconds}
    
    # Status metrics
    total_executions: int  # How many times resumed
    approval_status: str  # "approved", "rejected", "expired"
    final_status: str  # "success", "failure", "timeout"
    
    # Cost metrics
    llm_tokens_used: int
    api_calls_count: int

# Example monitoring setup
import logging

logger = logging.getLogger(__name__)

def log_workflow_metrics(metrics: WorkflowMetrics):
    """Log metrics for alerting and dashboards."""
    logger.info(
        f"Workflow complete: {metrics.workflow_name} "
        f"thread_id={metrics.thread_id} "
        f"duration={metrics.total_duration_seconds:.1f}s "
        f"interrupt_time={metrics.time_in_interrupt_seconds:.1f}s "
        f"approval={metrics.approval_status} "
        f"status={metrics.final_status}"
    )
    
    # Alert if approval took too long
    if metrics.time_in_interrupt_seconds > 3600:  # 1 hour
        logger.warning(
            f"Approval delayed for {metrics.workflow_name}: "
            f"{metrics.time_in_interrupt_seconds/3600:.1f} hours"
        )
```

### Configuration Management

```python
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ApprovalWorkflowConfig:
    """Configuration for approval workflows."""
    
    # Storage
    checkpoint_db_url: str = os.getenv(
        "CHECKPOINT_DB_URL",
        "postgresql://localhost/checkpoints"
    )
    
    # Timeouts
    approval_timeout_hours: int = int(os.getenv("APPROVAL_TIMEOUT_HOURS", "24"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    retry_backoff_base: float = float(os.getenv("RETRY_BACKOFF_BASE", "1.0"))
    
    # Observability
    enable_tracing: bool = os.getenv("LANGCHAIN_TRACING_V2", "false") == "true"
    langsmith_api_key: Optional[str] = os.getenv("LANGSMITH_API_KEY")
    
    # Approval settings
    require_approval: bool = os.getenv("REQUIRE_APPROVAL", "true") == "true"
    approval_notification_url: Optional[str] = os.getenv(
        "APPROVAL_NOTIFICATION_URL"
    )
    
    def validate(self) -> bool:
        """Validate configuration before use."""
        if self.enable_tracing and not self.langsmith_api_key:
            raise ValueError(
                "LANGSMITH_API_KEY required when LANGCHAIN_TRACING_V2=true"
            )
        
        if self.approval_timeout_hours < 1:
            raise ValueError("approval_timeout_hours must be >= 1")
        
        return True
```

### Data Privacy & Security

```python
import hashlib
import json
from typing import Dict, Any
from cryptography.fernet import Fernet

class SecureCheckpointHandler:
    """Handle sensitive data in checkpoints."""
    
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())
    
    def mask_sensitive_fields(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive data before checkpointing."""
        masked = state.copy()
        
        # Example: Mask email content
        if "body" in masked:
            masked["body"] = f"[EMAIL BODY - {len(masked['body'])} chars]"
        
        # Example: Hash recipient email for audit trail
        if "recipient" in masked:
            h = hashlib.sha256(masked["recipient"].encode()).hexdigest()
            masked["recipient_hash"] = h
        
        return masked
    
    def encrypt_sensitive_fields(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields."""
        encrypted = state.copy()
        
        for field in ["body", "recipient"]:
            if field in encrypted and encrypted[field]:
                plaintext = json.dumps(encrypted[field])
                ciphertext = self.cipher.encrypt(plaintext.encode())
                encrypted[field] = ciphertext.decode()
        
        return encrypted
    
    def decrypt_sensitive_fields(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields."""
        decrypted = state.copy()
        
        for field in ["body", "recipient"]:
            if field in decrypted and isinstance(decrypted[field], str):
                try:
                    plaintext = self.cipher.decrypt(decrypted[field].encode())
                    decrypted[field] = json.loads(plaintext)
                except:
                    # Field is not encrypted, skip
                    pass
        
        return decrypted
```

---

## Section 9: Integration with Existing Patterns

### Relationship to WP-2.6

**WP-2.6** introduces LangGraph's state machine foundation:
- Node definitions
- Edge routing
- Automatic state management

**WP-2.7** extends WP-2.6 with:
- Checkpointing (persistence)
- Interrupts (human-in-the-loop)
- Approval workflows (guardrails)

```python
# WP-2.6: Basic orchestration
graph = StateGraph(State)
graph.add_node("step1", step1_fn)
graph.add_node("step2", step2_fn)
graph.add_edge(START, "step1")
graph.add_edge("step1", "step2")
compiled = graph.compile()

# WP-2.7: Add human approval
graph = StateGraph(State)
graph.add_node("step1", step1_fn)
graph.add_node("step2", step2_fn)
graph.add_edge(START, "step1")
graph.add_edge("step1", "step2")

# NEW: Add checkpointer and interrupt
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver(conn=":memory:")

compiled = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["step2"]  # Pause before step2
)
```

### Composition with ADR-2.2 (Orchestration)

This work product provides **infrastructure** for the Orchestration pattern (ADR-2.2):

```
ADR-2.2: Orchestration Pattern
├─ Central coordinator
├─ Step sequencing
├─ Error handling
└─ State tracking
   │
   └─ WP-2.7 Implementation
      ├─ LangGraph StateGraph
      ├─ Checkpointer (persistence)
      ├─ Interrupts (guardrails)
      └─ Approval workflow
```

### Composability with Other WPs

**With WP-1.3 (Runnable Protocol)**:
```python
# Runnable interface
approval_workflow = build_approval_workflow()

# Compose with other runnables
chain = input_processor | approval_workflow | output_formatter
```

**With WP-1.7 (LangSmith Tracing)**:
```python
# Automatic tracing integration
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# All node executions automatically traced
result = compiled.invoke(state, config=config)
```

---

## Section 10: Learning Path & Mastery Checklist

### Prerequisites

Before starting WP-2.7, ensure you understand:
- ✓ Async/await in Python ([reference](https://docs.python.org/3/library/asyncio.html))
- ✓ TypedDict and type hints ([reference](https://typing-extensions.readthedocs.io/))
- ✓ Runnable protocol from WP-1.3 (composability with `|` operator)
- ✓ LangGraph fundamentals from WP-2.6 (StateGraph, nodes, edges)
- ✓ Orchestration pattern from WP-2.3 (step sequencing, error handling)

### Step-by-Step Learning Path

**1. Understand the Problem (15 minutes)**
- Read "Section 1: The Problem"
- Run the provided "anti-pattern" code snippet
- Understand why polling is inefficient

**2. Learn the Solution (20 minutes)**
- Read "Section 2: Proposed Solution" (architecture diagram)
- Read "Section 3: Composable Pattern" (interfaces)
- Understand checkpointer abstraction

**3. Study Observability (10 minutes)**
- Read "Section 4: Observability & Tracing"
- Review trace structure diagram
- Understand what LangSmith shows

**4. Walk Through Implementation (45 minutes)**
- Read "Section 5: Implementation Guide" line by line
- Follow Step 1-6 in sequence
- Study how state flows through nodes

**5. Run the Example Code (20 minutes)**
- Execute `examples_2_7.py`
- Observe approval workflow in action
- Test rejection path
- Check LangSmith dashboard for traces

**6. Study Trade-Offs (15 minutes)**
- Review "Section 6: Trade-Off Analysis" table
- Understand when to use LangGraph vs. alternatives
- Consider your use case

**7. Learn Error Handling (20 minutes)**
- Read "Section 7: Error Handling"
- Study retry logic implementation
- Understand timeout scenarios

**8. Extend the Pattern (45 minutes)**
- Modify `examples_2_7.py` to add custom node
- Implement your own approval workflow
- Add monitoring/logging
- Test end-to-end

### Mastery Checklist

After completing this work product, you should be able to check all of these:

- ☐ **Problem Understanding**: I can explain why manual state serialization is problematic
- ☐ **Checkpointer Concept**: I understand what a checkpointer is and how it persists state
- ☐ **Interrupt Mechanism**: I can explain how interrupts pause execution and enable resumption
- ☐ **State Definition**: I can define a TypedDict state schema for a workflow
- ☐ **Node Implementation**: I can write async node functions that update state
- ☐ **Routing Logic**: I can implement conditional edges based on state
- ☐ **Graph Building**: I can build a StateGraph with nodes, edges, and checkpointer
- ☐ **Execution Model**: I can explain first execution (generate + pause) and second execution (resume + send)
- ☐ **Approval Workflow**: I can implement a complete approval workflow with approval/rejection paths
- ☐ **Error Handling**: I can add retry logic, timeout handling, and graceful degradation
- ☐ **Observability**: I can enable LangSmith tracing and interpret workflow traces
- ☐ **Composition**: I can compose the approval workflow with other runnables
- ☐ **Production Ready**: I can configure, deploy, and monitor a production workflow
- ☐ **Customization**: I can adapt this pattern to your specific use case

---

## Section 11: Common Patterns & Extensions

### Pattern 1: Multi-Step Approval

```python
# Require approval from multiple reviewers
def route_after_generation(state):
    return "review_legal" if not state.get("legal_reviewed") else "review_final"

graph.add_node("review_legal", legal_review_node)
graph.add_edge("review_legal", "review_final")

compiled = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["review_legal", "review_final"]  # Multiple interrupts
)
```

### Pattern 2: Conditional Approval

```python
# Only require approval for large amounts
def should_require_approval(state):
    amount = state.get("amount", 0)
    return amount > 1000  # Approval required for > $1000

def route_after_generation(state):
    if should_require_approval(state):
        return "approval"
    else:
        return "send"

graph.add_node("approval", noop)  # Just breakpoint
graph.add_edge("send", END)
compiled = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["approval"]
)
```

### Pattern 3: Request Modifications

```python
# Allow user to request changes, not just approve/reject
class ModificationRequest(BaseModel):
    status: str  # "approved" | "rejected" | "request_changes"
    requested_changes: Optional[str]
    updated_content: Optional[str]

# User can provide updated content in approval
state["approval_notes"] = "Add more details about..."
state["body"] = "[Updated body]"
state["approval_status"] = "request_changes"

# Workflow re-enters at content generation step
```

---

## Conclusion

LangGraph's checkpointer + interrupt system solves the enterprise requirement of guardrails in AI workflows. By abstracting state persistence and resumption, it eliminates the complexity of manual serialization while providing:

1. **Efficiency**: Event-driven (not polling), minimal memory overhead
2. **Auditability**: Built-in thread history and timestamps
3. **Flexibility**: Conditional routing, branching, and multi-step approval
4. **Observability**: Automatic LangSmith integration
5. **Scalability**: Works in distributed systems with database-backed checkpointing

The combination of WP-2.6 (LangGraph foundations), WP-2.7 (checkpointing), and ADR-2.2 (orchestration pattern) provides a complete, production-ready framework for building multi-step AI workflows with human oversight.

