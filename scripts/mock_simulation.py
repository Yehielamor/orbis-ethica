
import time
import random
from typing import List, Dict, Any

# Mock classes to simulate the real system
class MockProposal:
    def __init__(self, title, description):
        self.title = title
        self.description = description
        self.status = "DRAFT"

class MockEntity:
    def __init__(self, name, role, bias_towards):
        self.name = name
        self.role = role
        self.bias_towards = bias_towards # 'utility', 'life', 'rights'

    def evaluate(self, proposal):
        print(f"\n🤖 {self.name} ({self.role}) is thinking...")
        time.sleep(1) # Simulate thinking
        
        # Simulate decision logic based on bias
        score = 0.0
        vote = 0
        reasoning = ""
        
        if self.bias_towards == 'utility':
            score = 0.85
            vote = 1
            reasoning = "This maximizes efficiency and output. The numbers look great."
        elif self.bias_towards == 'life':
            score = 0.40
            vote = -1
            reasoning = "It's efficient, but it puts vulnerable people at risk. I cannot support this."
        elif self.bias_towards == 'rights':
            score = 0.60
            vote = 0 # Abstain
            reasoning = "I see the benefits, but I'm worried about privacy violations."
            
        return {
            "vote": vote,
            "score": score,
            "reasoning": reasoning
        }

def run_simulation():
    print("🚀 INITIALIZING ORBIS ETHICA SIMULATION...")
    print("------------------------------------------")
    
    # 1. Create Proposal
    proposal = MockProposal(
        "AI Triage System", 
        "Use AI to allocate ICU beds based on survival probability."
    )
    print(f"📄 PROPOSAL SUBMITTED: {proposal.title}")
    print(f"📝 DESCRIPTION: {proposal.description}")
    
    # 2. Initialize Entities
    entities = [
        MockEntity("SEEKER", "Utility Maximizer", "utility"),
        MockEntity("HEALER", "Harm Reducer", "life"),
        MockEntity("GUARDIAN", "Rights Protector", "rights")
    ]
    
    # 3. Deliberation Round 1
    print("\n⚖️  STARTING DELIBERATION ROUND 1")
    print("---------------------------------")
    
    votes = []
    for entity in entities:
        eval_result = entity.evaluate(proposal)
        print(f"   Vote: {eval_result['vote']} | Score: {eval_result['score']}")
        print(f"   Reasoning: {eval_result['reasoning']}")
        votes.append(eval_result['vote'])
        
    # 4. Consensus Check
    print("\n📊 CALCULATING CONSENSUS...")
    time.sleep(1)
    
    total_score = sum(votes)
    if total_score > 1:
        print("\n✅ RESULT: APPROVED")
    elif total_score < -1:
        print("\n❌ RESULT: REJECTED")
    else:
        print("\n🔄 RESULT: NO CONSENSUS - REFINEMENT NEEDED")
        print("   (The Mediator would now step in to propose changes...)")

if __name__ == "__main__":
    run_simulation()
