import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.api.app import app

def test_p2p_startup():
    print("🌐 Testing P2P Integration in App Startup...")
    
    # TestClient with lifespan context manager triggers startup/shutdown events
    with TestClient(app) as client:
        print("✅ App Startup Triggered")
        
        # Check if p2p_service was initialized and attached to app state
        if hasattr(app.state, 'p2p_service') and app.state.p2p_service:
            peer_id = app.state.p2p_service.get_peer_id()
            if peer_id:
                print(f"✅ Libp2p Service Active. Peer ID: {peer_id}")
            else:
                print("❌ Libp2p Service found but Peer ID is missing (not started?)")
        else:
            print("❌ Libp2p Service NOT found in app.state")

if __name__ == "__main__":
    test_p2p_startup()
