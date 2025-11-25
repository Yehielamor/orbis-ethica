import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.security.identity import NodeIdentity

def test_identity():
    print("🔐 Testing Node Identity...")
    
    # 1. Initialize Identity
    identity = NodeIdentity(node_id="test_node_01", key_dir=".test_keys")
    print(f"✅ Identity Initialized: {identity.node_id}")
    print(f"   Public Key: {identity.public_key_hex}")
    
    # 2. Sign a Message
    message = {
        "type": "GOSSIP_BLOCK",
        "sender_id": identity.node_id,
        "payload": {"block_index": 1, "hash": "abc12345"},
        "timestamp": 1234567890.0
    }
    
    signature = identity.sign(message)
    print(f"✅ Message Signed: {signature[:16]}...")
    
    # 3. Verify Signature (Valid)
    is_valid = NodeIdentity.verify(message, signature, identity.public_key_hex)
    if is_valid:
        print("✅ Signature Verification: PASSED")
    else:
        print("❌ Signature Verification: FAILED")
        
    # 4. Verify Signature (Tampered)
    tampered_message = message.copy()
    tampered_message["payload"]["hash"] = "deadbeef" # Tamper!
    
    is_valid_tampered = NodeIdentity.verify(tampered_message, signature, identity.public_key_hex)
    if not is_valid_tampered:
        print("✅ Tamper Detection: PASSED (Invalid signature rejected)")
    else:
        print("❌ Tamper Detection: FAILED (Tampered message accepted!)")

    # Cleanup
    import shutil
    if os.path.exists(".test_keys"):
        shutil.rmtree(".test_keys")
        print("🧹 Cleanup complete")

if __name__ == "__main__":
    test_identity()
