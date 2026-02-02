"""
Deliberation Engine - Orchestrates the multi-round deliberation process.
Integrates Extended ULFR scoring, Memory Graph storage, Researcher Agent, and Swarm Parallelism.
"""
import asyncio
import time
from typing import Any
from uuid import uuid4

# Entities & Logic
from ..entities.base import BaseEntity, EntityEvaluator
from ..entities.researcher import ResearcherEntity
from ..security.reputation_manager import ReputationManager
from .consensus import ConsensusManager
from .extended_ulfr import ExtendedULFR
from .memory import MemoryGraph
from .shard_manager import ShardManager

# Models
from .models import Decision, DecisionOutcome, Proposal
from .models.decision import EntityEvaluation
from .models.ulfr import ULFRScore


class DeliberationEngine:
    """
    Orchestrates the deliberation process (The "Workflow Engine").
    """
    
    def __init__(
        self,
        entities: list[BaseEntity],
        mediator: BaseEntity | None = None,
        memory_graph: MemoryGraph | None = None,
        reputation_manager: ReputationManager | None = None,
        config_manager: Any | None = None,
        node_manager: Any | None = None, # Injected NodeManager
        max_rounds: int = 4
    ):
        self.entities = entities
        self.mediator = mediator
        self.entity_evaluator = EntityEvaluator(entities)
        
        # NEW: Initialize the Researcher
        self.researcher = ResearcherEntity()
        
        self.memory_graph = memory_graph or MemoryGraph()
        self.reputation_manager = reputation_manager or ReputationManager()
        self.config_manager = config_manager
        self.node_manager = node_manager
        self.max_rounds = max_rounds
        self.extended_ulfr = ExtendedULFR()
        self.consensus_manager = ConsensusManager()
        
        # Thresholds (Load from config if available, else defaults)
        if self.config_manager:
            self.threshold_routine = 0.50
            self.threshold_high_impact = self.config_manager.get_config().deliberation_threshold
        else:
            self.threshold_routine = 0.50
            self.threshold_high_impact = 0.70
            
        # Initialize ShardManager if NetworkManager is present
        self.shard_manager = None
        if self.node_manager:
            self.shard_manager = ShardManager(self.node_manager)
            self.node_manager.set_shard_manager(self.shard_manager)
        
    def _calculate_weighted_score(self, evaluations: list[EntityEvaluation]) -> float:
        """
        Calculate the final weighted score using Extended ULFR logic.
        Aggregates scores from all entities based on their REPUTATION.
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
            
            # Ensure minimal weight to avoid division by zero
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

    async def _evaluate_via_swarm(self, proposal: Proposal) -> list[EntityEvaluation]:
        """
        TRUE PARALLEL SWARM DISPATCH.
        Sends prompts to the LLMProvider (which handles the Round Robin).
        Executes all agents simultaneously using asyncio.gather.
        """
        # tasks = []
        # print(f"🚀 [ENGINE] Dispatching {len(self.entities)} agents to the Swarm...")
        
        # # Create a task for each entity (Guardian, Healer, Seeker)
        # for entity in self.entities:
        #     # Note: evaluate_proposal calls llm_provider.generate internally.
        #     tasks.append(entity.evaluate_proposal(proposal))
            
        # # WAIT FOR ALL (Parallel Execution)
        # # This reduces wait time significantly compared to sequential execution.
        # results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # valid_evaluations = []
        # for res in results:
        #     if isinstance(res, Exception):
        #         print(f"❌ [SWARM ERROR] Agent execution failed: {res}")
        #     else:
        #         valid_evaluations.append(res)
                
        # return valid_evaluations
        
        # --- NEW: Distributed Sharding with Local Fallback ---
        if self.shard_manager:
            return await self.shard_manager.create_and_dispatch_shards(
                proposal, 
                local_fallback_callback=self.process_remote_shard
            )
        else:
            # Fallback to local if no network
            print("⚠️ [ENGINE] ShardManager not available. Falling back to local swarm.")
            
            # EXCLUDE ARBITER from routine voting (White Paper Alignment)
            # The Arbiter should only intervene if there is no clear consensus.
            active_entities = [e for e in self.entities if e.entity.name != "Arbiter"]
            
            tasks = [e.evaluate_proposal(proposal) for e in active_entities]
            return await asyncio.gather(*tasks)

    def _determine_outcome(self, score: float, threshold: float, round_num: int) -> DecisionOutcome:
        """Determine decision outcome based on score and round."""
        if score >= threshold:
            return DecisionOutcome.APPROVED
        elif round_num < self.max_rounds:
            return DecisionOutcome.REFINED
        else:
            return DecisionOutcome.REJECTED

    def _validate_quorum(self, evaluations: list[EntityEvaluation]) -> bool:
        """
        Ensures the returned evaluations meet the minimum standards for a valid vote.
        1. Must have at least X responses (Min 2).
        2. MUST include critical roles (Guardian).
        """
        if not evaluations:
            return False
            
        # 1. Check Count (Minimum 2 agents for consensus)
        if len(evaluations) < 2:
            print("❌ [QUORUM FAIL] Not enough agents responded.")
            return False

        # 2. Check Critical Roles
        responding_entities = [e.entity_type for e in evaluations]
        # Guardian is critical for rights protection
        # We need to handle potential case sensitivity or naming variations if they exist, 
        # but typically it checks against the EntityType value or Name.
        # Based on base.py, entity_type is usually the name (e.g. "Guardian").
        # Let's check for "Guardian" substring to be safe or exact match if possible.
        has_guardian = any("Guardian" in e for e in responding_entities)
        
        if not has_guardian:
            print("❌ [QUORUM FAIL] The Guardian (Critical) is missing. Cannot proceed ethically.")
            return False
            
        return True

    async def deliberate_generator(self, proposal: Proposal, submitter_id: str = "system"):
        """
        Generator that yields events during the deliberation process.
        """
        yield {"type": "init", "message": f"Starting deliberation for: {proposal.title}"}
        
        # --- PHASE 0.5: RESEARCH (RAG) ---
        yield {"type": "researching", "message": "The Researcher is gathering verified context..."}
        try:
            # 1. Fetch facts
            rag_context = await self.researcher.research(proposal.model_dump())
            
            # 2. Inject into proposal description so all agents see it
            original_desc = proposal.description
            proposal.description = f"{original_desc}\n\n{rag_context}"
            
            yield {"type": "research_complete", "snippet": rag_context[:100] + "..."}
        except Exception as e:
            print(f"Research failed: {e}")
            yield {"type": "warning", "message": "Research failed, using internal knowledge only."}
        # ----------------------------------

        # 0. Verify Signature
        if hasattr(self, 'consensus_manager') and proposal.signature:
            yield {"type": "verification", "message": "Verifying cryptographic signature..."}
            is_valid = self.consensus_manager.verify_proposal(proposal)
            if not is_valid:
                error_msg = f"❌ Signature Verification Failed for submitter {proposal.submitter_id}"
                print(error_msg)
                yield {"type": "error", "message": error_msg}
                return
            yield {"type": "verification", "message": "✅ Signature Verified (Ed25519)"}
        else:
             yield {"type": "verification", "message": "⚠️ Signature Skipped (Dev Mode)"}
        
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
            
            # 2. Entity Evaluation (Parallel Swarm)
            proposal.deliberation_round = current_round
            
            yield {"type": "swarm_dispatch", "message": "Broadcasting to Swarm Nodes..."}
            
            try:
                # Use the new PARALLEL method
                evaluations = await self._evaluate_via_swarm(proposal)
                
                # --- NEW: QUORUM CHECK ---
                if not self._validate_quorum(evaluations):
                    yield {"type": "error", "message": "Quorum Failed: Guardian missing or low participation."}
                    break
                # -------------------------
                
                # Stream results back to UI
                for evaluation in evaluations:
                    entity_obj = next((e for e in self.entities if e.entity.name == evaluation.entity_type), None)
                    reputation = entity_obj.entity.reputation if entity_obj else 0.5
                    
                    yield {
                        "type": "entity_vote", 
                        "entity": evaluation.entity_type, 
                        "reputation": reputation,
                        "vote": evaluation.vote,
                        "confidence": evaluation.confidence,
                        "ulfr": evaluation.ulfr_score.model_dump(),
                        "reasoning": evaluation.reasoning,
                        "evidence_cited": evaluation.evidence_cited
                    }
                    
            except Exception as e:
                print(f"Error in Swarm Execution: {e}")
                yield {"type": "error", "message": f"Execution Failed: {str(e)}"}
            
            if not evaluations:
                yield {"type": "error", "message": "No evaluations returned from Swarm."}
                break
            
            # 3. Calculate Score
            weighted_score = self._calculate_weighted_score(evaluations)
            
            # 4. Determine Outcome
            outcome = self._determine_outcome(weighted_score, threshold, current_round)
            
            # --- ARBITER INTERVENTION (Tie-Breaker) ---
            # If the vote is close to the threshold (e.g., +/- 10%), calling the Arbiter.
            margin = 0.10
            is_ambiguous = (threshold - margin) <= weighted_score <= (threshold + margin)
            
            if is_ambiguous and outcome != DecisionOutcome.APPROVED: # Only intervene if we are on the fence or rejected marginally
                arbiter = next((e for e in self.entities if e.entity.name == "Arbiter"), None)
                if arbiter:
                    yield {"type": "arbiter_intervention", "message": "⚖️ Decision ambiguous. Summoning the Arbiter..."}
                    
                    # Arbiter evaluates based on previous evaluations (synthesizing)
                    # For now, we ask for a direct evaluation
                    arb_eval = await arbiter.evaluate_proposal(proposal)
                    evaluations.append(arb_eval)
                    
                    # Recalculate Score with Arbiter's heavy weight
                    weighted_score = self._calculate_weighted_score(evaluations)
                    outcome = self._determine_outcome(weighted_score, threshold, current_round)
                    
                    yield {
                        "type": "entity_vote", 
                        "entity": "Arbiter", 
                        "reputation": arbiter.entity.reputation,
                        "vote": arb_eval.vote,
                        "confidence": arb_eval.confidence,
                        "ulfr": arb_eval.ulfr_score.model_dump(),
                        "reasoning": f"[ARBITER RULING] {arb_eval.reasoning}",
                        "evidence_cited": arb_eval.evidence_cited
                    }
            # ------------------------------------------

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
                # Refinement logic
                yield {"type": "refinement_needed", "round": current_round}
                if self.mediator and hasattr(self.mediator, 'refine_proposal'):
                    yield {"type": "mediator_thinking", "message": "Mediator is refining the proposal..."}
                    refined_description = await self.mediator.refine_proposal(proposal, evaluations)
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
        
        # 6. Final Verdict & Minting
        decision = Decision(
            id=uuid4(),
            proposal_id=proposal.id,
            outcome=final_outcome,
            weighted_vote=final_score,
            threshold_required=threshold,
            deliberation_rounds=current_round,
            entity_evaluations=evaluations,
            rationale=f"Reached score {final_score:.3f} after {current_round} rounds.",
            weights_used=self.extended_ulfr.weights,
            quorum_met=True
        )
        
        verdict_node_id = self.memory_graph.add_node(
            type="VERDICT",
            content=decision.model_dump(mode='json'),
            agent_id="DeliberationEngine",
            parent_ids=[proposal_node_id]
        )
        decision.graph_node_id = verdict_node_id
        
        # Update Reputation
        reputation_updates = []
        for eval in evaluations:
            entity_obj = next((e for e in self.entities if e.entity.name == eval.entity_type), None)
            if entity_obj:
                outcome_val = 1 if final_outcome == DecisionOutcome.APPROVED else -1
                is_aligned = (eval.vote == outcome_val)
                
                if is_aligned:
                    self.reputation_manager.update_reputation(entity_obj.entity, entity_obj.entity.reputation + 0.02)
                else:
                    self.reputation_manager.update_reputation(entity_obj.entity, 0.0, learning_rate=0.05)
                
                reputation_updates.append({
                    "entity": entity_obj.entity.name,
                    "new_reputation": entity_obj.entity.reputation,
                    "aligned": is_aligned
                })

        # Mint Rewards
        if final_outcome == DecisionOutcome.APPROVED and self.memory_graph.ledger:
            try:
                reward_tx = self._mint_proposal_reward(proposal, final_score)
                if reward_tx:
                    yield {
                        "type": "economic_reward", 
                        "message": f"💰 Minted {reward_tx.amount} ETHC to {reward_tx.receiver}",
                        "tx_id": reward_tx.id
                    }
            except Exception as e:
                print(f"❌ Error minting reward: {e}")

        yield {
            "type": "final_decision", 
            "outcome": final_outcome.value,
            "decision": decision.model_dump(mode='json'),
            "refinements_made": proposal.refinements_made,
            "reputation_updates": reputation_updates
        }

    def _mint_proposal_reward(self, proposal: Proposal, score: float) -> Any | None:
        """
        Mint a reward for an approved proposal.
        """
        if not self.memory_graph.ledger:
            return None
            
        base_reward = 100.0
        score_multiplier = max(1.0, score * 2)
        amount = base_reward * score_multiplier
        
        receiver = proposal.submitter_id
        if len(receiver) < 10: 
            print(f"⚠️ Cannot mint reward: Invalid wallet ID '{receiver}'")
            return None
            
        success = self.memory_graph.ledger.record_transaction(
            sender="mining_reward_pool",
            recipient=receiver,
            amount=amount,
            tx_type="transfer",
            description=f"Reward for Proposal {proposal.id}"
        )
        
        if not success:
            print("⚠️ Reward transfer failed.")
            return None
            
        from .ledger import TokenTransaction, TransactionType
        tx = TokenTransaction(
            id=f"reward_{proposal.id}_{int(time.time())}",
            type=TransactionType.TRANSFER,
            sender="mining_reward_pool",
            receiver=receiver,
            amount=amount,
            signature="system_auto_sig"
        )
        return tx

    async def deliberate(self, proposal: Proposal, submitter_id: str = "system") -> Decision:
        """Async wrapper for the generator."""
        print(f"\n🚀 STARTING DELIBERATION: {proposal.title}")
        generator = self.deliberate_generator(proposal, submitter_id)
        decision_data = None
        try:
            async for event in generator:
                if event.get("type") == "final_decision":
                    decision_data = event['decision']
        except Exception as e:
            print(f"❌ Error during deliberation: {e}")
        return Decision(**decision_data) if decision_data else None

    async def process_remote_shard(self, shard_data: dict[str, Any]) -> dict[str, Any]:
        """
        WORKER ROLE: Process a shard received from the network.
        """
        print(f"🛠️ [WORKER] Processing Shard {shard_data.get('id')} ({shard_data.get('dimension')})...")
        
        # 1. Select an Agent based on dimension (Simple mapping for V1)
        # U -> Seeker, L -> Healer, F -> Mediator, R -> Guardian
        dim = shard_data.get("dimension")
        agent_map = {
            "U": "Seeker",
            "L": "Healer", 
            "F": "Mediator",
            "R": "Guardian"
        }
        target_agent_name = agent_map.get(dim, "Guardian")
        
        agent = next((e for e in self.entities if e.entity.name == target_agent_name), self.entities[0])
        
        # 2. Execute (using internal LLM call)
        # We construct a synthetic prompt since we don't have a full Proposal object structure expected by evaluate_proposal
        prompt = f"""
        [SYSTEM: You are a distributed worker node.]
        {shard_data.get('context')}
        
        Evaluate this strictly. Return JSON.
        """
        
        try:
            # We bypass evaluate_proposal to send raw prompt, 
            # OR we create a dummy proposal. Let's try raw prompt access if possible.
            # BaseEntity doesn't expose raw _call_llm easily publicly? 
            # Actually evaluate_proposal calls _call_llm.
            # Let's use the agent's llm_provider directly.
            
            response_text = await agent.llm_provider.generate(prompt, system_role="You are a system worker. You must return valid JSON.")
            
            # Parse it
            eval_data = agent._parse_json_response(response_text)
            
            # 3. Sign Result (Proof of Inference)
            # We need consensus manager for this.
            signature = "auto_worker_sig" # Placeholder if no consensus manager linked in engine
            if hasattr(self, 'consensus_manager'):
                 signature = self.consensus_manager.sign_data(eval_data)

            return {
                "shard_id": shard_data.get("id"),
                "evaluation": {
                    "entity_type": f"{agent.entity.name} (Worker)",
                    "vote": eval_data.get("vote", 0),
                    "confidence": eval_data.get("confidence", 0.0),
                    "reasoning": eval_data.get("reasoning", "No reasoning provided"),
                    "ulfr_score": eval_data.get("ulfr_score", {})
                },
                "miner_id": "worker_node", # Should be public key
                "signature": signature
            }
            
        except Exception as e:
            print(f"❌ [WORKER] Shard processing failed: {e}")
            return {"error": str(e)}

    def print_detailed_report(self, decision: Decision) -> None:
        """Prints the report."""
        print(f"\nDECISION REPORT: {decision.outcome.value.upper()} (Score: {decision.weighted_vote})")