
import asyncio
import json
import logging
import time
from typing import Any
from uuid import uuid4
from pydantic import BaseModel

from .models.proposal import Proposal
from .models.decision import EntityEvaluation
from .models.ulfr import ULFRScore
from .network_manager import NetworkManager

logger = logging.getLogger("SHARD_MGR")

class CognitiveShard(BaseModel):
    id: str
    proposal_id: str
    dimension: str  # "U", "L", "F", "R"
    context: str    # The specific prompt/sub-task
    miner_id: str | None = None
    result: dict[str, Any] | None = None
    timestamp: float
    signature: str | None = None

class ShardManager:
    """
    Manages the decomposition of Proposals into Cognitive Shards,
    dispatches them to the P2P network, and aggregates results.
    """
    
    def __init__(self, network_manager: NetworkManager):
        self.network_manager = network_manager
        # Store pending shards: {shard_id: Future}
        self.pending_shards: dict[str, asyncio.Future] = {}
        
    async def create_and_dispatch_shards(self, proposal: Proposal, local_fallback_callback=None) -> list[EntityEvaluation]:
        """
        Main Entry Point: Decompose Proposal -> Dispatch -> Wait -> Aggregate.
        Args:
            local_fallback_callback: Async function to process shard locally if P2P fails.
        """
        logger.info(f"🧩 [SHARD] Decomposing Proposal {proposal.id} into cognitive shards...")
        
        # 1. Decompose
        shards = self._decompose_proposal(proposal)
        
        # 2. Dispatch
        tasks = []
        for shard in shards:
            tasks.append(self._dispatch_shard(shard))
            
        # 3. Wait for Results (with timeout)
        # We wait for ALL shards to return or timeout.
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 4. Handle Timeouts / Fallbacks
        final_results = []
        for i, res in enumerate(results):
            if isinstance(res, (asyncio.TimeoutError, Exception)) or res is None:
                if local_fallback_callback:
                    logger.warning(f"⚠️ [SHARD] Network failed for shard {shards[i].dimension}. Falling back to LOCAL.")
                    try:
                        # Convert model to dict for callback
                        local_res = await local_fallback_callback(shards[i].model_dump())
                        final_results.append(local_res)
                    except Exception as e:
                        logger.error(f"❌ [SHARD] Local fallback failed: {e}")
                else: 
                     logger.error(f"❌ [SHARD] Shard failed and no fallback: {res}")
            elif isinstance(res, dict):
                 final_results.append(res)
        
        # 5. Aggregate
        valid_evaluations = []
        for res in final_results:
            if isinstance(res, dict) and "evaluation" in res:
                valid_evaluations.append(EntityEvaluation(**res["evaluation"]))
        
        return valid_evaluations

    def _decompose_proposal(self, proposal: Proposal) -> list[CognitiveShard]:
        """
        Splits a proposal into 4 dimensions (ULFR).
        """
        shards = []
        dimensions = [
            ("U", "Analyze Systemic Utility & Efficiency"),
            ("L", "Analyze Harm to Life & Vulnerable Populations"),
            ("F", "Analyze Fairness & Distribution of Outcome"),
            ("R", "Analyze Fundamental Rights & Autonomy")
        ]
        
        for dim_code, dim_desc in dimensions:
            shard = CognitiveShard(
                id=str(uuid4()),
                proposal_id=str(proposal.id),
                dimension=dim_code,
                context=f"Focus ONLY on {dim_desc}.\nProposal: {proposal.title}\n{proposal.description}",
                timestamp=time.time()
            )
            shards.append(shard)
            
        return shards

    async def _dispatch_shard(self, shard: CognitiveShard) -> dict[str, Any]:
        """
        Sends a single shard to the network and waits for a result.
        """
        # Create a Future to wait for the result
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_shards[shard.id] = future
        
        try:
            # Broadcast to P2P Network
            logger.info(f"📡 [SHARD] Broadcasting Shard {shard.dimension} ({shard.id})")
            await self.network_manager.broadcast_shard(shard.model_dump())
            
            # Wait for response (Timeout 5s - Fast fail for demo)
            result = await asyncio.wait_for(future, timeout=5.0)
            return result
        except asyncio.TimeoutError:
            # logger.warning(f"⏳ [SHARD] Timeout waiting for Shard {shard.dimension}")
            raise
        finally:
            if shard.id in self.pending_shards:
                del self.pending_shards[shard.id]

    def handle_shard_result(self, result_payload: dict[str, Any]):
        """
        Callback when NetworkManager receives a 'shard_result' message.
        """
        shard_id = result_payload.get("shard_id")
        if shard_id in self.pending_shards:
            future = self.pending_shards[shard_id]
            if not future.done():
                future.set_result(result_payload)
                logger.info(f"✅ [SHARD] Received result for {shard_id}")
