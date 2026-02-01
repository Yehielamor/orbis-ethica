import os
import sys

import pytest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.core.extended_ulfr import ExtendedULFR, OutcomeGroup, RiskFactors


def test_ulfr_logic():
    ulfr = ExtendedULFR()

    # Case 1: High Inequality (should have high F_penalty)
    groups_unequal = [
        OutcomeGroup(group_id="g1", impact=0.9, baseline_welfare=0.5, population_size=100),
        OutcomeGroup(group_id="g2", impact=-0.8, baseline_welfare=0.2, population_size=100)
    ]
    
    # Case 2: Low Inequality
    groups_equal = [
        OutcomeGroup(group_id="g1", impact=0.5, baseline_welfare=0.5, population_size=100),
        OutcomeGroup(group_id="g2", impact=0.4, baseline_welfare=0.5, population_size=100)
    ]
    
    risk_low = RiskFactors(probability_failure=0.1, magnitude_harm=0.2, irreversibility_score=0.1)
    
    # Calculate
    score_unequal = ulfr.calculate_score(0.6, 0.5, groups_unequal, risk_low)
    score_equal = ulfr.calculate_score(0.8, 0.5, groups_equal, risk_low)
    
    print(f"Score Unequal: {score_unequal['score']:.3f}")
    print(f"Score Equal: {score_equal['score']:.3f}")
    
    assert score_equal['score'] > score_unequal['score'], "Equal outcome should score higher"
    print("✓ Extended ULFR Logic Verified")

if __name__ == "__main__":
    test_ulfr_logic()