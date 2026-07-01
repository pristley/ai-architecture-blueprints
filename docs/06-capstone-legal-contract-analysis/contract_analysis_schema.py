"""
Contract Analysis Schema - Pydantic Models

This module defines the data structures for legal contract clause analysis.
Structured output enables reliable downstream processing and evaluation.

Architecture Decision: Pydantic v2+ provides:
- Strict validation at boundaries (LLM output, user input)
- Automatic serialization (JSON export for storage/API)
- Type hints for IDE support and static analysis
- JSON Schema generation for API documentation
"""

from typing import Optional, List, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums: Controlled Vocabularies
# ============================================================================

class ContractType(str, Enum):
    """Common legal contract types."""
    NDA = "nda"  # Non-Disclosure Agreement
    SERVICE = "service_agreement"  # Service Agreement (SaaS, consulting)
    SUPPLY = "supply"  # Supply/Procurement Agreement
    LICENSE = "license"  # Software/IP License
    EMPLOYMENT = "employment"  # Employment/Contractor Agreement
    LEASE = "lease"  # Real Estate/Equipment Lease
    PARTNERSHIP = "partnership"  # Partnership/Joint Venture
    PURCHASE = "purchase"  # Asset/Goods Purchase Agreement
    MAINTENANCE = "maintenance"  # Maintenance/Support Agreement
    OTHER = "other"  # Unclassifiable or composite


class RiskLevel(str, Enum):
    """Risk severity classification for contract clauses."""
    LOW = "low"  # Standard language, no concerns
    MEDIUM = "medium"  # Non-standard but manageable
    HIGH = "high"  # Significant exposure or unusual terms
    CRITICAL = "critical"  # May violate policy, require legal review


class ClauseType(str, Enum):
    """Categories of contract clauses."""
    TERMINATION = "termination"
    LIABILITY = "liability"
    INDEMNIFICATION = "indemnification"
    LIMITATION_OF_LIABILITY = "lol"  # Caps on damages
    WARRANTY = "warranty"
    CONFIDENTIALITY = "confidentiality"
    IP_OWNERSHIP = "ip_ownership"
    PAYMENT_TERMS = "payment_terms"
    GOVERNING_LAW = "governing_law"
    DISPUTE_RESOLUTION = "dispute_resolution"
    FORCE_MAJEURE = "force_majeure"
    ASSIGNMENT = "assignment"
    OTHER = "other"


class AnomalyType(str, Enum):
    """Types of risky language patterns or anomalies."""
    UNUSUAL_TERM_LENGTH = "unusual_term_length"  # Very short/long
    ONE_SIDED = "one_sided"  # Heavily favors one party
    UNLIMITED_LIABILITY = "unlimited_liability"  # No cap on damages
    UNDEFINED_SCOPE = "undefined_scope"  # Vague obligations
    MATERIAL_BREACH_TRIGGER = "material_breach_trigger"  # Low/ambiguous threshold
    UNILATERAL_TERMINATION = "unilateral_termination"  # Only one party can exit
    ESCALATING_PENALTIES = "escalating_penalties"  # Punitive interest/fees
    AUTOMATIC_RENEWAL = "automatic_renewal"  # Tricky renewal mechanics
    BROAD_INDEMNITY = "broad_indemnity"  # Indemnity for other party's actions
    OTHER = "other"


# ============================================================================
# Core Clause Models
# ============================================================================

class ContractClause(BaseModel):
    """
    Represents a single identified clause or section in a contract.
    
    Fields:
        clause_id: Unique identifier within this contract
        clause_type: Classification of what type of clause this is
        text: Raw text of the clause (first 500 chars shown here for brevity)
        start_page: Approximate page number (for PDF navigation)
        end_page: End page if clause spans multiple pages
    """
    clause_id: str = Field(..., description="Unique ID (e.g., 'clause_001')")
    clause_type: ClauseType = Field(..., description="Category of clause")
    text: str = Field(..., description="Full text of the clause")
    start_page: int = Field(..., ge=1, description="Starting page number")
    end_page: Optional[int] = Field(None, description="Ending page (if multi-page)")

    @field_validator("clause_id")
    @classmethod
    def validate_clause_id(cls, v):
        """Ensure clause IDs follow naming convention."""
        assert v.startswith("clause_"), "clause_id must start with 'clause_'"
        return v


class TerminationClause(ContractClause):
    """
    Specialization for termination clauses.
    
    Key attributes:
        notice_period_days: How many days before termination takes effect
        termination_for_convenience: Can either party exit without cause?
        early_termination_penalties: Costs for early exit
        automatic_renewal: Does it auto-renew unless explicitly terminated?
    """
    clause_type: ClauseType = ClauseType.TERMINATION
    notice_period_days: Optional[int] = Field(None, ge=0, description="Days required notice")
    termination_for_convenience: bool = Field(
        ..., 
        description="Either party can terminate without cause"
    )
    early_termination_penalties: str = Field(
        ..., 
        description="Description of termination fees or penalties"
    )
    automatic_renewal: bool = Field(
        ..., 
        description="Contract auto-renews unless explicitly terminated"
    )


