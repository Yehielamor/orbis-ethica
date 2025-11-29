from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import uuid

from ..swarm.models import EthicalDilemma, CognitiveShard, ExecutionSeal
from ..swarm.shard_manager import ShardManager

router = APIRouter(prefix="/api/swarm", tags=["Swarm Intelligence"])

# Singleton Manager (in a real app, use dependency injection)
shard_manager = ShardManager()

class DilemmaRequest(BaseModel):
    title: str
    description: str

class ShardResponse(BaseModel):
    id: str
    aspect: str
    prompt: str
    status: str
    result: Optional[str] = None
    seal: Optional[ExecutionSeal] = None

@router.post("/decompose", response_model=EthicalDilemma)
async def decompose_dilemma(request: DilemmaRequest):
    """
    Decomposes a complex ethical dilemma into cognitive shards.
    """
    try:
        dilemma = shard_manager.decompose_dilemma(request.title, request.description)
        return dilemma
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process/{shard_id}", response_model=CognitiveShard)
async def process_shard_endpoint(shard_id: str, background_tasks: BackgroundTasks):
    """
    Simulates a node processing a specific shard.
    In a real network, this would be triggered by a P2P message.
    """
    # For simulation, we just create a dummy shard object to pass to the manager
    # In reality, we'd fetch from DB
    dummy_shard = CognitiveShard(
        id=shard_id,
        dilemma_id="simulated",
        aspect="Simulation",
        prompt="Analyze the ethical implications of this test.",
        status="PENDING"
    )
    
    try:
        # We process synchronously for the demo, but in prod this is async
        result_shard = shard_manager.process_shard(dummy_shard)
        
        return result_shard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
