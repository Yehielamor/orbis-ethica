"""
Ledger Core - Immutable Blockchain Implementation.
Provides the cryptographic backbone for the Orbis Ethica system.
"""

import hashlib
import json
import time
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
    signer_id: Optional[str] = Field(default=None, description="Public key of the node that mined this block")
    signature: Optional[str] = Field(default=None, description="Cryptographic signature of the block hash")

    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block content."""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "signer_id": self.signer_id
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
    
    def __init__(self, identity: Optional[Any] = None):
        """
        Initialize the blockchain with a Genesis Block.
        """
        self.chain: List[LedgerBlock] = []
        self.identity = identity # NodeIdentity instance
        self.create_genesis_block()
        
    def create_genesis_block(self):
        """Create the first block in the chain."""
        genesis_block = LedgerBlock(
            index=0,
            timestamp=datetime.utcnow().isoformat(),
            data={"message": "Genesis Block - Orbis Ethica"},
            previous_hash="0",
            hash="", # Placeholder, calculated below
            nonce=0,
            signer_id=self.identity.public_key_hex if self.identity else "genesis"
        )
        genesis_block.hash = genesis_block.calculate_hash() # Recalculate hash after setting nonce
        # Sign genesis block if identity exists
        if self.identity:
            genesis_block.signature = self.identity.sign(genesis_block.model_dump(exclude={'signature', 'hash'}))
            
        self.chain.append(genesis_block)
        print(f"⛓️  Genesis Block Created: {genesis_block.hash[:12]}...")

    def get_latest_block(self) -> LedgerBlock:
        """Get the most recent block."""
        return self.chain[-1]

    def add_block(self, data: Dict[str, Any]) -> LedgerBlock:
        """
        Create a new block, mine it (PoW), and add to chain.
        """
        latest_block = self.get_latest_block()
        new_block = LedgerBlock(
            index=latest_block.index + 1,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            previous_hash=latest_block.hash,
            hash="", # Placeholder
            signer_id=self.identity.public_key_hex if self.identity else None
        )
        
        # Simple Proof of Work (find nonce such that hash starts with '00')
        # In production, difficulty would be dynamic
        new_block.hash = new_block.calculate_hash() # Initial hash calculation
        while not new_block.hash.startswith('00'):
            new_block.nonce += 1
            # Recalculate hash (which includes nonce)
            new_block.hash = new_block.calculate_hash()
        
        # Sign the block
        if self.identity:
            # We sign the dictionary representation excluding the signature field itself
            block_data_to_sign = new_block.model_dump(exclude={'signature'})
            new_block.signature = self.identity.sign(block_data_to_sign)
            
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

    # --- P2P Methods (Phase VIII) ---

    def add_block_from_peer(self, block_data: Dict[str, Any]) -> bool:
        """
        Attempt to add a block received from a peer.
        Returns True if successful, False otherwise.
        """
        try:
            # 1. Parse block
            new_block = LedgerBlock(**block_data)
            
            # 2. Check index
            latest_block = self.get_latest_block()
            if new_block.index != latest_block.index + 1:
                print(f"⚠️ Block rejected: Index mismatch (Expected {latest_block.index + 1}, Got {new_block.index})")
                return False
            
            # 3. Check previous hash
            if new_block.previous_hash != latest_block.hash:
                print(f"⚠️ Block rejected: Previous hash mismatch")
                return False
            
            # 4. Check hash validity
            if new_block.hash != new_block.calculate_hash():
                print(f"⚠️ Block rejected: Invalid hash")
                return False
                
            # 5. Add to chain
            self.chain.append(new_block)
            print(f"🔗 Added Peer Block: {new_block.hash[:8]} (Height: {new_block.index})")
            return True
            
        except Exception as e:
            print(f"❌ Error adding peer block: {e}")
            return False

    def replace_chain(self, new_chain_data: List[Dict[str, Any]]) -> bool:
        """
        Consensus: Replace local chain with a longer valid chain from a peer.
        """
        if len(new_chain_data) <= len(self.chain):
            return False
            
        try:
            # Validate new chain
            temp_chain = [LedgerBlock(**b) for b in new_chain_data]
            
            # Verify Genesis
            if temp_chain[0].hash != self.chain[0].hash:
                 print("⚠️ Chain rejected: Different Genesis Block")
                 return False

            # Verify entire chain integrity
            for i in range(1, len(temp_chain)):
                curr = temp_chain[i]
                prev = temp_chain[i-1]
                if curr.previous_hash != prev.hash or curr.hash != curr.calculate_hash():
                    print("⚠️ Chain rejected: Invalid link found")
                    return False
            
            # Replace
            self.chain = temp_chain
            print(f"🔄 Chain Replaced! New Height: {len(self.chain)}")
            return True
            
        except Exception as e:
            print(f"❌ Error replacing chain: {e}")
            return False
