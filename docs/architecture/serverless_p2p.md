# Orbis Ethica: Serverless P2P Architecture (True P2P)

## 1. Vision: The "Headless" Network
The goal is to eliminate reliance on central servers for node coordination. In this architecture, **Orbis Ethica** transforms from a client-server application into a purely peer-to-peer protocol. Every instance (whether running on a laptop, a cloud VM, or a browser) is an equal peer in the mesh.

## 2. Core Technologies

### 2.1 Transport Layer: Libp2p & WebRTC
To bypass NAT (Network Address Translation) and firewalls without central relays, we will adopt a hybrid transport strategy:
- **Desktop/Server Nodes (Python)**: Use **Libp2p** (via `libp2p-python`). This provides robust TCP/QUIC connections, DHT discovery, and pubsub.
- **Browser Nodes (JS)**: Use **WebRTC**. Browsers cannot open raw TCP ports. They will connect to the mesh via WebRTC, using other nodes as signaling relays.

### 2.2 Discovery: Kademlia DHT
Instead of a hardcoded list of `SEED_NODES` or a central directory:
- **Distributed Hash Table (DHT)**: Nodes form a Kademlia DHT. To find a peer (or a piece of data), a node queries the DHT.
- **Bootstrap Nodes**: We only need a few stable nodes (Bootstrap Nodes) for the *initial* entry into the network. Once connected, the node discovers others and no longer relies on the bootstrap node.

### 2.3 Communication: GossipSub
- **PubSub**: We will use **GossipSub** (a scalable pubsub protocol) for broadcasting blocks, transactions, and deliberation messages.
- **Topics**:
    - `/orbis/1.0.0/blocks`: Validated blocks.
    - `/orbis/1.0.0/tx`: Pending transactions/proposals.
    - `/orbis/1.0.0/deliberation`: Real-time AI debate messages.

## 3. Architecture Components

### 3.1 The "Switch" (Node Core)
The Python backend (`app.py`) currently acts as an API server. We will refactor it to become a **P2P Switch**.
- **Old Flow**: Frontend -> HTTP -> Backend -> HTTP -> Peer.
- **New Flow**: Frontend -> WebSocket (Local) -> Backend (Libp2p Host) -> Encrypted Tunnel -> Peer (Libp2p Host).

### 3.2 NAT Traversal (Hole Punching)
- **STUN Servers**: Public servers (like Google's) used only to discover our own public IP.
- **DCUtR (Direct Connection Upgrade through Relay)**: A protocol to establish direct connections between two NAT'd nodes using a third node as a temporary relay.

## 4. Implementation Stages

### Stage 1: The Hybrid Bridge (Current -> Libp2p)
*Objective: Replace custom WebSocket logic with Libp2p.*
1.  Install `libp2p` python library.
2.  Create a `Libp2pService` class that replaces `NodeManager`.
3.  Implement basic "Ping" and "Chat" over Libp2p.

### Stage 2: The DHT & Discovery
*Objective: Remove hardcoded peers.*
1.  Enable Kademlia DHT.
2.  Implement peer discovery logic.
3.  Visualize the DHT routing table in the Network UI.

### Stage 3: Browser Mesh (WebRTC)
*Objective: Allow browser-only nodes.*
1.  Implement WebRTC transport in the Python backend.
2.  Allow the Frontend to connect directly to other browsers (optional, advanced).

## 5. Security Implications
- **Identity**: We already use Ed25519. This is compatible with Libp2p PeerIDs.
- **Encryption**: Libp2p uses Noise/TLS 1.3 by default. All traffic is encrypted.
- **Anonymity**: Traffic is encrypted, but IP addresses are visible. (Tor/I2P support can be added later).

## 6. Migration Plan
We will start by implementing **Stage 1**: Replacing our custom `NodeManager` with a `Libp2p` host running inside our Python backend. This gives us immediate access to robust P2P features without rewriting the entire application.
