from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import time

class MessageType(str, Enum):
    HANDSHAKE = "HANDSHAKE"
    HANDSHAKE_ACK = "HANDSHAKE_ACK"
    GOSSIP_BLOCK = "GOSSIP_BLOCK"
    GOSSIP_TX = "GOSSIP_TX"
    SYNC_REQUEST = "SYNC_REQUEST"
    SYNC_RESPONSE = "SYNC_RESPONSE"
    PEER_DISCOVERY = "PEER_DISCOVERY"

class PeerInfo(BaseModel):
    """Information about a peer node."""
    node_id: str
    host: str
    port: int
    first_seen: float = Field(default_factory=time.time) # Added first_seen with default
    last_seen: float = Field(default_factory=time.time) # Retained default_factory for last_seen
    reputation: float = 0.5 # Default neutral reputation

class P2PMessage(BaseModel):
    """Standard P2P message envelope."""
    type: MessageType
    sender_id: str
    payload: Dict[str, Any]
    timestamp: float = Field(default_factory=time.time)
    signature: Optional[str] = None  # For future cryptographic verification
