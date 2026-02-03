
import asyncio
import os
import sys
# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.ledger import Ledger
from backend.core.models.sql_models import LedgerEntryModel

def simulate_payment_flow():
    print("🚀 Starting Payment Flow Simulation...")
    
    # 1. Initialize Ledger (uses default orbis_ethica.db)
    ledger = Ledger()
    
    # 2. Get Genesis Wallet
    # In genesis.json we saw: "0xde8037e96eadf0ae71b5b2b78b8754484afce931d78a1a19b63700f3a76b85eb"
    genesis_wallet = "0xde8037e96eadf0ae71b5b2b78b8754484afce931d78a1a19b63700f3a76b85eb"
    
    initial_balance = ledger.get_balance(genesis_wallet)
    print(f"💰 Initial Balance for Genesis Wallet: {initial_balance} ETHC")
    
    if initial_balance <= 0:
        print("⚠️ Warning: Genesis wallet has 0 balance. Did you load genesis.json?")
        # Try loading genesis manually just in case
        ledger.load_genesis("genesis.json")
        initial_balance = ledger.get_balance(genesis_wallet)
        print(f"💰 Balance after reload: {initial_balance} ETHC")

    # 3. Simulate User Payment (0.1 ETHC)
    cost = 0.1
    print(f"\n💸 Attempting to pay {cost} ETHC for query...")
    
    success = ledger.record_transaction(
        sender=genesis_wallet,
        recipient="system_treasury",
        amount=cost,
        tx_type="transfer",
        description="Simulation Fee Payment"
    )
    
    if success:
        print("✅ Payment Succeeded!")
    else:
        print("❌ Payment Failed!")
        return

    # 4. Verify New Balance
    new_balance = ledger.get_balance(genesis_wallet)
    print(f"💰 New Balance: {new_balance} ETHC")
    print(f"📉 Cost deducted: {initial_balance - new_balance} (Expected: {cost})")
    
    # 5. Check Pending Transactions (Mempool)
    session = ledger.db_manager.get_session()
    pending = session.query(LedgerEntryModel).filter(LedgerEntryModel.block_hash == None).all()
    print(f"\n⏳ Pending Transactions (Mempool): {len(pending)}")
    for tx in pending:
        print(f"   - {tx.sender[:8]}... -> {tx.recipient} : {tx.amount}")
    session.close()

    print("\n✅ Simulation Complete. To mine these, run 'scripts/genesis_miner.py'")

if __name__ == "__main__":
    simulate_payment_flow()
