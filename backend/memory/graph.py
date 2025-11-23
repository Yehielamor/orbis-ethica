"""
Distributed Memory Graph (DAG).
Stores the causal chain of reasoning, proposals, and decisions.
Unlike a simple log, each node points to its parents (evidence/previous decisions),
creating an immutable audit trail.
"""

import json
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MemoryNode(BaseModel):
    """
    A single atom of memory in the system.
    Could be a Piece of Knowledge, a Proposal, a Vote, or a Verdict.
    """
    id: str
    type: str  # 'KNOWLEDGE', 'PROPOSAL', 'VOTE', 'VERDICT', 'BURN'
    content: Dict[str, Any]
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    parent_ids: List[str] = [] # Links to previous nodes (The DAG structure)
    node_hash: str = "" # Cryptographic seal of this node

    def seal(self):
        """Compute the hash of the node (Content + Parents)."""
        payload = {
            "content": self.content,
            "parent_ids": sorted(self.parent_ids),
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat()
        }
        serialized = json.dumps(payload, sort_keys=True)
        self.node_hash = hashlib.sha256(serialized.encode()).hexdigest()

class MemoryGraph:
    """
    Manages the DAG. In a real implementation, this would sync with IPFS/Arweave.
    """
    def __init__(self):
        self.nodes: Dict[str, MemoryNode] = {}
        self.head_ids: List[str] = [] # Tips of the graph

    def add_node(self, type: str, content: Dict[str, Any], agent_id: str, parent_ids: List[str] = []) -> str:
        """
        Create, seal, and store a new memory node.
        """
        # Create Node
        node = MemoryNode(
            id=hashlib.sha256(f"{datetime.utcnow()}-{content}".encode()).hexdigest()[:12],
            type=type,
            content=content,
            agent_id=agent_id,
            parent_ids=parent_ids
        )
        
        # Seal it (Immutable)
        node.seal()
        
        # Store
        self.nodes[node.id] = node
        print(f"🕸️ [MEMORY] Node Added: [{type}] {node.id} (Parents: {len(parent_ids)})")
        
        return node.id

    def get_audit_trail(self, node_id: str) -> List[MemoryNode]:
        """
        Recursively fetch the history that led to a specific node.
        Used for 'Explainability'.
        """
        if node_id not in self.nodes:
            return []
        
        node = self.nodes[node_id]
        history = [node]
        
        for pid in node.parent_ids:
            history.extend(self.get_audit_trail(pid))
            
        return history

    def export_to_json(self, filepath: str = "memory_graph.json"):
        """Export the entire graph to JSON for persistence."""
        export_data = {
            "nodes": {
                node_id: node.model_dump(mode='json')
                for node_id, node in self.nodes.items()
            },
            "exported_at": datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"💾 [MEMORY] Graph exported to {filepath} ({len(self.nodes)} nodes)")

    def visualize_trail(self, node_id: str) -> str:
        """
        Generate a human-readable audit trail for a specific decision.
        """
        trail = self.get_audit_trail(node_id)
        
        if not trail:
            return f"No trail found for node {node_id}"
        
        output = [f"\n📜 AUDIT TRAIL FOR: {node_id}"]
        output.append("=" * 60)
        
        for i, node in enumerate(reversed(trail)):
            indent = "  " * i
            output.append(f"{indent}[{node.type}] {node.id}")
            output.append(f"{indent}  Agent: {node.agent_id}")
            output.append(f"{indent}  Time: {node.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            if node.parent_ids:
                output.append(f"{indent}  Parents: {', '.join(node.parent_ids)}")
            output.append("")
        
        return "\n".join(output)
