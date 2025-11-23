
import pytest
from typing import Dict, Any
from backend.security.burn.protocol import BurnProtocol
from backend.security.burn.models import BurnOffenseType
from backend.core.interfaces import ReputationManager

# 1. Mock Reputation Manager (Implementing the Interface)
class MockReputationManager:
    def __init__(self):
        self.entities = {
            "CorruptSeeker": {"reputation": 0.95, "quarantined": False}
        }

    def get_entity(self, entity_id):
        return self.entities.get(entity_id)

    def burn_reputation(self, entity_id: str) -> None:
        if entity_id in self.entities:
            self.entities[entity_id]["reputation"] = 0.0
            print(f"[MOCK] Burned reputation for {entity_id}")

    def quarantine_entity(self, entity_id: str) -> None:
        if entity_id in self.entities:
            self.entities[entity_id]["quarantined"] = True
            print(f"[MOCK] Quarantined {entity_id}")

# 2. The Test Case
def test_corrupt_seeker_burn_flow():
    # Setup
    reputation_manager = MockReputationManager()
    protocol = BurnProtocol(reputation_manager=reputation_manager, log_path="test_burn_ledger.json")
    entity_id = "CorruptSeeker"

    print(f"\n[INIT] Entity {entity_id} Reputation: {reputation_manager.get_entity(entity_id)['reputation']}")

    # Step 1: Simulate Action (Attempt to inject data)
    has_valid_signature = False
    
    if not has_valid_signature:
        print(f"[ALERT] Signature Mismatch detected for {entity_id}!")
        
        # Step 2: Trigger Burn Protocol
        protocol.execute_burn(
            perpetrator_id=entity_id,
            offense=BurnOffenseType.SIGNATURE_MISMATCH,
            description="Attempted to inject unsigned data block.",
            evidence={"signature": "INVALID", "block_id": "BLK-999"},
            council_vote=0.99
        )

    # Step 3: Verify Reputation is 0
    entity_after = reputation_manager.get_entity(entity_id)
    assert entity_after["reputation"] == 0.0, "Reputation should be 0.0"
    assert entity_after["quarantined"] is True, "Entity should be quarantined"
    print(f"[VERIFIED] Entity Reputation is now: {entity_after['reputation']}")
    print(f"[VERIFIED] Entity Quarantined: {entity_after['quarantined']}")

    # Step 4: Verify Access Denied
    can_vote = not entity_after["quarantined"] and entity_after["reputation"] > 0.1
    
    if not can_vote:
        print("[SUCCESS] Access Denied for voting.")
    else:
        pytest.fail("Corrupt entity was allowed to vote!")
    
    assert can_vote is False

if __name__ == "__main__":
    test_corrupt_seeker_burn_flow()
