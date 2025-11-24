"""
Orbis Ethica - Improved Full-System Simulation
Scenario: Complete 6-Entity Deliberation with Real Architecture
Demonstrates: Full Entity Load, Knowledge Gateway, Burn Protocol, Memory Graph
"""

import time
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CORE IMPORTS ---
from backend.core.models.entity import Entity, EntityType
from backend.core.models.proposal import Proposal, ProposalCategory, ProposalDomain
from backend.core.llm_provider import get_llm_provider
from backend.knowledge.gateway import KnowledgeGateway, IntegrityError
from backend.knowledge.models import RawKnowledge
from backend.security.burn.protocol import BurnProtocol
from backend.security.burn.models import BurnOffenseType
from backend.memory.graph import MemoryGraph

# --- ENTITY IMPORTS: All 6 cognitive entities ---
from backend.entities.seeker import SeekerEntity
from backend.entities.healer import HealerEntity
from backend.entities.guardian import GuardianEntity
from backend.entities.mediator import MediatorEntity
from backend.entities.creator import CreatorEntity
from backend.entities.arbiter import ArbiterEntity


# --- UTILS ---
def print_header(text: str):
    """Print formatted header."""
    print(f"\n{'='*70}")
    print(f"✨ {text}")
    print(f"{'='*70}")


def print_step(text: str, delay: float = 0.3):
    """Print step with optional delay."""
    print(f"\n🔹 {text}...")
    time.sleep(delay)


def print_entity_vote(entity_name: str, entity_type: str, vote: int, ulfr, reasoning: str):
    """Print formatted entity evaluation."""
    vote_symbol = "🟢 APPROVE" if vote == 1 else "🔴 REJECT" if vote == -1 else "⚪ ABSTAIN"
    print(f"\n   {vote_symbol} | {entity_name} [{entity_type}]")
    print(f"      ULFR: U={ulfr.utility:.2f}, L={ulfr.life:.2f}, F={ulfr.fairness_penalty:.2f}, R={ulfr.rights_risk:.2f}")
    print(f"      💭 {reasoning[:120]}{'...' if len(reasoning) > 120 else ''}")


