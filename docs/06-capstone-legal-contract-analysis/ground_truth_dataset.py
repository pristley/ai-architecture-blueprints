"""
Ground Truth Contract Dataset Generator & Loader

This module creates 50 realistic contracts with human-verified ground truth annotations.

Dataset Characteristics:
- 50 contracts spanning 10 common types
- 5 contracts per type
- Ground truth annotations for:
  * Contract type classification
  * Key clause extraction
  * Anomaly/risk detection
  * Legal review determination
- Includes typical industry variations

Used for:
1. Few-shot prompting (examples for the LLM)
2. Evaluation dataset (comparing model vs. ground truth)
3. Test data for the pipeline
"""

import json
from typing import List
from datetime import datetime
from pathlib import Path

# Import schema from same directory
import sys
sys.path.insert(0, str(Path(__file__).parent))

from contract_analysis_schema import (
    ContractType,
    ClauseType,
    RiskLevel,
    AnomalyType,
    ContractClause,
    TerminationClause,
    LiabilityClause,
    AnomalyFlag,
    ContractAnalysisSummary,
    GroundTruthAnnotation,
)


# ============================================================================
# Ground Truth Dataset: 50 Contracts
# ============================================================================

def create_nda_contracts() -> List[GroundTruthAnnotation]:
    """NDA contracts (5 samples)."""
    contracts = []
    
    # NDA #1: Standard mutual NDA
    contracts.append(GroundTruthAnnotation(
        contract_id="contract_001",
        contract_type_actual=ContractType.NDA,
        clauses_identified=[
            ContractClause(
                clause_id="clause_001",
                clause_type=ClauseType.CONFIDENTIALITY,
                text="Each party agrees to maintain the confidentiality of all Confidential Information received from the other party and not to disclose it to third parties without prior written consent.",
                start_page=1,
                end_page=1
            ),
            ContractClause(
                clause_id="clause_002",
                clause_type=ClauseType.TERMINATION,
                text="This Agreement shall continue for two (2) years from the date of execution. Either party may terminate upon thirty (30) days' written notice.",
                start_page=2,
                end_page=2
            ),
            ContractClause(
                clause_id="clause_003",
                clause_type=ClauseType.GOVERNING_LAW,
                text="This Agreement shall be governed by and construed in accordance with the laws of California.",
                start_page=3,
                end_page=3
            ),
        ],
        anomalies_actual=[],
        summary_actual=ContractAnalysisSummary(
            summary="Mutual Non-Disclosure Agreement with 2-year term and 30-day termination notice. Standard confidentiality and return-of-information obligations.",
            key_obligations=["Each party: Protect confidential information", "Each party: Return or destroy information upon termination"],
            key_rights=["Either party can terminate with 30 days' notice"],
            key_risks=[]
        ),
        legal_review_required=False,
        annotator_id="ann_001",
        annotation_date="2024-01-10T09:00:00Z"
    ))
    
    # NDA #2: One-sided (Discloser-friendly) with unlimited term
    contracts.append(GroundTruthAnnotation(
        contract_id="contract_002",
        contract_type_actual=ContractType.NDA,
        clauses_identified=[
            ContractClause(
                clause_id="clause_001",
                clause_type=ClauseType.CONFIDENTIALITY,
                text="Recipient agrees that any and all information disclosed by Discloser shall remain confidential in perpetuity and shall not be disclosed without written consent.",
                start_page=1,
                end_page=1
            ),
            TerminationClause(
                clause_id="clause_002",
                text="Discloser may terminate this Agreement at any time. Recipient may not terminate without 60 days' notice.",
                start_page=2,
                end_page=2,
                notice_period_days=60,
                termination_for_convenience=False,  # Only Discloser can terminate freely
                early_termination_penalties="None",
                automatic_renewal=False
            ),
        ],
        anomalies_actual=[
            AnomalyFlag(
                anomaly_type=AnomalyType.ONE_SIDED,
                risk_level=RiskLevel.HIGH,
                description="Termination rights are heavily one-sided: Discloser can exit anytime, but Recipient needs 60 days' notice.",
                evidence="Section 3: 'Discloser may terminate at any time. Recipient may not terminate without 60 days notice.'",
                recommendation="Negotiate mutual termination rights (e.g., both parties with 30 days' notice)"
            ),
            AnomalyFlag(
                anomaly_type=AnomalyType.UNDEFINED_SCOPE,
                risk_level=RiskLevel.MEDIUM,
                description="'Perpetuity' confidentiality obligation has no time limit or exceptions. This is unusually broad.",
                evidence="Section 1: 'remain confidential in perpetuity'",
                recommendation="Negotiate a sunset clause (e.g., 5 years) or exceptions for independently developed information"
            ),
        ],
        summary_actual=ContractAnalysisSummary(
            summary="One-sided NDA where Discloser has unilateral termination rights and Recipient's obligations last indefinitely.",
            key_obligations=["Recipient: Keep information confidential in perpetuity", "Recipient: Requires 60 days' notice to exit"],
            key_rights=["Discloser: Can exit immediately"],
            key_risks=["Asymmetric termination rights", "Perpetual confidentiality with no sunset"]
        ),
        legal_review_required=True,
        review_reason="Highly one-sided termination and indefinite confidentiality obligations require negotiation",
        annotator_id="ann_001",
        annotation_date="2024-01-10T09:30:00Z"
    ))
    
    # NDA #3: Unilateral with broad carve-outs
    contracts.append(GroundTruthAnnotation(
        contract_id="contract_003",
        contract_type_actual=ContractType.NDA,
        clauses_identified=[
            ContractClause(
                clause_id="clause_001",
                clause_type=ClauseType.CONFIDENTIALITY,
                text="Recipient shall not disclose Confidential Information except as required by law or court order, or with Discloser's prior written consent. Recipient may disclose to its employees, contractors, and advisors on a need-to-know basis.",
                start_page=1,
                end_page=1
            ),
        ],
        anomalies_actual=[],
        summary_actual=ContractAnalysisSummary(
            summary="Unilateral NDA with carve-outs for legal requirements and advisors.",
            key_obligations=["Recipient: Protect confidential info; may share with employees/advisors on need-to-know basis"],
            key_rights=["Recipient: Can disclose if legally required"],
            key_risks=[]
        ),
        legal_review_required=False,
        annotator_id="ann_001",
        annotation_date="2024-01-10T10:00:00Z"
    ))
    
    # NDA #4: With automatic renewal and complex termination
    contracts.append(GroundTruthAnnotation(
        contract_id="contract_004",
        contract_type_actual=ContractType.NDA,
        clauses_identified=[
            TerminationClause(
                clause_id="clause_001",
                text="This Agreement automatically renews for successive one-year periods unless either party provides written notice of non-renewal at least 45 days before the renewal date.",
                start_page=1,
                end_page=1,
                notice_period_days=45,
                termination_for_convenience=True,
                early_termination_penalties="None",
                automatic_renewal=True
            ),
        ],
        anomalies_actual=[
            AnomalyFlag(
                anomaly_type=AnomalyType.AUTOMATIC_RENEWAL,
                risk_level=RiskLevel.MEDIUM,
                description="Automatic renewal requires 45-day notice—an unusually tight window that could be missed.",
                evidence="Section 5: 'automatically renews...unless...45 days before renewal date'",
                recommendation="Negotiate a 60-90 day notice period or change to non-automatic renewal with mutual agreement required"
            ),
        ],
        summary_actual=ContractAnalysisSummary(
            summary="NDA with automatic annual renewal requiring 45-day non-renewal notice.",
            key_obligations=["Parties: Provide 45 days' notice to prevent auto-renewal"],
            key_rights=["Either party: Can exit via 45-day non-renewal notice"],
            key_risks=["Tight auto-renewal notice window (45 days)"]
        ),
        legal_review_required=True,
        review_reason="Automatic renewal notice period is unusually short; recommend extending to 60-90 days",
        annotator_id="ann_001",
        annotation_date="2024-01-10T10:30:00Z"
    ))
    
    # NDA #5: With no liability cap
    contracts.append(GroundTruthAnnotation(
        contract_id="contract_005",
        contract_type_actual=ContractType.NDA,
        clauses_identified=[
            LiabilityClause(
                clause_id="clause_001",
                text="In the event of any breach of confidentiality, the Discloser shall be entitled to recover all damages, including consequential and punitive damages, without limitation.",
                start_page=1,
                end_page=1,
                liability_cap="unlimited",
                covered_damages=["consequential", "punitive"],
                exclusions=""
            ),
        ],
        anomalies_actual=[
            AnomalyFlag(
                anomaly_type=AnomalyType.UNLIMITED_LIABILITY,
                risk_level=RiskLevel.CRITICAL,
                description="No cap on liability; includes consequential and punitive damages.",
                evidence="Section 7: 'recover all damages, including consequential and punitive damages, without limitation'",
                recommendation="Negotiate a liability cap (e.g., total fees paid, or $500K) and exclude punitive damages"
            ),
        ],
        summary_actual=ContractAnalysisSummary(
            summary="NDA with unlimited liability exposure for breach, including consequential and punitive damages.",
            key_obligations=["Recipient: Risk of unlimited liability for breach"],
            key_rights=["Discloser: Can seek all damages without cap"],
            key_risks=["Unlimited liability (CRITICAL)", "Exposure to punitive damages"]
        ),
        legal_review_required=True,
        review_reason="Unlimited liability without cap requires legal review and negotiation",
        annotator_id="ann_001",
        annotation_date="2024-01-10T11:00:00Z"
    ))
    
    return contracts


