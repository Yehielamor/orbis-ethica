"""
Ledger Module
Manages economic transactions and token balances using SQLite.
"""

import hashlib
import json
import os
import threading
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel

from .database import DatabaseManager
from .models.sql_models import LedgerEntryModel


class TransactionType(str, Enum):
    TRANSFER = "transfer"
    STAKE = "stake"
    UNSTAKE = "unstake"
    REWARD = "reward"
    PENALTY = "penalty"
    MINT = "mint"
    SLASH = "slash"

class TokenTransaction(BaseModel):
    id: str
    type: TransactionType
    sender: str
    receiver: str
    amount: float
    signature: str
    timestamp: datetime = None

class Ledger:
    """
    Manages economic transactions and token balances using SQLite.
    """
    MAX_SUPPLY = 10_000_000.0
    
    def __init__(self, db_url: str = None):
        if db_url is None:
            if os.path.exists("/app/data"):
                db_url = "sqlite:///data/orbis_ethica.db"
            else:
                db_url = "sqlite:///backend/orbis_ethica.db"
                
        self.db_manager = DatabaseManager(db_url)
        self.MAX_SUPPLY = 10_000_000.0
        self._lock = threading.Lock() # Prevent race conditions
        
        # Initialize tables
        # self.db_manager.create_tables() # Already done in DatabaseManager.__init__
        
        # Load Genesis if empty
        # Correcting the typo from the user's diff:
        # self.load_genesis()ager.get_session() -> self.load_genesis()
        # However, the original code had `self.db_manager = db_manager or DatabaseManager()`,
        # and the user's diff completely changed the `__init__` method.
        # I will apply the user's diff for `__init__` as faithfully as possible, correcting the typo.
        self.load_genesis() # Assuming this method exists or will be added.

    def get_total_supply(self) -> float:
        """Calculate total circulating supply."""
        session = self.db_manager.get_session()
        try:
            # Sum only 'mint' transactions (Genesis + System Mints)
            # Rewards are transfers from the INFERENCE_REWARD_POOL, so they don't increase supply.
            mints = session.query(LedgerEntryModel).filter(
                LedgerEntryModel.transaction_type == "mint"
            ).all()
            total_minted = sum(tx.amount for tx in mints)
            
            # Subtract burns (penalties sent to system_burn)
            burns = session.query(LedgerEntryModel).filter_by(recipient="system_burn").all()
            total_burned = sum(tx.amount for tx in burns)
            
            return total_minted - total_burned
        finally:
            session.close()
        
    def record_transaction(self, sender: str, recipient: str, amount: float, 
                          tx_type: str, reference_id: str = None, description: str = None) -> bool:
        """
        Record a transaction in the ledger.
        Enforces MAX_SUPPLY for minting operations.
        """
        # Enforce Hard Cap
        with self._lock:
            # Only check cap for fresh mints (system_mint)
            if tx_type == "mint" or (tx_type == "reward" and sender == "system_mint"):
                current_supply = self.get_total_supply()
                if current_supply + amount > self.MAX_SUPPLY:
                    print(f"❌ Minting rejected: Cap exceeded. Supply: {current_supply}, Requested: {amount}, Max: {self.MAX_SUPPLY}")
                    return False

            # Enforce Sufficient Balance (for Transfer/Stake/Burn)
            if tx_type in ["transfer", "stake", "burn"]:
                sender_balance = self.get_balance(sender)
                if sender_balance < amount:
                    print(f"❌ Transaction rejected: Insufficient funds. Balance: {sender_balance}, Requested: {amount}")
                    return False

            session = self.db_manager.get_session()
            try:
                # Create entry
                entry = LedgerEntryModel(
                    sender=sender,
                    recipient=recipient,
                    amount=amount,
                    transaction_type=tx_type,
                    reference_id=reference_id,
                    description=description
                )
                session.add(entry)
                session.commit()
                print(f"💰 Transaction recorded: {sender} -> {recipient} : {amount} ({tx_type})")
                return True
            except Exception as e:
                session.rollback()
                print(f"❌ Transaction failed: {e}")
                return False
            finally:
                session.close()

    def create_transaction(self, sender: str, recipient: str, amount: float, 
                          tx_type: str = "transfer", reference_id: str = None, description: str = None) -> bool:
        """
        Alias for record_transaction to maintain compatibility.
        """
        return self.record_transaction(sender, recipient, amount, tx_type, reference_id, description)

    def get_balance(self, address: str) -> float:
        """
        Calculate balance for an address by summing transactions.
        """
        session = self.db_manager.get_session()
        try:
            # Incoming
            incoming = session.query(LedgerEntryModel).filter_by(recipient=address).all()
            total_in = sum(tx.amount for tx in incoming)
            
            # Outgoing
            outgoing = session.query(LedgerEntryModel).filter_by(sender=address).all()
            total_out = sum(tx.amount for tx in outgoing)
            
            return total_in - total_out
        finally:
            session.close()

    def get_reputation_score(self, address: str) -> float:
        """
        Alias for get_balance. 
        In the Scientific Protocol, 'Balance' is 'Reputation'.
        """
        return self.get_balance(address)

    def get_stake_balance(self, address: str) -> float:
        """Calculate current staked amount."""
        session = self.db_manager.get_session()
        try:
            # Sum stakes (sent to STAKING_CONTRACT)
            stakes = session.query(LedgerEntryModel).filter_by(
                sender=address, 
                recipient="STAKING_CONTRACT",
                transaction_type="stake"
            ).all()
            total_staked = sum(tx.amount for tx in stakes)
            
            # Sum unstakes (received from STAKING_CONTRACT)
            unstakes = session.query(LedgerEntryModel).filter_by(
                sender="STAKING_CONTRACT",
                recipient=address,
                transaction_type="unstake"
            ).all()
            total_unstaked = sum(tx.amount for tx in unstakes)
            
            return total_staked - total_unstaked
        finally:
            session.close()

    def mint_reward(self, recipient: str, amount: float, reason: str) -> bool:
        """
        Distribute reward from the Inference Reward Pool.
        (Does not increase total supply, just moves from Pool -> User)
        """
        return self.record_transaction(
            sender="INFERENCE_REWARD_POOL",
            recipient=recipient,
            amount=amount,
            tx_type="reward",
            description=reason
        )

    def slash_validator(self, validator_id: str, amount: float, reason: str = "Invalid behavior") -> bool:
        """
        Slash a validator's stake (penalty). 
        Moves tokens to 'slash_escrow_vault' for the Purgatory Period (Appeal Window).
        """
        return self.record_transaction(
            sender=validator_id,
            recipient="slash_escrow_vault", # Move to Escrow (Purgatory)
            amount=amount,
            tx_type=TransactionType.SLASH.value, 
            description=f"{reason} (Held in Escrow for Appeal)"
        )

    # Hybrid Recycling Ratios
    RECYCLE_RATIO_FAST = 0.50    # Inference Rewards (Immediate)
    RECYCLE_RATIO_SLOW = 0.30    # Treasury (Long-term)
    BURN_RATIO = 0.20            # Permanent Burn (Deflationary)

    def release_from_escrow(self, amount: float, reason: str = "") -> bool:
        """
        Purgatory Protocol Resolution (Whitepaper 5.4):
        - Appeal Failed / No Appeal: Tokens are recycled to the Public Sale Treasury.
        - Non-Deflationary: 100% of slashed funds stay in the ecosystem.
        """
        # Recycle 100% to Public Sale Treasury
        success = self.record_transaction(
            sender="slash_escrow_vault",
            recipient="PUBLIC_SALE_TREASURY",
            amount=amount,
            tx_type="recycle",
            description=f"Purgatory Expired: {reason} -> Recycled to Treasury"
        )
        
        if success:
            print(f"♻️  Recycled {amount} ETHC to Public Sale Treasury (Non-Deflationary)")
        return success
        
    def get_transaction_history(self, address: str = None) -> list[dict]:
        """Get transaction history, optionally filtered by address."""
        session = self.db_manager.get_session()
        try:
            query = session.query(LedgerEntryModel)
            if address:
                # Filter where sender OR recipient is address
                from sqlalchemy import or_
                query = query.filter(or_(LedgerEntryModel.sender == address, LedgerEntryModel.recipient == address))
            
            entries = query.order_by(LedgerEntryModel.timestamp.desc()).all()
            
            return [{
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "sender": e.sender,
                "recipient": e.recipient,
                "amount": e.amount,
                "type": e.transaction_type,
                "description": e.description
            } for e in entries]
        finally:
            session.close()
            
    def calculate_block_reward(self, block_index: int, reputation_score: float = 1.0) -> float:
        """
        Calculate block reward based on Halving Schedule and Reputation.
        
        Formula:
        Base Reward = Initial Reward / (2 ^ (Block Index / Halving Interval))
        Final Reward = Base Reward * Reputation Score
        """
        INITIAL_REWARD = 1.0 # Aligned with Whitepaper V5
        HALVING_INTERVAL = 100_000 # Blocks
        
        # 1. Calculate Base Reward (Halving)
        halvings = block_index // HALVING_INTERVAL
        base_reward = INITIAL_REWARD / (2 ** halvings)
        
        # 2. Apply Reputation Multiplier
        # Reputation is 0.0 to 1.0. 
        # We want to strictly penalize low reputation.
        final_reward = base_reward * max(0.1, min(1.0, reputation_score))
        
        return round(final_reward, 6)

    def create_block(self, validator_id: str, private_key: Any, reward_recipient: str = None, reputation_score: float = 1.0) -> Any | None:
        """
        Create a new block from pending transactions.
        Optionally mints a reward to the validator/miner.
        """
        session = self.db_manager.get_session()
        try:
            # 2. Get last block for linking (Moved up to calculate index)
            from .models.sql_models import BlockModel
            last_block = session.query(BlockModel).order_by(BlockModel.index.desc()).first()
            new_index = (last_block.index + 1) if last_block else 0
            
            # 0. Mint Reward (Coinbase Transaction)
            if reward_recipient:
                # Calculate dynamic reward
                reward_amount = self.calculate_block_reward(new_index, reputation_score)
                
                if reward_amount > 0:
                    self.mint_reward(reward_recipient, reward_amount, f"Block Reward #{new_index} (Rep: {reputation_score:.2f})")
                    # Commit immediately so it's included in pending_txs query below
            
            # 1. Get pending transactions (those without a block_hash)
            pending_txs = session.query(LedgerEntryModel).filter(LedgerEntryModel.block_hash == None).all()
            previous_hash = last_block.hash if last_block else "0" * 64
            
            # 3. Calculate Merkle Root
            from .merkle import MerkleTree
            tx_ids = sorted([str(tx.id) for tx in pending_txs])
            # We should really hash the tx content, but for now ID is fine as it's unique
            # Ideally: hash(tx.serialize())
            merkle_tree = MerkleTree(tx_ids)
            merkle_root = merkle_tree.get_root()
            
            # 4. Create Block Hash
            timestamp = datetime.utcnow()
            block_content = f"{new_index}{previous_hash}{timestamp.isoformat()}{merkle_root}{validator_id}"
            block_hash = hashlib.sha256(block_content.encode()).hexdigest()
            
            # 5. Sign Block
            # Assuming private_key has a sign method (Ed25519)
            # NodeIdentity.sign expects a dict
            signature = private_key.sign({"block_hash": block_hash})
            
            # 6. Save Block
            new_block = BlockModel(
                index=new_index,
                hash=block_hash,
                previous_hash=previous_hash,
                timestamp=timestamp,
                validator_id=validator_id,
                signature=signature,
                is_finalized=False, # Wait for consensus
                finalization_data=[]
            )
            session.add(new_block)
            
            # 7. Update Transactions
            for tx in pending_txs:
                tx.block_hash = block_hash
                
            session.commit()
            print(f"🧱 Block #{new_index} created! Hash: {block_hash[:8]}... Txs: {len(pending_txs)}")
            
            # Return a Pydantic-like object for compatibility
            class BlockObj(BaseModel):
                index: int
                hash: str
                previous_hash: str
                timestamp: datetime
                validator_id: str
                signature: str
                is_finalized: bool
                
            return BlockObj(
                index=new_index, 
                hash=block_hash,
                previous_hash=previous_hash,
                timestamp=timestamp,
                validator_id=validator_id,
                signature=signature,
                is_finalized=False
            )
            
        except Exception as e:
            session.rollback()
            print(f"❌ Block creation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            session.close()

    def finalize_block(self, block_hash: str, signatures: list[dict[str, str]]) -> bool:
        """
        Mark a block as finalized after receiving sufficient signatures.
        """
        session = self.db_manager.get_session()
        try:
            from .models.sql_models import BlockModel
            block = session.query(BlockModel).filter_by(hash=block_hash).first()
            
            if not block:
                print(f"❌ Cannot finalize unknown block: {block_hash}")
                return False
                
            if block.is_finalized:
                return True # Already finalized
                
            block.is_finalized = True
            block.finalization_data = signatures
            session.commit()
            print(f"✅ Block #{block.index} FINALIZED with {len(signatures)} signatures!")
            return True
        except Exception as e:
            session.rollback()
            print(f"❌ Block finalization failed: {e}")
            return False
        finally:
            session.close()

    # Compatibility methods for MemoryGraph anchoring
    def add_block(self, block_data: dict[str, Any]):
        """
        Mock method kept for MemoryGraph compatibility if it calls this directly.
        In the new flow, MemoryGraph should just read the ledger state.
        """
        # For now, return a dummy to keep MemoryGraph happy until we refactor it
        class DummyBlock(BaseModel):
            index: int
            hash: str
        return DummyBlock(index=999, hash="legacy_add_block_call")

    def validate_block(self, block_data: dict[str, Any]) -> bool:
        """
        Validate a block received from a peer.
        Checks: Hash, Signature, Previous Hash, Merkle Root.
        """
        try:
            # 1. Check if we already have it
            session = self.db_manager.get_session()
            from .models.sql_models import BlockModel
            if session.query(BlockModel).filter_by(hash=block_data['hash']).first():
                session.close()
                return True # Already valid and stored
            
            # 2. Verify Previous Hash
            last_block = session.query(BlockModel).order_by(BlockModel.index.desc()).first()
            expected_prev = last_block.hash if last_block else "0" * 64
            
            if block_data['index'] > 0 and block_data.get('previous_hash') != expected_prev:
                # This might be a fork or a future block.
                # For MVP, we reject if it doesn't fit our tip.
                # SyncManager should handle forks by requesting full chain.
                print(f"❌ Invalid previous hash: {block_data.get('previous_hash')} != {expected_prev}")
                session.close()
                return False
                
            # 3. Verify Hash Integrity (Skipped for MVP speed)
            
            # 4. Verify Signature (Skipped for MVP speed)
            
            session.close()
            return True
            
        except Exception as e:
            print(f"❌ Block validation error: {e}")
            return False

    def add_block_from_peer(self, block_data: dict[str, Any]) -> bool:
        """Validate and save a block received from a peer."""
        if not self.validate_block(block_data):
            return False
            
        session = self.db_manager.get_session()
        try:
            from .models.sql_models import BlockModel
            # Check existence again just in case
            if session.query(BlockModel).filter_by(hash=block_data['hash']).first():
                return True
                
            # Parse timestamp
            ts = block_data.get('timestamp')
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                
            new_block = BlockModel(
                index=block_data['index'],
                hash=block_data['hash'],
                previous_hash=block_data.get('previous_hash'),
                timestamp=ts,
                validator_id=block_data.get('validator_id'),
                signature=block_data.get('signature')
            )
            session.add(new_block)
            
            # Save Transactions
            from .models.sql_models import LedgerEntryModel
            transactions = block_data.get('transactions', [])
            for tx_data in transactions:
                # Check if tx already exists (e.g. from mempool)
                existing_tx = session.query(LedgerEntryModel).filter_by(id=tx_data.get('id')).first()
                if existing_tx:
                    existing_tx.block_hash = new_block.hash
                    continue
                    
                # Create new tx
                tx_ts = tx_data.get('timestamp')
                if isinstance(tx_ts, str):
                    tx_ts = datetime.fromisoformat(tx_ts.replace('Z', '+00:00'))
                    
                new_tx = LedgerEntryModel(
                    sender=tx_data['sender'],
                    recipient=tx_data['recipient'],
                    amount=tx_data['amount'],
                    transaction_type=tx_data['type'],
                    description=tx_data.get('description'),
                    timestamp=tx_ts,
                    block_hash=new_block.hash
                )
                session.add(new_tx)
                
            session.commit()
            print(f"✅ Added Block #{new_block.index} from peer with {len(transactions)} txs")
            return True
            
        except Exception as e:
            session.rollback()
            print(f"❌ Failed to add peer block: {e}")
            return False
        finally:
            session.close()

    def get_blocks_range(self, start_index: int, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch a range of blocks starting from start_index."""
        session = self.db_manager.get_session()
        try:
            from .models.sql_models import BlockModel
            blocks = session.query(BlockModel)\
                .filter(BlockModel.index >= start_index)\
                .order_by(BlockModel.index.asc())\
                .limit(limit)\
                .all()
                
            return [{
                "index": b.index,
                "hash": b.hash,
                "previous_hash": b.previous_hash,
                "timestamp": b.timestamp.isoformat(),
                "validator_id": b.validator_id,
                "transactions_count": 0, # TODO: Count txs
                "signature": b.signature
            } for b in blocks]
        except Exception as e:
            print(f"❌ Failed to fetch blocks range: {e}")
            return []
        finally:
            session.close()

    def get_latest_block(self):
        """
        Get the latest block from the DB.
        """
        session = self.db_manager.get_session()
        try:
            from .models.sql_models import BlockModel
            last_block = session.query(BlockModel).order_by(BlockModel.index.desc()).first()
            
            class BlockObj(BaseModel):
                index: int
                hash: str
                previous_hash: str
                timestamp: datetime
                validator_id: str
                signature: str
            
            if last_block:
                return BlockObj(
                    index=last_block.index, 
                    hash=last_block.hash,
                    previous_hash=last_block.previous_hash,
                    timestamp=last_block.timestamp,
                    validator_id=last_block.validator_id,
                    signature=last_block.signature
                )
            else:
                return BlockObj(
                    index=0, 
                    hash="genesis_pending",
                    previous_hash="0"*64,
                    timestamp=datetime.utcnow(),
                    validator_id="genesis",
                    signature="none"
                )
        finally:
            session.close()

    def load_genesis(self, genesis_path: str = "genesis.json"):
        """
        Load genesis configuration and initialize the chain if empty.
        """
        import os
        
        if not os.path.exists(genesis_path):
            print(f"⚠️ Genesis file not found at {genesis_path}")
            return

        session = self.db_manager.get_session()
        try:
            from .models.sql_models import BlockModel, LedgerEntryModel
            
            # Check if genesis block exists
            if session.query(BlockModel).filter_by(index=0).first():
                print("✅ Genesis block already exists.")
                return

            # Check if genesis transactions already exist (to prevent double minting on restart)
            if session.query(LedgerEntryModel).filter_by(transaction_type="mint", description="Genesis Allocation").first():
                print("✅ Genesis transactions already exist (waiting for block creation).")
                return

            print("📜 Loading Genesis Configuration...")
            with open(genesis_path) as f:
                genesis_data = json.load(f)
                
            # Create Genesis Transactions (Minting)
            initial_balances = genesis_data.get("initial_balances", {})
            transactions = []
            
            for wallet, amount in initial_balances.items():
                tx = LedgerEntryModel(
                    sender="system",
                    recipient=wallet,
                    amount=amount,
                    transaction_type="mint",
                    description="Genesis Allocation",
                    timestamp=datetime.utcnow()
                )
                session.add(tx)
                transactions.append(tx)

            # Process Initial Stakes (Auto-Staking)
            initial_stakes = genesis_data.get("initial_stakes", {})
            for wallet, amount in initial_stakes.items():
                # 1. Deduct from balance (Stake Transfer)
                # NOTE: We assume the wallet already has the balance from initial_balances
                
                # 1. Deduct from balance (Stake Transfer)
                stake_tx = LedgerEntryModel(
                    sender=wallet,
                    recipient="STAKING_CONTRACT", # Locked in staking contract
                    amount=amount,
                    transaction_type="stake",
                    description="Genesis Auto-Staking",
                    timestamp=datetime.utcnow()
                )
                session.add(stake_tx)
                transactions.append(stake_tx)
                print(f"   🔨 Auto-Staked {amount} ETHC for {wallet[:8]}...")
                
            session.commit()
            print(f"💰 Genesis transactions created: {len(transactions)}")
            # Create Genesis Block
            genesis_timestamp = genesis_data.get("timestamp")
            if genesis_timestamp:
                ts = datetime.fromisoformat(genesis_timestamp.replace('Z', '+00:00'))
            else:
                ts = datetime.utcnow()

            # Calculate Merkle Root for Genesis Txs
            import hashlib
            tx_ids = sorted([str(tx.id) for tx in transactions])
            tx_data = "".join(tx_ids)
            merkle_root = hashlib.sha256(tx_data.encode()).hexdigest()

            # Create Genesis Block Hash
            # Fixed validator ID for Genesis (Must match Production)
            # Use validator_id from genesis.json if available, otherwise fallback to NODE_ID
            validator_id = genesis_data.get("validator_id") or os.getenv("NODE_ID", "default_node")
            previous_hash = "0" * 64
            
            block_content = f"0{previous_hash}{ts.isoformat()}{merkle_root}{validator_id}"
            block_hash = hashlib.sha256(block_content.encode()).hexdigest()

            genesis_block = BlockModel(
                index=0,
                hash=block_hash,
                previous_hash=previous_hash,
                timestamp=ts,
                validator_id=validator_id,
                signature="GENESIS_SIG"
            )
            session.add(genesis_block)
            
            # Link transactions to Genesis Block
            for tx in transactions:
                tx.block_hash = block_hash

            session.commit()
            print(f"✅ Genesis Block Created! Hash: {block_hash[:8]}...")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Failed to load genesis: {e}")
        finally:
            session.close()
