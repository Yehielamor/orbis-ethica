
from backend.core.extended_ulfr import ExtendedULFR, OutcomeGroup, RiskFactors

def test_extended_ulfr():
    print("Testing Extended ULFR...")
    
    # Setup
    ulfr = ExtendedULFR()
    
    # Case 1: High Inequality (should have high F_penalty)
    groups_unequal = [
        OutcomeGroup(group_id="g1", impact=0.9, baseline_welfare=0.5, population_size=100),
        OutcomeGroup(group_id="g2", impact=-0.8, baseline_welfare=0.2, population_size=100) # Harm to vulnerable
    ]
    
    # Case 2: Low Inequality
    groups_equal = [
        OutcomeGroup(group_id="g1", impact=0.5, baseline_welfare=0.5, population_size=100),
        OutcomeGroup(group_id="g2", impact=0.4, baseline_welfare=0.5, population_size=100)
    ]
    
    risk_low = RiskFactors(probability_failure=0.1, magnitude_harm=0.2, irreversibility_score=0.1)
    
    # Calculate
    score_unequal = ulfr.calculate_score(0.8, 0.5, groups_unequal, risk_low)
    score_equal = ulfr.calculate_score(0.8, 0.5, groups_equal, risk_low)
    
    print(f"Score Unequal: {score_unequal['score']:.3f} (F_penalty: {score_unequal['F_penalty']:.3f})")
    print(f"Score Equal: {score_equal['score']:.3f} (F_penalty: {score_equal['F_penalty']:.3f})")
    
    assert score_equal['score'] > score_unequal['score'], "Equal outcome should score higher"
    assert score_unequal['F_penalty'] > score_equal['F_penalty'], "Unequal outcome should have higher penalty"
    
    print("✓ Extended ULFR Logic Verified")

if __name__ == "__main__":
    test_extended_ulfr()