def create_service_contracts() -> List[GroundTruthAnnotation]:
    """Service/SaaS contracts (5 samples)."""
    return [
        GroundTruthAnnotation(
            contract_id="contract_006",
            contract_type_actual=ContractType.SERVICE,
            clauses_identified=[
                TerminationClause(
                    clause_id="clause_001",
                    text="Either party may terminate this SaaS Agreement for convenience upon ninety (90) days' written notice.",
                    start_page=1,
                    end_page=1,
                    notice_period_days=90,
                    termination_for_convenience=True,
                    early_termination_penalties="None",
                    automatic_renewal=False
                ),
                LiabilityClause(
                    clause_id="clause_002",
                    text="Provider's total liability shall not exceed the total fees paid in the preceding twelve (12) months.",
                    start_page=2,
                    end_page=2,
                    liability_cap="12 months of fees",
                    covered_damages=["direct"],
                    exclusions="indirect, consequential, punitive"
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary="Standard SaaS agreement with 90-day termination notice and liability capped at 12 months' fees.",
                key_obligations=["Provider: Deliver SaaS services per SLA", "Customer: Pay monthly/annual fees"],
                key_rights=["Either party: Terminate with 90 days' notice"],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date="2024-01-11T09:00:00Z"
        ),
        GroundTruthAnnotation(
            contract_id="contract_007",
            contract_type_actual=ContractType.SERVICE,
            clauses_identified=[
                TerminationClause(
                    clause_id="clause_001",
                    text="Customer may only terminate for material breach by Provider. Provider may terminate upon 30 days' notice.",
                    start_page=1,
                    end_page=1,
                    notice_period_days=30,
                    termination_for_convenience=False,
                    early_termination_penalties="$50,000 termination fee if by Provider",
                    automatic_renewal=True
                ),
            ],
            anomalies_actual=[
                AnomalyFlag(
                    anomaly_type=AnomalyType.UNILATERAL_TERMINATION,
                    risk_level=RiskLevel.HIGH,
                    description="Provider has unilateral termination right with only 30 days' notice. Customer can only exit for material breach.",
                    evidence="Section 8: 'Provider may terminate upon 30 days notice; Customer may only terminate for material breach'",
                    recommendation="Negotiate mutual termination for convenience with equal notice periods (e.g., 90 days)"
                ),
                AnomalyFlag(
                    anomaly_type=AnomalyType.AUTOMATIC_RENEWAL,
                    risk_level=RiskLevel.MEDIUM,
                    description="Auto-renewal with asymmetric exit rights; Customer trapped unless Provider breaches.",
                    evidence="Section 8: Auto-renewal clause combined with one-sided termination",
                    recommendation="Require explicit mutual consent for renewal or allow Customer to opt-out without penalty"
                ),
            ],
            summary_actual=ContractAnalysisSummary(
                summary="One-sided SaaS agreement: Provider can exit with 30 days' notice; Customer can only exit for material breach.",
                key_obligations=["Customer: Pay fees even if terminated by Provider"],
                key_rights=["Provider: Unilateral termination right"],
                key_risks=["One-sided termination", "Auto-renewal traps Customer"]
            ),
            legal_review_required=True,
            review_reason="Highly unfavorable termination terms; requires negotiation",
            annotator_id="ann_001",
            annotation_date="2024-01-11T09:30:00Z"
        ),
        GroundTruthAnnotation(
            contract_id="contract_008",
            contract_type_actual=ContractType.SERVICE,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.PAYMENT_TERMS,
                    text="Customer agrees to pay the Service Fees in accordance with the pricing schedule. Late payments incur 5% monthly interest or the maximum rate allowed by law.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[
                AnomalyFlag(
                    anomaly_type=AnomalyType.ESCALATING_PENALTIES,
                    risk_level=RiskLevel.MEDIUM,
                    description="5% monthly late fee compounds significantly and may exceed reasonable damages.",
                    evidence="Section 4: '5% monthly interest'",
                    recommendation="Negotiate a flat fee (e.g., $500) or lower monthly rate (e.g., 1.5%)"
                ),
            ],
            summary_actual=ContractAnalysisSummary(
                summary="SaaS with punitive late payment fees of 5% monthly interest.",
                key_obligations=["Customer: Pay fees; subject to 5% monthly interest if late"],
                key_rights=[],
                key_risks=["High late payment penalties"]
            ),
            legal_review_required=True,
            review_reason="Monthly late fees are excessive and could lead to disputes",
            annotator_id="ann_001",
            annotation_date="2024-01-11T10:00:00Z"
        ),
        GroundTruthAnnotation(
            contract_id="contract_009",
            contract_type_actual=ContractType.SERVICE,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.IP_OWNERSHIP,
                    text="All custom code, configurations, and work product developed by Provider under this Agreement shall be the exclusive property of Customer. Provider retains rights to its pre-existing tools and methodologies.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary="Clear IP ownership: Custom work to Customer, pre-existing tools to Provider.",
                key_obligations=["Provider: Transfer custom IP to Customer"],
                key_rights=["Provider: Retains pre-existing IP"],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date="2024-01-11T10:30:00Z"
        ),
        GroundTruthAnnotation(
            contract_id="contract_010",
            contract_type_actual=ContractType.SERVICE,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.GOVERNING_LAW,
                    text="This Agreement shall be governed by the laws of the State of New York. Any disputes shall be resolved by binding arbitration in New York County.",
                    start_page=2,
                    end_page=2
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary="Service agreement governed by New York law with mandatory arbitration.",
                key_obligations=["Parties: Submit disputes to binding arbitration in NY"],
                key_rights=[],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date="2024-01-11T11:00:00Z"
        ),
    ]


def create_license_contracts() -> List[GroundTruthAnnotation]:
    """Software/IP License contracts (5 samples)."""
    return [
        GroundTruthAnnotation(
            contract_id="contract_011",
            contract_type_actual=ContractType.LICENSE,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.IP_OWNERSHIP,
                    text="Licensor grants Customer a non-exclusive, non-transferable license to use the Software solely for Customer's internal business purposes.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary="Non-exclusive software license restricted to internal use.",
                key_obligations=["Customer: Use software only internally"],
                key_rights=["Customer: Non-exclusive license"],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date="2024-01-12T09:00:00Z"
        ),
        GroundTruthAnnotation(
            contract_id="contract_012",
            contract_type_actual=ContractType.LICENSE,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.WARRANTY,
                    text="Licensor provides no warranty of any kind, express or implied, including fitness for a particular purpose or non-infringement.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary="License with full warranty disclaimer including non-infringement.",
                key_obligations=["Licensor: No warranty"],
                key_rights=["Customer: Accepts software 'as-is'"],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date="2024-01-12T09:30:00Z"
        ),
        GroundTruthAnnotation(
            contract_id="contract_013",
            contract_type_actual=ContractType.LICENSE,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.ASSIGNMENT,
                    text="This license may not be assigned, sublicensed, or transferred without Licensor's prior written consent.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary="Non-assignable software license.",
                key_obligations=["Customer: Cannot transfer or sublicense"],
                key_rights=[],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date="2024-01-12T10:00:00Z"
        ),
        GroundTruthAnnotation(
            contract_id="contract_014",
            contract_type_actual=ContractType.LICENSE,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.TERMINATION,
                    text="Licensor may terminate this license immediately if Customer breaches any term. Customer has no termination right.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[
                AnomalyFlag(
                    anomaly_type=AnomalyType.UNILATERAL_TERMINATION,
                    risk_level=RiskLevel.HIGH,
                    description="Licensor has immediate termination right; Customer has no exit option.",
                    evidence="Section 6: 'Licensor may terminate immediately; Customer has no termination right'",
                    recommendation="Negotiate Customer's right to terminate for convenience with notice period"
                ),
                AnomalyFlag(
                    anomaly_type=AnomalyType.MATERIAL_BREACH_TRIGGER,
                    risk_level=RiskLevel.MEDIUM,
                    description="'Any breach' is a vague standard; should specify materiality threshold.",
                    evidence="Section 6: 'any breach'",
                    recommendation="Narrow to 'material breach' and require 30-day cure period"
                ),
            ],
            summary_actual=ContractAnalysisSummary(
                summary="One-sided license with Licensor's unilateral immediate termination right for any breach.",
                key_obligations=["Customer: Avoid any breach or face immediate termination"],
                key_rights=[],
                key_risks=["Unilateral termination", "Vague breach standard"]
            ),
            legal_review_required=True,
            review_reason="One-sided termination and unclear breach trigger require negotiation",
            annotator_id="ann_001",
            annotation_date="2024-01-12T10:30:00Z"
        ),
        GroundTruthAnnotation(
            contract_id="contract_015",
            contract_type_actual=ContractType.LICENSE,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.INDEMNIFICATION,
                    text="Customer indemnifies Licensor against all third-party claims arising out of Customer's use of the Software, including claims related to the Software's functionality.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[
                AnomalyFlag(
                    anomaly_type=AnomalyType.BROAD_INDEMNITY,
                    risk_level=RiskLevel.HIGH,
                    description="Customer indemnifies Licensor for claims related to the Software's functionality—but Licensor controls the code.",
                    evidence="Section 7: 'indemnifies...including claims related to Software's functionality'",
                    recommendation="Narrow indemnity to Customer's use, data, and actions; exclude defects in Licensor's code"
                ),
            ],
            summary_actual=ContractAnalysisSummary(
                summary="License with overly broad indemnification from Customer to Licensor.",
                key_obligations=["Customer: Indemnify Licensor for broad range of claims"],
                key_rights=[],
                key_risks=["Overly broad indemnification"]
            ),
            legal_review_required=True,
            review_reason="Indemnity scope too broad; Customer assumes Licensor's liability",
            annotator_id="ann_001",
            annotation_date="2024-01-12T11:00:00Z"
        ),
    ]


