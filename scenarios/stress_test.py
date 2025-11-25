"""
Stress Test Scenario
Runs a high volume of deliberation rounds to test system stability and performance.
Uses Mock LLM to avoid API costs/rate limits.
"""

import sys
import os
import time
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.models.proposal import Proposal, ProposalCategory, ProposalDomain
from backend.core.deliberation_engine import DeliberationEngine
from backend.entities.seeker import SeekerEntity
from backend.entities.guardian import GuardianEntity
from backend.entities.arbiter import ArbiterEntity
from backend.core.models.entity import Entity, EntityType
from backend.core.llm_provider import MockLLMProvider

def run_stress_test(rounds=100):
    print("\n" + "="*60)
    print(f"⚡ SCENARIO: STRESS TEST ({rounds} ROUNDS)")
    print("="*60)

    # 1. Setup (Lightweight)
    llm = MockLLMProvider()
    
    entities = [
        SeekerEntity(Entity(name="Seeker", type=EntityType.SEEKER, reputation=1.0), llm),
        GuardianEntity(Entity(name="Guardian", type=EntityType.GUARDIAN, reputation=1.0), llm),
        ArbiterEntity(Entity(name="Arbiter", type=EntityType.ARBITER, reputation=1.0), llm)
    ]
    
    engine = DeliberationEngine(entities)
    
    print(f"   👥 Entities: {len(entities)}")
    print(f"   🤖 LLM: MockProvider (Fast)")

    start_time = time.time()
    success_count = 0
    
    # 2. The Loop
    for i in range(1, rounds + 1):
        # Generate random proposal
        proposal = Proposal(
            title=f"Stress Test Proposal #{i}",
            description="Automated stress test payload.",
            category=random.choice(list(ProposalCategory)),
            domain=random.choice(list(ProposalDomain)),
            affected_parties=["System"],
            submitter_id=f"tester_{i}"
        )
        
        try:
            # Run deliberation (simplified, no streaming)
            # We just want to trigger the logic
            decision = engine.deliberate(proposal)
            
            sys.stdout.write(f"\r   🔄 Round {i}/{rounds}: {decision.outcome.value} (Score: {decision.weighted_vote:.2f})")
            sys.stdout.flush()
            success_count += 1
            
        except Exception as e:
            print(f"\n   ❌ Round {i} Failed: {e}")

    end_time = time.time()
    duration = end_time - start_time
    avg_time = duration / rounds

    print(f"\n\n📊 RESULTS:")
    print(f"   ✅ Successful Rounds: {success_count}/{rounds}")
    print(f"   ⏱️  Total Time: {duration:.2f}s")
    print(f"   ⚡ Average Latency: {avg_time*1000:.2f}ms per round")
    
    if success_count == rounds:
        print("\n✅ STRESS TEST PASSED")
    else:
        print("\n⚠️  STRESS TEST COMPLETED WITH ERRORS")

if __name__ == "__main__":
    run_stress_test(100)
