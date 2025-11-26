import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.core.database import init_db, DatabaseManager
from backend.core.ledger import Ledger
from backend.security.identity import NodeIdentity
from backend.core.models.sql_models import LedgerEntryModel

async def launch_genesis():
    print("🚀 Orbis Ethica Genesis Launch Sequence Initiated...")
    
    # 1. Initialize DB
    init_db()
    ledger = Ledger()
    session = DatabaseManager().get_session()
    
    try:
        # 2. Setup Genesis Identity
        # We use a specific identity for the genesis block creator
        password = os.getenv("KEY_PASSWORD")
        if not password:
            print("❌ KEY_PASSWORD env var missing!")
            return

        identity = NodeIdentity(node_id="genesis_validator", password=password)
        print(f"🔑 Genesis Creator: {identity.node_id}")
        
        # 3. Add Genesis Message
        message = "Orbis Ethica Genesis: Teaching silicon to care. Hello World."
        print(f"📜 Embedding Message: '{message}'")
        
        genesis_tx = LedgerEntryModel(
            sender="system",
            recipient="genesis_marker",
            amount=0.0,
            transaction_type="message",
            description=message,
            timestamp=datetime.utcnow()
        )
        session.add(genesis_tx)
        session.commit()
        print("✅ Genesis Message Transaction Recorded.")
        
        # 4. Create Genesis Block
        print("🧱 Mining Genesis Block...")
        block = ledger.create_block(validator_id=identity.node_id, private_key=identity)
        
        if block:
            print("\n" + "="*50)
            print(f"✨ GENESIS BLOCK CREATED SUCCESSFULLY ✨")
            print("="*50)
            print(f"Index:       {block.index}")
            print(f"Hash:        {block.hash}")
            print(f"Message:     {message}")
            print("="*50 + "\n")
        else:
            print("❌ Genesis Block Creation Failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(launch_genesis())
