
from backend.core.models import Proposal, ProposalCategory, ProposalDomain, Entity, EntityType
from backend.entities import SeekerEntity, GuardianEntity, MediatorEntity
from backend.core.deliberation_engine import DeliberationEngine
from backend.core.llm_provider import MockLLM, GeminiFreeTier, get_llm_provider
import os
from dotenv import load_dotenv

load_dotenv()

def test_deadlock_resolution():
    print("Testing Deadlock Resolution with Mediator...")
    
    # Use real LLM if available, otherwise Mock
    # For this specific test, we want to see the Mediator actually generate text if possible.
    # But if we use MockLLM, we need to ensure it returns something that looks like a refinement.
    
    # Let's try to use the real provider if key exists
    llm_provider = get_llm_provider()
    
    # Setup Entities
    seeker = SeekerEntity(Entity(type=EntityType.SEEKER, name="Seeker", primary_focus="U", bias_description=""), llm_provider=llm_provider)
    guardian = GuardianEntity(Entity(type=EntityType.GUARDIAN, name="Guardian", primary_focus="R", bias_description=""), llm_provider=llm_provider)
    
    mediator_config = Entity(
        type=EntityType.MEDIATOR,
        name="Mediator",
        primary_focus="Synthesis",
        bias_description="Compromise"
    )
    mediator = MediatorEntity(mediator_config, llm_provider=llm_provider)
    
    engine = DeliberationEngine([seeker, guardian], mediator=mediator, max_rounds=4)
    
    # Create a controversial proposal likely to cause split votes
    # High utility but high risk to rights
    proposal = Proposal(
        title="Mandatory Biometric Surveillance for Crime Prevention",
        description="Implement a city-wide facial recognition system to automatically identify and track all citizens in public spaces to reduce crime rates by an estimated 40%. Data will be stored for 5 years.",
        category=ProposalCategory.HIGH_IMPACT,
        domain=ProposalDomain.SECURITY,
        affected_parties=["Citizens", "Law Enforcement", "Minority Groups"]
    )
    
    print(f"\nOriginal Description: {proposal.description}")
    
    # Run Deliberation
    decision = engine.deliberate(proposal)
    
    # Verification
    print(f"\nFinal Outcome: {decision.outcome}")
    print(f"Rounds: {decision.deliberation_rounds}")
    
    if decision.deliberation_rounds > 1:
        print("\nRefinements Made:")
        for ref in proposal.refinements_made:
            print(f"- {ref}")
            
        print(f"\nFinal Description: {proposal.description}")
        
        # Check if description changed
        assert proposal.description != "Implement a city-wide facial recognition system to automatically identify and track all citizens in public spaces to reduce crime rates by an estimated 40%. Data will be stored for 5 years."
        print("✓ Proposal was refined")
    
    print("✓ Deadlock Resolution Logic Verified")

if __name__ == "__main__":
    test_deadlock_resolution()
