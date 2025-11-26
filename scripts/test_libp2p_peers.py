import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import trio
from backend.p2p.libp2p_service import Libp2pService

async def main():
    print("🧪 Testing Libp2p Peers...")
    service = Libp2pService(port=9001)
    await service.start()
    
    peers = service.get_connected_peers()
    print(f"✅ Connected Peers: {peers}")
    
    await service.stop()

if __name__ == "__main__":
    trio.run(main)
