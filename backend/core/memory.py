"""
Distributed Memory Graph (DAG).
Stores the causal chain of reasoning, proposals, and decisions.
Simplified for the Pivot (No VectorStore, No P2P Anchoring yet).
"""

import json
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .database import get_db, init_db, SessionLocal
from .models.sql_models import SQLMemoryNode

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
        init_db() # Ensure tables exist

    def add_node(self, type: str, content: Dict[str, Any], agent_id: str, parent_ids: List[str] = []) -> str:
        """
        Create, seal, and store a new memory node in the database.
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

    def get_recent_nodes(self, limit: int = 10, node_type: str = None) -> List[MemoryNode]:
        """Fetch recent nodes, optionally filtered by type."""
        db = SessionLocal()
        try:
            query = db.query(SQLMemoryNode)
            if node_type:
                query = query.filter(SQLMemoryNode.type == node_type)
            
            sql_nodes = query.order_by(SQLMemoryNode.timestamp.desc()).limit(limit).all()
            
            return [
                MemoryNode(
                    id=n.id,
                    type=n.type,
                    content=n.content,
                    agent_id=n.agent_id,
                    timestamp=n.timestamp,
                    parent_ids=n.parent_ids or [],
                    node_hash=n.node_hash
                ) for n in sql_nodes
            ]
        finally:
            db.close()
