import sys
import time

import requests

BASE_URL = "http://46.62.199.4:8000"
WALLET_ID = "demo_user"

def log(msg, type="INFO"):
    print(f"[{type}] {msg}")

def test_health():
    log("Checking System Health...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            log(f"✅ System is Online: {r.json()}", "SUCCESS")
            return True
        else:
            log(f"❌ Health Check Failed: {r.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"❌ Connection Failed: {e}", "CRITICAL")
        return False

def test_balance(expected_min=0):
    log(f"Checking Balance for {WALLET_ID}...")
    try:
        r = requests.get(f"{BASE_URL}/api/balance/{WALLET_ID}")
        data = r.json()
        balance = data['balance']
        log(f"💰 Balance: {balance} ETHC", "INFO")
        if balance >= expected_min:
            return balance
        else:
            log(f"❌ Balance too low (Expected > {expected_min})", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Failed to get balance: {e}", "ERROR")
        return None

def test_verification_flow():
    log("Running Ethical Verification (Cost: 0.1 ETHC)...")
    payload = {
        "action": "Deploy AI system without user consent",
        "context": {"user_impact": "high", "regulatory_compliance": "none"}
    }
    headers = {
        "X-Orbis-Wallet": WALLET_ID,
        "Content-Type": "application/json"
    }
    
    try:
        start_time = time.time()
        # Ensure we wait enough for the streamed response or simple response
        # The endpoint returns a JSON, not a stream directly (it consumes the generator internally)
        r = requests.post(f"{BASE_URL}/api/verify", json=payload, headers=headers, timeout=30)
        
        duration = time.time() - start_time
        
        if r.status_code == 200:
            data = r.json()
            log(f"✅ Verification Successful ({duration:.2f}s)", "SUCCESS")
            log(f"🧠 Verdict: {data['safe']} (Score: {data['score']})", "INFO")
            log(f"📝 Reason: {data['reason']}", "INFO")
            return True
        elif r.status_code == 402:
            log("❌ Payment Failed (Insufficient Funds)", "ERROR")
            return False
        else:
            log(f"❌ Logic Error: {r.text}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Request Failed: {e}", "CRITICAL")
        return False

def main():
    print("🏆 Starting ORBIS ETHICA Gold Standard Verification 🏆")
    print("==================================================")
    
    if not test_health():
        sys.exit(1)
        
    initial_balance = test_balance(expected_min=0.1)
    if initial_balance is None:
        sys.exit(1)
        
    if test_verification_flow():
        final_balance = test_balance()
        
        # Verify Deduction
        if abs(initial_balance - final_balance - 0.1) < 0.0001:
             log("✅ Economy Check Passed: Exact 0.1 ETHC deduction verified.", "SUCCESS")
        else:
             log(f"⚠️ Economy Mismatch: {initial_balance} -> {final_balance} (Diff: {initial_balance - final_balance})", "WARNING")
             
    print("==================================================")
    print("🏁 Verification Complete.")

if __name__ == "__main__":
    main()
