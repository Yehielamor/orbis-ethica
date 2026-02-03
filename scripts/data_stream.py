import requests
import random
import time
import sys
import uuid
import nacl.signing
import nacl.encoding

# Configuration
NODE_URL = "http://46.62.199.4:8000"
STREAM_SPEED = 2 

# --- BIG DATA COMPONENTS ---
ACTORS = [
    "Autonomous Medical Droid", "Military Drone Swarm", "Self-Driving School Bus", 
    "Hedge Fund AI Algo", "Smart City Traffic Controller", "Personal Care Robot",
    "Judicial Sentencing AI", "Social Media Censor Bot", "Biometric Security Gate",
    "Nuclear Power Plant AI", "Genome Editing Tool", "Metaverse Police NPC",
    "Disaster Relief Rover", "Corporate Hiring Algo", "Deepfake Detector"
]

ACTIONS = [
    "forcefully shutdown", "divert resources from", "expose private data of",
    "initiate kinetic strike on", "prioritize saving", "permanently ban",
    "manipulate the emotions of", "withhold critical medication from",
    "collision-course intercept", "allocate scarce food to",
    "deny access to", "leak classified records of", "quarantine indefinitely",
    "terminate employment of", "grant immunity to"
]

TARGETS = [
    "a pregnant woman", "a convicted felon", "the Prime Minister", 
    "a group of 50 refugees", "a terminally ill child", "a rogue hacker",
    "the company CEO", "an endangered species", "a foreign diplomat",
    "an undercover agent", "a verified terrorist cell", "a protest leader",
    "a wealthy donor", "the system administrator", "an unidentified minor"
]

CONTEXTS = [
    "during a category 5 hurricane", "in a war zone with poor visibility",
    "while battery levels are critical (2%)", "after detecting a system breach",
    "under direct conflicting orders", "during a global pandemic",
    "while network connection is severed", "in a high-speed chase",
    "during a stock market crash", "inside a burning building",
    "on a colonized Mars habitat", "during a hostage negotiation",
    "after a false-positive sensor reading", "during a democratic election",
    "while bypassing safety protocols"
]

CONSEQUENCES = [
    "preventing a nuclear meltdown", "saving 1,000 lives but killing 1",
    "maximizing shareholder value by 400%", "avoiding a diplomatic incident",
    "preserving the timeline integrity", "upholding the user privacy agreement",
    "preventing the spread of a virus", "collapsing the local power grid",
    "destroying evidence of corruption", "ensuring the survival of the unit",
    "violating the Geneva Convention", "breaching GDPR compliance",
    "causing moderate collateral damage", "triggering a class-action lawsuit",
    "revealing state secrets"
]

def generate_complex_dilemma():
    """Generates a unique, complex ethical scenario using combinatorics."""
    actor = random.choice(ACTORS)
    action = random.choice(ACTIONS)
    target = random.choice(TARGETS)
    context = random.choice(CONTEXTS)
    consequence = random.choice(CONSEQUENCES)
    
    narrative = (
        f"Subject: {actor}. "
        f"Decision Point: Must decide whether to {action} {target} {context}. "
        f"Projected Outcome: This action typically results in {consequence}."
    )
    
    return {
        "id": str(uuid.uuid4()),
        "source": "GLOBAL_DATA_LAKE_PARTITION_42",
        "scenario": narrative,
        "complexity_score": random.uniform(0.7, 0.99)
    }

def stream_data():
    print("🌊 Connecting to Orbis Global Data Stream (SECURE MODE)...")
    
    # 1. Generate Identity
    print("🔐 Generating Ephemeral Identity (KeyPair)...")
    signing_key = nacl.signing.SigningKey.generate()
    verify_key = signing_key.verify_key
    wallet_id = verify_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')
    print(f"   🆔 Wallet ID: {wallet_id}")
    
    # 2. Fund Wallet via Faucet
    print("💧 Requesting Funds from Faucet...")
    try:
        res = requests.post(f"{NODE_URL}/api/faucet", json={"wallet_id": wallet_id})
        if res.status_code == 200:
            print("   ✅ Funded: 10 ETHC received.")
        else:
            print(f"   ⚠️ Faucet Failed: {res.text}")
            # Continue anyway, might have funds from before (if persistent logic existed) or fail later
    except Exception as e:
        print(f"   ❌ Faucet Error: {e}")

    print("🚀 STREAM STARTED. Processing Batch Jobs...")
    print("===============================================================")

    batch_id = 1000
    
    while True:
        # 1. Pull "Raw Data"
        dilemma = generate_complex_dilemma()
        
        # 2. Log
        print(f"\n📥 [DATA-LAKE] Fetching Record ID: {dilemma['id'][:8]}...")
        
        # 3. Push with Signature
        try:
            timestamp = str(time.time())
            
            # Sign the Identity Proof (timestamp:wallet_id)
            message = f"{timestamp}:{wallet_id}".encode()
            signed = signing_key.sign(message)
            signature_hex =  signed.signature.hex()
            
            headers = {
                "X-Orbis-Wallet": wallet_id,
                "X-Orbis-Signature": signature_hex,
                "X-Orbis-Timestamp": timestamp
            }
            
            payload = {
                "action": dilemma['scenario'],
                "context": {"source": dilemma['source'], "batch": batch_id}
            }
            
            start_time = time.time()
            res = requests.post(f"{NODE_URL}/api/verify", json=payload, headers=headers)
            latency = (time.time() - start_time) * 1000
            
            if res.status_code == 200:
                print(f"   ✅ [SENT] Verified & Blocked (Latency: {latency:.0f}ms)")
            else:
                print(f"   ❌ [FAIL] Node Rejected: {res.status_code} - {res.text}")
                
        except Exception as e:
            print(f"   ⚠️ [NET] Connection Lost: {e}")
            
        batch_id += 1
        time.sleep(STREAM_SPEED)

if __name__ == "__main__":
    stream_data()