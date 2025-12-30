import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.core.models.entity import Entity, EntityType
from backend.security.reputation_manager import ReputationManager

def test_reputation_manager():
    print("Testing Reputation Manager...")
    
    # Setup
    manager = ReputationManager()
    entity = Entity(
        type=EntityType.SEEKER,
        name="TestSeeker",
        reputation=0.8,
        primary_focus="U",
        bias_description="None"
    )
    
    # Test 1: Staking
    print(f"Initial Reputation: {entity.reputation}, Staked: {entity.staked_reputation}")
    success = manager.stake_reputation(entity, 0.2)
    assert success, "Staking should succeed"
    assert entity.staked_reputation == 0.2, "Staked amount should be 0.2"
    print(f"After Staking 0.2: {entity.reputation}, Staked: {entity.staked_reputation}")
    
    # Test 2: Slashing
    new_rep = manager.slash_stake(entity, 0.2, "Malicious voting")
    assert abs(new_rep - 0.6) < 0.0001, f"Reputation should be ~0.6, got {new_rep}"
    assert entity.staked_reputation == 0.0, "Staked amount should be reset"
    print(f"After Slashing: {entity.reputation}, Staked: {entity.staked_reputation}")
    
    print("✓ Reputation Manager Logic Verified")

if __name__ == "__main__":
    test_reputation_manager()
