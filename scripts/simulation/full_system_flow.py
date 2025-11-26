import subprocess
import time
import requests
import sys
import os
import signal
import json

# Configuration
API_URL = "http://localhost:6429/api"
SERVER_CMD = ["/Users/yaron/CascadeProjects/Orbis-Ethica/venv/bin/python", "-m", "uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "6429"]

def wait_for_server():
    print("⏳ Waiting for server to start...")
    for _ in range(30):
        try:
            requests.get(f"{API_URL}/docs")
            print("✅ Server is UP!")
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

def run_simulation():
    print("🚀 Starting Full System Simulation...")
    
    # 1. Start Server
    server_process = subprocess.Popen(SERVER_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    try:
        if not wait_for_server():
            print("❌ Server failed to start.")
            return

        # 2. Get Initial Wallet Balance
        # We need to know who we are. The server generates a random node ID/Identity on startup unless persisted.
        # But for the proposal, we can submit as ANY wallet ID.
        # Let's use a specific test wallet ID.
        test_wallet = "0xSIMULATION_WALLET_12345"
        
        print(f"\n💰 Checking Initial Balance for {test_wallet}...")
        # Note: The /api/wallet endpoint returns the NODE'S wallet, not an arbitrary one.
        # We need to check the balance via the ledger directly or if there's an endpoint for it.
        # Currently /api/wallet gets "my" wallet.
        # Let's assume we are the node. But the node identity is random.
        # We can get the node's address from /api/wallet.
        
        resp = requests.get(f"{API_URL}/wallet")
        if resp.status_code != 200:
            print(f"❌ Failed to get wallet info: {resp.text}")
            return
            
        wallet_info = resp.json()
        my_address = wallet_info['address']
        initial_balance = wallet_info['liquid_balance']
        print(f"   Identity: {my_address}")
        print(f"   Initial Balance: {initial_balance} ETHC")
        
        # 3. Submit Proposal & Listen to Stream
        print("\n📝 Submitting Proposal & Listening to Deliberation Stream...")
        
        proposal_data = {
            "title": "Simulation Test Proposal",
            "description": "This is a test proposal to verify the full system flow including P2P, Deliberation, and Ledger integration.",
            "author": "0xSIMULATION_WALLET_12345",
            "category": "high_impact",
            "domain": "technology",
            "submitter_id": "0xSIMULATION_WALLET_12345" # Using wallet as ID for reward
        }
        

        
        # Sign Request (Phase XVI)
        # Add project root to path to import backend
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
        from backend.security.identity import NodeIdentity
        
        # Use simulation password or env
        password = os.getenv("KEY_PASSWORD", "OrbisEthicaSecureKey2025!") 
        # Create a temporary identity for the simulation client
        # We use a random ID for the client to avoid conflict with the server's identity if running on same machine/dir
        client_identity = NodeIdentity(node_id="simulation_client", password=password)
        
        headers = client_identity.sign_request("POST", "/api/proposals/submit", proposal_data)
        
        # SSE Stream Request
        # Note: requests.post doesn't support streaming response easily with context manager in the same way for SSE
        # We use a session with stream=True
        
        session = requests.Session()
        response = session.post(
            f"{API_URL}/proposals/submit", 
            json=proposal_data, 
            headers=headers, # Add Auth Headers
            stream=True
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to submit proposal: {response.text}")
            return
        
        print("   ✅ Proposal Submitted. Listening for events...")
        
        proposal_approved = False
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    event_data = json.loads(decoded_line[6:])
                    event_type = event_data.get("type")
                    
                    if event_type == "init":
                        print(f"   🔹 {event_data.get('message')}")
                    elif event_type == "round_start":
                        print(f"   🔄 Round {event_data.get('round')} Started")
                    elif event_type == "entity_vote":
                        print(f"      🗳️  {event_data.get('entity')}: {event_data.get('vote')}")
                    elif event_type == "round_result":
                        print(f"   📊 Round Score: {event_data.get('score'):.2f} (Outcome: {event_data.get('outcome')})")
                    elif event_type == "economic_reward":
                        print(f"   💰 {event_data.get('message')}")
                    elif event_type == "final_decision":
                        outcome = event_data.get("outcome")
                        print(f"   🏁 Final Decision: {outcome.upper()}")
                        if outcome == "approved":
                            proposal_approved = True
                        break
                    elif event_type == "error":
                        print(f"   ❌ Error: {event_data.get('message')}")
                        break
                            
        if not proposal_approved:
            print("   ❌ Proposal was not approved. Cannot verify reward.")
            return
        
        # 6. Check Final Balance
        print("\n💰 Checking Final Balance...")
        time.sleep(2) # Wait for block processing
        resp = requests.get(f"{API_URL}/wallet")
        final_info = resp.json()
        final_balance = final_info['liquid_balance']
        
        print(f"   Final Balance: {final_balance} ETHC")
        
        if final_balance > initial_balance:
            print(f"   ✅ SUCCESS: Balance increased by {final_balance - initial_balance} ETHC!")
        else:
            print("   ❌ FAILURE: Balance did not increase.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("\n🛑 Stopping Server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    run_simulation()
