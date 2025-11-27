import requests
import time
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from backend.security.identity import NodeIdentity

API_URL = "http://localhost:6429"

def test_unsigned_request():
    print("\n⚔️  Test 1: Unsigned Request to /api/wallet/transfer")
    try:
        res = requests.post(f"{API_URL}/api/wallet/transfer", json={
            "recipient": "0x123",
            "amount": 100
        })
        if res.status_code == 401:
            print("✅ BLOCKED (401 Unauthorized) - As expected")
        else:
            print(f"❌ FAILED: Request accepted with status {res.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_invalid_signature():
    print("\n⚔️  Test 2: Invalid Signature")
    headers = {
        "X-Pubkey": "deadbeef",
        "X-Timestamp": str(int(time.time())),
        "X-Signature": "bad_signature"
    }
    res = requests.post(f"{API_URL}/api/wallet/transfer", json={"recipient": "0x123", "amount": 100}, headers=headers)
    if res.status_code == 401:
        print("✅ BLOCKED (401 Unauthorized) - As expected")
    else:
        print(f"❌ FAILED: Request accepted with status {res.status_code}")
        sys.exit(1)

def test_replay_attack():
    print("\n⚔️  Test 3: Replay Attack (Old Timestamp)")
    # 10 minutes ago
    old_time = str(int(time.time()) - 600)
    headers = {
        "X-Pubkey": "deadbeef",
        "X-Timestamp": old_time,
        "X-Signature": "valid_looking_but_old"
    }
    res = requests.post(f"{API_URL}/api/wallet/transfer", json={"recipient": "0x123", "amount": 100}, headers=headers)
    if res.status_code == 401:
        print("✅ BLOCKED (401 Unauthorized) - As expected")
    else:
        print(f"❌ FAILED: Request accepted with status {res.status_code}")
        sys.exit(1)

def test_encryption_enforcement():
    print("\n⚔️  Test 4: Encryption Enforcement (No Password)")
    try:
        # Try to generate a new identity without password
        # We use a random ID to ensure it tries to generate new
        NodeIdentity(node_id=f"test_no_pass_{int(time.time())}", key_dir="/tmp/test_keys", password=None)
        print("❌ FAILED: NodeIdentity generated key without password!")
        sys.exit(1)
    except ValueError as e:
        if "SECURITY ERROR" in str(e):
            print("✅ BLOCKED (ValueError) - As expected")
        else:
            print(f"⚠️  Blocked but with unexpected error: {e}")

if __name__ == "__main__":
    print("🛡️  Starting Penetration Test...")
    
    # Ensure server is running (check health)
    try:
        requests.get(f"{API_URL}/api/status")
    except:
        print("⚠️  Server not running. Please start docker-compose first.")
        # We can still test encryption enforcement locally
        
    test_unsigned_request()
    test_invalid_signature()
    test_replay_attack()
    test_encryption_enforcement()
    
    print("\n🎉 All Security Tests Passed!")
