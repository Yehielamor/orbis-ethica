import sys
import os
import json
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.core.ledger import LocalBlockchain, TokenTransaction, TransactionType

def run_test():
    print("🧪 Testing Integrity & Fairness Logic...")
    
    # 1. Setup Mock Genesis Config
    mock_genesis = {
        "initial_balances": {
            "genesis_wallet": 1000000.0,
            "founder_vesting_contract": 8000000.0,
            "ethical_allocation_pool": 1000000.0
        },
        "params": {
            "vesting_schedule": {
                "duration_years": 5,
                "cliff_months": 12,
                "release_per_year": 0.20
            },
            "junior_validator_program": {
                "grant_amount": 32000.0
            }
        },
        "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat() # Genesis was yesterday
    }
    
    # Mock loading config
    LocalBlockchain._load_genesis_config = lambda self: mock_genesis
    
    ledger = LocalBlockchain()
    
    # 2. Test Vesting Lock (Should Fail - Cliff not passed)
    print("\n🔒 Testing Vesting Lock (Cliff Period)...")
    tx_vesting = TokenTransaction(
        id="tx_vesting_1",
        type=TransactionType.TRANSFER,
        sender="founder_vesting_contract",
        receiver="founder_personal_wallet",
        amount=1000.0,
        signature="sig"
    )
    
    if ledger._validate_transaction(tx_vesting):
        print("❌ FAILURE: Vesting transaction allowed during cliff!")
        sys.exit(1)
    else:
        print("✅ SUCCESS: Vesting transaction blocked correctly (Cliff).")
        
    # 3. Test Ethical Pool Limits
    print("\n🛡️ Testing Ethical Pool Limits...")
    # Case A: Valid Grant
    tx_grant_ok = TokenTransaction(
        id="tx_grant_1",
        type=TransactionType.TRANSFER,
        sender="ethical_allocation_pool",
        receiver="junior_validator_1",
        amount=32000.0,
        signature="sig"
    )
    
    if ledger._validate_transaction(tx_grant_ok):
        print("✅ SUCCESS: Valid grant allowed.")
    else:
        print("❌ FAILURE: Valid grant blocked!")
        sys.exit(1)
        
    # Case B: Excessive Grant
    tx_grant_bad = TokenTransaction(
        id="tx_grant_2",
        type=TransactionType.TRANSFER,
        sender="ethical_allocation_pool",
        receiver="junior_validator_2",
        amount=50000.0, # Limit is 32000
        signature="sig"
    )
    
    if ledger._validate_transaction(tx_grant_bad):
        print("❌ FAILURE: Excessive grant allowed!")
        sys.exit(1)
    else:
        print("✅ SUCCESS: Excessive grant blocked correctly.")

    print("\n✨ All Integrity Tests Passed!")

if __name__ == "__main__":
    run_test()
