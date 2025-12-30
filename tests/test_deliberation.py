import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.core.models import Proposal, ProposalCategory, ProposalDomain, Entity, EntityType
from backend.entities.seeker import SeekerEntity
from backend.entities.guardian import GuardianEntity
from backend.core.llm_provider import MockLLM
from backend.core.deliberation_engine import DeliberationEngine
from backend.memory.graph import MemoryGraph

def test_deliberation_engine():
    print("Testing Deliberation Engine...")
    
    # Setup
    mock_llm = MockLLM()
    
    seeker = SeekerEntity(Entity(type=EntityType.SEEKER, name="Seeker", primary_focus="U", bias_description=""), llm_provider=mock_llm)
    guardian = GuardianEntity(Entity(type=EntityType.GUARDIAN, name="Guardian", primary_focus="R", bias_description=""), llm_provider=mock_llm)
    
    memory = MemoryGraph()
    engine = DeliberationEngine([seeker, guardian], memory_graph=memory)
    
    proposal = Proposal(
        title="Test Proposal",
        description="A test proposal with sufficient length to pass the validation requirements of the Proposal model. This needs to be at least 50 characters long.",
        category=ProposalCategory.ROUTINE,
        domain=ProposalDomain.TECHNOLOGY
    )
    
    # Run Deliberation
    decision = engine.deliberate(proposal)
    
    # Verify Decision
    print(f"Final Outcome: {decision.outcome}")
    assert decision.deliberation_rounds >= 1
    
    # Verify Memory
    print("\nVerifying Memory Graph:")
    assert len(memory.nodes) >= 2 # Proposal + at least 1 round/verdict
    
    # Visualize
    # Get the last node added (likely the verdict)
    last_node_id = list(memory.nodes.keys())[-1]
    print(memory.visualize_trail(last_node_id))
    
    print("✓ Deliberation Engine Logic Verified")

if __name__ == "__main__":
    test_deliberation_engine()
