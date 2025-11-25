"""
Ledger Core - Immutable Blockchain Implementation.
Provides the cryptographic backbone for the Orbis Ethica system.
"""

import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

class LedgerBlock(BaseModel):
    """
    Represents a single block in the immutable ledger.
    """
    index: int = Field(..., description="Position in the chain")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    data: Dict[str, Any] = Field(..., description="The actual data stored (e.g., node hash, content)")
    previous_hash: str = Field(..., description="Hash of the previous block")
    hash: str = Field(..., description="Hash of this block")
    nonce: int = Field(default=0, description="Nonce for proof of work (simplified)")

    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block content."""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()


class LedgerAdapter(ABC):
    """Abstract interface for blockchain interactions."""
    
    @abstractmethod
    def add_block(self, data: Dict[str, Any]) -> LedgerBlock:
        """Add a new block to the chain."""
        pass
    
    @abstractmethod
    def get_chain(self) -> List[LedgerBlock]:
        """Return the full chain."""
        pass
    
    @abstractmethod
    def verify_integrity(self) -> bool:
        """Verify the cryptographic integrity of the chain."""
        pass


class LocalBlockchain(LedgerAdapter):
    """
    Local implementation of a blockchain.
    Stores the chain in memory (and optionally persists to disk).
    """
    
    def __init__(self):
        self.chain: List[LedgerBlock] = []
        self._create_genesis_block()
        
    def _create_genesis_block(self):
        """Create the first block in the chain."""
        genesis_block = LedgerBlock(
            index=0,
            timestamp=datetime.utcnow().isoformat(),
            data={"message": "Genesis Block - Orbis Ethica System Start"},
            previous_hash="0" * 64,
            hash="",
            nonce=0
        )
        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)
        print(f"⛓️  Genesis Block Created: {genesis_block.hash[:12]}...")

    def get_latest_block(self) -> LedgerBlock:
        """Get the most recent block."""
        return self.chain[-1]

    def add_block(self, data: Dict[str, Any]) -> LedgerBlock:
        """
        Add a new block with the given data.
        """
        previous_block = self.get_latest_block()
        
        new_block = LedgerBlock(
            index=previous_block.index + 1,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            previous_hash=previous_block.hash,
            hash="",
            nonce=0
        )
        
        # Simple Proof of Work (optional, kept simple for speed)
        # In a real system, we might require hash to start with '0000'
        new_block.hash = new_block.calculate_hash()
        
        self.chain.append(new_block)
        return new_block

    def get_chain(self) -> List[LedgerBlock]:
        return self.chain

    def verify_integrity(self) -> bool:
        """
        Verify that the chain has not been tampered with.
        Checks:
        1. Block hash is valid for its content.
        2. Block's previous_hash matches the actual hash of the previous block.
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # 1. Check current block hash
            if current_block.hash != current_block.calculate_hash():
                print(f"❌ INTEGRITY ERROR: Block {i} hash invalid!")
                return False
                
            # 2. Check link to previous block
            if current_block.previous_hash != previous_block.hash:
                print(f"❌ INTEGRITY ERROR: Block {i} previous_hash mismatch!")
                return False
                
        return True
