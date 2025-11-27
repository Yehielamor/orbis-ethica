import os
import re
import sys
from pathlib import Path

def check_hardcoded_keys(root_dir):
    print("🔍 Scanning for hardcoded keys...")
    suspicious_patterns = [
        r"BEGIN PRIVATE KEY",
        r"sk_[a-zA-Z0-9]{20,}",
        r"ghp_[a-zA-Z0-9]{20,}",
        r"eyJ[a-zA-Z0-9]{20,}" # JWT-like
    ]
    
    issues = []
    
    for path in Path(root_dir).rglob("*"):
        if path.is_file() and not any(x in str(path) for x in [".git", "venv", "__pycache__", ".keys", "node_modules", ".DS_Store"]):
            try:
                content = path.read_text(errors="ignore")
                for pattern in suspicious_patterns:
                    if re.search(pattern, content):
                        # Ignore the audit script itself and tests
                        if "security_audit.py" not in str(path) and "test" not in str(path):
                            issues.append(f"⚠️  Potential secret in {path}: matches {pattern}")
            except Exception:
                pass
                
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✅ No obvious hardcoded keys found.")

def check_debug_mode(root_dir):
    print("\n🔍 Checking for Debug Mode configurations...")
    # Check docker-compose
    dc_path = os.path.join(root_dir, "docker-compose.yml")
    if os.path.exists(dc_path):
        content = open(dc_path).read()
        if "command: python -m uvicorn backend.api.app:app --reload" in content:
            print("⚠️  Warning: Docker Compose is using --reload (Debug Mode). Ensure this is not for production.")
        else:
            print("✅ Docker Compose looks production-ready (no --reload).")

def check_unencrypted_keys(root_dir):
    print("\n🔍 Checking for unencrypted keys...")
    keys_dir = os.path.join(root_dir, ".keys")
    if os.path.exists(keys_dir):
        for f in os.listdir(keys_dir):
            if f.endswith(".sk"):
                content = open(os.path.join(keys_dir, f), "rb").read()
                if b"ciphertext" not in content and b"nonce" not in content:
                     print(f"❌ CRITICAL: Unencrypted private key found: {f}")
                else:
                    print(f"✅ Encrypted key found: {f}")
    else:
        print("ℹ️  No .keys directory found (Clean state).")

if __name__ == "__main__":
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    print(f"🛡️  Starting Security Audit for {root}\n" + "="*50)
    
    check_hardcoded_keys(root)
    check_debug_mode(root)
    check_unencrypted_keys(root)
    
    print("\n" + "="*50 + "\n🏁 Audit Complete.")
