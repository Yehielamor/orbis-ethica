"""
Ledger Module
Manages economic transactions and token balances using SQLite.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from .database import DatabaseManager
from .models.sql_models import LedgerEntryModel, SQLEntity as NodeModel
from enum import Enum

class TransactionType(str, Enum):
    TRANSFER = "transfer"
    STAKE = "stake"
    UNSTAKE = "unstake"
    REWARD = "reward"
    PENALTY = "penalty"
    MINT = "mint"

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
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()

    def get_total_supply(self) -> float:
        """Calculate total circulating supply."""
        session = self.db_manager.get_session()
        try:
            # Sum all mints and rewards
            mints = session.query(LedgerEntryModel).filter(
                LedgerEntryModel.transaction_type.in_(["mint", "reward"])
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
        if tx_type in ["mint", "reward"]:
            current_supply = self.get_total_supply()
            if current_supply + amount > self.MAX_SUPPLY:
                print(f"❌ Minting rejected: Cap exceeded. Supply: {current_supply}, Requested: {amount}, Max: {self.MAX_SUPPLY}")
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
        """Mint new tokens as a reward."""
        return self.record_transaction(
            sender="system_mint",
            recipient=recipient,
            amount=amount,
            tx_type="reward",
            description=reason
        )

        """
        Slash a node's stake (penalty). 
        Moves tokens to 'slash_escrow_vault' for the Purgatory Period (Appeal Window).
        """
        return self.record_transaction(
            sender=target,
            recipient="slash_escrow_vault", # Move to Escrow (Purgatory)
            amount=amount,
            tx_type="slash_escrow", 
            description=f"{reason} (Held in Escrow for Appeal)"
        )

    def release_from_escrow(self, amount: float, destination: str = "public_sale_treasury") -> bool:
        """
        Release tokens from Escrow after appeal period expires.
        Default destination is Public Sale Treasury (Recycling).
        """
        return self.record_transaction(
            sender="slash_escrow_vault",
            recipient=destination,
            amount=amount,
            tx_type="escrow_release",
            description="Escrow period expired. Tokens recycled."
        )
        
    def get_transaction_history(self, address: str = None) -> List[Dict]:
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
            
    def create_block(self, validator_id: str, private_key: Any) -> Optional[Any]:
        """
        Create a new block from pending transactions.
        """
        session = self.db_manager.get_session()
        try:
            # 1. Get pending transactions (those without a block_hash)
            pending_txs = session.query(LedgerEntryModel).filter(LedgerEntryModel.block_hash == None).all()
            
            if not pending_txs:
                print("⚠️ No pending transactions to block.")
                return None
                
            # 2. Get last block for linking
            from .models.sql_models import BlockModel
            last_block = session.query(BlockModel).order_by(BlockModel.index.desc()).first()
            
            new_index = (last_block.index + 1) if last_block else 0
            previous_hash = last_block.hash if last_block else "0" * 64
            
            # 3. Calculate Merkle Root (Simplified: Hash of all tx IDs)
            import hashlib
            tx_ids = sorted([str(tx.id) for tx in pending_txs])
            tx_data = "".join(tx_ids)
            merkle_root = hashlib.sha256(tx_data.encode()).hexdigest()
            
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
                signature=signature
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
                
            return BlockObj(index=new_index, hash=block_hash)
            
        except Exception as e:
            session.rollback()
            print(f"❌ Block creation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            session.close()

    # Compatibility methods for MemoryGraph anchoring
    def add_block(self, block_data: Dict[str, Any]):
        """
        Mock method kept for MemoryGraph compatibility if it calls this directly.
        In the new flow, MemoryGraph should just read the ledger state.
        """
        # For now, return a dummy to keep MemoryGraph happy until we refactor it
        class DummyBlock(BaseModel):
            index: int
            hash: str
        return DummyBlock(index=999, hash="legacy_add_block_call")

    def validate_block(self, block_data: Dict[str, Any]) -> bool:
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

    def add_block_from_peer(self, block_data: Dict[str, Any]) -> bool:
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
            session.commit()
            print(f"🧱 Added block #{block_data['index']} from peer.")
            return True
        except Exception as e:
            session.rollback()
            print(f"❌ Failed to add peer block: {e}")
            return False
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
            
            if last_block:
                return BlockObj(index=last_block.index, hash=last_block.hash)
            else:
                return BlockObj(index=0, hash="genesis_pending")
        finally:
            session.close()

    def load_genesis(self, genesis_path: str = "genesis.json"):
        """
        Load genesis configuration and initialize the chain if empty.
        """
        import json
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
            with open(genesis_path, 'r') as f:
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
                # In our ledger model, staking is often just a state change or a transfer to a stake address.
                # Let's assume it's a transfer to "system_stake" or similar, or just a "stake" transaction type.
                # Based on slash_stake, we have record_transaction.
                # But here we are manually creating LedgerEntryModel to batch them.
                
                stake_tx = LedgerEntryModel(
                    sender=wallet,
                    recipient="system_stake", # Locked in staking contract
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
            print("⚠️ Waiting for user message to create Genesis Block...")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Failed to load genesis: {e}")
        finally:
            session.close()
