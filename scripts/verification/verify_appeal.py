import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.core.ledger import LocalBlockchain, TokenTransaction, TransactionType

def test_appeal_and_rewards():
    print("⚖️  Testing Appeal Mechanism & Incentives...")
    
    ledger = LocalBlockchain()
    
    victim_address = "victim_wallet_123"
    gov_address = "GOVERNANCE_DAO_MULTI_SIG_V1"
    hacker_address = "hacker_wallet_666"
    miner_address = "miner_node_001"
    
    # 1. Attempt Unauthorized Appeal
    print("\n1️⃣  Testing Unauthorized Appeal...")
    fake_appeal = TokenTransaction(
        id="tx_fake_appeal",
        type=TransactionType.APPEAL,
        sender=hacker_address,
        receiver=victim_address,
        amount=5000.0,
        signature="fake_sig"
    )
    
    # Try to add block with fake appeal
    # We use _validate_transaction directly to test the logic, 
    # as add_block filters out invalid txs silently (printing error).
    is_valid = ledger._validate_transaction(fake_appeal)
    if not is_valid:
        print("✅ Unauthorized Appeal correctly rejected.")
    else:
        print("❌ SECURITY FAILURE: Unauthorized Appeal accepted!")
        sys.exit(1)

    # 2. Attempt Authorized Appeal
    print("\n2️⃣  Testing Authorized Appeal (Governance)...")
    real_appeal = TokenTransaction(
        id="tx_real_appeal",
        type=TransactionType.APPEAL,
        sender=gov_address,
        receiver=victim_address,
        amount=5000.0,
        signature="gov_multi_sig_valid"
    )
    
    is_valid = ledger._validate_transaction(real_appeal)
    if is_valid:
        print("✅ Authorized Appeal accepted.")
    else:
        print("❌ FAILURE: Authorized Appeal rejected!")
        sys.exit(1)
        
    # 3. Execute Appeal & Check Balance + Block Reward
    print("\n3️⃣  Executing Appeal & Checking Rewards...")
    
    # Create a block with the appeal
    # We need to mock the signer_id for the block to test block reward
    # Since add_block uses self.identity, we can't easily set signer_id unless we mock identity.
    # Instead, we'll check the logic of _apply_block_reward directly or inspect the block created.
    
    # Let's just run add_block. If we don't have identity, signer is None.
    # But we want to test reward.
    # We can manually call _apply_block_reward for testing purposes or set a mock identity.
    
    # Let's just check the Appeal execution first.
    ledger.add_block(data={"msg": "Appeal Block"}, transactions=[real_appeal])
    
    victim_balance = ledger.get_balance(victim_address)
    if victim_balance == 5000.0:
        print(f"✅ Victim Balance Restored: {victim_balance} ETHC")
    else:
        print(f"❌ Balance Restoration Failed. Got {victim_balance}")
        sys.exit(1)

    # 4. Test Block Reward Logic
    print("\n4️⃣  Testing Block Reward...")
    ledger._apply_block_reward(miner_address)
    miner_balance = ledger.get_balance(miner_address)
    if miner_balance == 5.0:
        print(f"✅ Block Reward Minted: {miner_balance} ETHC")
    else:
        print(f"❌ Block Reward Failed. Got {miner_balance}")
        sys.exit(1)

if __name__ == "__main__":
    test_appeal_and_rewards()
