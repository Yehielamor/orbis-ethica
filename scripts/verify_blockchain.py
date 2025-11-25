import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.ledger import LocalBlockchain
from backend.memory.graph import MemoryGraph

def test_blockchain_integration():
    print("🧪 Starting Blockchain Verification...")
    
    # 1. Initialize Ledger
    ledger = LocalBlockchain()
    
    # 2. Verify Genesis Block
    genesis = ledger.get_latest_block()
    print(f"\n🔹 Checking Genesis Block...")
    print(f"   Hash: {genesis.hash}")
    print(f"   Data: {genesis.data}")
    
    if genesis.index == 0 and genesis.previous_hash == "0" * 64:
        print("   ✅ Genesis Block Valid")
    else:
        print("   ❌ Genesis Block Invalid")
        return

    # 3. Initialize MemoryGraph with Ledger
    memory = MemoryGraph(ledger=ledger)
    
    # 4. Add Nodes (Should create blocks)
    print("\n🔹 Adding Memory Nodes...")
    
    node1_id = memory.add_node("TEST_NODE", {"msg": "Hello Blockchain"}, "tester")
    block1 = ledger.get_latest_block()
    
    if block1.index == 1 and block1.data['node_id'] == node1_id:
        print(f"   ✅ Block #1 Created for Node {node1_id}")
    else:
        print(f"   ❌ Block #1 Failed")
        
    node2_id = memory.add_node("TEST_NODE_2", {"msg": "Another Node"}, "tester")
    block2 = ledger.get_latest_block()
    
    if block2.index == 2 and block2.data['node_id'] == node2_id:
        print(f"   ✅ Block #2 Created for Node {node2_id}")
    else:
        print(f"   ❌ Block #2 Failed")
        
    # 5. Verify Integrity
    print("\n🔹 Verifying Chain Integrity...")
    if ledger.verify_integrity():
        print("   ✅ Chain Integrity Verified")
    else:
        print("   ❌ Chain Integrity Failed")
        
    # 6. Test Tampering
    print("\n🔹 Testing Tamper Detection...")
    # Tamper with Block 1 data
    ledger.chain[1].data['msg'] = "TAMPERED DATA"
    
    if not ledger.verify_integrity():
        print("   ✅ Tampering Detected (Integrity Check Failed as expected)")
    else:
        print("   ❌ Tampering NOT Detected!")

if __name__ == "__main__":
    test_blockchain_integration()
