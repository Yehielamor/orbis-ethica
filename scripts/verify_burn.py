import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.ledger import LocalBlockchain
from backend.security.reputation_manager import ReputationManager
from backend.security.burn.protocol import BurnProtocol
from backend.security.burn.models import BurnOffenseType
from backend.core.models.entity import Entity, EntityType

def test_burn_protocol():
    print("🔥 Starting Burn Protocol Verification...")
    
    # 1. Setup Components
    ledger = LocalBlockchain()
    reputation_manager = ReputationManager()
    
    # 2. Create Mock Entity
    mock_entity = Entity(
        name="Malicious Actor",
        type=EntityType.SEEKER,
        reputation=0.95,
        primary_focus="Chaos",
        bias_description="None"
    )
    # Simulate staking
    reputation_manager.stake_reputation(mock_entity, 0.5)
    
    print(f"\n🔹 Target Entity: {mock_entity.name}")
    print(f"   ID: {mock_entity.id}")
    print(f"   Reputation: {mock_entity.reputation}")
    print(f"   Staked: {mock_entity.staked_reputation}")
    
    # 3. Initialize Burn Protocol
    entity_lookup = {str(mock_entity.id): mock_entity}
    burn_protocol = BurnProtocol(
        reputation_manager=reputation_manager,
        ledger=ledger,
        entity_lookup=entity_lookup
    )
    
    # 4. Execute Burn
    print("\n🔹 Executing Burn...")
    event = burn_protocol.execute_burn(
        perpetrator_id=str(mock_entity.id),
        offense=BurnOffenseType.SIGNATURE_MISMATCH,
        description="Tampered with ledger block hash",
        evidence={"block_index": 5, "expected": "abc", "actual": "xyz"},
        council_vote=1.0
    )
    
    # 5. Verify Results
    print("\n🔹 Verifying Results...")
    
    # Check Reputation
    if mock_entity.reputation == 0.0 and mock_entity.staked_reputation == 0.0:
        print("   ✅ Reputation Slashed to 0.0")
    else:
        print(f"   ❌ Reputation Check Failed: {mock_entity.reputation}")
        
    # Check Ledger
    latest_block = ledger.get_latest_block()
    if latest_block.data.get('type') == 'BURN_EVENT' and latest_block.data.get('perpetrator') == str(mock_entity.id):
        print(f"   ✅ Burn Event Anchored in Ledger (Block #{latest_block.index})")
    else:
        print("   ❌ Ledger Check Failed")
        print(f"   Latest Block Data: {latest_block.data}")

if __name__ == "__main__":
    test_burn_protocol()
