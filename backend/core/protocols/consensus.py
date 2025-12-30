"""Consensus Protocol - Weighted voting and decision logic."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..models import Proposal, Decision, DecisionOutcome, ULFRWeights
from ..models.decision import EntityEvaluation


class ThresholdType(str, Enum):
    """Types of decision thresholds."""
    
    ROUTINE = "routine"                  # τ = 0.50
    HIGH_IMPACT = "high_impact"          # τ = 0.70
    CONSTITUTIONAL = "constitutional"     # τ = 0.85
    EMERGENCY = "emergency"              # τ = 0.60


@dataclass
class ConsensusResult:
    """Result of consensus calculation."""
    
    weighted_vote: float
    threshold_required: float
    quorum_met: bool
    outcome: DecisionOutcome
    rationale: str
    entity_votes: Dict[str, int]
    entity_weights: Dict[str, float]


class ConsensusProtocol:
    """
    Implements the Ethical Consensus Protocol from the whitepaper.
    
    Algorithm:
    1. Check quorum (minimum participation)
    2. Calculate weighted vote: Σ(w_i · v_i) / Σ(w_i)
    3. Compare to threshold:
       - If weighted_vote ≥ τ: APPROVE
       - If weighted_vote ≥ τ_min: REFINE (close to threshold)
       - Else: REJECT
    """
    
    def __init__(
        self,
        quorum: float = 0.6,
        refinement_margin: float = 0.15,
        weights: Optional[ULFRWeights] = None
    ):
        """
        Initialize consensus protocol.
        
        Args:
            quorum: Minimum participation rate (default 0.6 = 60%)
            refinement_margin: How close to threshold triggers refinement (default 0.15)
            weights: ULFR weights for scoring (optional)
        """
        self.quorum = quorum
        self.refinement_margin = refinement_margin
        self.weights = weights or ULFRWeights()
        
        # Thresholds from whitepaper
        self.thresholds = {
            ThresholdType.ROUTINE: 0.50,
            ThresholdType.HIGH_IMPACT: 0.70,
            ThresholdType.CONSTITUTIONAL: 0.85,
            ThresholdType.EMERGENCY: 0.60,
        }
    
    def get_threshold(self, proposal: Proposal) -> float:
        """
        Get appropriate threshold for proposal.
        
        Args:
            proposal: Proposal being evaluated
            
        Returns:
            Threshold value (0.0-1.0)
        """
        # Map proposal category to threshold type
        category_map = {
            "routine": ThresholdType.ROUTINE,
            "high_impact": ThresholdType.HIGH_IMPACT,
            "constitutional": ThresholdType.CONSTITUTIONAL,
            "emergency": ThresholdType.EMERGENCY,
        }
        
        threshold_type = category_map.get(
            proposal.category.value,
            ThresholdType.ROUTINE
        )
        
        return self.thresholds[threshold_type]
    
    def check_quorum(
        self,
        evaluations: List[EntityEvaluation],
        total_entities: int
    ) -> bool:
        """
        Check if quorum is met.
        
        Args:
            evaluations: Entity evaluations received
            total_entities: Total number of active entities
            
        Returns:
            True if quorum met
        """
        if total_entities == 0:
            return False
        
        participation_rate = len(evaluations) / total_entities
        return participation_rate >= self.quorum
    
    def calculate_weighted_vote(
        self,
        evaluations: List[EntityEvaluation],
        entity_reputations: Optional[Dict[str, float]] = None
    ) -> tuple[float, Dict[str, float]]:
        """
        Calculate weighted consensus vote.
        
        Formula: weighted_vote = Σ(w_i · v_i) / Σ(w_i)
        
        where:
        - w_i = entity reputation (weight)
        - v_i = entity vote (-1, 0, 1)
        
        Args:
            evaluations: List of entity evaluations
            entity_reputations: Optional dict of entity_id -> reputation
            
        Returns:
            Tuple of (weighted_vote, weights_used)
        """
        if not evaluations:
            return 0.0, {}
        
        total_weight = 0.0
        weighted_sum = 0.0
        weights_used = {}
        
        for eval in evaluations:
            # Get entity weight (reputation)
            entity_id = str(eval.entity_id)
            
            if entity_reputations and entity_id in entity_reputations:
                weight = entity_reputations[entity_id]
            else:
                # Default: equal weights
                weight = 1.0
            
            # Apply confidence as additional weight factor
            weight *= eval.confidence
            
            weighted_sum += weight * eval.vote
            total_weight += weight
            weights_used[entity_id] = weight
        
        if total_weight == 0:
            return 0.0, weights_used
        
        weighted_vote = weighted_sum / total_weight
        return weighted_vote, weights_used
    
    def determine_outcome(
        self,
        weighted_vote: float,
        threshold: float,
        quorum_met: bool
    ) -> DecisionOutcome:
        """
        Determine final outcome based on vote and threshold.
        
        Args:
            weighted_vote: Calculated weighted vote
            threshold: Required threshold
            quorum_met: Whether quorum was achieved
            
        Returns:
            DecisionOutcome
        """
        if not quorum_met:
            return DecisionOutcome.REJECTED
        
        if weighted_vote >= threshold:
            return DecisionOutcome.APPROVED
        
        # Check if close to threshold (refinement zone)
        threshold_min = threshold - self.refinement_margin
        if weighted_vote >= threshold_min:
            return DecisionOutcome.REFINED
        
        return DecisionOutcome.REJECTED
    
    def generate_rationale(
        self,
        outcome: DecisionOutcome,
        weighted_vote: float,
        threshold: float,
        evaluations: List[EntityEvaluation]
    ) -> str:
        """
        Generate human-readable rationale for decision.
        
        Args:
            outcome: Decision outcome
            weighted_vote: Weighted vote score
            threshold: Required threshold
            evaluations: Entity evaluations
            
        Returns:
            Rationale text
        """
        approve_count = sum(1 for e in evaluations if e.vote == 1)
        reject_count = sum(1 for e in evaluations if e.vote == -1)
        abstain_count = sum(1 for e in evaluations if e.vote == 0)
        
        rationale = f"""Decision: {outcome.value.upper()}

