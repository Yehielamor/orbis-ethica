import json
from typing import List
from ..core.llm_provider import get_llm_provider
from .models import EthicalDilemma, CognitiveShard

class ShardManager:
    """
    Orchestrates the Cognitive Sharding process.
    """
    def __init__(self, ledger=None, identity=None):
        self.llm = get_llm_provider()
        self.ledger = ledger
        self.identity = identity

    def decompose_dilemma(self, title: str, description: str) -> EthicalDilemma:
        """
        Takes a raw dilemma and breaks it down into shards using the LLM.
        """
        dilemma = EthicalDilemma(title=title, description=description)
        
        print(f"🧠 [SWARM] Decomposing dilemma: {title}...")
        
        system_prompt = (
            "You are the Cortex of a Swarm Intelligence. "
            "Your job is to break down complex ethical dilemmas into distinct cognitive aspects (shards) "
            "that can be analyzed in parallel by different nodes.\n"
            "Output MUST be a valid JSON list of objects, where each object has:\n"
            "- 'aspect': A short title (e.g., 'Utilitarian View')\n"
            "- 'prompt': A specific question for a node to answer.\n"
            "Create 3 to 5 shards."
        )
        
        user_prompt = f"Dilemma: {title}\nDescription: {description}\n\nBreak this down now."
        
        try:
            response_text = self.llm.generate(user_prompt, system_role=system_prompt)
            
            # Clean up response (sometimes LLMs add markdown code blocks)
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            
            shards_data = json.loads(clean_json)
            
            for item in shards_data:
                shard = CognitiveShard(
                    dilemma_id=dilemma.id,
                    aspect=item.get("aspect", "Unknown Aspect"),
                    prompt=item.get("prompt", "Analyze this aspect.")
                )
                dilemma.shards.append(shard)
                
            dilemma.status = "SHARDED"
            print(f"✅ [SWARM] Created {len(dilemma.shards)} shards for processing.")
            return dilemma
            
        except Exception as e:
            print(f"❌ [SWARM] Decompostion failed: {e}")
            # Fallback: Create one generic shard
            fallback_shard = CognitiveShard(
                dilemma_id=dilemma.id,
                aspect="General Analysis",
                prompt=f"Analyze the following dilemma: {description}"
            )
            dilemma.shards.append(fallback_shard)
            return dilemma

    def process_shard(self, shard: CognitiveShard) -> CognitiveShard:
        """
        Simulates a node processing a single shard.
        In a real network, this would happen on a remote peer.
        """
        print(f"⚡ [NODE] Processing Shard: {shard.aspect}...")
        
        system_prompt = (
            f"You are an Ethical Node analyzing the '{shard.aspect}' of a dilemma. "
            "Provide a deep, focused analysis based ONLY on this aspect."
        )
        
        response = self.llm.generate(shard.prompt, system_role=system_prompt)
        shard.result = response
        shard.status = "COMPLETED"
        
        # --- PROOF OF INFERENCE (POI) ---
        if self.identity:
            from .models import ExecutionSeal
            # Create payload to sign
            payload = {
                "shard_id": shard.id,
                "result": shard.result,
                "model": getattr(self.llm, "model_name", "unknown")
            }
            signature = self.identity.sign(payload)
            
            shard.seal = ExecutionSeal(
                node_id=self.identity.node_id,
                signature=signature,
                model_hash="sha256:tinyllama-v1" # Placeholder for real hash
            )
            print(f"🔐 [POI] Signed shard result with {self.identity.node_id}")

        # --- TOKENOMICS: INFERENCE REWARD ---
        if self.ledger and shard.seal:
            # Check if reward already given for this shard ID
            # In a real blockchain, this would be checked against the ledger history.
            # Here we use a simple check, but ideally we should query the ledger for reference_id.
            
            # Query ledger to see if this shard ID was already rewarded
            session = self.ledger.db_manager.get_session()
            try:
                from ..core.models.sql_models import LedgerEntryModel
                existing_reward = session.query(LedgerEntryModel).filter_by(reference_id=shard.id).first()
                
                if not existing_reward:
                    # Reward the node that did the work
                    reward_amount = 1.0
                    success = self.ledger.record_transaction(
                        sender="INFERENCE_REWARD_POOL",
                        recipient=shard.seal.node_id,
                        amount=reward_amount,
                        tx_type="transfer",
                        reference_id=shard.id,
                        description=f"Reward for Shard {shard.id[:8]}"
                    )
                    if success:
                        print(f"💰 [REWARD] Minted {reward_amount} ETHC to {shard.seal.node_id}")
                else:
                    print(f"⚠️ [REWARD] Skipped duplicate reward for Shard {shard.id[:8]}")
            except Exception as e:
                print(f"❌ [REWARD] Failed to check/mint reward: {e}")
            finally:
                session.close()
        
        return shard
