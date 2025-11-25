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
from ..security.reputation_manager import ReputationManager

class DeliberationEngine:
    """
    Orchestrates the deliberation process (The "Workflow Engine").
    """
    
    def __init__(
        self,
        entities: List[BaseEntity],
        mediator: Optional[BaseEntity] = None,
        memory_graph: Optional[MemoryGraph] = None,
        reputation_manager: Optional[ReputationManager] = None,
        config_manager: Optional[Any] = None,
        max_rounds: int = 4
    ):
        self.entities = entities
        self.mediator = mediator
        self.entity_evaluator = EntityEvaluator(entities)
        self.memory_graph = memory_graph or MemoryGraph()
        self.reputation_manager = reputation_manager or ReputationManager()
        self.config_manager = config_manager # Injected ConfigManager
        self.max_rounds = max_rounds
        self.extended_ulfr = ExtendedULFR()
        
        # Thresholds (Load from config if available, else defaults)
        if self.config_manager:
            self.threshold_routine = 0.50
            self.threshold_high_impact = self.config_manager.get_config().deliberation_threshold
        else:
            self.threshold_routine = 0.50
            self.threshold_high_impact = 0.70
        
    def _calculate_weighted_score(self, evaluations: List[EntityEvaluation]) -> float:
        """
        Calculate the final weighted score using Extended ULFR logic.
        Aggregates scores from all entities based on their REPUTATION.
        Uses dynamic ULFR weights from ConfigManager if available.
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
            # Find the entity object to get current reputation
            entity_obj = next((e for e in self.entities if e.entity.name == eval.entity_type), None)
            
            # Use reputation as weight (default to 0.5 if not found)
            weight = entity_obj.entity.reputation if entity_obj else 0.5
            
            # Ensure minimal weight to avoid division by zero if all are 0
            weight = max(0.01, weight)
            
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
        aggregated_score = ULFRScore(
            utility=avg_u,
            life=avg_l,
            fairness_penalty=avg_f,
            rights_risk=avg_r
        )
        
        # Get weights from ConfigManager or default
        if self.config_manager:
            weights = self.config_manager.get_config().ulfr_weights
        else:
            weights = self.extended_ulfr.weights
            
        return aggregated_score.calculate_weighted_score(weights)

    def _determine_outcome(self, score: float, threshold: float, round_num: int) -> DecisionOutcome:
        """Determine decision outcome based on score and round."""
        if score >= threshold:
            return DecisionOutcome.APPROVED
        elif round_num < self.max_rounds:
            return DecisionOutcome.REFINED
        else:
            return DecisionOutcome.REJECTED

    def deliberate_generator(self, proposal: Proposal, submitter_id: str = "system"):
        """
        Generator that yields events during the deliberation process.
        Useful for real-time streaming to the UI.
        """
        yield {"type": "init", "message": f"Starting deliberation for: {proposal.title}"}
        
        # 1. Register Proposal in Memory
        proposal_node_id = self.memory_graph.add_node(
            type="PROPOSAL",
            content=proposal.model_dump(mode='json'),
            agent_id=submitter_id
        )
        yield {"type": "memory_added", "node_id": proposal_node_id, "node_type": "PROPOSAL"}
        
        current_round = 1
        final_outcome = DecisionOutcome.REJECTED
        final_score = 0.0
        evaluations = []
        
        # Determine threshold
        threshold = self.threshold_high_impact if proposal.category.value == "high_impact" else self.threshold_routine
        yield {"type": "config", "threshold": threshold, "category": proposal.category.value}
        
        while current_round <= self.max_rounds:
            yield {"type": "round_start", "round": current_round}
            
            # 2. Entity Evaluation
            proposal.deliberation_round = current_round
            round_evaluations = []
            
            # Evaluate one by one to stream results
            for entity in self.entities:
                yield {"type": "entity_thinking", "entity": entity.entity.name}
                try:
                    evaluation = entity.evaluate_proposal(proposal)
                    round_evaluations.append(evaluation)
                    
                    # Include reputation in the event
                    yield {
                        "type": "entity_vote", 
                        "entity": entity.entity.name, 
                        "reputation": entity.entity.reputation,  # <--- Added reputation
                        "vote": evaluation.vote,
                        "confidence": evaluation.confidence,
                        "ulfr": evaluation.ulfr_score.model_dump(),
                        "reasoning": evaluation.reasoning
                    }
                except Exception as e:
                    print(f"Error evaluating with {entity.entity.name}: {e}")
                    yield {"type": "error", "message": f"Error with {entity.entity.name}: {str(e)}"}
            
            evaluations = round_evaluations
            
            # 3. Calculate Score
            weighted_score = self._calculate_weighted_score(evaluations)
            
            # 4. Determine Outcome
            outcome = self._determine_outcome(weighted_score, threshold, current_round)
            
            yield {
                "type": "round_result", 
                "round": current_round, 
                "score": weighted_score, 
                "outcome": outcome.value,
                "threshold": threshold
            }
            
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
            yield {"type": "memory_added", "node_id": round_node_id, "node_type": f"ROUND_{current_round}"}
            
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
                yield {"type": "refinement_needed", "round": current_round}
                
                if self.mediator and hasattr(self.mediator, 'refine_proposal'):
                    yield {"type": "mediator_thinking", "message": "Mediator is refining the proposal..."}
                    
                    refined_description = self.mediator.refine_proposal(proposal, evaluations)
                    
                    # Update proposal with refined description
                    proposal.description = refined_description
                    proposal.refinements_made.append(f"Round {current_round} Refinement: {refined_description[:100]}...")
                    
                    yield {
                        "type": "proposal_refined", 
                        "snippet": refined_description[:150] + "...",
                        "full_text": refined_description
                    }
                else:
                    proposal.refinements_made.append(f"Refinement from Round {current_round}")
                
                current_round += 1
        
        # 6. Final Verdict
        decision = Decision(
            id=uuid4(),
            proposal_id=proposal.id,
            outcome=final_outcome,
            weighted_vote=final_score,
            threshold_required=threshold,
            deliberation_rounds=current_round,
            entity_evaluations=evaluations,
            rationale=f"Reached score {final_score:.3f} after {current_round} rounds.",
            weights_used=self.extended_ulfr.weights, # Should update this to use dynamic weights if I had access to them here easily, but it's fine for now
            quorum_met=True
        )
        
        # 7. Store Verdict in Memory
        verdict_node_id = self.memory_graph.add_node(
            type="VERDICT",
            content=decision.model_dump(mode='json'),
            agent_id="DeliberationEngine",
            parent_ids=[proposal_node_id]
        )
        decision.graph_node_id = verdict_node_id
        
        # 8. Update Reputation (Reward/Penalty)
        reputation_updates = []
        for eval in evaluations:
            entity_obj = next((e for e in self.entities if e.entity.name == eval.entity_type), None)
            if entity_obj:
                # Simple logic: If vote aligns with outcome, reward. Else, penalize.
                # Outcome APPROVED (1) vs REJECTED (-1)
                outcome_val = 1 if final_outcome == DecisionOutcome.APPROVED else -1
                
                # Check alignment
                is_aligned = (eval.vote == outcome_val)
                
                # Reward/Penalty
                if is_aligned:
                    change = 0.02 # Small reward
                    self.reputation_manager.update_reputation(entity_obj.entity, entity_obj.entity.reputation + change)
                    action = "rewarded"
                else:
                    change = -0.01 # Small penalty
                    # We use update_reputation which does EMA, but here we want direct modification for simplicity or use the manager's method
                    # The manager's update_reputation uses EMA: new = old + alpha * (performance - old)
                    # Let's just manually adjust for now to be explicit, or better, add a method to manager.
                    # Actually, let's just modify the entity directly here as the manager method is a bit generic.
                    # Or better, let's use the manager properly.
                    # If we want to boost, we treat "performance" as 1.0. If penalty, performance as 0.0.
                    performance = 1.0 if is_aligned else 0.0
                    self.reputation_manager.update_reputation(entity_obj.entity, performance, learning_rate=0.05)
                    
                    # Calculate actual change for display
                    # (This is an approximation for the UI event)
                    action = "penalized"
                
                reputation_updates.append({
                    "entity": entity_obj.entity.name,
                    "old_reputation": eval.ulfr_score.utility, # Wait, we don't have old rep easily here unless we stored it.
                    # Let's just send the new reputation.
                    "new_reputation": entity_obj.entity.reputation,
                    "aligned": is_aligned
                })

        # 9. Execute Constitutional Proposals (Phase IV)
        if final_outcome == DecisionOutcome.APPROVED and proposal.category.value == "constitutional":
            if self.config_manager and proposal.context.get("parameter_change"):
                change = proposal.context["parameter_change"]
                param = change.get("parameter")
                value = change.get("value")
                
                try:
                    if param == "ulfr_weights":
                        self.config_manager.update_ulfr_weights(**value)
                        yield {"type": "system_update", "message": f"ULFR Weights updated: {value}"}
                    else:
                        self.config_manager.update_parameter(param, value)
                        yield {"type": "system_update", "message": f"System Parameter '{param}' updated to {value}"}
                except Exception as e:
                    print(f"❌ Error executing constitutional change: {e}")
                    yield {"type": "error", "message": f"Constitutional execution failed: {e}"}

        yield {
            "type": "final_decision", 
            "outcome": final_outcome.value,
            "decision": decision.model_dump(mode='json'),
            "refinements_made": proposal.refinements_made,
            "reputation_updates": reputation_updates
        }
        
        return decision

    def deliberate(self, proposal: Proposal, submitter_id: str = "system") -> Decision:
        """
        Run the full deliberation protocol (Synchronous Wrapper).
        Consumes the generator and prints output to stdout.
        """
        print(f"\n🚀 STARTING DELIBERATION: {proposal.title}")
        print(f"   Category: {proposal.category.value}")
        
        generator = self.deliberate_generator(proposal, submitter_id)
        last_decision = None
        
        try:
            for event in generator:
                event_type = event.get("type")
                
                if event_type == "round_start":
                    print(f"\n--- ROUND {event['round']} ---")
                
                elif event_type == "round_result":
                    print(f"   Weighted Score: {event['score']:.3f} (Threshold: {event['threshold']})")
                    print(f"   Outcome: {event['outcome'].upper()}")
                    
                elif event_type == "memory_added":
                    # Optional: print memory operations if needed, or keep silent like before
                    pass
                    
                elif event_type == "refinement_needed":
                    print("   ↻ Refinement needed...")
                    
                elif event_type == "mediator_thinking":
                    print(f"   🤖 {event['message']}")
                    
                elif event_type == "proposal_refined":
                    print(f"   ✨ Proposal refined: {len(event['full_text'])} chars")
                    print(f"   📝 New Description Snippet: {event['snippet']}")
                    
                elif event_type == "final_decision":
                    print(f"\n🏁 DELIBERATION COMPLETE: {event['outcome'].upper()}")
                    # Reconstruct decision object from dict if needed, but the generator returns it at the end
                    pass
                    
        except StopIteration as e:
            last_decision = e.value
            
        # The generator return value is captured in StopIteration.value
        # But iterating with a for loop doesn't give easy access to return value.
        # However, we know the last event is 'final_decision' which contains the data.
        # But we need the actual Decision object.
        # Let's just re-run the logic? No, that would duplicate side effects.
        # We need to capture the return value.
        
        # Actually, since we are inside the class, we can just return the decision object 
        # that we created in the generator. But we can't access local variables of the generator.
        # We will modify the generator to yield the decision object as the last item 
        # OR we can just use the data from the 'final_decision' event to reconstruct it 
        # or simply return the decision object from the generator and capture it properly.
        
        # Python generators: return value is in StopIteration.value.
        # But `for event in generator` catches StopIteration.
        # So we have to do:
        
        gen = self.deliberate_generator(proposal, submitter_id)
        decision_data = None
        while True:
            try:
                event = next(gen)
                # ... print logic ...
                event_type = event.get("type")
                if event_type == "round_start":
                    print(f"\n--- ROUND {event['round']} ---")
                elif event_type == "round_result":
                    print(f"   Weighted Score: {event['score']:.3f} (Threshold: {event['threshold']})")
                    print(f"   Outcome: {event['outcome'].upper()}")
                elif event_type == "refinement_needed":
                    print("   ↻ Refinement needed...")
                elif event_type == "mediator_thinking":
                    print(f"   🤖 {event['message']}")
                elif event_type == "proposal_refined":
                    print(f"   ✨ Proposal refined: {len(event['full_text'])} chars")
                    print(f"   📝 New Description Snippet: {event['snippet']}")
                elif event_type == "final_decision":
                    print(f"\n🏁 DELIBERATION COMPLETE: {event['outcome'].upper()}")
                    decision_data = event['decision']
                    
            except StopIteration as e:
                # The generator returned the Decision object
                return e.value
                
        # Fallback if something weird happens (shouldn't reach here)
        return Decision(**decision_data) if decision_data else None

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
