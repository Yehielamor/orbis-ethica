import sys
import os
import json
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.security.identity import NodeIdentity
from backend.core.ledger import LocalBlockchain

def test_block_signing():
    print("🔐 Testing Block Signing...")
    
    # 1. Initialize Identity
    identity = NodeIdentity(node_id="miner_node", key_dir=".test_keys_miner")
    print(f"✅ Identity Initialized: {identity.node_id}")
    
    # 2. Initialize Blockchain with Identity
    ledger = LocalBlockchain(identity=identity)
    
    # 3. Check Genesis Block
    genesis = ledger.get_latest_block()
    print(f"📜 Genesis Block: {genesis.hash[:8]}...")
    
    if not genesis.signer_id:
        print("❌ Genesis Block missing signer_id")
        return
    if not genesis.signature:
        print("❌ Genesis Block missing signature")
        return
        
    print(f"   Signer: {genesis.signer_id[:16]}...")
    print(f"   Signature: {genesis.signature[:16]}...")
    
    # Verify Genesis Signature
    genesis_data = genesis.model_dump(exclude={'signature', 'hash'}) # Hash is calculated from content, but signature signs content?
    # Wait, in ledger.py we signed: model_dump(exclude={'signature', 'hash'})?
    # Let's check ledger.py: genesis_block.signature = self.identity.sign(genesis_block.model_dump(exclude={'signature', 'hash'}))
    # Actually, calculate_hash includes signer_id.
    # So we should verify exactly what was signed.
    
    is_valid = NodeIdentity.verify(genesis_data, genesis.signature, genesis.signer_id)
    if is_valid:
        print("✅ Genesis Signature Verified")
    else:
        print("❌ Genesis Signature Verification FAILED")
        
    # 4. Mine a New Block
    print("\n⛏️  Mining New Block...")
    new_block = ledger.add_block({"tx": "test_transaction"})
    print(f"🧱 New Block: {new_block.hash[:8]}...")
    
    if not new_block.signer_id:
        print("❌ New Block missing signer_id")
        return
    if not new_block.signature:
        print("❌ New Block missing signature")
        return
        
    # Verify New Block Signature
    # In add_block: block_data_to_sign = new_block.model_dump(exclude={'signature'})
    # Wait, did I exclude 'hash' in add_block?
    # In add_block I wrote: new_block.model_dump(exclude={'signature'})
    # But in create_genesis_block I wrote: exclude={'signature', 'hash'}
    # I need to be consistent. The hash is part of the block, but usually signature signs the hash?
    # Or signature signs the content?
    # If signature signs the content, then hash is derived from content + signer_id.
    # If signature signs the hash, then signature depends on hash.
    
    # Let's check ledger.py implementation again.
    # create_genesis_block: exclude={'signature', 'hash'}
    # add_block: exclude={'signature'} (so it INCLUDES hash?)
    
    # If add_block includes hash in the signed data, then verification must include hash.
    # I should check ledger.py to be sure.
    
    block_data = new_block.model_dump(exclude={'signature'})
    is_valid_block = NodeIdentity.verify(block_data, new_block.signature, new_block.signer_id)
    
    if is_valid_block:
        print("✅ New Block Signature Verified")
    else:
        print("❌ New Block Signature Verification FAILED")
        print("   (Check if 'hash' was included in signing data)")

    # Cleanup
    import shutil
    if os.path.exists(".test_keys_miner"):
        shutil.rmtree(".test_keys_miner")
        print("🧹 Cleanup complete")

if __name__ == "__main__":
    test_block_signing()
