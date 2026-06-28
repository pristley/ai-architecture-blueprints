"""
Controller Orchestration Agent: Centralized Workflow Control

Demonstrates the Orchestration pattern (ADR-2.2) where a Controller agent:
1. Explicitly plans the workflow
2. Executes tools sequentially
3. Evaluates each step's output
4. Decides the next action
5. Tracks complete audit trail

Case Study: "Write AI Trends Report" workflow
- Task: Generate a 2000+ word report on AI trends with 15+ citations
- Workflow: Plan → Fetch → Analyze → Synthesize → Cite → Format
- Orchestration: Controller decides: continue? retry? branch? fail?
- Observability: Full audit trail of each decision and result
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# Step Types and States
# ============================================================================

class StepName(str, Enum):
    """Valid orchestration steps."""
    PLANNING = "PLANNING"
    FETCHING = "FETCHING"
    ANALYZING = "ANALYZING"
    SYNTHESIZING = "SYNTHESIZING"
    CITING = "CITING"
    FORMATTING = "FORMATTING"


class StepStatus(str, Enum):
    """Execution status of a step."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRY = "RETRY"
    SKIPPED = "SKIPPED"


class Decision(str, Enum):
    """What the Controller decides after evaluating a step."""
    CONTINUE = "CONTINUE"          # Proceed to next step
    RETRY = "RETRY"                # Retry current step
    BRANCH = "BRANCH"              # Take alternate path
    SKIP = "SKIP"                  # Skip this step
    ABORT = "ABORT"                # Stop execution


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class StepExecution:
    """Record of a single step execution."""
    step_name: StepName
    status: StepStatus
    input_data: Any
    output_data: Optional[Any] = None
    error: Optional[str] = None
    attempt: int = 1
    duration_seconds: float = 0.0
    evaluation_result: Optional[str] = None
    decision: Optional[Decision] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "step": self.step_name.value,
            "status": self.status.value,
            "input_size": len(str(self.input_data)),
            "output_size": len(str(self.output_data)) if self.output_data else 0,
            "error": self.error,
            "attempt": self.attempt,
            "duration_seconds": round(self.duration_seconds, 2),
            "evaluation": self.evaluation_result,
            "decision": self.decision.value if self.decision else None,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class OrchestrationState:
    """Complete state of an orchestration run."""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task: str = ""
    plan: Optional[List[str]] = None
    fetched_data: Optional[List[Dict]] = None
    extracted_facts: Optional[List[Dict]] = None
    draft_report: Optional[str] = None
    report_with_citations: Optional[str] = None
    final_report: Optional[str] = None
    step_history: List[StepExecution] = field(default_factory=list)
    
    # Tracking
    current_step_index: int = 0
    total_steps_completed: int = 0
    total_retries: int = 0
    total_branches: int = 0
    errors: List[str] = field(default_factory=list)
    
    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    def record_step(self, execution: StepExecution) -> None:
        """Record a step execution."""
        self.step_history.append(execution)
        if execution.status == StepStatus.SUCCESS:
            self.total_steps_completed += 1
        elif execution.status == StepStatus.RETRY:
            self.total_retries += 1
        elif execution.status == StepStatus.SKIPPED:
            self.total_branches += 1
        
        if execution.error:
            self.errors.append(f"{execution.step_name}: {execution.error}")
    
    def get_status_string(self) -> str:
        """Human-readable status."""
        status_lines = [
            f"Workflow: {self.workflow_id[:8]}...",
            f"Task: {self.task}",
            f"Progress: {self.total_steps_completed} steps completed",
            f"Retries: {self.total_retries}, Branches: {self.total_branches}",
        ]
        
        if self.final_report:
            status_lines.append(f"Result: {len(self.final_report)} characters")
        
        if self.errors:
            status_lines.append(f"Errors: {len(self.errors)}")
        
        return " | ".join(status_lines)


# ============================================================================
# Evaluation Functions
# ============================================================================

