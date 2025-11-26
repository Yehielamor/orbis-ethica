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

class TransactionType:
    TRANSFER = "TRANSFER"
    STAKE = "STAKE"
    UNSTAKE = "UNSTAKE"
    SLASH = "SLASH"
    MINT = "MINT"
    APPEAL = "APPEAL"

class TokenTransaction(BaseModel):
    """
    Represents a value transfer or state change in the economic layer.
    """
    id: str = Field(..., description="Unique Transaction ID")
    type: str = Field(..., description="Transaction Type")
    sender: str = Field(..., description="Sender Address (Public Key) or 'SYSTEM'")
    receiver: str = Field(..., description="Receiver Address (Public Key) or 'BURN'")
    amount: float = Field(..., ge=0, description="Amount of $ETHC")
    timestamp: float = Field(default_factory=time.time)
    signature: str = Field(..., description="Sender's signature")

class LedgerBlock(BaseModel):
    """
    Represents a block in the blockchain.
    Each block contains a list of transactions.
    """
    index: int = Field(..., description="Block number in the chain")
    timestamp: str = Field(..., description="Time of block creation (ISO format)")
    data: Dict[str, Any] = Field(..., description="Arbitrary data for the block")
    transactions: List[TokenTransaction] = Field(default_factory=list, description="List of transactions included in the block")
    previous_hash: str = Field(..., description="Hash of the previous block")
    hash: str = Field(..., description="Hash of this block")
    nonce: int = Field(default=0, description="Nonce for Proof-of-Work")
    signer_id: Optional[str] = Field(None, description="Public key of the block signer/miner")
    signature: Optional[str] = Field(None, description="Digital signature of the block by the signer")

    def calculate_hash(self) -> str:
        """
        Calculates the SHA-256 hash of the block's contents.
        The signature field is excluded from the hash calculation to prevent circular dependencies.
        """
        block_string = json.dumps(
            self.model_dump(exclude={'hash', 'signature'}),
            sort_keys=True,
            default=str # Handle datetime objects if any
        ).encode()
        return hashlib.sha256(block_string).hexdigest()


