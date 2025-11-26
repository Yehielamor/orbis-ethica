import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.core.database import init_db, DatabaseManager
from backend.core.ledger import Ledger
from backend.security.identity import NodeIdentity

async def test_block_creation():
    print("🚀 Starting Block Creation Test...")
    
    # 1. Initialize DB
    init_db()
    ledger = Ledger()
    
    # 2. Setup Identity
    identity = NodeIdentity(node_id="test_validator")
    print(f"🔑 Validator: {identity.node_id}")
    
    # 3. Create Transactions
    print("💰 Creating transactions...")
    ledger.record_transaction("alice", "bob", 10.0, "transfer", description="Test Tx 1")
    ledger.record_transaction("bob", "charlie", 5.0, "transfer", description="Test Tx 2")
    
    # 4. Create Block
    print("🧱 Creating block...")
    block = ledger.create_block(validator_id=identity.node_id, private_key=identity)
    
    if block:
        print(f"✅ Block Created: Index={block.index}, Hash={block.hash}")
    else:
        print("❌ Block creation failed (or no txs)")
        
    # 5. Verify in DB
    session = DatabaseManager().get_session()
    from backend.core.models.sql_models import BlockModel, LedgerEntryModel
    
    db_block = session.query(BlockModel).filter_by(hash=block.hash).first()
    if db_block:
        print(f"🔍 Verified in DB: Block #{db_block.index} has {len(db_block.transactions)} transactions")
        for tx in db_block.transactions:
            print(f"   - Tx {tx.id}: {tx.sender} -> {tx.recipient} ({tx.amount})")
    else:
        print("❌ Block not found in DB!")
        
    session.close()

if __name__ == "__main__":
    asyncio.run(test_block_creation())
