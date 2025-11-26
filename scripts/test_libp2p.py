import sys
import os
import trio
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.p2p.libp2p_service import Libp2pService

logging.basicConfig(level=logging.INFO)

async def main():
    print("🧪 Testing Libp2p Service...")
    
    service = Libp2pService(port=9000)
    
    try:
        await service.start()
        
        print(f"✅ Service Started. Peer ID: {service.get_peer_id()}")
        
        # Keep alive for a few seconds to verify it stays up
        await trio.sleep(5)
        
        await service.stop()
        print("✅ Service Stopped")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        trio.run(main)
    except KeyboardInterrupt:
        pass
