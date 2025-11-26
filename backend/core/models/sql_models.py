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

class VoteModel(Base):
    """Represents a vote on a proposal."""
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(String, ForeignKey("proposals.id"), nullable=False)
    voter_id = Column(String, nullable=False) # Node ID
    vote_value = Column(Float, nullable=False) # -1.0 to 1.0
    weight = Column(Float, default=1.0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    proposal = relationship("SQLProposal", back_populates="votes")

class BlockModel(Base):
    """Represents a block in the blockchain."""
    __tablename__ = "blocks"

    index = Column(Integer, primary_key=True)
    hash = Column(String, unique=True, nullable=False)
    previous_hash = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    validator_id = Column(String, nullable=False)
    signature = Column(String, nullable=False)
    
    # Relationship
    transactions = relationship("LedgerEntryModel", back_populates="block")

class LedgerEntryModel(Base):
    """Represents a transaction or ledger entry."""
    __tablename__ = "ledger_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sender = Column(String, nullable=False) # "system" or node_id
    recipient = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="ETHC")
    transaction_type = Column(String, nullable=False) # "reward", "transfer", "penalty"
    reference_id = Column(String, nullable=True) # e.g. proposal_id
    description = Column(String, nullable=True)
    
    # Link to Block
    block_hash = Column(String, ForeignKey("blocks.hash"), nullable=True)
    block = relationship("BlockModel", back_populates="transactions")

# Update SQLProposal to include relationship
SQLProposal.votes = relationship("VoteModel", back_populates="proposal")
