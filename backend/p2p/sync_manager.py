import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.ledger import Ledger
from .node_manager import NodeManager

logger = logging.getLogger(__name__)

class SyncManager:
    """
    Manages blockchain synchronization between peers.
    Implements Longest Chain Rule.
    """
    def __init__(self, ledger: Ledger, node_manager: NodeManager):
        self.ledger = ledger
        self.node_manager = node_manager
        self.is_syncing = False
        
    async def start_sync_loop(self, interval: int = 60):
        """Periodically check for longer chains."""
        while True:
            try:
                await self.sync_with_peers()
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
            await asyncio.sleep(interval)
            
    async def sync_with_peers(self):
        """Query peers for their chain height and sync if needed."""
        if self.is_syncing:
            return
            
        self.is_syncing = True
        try:
            peers = self.node_manager.get_known_peers()
            if not peers:
                return

            my_latest = self.ledger.get_latest_block()
            my_height = my_latest.index if my_latest else 0
            
            logger.info(f"🔄 Sync Check: My Height = {my_height}. Peers: {len(peers)}")
            
            # Ask for their latest block to compare height
            # In a real implementation, we'd send a specific message.
            # Here we simulate the logic:
            for peer in peers:
                # 1. Request latest block (simulated via direct API call or message)
                # In P2P, we'd send MessageType.GET_STATUS
                pass 
                
        except Exception as e:
            logger.error(f"Sync error: {e}")
        finally:
            self.is_syncing = False 
                
    async def handle_chain_response(self, chain_data: List[Dict[str, Any]]):
        """
        Handle a received chain from a peer.
        Implements Longest Chain Rule.
        """
        if not chain_data:
            return

        # 1. Validate the chain structure
        # Check links (prev_hash) and signatures
        if not self._validate_chain(chain_data):
            logger.warning("❌ Received invalid chain from peer")
            return

        # 2. Compare length
        my_latest = self.ledger.get_latest_block()
        my_height = my_latest.index if my_latest else -1
        peer_height = chain_data[-1]['index']

        if peer_height > my_height:
            logger.info(f"🔗 Found longer chain! My height: {my_height}, Peer height: {peer_height}")
            if self._replace_chain(chain_data):
                logger.info("✅ Chain replaced successfully!")
            else:
                logger.error("❌ Failed to replace chain")
        else:
            logger.info("🔗 Received chain is not longer. Ignoring.")

    def _validate_chain(self, chain: List[Dict[str, Any]]) -> bool:
        """Validate an entire chain of blocks."""
        # 1. Check Genesis (Index 0) - For now, just check index
        if chain[0]['index'] != 0:
            return False
            
        # 2. Check links
        for i in range(1, len(chain)):
            current = chain[i]
            prev = chain[i-1]
            
            if current['previous_hash'] != prev['hash']:
                return False
                
            # 3. Verify individual block (hash, signature)
            if not self.ledger.validate_block(current):
                return False
                
        return True

    def _replace_chain(self, new_chain: List[Dict[str, Any]]) -> bool:
        """
        Atomically replace the local chain with the new one.
        WARNING: This is a destructive operation!
        """
        session = self.ledger.db_manager.get_session()
        try:
            from ..core.models.sql_models import BlockModel, LedgerEntryModel
            
            # 1. Clear existing blocks (and unlink transactions)
            # In a real system, we might keep orphaned blocks or handle re-orgs more gracefully.
            # Here we just wipe and rewrite for MVP.
            
            # Unlink all txs first
            session.query(LedgerEntryModel).update({LedgerEntryModel.block_hash: None})
            
            # Delete all blocks
            session.query(BlockModel).delete()
            
            # 2. Insert new blocks
            for block_data in new_chain:
                block = BlockModel(
                    index=block_data['index'],
                    hash=block_data['hash'],
                    previous_hash=block_data['previous_hash'],
                    timestamp=datetime.fromisoformat(block_data['timestamp']),
                    validator_id=block_data['validator_id'],
                    signature=block_data['signature']
                )
                session.add(block)
                
                # Note: We are NOT syncing the transactions themselves here for simplicity.
                # In a real system, we would need to fetch the txs for each block too.
                # For this MVP, we assume the nodes share the same tx pool or we sync txs separately.
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Chain replacement failed: {e}")
            return False
        finally:
            session.close()