def evaluate_plan(plan: Optional[List[str]]) -> Tuple[bool, str]:
    """
    Evaluate if the plan is acceptable.
    
    Returns: (is_acceptable, reason)
    """
    if not plan:
        return False, "Plan is empty"
    
    if len(plan) < 3:
        return False, f"Plan has {len(plan)} steps, need ≥3"
    
    if any(not step or not isinstance(step, str) for step in plan):
        return False, "Plan contains invalid steps"
    
    return True, f"Plan accepted: {len(plan)} steps"


def evaluate_fetched_data(data: Optional[List[Dict]]) -> Tuple[bool, str]:
    """
    Evaluate if we fetched enough data.
    
    Returns: (is_acceptable, reason)
    """
    MIN_SOURCES = 8
    
    if not data:
        return False, "No data fetched"
    
    if len(data) < MIN_SOURCES:
        return False, f"Fetched {len(data)} sources, need ≥{MIN_SOURCES}"
    
    # Check data quality
    if any(not item.get("title") or not item.get("content") for item in data):
        return False, "Some sources missing title or content"
    
    return True, f"Fetched {len(data)} sources (minimum: {MIN_SOURCES})"


def evaluate_extracted_facts(facts: Optional[List[Dict]]) -> Tuple[bool, str]:
    """
    Evaluate if we extracted enough facts.
    
    Returns: (is_acceptable, reason)
    """
    MIN_FACTS = 20
    
    if not facts:
        return False, "No facts extracted"
    
    if len(facts) < MIN_FACTS:
        return False, f"Extracted {len(facts)} facts, need ≥{MIN_FACTS}"
    
    # Check fact quality
    if any(not f.get("fact") or not f.get("source") for f in facts):
        return False, "Some facts missing text or source"
    
    return True, f"Extracted {len(facts)} facts (minimum: {MIN_FACTS})"


def evaluate_draft_report(draft: Optional[str]) -> Tuple[bool, str]:
    """
    Evaluate if the draft report is acceptable.
    
    Returns: (is_acceptable, reason)
    """
    MIN_WORDS = 1000
    MIN_PARAGRAPHS = 5
    
    if not draft:
        return False, "Draft is empty"
    
    word_count = len(draft.split())
    paragraph_count = len([p for p in draft.split("\n\n") if p.strip()])
    
    if word_count < MIN_WORDS:
        return False, f"Draft has {word_count} words, need ≥{MIN_WORDS}"
    
    if paragraph_count < MIN_PARAGRAPHS:
        return False, f"Draft has {paragraph_count} paragraphs, need ≥{MIN_PARAGRAPHS}"
    
    return True, f"Draft report: {word_count} words, {paragraph_count} paragraphs"


def evaluate_cited_report(report: Optional[str]) -> Tuple[bool, str]:
    """
    Evaluate if citations are present.
    
    Returns: (is_acceptable, reason)
    """
    MIN_CITATIONS = 10
    
    if not report:
        return False, "Report is empty"
    
    citation_count = report.count("[source:")
    
    if citation_count < MIN_CITATIONS:
        return False, f"Report has {citation_count} citations, need ≥{MIN_CITATIONS}"
    
    return True, f"Report has {citation_count} citations"


def evaluate_formatted_report(report: Optional[str]) -> Tuple[bool, str]:
    """
    Evaluate if the final report is well-formatted.
    
    Returns: (is_acceptable, reason)
    """
    if not report:
        return False, "Report is empty"
    
    if "# " not in report:
        return False, "Report missing Markdown headers"
    
    if not report.endswith("\n"):
        return False, "Report not properly terminated"
    
    return True, f"Final report: {len(report)} characters"


# ============================================================================
# Tool Implementations
# ============================================================================

async def plan_tool(task: str) -> List[str]:
    """
    Planning step: Break down task into explicit steps.
    """
    await asyncio.sleep(0.2)  # Simulate LLM latency
    
    plan = [
        "Identify key AI trend topics (machine learning, LLMs, ethics)",
        "Search for recent research papers and news articles",
        "Extract key facts and insights from sources",
        "Synthesize findings into structured report",
        "Add citations linking claims to sources",
        "Format with Markdown headers and sections",
    ]
    
    return plan


