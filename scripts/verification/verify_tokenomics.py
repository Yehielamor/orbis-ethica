import sys
import os
import uuid
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.core.ledger import LocalBlockchain, TokenTransaction, TransactionType
from backend.security.identity import NodeIdentity

def test_tokenomics():
    print("💰 Testing Economic Layer (Tokenomics)...")
    
    # 1. Setup Identity & Blockchain
    identity = NodeIdentity()
    print(f"🔑 Node Identity: {identity.public_key_hex[:16]}...")
    
    ledger = LocalBlockchain(identity=identity)
    
    # 2. Verify Genesis Mint
    my_address = identity.public_key_hex
    balance = ledger.get_balance(my_address)
    print(f"💵 Genesis Balance: {balance} ETHC")
    
    if balance != 1_000_000.0:
        print("❌ Genesis Mint Failed!")
        sys.exit(1)
        
    # 3. Test Transfer
    receiver_address = "wallet_alice"
    amount = 500.0
    
    print(f"\n💸 Sending {amount} ETHC to {receiver_address}...")
    
    tx = TokenTransaction(
        id=str(uuid.uuid4()),
        type=TransactionType.TRANSFER,
        sender=my_address,
        receiver=receiver_address,
        amount=amount,
        signature="sig_placeholder" # In real app, identity.sign(tx)
    )
    
    # Add block with transaction
    ledger.add_block(data={"msg": "Transfer Block"}, transactions=[tx])
    
    # 4. Verify Balances
    new_balance = ledger.get_balance(my_address)
    alice_balance = ledger.get_balance(receiver_address)
    
    print(f"   My New Balance: {new_balance}")
    print(f"   Alice Balance: {alice_balance}")
    
    if new_balance == 999_500.0 and alice_balance == 500.0:
        print("✅ Transfer Successful!")
    else:
        print("❌ Transfer Failed (Balances incorrect)")
        sys.exit(1)

    # 5. Test Insufficient Funds
    print(f"\n🚫 Testing Insufficient Funds (Sending 2,000,000 ETHC)...")
    bad_tx = TokenTransaction(
        id=str(uuid.uuid4()),
        type=TransactionType.TRANSFER,
        sender=my_address,
        receiver="wallet_bob",
        amount=2_000_000.0,
        signature="sig_placeholder"
    )
    
    ledger.add_block(data={"msg": "Bad Block"}, transactions=[bad_tx])
    
    # Verify balance didn't change
    final_balance = ledger.get_balance(my_address)
    if final_balance == 999_500.0:
        print("✅ Invalid Transaction Rejected (Balance unchanged)")
    else:
        print(f"❌ Failed: Balance changed to {final_balance}")
        sys.exit(1)

if __name__ == "__main__":
    test_tokenomics()
