import time

import requests

LOCAL_URL = "http://localhost:8000"
REMOTE_URL = "http://77.42.30.95:8000"

def get_local_blocks(start_index):
    print(f"📥 Fetching local blocks from index {start_index}...")
    response = requests.get(f"{LOCAL_URL}/api/ledger/blocks?limit=100")
    if response.status_code != 200:
        print(f"❌ Failed to fetch local blocks: {response.text}")
        return []
    
    blocks = response.json()['blocks']
    # Sort by index ascending
    blocks.sort(key=lambda x: x['index'])
    
    # Filter for blocks >= start_index
    return [b for b in blocks if b['index'] >= start_index]

def push_block_to_remote(block):
    print(f"🚀 Pushing Block #{block['index']} to remote...")
    # We use the P2P WebSocket protocol usually, but for this force sync we might need a direct API if available.
    # Since there is no direct POST /api/ledger/blocks, we have to simulate P2P or rely on the node's sync.
    # Wait! The remote node should request sync if it sees a higher block.
    # But it only requests sync if it receives a GOSSIP_BLOCK message.
    
    # Let's try to use the P2P WebSocket to send the block as a GOSSIP_BLOCK message.
    pass

async def main():
    # 1. Get Remote Height
    try:
        r = requests.get(f"{REMOTE_URL}/api/ledger/blocks?limit=1")
        remote_tip = r.json()['blocks'][0]['index']
        print(f"🌍 Remote Height: {remote_tip}")
    except Exception as e:
        print(f"❌ Failed to get remote height: {e}")
        return

    # 2. Get Local Blocks starting from Index 1 (Full Sync)
    # We ignore remote_tip because we want to ensure full chain integrity from Genesis
    start_index = 1 
    blocks_to_push = get_local_blocks(start_index)
    
    if not blocks_to_push:
        print("✅ No blocks to push.")
        return

    print(f"📦 Found {len(blocks_to_push)} blocks to push (Full Chain Sync).")

    # 3. Connect via WebSocket and push
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("ws://77.42.30.95:8000/ws/p2p") as ws:
            # Handshake - Must match P2PMessage structure exactly
            handshake_payload = {
                "type": "HANDSHAKE",
                "sender_id": "force_sync_node",
                "timestamp": time.time(),
                "payload": {
                    "node_id": "force_sync_node",
                    "host": "0.0.0.0",
                    "port": 0,
                    "role": "peer",
                    "status": "active",
                    "reputation": 1.0
                }
            }
            await ws.send_json(handshake_payload)
            
            # Handle potential close frame or text response
            msg = await ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                print(f"🤝 Handshake Ack: {msg.data}")
            elif msg.type == aiohttp.WSMsgType.CLOSE:
                print(f"❌ Connection closed: {msg.data}")
                return

            for block in blocks_to_push:
                msg = {
                    "type": "GOSSIP_BLOCK",
                    "sender_id": "force_sync_script",
                    "timestamp": time.time(),
                    "payload": block
                }
                await ws.send_json(msg)
                print(f"📤 Sent Block #{block['index']}")
                await asyncio.sleep(0.5) # Rate limit

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