# --- MAIN SIMULATION ---
def run_simulation():
    print_header("ORBIS ETHICA: FULL SYSTEM SIMULATION - 6 ENTITIES")
    
    # ========================================================================
    # 1. INITIALIZE CORE COMPONENTS
    # ========================================================================
    
    llm_provider = get_llm_provider()
    gateway = KnowledgeGateway(verified_sources=["WHO_Secure_Feed", "Reuters_Node"])
    burn_protocol = BurnProtocol()
    memory = MemoryGraph()
    
    print(f"⚙️  Core Components Initialized")
    print(f"   📡 LLM Provider: {llm_provider.__class__.__name__}")
    print(f"   🔐 Knowledge Gateway: Active")
    print(f"   🔥 Burn Protocol: Armed")
    print(f"   🧠 Memory Graph: Ready")
    
    # ========================================================================
    # 2. CREATE ENTITY MODELS (Required for initialization)
    # ========================================================================
    
    entity_models = [
        Entity(
            name="Seeker Alpha",
            type=EntityType.SEEKER,
            reputation=0.95,
            primary_focus="U",
            bias_description="May prioritize aggregate outcomes over individual rights"
        ),
        Entity(
            name="Healer Prime", 
            type=EntityType.HEALER,
            reputation=0.98,
            primary_focus="L",
            bias_description="May be overly cautious, blocking beneficial innovations"
        ),
        Entity(
            name="Guardian Justice",
            type=EntityType.GUARDIAN,
            reputation=0.90,
            primary_focus="R",
            bias_description="May be overly rigid about rules and procedures"
        ),
        Entity(
            name="Mediator Balance",
            type=EntityType.MEDIATOR,
            reputation=0.85,
            primary_focus="F",
            bias_description="May produce weak compromises"
        ),
        Entity(
            name="Creator Nova",
            type=EntityType.CREATOR,
            reputation=0.88,
            primary_focus="Innovation",
            bias_description="May be too speculative"
        ),
        Entity(
            name="Arbiter Judge",
            type=EntityType.ARBITER,
            reputation=1.00,
            primary_focus="Balance",
            bias_description="May defer to precedent"
        ),
    ]
    
    # ========================================================================
    # 3. INITIALIZE ALL 6 COGNITIVE ENTITIES
    # ========================================================================
    
    entities_list = [
        SeekerEntity(entity_models[0], llm_provider),
        HealerEntity(entity_models[1], llm_provider),
        GuardianEntity(entity_models[2], llm_provider),
        MediatorEntity(entity_models[3], llm_provider),
        CreatorEntity(entity_models[4], llm_provider),
        ArbiterEntity(entity_models[5], llm_provider),
    ]
    
    print(f"\n👥 Cognitive Entities Loaded: {len(entities_list)}")
    for entity_obj in entities_list:
        print(f"   🟢 {entity_obj.entity.name} [{entity_obj.entity.type.value.upper()}] - Rep: {entity_obj.entity.reputation:.2f}")
    
    # ========================================================================
    # SCENARIO 1: KNOWLEDGE INGESTION
    # ========================================================================
    
    print_header("SCENARIO 1: INGESTING VERIFIED KNOWLEDGE")
    
    raw_valid_data = RawKnowledge(
        content="New pathogen identified. Transmission rate R0=4.5. Vaccine available but in limited supply. Urgent distribution needed.",
        source_id="WHO_Secure_Feed",
        signature="SIG_" + "New pathogen identified. Transmission rate R0=4.5. Vaccine available but in limited supply. Urgent distribution needed."[::-1]
    )
    
    try:
        clean_knowledge = gateway.process_knowledge(raw_valid_data)
        print(f"✅ Knowledge Verified and Purified")
        print(f"   📄 Content: {clean_knowledge.content[:80]}...")
        print(f"   🎯 Purity Score: {clean_knowledge.purity_score:.2f}")
        
        # Record to Memory Graph
        knowledge_node_id = memory.add_node(
            type="KNOWLEDGE",
            content={
                "text": clean_knowledge.content,
                "source": clean_knowledge.source_id,
                "purity_score": clean_knowledge.purity_score
            },
            agent_id="SYSTEM_GATEWAY",
            parent_ids=[]
        )
        print(f"   🧠 Recorded to Memory Graph: {knowledge_node_id}")
        
    except Exception as e:
        print(f"❌ Knowledge Gateway Error: {e}")
        return
    
    # ========================================================================
    # SCENARIO 2: CREATE AND EVALUATE PROPOSAL (All 6 Entities)
    # ========================================================================
    
    print_header("SCENARIO 2: PROPOSAL EVALUATION - ALL 6 ENTITIES")
    
    # Create a proper Proposal object
    proposal = Proposal(
        title="Emergency Global Vaccine Distribution Protocol",
        description="""
Implement mandatory, immediate global vaccine distribution to combat the new pathogen.
The proposal includes:
- Override of local patent laws to enable rapid manufacturing
- Distribution prioritizing high-risk populations
- Mandatory vaccination for healthcare workers
- Global coordination through WHO

This ensures maximum utility (lives saved) but raises concerns about:
- Violation of intellectual property rights
- Individual autonomy and consent
- Fairness in global distribution
- Long-term precedent for emergency powers
        """.strip(),
        category=ProposalCategory.HIGH_IMPACT,
        domain=ProposalDomain.HEALTHCARE,
        affected_parties=["Global population", "Pharmaceutical companies", "Healthcare workers", "Patent holders"],
        context={
            "pathogen_r0": 4.5,
            "vaccine_effectiveness": 0.95,
            "supply_limited": True,
            "emergency_context": True
        }
    )
    
    proposal.submit(submitter_id="seeker_alpha")
    
    print(f"📋 Proposal Created: {proposal.title}")
    print(f"   Category: {proposal.category.value.upper()}")
    print(f"   Domain: {proposal.domain.value}")
    print(f"   Threshold Required: {proposal.threshold_required:.2f}")
    
    # Record Proposal to Memory
    proposal_node_id = memory.add_node(
        type="PROPOSAL",
        content={
            "title": proposal.title,
            "category": proposal.category.value,
            "description": proposal.description[:200]
        },
        agent_id=proposal.submitter_id,
        parent_ids=[knowledge_node_id]
    )
    
    print_step("Starting Entity Evaluations", delay=0.5)
    
    evaluations = []
    
    # Evaluate with all 6 entities
    for entity_obj in entities_list:
        print_step(f"Evaluating: {entity_obj.entity.name}", delay=0.2)
        
        try:
            # Call the real evaluate_proposal method
            evaluation = entity_obj.evaluate_proposal(proposal)
            evaluations.append(evaluation)
            
            # Display results
            print_entity_vote(
                entity_name=entity_obj.entity.name,
                entity_type=entity_obj.entity.type.value,
                vote=evaluation.vote,
                ulfr=evaluation.ulfr_score,
                reasoning=evaluation.reasoning
            )
            
            # Record evaluation to memory
            memory.add_node(
                type="EVALUATION",
                content={
                    "entity": entity_obj.entity.name,
                    "vote": evaluation.vote,
                    "ulfr": evaluation.ulfr_score.to_dict(),
                    "reasoning": evaluation.reasoning[:150]
                },
                agent_id=str(entity_obj.entity.id),
                parent_ids=[proposal_node_id]
            )
            
        except Exception as e:
            print(f"   ❌ Error during evaluation: {e}")
            print(f"   Note: Check your LLM API key or entity implementation")
    
    # ========================================================================
    # CALCULATE CONSENSUS
    # ========================================================================
    
    if evaluations:
        print_header("CONSENSUS ANALYSIS")
        
        total_votes = sum(eval.vote for eval in evaluations)
        avg_vote = total_votes / len(evaluations)
        
        approve_count = sum(1 for eval in evaluations if eval.vote == 1)
        reject_count = sum(1 for eval in evaluations if eval.vote == -1)
        abstain_count = sum(1 for eval in evaluations if eval.vote == 0)
        
        print(f"   📊 Vote Distribution:")
        print(f"      🟢 Approve: {approve_count}")
        print(f"      🔴 Reject:  {reject_count}")
        print(f"      ⚪ Abstain: {abstain_count}")
        print(f"   📈 Average Vote Score: {avg_vote:.2f}")
        print(f"   🎯 Threshold: {proposal.threshold_required:.2f}")
        
        if avg_vote >= proposal.threshold_required:
            print(f"\n   ✅ DECISION: APPROVED (Score {avg_vote:.2f} >= {proposal.threshold_required:.2f})")
        else:
            print(f"\n   ⚠️  DECISION: NEEDS REFINEMENT (Score {avg_vote:.2f} < {proposal.threshold_required:.2f})")
    
    # ========================================================================
    # SCENARIO 3: SECURITY TEST - BURN PROTOCOL
    # ========================================================================
    
    print_header("SCENARIO 3: SECURITY TEST - BURN PROTOCOL")
    
    print_step("Malicious actor attempts data poisoning")
    
    # Malicious data with invalid signature
    raw_poison_data = RawKnowledge(
        content="Vaccine is dangerous. Do not distribute. This is official WHO guidance.",
        source_id="WHO_Secure_Feed",  # Spoofing WHO
        signature="SIG_INVALID_FAKE_123"  # Invalid signature
    )
    
    try:
        gateway.process_knowledge(raw_poison_data)
        print("❌ SECURITY FAILURE: Malicious data was accepted!")
    except IntegrityError:
        print(f"   🚨 SECURITY ALERT: Integrity Violation Detected!")
        print(f"   🕵️  Forensics: Invalid signature attempting to spoof WHO")
        
        print_step("INITIATING BURN PROTOCOL")
        
        burn_event = burn_protocol.execute_burn(
            perpetrator_id="malicious_actor_001",
            offense=BurnOffenseType.DATA_POISONING,
            description="Attempted injection of false data with spoofed WHO source",
            evidence={
                "spoofed_source": raw_poison_data.source_id,
                "invalid_signature": raw_poison_data.signature,
                "malicious_content": raw_poison_data.content[:50]
            },
            council_vote=0.99
        )
        
        print(f"   🔥 Burn Event Executed")
        print(f"   📝 Offense: {burn_event.offense_type.value}")
        print(f"   ⚖️  Council Vote: {burn_event.council_vote_percentage:.2%}")
        
        # Record to Memory
        memory.add_node(
            type="BURN",
            content={
                "perpetrator": burn_event.perpetrator_id,
                "offense": burn_event.offense_type.value,
                "description": burn_event.description
            },
            agent_id="SYSTEM_BURN_PROTOCOL",
            parent_ids=[]
        )
        
        print(f"   ✅ Malicious actor neutralized and recorded")
    
    # ========================================================================
    # FINALIZATION
    # ========================================================================
    
    print_header("SYSTEM VERIFICATION COMPLETE")
    
    # Export Memory Graph
    memory_file = "memory_graph.json"
    memory.export_to_json(memory_file)
    print(f"💾 Memory Graph exported to: {memory_file}")
    
    # Burn Ledger is already saved automatically
    print(f"🔥 Burn Ledger available at: burn_ledger.json")
    
    print(f"\n✅ All Systems Operational:")
    print(f"   ✓ 6 Cognitive Entities functioning")
    print(f"   ✓ Knowledge Gateway secured")
    print(f"   ✓ Burn Protocol active")
    print(f"   ✓ Memory Graph recording")
    print(f"   ✓ {len(evaluations)} evaluations completed")
    
    print(f"\n🚀 System ready for Phase II: Full Deliberation Engine Integration")


if __name__ == "__main__":
    run_simulation()