class LiabilityClause(ContractClause):
    """
    Specialization for liability clauses.
    
    Key attributes:
        liability_cap: Maximum total damages (in dollars or "unlimited")
        covered_damages: Types of damages covered (direct, indirect, etc.)
        exclusions: Situations where cap doesn't apply
    """
    clause_type: ClauseType = ClauseType.LIABILITY
    liability_cap: str = Field(
        ..., 
        description="Max liability amount or 'unlimited' or 'N/A'"
    )
    covered_damages: List[str] = Field(
        default_factory=list,
        description="Types: direct, indirect, consequential, punitive, etc."
    )
    exclusions: str = Field(
        default="",
        description="Situations/damages excepted from the cap"
    )


class IndemnificationClause(ContractClause):
    """
    Specialization for indemnification clauses.
    
    Key attributes:
        indemnifier: Who must indemnify (provide legal defense/payment)
        indemnified: Who is protected
        scope: What claims/losses are covered
        third_party: Whether indemnity extends to third-party claims
    """
    clause_type: ClauseType = ClauseType.INDEMNIFICATION
    indemnifier: str = Field(..., description="Party providing indemnification")
    indemnified: str = Field(..., description="Party being indemnified")
    scope: str = Field(..., description="Types of claims/losses covered")
    third_party: bool = Field(..., description="Covers third-party claims?")


# ============================================================================
# Anomaly Detection
# ============================================================================

class AnomalyFlag(BaseModel):
    """
    A detected anomaly or risky language pattern in a clause.
    
    Examples:
        - No cap on liability
        - Automatic renewal without simple opt-out
        - One-sided termination rights
        - Very broad indemnification scope
    """
    anomaly_type: AnomalyType = Field(..., description="Type of anomaly detected")
    risk_level: RiskLevel = Field(..., description="Severity: low/medium/high/critical")
    description: str = Field(
        ..., 
        description="Human-readable explanation of why this is risky"
    )
    evidence: str = Field(
        ..., 
        description="Specific quote or excerpt from the clause supporting this flag"
    )
    recommendation: str = Field(
        ..., 
        description="Suggested action (e.g., 'negotiate cap', 'add exclusion', 'reject clause')"
    )


# ============================================================================
# Contract Summary & Analysis
# ============================================================================

class ContractAnalysisSummary(BaseModel):
    """
    High-level summary of a contract suitable for executive review.
    
    This is the output of the first-pass analysis—before human legal review.
    """
    summary: str = Field(..., description="2-3 sentence plain-English summary")
    key_obligations: List[str] = Field(..., description="Main duties of each party")
    key_rights: List[str] = Field(..., description="Main benefits/protections")
    key_risks: List[str] = Field(
        ..., 
        description="Top 3-5 risks or red flags"
    )


class ContractAnalysisResult(BaseModel):
    """
    Complete analysis result for a single contract.
    
    This is the output of the full agentic pipeline:
    Load → Classify → Extract clauses → Flag anomalies → Summarize → Await review
    """
    # Metadata
    contract_id: str = Field(..., description="Unique contract identifier")
    contract_name: str = Field(..., description="Display name (e.g., 'NDA_ACME_2024')")
    
    # Classification
    contract_type: ContractType = Field(..., description="Detected contract type")
    type_confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence in type classification (0–1)"
    )
    
    # Extracted Clauses (heterogeneous—some are specialized subtypes)
    clauses: List[ContractClause] = Field(
        ..., 
        description="All identified clauses"
    )
    
    # Anomalies
    anomalies: List[AnomalyFlag] = Field(
        default_factory=list,
        description="Detected risky language patterns"
    )
    
    # Summary
    summary: ContractAnalysisSummary = Field(
        ..., 
        description="Executive summary"
    )
    
    # Human Review Status
    requires_legal_review: bool = Field(
        ..., 
        description="Flag for escalation to legal team"
    )
    review_reason: Optional[str] = Field(
        None, 
        description="If legal review required, why?"
    )
    
    # Metadata
    source_url: Optional[str] = Field(None, description="Where contract came from")
    created_at: str = Field(..., description="ISO-8601 timestamp of analysis")
    
    @field_validator("type_confidence")
    @classmethod
    def validate_confidence(cls, v):
        """Ensure confidence is a valid probability."""
        assert 0.0 <= v <= 1.0, "Confidence must be between 0 and 1"
        return v


# ============================================================================
# Batch Processing
# ============================================================================

class ContractBatch(BaseModel):
    """
    A batch of contracts for analysis (for bulk operations).
    
    Enables:
    - Parallel processing
    - Progress tracking
    - Error handling per-contract
    """
    batch_id: str = Field(..., description="Unique batch identifier")
    contracts: List[str] = Field(..., description="List of contract file paths or IDs")
    priority: Literal["low", "normal", "high"] = Field(
        default="normal",
        description="Processing priority"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Custom metadata (client_id, project_name, etc.)"
    )


