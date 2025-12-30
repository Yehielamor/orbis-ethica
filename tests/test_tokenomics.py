import pytest
import os
from backend.core.ledger import Ledger
from backend.core.database import DatabaseManager

# Use an in-memory DB for testing
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def ledger():
    db_manager = DatabaseManager(TEST_DB_URL)
    # Create tables
    from backend.core.models.sql_models import Base
    Base.metadata.create_all(db_manager.engine)
    return Ledger(db_manager)

def test_hard_cap_enforcement(ledger):
    """Test that minting cannot exceed MAX_SUPPLY."""
    
    # 1. Mint up to the cap (minus 1)
    almost_cap = ledger.MAX_SUPPLY - 1.0
    success = ledger.mint_reward("user1", almost_cap, "Initial Mint")
    assert success is True
    assert ledger.get_total_supply() == almost_cap
    
    # 2. Mint exactly to the cap
    success = ledger.mint_reward("user1", 1.0, "Fill Cap")
    assert success is True
    assert ledger.get_total_supply() == ledger.MAX_SUPPLY
    
    # 3. Attempt to mint 1 more (Should Fail)
    success = ledger.mint_reward("user1", 1.0, "Overflow")
    assert success is False
    assert ledger.get_total_supply() == ledger.MAX_SUPPLY
    
    # 4. Burn 10 tokens
    # Note: slash_stake sends to "system_burn"
    success = ledger.slash_stake("user1", 10.0, "Penalty")
    assert success is True
    # Supply should decrease
    assert ledger.get_total_supply() == ledger.MAX_SUPPLY - 10.0
    
    # 5. Mint 5 tokens (Should Succeed now)
    success = ledger.mint_reward("user1", 5.0, "Recovery")
    assert success is True
    assert ledger.get_total_supply() == ledger.MAX_SUPPLY - 5.0
    
    # 6. Mint 6 tokens (Should Fail - exceeds by 1)
    success = ledger.mint_reward("user1", 6.0, "Overflow Again")
    assert success is False
    assert ledger.get_total_supply() == ledger.MAX_SUPPLY - 5.0

if __name__ == "__main__":
    # Allow running directly
    db_manager = DatabaseManager(TEST_DB_URL)
    from backend.core.models.sql_models import Base
    Base.metadata.create_all(db_manager.engine)
    l = Ledger(db_manager)
    
    test_hard_cap_enforcement(l)
    print("✅ Tokenomics Test Passed!")
