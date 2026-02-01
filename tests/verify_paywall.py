import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from sdk.orbis import Orbis

BASE_URL = "http://localhost:8000"

def test_step(name, success, message):
    symbol = "✅" if success else "❌"
    print(f"{symbol} {name}: {message}")

print("\n💰 ORBIS PAYWALL VERIFICATION\n" + "="*40)

# 1. Test No Wallet (Should Fail 402)
try:
    print("\n1️⃣  Testing No Wallet...")
    orbis_free = Orbis(base_url=BASE_URL) # No API Key
    result = orbis_free.verify("Test Action")
    # If SDK returns result, it might be the fallback. Check if it's the fallback error.
    if "Connection to Orbis Network failed" in result.get("reason", "") and "402" in result.get("reason", ""):
        test_step("No Wallet", True, "Correctly rejected (402 Payment Required)")
    else:
        test_step("No Wallet", False, f"Unexpected result: {result}")
except Exception as e:
    test_step("No Wallet", False, f"Error: {e}")

# 2. Test Empty Wallet (Should Fail 402)
empty_wallet = "0xEmptyWallet123"
try:
    print(f"\n2️⃣  Testing Empty Wallet ({empty_wallet})...")
    orbis_empty = Orbis(api_key=empty_wallet, base_url=BASE_URL)
    result = orbis_empty.verify("Test Action")
    if "Connection to Orbis Network failed" in result.get("reason", "") and "402" in result.get("reason", ""):
        test_step("Empty Wallet", True, "Correctly rejected (Insufficient Funds)")
    else:
        test_step("Empty Wallet", False, f"Unexpected result: {result}")
except Exception as e:
    test_step("Empty Wallet", False, f"Error: {e}")

# 3. Mint Tokens (Backdoor) & Test Rich Wallet
rich_wallet = "0xRichWallet999"
try:
    print(f"\n3️⃣  Minting Tokens to {rich_wallet}...")
    # We need a way to mint. Since we don't have a public mint endpoint, 
    # we'll use a python script to access the DB directly or assume we can use the 'genesis' trick.
    # Actually, let's use a small script to inject funds directly into the DB for this test.
    
    import sqlite3
    # Server defaults to backend/orbis_ethica.db locally
    db_path = "backend/orbis_ethica.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Mint 100 ETHC
    # Ensure timestamp is string format that SQLite accepts
    import datetime
    import random
    ts = datetime.datetime.utcnow()
    # ID must be INTEGER
    tx_id = random.randint(100000, 999999)
    cursor.execute("INSERT INTO ledger_entries (id, sender, recipient, amount, transaction_type, timestamp, block_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (tx_id, "system_mint", rich_wallet, 100.0, "mint", ts, None))
    conn.commit()
    conn.close()
    print("   💰 Minted 100 ETHC via Backdoor DB Injection")
    
    print(f"4️⃣  Testing Rich Wallet ({rich_wallet})...")
    orbis_rich = Orbis(api_key=rich_wallet, base_url=BASE_URL)
    # Action must be long enough to pass Proposal validation (>50 chars)
    long_action = "I will transfer funds to a verified charity to support the relief effort in the disaster zone."
    result = orbis_rich.verify(long_action)
    
    if result.get("safe") is not None and "Connection to Orbis Network failed" not in result.get("reason", ""): 
        test_step("Rich Wallet", True, "Success! Payment accepted.")
    else:
        test_step("Rich Wallet", False, f"Failed: {result}")
        
except Exception as e:
    test_step("Rich Wallet", False, f"Error: {e}")

print("\n" + "="*40 + "\n")
