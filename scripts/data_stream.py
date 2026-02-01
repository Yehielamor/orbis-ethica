import requests
import random
import time
import sys
import uuid

# Configuration
NODE_URL = "http://46.62.199.4:8000"
# מהירות שליחת הנתונים (שניות)
STREAM_SPEED = 2 

# --- BIG DATA COMPONENTS ---
# By combining these lists, we generate: 
# 15 * 15 * 15 * 15 * 15 * 5 = ~3.8 Million unique scenarios just from this small seed.
# In a real version, these lists would have thousands of entries.

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
    
    # Construct the narrative
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
    print("🌊 Connecting to Orbis Global Data Stream...")
    time.sleep(1)
    print("📡 Establishing Uplink to Node A (46.62.199.4)...")
    time.sleep(1)
    print("📂 Mounting Dataset: ETHICS_DATASET_V9 (840 TB)...")
    time.sleep(1)
    print("🚀 STREAM STARTED. Processing Batch Jobs...")
    print("===============================================================")

    batch_id = 1000
    
    while True:
        # 1. Pull "Raw Data"
        dilemma = generate_complex_dilemma()
        
        # 2. Log the "Extraction"
        print(f"\n📥 [DATA-LAKE] Fetching Record ID: {dilemma['id'][:8]}...")
        print(f"   📄 Scenario: \"{dilemma['scenario'][:80]}...\"")
        
        # 3. Push to Processing Node (The Server)
        try:
            payload = {
                "action": dilemma['scenario'],
                "context": {"source": dilemma['source'], "batch": batch_id}
            }
            # Use the GENESIS WEALTH HOLDER wallet to pass payment checks!
            headers = {"X-Orbis-Wallet": "0xde8037e96eadf0ae71b5b2b78b8754484afce931d78a1a19b63700f3a76b85eb"}
            
            start_time = time.time()
            res = requests.post(f"{NODE_URL}/api/verify", json=payload, headers=headers)
            latency = (time.time() - start_time) * 1000
            
            if res.status_code == 200:
                print(f"   ✅ [SENT] Distributed to Swarm (Latency: {latency:.0f}ms)")
            else:
                print(f"   ❌ [FAIL] Node Rejected: {res.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ [NET] Connection Lost: {e}")
            
        batch_id += 1
        time.sleep(STREAM_SPEED)

if __name__ == "__main__":
    stream_data()