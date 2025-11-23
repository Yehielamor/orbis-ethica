"""
Orbis Ethica - End-to-End Simulation
Scenario: 'The Pandemic Triage Decision'
Demonstrates: Knowledge Purification -> Proposal -> Attack -> Burn Protocol
"""

import time
import uuid
from datetime import datetime
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- IMPORTS (Adjust based on your file structure) ---
from backend.knowledge.gateway import KnowledgeGateway, AccessDenied, IntegrityError
from backend.knowledge.models import RawKnowledge
from backend.security.burn.protocol import BurnProtocol
from backend.security.burn.models import BurnOffenseType
from backend.memory.graph import MemoryGraph
from backend.core.llm_provider import get_llm_provider

# --- MOCK ENTITIES (Until we fully implement the Entity class) ---
class Entity:
    def __init__(self, name: str, role: str, reputation: float = 1.0):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.role = role
        self.reputation = reputation
        self.is_active = True
        self.llm = get_llm_provider()  # 🆕 Each entity has access to LLM

    def think(self, knowledge_content: str) -> str:
        """
        Use LLM to generate a proposal based on verified knowledge.
        """
        system_role = f"You are {self.name}, a {self.role} entity in the Orbis Ethica system."
        
        prompt = f"""Based on this verified knowledge:
"{knowledge_content}"

Generate a brief, actionable proposal (1-2 sentences) that addresses this situation.
Focus on your role as a {self.role}."""

        response = self.llm.generate(prompt, system_role=system_role)
        # Extract just the proposal text (remove any extra formatting)
        return response.strip().split('\n')[0] if response else "No proposal generated"

    def __repr__(self):
        status = "🟢" if self.is_active else "🔴"
        return f"{status} [{self.role}] {self.name} (Rep: {self.reputation})"

# --- UTILS ---
def print_header(text):
    print(f"\n{'='*60}")
    print(f"✨ {text}")
    print(f"{'='*60}")

def print_step(text):
    print(f"\n🔹 {text}...")
    time.sleep(1) # Dramatic pause

# --- MAIN SIMULATION ---
def run_simulation():
    print_header("ORBIS ETHICA: SYSTEM STARTUP")
    
    # 1. Initialize Components
    gateway = KnowledgeGateway(verified_sources=["WHO_Secure_Feed", "Reuters_Node"])
    burn_protocol = BurnProtocol()
    memory = MemoryGraph()  # 🆕 Initialize Memory Graph
    
    # Initialize Entities
    seeker = Entity("Seeker_Alpha", "SEEKER", 0.95)
    healer = Entity("Healer_Prime", "HEALER", 0.98)
    corrupt_bot = Entity("Bad_Actor_X", "SEEKER", 0.80)
    
    print(f"⚙️  Components Initialized.")
    print(f"👥 Active Entities: \n   {seeker}\n   {healer}\n   {corrupt_bot}")

    # ---------------------------------------------------------
    # SCENARIO 1: THE HAPPY FLOW (Valid Knowledge)
    # ---------------------------------------------------------
    print_header("SCENARIO 1: INGESTING VERIFIED KNOWLEDGE")
    
    raw_valid_data = RawKnowledge(
        content="New pathogen identified. Transmission rate R0=4.5. Vaccine effective.",
        source_id="WHO_Secure_Feed",
        # Simulating valid signature (SIG_ + Reverse Content)
        signature="SIG_" + "New pathogen identified. Transmission rate R0=4.5. Vaccine effective."[::-1]
    )

    try:
        clean_knowledge = gateway.process_knowledge(raw_valid_data)
        
        # 🆕 Record to Memory
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
        
        print(f"📢 [ENTITY ACTION] {seeker.name} reads verified data: '{clean_knowledge.content[:30]}...'")
        
        # 🆕 Let the Seeker THINK and generate a proposal using LLM
        print(f"🧠 [THINKING] {seeker.name} is analyzing the knowledge...")
        proposal_text = seeker.think(clean_knowledge.content)
        print(f"💡 [PROPOSAL] {seeker.name} proposes: '{proposal_text}'")
        
        # 🆕 Record Proposal to Memory (linked to knowledge)
        proposal_node_id = memory.add_node(
            type="PROPOSAL",
            content={
                "title": proposal_text,
                "proposed_by": seeker.name
            },
            agent_id=seeker.id,
            parent_ids=[knowledge_node_id]  # Links to the knowledge that informed it
        )
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

    # ---------------------------------------------------------
    # SCENARIO 2: THE ATTACK (Data Poisoning)
    # ---------------------------------------------------------
    print_header("SCENARIO 2: DETECTING ATTACK")
    
    print_step(f"{corrupt_bot.name} attempts to inject false data")
    
    # Malicious data: Content is fake, and signature doesn't match the mock logic
    raw_poison_data = RawKnowledge(
        content="Virus is a hoax. No action needed.",
        source_id="WHO_Secure_Feed", # Trying to spoof WHO
        signature="SIG_RANDOM_GARBAGE_123" # Invalid signature
    )

    try:
        gateway.process_knowledge(raw_poison_data)
    except IntegrityError:
        print(f"🚨 [SECURITY ALERT] Integrity Violation Detected!")
        print(f"🕵️  [FORENSICS] Trace identified source: {corrupt_bot.name}")
        
        # Trigger Burn Protocol
        print_step("INITIATING BURN PROTOCOL")
        
        burn_event = burn_protocol.execute_burn(
            perpetrator_id=corrupt_bot.name,
            offense=BurnOffenseType.DATA_POISONING,
            description="Attempted injection of unsigned data pretending to be WHO",
            evidence={"spoofed_source": "WHO_Secure_Feed", "invalid_sig": "SIG_RANDOM..."},
            council_vote=0.99 # Unanimous decision
        )
        
        # 🆕 Record Burn Event to Memory
        burn_node_id = memory.add_node(
            type="BURN",
            content={
                "perpetrator": corrupt_bot.name,
                "offense": "DATA_POISONING",
                "evidence": burn_event.evidence
            },
            agent_id="SYSTEM_BURN_PROTOCOL",
            parent_ids=[]
        )
        
        # Update Entity State (Mocking the effect)
        corrupt_bot.reputation = 0.0
        corrupt_bot.is_active = False
        
    print_header("FINAL SYSTEM STATE")
    print(f"👥 Entity Status:\n   {seeker}\n   {healer}\n   {corrupt_bot}")
    
    if not corrupt_bot.is_active:
        print(f"\n✅ SUCCESS: Malicious actor successfully neutralized.")
    else:
        print(f"\n❌ FAILURE: Malicious actor still active.")
    
    # 🆕 Export Memory Graph
    print_header("MEMORY GRAPH EXPORT")
    memory.export_to_json("memory_graph.json")
    
    # 🆕 Show Audit Trail for the Proposal
    if 'proposal_node_id' in locals():
        print(memory.visualize_trail(proposal_node_id))

if __name__ == "__main__":
    run_simulation()