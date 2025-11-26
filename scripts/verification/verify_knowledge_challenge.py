import requests
import sys

BASE_URL = "http://localhost:6429/api"

def test_challenge_flow():
    print("🛡️ Testing Knowledge Gateway Challenge-Response...")
    
    source_id = "WHO_Secure_Feed"
    content = "COVID-19 is airborne."
    
    # 1. Request Challenge
    print(f"\n1. Requesting challenge for {source_id}...")
    try:
        resp = requests.post(f"{BASE_URL}/knowledge/challenge", json={"source_id": source_id})
        resp.raise_for_status()
        nonce = resp.json()["nonce"]
        print(f"✅ Received Nonce: {nonce}")
    except Exception as e:
        print(f"❌ Failed to get challenge: {e}")
        sys.exit(1)

    # 2. Sign Challenge (Mock Wallet)
    print(f"\n2. Signing nonce...")
    try:
        resp = requests.post(f"{BASE_URL}/knowledge/sign", json={"content": nonce})
        resp.raise_for_status()
        signature = resp.json()["signature"]
        print(f"✅ Generated Signature: {signature}")
    except Exception as e:
        print(f"❌ Failed to sign: {e}")
        sys.exit(1)

    # 3. Submit Knowledge with Proof
    print(f"\n3. Submitting knowledge...")
    payload = {
        "content": content,
        "source_id": source_id,
        "signature": signature
    }
    try:
        resp = requests.post(f"{BASE_URL}/knowledge/ingest", json=payload)
        resp.raise_for_status()
        result = resp.json()
        print(f"✅ Knowledge Ingested! ID: {result['id']}")
        print(f"   Purity Score: {result['purity_score']}")
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Server Response: {e.response.text}")
        sys.exit(1)

    # 4. Test Replay Attack (Reuse same nonce/signature)
    print(f"\n4. Testing Replay Attack (should fail)...")
    try:
        resp = requests.post(f"{BASE_URL}/knowledge/ingest", json=payload)
        if resp.status_code == 400 or resp.status_code == 403: # Expecting error
            print(f"✅ Replay Attack Blocked! (Status: {resp.status_code})")
        else:
            print(f"❌ Replay Attack SUCCEEDED (This is bad): {resp.status_code}")
    except Exception as e:
        print(f"✅ Replay Attack Blocked (Exception): {e}")

if __name__ == "__main__":
    test_challenge_flow()
