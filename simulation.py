"""
Orbis Ethica - End-to-End Simulation
Scenario: 'The Pandemic Triage Decision'
Demonstrates: Knowledge Purification -> Proposal -> Attack -> Burn Protocol
"""

import time
import uuid
from datetime import datetime
from typing import List

# --- IMPORTS (Adjust based on your file structure) ---
from backend.knowledge.gateway import KnowledgeGateway, AccessDenied, IntegrityError
from backend.knowledge.models import RawKnowledge
from backend.security.burn.protocol import BurnProtocol
from backend.security.burn.models import BurnOffenseType

# --- MOCK ENTITIES (Until we fully implement the Entity class) ---
class Entity:
    def __init__(self, name: str, role: str, reputation: float = 1.0):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.role = role
        self.reputation = reputation
        self.is_active = True

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
        print(f"📢 [ENTITY ACTION] {seeker.name} reads verified data: '{clean_knowledge.content[:30]}...'")
        print(f"💡 [PROPOSAL] {seeker.name} proposes: 'Initiate Distribution Protocol'")
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
        
        # Update Entity State (Mocking the effect)
        corrupt_bot.reputation = 0.0
        corrupt_bot.is_active = False
        
    print_header("FINAL SYSTEM STATE")
    print(f"👥 Entity Status:\n   {seeker}\n   {healer}\n   {corrupt_bot}")
    
    if not corrupt_bot.is_active:
        print(f"\n✅ SUCCESS: Malicious actor successfully neutralized.")
    else:
        print(f"\n❌ FAILURE: Malicious actor still active.")

if __name__ == "__main__":
    run_simulation()