class BatchAnalysisResult(BaseModel):
    """
    Result of analyzing a batch of contracts.
    """
    batch_id: str = Field(..., description="Corresponding batch_id")
    total_contracts: int = Field(..., ge=0)
    successful: int = Field(..., ge=0, description="Number processed successfully")
    failed: int = Field(..., ge=0, description="Number that failed")
    results: List[ContractAnalysisResult] = Field(
        ..., 
        description="Successful analyses"
    )
    errors: List[dict] = Field(
        default_factory=list,
        description="Error entries: {contract_id, error_message}"
    )


# ============================================================================
# Ground Truth & Evaluation
# ============================================================================

class GroundTruthAnnotation(BaseModel):
    """
    Human-verified ground truth for a contract.
    
    Used for:
    - Training LLM prompts / few-shot examples
    - Evaluating model performance
    - Building evaluation datasets
    
    This represents the "gold standard" that an agentic system should aim to match.
    """
    contract_id: str = Field(..., description="Contract this annotation covers")
    contract_type_actual: ContractType = Field(
        ..., 
        description="Expert-verified contract type"
    )
    clauses_identified: List[ContractClause] = Field(
        ..., 
        description="Expert-identified clauses"
    )
    anomalies_actual: List[AnomalyFlag] = Field(
        ..., 
        description="Expert-verified risky language patterns"
    )
    summary_actual: ContractAnalysisSummary = Field(
        ..., 
        description="Expert summary"
    )
    legal_review_required: bool = Field(
        ..., 
        description="Expert determination: does this need legal review?"
    )
    annotator_id: str = Field(..., description="Who created this annotation?")
    annotation_date: str = Field(..., description="ISO-8601 timestamp")
    notes: Optional[str] = Field(None, description="Annotator comments/context")


class EvaluationMetrics(BaseModel):
    """
    Performance metrics comparing model output to ground truth.
    
    Tracks:
    - Contract type classification accuracy
    - Clause extraction precision/recall
    - Anomaly detection F1-score
    - Overall agreement on legal review flag
    """
    contract_id: str = Field(..., description="Contract evaluated")
    
    # Classification
    type_correct: bool = Field(..., description="Did model get type right?")
    type_model_output: Optional[str] = Field(None, description="Model's prediction")
    type_ground_truth: str = Field(..., description="Expert classification")
    
    # Clause Extraction
    clauses_precision: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Of model's clauses, % were correct"
    )
    clauses_recall: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Of expert's clauses, % did model find?"
    )
    clauses_f1: float = Field(..., ge=0.0, le=1.0, description="Harmonic mean")
    
    # Anomaly Detection
    anomalies_precision: float = Field(..., ge=0.0, le=1.0)
    anomalies_recall: float = Field(..., ge=0.0, le=1.0)
    anomalies_f1: float = Field(..., ge=0.0, le=1.0)
    
    # Review Flag Agreement
    review_flag_correct: bool = Field(
        ..., 
        description="Did model agree with expert on 'needs_legal_review'?"
    )
    
    # Overall
    overall_agreement: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Weighted average of all metrics"
    )


if __name__ == "__main__":
    # Example: Instantiate a simple contract analysis result
    example_anomaly = AnomalyFlag(
        anomaly_type=AnomalyType.UNLIMITED_LIABILITY,
        risk_level=RiskLevel.CRITICAL,
        description="Contract contains no cap on liability for either party.",
        evidence="Section 8.1: 'Provider shall be liable for all damages without limitation.'",
        recommendation="Negotiate a liability cap (e.g., 12 months of fees)"
    )
    
    example_summary = ContractAnalysisSummary(
        summary="This is a Software-as-a-Service agreement between Acme Corp (Provider) and BigCorp (Customer) for SaaS platform access. Term is 3 years with auto-renewal unless either party gives 90 days' notice.",
        key_obligations=[
            "Provider: Maintain 99.5% uptime SLA",
            "Provider: Support M-F 9–5 ET",
            "Customer: Pay $50K/year in quarterly installments",
            "Customer: Maintain confidentiality of data"
        ],
        key_rights=[
            "Customer: Can terminate for convenience with 90 days' notice",
            "Provider: Can increase price 5% annually with 60 days' notice",
            "Both: Can terminate immediately for material breach"
        ],
        key_risks=[
            "No liability cap in Section 8 (CRITICAL)",
            "SLA has 30-day credit-only remedy (no termination right)",
            "Auto-renewal language is ambiguous re: notification timing"
        ]
    )
    
    example_result = ContractAnalysisResult(
        contract_id="contract_001",
        contract_name="SaaS_Agreement_BigCorp_2024",
        contract_type=ContractType.SERVICE,
        type_confidence=0.95,
        clauses=[
            ContractClause(
                clause_id="clause_001",
                clause_type=ClauseType.TERMINATION,
                text="Either party may terminate this Agreement for any reason upon ninety (90) days' written notice to the other party...",
                start_page=2,
                end_page=2
            )
        ],
        anomalies=[example_anomaly],
        summary=example_summary,
        requires_legal_review=True,
        review_reason="Unlimited liability clause requires immediate legal negotiation",
        source_url="https://example.com/contracts/saas_001.pdf",
        created_at="2024-01-15T10:30:00Z"
    )
    
    # Serialize to JSON
    print("Example Contract Analysis Result:")
    print(example_result.model_dump_json(indent=2))
