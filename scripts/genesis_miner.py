"""
Genesis Miner - Real Proof of Work (PoW) Implementation.
No sleep. Pure CPU grinding.
"""
import hashlib
import time
import requests
import os
import sys
import random
from datetime import datetime

# Configuration
NODE_URL = os.getenv("NODE_URL", "http://127.0.0.1:8000")
MINER_ID = f"miner_{random.randint(1000, 9999)}"

# Adjust difficulty: 4 = fast (~1-2s), 5 = medium (~10-30s), 6 = hard
DIFFICULTY_TARGET = "000000" 

def get_mining_info():
    try:
        resp = requests.get(f"{NODE_URL}/api/mining/info", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.ConnectionError:
        return None
    except Exception as e:
        print(f"⚠️ Error fetching info: {e}")
        return None

def calculate_hash(index, prev_hash, timestamp, merkle_root, validator, nonce):
    # We include the NONCE in the hash calculation, otherwise the hash never changes!
    payload = f"{index}{prev_hash}{timestamp}{merkle_root}{validator}{nonce}"
    return hashlib.sha256(payload.encode()).hexdigest()

def mine_block(info):
    index = info['index']
    prev_hash = info['previous_hash']
    
    print(f"\n⛏️  Mining Block #{index} [Target: starts with '{DIFFICULTY_TARGET}']")
    print(f"🔗 Parent: {prev_hash[:12]}...")
    
    timestamp = datetime.utcnow().isoformat()
    validator = MINER_ID
    merkle_root = hashlib.sha256("".encode()).hexdigest() # Empty transactions for now
    
    nonce = 0
    start_time = time.time()
    
    # --- THE REAL WORK LOOP ---
    while True:
        # 1. Calculate Hash
        block_hash = calculate_hash(index, prev_hash, timestamp, merkle_root, validator, nonce)
        
        # 2. Check Difficulty (PoW)
        if block_hash.startswith(DIFFICULTY_TARGET):
            elapsed = time.time() - start_time
            hashrate = nonce / elapsed if elapsed > 0 else 0
            
            print(f"\n💎 BOOM! Block Mined!")
            print(f"   Nonce: {nonce}")
            print(f"   Hash:  {block_hash}")
            print(f"   Time:  {elapsed:.2f}s ({hashrate:.0f} H/s)")
            
            return {
                "index": index,
                "hash": block_hash,
                "previous_hash": prev_hash,
                "timestamp": timestamp,
                "validator_id": validator,
                "signature": "miner_sig_pow", # In real protocol, we sign the hash
                "transactions": [],
                "nonce": nonce  # Sending nonce so server can verify if it wants to
            }
        
        # 3. Status Update (Visuals)
        if nonce % 100000 == 0:
            sys.stdout.write(f"\r⏳ Grinding... Nonce: {nonce} | Last Hash: {block_hash[:12]}...")
            sys.stdout.flush()
            
            # OPTIONAL: Check if someone else mined the block while we work
            # (In a real miner we would poll the node here every few seconds)
            
        nonce += 1

def submit_block(block):
    try:
        print(f"📡 Broadcasting Block #{block['index']}...")
        resp = requests.post(f"{NODE_URL}/api/p2p/receive_block", json=block, timeout=5)
        if resp.status_code == 200:
            print(f"✅ Accepted by network.")
        else:
            print(f"❌ Rejected: {resp.text}")
    except Exception as e:
        print(f"❌ Broadcast error: {e}")

def main():
    print("=========================================")
    print(f"🚀 ORBIS POW MINER v2.0 ({MINER_ID})")
    print(f"🎯 Difficulty: {len(DIFFICULTY_TARGET)} Leading Zeros")
    print(f"🔌 Node: {NODE_URL}")
    print("=========================================")
    
    while True:
        info = get_mining_info()
        if info:
            # Mining takes time now, so no need to sleep!
            new_block = mine_block(info)
            submit_block(new_block)
        else:
            print("💤 Node unreachable. Retrying in 2s...")
            time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Miner stopped by user.")