Weighted Vote: {weighted_vote:.3f}
Threshold Required: {threshold:.2f}

Entity Votes:
- {approve_count} APPROVE
- {reject_count} REJECT
- {abstain_count} ABSTAIN

"""
        
        if outcome == DecisionOutcome.APPROVED:
            rationale += "The proposal has achieved consensus and is APPROVED for implementation."
        
        elif outcome == DecisionOutcome.REFINED:
            rationale += f"""The proposal is close to threshold (within {self.refinement_margin:.2f}) but has not achieved full consensus.

RECOMMENDATION: Refine the proposal based on entity feedback and re-evaluate.

Key concerns to address:"""
            
            # Collect concerns from entities
            all_concerns = []
            for eval in evaluations:
                if eval.vote <= 0:  # Reject or abstain
                    all_concerns.extend(eval.concerns)
            
            for concern in all_concerns[:5]:  # Top 5 concerns
                rationale += f"\n- {concern}"
        
        elif outcome == DecisionOutcome.REJECTED:
            rationale += "The proposal has failed to achieve consensus and is REJECTED."
            
            # Collect main objections
            rationale += "\n\nMain objections:"
            for eval in evaluations:
                if eval.vote == -1:
                    rationale += f"\n\n{eval.entity_type.upper()}:\n{eval.reasoning[:200]}..."
        
        return rationale
    
    def evaluate(
        self,
        proposal: Proposal,
        evaluations: List[EntityEvaluation],
        total_entities: int = 3,
        entity_reputations: Optional[Dict[str, float]] = None
    ) -> ConsensusResult:
        """
        Run full consensus protocol evaluation.
        
        Args:
            proposal: Proposal being evaluated
            evaluations: Entity evaluations
            total_entities: Total number of active entities
            entity_reputations: Optional reputation scores
            
        Returns:
            ConsensusResult with outcome and details
        """
        # 1. Check quorum
        quorum_met = self.check_quorum(evaluations, total_entities)
        
        # 2. Calculate weighted vote
        weighted_vote, weights_used = self.calculate_weighted_vote(
            evaluations,
            entity_reputations
        )
        
        # 3. Get threshold
        threshold = self.get_threshold(proposal)
        
        # 4. Determine outcome
        outcome = self.determine_outcome(weighted_vote, threshold, quorum_met)
        
        # 5. Generate rationale
        rationale = self.generate_rationale(
            outcome,
            weighted_vote,
            threshold,
            evaluations
        )
        
        # 6. Collect entity votes
        entity_votes = {
            str(eval.entity_id): eval.vote
            for eval in evaluations
        }
        
        return ConsensusResult(
            weighted_vote=weighted_vote,
            threshold_required=threshold,
            quorum_met=quorum_met,
            outcome=outcome,
            rationale=rationale,
            entity_votes=entity_votes,
            entity_weights=weights_used
        )
    
    def create_decision(
        self,
        proposal: Proposal,
        evaluations: List[EntityEvaluation],
        consensus_result: ConsensusResult
    ) -> Decision:
        """
        Create Decision object from consensus result.
        
        Args:
            proposal: Original proposal
            evaluations: Entity evaluations
            consensus_result: Result from consensus protocol
            
        Returns:
            Decision object
        """
        decision = Decision(
            proposal_id=proposal.id,
            entity_evaluations=evaluations,
            weights_used=self.weights,
            weighted_vote=consensus_result.weighted_vote,
            threshold_required=consensus_result.threshold_required,
            quorum_met=consensus_result.quorum_met,
            outcome=consensus_result.outcome,
            rationale=consensus_result.rationale,
            deliberation_rounds=proposal.deliberation_round
        )
        
        return decision
