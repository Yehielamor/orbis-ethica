import logging
import trio
from libp2p import new_host
from libp2p.peer.peerinfo import info_from_p2p_addr
from multiaddr import Multiaddr

logger = logging.getLogger(__name__)

class Libp2pService:
    """
    Manages the Libp2p host and P2P networking.
    Uses Trio as the async backend (required by python-libp2p).
    """
    def __init__(self, port: int = 0):
        self.port = port
        self.host = None
        self.is_running = False

    async def start(self, nursery=None):
        """Start the Libp2p host."""
        try:
            # Listen ONLY on localhost to prevent network visibility
            listen_addr = Multiaddr(f"/ip4/127.0.0.1/tcp/{self.port}")
            
            self.host = new_host()
            
            # Explicitly listen on the address
            await self.host.get_network().listen(listen_addr)
            
            # DEBUG: Check addresses immediately
            addrs = self.host.get_addrs()
            if not addrs:
                logger.warning("⚠️ Host created but no addresses found even after listen!")
            else:
                logger.info(f"✅ Host bound to: {addrs}")
            
            # Initialize GossipSub
            from libp2p.pubsub.gossipsub import GossipSub
            from libp2p.pubsub.pubsub import Pubsub
            
            # Create Router
            self.gossip_router = GossipSub(
                protocols=["/meshsub/1.1.0"], 
                degree=10, 
                degree_low=9, 
                degree_high=11
            )
            
            # Create PubSub with Host and Router
            self.pubsub = Pubsub(host=self.host, router=self.gossip_router)
            
            # Subscribe to Blocks Topic
            self.blocks_topic = "orbis/blocks/1.0.0"
            self.blocks_sub = await self.pubsub.subscribe(self.blocks_topic)
            
            # Start handling messages in background
            if nursery:
                nursery.start_soon(self._handle_block_messages)
            else:
                logger.warning("⚠️ No nursery provided to start(), background tasks won't run!")
            
            self.is_running = True
            logger.info(f"🚀 Libp2p Host Started!")
            logger.info(f"🆔 Peer ID: {self.host.get_id().to_string()}")
            for addr in self.host.get_addrs():
                logger.info(f"📍 Address: {addr}")
                
        except Exception as e:
            logger.error(f"❌ Failed to start Libp2p host: {e}")
            raise e

    async def _handle_block_messages(self):
        """Handle incoming block messages."""
        while self.is_running:
            try:
                msg = await self.blocks_sub.get()
                data = msg.data.decode()
                sender = msg.from_id.to_string()
                logger.info(f"🧱 Received Block from {sender}: {data[:50]}...")
                
                # Here we would callback to the Ledger to add the block
                # For now, we just log it. In full integration, we'd use an event bus or callback.
                if hasattr(self, 'on_block_received'):
                    await self.on_block_received(data, sender)
                    
            except Exception as e:
                logger.error(f"Error handling block message: {e}")
                await trio.sleep(0.1)

    async def broadcast_block(self, block_json: str):
        """Broadcast a block to the network."""
        if not self.host or not self.pubsub:
            logger.warning("Cannot broadcast: P2P not initialized")
            return
            
        try:
            await self.pubsub.publish(self.blocks_topic, block_json.encode())
            logger.info(f"📡 Broadcasted Block: {block_json[:50]}...")
        except Exception as e:
            logger.error(f"Failed to broadcast block: {e}")

    async def stop(self):
        """Stop the host."""
        if self.host:
            # self.host.close() # Check if close method exists in this version
            pass
        self.is_running = False
        logger.info("🛑 Libp2p Host Stopped")

    def get_peer_id(self):
        if self.host:
            return self.host.get_id().to_string()
        return None

    def get_connected_peers(self):
        """Get list of connected peer IDs."""
        if not self.host:
            return []
        return [p.to_string() for p in self.host.get_peerstore().peer_ids()]

    # --- Background Thread Support ---
    
    def start_background(self):
        """Start the service in a background thread (for Asyncio integration)."""
        import threading
        self._trio_token = None
        self._thread = threading.Thread(target=self._run_trio_loop, daemon=True)
        self._thread.start()

    def _run_trio_loop(self):
        """Run the Trio loop."""
        try:
            trio.run(self._trio_main)
        except Exception as e:
            logger.error(f"Trio loop crashed: {e}")

    async def _trio_main(self):
        """Main entry point for Trio."""
        self._trio_token = trio.lowlevel.current_trio_token()
        async with trio.open_nursery() as nursery:
            await self.start(nursery)
            # Keep running until stopped
            while self.is_running:
                await trio.sleep(1)
