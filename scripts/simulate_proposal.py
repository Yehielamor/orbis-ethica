import asyncio
import json
import time
import httpx
import nacl.signing
import nacl.encoding
from datetime import datetime

# Configuration
API_URL = "http://localhost:6429/api/proposals/submit"

def generate_identity():
    """Generate a fresh keypair for testing."""
    signing_key = nacl.signing.SigningKey.generate()
    verify_key = signing_key.verify_key
    return signing_key, verify_key

def canonicalize(obj):
    """Canonicalize JSON for signing (Recursive Sort)."""
    if isinstance(obj, dict):
        return {k: canonicalize(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [canonicalize(i) for i in obj]
    return obj

def sign_request(method, path, body, signing_key):
    """Generate authentication headers."""
    timestamp = str(int(time.time()))
    
    # Canonicalize body
    sorted_body = canonicalize(body)
    body_str = json.dumps(sorted_body, separators=(',', ':')) # Compact JSON
    
    # Construct payload: METHOD:PATH:TIMESTAMP:BODY
    payload = f"{method.upper()}:{path}:{timestamp}:{body_str}"
    
    # Sign
    signed = signing_key.sign(payload.encode('utf-8'))
    signature_hex = signed.signature.hex()
    public_key_hex = signing_key.verify_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')
    
    return {
        "X-Pubkey": public_key_hex,
        "X-Timestamp": timestamp,
        "X-Signature": signature_hex,
        "Content-Type": "application/json"
    }

async def simulate_proposal():
    print("🚀 Starting End-to-End Simulation...")
    
    # 1. Generate Identity
    signing_key, verify_key = generate_identity()
    print(f"🔑 Generated Identity: {verify_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')[:16]}...")
    
    # 2. Prepare Proposal
    proposal_data = {
        "title": "End-to-End Test Proposal for Tokenomics",
        "description": "This is a test proposal to verify the full system flow including tokenomics enforcement and ledger recording.",
        "category": "ROUTINE",
        "domain": "TECHNOLOGY",
        "submitter_id": "Simulation_Script",
        "affected_parties": ["Developers", "System"],
        "context": {"test_run": True}
    }
    
    # 3. Sign Request
    headers = sign_request("POST", "/api/proposals/submit", proposal_data, signing_key)
    print("✍️  Signed Request")
    
    # 4. Submit via SSE
    print("📡 Submitting to API (SSE Stream)...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", API_URL, json=proposal_data, headers=headers) as response:
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                content = await response.aread()
                print(content.decode())
                return

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    event_type = data.get("type", "unknown")
                    print(f"   🔹 Event: {event_type}")
                    
                    if event_type == "final_decision":
                        print("\n✅ Final Decision Received!")
                        print(f"   Outcome: {data.get('outcome')}")
                        print(f"   Block Hash: {data.get('decision', {}).get('block_hash', 'N/A')}")
                        break
                    elif event_type == "error":
                        print(f"❌ Error Event: {data.get('message')}")
                        break

if __name__ == "__main__":
    asyncio.run(simulate_proposal())