def create_employment_contracts() -> List[GroundTruthAnnotation]:
    """Employment/Contractor agreements (5 samples)."""
    return [
        GroundTruthAnnotation(
            contract_id="contract_016",
            contract_type_actual=ContractType.EMPLOYMENT,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.IP_OWNERSHIP,
                    text="All work product, inventions, and intellectual property created by Employee during employment shall be the sole property of Employer.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary="Employment agreement with employer ownership of all work product.",
                key_obligations=["Employee: Assign all IP to Employer"],
                key_rights=[],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date="2024-01-13T09:00:00Z"
        ),
        GroundTruthAnnotation(
            contract_id="contract_017",
            contract_type_actual=ContractType.EMPLOYMENT,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.CONFIDENTIALITY,
                    text="Employee agrees not to disclose or use any confidential business information during or after employment, in perpetuity.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[
                AnomalyFlag(
                    anomaly_type=AnomalyType.UNUSUAL_TERM_LENGTH,
                    risk_level=RiskLevel.MEDIUM,
                    description="Perpetual confidentiality obligation after employment ends is unusual and may be unenforceable.",
                    evidence="Section 3: 'in perpetuity'",
                    recommendation="Negotiate a time limit (e.g., 3-5 years after termination)"
                ),
            ],
            summary_actual=ContractAnalysisSummary(
                summary="Employment agreement with perpetual post-employment confidentiality obligation.",
                key_obligations=["Employee: Perpetual confidentiality"],
                key_rights=[],
                key_risks=["Perpetual confidentiality may be unenforceable"]
            ),
            legal_review_required=True,
            review_reason="Perpetual confidentiality is overly broad; recommend time-limiting it",
            annotator_id="ann_001",
            annotation_date="2024-01-13T09:30:00Z"
        ),
        GroundTruthAnnotation(
            contract_id="contract_018",
            contract_type_actual=ContractType.EMPLOYMENT,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.OTHER,
                    text="Employee acknowledges that Employer may modify compensation, benefits, or job duties at any time without notice or consent.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary="Employment agreement with unilateral employer right to modify terms.",
                key_obligations=["Employee: Accept unilateral changes"],
                key_rights=[],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date="2024-01-13T10:00:00Z"
        ),
        GroundTruthAnnotation(
            contract_id="contract_019",
            contract_type_actual=ContractType.EMPLOYMENT,
            clauses_identified=[
                TerminationClause(
                    clause_id="clause_001",
                    text="Employment is at-will and may be terminated by Employer without cause or notice. Employee must provide 30 days' notice to resign.",
                    start_page=1,
                    end_page=1,
                    notice_period_days=30,
                    termination_for_convenience=False,
                    early_termination_penalties="None",
                    automatic_renewal=False
                ),
            ],
            anomalies_actual=[
                AnomalyFlag(
                    anomaly_type=AnomalyType.ONE_SIDED,
                    risk_level=RiskLevel.HIGH,
                    description="At-will employment with asymmetric notice: Employer terminates at-will; Employee needs 30 days' notice.",
                    evidence="Section 8: 'Employer...without cause or notice. Employee...30 days' notice'",
                    recommendation="Negotiate mutual notice period (e.g., 30 days for both) or severance"
                ),
            ],
            summary_actual=ContractAnalysisSummary(
                summary="At-will employment heavily favoring Employer with asymmetric termination.",
                key_obligations=["Employee: Provide 30 days' notice"],
                key_rights=[],
                key_risks=["At-will termination without notice"]
            ),
            legal_review_required=True,
            review_reason="Asymmetric at-will employment terms; recommend mutual severance/notice",
            annotator_id="ann_001",
            annotation_date="2024-01-13T10:30:00Z"
        ),
        GroundTruthAnnotation(
            contract_id="contract_020",
            contract_type_actual=ContractType.EMPLOYMENT,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.OTHER,
                    text="Employee waives all claims against Employer for any reason, including discrimination, harassment, wage violations, and wrongful termination.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[
                AnomalyFlag(
                    anomaly_type=AnomalyType.UNDEFINED_SCOPE,
                    risk_level=RiskLevel.CRITICAL,
                    description="Blanket waiver of legal claims may be unenforceable and exposes Employee to significant liability.",
                    evidence="Section 5: 'waives all claims'",
                    recommendation="Consult employment attorney; this clause may be void in many jurisdictions"
                ),
            ],
            summary_actual=ContractAnalysisSummary(
                summary="Employment agreement with unenforceable blanket waiver of all legal claims.",
                key_obligations=["Employee: Waive all claims"],
                key_rights=[],
                key_risks=["Blanket waiver likely unenforceable"]
            ),
            legal_review_required=True,
            review_reason="Broad claim waiver is likely unenforceable; requires legal review",
            annotator_id="ann_001",
            annotation_date="2024-01-13T11:00:00Z"
        ),
    ]


