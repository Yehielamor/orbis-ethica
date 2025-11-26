import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.core.ledger import LocalBlockchain

def test_genesis_loading():
    print("📜 Testing Genesis Block Loading...")
    
    # Initialize Blockchain (should load genesis.json)
    ledger = LocalBlockchain()
    
    # 1. Verify Genesis Config Loaded
    if not ledger.genesis_config:
        print("❌ Failed to load genesis config")
        sys.exit(1)
        
    print("✅ Genesis config loaded")
    
    # 2. Verify Initial Balance
    genesis_wallet_balance = ledger.get_balance("genesis_wallet")
    expected_balance = 10_000_000.0
    
    if genesis_wallet_balance == expected_balance:
        print(f"✅ Genesis Wallet Balance Verified: {genesis_wallet_balance} ETHC")
    else:
        print(f"❌ Balance Mismatch: Expected {expected_balance}, Got {genesis_wallet_balance}")
        sys.exit(1)

    # 3. Verify Governance Param
    gov_wallet = ledger.genesis_config.get("governance_wallet")
    if gov_wallet == "GOVERNANCE_DAO_MULTI_SIG_V1":
        print(f"✅ Governance Wallet Verified: {gov_wallet}")
    else:
        print(f"❌ Governance Wallet Mismatch: {gov_wallet}")
        sys.exit(1)

if __name__ == "__main__":
    test_genesis_loading()