async def fetch_tool(task: str) -> List[Dict]:
    """
    Fetch step: Search for relevant information.
    """
    await asyncio.sleep(0.3)  # Simulate search latency
    
    sources = [
        {
            "title": "Machine Learning Breakthroughs 2024",
            "content": "Recent advances in transfer learning and few-shot learning...",
            "url": "https://example.com/ml-2024",
            "date": "2024-06-01",
        },
        {
            "title": "Large Language Models: Scaling Laws and Efficiency",
            "content": "New findings on optimal model scaling and training efficiency...",
            "url": "https://example.com/llm-efficiency",
            "date": "2024-05-15",
        },
        {
            "title": "AI Ethics and Responsible Development",
            "content": "Guidelines for responsible AI development and deployment...",
            "url": "https://example.com/ai-ethics",
            "date": "2024-06-10",
        },
        {
            "title": "Multimodal AI Systems",
            "content": "Integration of vision, language, and audio in unified models...",
            "url": "https://example.com/multimodal",
            "date": "2024-05-20",
        },
        {
            "title": "Real-time AI Inference",
            "content": "Edge computing and optimized inference for production systems...",
            "url": "https://example.com/inference",
            "date": "2024-06-05",
        },
        {
            "title": "AI and Climate Change",
            "content": "Applications of AI to climate modeling and prediction...",
            "url": "https://example.com/ai-climate",
            "date": "2024-04-30",
        },
        {
            "title": "Autonomous Agents and Planning",
            "content": "Recent developments in autonomous agent architectures...",
            "url": "https://example.com/agents",
            "date": "2024-06-12",
        },
        {
            "title": "AI Regulatory Landscape",
            "content": "Global regulations and compliance frameworks...",
            "url": "https://example.com/regulation",
            "date": "2024-06-08",
        },
        {
            "title": "Fine-tuning and Adaptation",
            "content": "Techniques for adapting models to specific domains...",
            "url": "https://example.com/finetuning",
            "date": "2024-05-25",
        },
    ]
    
    return sources


async def analyze_tool(fetched_data: List[Dict]) -> List[Dict]:
    """
    Analysis step: Extract facts and insights from sources.
    """
    await asyncio.sleep(0.4)  # Simulate analysis latency
    
    facts = [
        {"fact": "Transfer learning reduces training time by 70%", "source": "Machine Learning Breakthroughs 2024"},
        {"fact": "Few-shot learning enables rapid model adaptation", "source": "Machine Learning Breakthroughs 2024"},
        {"fact": "LLMs follow power law scaling: loss ∝ 1/N^0.07", "source": "Large Language Models: Scaling Laws and Efficiency"},
        {"fact": "Model efficiency improves 3x with knowledge distillation", "source": "Large Language Models: Scaling Laws and Efficiency"},
        {"fact": "Responsible AI requires transparent model documentation", "source": "AI Ethics and Responsible Development"},
        {"fact": "Bias auditing is critical for production deployment", "source": "AI Ethics and Responsible Development"},
        {"fact": "Multimodal models improve performance by 25% on complex tasks", "source": "Multimodal AI Systems"},
        {"fact": "Vision-language models enable new applications in robotics", "source": "Multimodal AI Systems"},
        {"fact": "Edge inference reduces latency to <100ms", "source": "Real-time AI Inference"},
        {"fact": "Quantization enables 10x model size reduction", "source": "Real-time AI Inference"},
        {"fact": "AI improves climate prediction accuracy by 40%", "source": "AI and Climate Change"},
        {"fact": "Neural networks outperform physics-based models", "source": "AI and Climate Change"},
        {"fact": "Autonomous agents require hierarchical planning", "source": "Autonomous Agents and Planning"},
        {"fact": "Multi-agent systems enable complex problem solving", "source": "Autonomous Agents and Planning"},
        {"fact": "EU AI Act establishes risk-based regulation framework", "source": "AI Regulatory Landscape"},
        {"fact": "Transparency requirements drive model interpretability", "source": "AI Regulatory Landscape"},
        {"fact": "Domain adaptation via fine-tuning is cost-effective", "source": "Fine-tuning and Adaptation"},
        {"fact": "Few parameters fine-tuning achieves 95% performance", "source": "Fine-tuning and Adaptation"},
        {"fact": "Prompt engineering is now a critical skill", "source": "Machine Learning Breakthroughs 2024"},
        {"fact": "Retrieval-augmented generation combines LLMs with knowledge bases", "source": "Large Language Models: Scaling Laws and Efficiency"},
        {"fact": "Mixture-of-experts enables efficient scaling", "source": "Large Language Models: Scaling Laws and Efficiency"},
        {"fact": "Federated learning enables privacy-preserving training", "source": "AI Ethics and Responsible Development"},
    ]
    
    return facts


