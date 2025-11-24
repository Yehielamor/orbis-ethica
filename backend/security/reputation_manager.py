"""
Reputation Manager - Handles staking and slashing of reputation.
"""

from typing import Dict, Optional
from ..core.models.entity import Entity

class ReputationManager:
    """
    Manages entity reputation, including staking and slashing mechanisms.
    """
    
    def __init__(self):
        self.stakes: Dict[str, float] = {}  # Map entity_id -> staked_amount

    def stake_reputation(self, entity: Entity, amount: float) -> bool:
        """
        Stake reputation for a high-stakes vote.
        
        Args:
            entity: The entity staking reputation
            amount: Amount to stake
            
        Returns:
            True if successful, False if insufficient reputation
        """
        if amount < 0:
            return False
            
        # Check if entity has enough free reputation
        # Free reputation = Total - Staked
        free_reputation = entity.reputation - entity.staked_reputation
        
        if free_reputation < amount:
            return False
            
        # Lock the stake
        entity.staked_reputation += amount
        return True

    def release_stake(self, entity: Entity, amount: float) -> bool:
        """
        Release staked reputation after successful/honest participation.
        """
        if entity.staked_reputation < amount:
            # Should not happen in normal operation
            entity.staked_reputation = 0.0
            return False
            
        entity.staked_reputation -= amount
        return True

    def slash_stake(self, entity: Entity, amount: float, reason: str) -> float:
        """
        Slash (burn) staked reputation due to malicious behavior.
        
        Args:
            entity: The entity to slash
            amount: Amount to slash (usually the staked amount)
            reason: Reason for slashing (for logging)
            
        Returns:
            New reputation score
        """
        # Reduce total reputation
        entity.reputation -= amount
        
        # Reduce staked amount (since it's now gone)
        entity.staked_reputation -= amount
        
        # Clamp to 0
        if entity.reputation < 0:
            entity.reputation = 0.0
        if entity.staked_reputation < 0:
            entity.staked_reputation = 0.0
            
        print(f"SLASHED entity {entity.name}: -{amount} reputation. Reason: {reason}")
        return entity.reputation

    def update_reputation(self, entity: Entity, performance: float, learning_rate: float = 0.1):
        """
        Update reputation based on performance (standard update).
        """
        entity.update_reputation(performance, learning_rate)
