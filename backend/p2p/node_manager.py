import logging
import time
from typing import Dict, Set, List, Optional, Any
import asyncio
import aiohttp
from .models import PeerInfo, P2PMessage, MessageType

logger = logging.getLogger(__name__)

class NodeManager:
    """
    Manages the lifecycle of P2P connections and peer discovery.
    """
    def __init__(self, node_id: str, host: str, port: int, seed_nodes: List[str] = None, identity: Optional[Any] = None):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.peers: Dict[str, PeerInfo] = {}  # node_id -> PeerInfo
        self.active_connections: Dict[str, Any] = {} # node_id -> WebSocket connection
        self.seed_nodes = seed_nodes or []
        self.identity = identity # NodeIdentity instance
        
        # Deduplication cache for gossip
        self.seen_messages: Set[str] = set()

    async def start(self):
        """Initialize P2P networking."""
        logger.info(f"🚀 Starting NodeManager for {self.node_id} on {self.host}:{self.port}")
        # Connect to seed nodes
        for seed in self.seed_nodes:
            await self.connect_to_seed(seed)

    async def connect_to_seed(self, seed_address: str):
        """
        Connect to a seed node (format: 'host:port').
        """
        try:
            host, port = seed_address.split(":")
            # In a real implementation, we would establish a persistent WebSocket connection here.
            # For now, we just register it as a known peer.
            # The actual connection logic will be handled by the WebSocket client.
            logger.info(f"🌱 Registering seed node: {seed_address}")
            # We don't know the ID yet, so we'll discover it during handshake
            pass 
        except Exception as e:
            logger.error(f"Failed to parse seed address {seed_address}: {e}")

    def add_peer(self, peer: PeerInfo):
        """Register a new peer."""
        if peer.node_id != self.node_id and peer.node_id not in self.peers:
            logger.info(f"🔗 New Peer Added: {peer.node_id} ({peer.host}:{peer.port})")
            self.peers[peer.node_id] = peer
        
        # Update last seen if already exists
        if peer.node_id in self.peers:
            self.peers[peer.node_id].last_seen = time.time()

    def remove_peer(self, node_id: str):
        """Remove a disconnected peer."""
        if node_id in self.peers:
            logger.info(f"❌ Peer Removed: {node_id}")
            del self.peers[node_id]

    def get_known_peers(self) -> List[PeerInfo]:
        """Return list of all known active peers."""
        # Filter out stale peers (e.g., not seen in 1 hour)
        # For now, return all
        return list(self.peers.values())

    async def broadcast(self, message: P2PMessage):
        """
        Broadcast a message to all active peers (Gossip Protocol).
        """
        # Sign the message if identity is available
        if self.identity and not message.signature:
            # We sign the payload + timestamp + type + sender_id
            # To simplify, we'll sign a dict representation of the core fields
            sign_data = {
                "type": message.type,
                "sender_id": message.sender_id,
                "payload": message.payload,
                "timestamp": message.timestamp
            }
            message.signature = self.identity.sign(sign_data)

        # Add to seen cache to prevent re-broadcasting
        msg_hash = f"{message.sender_id}:{message.timestamp}:{message.type}"
        if msg_hash in self.seen_messages:
            return
        self.seen_messages.add(msg_hash)

        logger.info(f"📢 Broadcasting {message.type} to {len(self.active_connections)} peers")
        
        # Serialize message once
        json_msg = message.json()
        
        # Send to all active connections
        for peer_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json_msg)
            except Exception as e:
                logger.error(f"Failed to send to {peer_id}: {e}")
                # We might want to remove the peer here if it fails repeatedly
