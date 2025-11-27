from backend.core.ledger import Ledger
from backend.core.database import DatabaseManager

def inspect():
    db = DatabaseManager()
    ledger = Ledger(db)
    
    supply = ledger.get_total_supply()
    print(f"💰 Current Total Supply: {supply:,.2f} ETHC")
    print(f"🛑 Max Supply: {ledger.MAX_SUPPLY:,.2f} ETHC")
    
    if supply >= ledger.MAX_SUPPLY:
        print("⚠️  CAP REACHED! No more minting possible.")
    else:
        print(f"✅ Remaining Mintable: {ledger.MAX_SUPPLY - supply:,.2f} ETHC")
        
    print("\n📊 Wallet Balances:")
    wallets = [
        "d3be456fb17c12dbcf2b2d3a1b34fae6c904e3d5ac91469719ff53b92ad055de",
        "founder_vesting_contract", 
        "public_sale_treasury", 
        "ethical_allocation_pool",
        "mining_reward_pool",
        "slash_escrow_vault",
        "system_stake"
    ]
    for w in wallets:
        bal = ledger.get_balance(w)
        print(f"   - {w[:10]}...: {bal:,.2f} ETHC")

if __name__ == "__main__":
    inspect()
