"""
Distributed Memory Graph (DAG).
Stores the causal chain of reasoning, proposals, and decisions.
Simplified for the Pivot (No VectorStore, No P2P Anchoring yet).
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Optional  # Removed List (deprecated)
from uuid import uuid4

from pydantic import BaseModel, Field

from .database import SessionLocal, init_db
from .models.sql_models import SQLMemoryNode


class MemoryNode(BaseModel):
    """
    A single atom of memory in the system.
    Could be a Piece of Knowledge, a Proposal, a Vote, or a Verdict.
    """
    id: str
    type: str  # 'KNOWLEDGE', 'PROPOSAL', 'VOTE', 'VERDICT', 'BURN'
    content: dict[str, Any]
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    parent_ids: list[str] = []  # Links to previous nodes (The DAG structure)
    node_hash: str = ""  # Cryptographic seal of this node

    def seal(self):
        """Compute the hash of the node (Content + Parents)."""
        payload = {
            "content": self.content,
            "parent_ids": sorted(self.parent_ids),
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat()
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        self.node_hash = hashlib.sha256(serialized.encode()).hexdigest()

class MemoryGraph:
    """
    Manages the DAG. Now backed by SQLAlchemy (SQLite/PostgreSQL).
    """
    def __init__(self, ledger=None):
        self.ledger = ledger  # Injected ledger instance
        init_db()  # Ensure tables exist

    def add_node(self, type: str, content: dict[str, Any], agent_id: str, parent_ids: list[str] = None) -> str:
        """
        Create, seal, and store a new memory node in the database.
        """
        if parent_ids is None:
            parent_ids = []

        # 1. Create Node Object
        node = MemoryNode(
            id=str(uuid4()),
            type=type,
            content=content,
            agent_id=agent_id,
            parent_ids=parent_ids
        )

        # 2. Seal it (Immutable)
        node.seal()

        # 3. Store in Database
        db = SessionLocal()
        try:
            sql_node = SQLMemoryNode(
                id=node.id,
                type=node.type,
                content=json.dumps(node.content),  # Serialize dict to JSON string for DB
                agent_id=node.agent_id,
                timestamp=node.timestamp,
                node_hash=node.node_hash,
                parent_ids=json.dumps(node.parent_ids)  # Serialize list to JSON string
            )
            db.add(sql_node)
            db.commit()
            print(f"🕸️ [MEMORY] Node Added to DB: [{type}] {node.id}")
            return node.id

        except Exception as e:
            print(f"❌ Error saving node to DB: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def get_node(self, node_id: str) -> MemoryNode | None:
        """Fetch a node from the database."""
        db = SessionLocal()
        try:
            sql_node = db.query(SQLMemoryNode).filter(SQLMemoryNode.id == node_id).first()
            if not sql_node:
                return None

            return MemoryNode(
                id=sql_node.id,
                type=sql_node.type,
                content=json.loads(sql_node.content) if isinstance(sql_node.content, str) else sql_node.content,
                agent_id=sql_node.agent_id,
                timestamp=sql_node.timestamp,
                parent_ids=json.loads(sql_node.parent_ids) if sql_node.parent_ids else [],
                node_hash=sql_node.node_hash
            )
        except Exception as e:
            print(f"❌ Error fetching node: {e}")
            return None
        finally:
            db.close()

    def get_recent_nodes(self, limit: int = 10, node_type: str = None) -> list[MemoryNode]:
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
                    content=json.loads(n.content) if isinstance(n.content, str) else n.content,
                    agent_id=n.agent_id,
                    timestamp=n.timestamp,
                    parent_ids=json.loads(n.parent_ids) if n.parent_ids else [],
                    node_hash=n.node_hash
                ) for n in sql_nodes
            ]
        finally:
            db.close()