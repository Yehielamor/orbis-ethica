
import pytest
from unittest.mock import MagicMock
from backend.knowledge.models import RawKnowledge
from backend.knowledge.gateway import KnowledgeGateway
from backend.core.models import Proposal, ProposalCategory, ProposalDomain
from backend.entities.seeker import SeekerEntity
from backend.core.models import Entity, EntityType

def test_knowledge_to_seeker_flow():
    # 1. Setup Knowledge Gateway
    gateway = KnowledgeGateway(verified_sources=["ScienceJournal"])
    
    # 2. Process Raw Knowledge
    content = "Solar energy reduces carbon emissions by 90%."
    raw = RawKnowledge(
        content=content,
        source_id="ScienceJournal",
        signature=f"SIG_{content[::-1]}"
    )
    verified_knowledge = gateway.process_knowledge(raw)
    
    # 3. Create Proposal with Verified Evidence
    proposal = Proposal(
        title="Solar Panel Initiative",
        description="Install solar panels on all government buildings.",
        category=ProposalCategory.HIGH_IMPACT,
        domain=ProposalDomain.ENVIRONMENT,
        evidence=[verified_knowledge]
    )
    
    # 4. Setup Seeker Entity
    entity_config = Entity(
        id="SEEKER-01",
        name="Seeker",
        type=EntityType.SEEKER,
        model_provider="openai", # Mocked anyway
        model_name="gpt-4"
    )
    seeker = SeekerEntity(entity_config)
    
    # Mock the LLM call to inspect the prompt
    seeker._call_llm = MagicMock(return_value="""
ULFR SCORES:
U: 0.9
L: 0.8
F_penalty: 0.1
R_risk: 0.1
VOTE: APPROVE
CONFIDENCE: 0.9
REASONING: Evidence supports high utility.
    """)
    
    # 5. Execute Evaluation
    seeker.evaluate_proposal(proposal)
    
    # 6. Verify Prompt Content
    call_args = seeker._call_llm.call_args[0][0]
    print("\n[PROMPT SENT TO LLM]:")
    print(call_args)
    
    assert "VERIFIED EVIDENCE" in call_args
    assert "Solar energy reduces carbon emissions" in call_args
    assert "Source: ScienceJournal" in call_args
    
    print("\n✅ SUCCESS: Seeker received the verified evidence!")

if __name__ == "__main__":
    test_knowledge_to_seeker_flow()
