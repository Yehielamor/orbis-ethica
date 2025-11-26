import sys
import os
import uuid
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.core.ledger import LocalBlockchain, TokenTransaction, TransactionType, StakingContract
from backend.security.identity import NodeIdentity

def test_staking():
    print("🔐 Testing Economic Layer (Staking & Slashing)...")
    
    # 1. Setup
    identity = NodeIdentity()
    ledger = LocalBlockchain(identity=identity)
    contract = StakingContract(ledger)
    my_address = identity.public_key_hex
    
    print(f"💵 Initial Balance: {ledger.get_balance(my_address)}")
    
    # 2. Test Staking (Deposit)
    stake_amount = 40_000.0
    print(f"\n🔒 Staking {stake_amount} ETHC...")
    
    stake_tx = TokenTransaction(
        id=str(uuid.uuid4()),
        type=TransactionType.STAKE,
        sender=my_address,
        receiver=StakingContract.STAKING_ADDRESS,
        amount=stake_amount,
        signature="sig"
    )
    ledger.add_block(data={"msg": "Stake"}, transactions=[stake_tx])
    
    # Verify State
    liquid = ledger.get_balance(my_address)
    staked = ledger.get_stake_balance(my_address)
    is_validator = contract.is_validator(my_address)
    
    print(f"   Liquid: {liquid}")
    print(f"   Staked: {staked}")
    print(f"   Is Validator? {is_validator}")
    
    if staked == 40_000.0 and is_validator:
        print("✅ Staking Successful!")
    else:
        print("❌ Staking Failed")
        sys.exit(1)

    # 3. Test Slashing (The Burn)
    slash_amount = 20_000.0
    print(f"\n🔥 Slashing {slash_amount} ETHC (Penalty)...")
    
    slash_tx = TokenTransaction(
        id=str(uuid.uuid4()),
        type=TransactionType.SLASH,
        sender=my_address,
        receiver="BURN_ADDRESS",
        amount=slash_amount,
        signature="authority_sig" # In real life, signed by other validators
    )
    ledger.add_block(data={"msg": "Slash"}, transactions=[slash_tx])
    
    # Verify State
    staked_after = ledger.get_stake_balance(my_address)
    print(f"   Staked after Slash: {staked_after}")
    
    if staked_after == 20_000.0:
        print("✅ Slashing Successful!")
    else:
        print(f"❌ Slashing Failed (Expected 20000, got {staked_after})")
        sys.exit(1)

    # 4. Test Unstaking (Withdraw)
    unstake_amount = 10_000.0
    print(f"\n🔓 Unstaking {unstake_amount} ETHC...")
    
    unstake_tx = TokenTransaction(
        id=str(uuid.uuid4()),
        type=TransactionType.UNSTAKE,
        sender=my_address,
        receiver=my_address, # Back to self
        amount=unstake_amount,
        signature="sig"
    )
    ledger.add_block(data={"msg": "Unstake"}, transactions=[unstake_tx])
    
    # Verify State
    final_liquid = ledger.get_balance(my_address)
    final_staked = ledger.get_stake_balance(my_address)
    
    print(f"   Final Liquid: {final_liquid}")
    print(f"   Final Staked: {final_staked}")
    
    if final_staked == 10_000.0 and final_liquid == 970_000.0: # 1M - 40k + 10k (20k burned)
        print("✅ Unstaking Successful!")
    else:
        print("❌ Unstaking Failed")
        sys.exit(1)

if __name__ == "__main__":
    test_staking()