async def synthesize_tool(facts: List[Dict]) -> str:
    """
    Synthesis step: Write draft report from facts.
    """
    await asyncio.sleep(0.5)  # Simulate writing latency
    
    draft = """# AI Trends 2024: Comprehensive Analysis

## Executive Summary

Artificial Intelligence continues its rapid evolution with significant breakthroughs across multiple domains in 2024. This report provides a comprehensive analysis of key trends emerging in the field, including revolutionary advances in large language models, innovative multimodal systems that combine vision and language, practical real-time inference capabilities, and the growing emphasis on responsible AI development practices. Our analysis synthesizes findings from leading research institutions, industry practitioners, and academic experts worldwide.

The trends identified in this report represent fundamental shifts in how artificial intelligence systems are designed, deployed, and governed. These developments have profound implications for organizations adopting AI technologies and for society at large. The following sections provide detailed analysis of each major trend area.

## Machine Learning Foundations and Innovation

Recent advances in transfer learning and few-shot learning have fundamentally transformed how we approach artificial intelligence development. Transfer learning reduces training time by 70%, enabling practitioners to leverage existing knowledge to solve new problems more efficiently. Few-shot learning enables rapid model adaptation to new domains with minimal training data, opening possibilities for applications where data collection is expensive or time-consuming.

These techniques are rapidly becoming foundational components of modern production AI systems. Organizations are discovering that combining transfer learning with few-shot approaches yields robust, adaptable solutions that can be deployed across diverse use cases. The economic implications are significant: reduced development time directly translates to faster time-to-market and lower costs.

Prompt engineering has emerged as a critical and essential skill alongside traditional machine learning expertise. The combination of well-designed prompts with retrieval-augmented generation enables powerful applications that leverage the benefits of large language models while grounding responses in factual, up-to-date knowledge bases. This hybrid approach represents a new paradigm in AI application development that moves beyond pure neural approaches.

## Large Language Models: Scaling, Efficiency, and Optimization

Large language models continue to follow consistent power law scaling relationships, with loss inversely proportional to model size. This mathematical understanding allows practitioners to make informed trade-offs between model capability and computational cost, enabling more efficient resource allocation. Understanding these relationships enables more efficient research and development practices.

Model efficiency improvements through knowledge distillation achieve approximately 3x improvements in inference speed without significant accuracy degradation. Quantization techniques enable 10x model size reduction while maintaining reasonable accuracy levels, making deployment on edge devices practical and economically viable. These advances have dramatic implications for accessibility and scalability.

Mixture-of-experts architectures represent a particularly promising direction for efficient scaling. These architectures enable selective activation of model components based on input characteristics, maintaining capability while controlling computational costs. Early results suggest these approaches may be crucial for future AI scalability and cost-effectiveness. The potential impact on the industry cannot be overstated.

## Multimodal AI Systems and Integrated Intelligence

Multimodal models that effectively integrate vision, language, and audio modalities improve performance by approximately 25% on complex, real-world tasks. Vision-language models are enabling innovative applications in robotics, content understanding, visual reasoning, and accessible AI systems that serve diverse user populations. The convergence of different modalities represents a major milestone in AI development.

The integration of multiple modalities into unified AI systems provides richer, more informative representations of complex phenomena. This represents a significant shift from single-modality systems toward more capable and versatile AI systems that can handle multi-faceted problems. The ability to process and reason about multiple types of information simultaneously opens entirely new application possibilities.

## Real-time AI Inference and Edge Computing

Edge inference has achieved practical viability with inference latency reduced to under 100 milliseconds. This breakthrough enables deployment of AI systems in latency-sensitive applications including mobile devices, robotics, and real-time decision-making systems that cannot tolerate cloud round-trip delays. The implications for real-time applications are transformative.

The ability to run sophisticated AI models directly on edge devices has profound implications for privacy, latency, and cost economics. Applications no longer require continuous cloud connectivity, enabling AI deployment in remote locations, offline scenarios, and privacy-critical applications where data should not leave the device. This architectural shift represents a fundamental change in how AI systems can be deployed and accessed.

## Responsible AI, Ethics, and Trustworthiness

Responsible AI development requires transparent model documentation, careful bias auditing, and rigorous testing for failure modes. These practices are essential for production deployment and increasingly for regulatory compliance across jurisdictions. Organizations recognizing the business value of responsible practices gain significant competitive advantages.

Federated learning enables privacy-preserving model training across distributed data sources without centralizing sensitive information. This approach balances the benefits of collective machine learning with individual privacy protection, enabling collaboration while maintaining confidentiality. The ability to train on sensitive data without exposing it represents a major breakthrough in privacy-preserving AI.

## AI Regulations, Governance, and Compliance

The EU AI Act establishes a comprehensive risk-based regulation framework for AI systems. Transparency requirements are driving increased focus on model interpretability and explainability across the industry, making interpretable AI a competitive advantage. Organizations that invest in interpretability now will be positioned to comply with future regulations.

Global regulatory frameworks are evolving rapidly with significant implications for AI system design, deployment, and monitoring. Organizations must adopt governance practices that anticipate and exceed regulatory requirements to maintain compliance and build stakeholder trust. Proactive engagement with regulatory frameworks provides advantages over reactive approaches.

## Autonomous Agents and Planning Capabilities

Autonomous agents require sophisticated hierarchical planning capabilities and advanced decision-making architectures. Multi-agent systems demonstrate significant promise for solving complex problems that exceed the capabilities of single-agent approaches. The sophistication of agent coordination continues to advance rapidly.

The integration of explicit planning with autonomous agent behaviors represents an important evolution in AI system design, enabling more sophisticated collaborative problem-solving. Agents that can reason about goals, subgoals, and dependencies are fundamentally more capable than simpler reactive systems.

## Domain Adaptation and Fine-tuning Strategies

Domain adaptation via fine-tuning remains highly cost-effective in practice. Few-parameter fine-tuning achieves 95% of full fine-tuning performance while requiring minimal computational resources. This approach is enabling rapid deployment of AI systems across diverse domains and verticals. The democratization of AI through efficient adaptation is reshaping the industry.

## Applications to Climate and Sustainability Challenges

Artificial intelligence improves climate prediction accuracy by 40% compared to traditional physics-based models. Neural networks are becoming essential tools for climate science, environmental monitoring, and understanding complex ecological systems. The environmental implications of these advances are significant for sustainable technology development.

## Workforce Implications and Skills Development

The rapid evolution of AI technology has major implications for workforce development and skills requirements. Organizations need to invest in training programs that develop competencies in prompt engineering, model evaluation, and responsible AI practices. The jobs market for AI professionals continues to expand rapidly.

## Conclusion and Future Outlook

The AI field continues to evolve rapidly with important breakthroughs in scaling, efficiency, multimodal capabilities, and responsible development practices. These trends point toward AI systems that are simultaneously more capable, more efficient, more responsible, and more trustworthy.

Organizations adopting these trends will be well-positioned for competitive advantage, while those lagging risk falling behind in capability, efficiency, and compliance. The time to invest in these capabilities is now. The future belongs to organizations that successfully integrate these advances into their strategic operations.
"""
    
    return draft


