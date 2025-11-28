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
            url = f"ws://{host}:{port}/ws/p2p"
            logger.info(f"🌱 Connecting to seed node: {url}")
            
            session = aiohttp.ClientSession()
            ws = await session.ws_connect(url)
            
            # 1. Send Handshake
            handshake = P2PMessage(
                type=MessageType.HANDSHAKE,
                sender_id=self.node_id,
                payload={
                    "node_id": self.node_id,
                    "host": self.host,
                    "port": self.port,
                    "reputation": 1.0,
                    "status": "active"
                }
            )
            await ws.send_str(handshake.json())
            
            # 2. Wait for ACK
            ack_data = await ws.receive_str()
            ack = P2PMessage.parse_raw(ack_data)
            
            if ack.type == MessageType.HANDSHAKE_ACK:
                peer_id = ack.sender_id
                logger.info(f"✅ Connected to seed {peer_id}")
                
                # Register peer
                peer_info = PeerInfo(
                    node_id=peer_id,
                    host=host,
                    port=int(port),
                    status="connected",
                    reputation=1.0,
                    last_seen=time.time()
                )
                self.add_peer(peer_info)
                self.active_connections[peer_id] = ws
                
                # Start listener task
                asyncio.create_task(self._listen_to_peer(peer_id, ws))
                
        except Exception as e:
            logger.error(f"Failed to connect to seed {seed_address}: {e}")

    async def _listen_to_peer(self, peer_id: str, ws: Any):
        """Listen for messages from a connected peer (Client Side)."""
        try:
            async for msg_str in ws:
                if msg_str.type == aiohttp.WSMsgType.TEXT:
                    try:
                        message = P2PMessage.parse_raw(msg_str.data)
                        # Deduplicate
                        msg_hash = f"{message.sender_id}:{message.timestamp}:{message.type}"
                        if msg_hash in self.seen_messages:
                            continue
                        self.seen_messages.add(msg_hash)
                        
                        logger.info(f"📩 Client received {message.type} from {peer_id}")
                        
                        # Handle Gossip (Basic forwarding for now)
                        # In a real app, we'd share the handler logic with app.py
                        if message.type in [MessageType.GOSSIP_TX, MessageType.GOSSIP_BLOCK]:
                             pass # Logic is currently in app.py server handler, need to unify
                             
                    except Exception as e:
                        logger.error(f"Error parsing message from {peer_id}: {e}")
                elif msg_str.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"ws connection closed with exception {ws.exception()}")
        except Exception as e:
            logger.error(f"Connection lost with {peer_id}: {e}")
        finally:
            self.remove_peer(peer_id)
            if peer_id in self.active_connections:
                del self.active_connections[peer_id]

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

    def get_peers_status(self) -> List[Dict[str, Any]]:
        """Return formatted status of all peers for UI."""
        status_list = []
        
        # Add self
        status_list.append({
            "id": self.node_id,
            "role": "local",
            "status": "active",
            "address": f"{self.host}:{self.port}",
            "reputation": 1.0, # Self is always trusted
            "last_seen": time.time()
        })
        
        # Add peers
        for peer in self.peers.values():
            status_list.append({
                "id": peer.node_id,
                "role": "peer",
                "status": "connected" if peer.node_id in self.active_connections else "known",
                "address": f"{peer.host}:{peer.port}",
                "reputation": peer.reputation,
                "last_seen": peer.last_seen
            })
            
        return status_list

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
