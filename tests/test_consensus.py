import sys
import os
import asyncio
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.consensus import ConsensusManager
from backend.core.models import Proposal, ProposalCategory, ProposalDomain

def test_consensus_flow():
    print("🚀 Testing Consensus Manager...")
    
    # 1. Initialize Manager
    manager = ConsensusManager("test_node_key.json")
    print(f"✅ Manager Initialized. Public Key: {manager.get_public_key()[:16]}...")
    
    # 2. Create Proposal
    proposal = Proposal(
        title="Test Proposal for Consensus",
        description="This is a test proposal to verify Ed25519 signatures.",
        category=ProposalCategory.ROUTINE,
        domain=ProposalDomain.TECHNOLOGY
    )
    print(f"📝 Created Proposal: {proposal.id}")
    
    # 3. Sign Proposal
    print("🔐 Signing Proposal...")
    manager.sign_proposal(proposal)
    print(f"✅ Signed. Signature: {proposal.signature[:16]}...")
    print(f"   Submitter ID: {proposal.submitter_id[:16]}...")
    
    # 4. Verify Valid Proposal
    print("🔍 Verifying Valid Proposal...")
    is_valid = manager.verify_proposal(proposal)
    if is_valid:
        print("✅ Verification SUCCESS")
    else:
        print("❌ Verification FAILED (Unexpected)")
        exit(1)
        
    # 5. Tamper with Proposal
    print("😈 Tampering with Proposal...")
    proposal.description = "This description has been modified by a hacker."
    
    # 6. Verify Tampered Proposal
    print("🔍 Verifying Tampered Proposal...")
    is_valid_tampered = manager.verify_proposal(proposal)
    if not is_valid_tampered:
        print("✅ Tamper Detection SUCCESS (Verification Failed as expected)")
    else:
        print("❌ Tamper Detection FAILED (Verification Succeeded unexpectedly)")
        exit(1)

    # Cleanup
    if os.path.exists("test_node_key.json"):
        os.remove("test_node_key.json")
    print("\n🎉 All Consensus Tests Passed!")

if __name__ == "__main__":
    test_consensus_flow()