async def cite_tool(draft: str) -> str:
    """
    Citation step: Add citations to claims.
    """
    await asyncio.sleep(0.3)  # Simulate citation lookup
    
    cited = draft.replace(
        "Transfer learning reduces training time by 70%",
        "Transfer learning reduces training time by 70% [source: Machine Learning Breakthroughs 2024]"
    ).replace(
        "Few-shot learning enables rapid model adaptation",
        "Few-shot learning enables rapid model adaptation [source: Machine Learning Breakthroughs 2024]"
    ).replace(
        "Prompt engineering has emerged as a critical skill",
        "Prompt engineering has emerged as a critical skill [source: Machine Learning Breakthroughs 2024]"
    ).replace(
        "loss inversely proportional to model size (approximately 1/N^0.07)",
        "loss inversely proportional to model size [source: Large Language Models: Scaling Laws and Efficiency]"
    ).replace(
        "knowledge distillation achieve 3x improvements",
        "knowledge distillation achieve 3x improvements [source: Large Language Models: Scaling Laws and Efficiency]"
    ).replace(
        "Quantization enables 10x model size reduction",
        "Quantization enables 10x model size reduction [source: Real-time AI Inference]"
    ).replace(
        "retrieval-augmented generation enables powerful applications",
        "retrieval-augmented generation enables powerful applications [source: Large Language Models: Scaling Laws and Efficiency]"
    ).replace(
        "Multimodal models... improve performance by approximately 25%",
        "Multimodal models improve performance by approximately 25% [source: Multimodal AI Systems]"
    ).replace(
        "Vision-language models are enabling new applications",
        "Vision-language models are enabling new applications [source: Multimodal AI Systems]"
    ).replace(
        "inference latency reduced to under 100 milliseconds",
        "inference latency reduced to under 100 milliseconds [source: Real-time AI Inference]"
    ).replace(
        "Responsible AI development requires transparent model documentation",
        "Responsible AI development requires transparent model documentation [source: AI Ethics and Responsible Development]"
    ).replace(
        "bias auditing. These practices are essential",
        "bias auditing [source: AI Ethics and Responsible Development]. These practices are essential"
    ).replace(
        "Federated learning enables privacy-preserving",
        "Federated learning enables privacy-preserving [source: AI Ethics and Responsible Development]"
    ).replace(
        "EU AI Act establishes a comprehensive risk-based regulation",
        "EU AI Act establishes a comprehensive risk-based regulation [source: AI Regulatory Landscape]"
    ).replace(
        "Transparency requirements are driving increased focus",
        "Transparency requirements are driving increased focus [source: AI Regulatory Landscape]"
    ).replace(
        "Autonomous agents require hierarchical planning",
        "Autonomous agents require hierarchical planning [source: Autonomous Agents and Planning]"
    ).replace(
        "Multi-agent systems demonstrate significant promise",
        "Multi-agent systems demonstrate significant promise [source: Autonomous Agents and Planning]"
    ).replace(
        "Domain adaptation via fine-tuning remains cost-effective",
        "Domain adaptation via fine-tuning remains cost-effective [source: Fine-tuning and Adaptation]"
    ).replace(
        "few-parameter fine-tuning achieving 95%",
        "few-parameter fine-tuning achieving 95% [source: Fine-tuning and Adaptation]"
    ).replace(
        "AI improves climate prediction accuracy by 40%",
        "AI improves climate prediction accuracy by 40% [source: AI and Climate Change]"
    ).replace(
        "Neural networks are becoming essential tools",
        "Neural networks are becoming essential tools [source: AI and Climate Change]"
    )
    
    return cited


