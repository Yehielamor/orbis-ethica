"""Proposal model - represents ethical decisions to be evaluated."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from ...knowledge.models import VerifiedKnowledge


class ProposalStatus(str, Enum):
    """Status of a proposal in the deliberation pipeline."""
    
    DRAFT = "draft"                      # Being prepared
    SUBMITTED = "submitted"              # Submitted for evaluation
    UNDER_REVIEW = "under_review"        # Entities are evaluating
    REFINEMENT = "refinement"            # Creator is refining based on feedback
    VOTING = "voting"                    # In consensus voting phase
    APPROVED = "approved"                # Passed threshold
    REJECTED = "rejected"                # Failed threshold
    BURNED = "burned"                    # Flagged as corrupted/harmful
    ARCHIVED = "archived"                # Historical record


class ProposalCategory(str, Enum):
    """Categories of proposals based on impact and domain."""
    
    ROUTINE = "routine"                  # Low-impact, standard decisions
    HIGH_IMPACT = "high_impact"          # Significant consequences
    CONSTITUTIONAL = "constitutional"     # Changes to system parameters
    EMERGENCY = "emergency"              # Time-critical decisions
    RESEARCH = "research"                # Experimental/exploratory
    

class ProposalDomain(str, Enum):
    """Domain/field of the proposal."""
    
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    ENVIRONMENT = "environment"
    SECURITY = "security"
    GOVERNANCE = "governance"
    TECHNOLOGY = "technology"
    SOCIAL = "social"
    LEGAL = "legal"
    OTHER = "other"


class Proposal(BaseModel):
    """
    A proposal represents an ethical decision to be evaluated by the system.
    
    Proposals flow through the deliberation pipeline:
    1. Submission
    2. Entity evaluation (ULFR scoring)
    3. Deliberation rounds
    4. Consensus voting
    5. Decision (approve/reject/refine)
    """
    
    # Identity
    id: UUID = Field(default_factory=uuid4, description="Unique proposal identifier")
    title: str = Field(min_length=10, max_length=200, description="Brief title")
    description: str = Field(min_length=50, description="Detailed description")
    
    # Classification
    category: ProposalCategory = Field(description="Impact category")
    domain: ProposalDomain = Field(description="Domain/field")
    
    # Context
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (stakeholders, constraints, etc.)"
    )
    affected_parties: List[str] = Field(
        default_factory=list,
        description="Groups/entities affected by this decision"
    )
    precedents: List[UUID] = Field(
        default_factory=list,
        description="Related past decisions"
    )
    
    # Status
    status: ProposalStatus = Field(default=ProposalStatus.DRAFT)
    
    # Metadata
    submitter_id: Optional[str] = Field(None, description="Who submitted this")
    submitted_at: Optional[datetime] = Field(None, description="Submission timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Deliberation tracking
    deliberation_round: int = Field(default=0, description="Current round number")
    entity_evaluations: Dict[str, Any] = Field(
        default_factory=dict,
        description="Evaluations from each entity"
    )
    
    # Consensus
    weighted_vote: Optional[float] = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="Final weighted consensus vote"
    )
    threshold_required: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Threshold needed for approval"
    )
    
    # Cryptographic provenance
    content_hash: Optional[str] = Field(None, description="SHA-256 hash of content")
    signature: Optional[str] = Field(None, description="Cryptographic signature")
    ipfs_cid: Optional[str] = Field(None, description="IPFS content identifier")
    
    # Outcome
    decision_rationale: Optional[str] = Field(
        None,
        description="Explanation of final decision"
    )
    
    # Knowledge Layer Integration
    evidence: List[VerifiedKnowledge] = Field(
        default_factory=list,
        description="Verified knowledge atoms supporting this proposal"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    
    def set_threshold_by_category(self) -> None:
        """Set appropriate threshold based on proposal category."""
        thresholds = {
            ProposalCategory.ROUTINE: 0.50,
            ProposalCategory.HIGH_IMPACT: 0.70,
            ProposalCategory.CONSTITUTIONAL: 0.85,
            ProposalCategory.EMERGENCY: 0.60,
            ProposalCategory.RESEARCH: 0.55,
        }
        self.threshold_required = thresholds.get(self.category, 0.50)
    
    def advance_round(self) -> None:
        """Advance to next deliberation round."""
        self.deliberation_round += 1
        self.updated_at = datetime.utcnow()
    
    def submit(self, submitter_id: str) -> None:
        """Mark proposal as submitted."""
        self.status = ProposalStatus.SUBMITTED
        self.submitter_id = submitter_id
        self.submitted_at = datetime.utcnow()
        self.set_threshold_by_category()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "domain": self.domain.value,
            "status": self.status.value,
            "deliberation_round": self.deliberation_round,
            "weighted_vote": self.weighted_vote,
            "threshold_required": self.threshold_required,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
        }
    
    def get_summary(self) -> str:
        """Get a brief summary of the proposal."""
        return f"[{self.category.value.upper()}] {self.title} - {self.status.value}"


class ProposalTemplate(BaseModel):
    """Template for creating common types of proposals."""
    
    name: str = Field(description="Template name")
    category: ProposalCategory
    domain: ProposalDomain
    description_template: str = Field(description="Template with placeholders")
    required_context_fields: List[str] = Field(
        default_factory=list,
        description="Required context fields"
    )
    
    def create_proposal(self, **kwargs: Any) -> Proposal:
        """Create a proposal from this template."""
        description = self.description_template.format(**kwargs)
        
        return Proposal(
            title=kwargs.get("title", self.name),
            description=description,
            category=self.category,
            domain=self.domain,
            context=kwargs
        )


# Common proposal templates
HOSPITAL_TRIAGE_TEMPLATE = ProposalTemplate(
    name="Hospital Resource Allocation",
    category=ProposalCategory.HIGH_IMPACT,
    domain=ProposalDomain.HEALTHCARE,
    description_template="""
Allocate {num_beds} ICU beds among {num_patients} patients during {crisis_type}.

Proposed allocation criteria:
- {criterion_1}: {weight_1}%
- {criterion_2}: {weight_2}%
- {criterion_3}: {weight_3}%

Expected outcomes:
- Survival rate: {expected_survival}%
- Fairness (Gini): {gini_coefficient}
    """.strip(),
    required_context_fields=["num_beds", "num_patients", "crisis_type"]
)

AUTONOMOUS_SYSTEM_TEMPLATE = ProposalTemplate(
    name="Autonomous System Authorization",
    category=ProposalCategory.HIGH_IMPACT,
    domain=ProposalDomain.TECHNOLOGY,
    description_template="""
Grant authorization for autonomous system to {action} with constraints:

Constraints:
{constraints}

Safeguards:
{safeguards}

Risk assessment:
{risk_assessment}
    """.strip(),
    required_context_fields=["action", "constraints", "safeguards"]
)
