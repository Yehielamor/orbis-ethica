import trio
import sys
import os
import json
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.p2p.libp2p_service import Libp2pService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_test():
    print("🧪 Testing P2P GossipSub (Block Broadcasting)...")
    
    async with trio.open_nursery() as nursery:
        # 1. Start Node A (Bootstrapper)
        node_a = Libp2pService(port=10001)
        await node_a.start(nursery)
        
        # 2. Start Node B (Peer)
        node_b = Libp2pService(port=10002)
        await node_b.start(nursery)
        
        # 3. Connect Node B to Node A
        # We need to manually connect them for GossipSub to form a mesh
        addr_a = node_a.host.get_addrs()[0]
        peer_id_a = node_a.get_peer_id()
        multiaddr_a = f"{addr_a}/p2p/{peer_id_a}"
        
        print(f"🔗 Connecting B to A: {multiaddr_a}")
        
        connected = False
        for i in range(5):
            try:
                await node_b.host.connect(multiaddr_a)
                connected = True
                print(f"✅ Nodes Connected: A <-> B (Attempt {i+1})")
                break
            except Exception as e:
                print(f"⚠️ Connection attempt {i+1} failed: {e}")
                await trio.sleep(1)
                
        if not connected:
            print("❌ Failed to connect nodes after 5 attempts")
            sys.exit(1)
        
        # 4. Setup Message Capture on Node B
        received_messages = []
        
        # Mock the callback
        async def on_block_received(data, sender):
            print(f"📥 Node B received block from {sender}")
            received_messages.append(data)
            
        node_b.on_block_received = on_block_received
        
        # 5. Broadcast from Node A
        test_block = {
            "index": 1,
            "hash": "0000testblockhash",
            "data": {"msg": "Hello P2P World"}
        }
        block_json = json.dumps(test_block)
        
        print("📡 Node A broadcasting block...")
        # Wait a bit for the mesh to form
        await trio.sleep(1) 
        
        await node_a.broadcast_block(block_json)
        
        # 6. Wait for reception
        print("⏳ Waiting for message...")
        with trio.move_on_after(5): # 5 second timeout
            while len(received_messages) == 0:
                await trio.sleep(0.1)
                
        # 7. Verify
        if len(received_messages) > 0:
            print("✅ SUCCESS: Block received via GossipSub!")
            print(f"   Content: {received_messages[0]}")
        else:
            print("❌ FAILURE: Message not received within timeout.")
            # Don't exit here, let cleanup happen
            
        # Cleanup
        await node_a.stop()
        await node_b.stop()
        nursery.cancel_scope.cancel() # Stop background tasks

if __name__ == "__main__":
    try:
        trio.run(run_test)
    except KeyboardInterrupt:
        pass
    except BaseException as e:
        # Python 3.11+ uses ExceptionGroup for Trio
        print(f"❌ Error caught: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
