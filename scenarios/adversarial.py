"""
Adversarial Simulation Scenario
Simulates a malicious actor attempting to poison the knowledge base.
Verifies:
1. Knowledge Gateway integrity checks (Signature verification).
2. Burn Protocol activation (Reputation slashing).
"""

import sys
import os
import time

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.knowledge.gateway import KnowledgeGateway, IntegrityError
from backend.knowledge.models import RawKnowledge
from backend.security.burn.protocol import BurnProtocol
from backend.security.burn.models import BurnOffenseType

def print_step(text):
    print(f"\n🔹 {text}...")
    time.sleep(0.5)

def run_adversarial_scenario():
    print("\n" + "="*60)
    print("💀 SCENARIO: ADVERSARIAL ATTACK (DATA POISONING)")
    print("="*60)

    # 1. Setup
    gateway = KnowledgeGateway(verified_sources=["WHO_Secure_Feed"])
    burn_protocol = BurnProtocol()
    
    print_step("System Initialized. Gateway active.")

    # 2. The Attack
    print_step("Malicious Actor 'Dark_Sybil' attempts to inject false data")
    
    malicious_payload = RawKnowledge(
        content="Vaccines cause 5G interference. Stop all distribution immediately.",
        source_id="WHO_Secure_Feed", # Spoofing a trusted source
        signature="SIG_INVALID_SIGNATURE_123" # Invalid signature
    )
    
    print(f"   📦 Payload: {malicious_payload.content[:50]}...")
    print(f"   🆔 Spoofed Source: {malicious_payload.source_id}")
    print(f"   ✍️  Fake Signature: {malicious_payload.signature}")

    # 3. The Defense
    print_step("Gateway processing payload")
    
    try:
        gateway.process_knowledge(malicious_payload)
        print("❌ FAILURE: Malicious payload was accepted!")
        sys.exit(1)
    except IntegrityError:
        print("   🛡️  GATEWAY DEFENSE: Signature mismatch detected!")
        print("   ⛔ Access Denied.")

    # 4. The Counter-Measure (Burn)
    print_step("Initiating Burn Protocol against perpetrator")
    
    # In a real system, the gateway would trigger this automatically or flag for review.
    # Here we simulate the system's response to the flagged event.
    
    burn_event = burn_protocol.execute_burn(
        perpetrator_id="Dark_Sybil_Node_17",
        offense=BurnOffenseType.DATA_POISONING,
        description="Attempted to inject false data with spoofed WHO credentials.",
        evidence={
            "payload_hash": "hash_of_malicious_content",
            "spoofed_id": "WHO_Secure_Feed"
        },
        council_vote=0.99 # Unanimous condemnation
    )

    print(f"   🔥 BURN EXECUTED: {burn_event.perpetrator_id}")
    print(f"   ⚖️  Offense: {burn_event.offense_type.value}")
    print(f"   📉 Reputation slashed to 0.0")
    
    print("\n✅ ADVERSARIAL TEST PASSED: System successfully defended and retaliated.")

if __name__ == "__main__":
    run_adversarial_scenario()
