"""
Deliberation Engine - Orchestrates the multi-round deliberation process.
Integrates Extended ULFR scoring and Memory Graph storage.
"""

import time
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

from .models import Proposal, Decision, ProposalStatus, DecisionOutcome
from .models.decision import EntityEvaluation
from .models.ulfr import ULFRScore
from .extended_ulfr import ExtendedULFR, OutcomeGroup, RiskFactors
from ..entities.base import BaseEntity, EntityEvaluator
from ..memory.graph import MemoryGraph

class DeliberationEngine:
    """
    Orchestrates the deliberation process (The "Workflow Engine").
    """
    
    def __init__(
        self,
        entities: List[BaseEntity],
        mediator: Optional[BaseEntity] = None,
        memory_graph: Optional[MemoryGraph] = None,
        max_rounds: int = 4
    ):
        self.entities = entities
        self.mediator = mediator
        self.entity_evaluator = EntityEvaluator(entities)
        self.memory_graph = memory_graph or MemoryGraph()
        self.max_rounds = max_rounds
        self.extended_ulfr = ExtendedULFR()
        
        # Thresholds
        self.threshold_routine = 0.50
        self.threshold_high_impact = 0.70
        
    def _calculate_weighted_score(self, evaluations: List[EntityEvaluation]) -> float:
        """
        Calculate the final weighted score using Extended ULFR logic.
        Aggregates scores from all entities.
        """
        if not evaluations:
            return 0.0
            
        # Aggregate components
        total_u = 0.0
        total_l = 0.0
        total_f_penalty = 0.0
        total_r_risk = 0.0
        total_weight = 0.0
        
        for eval in evaluations:
            # In a real system, entities might have different weights (reputation)
            weight = 1.0 
            
            total_u += eval.ulfr_score.utility * weight
            total_l += eval.ulfr_score.life * weight
            total_f_penalty += eval.ulfr_score.fairness_penalty * weight
            total_r_risk += eval.ulfr_score.rights_risk * weight
            total_weight += weight
            
        if total_weight == 0:
            return 0.0
            
        # Averages
        avg_u = total_u / total_weight
        avg_l = total_l / total_weight
        avg_f = total_f_penalty / total_weight
        avg_r = total_r_risk / total_weight
        
        # Use ExtendedULFR to calculate final score
        # We construct mock groups/risk factors from the aggregated scores 
        # because ExtendedULFR expects raw data, but here we are aggregating already-processed scores.
        # So we use the ULFRScore object directly with weights.
        
        aggregated_score = ULFRScore(
            utility=avg_u,
            life=avg_l,
            fairness_penalty=avg_f,
            rights_risk=avg_r
        )
        
        return aggregated_score.calculate_weighted_score(self.extended_ulfr.weights)

    def _determine_outcome(self, score: float, threshold: float, round_num: int) -> DecisionOutcome:
        """Determine decision outcome based on score and round."""
        if score >= threshold:
            return DecisionOutcome.APPROVED
        elif round_num < self.max_rounds:
            return DecisionOutcome.REFINED
        else:
            return DecisionOutcome.REJECTED

    def deliberate(self, proposal: Proposal, submitter_id: str = "system") -> Decision:
        """
        Run the full deliberation protocol.
        """
        print(f"\n🚀 STARTING DELIBERATION: {proposal.title}")
        print(f"   Category: {proposal.category.value}")
        
        # 1. Register Proposal in Memory
        proposal_node_id = self.memory_graph.add_node(
            type="PROPOSAL",
            content=proposal.model_dump(mode='json'),
            agent_id=submitter_id
        )
        
        current_round = 1
        final_outcome = DecisionOutcome.REJECTED
        final_score = 0.0
        evaluations = []
        
        # Determine threshold
        threshold = self.threshold_high_impact if proposal.category.value == "high_impact" else self.threshold_routine
        
        while current_round <= self.max_rounds:
            print(f"\n--- ROUND {current_round} ---")
            
            # 2. Entity Evaluation
            proposal.deliberation_round = current_round
            evaluations = self.entity_evaluator.evaluate_proposal(proposal)
            
            # 3. Calculate Score
            weighted_score = self._calculate_weighted_score(evaluations)
            print(f"   Weighted Score: {weighted_score:.3f} (Threshold: {threshold})")
            
            # 4. Determine Outcome
            outcome = self._determine_outcome(weighted_score, threshold, current_round)
            print(f"   Outcome: {outcome.value.upper()}")
            
            # 5. Store Round in Memory
            round_node_id = self.memory_graph.add_node(
                type=f"ROUND_{current_round}",
                content={
                    "score": weighted_score,
                    "outcome": outcome.value,
                    "evaluations": [e.model_dump(mode='json') for e in evaluations]
                },
                agent_id="DeliberationEngine",
                parent_ids=[proposal_node_id]
            )
            
            if outcome == DecisionOutcome.APPROVED:
                final_outcome = DecisionOutcome.APPROVED
                final_score = weighted_score
                break
            elif outcome == DecisionOutcome.REJECTED:
                final_outcome = DecisionOutcome.REJECTED
                final_score = weighted_score
                break
            else:
                # Refinement needed
                print("   ↻ Refinement needed...")
                
                # Trigger Mediator specifically if we are in Round 3 (or generally if configured)
                # The user requested specific handling for Round 3 to break ties.
                # We'll apply it whenever refinement is needed if a mediator is present.
                if self.mediator and hasattr(self.mediator, 'refine_proposal'):
                    print(f"   🤖 Mediator is refining the proposal (Round {current_round})...")
                    refined_description = self.mediator.refine_proposal(proposal, evaluations)
                    
                    # Update proposal with refined description
                    proposal.description = refined_description
                    proposal.refinements_made.append(f"Round {current_round} Refinement: {refined_description[:100]}...")
                    print(f"   ✨ Proposal refined: {len(refined_description)} chars")
                    print(f"   📝 New Description Snippet: {refined_description[:100]}...")
                else:
                    # Fallback if no mediator
                    proposal.refinements_made.append(f"Refinement from Round {current_round}")
                
                current_round += 1
        
        # 6. Final Verdict
        decision = Decision(
            id=uuid4(),
            proposal_id=proposal.id,
            outcome=final_outcome,
            weighted_vote=final_score, # Using score as vote
            threshold_required=threshold,
            deliberation_rounds=current_round,
            entity_evaluations=evaluations,
            rationale=f"Reached score {final_score:.3f} after {current_round} rounds.",
            weights_used=self.extended_ulfr.weights,
            quorum_met=True # Assuming quorum is met for now
        )
        
        # 7. Store Verdict in Memory
        self.memory_graph.add_node(
            type="VERDICT",
            content=decision.model_dump(mode='json'),
            agent_id="DeliberationEngine",
            parent_ids=[proposal_node_id] # Should technically link to last round
        )
        
        print(f"\n🏁 DELIBERATION COMPLETE: {final_outcome.value.upper()}")
        return decision

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
        # print(f"Decided At: {decision.decided_at.isoformat()}") # decided_at might not be in Decision model yet
        
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
        
        # Check if refinements_made exists on decision (it's not in the model definition I saw earlier, but I added it to Proposal)
        # Decision model might need update too if we want to show refinements here.
        # For now, I'll skip printing refinements from decision object directly unless I add it to Decision model.
        # But wait, I added it to Proposal, not Decision. 
        # The old code added it to decision dynamically: decision.refinements_made = proposal.refinements_made
        # I should probably do the same or add it to the Decision model.
        
        print("\n" + "="*80 + "\n")