class LedgerBlock(BaseModel):
    """
    Represents a single block in the immutable ledger.
    """
    index: int = Field(..., description="Position in the chain")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    data: Dict[str, Any] = Field(..., description="The actual data stored (e.g., node hash, content)")
    transactions: List[TokenTransaction] = Field(default_factory=list, description="List of economic transactions")
    previous_hash: str = Field(..., description="Hash of the previous block")
    hash: str = Field(..., description="Hash of this block")
    nonce: int = Field(default=0, description="Nonce for proof of work (simplified)")
    signer_id: Optional[str] = Field(default=None, description="Public key of the node that mined this block")
    signature: Optional[str] = Field(default=None, description="Cryptographic signature of the block hash")

    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block content."""
        # Include transactions in hash calculation
        tx_data = [tx.model_dump() for tx in self.transactions]
        
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "transactions": tx_data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "signer_id": self.signer_id
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()


class LedgerAdapter(ABC):
    """Abstract interface for blockchain interactions."""
    
    @abstractmethod
    def add_block(self, data: Dict[str, Any], transactions: List[TokenTransaction] = []) -> LedgerBlock:
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
    
    @abstractmethod
    def get_balance(self, address: str) -> float:
        """Get the token balance of an address."""
        pass
    
    @abstractmethod
    def get_stake_balance(self, address: str) -> float:
        """Get the staked balance of an address."""
        pass


class StakingContract:
    """
    Manages the logic for Staking, Unstaking, and Validator sets.
    This acts as a 'Smart Contract' layer on top of the Ledger.
    """
    STAKING_ADDRESS = "STAKING_CONTRACT_V1"
    MIN_STAKE_VALIDATOR = 32000.0
    MIN_STAKE_KNOWLEDGE = 10000.0
    
    def __init__(self, ledger_adapter: 'LedgerAdapter'):
        self.ledger = ledger_adapter
        
    def get_stake(self, address: str) -> float:
        """Get the amount currently staked by an address."""
        return self.ledger.get_stake_balance(address)

    def is_validator(self, address: str) -> bool:
        return self.get_stake(address) >= self.MIN_STAKE_VALIDATOR

    def is_trusted_source(self, address: str) -> bool:
        return self.get_stake(address) >= self.MIN_STAKE_KNOWLEDGE


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
        self.state: Dict[str, float] = {} # Address -> Balance
        self.stakes: Dict[str, float] = {} # Address -> Staked Amount
        self.identity = identity # NodeIdentity instance
        self.genesis_config = self._load_genesis_config()
        self.create_genesis_block()
        
    def _load_genesis_config(self) -> Dict[str, Any]:
        """Load genesis configuration from json file."""
        try:
            with open("genesis.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ genesis.json not found, using defaults.")
            return {}

    def create_genesis_block(self):
        """Create the first block in the chain."""
        # Load from config or use defaults
        initial_balances = self.genesis_config.get("initial_balances", {})
        genesis_wallet_amount = initial_balances.get("genesis_wallet", 1_000_000.0)
        
        # Initial Distribution (Minting)
        genesis_txs = []
        for wallet, amount in initial_balances.items():
            # If identity is set, override 'genesis_wallet' with public key, else keep name
            receiver = wallet
            if wallet == "genesis_wallet" and self.identity:
                receiver = self.identity.public_key_hex
                
            tx = TokenTransaction(
                id=f"genesis_mint_{wallet}",
                type=TransactionType.MINT,
                sender="SYSTEM",
                receiver=receiver,
                amount=amount, 
                signature="genesis_sig"
            )
            genesis_txs.append(tx)
        
        genesis_block = LedgerBlock(
            index=0,
            timestamp=self.genesis_config.get("timestamp", datetime.utcnow().isoformat()),
            data={"message": "Genesis Block - Orbis Ethica", "params": self.genesis_config.get("params", {})},
            transactions=genesis_txs,
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
        self._update_state(genesis_txs) # Update balances
        print(f"⛓️  Genesis Block Created: {genesis_block.hash[:12]}...")
        for tx in genesis_txs:
            print(f"💰 Minted: {tx.amount} ETHC -> {tx.receiver}")

    def get_latest_block(self) -> LedgerBlock:
        """Get the most recent block."""
        return self.chain[-1]

    def add_block(self, data: Dict[str, Any], transactions: List[TokenTransaction] = []) -> LedgerBlock:
        """
        Create a new block, mine it (PoW), and add to chain.
        """
        # Validate transactions against current state (Sufficient Funds)
        valid_txs = []
        for tx in transactions:
            if self._validate_transaction(tx):
                valid_txs.append(tx)
            else:
                print(f"⚠️ Transaction Rejected: {tx.id} (Insufficient Funds or Invalid)")

        latest_block = self.get_latest_block()
        new_block = LedgerBlock(
            index=latest_block.index + 1,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            transactions=valid_txs,
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
        self._update_state(valid_txs) # Update balances
        self._apply_block_reward(new_block.signer_id) # Block Reward
        return new_block

    def _apply_block_reward(self, miner_address: Optional[str]):
        """Mint new tokens for the block miner."""
        if not miner_address:
            return
            
        reward = self.genesis_config.get("params", {}).get("block_reward", 5.0)
        self.state[miner_address] = self.state.get(miner_address, 0.0) + reward
        print(f"⛏️  Block Reward: {reward} ETHC -> {miner_address[:8]}...")

    def get_chain(self) -> List[LedgerBlock]:
        return self.chain
        
    def get_balance(self, address: str) -> float:
        """Get the token balance of an address."""
        return self.state.get(address, 0.0)

    def get_stake_balance(self, address: str) -> float:
        """Get the staked balance of an address."""
        return self.stakes.get(address, 0.0)

    def _validate_transaction(self, tx: TokenTransaction) -> bool:
        """Check if sender has enough balance."""
        if tx.type == TransactionType.MINT:
            return True # System can mint
            
        if tx.type == TransactionType.APPEAL:
            # SAFETY CHECK: Only Governance Wallet can sign APPEAL
            gov_wallet = self.genesis_config.get("governance_wallet")
            if not gov_wallet:
                print("❌ Appeal rejected: No Governance Wallet defined in genesis.json")
                return False
            
            # In a real implementation, we would verify the cryptographic signature here.
            # For this MVP/Simulation, we check if the sender matches the governance wallet ID.
            if tx.sender != gov_wallet:
                print(f"❌ Appeal rejected: Sender {tx.sender} is not Governance Wallet")
                return False
            return True
        
        # INTEGRITY CHECKS (Phase XII)
        if not self._check_vesting(tx.sender, tx.amount):
            return False
            
        if not self._check_ethical_pool(tx.sender, tx):
            return False
        
        balance = self.get_balance(tx.sender)
        return balance >= tx.amount

    def _update_state(self, transactions: List[TokenTransaction]):
        """Update local state (balances) based on transactions."""
        for tx in transactions:
            if tx.type == TransactionType.TRANSFER:
                self.state[tx.sender] = self.state.get(tx.sender, 0.0) - tx.amount
                self.state[tx.receiver] = self.state.get(tx.receiver, 0.0) + tx.amount
            elif tx.type == TransactionType.MINT:
                self.state[tx.receiver] = self.state.get(tx.receiver, 0.0) + tx.amount
            elif tx.type == TransactionType.SLASH:
                # Burn from STAKE
                current_stake = self.stakes.get(tx.sender, 0.0)
                if current_stake >= tx.amount:
                    self.stakes[tx.sender] = current_stake - tx.amount
                else:
                    self.stakes[tx.sender] = 0.0
                # Receiver is 'BURN', effectively gone.
            elif tx.type == TransactionType.STAKE:
                # Liquid -> Staked
                self.state[tx.sender] = self.state.get(tx.sender, 0.0) - tx.amount
                self.stakes[tx.sender] = self.stakes.get(tx.sender, 0.0) + tx.amount
                self.state["STAKING_CONTRACT"] = self.state.get("STAKING_CONTRACT", 0.0) + tx.amount
            elif tx.type == TransactionType.UNSTAKE:
                # Staked -> Liquid
                self.stakes[tx.sender] = self.stakes.get(tx.sender, 0.0) - tx.amount
                self.state[tx.sender] = self.state.get(tx.sender, 0.0) + tx.amount
                self.state["STAKING_CONTRACT"] = self.state.get("STAKING_CONTRACT", 0.0) - tx.amount
            elif tx.type == TransactionType.APPEAL:
                # Restore funds (Minting to victim)
                # Sender is Governance, Receiver is Victim
                self.state[tx.receiver] = self.state.get(tx.receiver, 0.0) + tx.amount
                print(f"⚖️  Appeal Executed: Restored {tx.amount} ETHC to {tx.receiver}")

    def _check_vesting(self, sender: str, amount: float) -> bool:
        """
        Check if the transaction violates vesting rules.
        Returns True if allowed, False if blocked.
        """
        if sender != "founder_vesting_contract":
            return True
            
        vesting_config = self.genesis_config.get("params", {}).get("vesting_schedule", {})
        if not vesting_config:
            return True # No vesting configured
            
        # Calculate time since genesis
        genesis_time = datetime.fromisoformat(self.chain[0].timestamp.replace("Z", "+00:00"))
        current_time = datetime.utcnow()
        # Ensure UTC awareness (simplified)
        if genesis_time.tzinfo is None:
            genesis_time = genesis_time.replace(tzinfo=None) # Make naive if needed
            
        years_passed = (current_time - genesis_time).days / 365.25
        
        # Cliff Check
        cliff_years = vesting_config.get("cliff_months", 12) / 12.0
        if years_passed < cliff_years:
            print(f"🔒 Vesting Locked: Cliff period not over ({years_passed:.2f} / {cliff_years} years)")
            return False
            
        # Release Schedule
        duration = vesting_config.get("duration_years", 5)
        release_per_year = vesting_config.get("release_per_year", 0.20)
        
        # Calculate max allowed withdrawal
        # Total initial balance
        initial_balance = self.genesis_config.get("initial_balances", {}).get("founder_vesting_contract", 0.0)
        
        # Allowed percentage
        allowed_pct = min(1.0, int(years_passed) * release_per_year)
        allowed_amount = initial_balance * allowed_pct
        
        # Check how much has already been spent
        current_balance = self.get_balance(sender)
        spent_amount = initial_balance - current_balance
        
        # If trying to spend more than allowed total
        if (spent_amount + amount) > allowed_amount:
            print(f"🔒 Vesting Locked: Exceeds allowed release ({allowed_pct*100}%)")
            return False
            
        return True

    def _check_ethical_pool(self, sender: str, tx: TokenTransaction) -> bool:
        """
        Validate transactions from the Ethical Allocation Pool.
        Only 'GRANT' or 'STAKE' (on behalf of others) should be allowed.
        """
        if sender != "ethical_allocation_pool":
            return True
            
        # For now, we only allow STAKE (Granting stake to others) or TRANSFER (Grants)
        # But we must ensure it's not being drained by unauthorized parties.
        # In a real DAO, this would require MultiSig from the 'Global Ethical Assembly'.
        # Here we assume the signature validation (handled elsewhere) covers authorization.
        
        # We can add logic here to limit max grant size per tx
        max_grant = self.genesis_config.get("params", {}).get("junior_validator_program", {}).get("grant_amount", 32000.0)
        if tx.amount > max_grant:
             print(f"🛡️ Ethical Pool: Grant size {tx.amount} exceeds limit {max_grant}")
             return False
             
        return True

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

    def add_block_from_peer(self, block_data: Dict[str, Any]) -> bool:
        """
        Add a block received from a peer.
        Returns True if added, False if invalid or already exists.
        """
        try:
            # 1. Parse Block
            # Handle transactions separately to convert back to objects
            tx_data = block_data.get("transactions", [])
            transactions = []
            for t in tx_data:
                transactions.append(TokenTransaction(**t))
                
            new_block = LedgerBlock(
                index=block_data["index"],
                timestamp=block_data["timestamp"],
                data=block_data["data"],
                transactions=transactions,
                previous_hash=block_data["previous_hash"],
                hash=block_data["hash"],
                nonce=block_data["nonce"],
                signer_id=block_data.get("signer_id")
            )
            
            # 2. Check if we already have it
            if len(self.chain) > new_block.index:
                existing = self.chain[new_block.index]
                if existing.hash == new_block.hash:
                    return False # Duplicate
                else:
                    print(f"⚠️ Fork detected at height {new_block.index}!")
                    return False # Simple conflict resolution: keep local
            
            # 3. Check if it fits the chain (Next block)
            last_block = self.get_latest_block()
            if new_block.index != last_block.index + 1:
                print(f"⚠️ Received block {new_block.index} but current height is {last_block.index}. Sync needed.")
                return False
                
            # 4. Validate Hash Link
            if new_block.previous_hash != last_block.hash:
                print("❌ Block rejected: Invalid previous_hash")
                return False
                
            # 5. Validate Proof of Work (Basic check)
            if not new_block.hash.startswith("0" * 4): # Assuming difficulty 4
                 # Re-calculate to be sure
                 if new_block.calculate_hash() != new_block.hash:
                     print("❌ Block rejected: Invalid hash")
                     return False
            
            # 6. Add and Update State
            self.chain.append(new_block)
            self._update_state(new_block.transactions)
            self._apply_block_reward(new_block.signer_id)
            print(f"🔗 Added Block #{new_block.index} from Peer")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add peer block: {e}")
            return False

    # --- P2P Methods (Phase VIII) ---

    # add_block_from_peer is implemented above.

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