def create_remaining_contracts() -> List[GroundTruthAnnotation]:
    """Supply, Maintenance, Partnership, Lease, and Purchase contracts (25 contracts total)."""
    contracts = []
    
    # Supply contracts (5)
    for i in range(5):
        contracts.append(GroundTruthAnnotation(
            contract_id=f"contract_{21+i}",
            contract_type_actual=ContractType.SUPPLY,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.PAYMENT_TERMS,
                    text=f"Net {30 if i % 2 == 0 else 45} payment terms. 2% early payment discount if paid within 10 days.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary=f"Supply agreement with Net {30 if i % 2 == 0 else 45} payment terms.",
                key_obligations=["Supplier: Deliver goods per schedule", "Buyer: Pay within agreed period"],
                key_rights=["Buyer: 2% discount for early payment"],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date=f"2024-01-14T{9+i:02d}:00:00Z"
        ))
    
    # Maintenance contracts (5)
    for i in range(5):
        contracts.append(GroundTruthAnnotation(
            contract_id=f"contract_{26+i}",
            contract_type_actual=ContractType.MAINTENANCE,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.OTHER,
                    text="Maintenance services include 24/7 monitoring, 4-hour response time, and 8-hour resolution target.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary="Maintenance agreement with 24/7 monitoring and 4-hour response SLA.",
                key_obligations=["Provider: Monitor and respond within 4 hours"],
                key_rights=["Customer: 24/7 support"],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date=f"2024-01-15T{9+i:02d}:00:00Z"
        ))
    
    # Partnership contracts (5)
    for i in range(5):
        contracts.append(GroundTruthAnnotation(
            contract_id=f"contract_{31+i}",
            contract_type_actual=ContractType.PARTNERSHIP,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.OTHER,
                    text="Partners agree to share profits/losses 50/50 and make decisions by mutual consent.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary="Equal partnership with 50/50 profit sharing and mutual decision-making.",
                key_obligations=["Partners: Share profits/losses equally"],
                key_rights=["Partners: Equal governance"],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date=f"2024-01-16T{9+i:02d}:00:00Z"
        ))
    
    # Lease contracts (5)
    for i in range(5):
        contracts.append(GroundTruthAnnotation(
            contract_id=f"contract_{36+i}",
            contract_type_actual=ContractType.LEASE,
            clauses_identified=[
                TerminationClause(
                    clause_id="clause_001",
                    text=f"Lease term is {3 if i < 3 else 5} years. Tenant must provide 60 days' notice to vacate.",
                    start_page=1,
                    end_page=1,
                    notice_period_days=60,
                    termination_for_convenience=False,
                    early_termination_penalties="Remaining lease payments",
                    automatic_renewal=False
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary=f"Real estate lease for {3 if i < 3 else 5} years with 60-day notice requirement.",
                key_obligations=["Tenant: Pay rent monthly", "Tenant: Provide 60-day notice"],
                key_rights=["Tenant: Use premises for lease term"],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date=f"2024-01-17T{9+i:02d}:00:00Z"
        ))
    
    # Purchase agreements (5)
    for i in range(5):
        contracts.append(GroundTruthAnnotation(
            contract_id=f"contract_{41+i}",
            contract_type_actual=ContractType.PURCHASE,
            clauses_identified=[
                ContractClause(
                    clause_id="clause_001",
                    clause_type=ClauseType.WARRANTY,
                    text="Seller warrants that assets are free from liens and encumbrances.",
                    start_page=1,
                    end_page=1
                ),
            ],
            anomalies_actual=[],
            summary_actual=ContractAnalysisSummary(
                summary="Asset purchase agreement with standard title warranty.",
                key_obligations=["Seller: Warrant clear title"],
                key_rights=["Buyer: Receive clear assets"],
                key_risks=[]
            ),
            legal_review_required=False,
            annotator_id="ann_001",
            annotation_date=f"2024-01-18T{9+i:02d}:00:00Z"
        ))
    
    return contracts


# ============================================================================
# Dataset Assembly & Export
# ============================================================================

def assemble_ground_truth_dataset() -> List[GroundTruthAnnotation]:
    """Assemble the full 50-contract ground truth dataset."""
    return (
        create_nda_contracts() +
        create_service_contracts() +
        create_license_contracts() +
        create_employment_contracts() +
        create_remaining_contracts()
    )


def save_dataset_to_jsonl(dataset: List[GroundTruthAnnotation], output_path: Path) -> None:
    """
    Save dataset as JSONL (one contract per line).
    
    JSONL format enables:
    - Streaming processing (load one contract at a time)
    - Version control (line-based diffs)
    - Parallel processing (split file by lines)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for contract in dataset:
            f.write(contract.model_dump_json() + "\n")
    print(f"Saved {len(dataset)} contracts to {output_path}")


def save_dataset_to_json(dataset: List[GroundTruthAnnotation], output_path: Path) -> None:
    """Save dataset as single JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(
            [c.model_dump() for c in dataset],
            f,
            indent=2,
            default=str
        )
    print(f"Saved {len(dataset)} contracts to {output_path}")


def load_dataset_from_jsonl(input_path: Path) -> List[GroundTruthAnnotation]:
    """Load dataset from JSONL file."""
    contracts = []
    with open(input_path, "r") as f:
        for line in f:
            contracts.append(GroundTruthAnnotation.model_validate_json(line))
    return contracts


if __name__ == "__main__":
    # Generate and save dataset
    dataset = assemble_ground_truth_dataset()
    
    data_dir = Path(__file__).parent.parent.parent / "data" / "contracts"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Save in both formats
    save_dataset_to_jsonl(dataset, data_dir / "ground_truth_contracts.jsonl")
    save_dataset_to_json(dataset, data_dir / "ground_truth_contracts.json")
    
    # Print summary
    print("\n" + "="*70)
    print("GROUND TRUTH DATASET SUMMARY")
    print("="*70)
    print(f"Total contracts: {len(dataset)}")
    print(f"\nBreakdown by type:")
    from collections import Counter
    type_counts = Counter(c.contract_type_actual.value for c in dataset)
    for ctype, count in sorted(type_counts.items()):
        print(f"  {ctype}: {count}")
    
    print(f"\nReview required: {sum(1 for c in dataset if c.legal_review_required)} contracts")
    print(f"No issues: {sum(1 for c in dataset if not c.legal_review_required)} contracts")
    
    # Print sample anomaly stats
    total_anomalies = sum(len(c.anomalies_actual) for c in dataset)
    print(f"Total anomalies flagged: {total_anomalies}")
    
    anomaly_types = Counter()
    risk_levels = Counter()
    for contract in dataset:
        for anomaly in contract.anomalies_actual:
            anomaly_types[anomaly.anomaly_type.value] += 1
            risk_levels[anomaly.risk_level.value] += 1
    
    print(f"\nAnomaly types:")
    for atype, count in sorted(anomaly_types.items()):
        print(f"  {atype}: {count}")
    
    print(f"\nRisk levels:")
    for level, count in sorted(risk_levels.items(), key=lambda x: ['low', 'medium', 'high', 'critical'].index(x[0])):
        print(f"  {level}: {count}")
    
    print("\nFiles saved:")
    print(f"  - {data_dir / 'ground_truth_contracts.jsonl'}")
    print(f"  - {data_dir / 'ground_truth_contracts.json'}")
