
from backend.governance.assembly_manager import PoolManager

def test_pool_manager():
    print("Testing Pool Manager...")
    
    manager = PoolManager()
    
    # Test 1: Enroll Human (Success)
    attestation_valid = {"time_spent": 8.0, "challenge_response": "valid_hash"}
    candidate1 = manager.enroll_human("Alice", attestation_valid)
    assert candidate1 is not None, "Alice should be enrolled"
    assert manager.get_pool_size() == 1
    
    # Test 2: Enroll Human (Fail - PoA)
    attestation_invalid = {"time_spent": 2.0, "challenge_response": "valid_hash"}
    candidate2 = manager.enroll_human("Bob", attestation_invalid)
    assert candidate2 is None, "Bob should fail PoA"
    assert manager.get_pool_size() == 1
    
    # Enroll more for sortition
    manager.enroll_human("Charlie", attestation_valid)
    manager.enroll_human("Dave", attestation_valid)
    manager.enroll_human("Eve", attestation_valid)
    
    assert manager.get_pool_size() == 4
    
    # Test 3: Sortition
    assembly = manager.select_assembly(2, seed="test_seed")
    print(f"Selected Assembly: {[c.name for c in assembly]}")
    assert len(assembly) == 2, "Should select 2 members"
    
    # Test 4: Sortition Reproducibility
    assembly2 = manager.select_assembly(2, seed="test_seed")
    assert [c.id for c in assembly] == [c.id for c in assembly2], "Selection should be reproducible with same seed"
    
    print("✓ Pool Manager Logic Verified")

if __name__ == "__main__":
    test_pool_manager()
