import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import ConfigManager
from backend.core.deliberation_engine import DeliberationEngine
from backend.core.models import Proposal, ProposalCategory, ProposalDomain, DecisionOutcome
from backend.entities.base import BaseEntity, EntityType
from backend.core.models.entity import Entity

# Mock Entity for testing
class MockEntity(BaseEntity):
    def __init__(self, name, reputation, vote_val):
        model = Entity(
            name=name, 
            type=EntityType.SEEKER, 
            reputation=reputation,
            primary_focus="U",
            bias_description="None"
        )
        super().__init__(model, None)
        self.vote_val = vote_val

    def evaluate_proposal(self, proposal):
        from backend.core.models.decision import EntityEvaluation
        from backend.core.models.ulfr import ULFRScore
        return EntityEvaluation(
            entity_id=str(self.entity.id),
            entity_type=self.entity.name,
            vote=self.vote_val,
            confidence=1.0,
            ulfr_score=ULFRScore(utility=1.0, life=1.0, fairness_penalty=0.0, rights_risk=0.0), # High score
            reasoning="Mock reasoning"
        )
    
    def get_system_prompt(self):
        return ""

def test_governance():
    print("🗳️  Starting Governance Verification...")
    
    # 1. Setup Config Manager
    config_path = "test_system_config.json"
    if os.path.exists(config_path):
        os.remove(config_path)
        
    config_manager = ConfigManager(config_path=config_path)
    initial_weights = config_manager.get_config().ulfr_weights
    print(f"\n🔹 Initial Weights: U={initial_weights.alpha}, L={initial_weights.beta}")
    
    # 2. Setup Engine with Mock Entities (All voting YES)
    entities = [
        MockEntity("Voter 1", 1.0, 1),
        MockEntity("Voter 2", 1.0, 1),
        MockEntity("Voter 3", 1.0, 1)
    ]
    
    engine = DeliberationEngine(
        entities=entities,
        config_manager=config_manager
    )
    
    # 3. Create Constitutional Proposal
    new_weights = {"alpha": 0.5, "beta": 0.2, "gamma": 0.2, "delta": 0.1}
    
    proposal = Proposal(
        title="Constitutional Amendment: Prioritize Utility",
        description="This proposal changes the system weights to prioritize Utility (alpha=0.5).",
        category=ProposalCategory.CONSTITUTIONAL,
        domain=ProposalDomain.OTHER,
        context={
            "parameter_change": {
                "parameter": "ulfr_weights",
                "value": new_weights
            }
        }
    )
    
    print(f"\n🔹 Submitting Proposal: {proposal.title}")
    print(f"   Target Change: {new_weights}")
    
    # 4. Run Deliberation
    decision = engine.deliberate(proposal)
    
    print(f"\n🔹 Verdict: {decision.outcome.value}")
    
    # 5. Verify Config Update
    updated_config = config_manager.get_config()
    updated_weights = updated_config.ulfr_weights
    
    print(f"\n🔹 Updated Weights: U={updated_weights.alpha}, L={updated_weights.beta}")
    
    if updated_weights.alpha == 0.5 and decision.outcome == DecisionOutcome.APPROVED:
        print("   ✅ Governance Update Successful!")
    else:
        print("   ❌ Governance Update Failed!")
        
    # Cleanup
    if os.path.exists(config_path):
        os.remove(config_path)

if __name__ == "__main__":
    test_governance()
