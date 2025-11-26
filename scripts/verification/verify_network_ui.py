import sys
import os
import asyncio
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.p2p.node_manager import NodeManager, PeerInfo
from backend.api.app import app

async def test_network_api():
    print("🌐 Testing Network Visualization API...")
    
    # 1. Initialize NodeManager
    node_manager = NodeManager(node_id="test_node", host="127.0.0.1", port=8000)
    
    # 2. Add a mock peer
    peer = PeerInfo(
        node_id="peer_node_1",
        host="192.168.1.5",
        port=8001,
        first_seen=datetime.utcnow().timestamp(),
        last_seen=datetime.utcnow().timestamp(),
        reputation=0.85
    )
    node_manager.add_peer(peer)
    
    # 3. Get Peer Status (Simulate API call)
    status_list = node_manager.get_peers_status()
    
    print(f"📊 Retrieved {len(status_list)} nodes from status list")
    
    # 4. Verify Local Node
    local_node = next((n for n in status_list if n["role"] == "local"), None)
    if local_node:
        print(f"✅ Local Node Found: {local_node['id']} ({local_node['address']})")
    else:
        print("❌ Local Node MISSING")
        
    # 5. Verify Peer Node
    peer_node = next((n for n in status_list if n["role"] == "peer"), None)
    if peer_node:
        print(f"✅ Peer Node Found: {peer_node['id']} ({peer_node['address']}) - Rep: {peer_node['reputation']}")
        if peer_node['id'] == "peer_node_1" and peer_node['reputation'] == 0.85:
             print("✅ Peer Data Integrity: PASSED")
        else:
             print("❌ Peer Data Integrity: FAILED")
    else:
        print("❌ Peer Node MISSING")

if __name__ == "__main__":
    asyncio.run(test_network_api())
