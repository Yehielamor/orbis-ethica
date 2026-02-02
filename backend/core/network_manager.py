"""
Network Manager - True P2P Mesh Protocol (Satoshi Style).
Implements:
1. Peer Discovery (Recursive 'GetAddr')
2. Gossip Protocol (Viral Broadcast)
3. Handshake & Health Checks
"""
import asyncio
import logging
import random
import time
from typing import Any

import httpx

from .ledger import Ledger

import os

# Configuration
MAX_PEERS = 50          # Don't connect to the whole world
GOSSIP_FANOUT = 3       # Send to 3 random peers (Epidemic Algorithm)
PORT = int(os.getenv("PORT", 8000))             # Default port

logger = logging.getLogger("P2P")

class NodeInfo:
    def __init__(self, ip: str, port: int, last_seen: float = 0):
        self.ip = ip
        self.port = port
        self.last_seen = last_seen
        self.failed_attempts = 0

    @property
    def url(self):
        return f"http://{self.ip}:{self.port}"

    def __eq__(self, other):
        return self.url == other.url

    def __hash__(self):
        return hash(self.url)

class NetworkManager:
    def __init__(self, ledger: Ledger, my_ip: str, bootstrap_nodes: list[str]):
        self.ledger = ledger
        self.my_ip = my_ip
        self.my_url = f"http://{my_ip}:{PORT}"
        
        # Routing Table: The list of all known peers in the mesh
        self.known_peers: set[NodeInfo] = set()
        
        # Parse bootstrap nodes
        for node in bootstrap_nodes:
            if node and node != self.my_url:
                # Cleaning: remove protocol and trailing slashes
                clean_node = node.replace("http://", "").replace("https://", "").strip("/")
                
                # Split (handle port presence)
                if ":" in clean_node:
                    ip, port = clean_node.split(":") 
                    self.known_peers.add(NodeInfo(ip, int(port)))
                else:
                    self.known_peers.add(NodeInfo(clean_node, 8000))
        
        # Dependency Injection (Circular)
        self.shard_manager = None
        
    def set_shard_manager(self, manager):
        self.shard_manager = manager

    async def start(self):
        """Start the background P2P loops."""
        logger.info(f"🕸️ [NET] Starting P2P Node at {self.my_url}")
        asyncio.create_task(self._discovery_loop())
        asyncio.create_task(self._health_check_loop())

    # --- 1. DISCOVERY PROTOCOL (Find new friends) ---
    async def _discovery_loop(self):
        """Periodically ask peers: 'Who else do you know?'"""
        while True:
            # If I'm lonely, try bootstrap nodes specifically
            targets = list(self.known_peers)
            if not targets:
                logger.warning("🕸️ [NET] No peers! Waiting for connection...")
                await asyncio.sleep(5)
                continue

            # Pick a random peer to query
            peer = random.choice(targets)
            try:
                # ASK: "GetAddr" (Give me addresses)
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(f"{peer.url}/api/p2p/peers")
                    if resp.status_code == 200:
                        new_peers = resp.json()
                        self._merge_peers(new_peers)
            except Exception:
                pass # Fail silently, health check will handle it
            
            await asyncio.sleep(10) # Run every 10s

    def _merge_peers(self, new_list: list[str]):
        """Add new peers to my routing table."""
        for url in new_list:
            if url == self.my_url: continue # Don't talk to myself
            
            # Parse URL to NodeInfo
            try:
                clean = url.replace("http://", "").replace("/", "")
                ip, port = clean.split(":")
                new_node = NodeInfo(ip, int(port), time.time())
                
                # Check if we already know him
                if new_node not in self.known_peers:
                    logger.info(f"🔭 [NET] Discovered new peer: {url}")
                    self.known_peers.add(new_node)
            except:
                pass

    def add_peer(self, url: str):
        """Manually add a peer (e.g. via Handshake)."""
        try:
            if url == self.my_url: return
            clean = url.replace("http://", "").replace("/", "")
            ip, port = clean.split(":")
            new_node = NodeInfo(ip, int(port), time.time())
            self.known_peers.add(new_node)
            logger.info(f"🤝 [NET] Accepted active connection from: {url}")
        except Exception as e:
            logger.error(f"Failed to add peer {url}: {e}")

    async def _handshake_with_seeds(self):
        """Actively say hello to seeds."""
        print(f"👋 [NET] Initiating Handshake with {len(self.known_peers)} seeds...")
        async with httpx.AsyncClient(timeout=3.0) as client:
            # Create a snapshot list to avoid "Set changed size during iteration"
            seed_snapshot = list(self.known_peers)
            for seed in seed_snapshot: # Started with seeds
                try:
                    print(f"👉 [NET] Sending Handshake to {seed.url}")
                    resp = await client.post(f"{seed.url}/api/p2p/handshake", json={"url": self.my_url})
                    print(f"✅ [NET] Handshake response: {resp.status_code} {resp.text}")
                except Exception as e:
                    print(f"❌ [NET] Handshake failed with {seed.url}: {e}")
                    logger.error(f"❌ [NET] Handshake failed with {seed.url}: {e}")
                    pass
    
    # Update start to include handshake
    async def start(self):
        """Start the background P2P loops."""
        logger.info(f"🕸️ [NET] Starting P2P Node at {self.my_url}")
        
        # 0. Initial Handshake
        asyncio.create_task(self._handshake_with_seeds())
        
        asyncio.create_task(self._discovery_loop())
        asyncio.create_task(self._health_check_loop())
    async def broadcast_block(self, block_data: dict[str, Any]):
        """
        The 'Infection' logic. 
        I don't send to everyone. I send to 3 random peers.
        They will send to 3 others. 
        Mathematical proof shows this covers the whole network in log(N) steps.
        """
        active_peers = [p for p in self.known_peers if p.failed_attempts < 3]
        if not active_peers:
            logger.warning("🕸️ [NET] Mining successful, but no peers to broadcast to!")
            return

        # Fanout (GossipSub strategy)
        targets = random.sample(active_peers, min(GOSSIP_FANOUT, len(active_peers)))
        
        logger.info(f"🗣️ [GOSSIP] Whispering new block {block_data['index']} to {len(targets)} peers...")
        
        async with httpx.AsyncClient(timeout=3.0) as client:
            tasks = []
            for peer in targets:
                tasks.append(client.post(f"{peer.url}/api/p2p/receive_block", json=block_data))
            
            # Fire and forget
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_shard(self, shard_data: dict[str, Any]):
        """
        Tasks (Shards) are also gossiped to find a willing worker.
        """
        active_peers = [p for p in self.known_peers if p.failed_attempts < 3]
        if not active_peers:
            logger.warning("🕸️ [NET] No peers to broadcast shard to!")
            return

        targets = random.sample(active_peers, min(GOSSIP_FANOUT, len(active_peers)))
        logger.info(f"🧩 [GOSSIP] Broadcasting shard {shard_data['id'][:8]} to {len(targets)} peers...")
        
        async with httpx.AsyncClient(timeout=3.0) as client:
            tasks = []
            for peer in targets:
                tasks.append(client.post(f"{peer.url}/api/p2p/shard/process", json=shard_data))
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_result(self, result_data: dict[str, Any]):
        """
        Send result back to the originator (or gossip it back).
        For V1, we try to gossip back, but ideally we should send to specific origin.
        Since we don't have direct routing, we gossip.
        """
        active_peers = [p for p in self.known_peers if p.failed_attempts < 3]
        targets = random.sample(active_peers, min(GOSSIP_FANOUT, len(active_peers)))
        
        async with httpx.AsyncClient(timeout=3.0) as client:
            tasks = []
            for peer in targets:
                tasks.append(client.post(f"{peer.url}/api/p2p/shard/result", json=result_data))
            await asyncio.gather(*tasks, return_exceptions=True)

    # --- 3. SYNC LOGIC (Longest Chain Rule) ---
    async def sync_chain(self):
        """Ask everyone for their height, download from the winner."""
        best_height = self.ledger.get_chain_height()
        best_peer = None

        active_peers = [p for p in self.known_peers]
        if not active_peers: return

        async with httpx.AsyncClient(timeout=2.0) as client:
            for peer in active_peers:
                try:
                    resp = await client.get(f"{peer.url}/api/stats")
                    if resp.status_code == 200:
                        remote_height = resp.json().get("chain_height", 0)
                        peer.last_seen = time.time()
                        
                        if remote_height > best_height:
                            best_height = remote_height
                            best_peer = peer
                except:
                    peer.failed_attempts += 1

        if best_peer:
            logger.info(f"🔄 [SYNC] Found longer chain ({best_height}) at {best_peer.url}. Downloading...")
            # Here we would trigger the download logic
            # await self._download_blocks(best_peer, start_index=self.ledger.get_chain_height())

    # --- 4. HEALTH CHECK (Garbage Collection) ---
    async def _health_check_loop(self):
        """Remove dead peers so we don't waste gossip."""
        while True:
            # Remove peers that failed too many times
            dead_peers = {p for p in self.known_peers if p.failed_attempts >= 5}
            if dead_peers:
                logger.info(f"💀 [NET] Pruning {len(dead_peers)} dead peers.")
                self.known_peers -= dead_peers
            await asyncio.sleep(60)
            
    def get_known_peers_urls(self) -> list[str]:
        return [p.url for p in self.known_peers]