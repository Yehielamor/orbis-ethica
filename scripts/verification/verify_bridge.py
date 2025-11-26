import sys
import os
import asyncio
from typing import List
from uuid import uuid4

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.core.deliberation_engine import DeliberationEngine
from backend.core.ledger import LocalBlockchain, TokenTransaction, TransactionType
from backend.core.models import Proposal, ProposalCategory, ProposalDomain, ProposalStatus
from backend.entities.base import BaseEntity, EntityType
from backend.memory.graph import MemoryGraph

# Mock Entity
class MockEntity(BaseEntity):
    def evaluate_proposal(self, proposal):
        from backend.core.models.decision import EntityEvaluation
        from backend.core.models.ulfr import ULFRScore
        return EntityEvaluation(
            entity_id=self.entity.id, # Added required field
            entity_type=self.entity.type.value,
            vote=1, # Approve
            confidence=0.9,
            ulfr_score=ULFRScore(utility=0.9, life=0.9, fairness_penalty=0.0, rights_risk=0.0),
            reasoning="Looks good for the bridge test.",
            evidence_cited=[]
        )
        
    def get_system_prompt(self):
        return "You are a mock entity."

async def run_test():
    print("🧪 Testing The Bridge (Deliberation -> Ledger)...")
    
    # 1. Setup Components
    # Identity
    from backend.security.identity import NodeIdentity
    identity = NodeIdentity(node_id="test_node")
    
    # Ledger
    ledger = LocalBlockchain(identity=identity)
    print(f"   ⛓️  Ledger Initialized. Genesis: {ledger.get_latest_block().hash[:8]}")
    
    # Memory Graph
    memory_graph = MemoryGraph(ledger=ledger)
    
    # Entities
    from backend.core.models import Entity, EntityType
    mock_entity_model = Entity(
        name="Tester",
        type=EntityType.SEEKER,
        reputation=1.0,
        primary_focus="U",
        bias_description="None"
    )
    entities = [MockEntity(entity=mock_entity_model)]
    
    # Engine
    engine = DeliberationEngine(
        entities=entities,
        memory_graph=memory_graph
    )
    
    # 2. Create Proposal
    proposer_wallet = "0x1234567890abcdef1234567890abcdef" # Mock Wallet
    proposal = Proposal(
        id=str(uuid4()),
        title="Bridge Test Proposal",
        description="Testing if I get paid for this. This description needs to be at least 50 characters long to pass the Pydantic validation checks in the Proposal model.",
        category=ProposalCategory.ROUTINE,
        domain=ProposalDomain.TECHNOLOGY,
        submitter_id=proposer_wallet
    )
    
    print(f"   📝 Proposal Created by {proposer_wallet}")
    print(f"   💰 Initial Balance: {ledger.get_balance(proposer_wallet)}")
    
    # 3. Run Deliberation
    print("   ⚖️  Running Deliberation...")
    decision = engine.deliberate(proposal)
    
    print(f"   🏁 Outcome: {decision.outcome.value}")
    
    # 4. Verify Reward
    final_balance = ledger.get_balance(proposer_wallet)
    print(f"   💰 Final Balance: {final_balance}")
    
    if final_balance > 0:
        print(f"   ✅ SUCCESS: Reward received! (+{final_balance})")
    else:
        print("   ❌ FAILURE: No reward received.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_test())