async def format_tool(report_with_citations: str) -> str:
    """
    Format step: Final polish and Markdown formatting.
    """
    await asyncio.sleep(0.2)  # Simulate formatting
    
    formatted = f"""{report_with_citations}

---

## References

The claims in this report are grounded in recent research and industry developments:

- Machine Learning Breakthroughs 2024
- Large Language Models: Scaling Laws and Efficiency  
- AI Ethics and Responsible Development
- Multimodal AI Systems
- Real-time AI Inference
- AI and Climate Change
- Autonomous Agents and Planning
- AI Regulatory Landscape
- Fine-tuning and Adaptation

*Report generated via Orchestration pattern (ADR-2.2)*
*Complete audit trail available in workflow logs*

"""
    return formatted


# ============================================================================
# Controller Base Class
# ============================================================================

class Controller(ABC):
    """
    Base Controller for orchestrating multi-step workflows.
    
    Provides:
    - Step execution with state tracking
    - Evaluation and decision-making
    - Error handling and retry logic
    - Complete audit trail
    """
    
    def __init__(self):
        self.tools: Dict[StepName, Callable] = {}
        self.evaluators: Dict[StepName, Callable] = {}
        self.state = OrchestrationState()
    
    def register_tool(self, step: StepName, tool: Callable) -> None:
        """Register a tool for a step."""
        self.tools[step] = tool
    
    def register_evaluator(self, step: StepName, evaluator: Callable) -> None:
        """Register an evaluation function for a step."""
        self.evaluators[step] = evaluator
    
    async def execute_step(
        self,
        step_name: StepName,
        input_data: Any,
        max_retries: int = 2,
    ) -> Tuple[Any, StepExecution]:
        """
        Execute a single step with retry logic and evaluation.
        
        Returns: (result, execution_record)
        """
        import time
        
        execution = None
        
        for attempt in range(1, max_retries + 1):
            execution = StepExecution(
                step_name=step_name,
                status=StepStatus.RUNNING,
                input_data=input_data,
                attempt=attempt,
            )
            
            start_time = time.time()
            
            try:
                # Execute tool
                logger.info(f"  ⚙️  [{step_name.value}] Attempt {attempt}")
                tool = self.tools[step_name]
                result = await tool(input_data)
                
                execution.output_data = result
                execution.duration_seconds = time.time() - start_time
                
                # Evaluate result
                if step_name in self.evaluators:
                    evaluator = self.evaluators[step_name]
                    is_acceptable, reason = evaluator(result)
                    execution.evaluation_result = reason
                    
                    if not is_acceptable:
                        logger.info(f"     ❌ Evaluation failed: {reason}")
                        execution.status = StepStatus.RETRY if attempt < max_retries else StepStatus.FAILED
                        continue
                
                execution.status = StepStatus.SUCCESS
                logger.info(f"     ✅ {reason}")
                
                self.state.record_step(execution)
                return result, execution
            
            except Exception as e:
                execution.error = str(e)
                execution.duration_seconds = time.time() - start_time
                execution.status = StepStatus.RETRY if attempt < max_retries else StepStatus.FAILED
                
                logger.info(f"     ❌ Error: {e}")
                
                if attempt < max_retries:
                    await asyncio.sleep(0.5 * attempt)  # Exponential backoff
                    continue
                
                self.state.record_step(execution)
                raise
        
        self.state.record_step(execution)
        raise RuntimeError(f"Step {step_name} failed after {max_retries} attempts")
    
    async def evaluate_and_decide(
        self,
        step_name: StepName,
        result: Any,
    ) -> Decision:
        """
        Evaluate result and decide next action.
        
        Returns: Decision (CONTINUE, RETRY, BRANCH, SKIP, ABORT)
        """
        if step_name not in self.evaluators:
            return Decision.CONTINUE
        
        evaluator = self.evaluators[step_name]
        is_acceptable, reason = evaluator(result)
        
        if is_acceptable:
            return Decision.CONTINUE
        else:
            return Decision.RETRY
    
    @abstractmethod
    async def orchestrate(self, task: str) -> str:
        """
        Main orchestration loop. Subclasses implement specific workflows.
        """
        pass
    
    def get_audit_trail(self) -> Dict:
        """Get complete audit trail."""
        return {
            "workflow_id": self.state.workflow_id,
            "task": self.state.task,
            "steps": [step.to_dict() for step in self.state.step_history],
            "summary": {
                "total_steps": self.state.total_steps_completed,
                "retries": self.state.total_retries,
                "branches": self.state.total_branches,
                "errors": self.state.errors,
                "duration_seconds": (self.state.end_time - self.state.start_time).total_seconds()
                    if self.state.end_time else None,
            }
        }


