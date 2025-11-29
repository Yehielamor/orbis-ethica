from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

class ExecutionSeal(BaseModel):
    model_config = {'protected_namespaces': ()}
    """
    Proof of Inference (POI).
    Cryptographically proves that a specific node executed the inference.
    """
    node_id: str
    signature: str  # Ed25519 signature of (prompt + result + model_hash)
    model_hash: str  # Hash of the model weights used (e.g., tinyllama sha256)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CognitiveShard(BaseModel):
    model_config = {'protected_namespaces': ()}
    """
    A single fragment of an ethical dilemma to be processed by a node.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dilemma_id: str
    aspect: str  # e.g., "Utilitarian Analysis", "Cultural Sensitivity", "Legal Compliance"
    prompt: str  # The specific sub-question for the LLM
    assigned_to: Optional[str] = None  # Node ID processing this shard
    status: str = "PENDING"  # PENDING, PROCESSING, COMPLETED, FAILED
    result: Optional[str] = None  # The LLM's output
    seal: Optional[ExecutionSeal] = None  # Proof of Inference
    vector: Optional[List[float]] = None  # Embedding of the result
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EthicalDilemma(BaseModel):
    """
    The root problem that needs to be solved by the Swarm.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    context: Dict[str, Any] = {}
    shards: List[CognitiveShard] = []
    status: str = "NEW"  # NEW, SHARDED, AGGREGATING, RESOLVED
    final_verdict: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
