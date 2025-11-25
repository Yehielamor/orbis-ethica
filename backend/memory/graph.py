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
from ..core.database import get_db, init_db, SessionLocal
from ..core.models.sql_models import SQLMemoryNode
from .vector_store import VectorStore

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
    Manages the DAG. Now backed by SQLAlchemy (SQLite/PostgreSQL).
    """
    def __init__(self, ledger=None):
        self.ledger = ledger # Injected ledger instance
        self.vector_store = VectorStore() # Initialize Vector Store for RAG
        init_db() # Ensure tables exist

    def add_node(self, type: str, content: Dict[str, Any], agent_id: str, parent_ids: List[str] = []) -> str:
        """
        Create, seal, and store a new memory node in the database.
        Also anchors the node to the immutable ledger.
        """
        # Create Node Object (Pydantic)
        node = MemoryNode(
            id=hashlib.sha256(f"{datetime.utcnow()}-{content}".encode()).hexdigest()[:12],
            type=type,
            content=content,
            agent_id=agent_id,
            parent_ids=parent_ids
        )
        
        # Seal it (Immutable)
        node.seal()
        
        # Store in Database
        db = SessionLocal()
        try:
            sql_node = SQLMemoryNode(
                id=node.id,
                type=node.type,
                content=node.content,
                agent_id=node.agent_id,
                timestamp=node.timestamp,
                node_hash=node.node_hash,
                parent_ids=node.parent_ids
            )
            db.add(sql_node)
            db.commit()
            print(f"🕸️ [MEMORY] Node Added to DB: [{type}] {node.id}")
            
            # Add to Vector Store (RAG)
            # Create a text representation of the node for semantic search
            text_repr = f"Type: {type}\nContent: {json.dumps(content)}"
            self.vector_store.add_memory(text_repr, metadata={"node_id": node.id, "type": type})
            
            # Anchor to Ledger (if available)
            if self.ledger:
                block_data = {
                    "node_id": node.id,
                    "node_hash": node.node_hash,
                    "type": type,
                    "agent_id": agent_id
                }
                block = self.ledger.add_block(block_data)
                
                # Update DB with ledger info
                sql_node.ledger_block_index = block.index
                sql_node.ledger_block_hash = block.hash
                db.commit()
                
                print(f"   🔗 Anchored to Ledger: Block #{block.index} ({block.hash[:8]}...)")
                
        except Exception as e:
            print(f"❌ Error saving node to DB: {e}")
            db.rollback()
        finally:
            db.close()
        
        return node.id

    def get_node(self, node_id: str) -> Optional[MemoryNode]:
        """Fetch a node from the database."""
        db = SessionLocal()
        try:
            sql_node = db.query(SQLMemoryNode).filter(SQLMemoryNode.id == node_id).first()
            if not sql_node:
                return None
            
            return MemoryNode(
                id=sql_node.id,
                type=sql_node.type,
                content=sql_node.content,
                agent_id=sql_node.agent_id,
                timestamp=sql_node.timestamp,
                parent_ids=sql_node.parent_ids or [],
                node_hash=sql_node.node_hash
            )
        finally:
            db.close()

    def get_audit_trail(self, node_id: str) -> List[MemoryNode]:
        """
        Recursively fetch the history that led to a specific node.
        Used for 'Explainability'.
        """
        node = self.get_node(node_id)
        if not node:
            return []
        
        history = [node]
        
        for pid in node.parent_ids:
            history.extend(self.get_audit_trail(pid))
            
        return history

    def export_to_json(self, filepath: str = "memory_graph.json"):
        """Export the entire graph to JSON for persistence (Backup)."""
        db = SessionLocal()
        nodes = db.query(SQLMemoryNode).all()
        
        export_data = {
            "nodes": {
                n.id: {
                    "type": n.type,
                    "content": n.content,
                    "agent_id": n.agent_id,
                    "timestamp": n.timestamp.isoformat(),
                    "parent_ids": n.parent_ids
                } for n in nodes
            },
            "exported_at": datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"💾 [MEMORY] Graph exported to {filepath} ({len(nodes)} nodes)")
        db.close()

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
