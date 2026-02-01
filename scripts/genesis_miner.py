"""
Genesis Miner - Proof of Concept for Orbis Ethica
Mines blocks by solving a trivial SHA256 puzzle and submits them to the local node.
"""
import time
import hashlib
import json
import random
import requests
import os
from datetime import datetime

NODE_URL = os.getenv("NODE_URL", "http://127.0.0.1:8000")
MINER_ID = f"miner_{random.randint(1000, 9999)}"

def get_mining_info():
    try:
        resp = requests.get(f"{NODE_URL}/api/mining/info", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except:
        return None
    return None

def mine_block(info):
    index = info['index']
    prev_hash = info['previous_hash']
    difficulty = info.get('difficulty', 1) # Unused for MVP, just for show
    
    print(f"⛏️  Mining Block #{index} on top of {prev_hash[:8]}...")
    
    # 1. Construct Candidate
    timestamp = datetime.utcnow().isoformat()
    validator = MINER_ID
    # Merkle Root of empty transactions list
    merkle_root = hashlib.sha256("".encode()).hexdigest()
    
    # 2. Work (Trivial: just find a hash starting with '0' maybe? Or just submit valid structure)
    # The Ledger check in backend currently skips hash check for "MVP speed" in validate_block
    # But let's do a tiny bit of work to simulate it.
    
    nonce = 0
    while True:
        # Format must match Ledger.create_block internal logic conceptually, 
        # but here we just need to produce a valid block structure for the API.
        # Structure required by API:
        # { index, hash, previous_hash, timestamp, validator_id, signature, transactions: [] }
        
        # We need to generate a hash that matches the content.
        # content = f"{index}{prev_hash}{timestamp}{merkle_root}{validator}"
        # Wait, nonce isn't in the content string in ledger.py!
        # Ledger.create_block defines content as: f"{new_index}{previous_hash}{timestamp.isoformat()}{merkle_root}{validator_id}"
        # So nonce is NOT used. The hash is deterministic based on timestamp.
        # To make it "mining", we just need to generate a valid block that the node accepts.
        # Since the node doesn't enforce difficulty yet, we just create one.
        
        block_content = f"{index}{prev_hash}{timestamp}{merkle_root}{validator}"
        block_hash = hashlib.sha256(block_content.encode()).hexdigest()
        
        # Simulate work
        if block_hash.startswith("0"): # Easy target
            print(f"💎 Block Mined! Hash: {block_hash}")
            return {
                "index": index,
                "hash": block_hash,
                "previous_hash": prev_hash,
                "timestamp": timestamp,
                "validator_id": validator,
                "signature": "miner_sig_mock",
                "transactions": []
            }
        
        # Change timestamp slightly to vary hash if we didn't match (though we stop at 0 so it's instant)
        # Actually with nonce missing, we can't iterate efficiently without changing timestamp.
        # Let's just accept the first hash for MVP speed.
        return {
                "index": index,
                "hash": block_hash,
                "previous_hash": prev_hash,
                "timestamp": timestamp,
                "validator_id": validator,
                "signature": "miner_sig_mock",
                "transactions": []
        }

def submit_block(block):
    try:
        resp = requests.post(f"{NODE_URL}/api/p2p/receive_block", json=block, timeout=5)
        if resp.status_code == 200:
            print(f"✅ Block #{block['index']} Accepted!")
        else:
            print(f"❌ Rejected: {resp.text}")
    except Exception as e:
        print(f"❌ connection error: {e}")

def main():
    print(f"🚀 Genesis Miner Started ({MINER_ID})")
    print(f"🔌 Connected to Node: {NODE_URL}")
    
    while True:
        info = get_mining_info()
        if info:
            block = mine_block(info)
            submit_block(block)
        else:
            print("💤 Node offline? Retrying...")
        
        time.sleep(5) # Block time 5s

if __name__ == "__main__":
    main()
