
from backend.security.burn.protocol import BurnProtocol
from backend.security.burn.models import BurnOffenseType

def run_burn_simulation():
    print("🚨 INITIATING BURN PROTOCOL SIMULATION 🚨")
    print("------------------------------------------")
    
    protocol = BurnProtocol()
    
    # Simulate a detected offense
    perpetrator = "ENTITY-SEEKER-001"
    offense = BurnOffenseType.BIAS_INJECTION
    description = "Systematically lowered weight of 'Life' parameter for specific demographic group."
    
    evidence = {
        "log_id": "LOG-99283",
        "statistical_p_value": 0.00001,
        "witnesses": ["HEALER", "GUARDIAN"]
    }
    
    print(f"DETECTED OFFENSE: {offense.value}")
    print(f"PERPETRATOR: {perpetrator}")
    print("GATHERING COUNCIL VOTE...")
    
    # Simulate Council Vote
    council_vote = 0.96 # 96% support
    print(f"COUNCIL VOTE: {council_vote * 100}% - BURN APPROVED")
    
    print("\n🔥 EXECUTING BURN...")
    event = protocol.execute_burn(
        perpetrator_id=perpetrator,
        offense=offense,
        description=description,
        evidence=evidence,
        council_vote=council_vote
    )
    
    print("\n📄 PUBLIC NOTICE GENERATED:")
    print(event.to_markdown())

if __name__ == "__main__":
    run_burn_simulation()
