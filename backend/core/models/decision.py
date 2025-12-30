"""Decision model - represents the outcome of ethical deliberation."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from .ulfr import ULFRScore, ULFRWeights


class DecisionOutcome(str, Enum):
    """Possible outcomes of the deliberation process."""
    
    APPROVED = "approved"            # Passed threshold
    REJECTED = "rejected"            # Failed threshold
    REFINED = "refined"              # Sent back for refinement
    ESCALATED = "escalated"          # Escalated to Assembly
    BURNED = "burned"                # Flagged as corrupted
    PENDING = "pending"              # Still in deliberation


class EntityEvaluation(BaseModel):
    """Evaluation from a single cognitive entity."""
    
    entity_id: UUID = Field(description="Entity identifier")
    entity_type: str = Field(description="Entity type (seeker, healer, etc.)")
    
    # ULFR scores
    ulfr_score: ULFRScore = Field(description="ULFR evaluation")
    
    # Vote
    vote: int = Field(ge=-1, le=1, description="Vote: -1 (reject), 0 (abstain), 1 (approve)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in evaluation")
    
    # Reasoning
    reasoning: str = Field(description="Explanation of evaluation")
    concerns: List[str] = Field(default_factory=list, description="Specific concerns raised")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Suggestions for improvement"
    )
    
    # Evidence cited
    evidence_cited: List[str] = Field(
        default_factory=list,
        description="Sources/precedents cited"
    )
    
    # Metadata
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Cryptographic signature
    signature: Optional[str] = Field(None, description="Entity's signature on evaluation")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": str(self.entity_id),
            "entity_type": self.entity_type,
            "ulfr_score": self.ulfr_score.to_dict(),
            "vote": self.vote,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "concerns": self.concerns,
            "recommendations": self.recommendations,
        }


class Decision(BaseModel):
    """
    Decision represents the final outcome of ethical deliberation.
    
    Contains:
    - All entity evaluations
    - Weighted consensus calculation
    - Final outcome and rationale
    - Cryptographic proof
    - Link to memory graph
    """
    
    # Identity
    id: UUID = Field(default_factory=uuid4)
    proposal_id: UUID = Field(description="Proposal being decided")
    
    # Evaluations
    entity_evaluations: List[EntityEvaluation] = Field(
        default_factory=list,
        description="Evaluations from all entities"
    )
    
    # Consensus calculation
    weights_used: ULFRWeights = Field(description="Weights used in calculation")
    weighted_vote: float = Field(description="Final weighted vote score")
    threshold_required: float = Field(description="Threshold needed for approval")
    quorum_met: bool = Field(description="Whether quorum was achieved")
    
    # Outcome
    outcome: DecisionOutcome = Field(description="Final decision outcome")
    rationale: str = Field(description="Explanation of decision")
    
    # Deliberation history
    deliberation_rounds: int = Field(default=1, description="Number of rounds")
    refinements_made: List[str] = Field(
        default_factory=list,
        description="Refinements applied during deliberation"
    )
    
    # Precedent
    precedents_cited: List[UUID] = Field(
        default_factory=list,
        description="Past decisions referenced"
    )
    creates_precedent: bool = Field(
        default=False,
        description="Whether this creates new precedent"
    )
    precedent_summary: Optional[str] = Field(
        None,
        description="Summary of precedent if applicable"
    )
    
    # Metadata
    decided_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Cryptographic provenance
    merkle_root: Optional[str] = Field(
        None,
        description="Merkle root of all evaluations"
    )
    content_hash: Optional[str] = Field(None, description="SHA-256 of decision")
    ipfs_cid: Optional[str] = Field(None, description="IPFS content identifier")
    
    # Memory graph
    graph_node_id: Optional[str] = Field(
        None,
        description="Node ID in distributed memory graph"
    )
    
    # Appeal
    appealable: bool = Field(default=True, description="Can this be appealed?")
    appeal_window_days: int = Field(default=7, description="Days to appeal")
    appeals: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Appeals filed"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    
    def calculate_weighted_vote(self) -> float:
        """
        Calculate weighted consensus vote.
        
        Formula: weighted_vote = Σ(w_i · v_i) / Σ(w_i)
        where w_i is entity reputation and v_i is vote (-1, 0, 1)
        
        Returns:
            Weighted vote score in range [-1, 1]
        """
        if not self.entity_evaluations:
            return 0.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for eval in self.entity_evaluations:
            # In real implementation, fetch entity reputation
            # For now, assume equal weights
            weight = 1.0
            weighted_sum += weight * eval.vote
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def check_quorum(self, required_participation: float = 0.6) -> bool:
        """
        Check if quorum is met.
        
        Args:
            required_participation: Minimum fraction of entities that must participate
            
        Returns:
            True if quorum met
        """
        # In real implementation, check against total active entities
        # For now, simple check
        return len(self.entity_evaluations) >= 3
    
    def determine_outcome(self) -> DecisionOutcome:
        """
        Determine final outcome based on weighted vote and threshold.
        
        Returns:
            DecisionOutcome
        """
        if not self.quorum_met:
            return DecisionOutcome.REJECTED
        
        if self.weighted_vote >= self.threshold_required:
            return DecisionOutcome.APPROVED
        elif self.weighted_vote >= (self.threshold_required - 0.15):
            # Close to threshold - send for refinement
            return DecisionOutcome.REFINED
        else:
            return DecisionOutcome.REJECTED
    
    def get_consensus_summary(self) -> str:
        """Get human-readable summary of consensus."""
        approve_count = sum(1 for e in self.entity_evaluations if e.vote == 1)
        reject_count = sum(1 for e in self.entity_evaluations if e.vote == -1)
        abstain_count = sum(1 for e in self.entity_evaluations if e.vote == 0)
        
        return (
            f"Vote: {self.weighted_vote:.3f} (threshold: {self.threshold_required:.2f})\n"
            f"Entities: {approve_count} approve, {reject_count} reject, "
            f"{abstain_count} abstain\n"
            f"Outcome: {self.outcome.value.upper()}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "proposal_id": str(self.proposal_id),
            "outcome": self.outcome.value,
            "weighted_vote": self.weighted_vote,
            "threshold_required": self.threshold_required,
            "quorum_met": self.quorum_met,
            "deliberation_rounds": self.deliberation_rounds,
            "decided_at": self.decided_at.isoformat(),
            "entity_evaluations": [e.to_dict() for e in self.entity_evaluations],
        }
    
    def get_explainability_report(self) -> Dict[str, Any]:
        """
        Generate explainability report for transparency.
        
        Returns:
            Dictionary with detailed explanation of decision
        """
        return {
            "decision_id": str(self.id),
            "outcome": self.outcome.value,
            "rationale": self.rationale,
            "consensus_summary": self.get_consensus_summary(),
            "entity_evaluations": [
                {
                    "entity": e.entity_type,
                    "vote": "approve" if e.vote == 1 else "reject" if e.vote == -1 else "abstain",
                    "reasoning": e.reasoning,
                    "concerns": e.concerns,
                    "recommendations": e.recommendations,
                }
                for e in self.entity_evaluations
            ],
            "precedents_cited": [str(p) for p in self.precedents_cited],
            "refinements_made": self.refinements_made,
            "appealable": self.appealable,
            "appeal_window_days": self.appeal_window_days,
        }