# ============================================================================
# Report Orchestrator: Concrete Implementation
# ============================================================================

class ReportOrchestrator(Controller):
    """
    Orchestrator for "Write AI Trends Report" workflow.
    
    Workflow: Plan → Fetch → Analyze → Synthesize → Cite → Format
    """
    
    def __init__(self):
        super().__init__()
        
        # Register tools
        self.register_tool(StepName.PLANNING, plan_tool)
        self.register_tool(StepName.FETCHING, fetch_tool)
        self.register_tool(StepName.ANALYZING, analyze_tool)
        self.register_tool(StepName.SYNTHESIZING, synthesize_tool)
        self.register_tool(StepName.CITING, cite_tool)
        self.register_tool(StepName.FORMATTING, format_tool)
        
        # Register evaluators
        self.register_evaluator(StepName.PLANNING, evaluate_plan)
        self.register_evaluator(StepName.FETCHING, evaluate_fetched_data)
        self.register_evaluator(StepName.ANALYZING, evaluate_extracted_facts)
        self.register_evaluator(StepName.SYNTHESIZING, evaluate_draft_report)
        self.register_evaluator(StepName.CITING, evaluate_cited_report)
        self.register_evaluator(StepName.FORMATTING, evaluate_formatted_report)
    
    async def orchestrate(self, task: str) -> str:
        """
        Execute the complete report generation workflow.
        
        Task: Generate a report on AI trends
        """
        logger.info("\n" + "="*80)
        logger.info("ORCHESTRATION: Report Generation Workflow")
        logger.info("="*80)
        
        self.state.task = task
        logger.info(f"\n📋 Task: {task}")
        logger.info(f"🔗 Workflow ID: {self.state.workflow_id[:8]}...\n")
        
        try:
            # Step 1: Plan
            logger.info("[Step 1/6] PLANNING")
            plan, _ = await self.execute_step(StepName.PLANNING, task)
            self.state.plan = plan
            
            # Step 2: Fetch Data
            logger.info("[Step 2/6] FETCHING DATA")
            data, _ = await self.execute_step(StepName.FETCHING, task)
            self.state.fetched_data = data
            
            # Step 3: Analyze
            logger.info("[Step 3/6] ANALYZING")
            facts, _ = await self.execute_step(StepName.ANALYZING, data)
            self.state.extracted_facts = facts
            
            # Step 4: Synthesize
            logger.info("[Step 4/6] SYNTHESIZING")
            draft, _ = await self.execute_step(StepName.SYNTHESIZING, facts)
            self.state.draft_report = draft
            
            # Step 5: Cite
            logger.info("[Step 5/6] ADDING CITATIONS")
            cited, _ = await self.execute_step(StepName.CITING, draft)
            self.state.report_with_citations = cited
            
            # Step 6: Format
            logger.info("[Step 6/6] FORMATTING")
            final, _ = await self.execute_step(StepName.FORMATTING, cited)
            self.state.final_report = final
            
            # Success
            logger.info("\n✅ Workflow succeeded!")
            logger.info(f"   {self.state.get_status_string()}\n")
            
            return final
        
        except Exception as e:
            logger.error(f"\n❌ Workflow failed: {e}")
            logger.error(f"   {self.state.get_status_string()}\n")
            raise
        
        finally:
            self.state.end_time = datetime.now()


# ============================================================================
# Main Demo
# ============================================================================

async def demo_orchestration() -> None:
    """Demonstrate the orchestration pattern."""
    
    orchestrator = ReportOrchestrator()
    
    try:
        report = await orchestrator.orchestrate(
            "Write a comprehensive report on AI trends in 2024"
        )
        
        # Print excerpt of report
        logger.info("📄 REPORT EXCERPT (first 800 characters):\n")
        logger.info(report[:800] + "...\n")
        
        # Print audit trail
        logger.info("="*80)
        logger.info("AUDIT TRAIL")
        logger.info("="*80 + "\n")
        
        audit_trail = orchestrator.get_audit_trail()
        logger.info(json.dumps(audit_trail, indent=2))
        logger.info("")
        
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(demo_orchestration())
