import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path so we can import models
# Resolve project root relative to this script (scripts/inspect_db.py -> project_root)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.core.models.sql_models import LedgerEntryModel, BlockModel

def inspect_db():
    print("🔍 Inspecting Database...")
    
    # Resolve DB path relative to script
    # project_root is already defined above
    db_path = os.path.join(project_root, "backend", "orbis_ethica.db")
    db_url = f"sqlite:///{db_path}"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Check Total and Pending Counts
        total = session.query(LedgerEntryModel).count()
        pending = session.query(LedgerEntryModel).filter(LedgerEntryModel.block_hash == None).count()
        print(f"📊 Total Transactions: {total}")
        print(f"⏳ Pending Transactions: {pending}")
        
        # 2. detailed inspection of last 5 transactions
        print("\n🕵️ Last 10 Transactions:")
        txs = session.query(LedgerEntryModel).order_by(LedgerEntryModel.id.desc()).limit(10).all()
        
        for tx in txs:
            print(f"   🔹 ID: {tx.id} | Type: {tx.transaction_type} | Amt: {tx.amount}")
            print(f"      Sender: {tx.sender[:10]}... -> Recipient: {tx.recipient[:10]}...")
            print(f"      Block Hash: {tx.block_hash} (Is None? {tx.block_hash is None})")
            print(f"      Time: {tx.timestamp}")
            print("      --------------------------------------------------")
            
        # 3. Check if block exists for the non-null hashes
        if txs and txs[0].block_hash:
            blk = session.query(BlockModel).filter_by(hash=txs[0].block_hash).first()
            if blk:
                print(f"\n🧱 Block {txs[0].block_hash[:8]} found! Index: {blk.index}")
            else:
                print(f"\n❌ Block {txs[0].block_hash[:8]} NOT FOUND in blocks table!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    inspect_db()
