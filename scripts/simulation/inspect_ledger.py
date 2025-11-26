import sys
import os
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

def inspect_ledger():
    print("🔍 Inspecting Ledger Database...")
    engine = create_engine("sqlite:///orbis_ethica.db")
    
    with engine.connect() as conn:
        # 1. List all transactions
        print("\n--- Transactions ---")
        result = conn.execute(text("SELECT id, sender, recipient, amount, transaction_type FROM ledger_entries"))
        txs = result.fetchall()
        for tx in txs:
            print(f"Tx {tx.id}: {tx.sender} -> {tx.recipient} | {tx.amount} {tx.transaction_type}")
            
        # 2. List all blocks
        print("\n--- Blocks ---")
        result = conn.execute(text("SELECT index, hash, validator_id FROM blocks"))
        blocks = result.fetchall()
        for b in blocks:
            print(f"Block #{b.index}: {b.validator_id} ({b.hash[:8]}...)")

if __name__ == "__main__":
    inspect_ledger()
