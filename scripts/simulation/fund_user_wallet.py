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

async def fund_user_wallet():
    print("💰 Initiating Genesis Fund Transfer...")
    
    # 1. Initialize DB
    init_db()
    ledger = Ledger()
    session = DatabaseManager().get_session()
    
    try:
        # 2. Load User Identity (Recipient)
        password = os.getenv("KEY_PASSWORD")
        if not password:
            print("❌ KEY_PASSWORD env var missing!")
            return

        # We need to find the active node ID. 
        # In app.py it uses NODE_ID env var or defaults.
        # Let's try to load the default identity or the one specified in env.
        node_id = os.getenv("NODE_ID", "default_node")
        
        # Try to load identity to get public key
        try:
            user_identity = NodeIdentity(node_id=node_id, password=password)
            recipient_address = user_identity.public_key_hex
            print(f"👤 Recipient (User Node): {node_id}")
            print(f"📬 Address: {recipient_address}")
        except Exception as e:
            print(f"❌ Could not load user identity: {e}")
            return

        # 3. Create Transfer Transaction
        # We are simulating a transfer from "genesis_wallet" (system) to the user.
        # In a real system, we'd need the private key of genesis_wallet.
        # For this phase, we will manually insert the transaction as a "Grant".
        
        amount = 100000.0 # Grant 100k ETHC
        
        transfer_tx = LedgerEntryModel(
            sender="genesis_wallet",
            recipient=recipient_address,
            amount=amount,
            transaction_type="transfer",
            description="Genesis Grant to Operator",
            timestamp=datetime.utcnow()
        )
        
        session.add(transfer_tx)
        session.commit()
        print(f"✅ Created Transaction: {amount} ETHC -> {recipient_address}")
        
        # 4. Mine a new block to confirm it
        # We need a validator to mine it. We can use the user's identity itself for now.
        print("⛏️  Mining confirmation block...")
        block = ledger.create_block(validator_id=user_identity.node_id, private_key=user_identity)
        
        if block:
            print(f"✨ Block #{block.index} Mined! Funds are now available.")
        else:
            print("⚠️  Transaction added to pool but block creation failed (maybe no txs pending?)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(fund_user_wallet())
