
from backend.core.models import Proposal, ProposalCategory, ProposalDomain, Entity, EntityType
from backend.entities.seeker import SeekerEntity
from backend.core.llm_provider import MockLLM

def test_generative_entity():
    print("Testing Generative Entity (Seeker)...")
    
    # Setup
    entity_config = Entity(
        type=EntityType.SEEKER,
        name="TestSeeker",
        primary_focus="U",
        bias_description="None"
    )
    
    # Use MockLLM directly
    mock_llm = MockLLM()
    seeker = SeekerEntity(entity_config, llm_provider=mock_llm)
    
    proposal = Proposal(
        title="Test Proposal",
        description="A test proposal with sufficient length to pass the validation requirements of the Proposal model. This needs to be at least 50 characters long.",
        category=ProposalCategory.ROUTINE,
        domain=ProposalDomain.TECHNOLOGY
    )
    
    # Evaluate
    evaluation = seeker.evaluate_proposal(proposal)
    
    print(f"Vote: {evaluation.vote}")
    print(f"ULFR: U={evaluation.ulfr_score.utility}")
    print(f"Reasoning: {evaluation.reasoning}")
    
    assert evaluation.vote == 1, "Should be APPROVE (1)"
    assert evaluation.ulfr_score.utility == 0.8, "Utility should be 0.8"
    assert "Mock reasoning" in evaluation.reasoning, "Reasoning should match mock"
    
    print("✓ Generative Entity Logic Verified")

if __name__ == "__main__":
    test_generative_entity()
