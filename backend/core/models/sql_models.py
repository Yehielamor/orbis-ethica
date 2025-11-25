"""
SQLAlchemy Models.
Maps core domain objects to database tables.
"""

from sqlalchemy import Column, String, Float, Integer, JSON, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class SQLEntity(Base):
    """Persistent storage for Cognitive Entities."""
    __tablename__ = "entities"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)
    reputation = Column(Float, default=0.5)
    staked_reputation = Column(Float, default=0.0)
    primary_focus = Column(String)
    bias_description = Column(String)
    decisions_participated = Column(Integer, default=0)
    
    # Relationships (optional for now)

class SQLProposal(Base):
    """Persistent storage for Proposals."""
    __tablename__ = "proposals"

    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String)
    domain = Column(String)
    submitter_id = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    context = Column(JSON)
    refinements_made = Column(JSON)

class SQLDecision(Base):
    """Persistent storage for Verdicts."""
    __tablename__ = "decisions"

    id = Column(String, primary_key=True, index=True)
    proposal_id = Column(String, ForeignKey("proposals.id"))
    outcome = Column(String)
    weighted_vote = Column(Float)
    threshold_required = Column(Float)
    deliberation_rounds = Column(Integer)
    rationale = Column(Text)
    weights_used = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Store full evaluations as JSON for simplicity in MVP
    entity_evaluations = Column(JSON)

class SQLMemoryNode(Base):
    """Persistent storage for the Memory Graph (DAG)."""
    __tablename__ = "memory_nodes"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, index=True)
    content = Column(JSON)
    agent_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    node_hash = Column(String)
    signature = Column(String)
    
    # Store parent IDs as JSON list
    parent_ids = Column(JSON)
    
    # Ledger anchoring
    ledger_block_index = Column(Integer, nullable=True)
    ledger_block_hash = Column(String, nullable=True)
