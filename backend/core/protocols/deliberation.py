"""Deliberation Engine - Orchestrates multi-round entity deliberation."""

from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import Proposal, Decision, ProposalStatus
from ..models.decision import EntityEvaluation
from ...entities.base import BaseEntity, EntityEvaluator
from .consensus import ConsensusProtocol, ConsensusResult, DecisionOutcome


class DeliberationEngine:
    """
    Orchestrates the full deliberation process.
    
    Process:
    1. Submit proposal
    2. Round 1: Independent entity evaluation
    3. Calculate consensus
    4. If needed: Round 2+ with refinement
    5. Final decision
    """
    
    def __init__(
        self,
        entities: List[BaseEntity],
        consensus_protocol: Optional[ConsensusProtocol] = None,
        max_rounds: int = 4
    ):
        """
        Initialize deliberation engine.
        
        Args:
            entities: List of cognitive entities
            consensus_protocol: Consensus protocol instance
            max_rounds: Maximum deliberation rounds (default 4)
        """
        self.entities = entities
        self.entity_evaluator = EntityEvaluator(entities)
        self.consensus_protocol = consensus_protocol or ConsensusProtocol()
        self.max_rounds = max_rounds
        
        # History tracking
        self.deliberation_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def submit_proposal(self, proposal: Proposal, submitter_id: str) -> Proposal:
        """
        Submit a proposal for deliberation.
        
        Args:
            proposal: Proposal to submit
            submitter_id: ID of submitter
            
        Returns:
            Updated proposal
        """
        proposal.submit(submitter_id)
        proposal.status = ProposalStatus.UNDER_REVIEW
        
        # Initialize history
        self.deliberation_history[str(proposal.id)] = []
        
        return proposal
    
    def run_deliberation_round(
        self,
        proposal: Proposal,
        round_number: int
    ) -> tuple[List[EntityEvaluation], ConsensusResult]:
        """
        Run a single deliberation round.
        
        Args:
            proposal: Proposal being evaluated
            round_number: Current round number
            
        Returns:
            Tuple of (evaluations, consensus_result)
        """
        print(f"\n{'='*60}")
        print(f"DELIBERATION ROUND {round_number}")
        print(f"{'='*60}\n")
        
        # Update proposal round
        proposal.deliberation_round = round_number
        
        # Get entity evaluations
        print("Evaluating with entities...")
        evaluations = self.entity_evaluator.evaluate_proposal(proposal)
        
        print(f"Received {len(evaluations)} evaluations")
        
        # Store evaluations in proposal
        proposal.entity_evaluations = {
            str(eval.entity_id): eval.to_dict()
            for eval in evaluations
        }
        
        # Run consensus protocol
        print("\nCalculating consensus...")
        consensus_result = self.consensus_protocol.evaluate(
            proposal=proposal,
            evaluations=evaluations,
            total_entities=len(self.entities)
        )
        
        # Update proposal
        proposal.weighted_vote = consensus_result.weighted_vote
        
        # Record in history
        self.deliberation_history[str(proposal.id)].append({
            "round": round_number,
            "timestamp": datetime.utcnow().isoformat(),
            "evaluations": [e.to_dict() for e in evaluations],
            "consensus": {
                "weighted_vote": consensus_result.weighted_vote,
                "threshold": consensus_result.threshold_required,
                "outcome": consensus_result.outcome.value
            }
        })
        
        return evaluations, consensus_result
    
    def refine_proposal(
        self,
        proposal: Proposal,
        evaluations: List[EntityEvaluation]
    ) -> Proposal:
        """
        Refine proposal based on entity feedback.
        
        This is a simplified version. In full implementation,
        the Creator entity would generate refinements.
        
        Args:
            proposal: Original proposal
            evaluations: Entity evaluations with feedback
            
        Returns:
            Refined proposal
        """
        print("\n" + "="*60)
        print("REFINEMENT PHASE")
        print("="*60 + "\n")
        
        # Collect all recommendations
        all_recommendations = []
        for eval in evaluations:
            if eval.vote <= 0:  # From rejecting/abstaining entities
                all_recommendations.extend(eval.recommendations)
        
        if all_recommendations:
            print("Applying refinements:")
            for rec in all_recommendations[:3]:  # Top 3
                print(f"  - {rec}")
                proposal.refinements_made.append(rec)
        
        proposal.status = ProposalStatus.REFINEMENT
        proposal.updated_at = datetime.utcnow()
        
        return proposal
    
    def deliberate(
        self,
        proposal: Proposal,
        submitter_id: str = "system"
    ) -> Decision:
        """
        Run full deliberation process with multiple rounds if needed.
        
        Args:
            proposal: Proposal to deliberate
            submitter_id: ID of submitter
            
        Returns:
            Final Decision
        """
        print("\n" + "="*80)
        print(f"STARTING DELIBERATION: {proposal.title}")
        print("="*80)
        
        # Submit proposal
        proposal = self.submit_proposal(proposal, submitter_id)
        
        # Run deliberation rounds
        for round_num in range(1, self.max_rounds + 1):
            evaluations, consensus_result = self.run_deliberation_round(
                proposal,
                round_num
            )
            
            # Print round summary
            print(f"\nRound {round_num} Result:")
            print(f"  Weighted Vote: {consensus_result.weighted_vote:.3f}")
            print(f"  Threshold: {consensus_result.threshold_required:.2f}")
            print(f"  Outcome: {consensus_result.outcome.value.upper()}")
            
            # Check outcome
            if consensus_result.outcome == DecisionOutcome.APPROVED:
                print("\n✓ PROPOSAL APPROVED")
                proposal.status = ProposalStatus.APPROVED
                break
            
            elif consensus_result.outcome == DecisionOutcome.REJECTED:
                print("\n✗ PROPOSAL REJECTED")
                proposal.status = ProposalStatus.REJECTED
                break
            
            elif consensus_result.outcome == DecisionOutcome.REFINED:
                if round_num < self.max_rounds:
                    print(f"\n↻ REFINEMENT NEEDED (Round {round_num + 1} will follow)")
                    proposal = self.refine_proposal(proposal, evaluations)
                else:
                    print(f"\n✗ MAX ROUNDS REACHED - REJECTED")
                    consensus_result.outcome = DecisionOutcome.REJECTED
                    proposal.status = ProposalStatus.REJECTED
                    break
        
        # Create final decision
        decision = self.consensus_protocol.create_decision(
            proposal,
            evaluations,
            consensus_result
        )
        
        # Add deliberation history
        decision.refinements_made = proposal.refinements_made
        
        print("\n" + "="*80)
        print("DELIBERATION COMPLETE")
        print("="*80)
        print(f"\nFinal Decision: {decision.outcome.value.upper()}")
        print(f"Deliberation Rounds: {decision.deliberation_rounds}")
        
        return decision
    
    def get_deliberation_summary(self, proposal_id: str) -> Dict[str, Any]:
        """
        Get summary of deliberation process.
        
        Args:
            proposal_id: Proposal ID
            
        Returns:
            Summary dictionary
        """
        history = self.deliberation_history.get(proposal_id, [])
        
        if not history:
            return {"error": "No deliberation history found"}
        
        return {
            "proposal_id": proposal_id,
            "total_rounds": len(history),
            "rounds": history,
            "final_outcome": history[-1]["consensus"]["outcome"] if history else None
        }
    
    def print_detailed_report(self, decision: Decision) -> None:
        """
        Print detailed deliberation report.
        
        Args:
            decision: Decision object
        """
        print("\n" + "="*80)
        print("DETAILED DELIBERATION REPORT")
        print("="*80 + "\n")
        
        print(f"Decision ID: {decision.id}")
        print(f"Proposal ID: {decision.proposal_id}")
        print(f"Outcome: {decision.outcome.value.upper()}")
        print(f"Weighted Vote: {decision.weighted_vote:.3f}")
        print(f"Threshold: {decision.threshold_required:.2f}")
        print(f"Rounds: {decision.deliberation_rounds}")
        print(f"Decided At: {decision.decided_at.isoformat()}")
        
        print("\n" + "-"*80)
        print("ENTITY EVALUATIONS")
        print("-"*80 + "\n")
        
        for eval in decision.entity_evaluations:
            vote_str = "✓ APPROVE" if eval.vote == 1 else "✗ REJECT" if eval.vote == -1 else "○ ABSTAIN"
            
            print(f"\n{eval.entity_type.upper()} - {vote_str}")
            print(f"Confidence: {eval.confidence:.2f}")
            print(f"\nULFR Scores:")
            print(f"  U (Utility): {eval.ulfr_score.utility:.2f}")
            print(f"  L (life/Care): {eval.ulfr_score.life:.2f}")
            print(f"  F (Fairness Penalty): {eval.ulfr_score.fairness_penalty:.2f}")
            print(f"  R (Rights Risk): {eval.ulfr_score.rights_risk:.2f}")
            
            if eval.concerns:
                print(f"\nConcerns:")
                for concern in eval.concerns[:3]:
                    print(f"  - {concern}")
            
            if eval.recommendations:
                print(f"\nRecommendations:")
                for rec in eval.recommendations[:3]:
                    print(f"  - {rec}")
        
        print("\n" + "-"*80)
        print("RATIONALE")
        print("-"*80 + "\n")
        print(decision.rationale)
        
        if decision.refinements_made:
            print("\n" + "-"*80)
            print("REFINEMENTS APPLIED")
            print("-"*80 + "\n")
            for i, refinement in enumerate(decision.refinements_made, 1):
                print(f"{i}. {refinement}")
        
        print("\n" + "="*80 + "\n")
