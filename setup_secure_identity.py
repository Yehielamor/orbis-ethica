import os
import secrets
import shutil
import json
from backend.security.identity import NodeIdentity

def setup_security():
    print("🔒 Setting up Secure Identity...")
    
    # 1. Generate Strong Password
    password = secrets.token_urlsafe(32)
    print(f"🔑 Generated Strong Password (length={len(password)})")
    
    # 2. Save to .env
    env_path = ".env"
    env_content = ""
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            env_content = f.read()
    
    # Remove existing KEY_PASSWORD if any
    lines = [l for l in env_content.splitlines() if not l.startswith("KEY_PASSWORD=")]
    lines.append(f"KEY_PASSWORD={password}")
    
    with open(env_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("✅ Saved password to .env")
    
    # 3. Backup Old Keys
    keys_dir = ".keys"
    if os.path.exists(keys_dir):
        backup_dir = f".keys_backup_{secrets.token_hex(4)}"
        shutil.move(keys_dir, backup_dir)
        print(f"📦 Backed up old keys to {backup_dir}")
    
    # 4. Generate New Keys
    # We need to set the env var for the class to use it? No, we pass it to init.
    identity = NodeIdentity(key_dir=keys_dir, node_id="default_node", password=password)
    pub_key = identity.public_key_hex
    print(f"👤 New Identity Public Key: {pub_key}")
    
    # 5. Update Genesis
    genesis_path = "genesis.json"
    with open(genesis_path, "r") as f:
        genesis_data = json.load(f)
        
    # Update initial balances
    # Reset to clean state first to avoid confusion
    genesis_data["initial_balances"] = {
        pub_key: 100000.0,
        "community_treasury": 900000.0,
        "founder_vesting_contract": 8000000.0,
        "ethical_allocation_pool": 1000000.0
    }
    print(f"💰 Allocation Updated:")
    print(f"   👤 User (You): 100,000 ETHC")
    print(f"   🏛️  Treasury: 900,000 ETHC")
    print(f"   🔒 Vesting: 8,000,000 ETHC")
    print(f"   🌱 Ethical Pool: 1,000,000 ETHC")
        
    with open(genesis_path, "w") as f:
        json.dump(genesis_data, f, indent=4)
    print("✅ Updated genesis.json")
    
    # 6. Reset DB
    db_path = "orbis_ethica.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Deleted old database (triggering fresh Genesis)")

if __name__ == "__main__":
    setup_security()
