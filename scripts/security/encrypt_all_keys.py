import os
import sys
import json
from nacl.encoding import HexEncoder

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.security.identity import NodeIdentity

def encrypt_all_keys(password: str):
    """
    Iterates over all .sk files in .keys/ and encrypts them if they are plain text.
    """
    key_dir = ".keys"
    if not os.path.exists(key_dir):
        print(f"❌ Key directory {key_dir} not found.")
        return

    count = 0
    encrypted_count = 0
    
    print(f"🔐 Starting Key Encryption Migration...")
    print(f"   Password Length: {len(password)} chars")
    
    for filename in os.listdir(key_dir):
        if filename.endswith(".sk"):
            node_id = filename[:-3]
            count += 1
            
            try:
                # 1. Try to load as PLAIN text (no password)
                # If this succeeds, the key is unencrypted
                identity = NodeIdentity(key_dir=key_dir, node_id=node_id, password=None)
                
                # If we are here, it loaded successfully without password.
                # Check if it was actually plain (NodeIdentity prints a warning, but we can check internal state if needed)
                # Actually, if it was encrypted, NodeIdentity(password=None) would raise ValueError or fail JSON parse.
                
                print(f"   Processing {node_id} (Plain)...")
                
                # 2. Encrypt
                # Get raw key bytes (Hex encoded)
                key_hex_bytes = identity.signing_key.encode(encoder=HexEncoder)
                
                # Use the internal helper to encrypt
                encrypted_json = identity._encrypt_private_key(key_hex_bytes, password)
                
                # 3. Save back to disk
                file_path = os.path.join(key_dir, filename)
                with open(file_path, "w") as f:
                    f.write(encrypted_json)
                    
                print(f"   ✅ Encrypted and saved.")
                encrypted_count += 1
                
            except ValueError as e:
                # Likely already encrypted (or corrupt)
                # Let's verify if it's encrypted
                try:
                    # Try loading WITH password
                    NodeIdentity(key_dir=key_dir, node_id=node_id, password=password)
                    print(f"   ⏭️  Skipping {node_id} (Already encrypted)")
                except Exception as inner_e:
                    print(f"   ❌ Failed to process {node_id}: {e} -> {inner_e}")
            except Exception as e:
                 print(f"   ❌ Error processing {node_id}: {e}")

    print(f"\n🎉 Migration Complete.")
    print(f"   Total Keys: {count}")
    print(f"   Newly Encrypted: {encrypted_count}")

if __name__ == "__main__":
    password = os.getenv("KEY_PASSWORD")
    if not password:
        print("❌ Error: KEY_PASSWORD environment variable is not set.")
        print("   Usage: KEY_PASSWORD=mypassword python scripts/security/encrypt_all_keys.py")
        sys.exit(1)
        
    encrypt_all_keys(password)
