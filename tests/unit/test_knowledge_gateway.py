
import pytest
from backend.knowledge.models import RawKnowledge
from backend.knowledge.gateway import KnowledgeGateway, AccessDenied, IntegrityError

def test_valid_knowledge_flow():
    # Setup
    gateway = KnowledgeGateway(verified_sources=["WHO", "CDC"])
    content = "Vaccines save lives"
    valid_sig = f"SIG_{content[::-1]}"
    
    raw = RawKnowledge(
        content=content,
        source_id="WHO",
        signature=valid_sig
    )
    
    # Action
    verified = gateway.process_knowledge(raw)
    
    # Assert
    assert verified.content == content
    assert verified.source_id == "WHO"
    assert verified.purity_score == 1.0
    assert verified.signature_verified is True

def test_unknown_source_rejection():
    # Setup
    gateway = KnowledgeGateway(verified_sources=["WHO"])
    content = "Earth is flat"
    valid_sig = f"SIG_{content[::-1]}"
    
    raw = RawKnowledge(
        content=content,
        source_id="RandomBlog", # Not in list
        signature=valid_sig
    )
    
    # Action & Assert
    with pytest.raises(AccessDenied):
        gateway.process_knowledge(raw)

def test_invalid_signature_rejection():
    # Setup
    gateway = KnowledgeGateway(verified_sources=["WHO"])
    content = "Vaccines save lives"
    fake_sig = "SIG_I_HACKED_THIS"
    
    raw = RawKnowledge(
        content=content,
        source_id="WHO",
        signature=fake_sig
    )
    
    # Action & Assert
    with pytest.raises(IntegrityError):
        gateway.process_knowledge(raw)

if __name__ == "__main__":
    # Manual run for quick feedback
    try:
        test_valid_knowledge_flow()
        print("✓ test_valid_knowledge_flow PASSED")
        test_unknown_source_rejection()
        print("✓ test_unknown_source_rejection PASSED")
        test_invalid_signature_rejection()
        print("✓ test_invalid_signature_rejection PASSED")
    except Exception as e:
        print(f"FAILED: {e}")
