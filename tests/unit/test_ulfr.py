"""Unit tests for ULFR Framework."""

import pytest
from backend.core.models.ulfr import ULFRScore, ULFRWeights, DEFAULT_WEIGHTS


class TestULFRScore:
    """Test ULFR Score model."""
    
    def test_create_valid_score(self):
        """Test creating a valid ULFR score."""
        score = ULFRScore(
            utility=0.8,
            life=0.7,
            fairness_penalty=0.2,
            rights_risk=0.1
        )
        
        assert score.utility == 0.8
        assert score.life == 0.7
        assert score.fairness_penalty == 0.2
        assert score.rights_risk == 0.1
    
    def test_score_validation(self):
        """Test that scores must be in [0, 1] range."""
        with pytest.raises(ValueError):
            ULFRScore(
                utility=1.5,  # Invalid
                life=0.5,
                fairness_penalty=0.2,
                rights_risk=0.1
            )
    
    def test_calculate_weighted_score(self):
        """Test weighted score calculation."""
        score = ULFRScore(
            utility=0.8,
            life=0.9,
            fairness_penalty=0.1,
            rights_risk=0.2
        )
        
        weights = ULFRWeights(
            alpha=0.25,
            beta=0.40,
            gamma=0.20,
            delta=0.15
        )
        
        # Score = 0.25*0.8 + 0.40*0.9 - 0.20*0.1 - 0.15*0.2
        # Score = 0.2 + 0.36 - 0.02 - 0.03 = 0.51
        weighted = score.calculate_weighted_score(weights)
        
        assert abs(weighted - 0.51) < 0.01
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        score = ULFRScore(
            utility=0.8,
            life=0.7,
            fairness_penalty=0.2,
            rights_risk=0.1
        )
        
        d = score.to_dict()
        
        assert d["U"] == 0.8
        assert d["L"] == 0.7
        assert d["F_penalty"] == 0.2
        assert d["R_risk"] == 0.1


class TestULFRWeights:
    """Test ULFR Weights model."""
    
    def test_default_weights(self):
        """Test default weights from whitepaper."""
        weights = DEFAULT_WEIGHTS
        
        assert weights.alpha == 0.25
        assert weights.beta == 0.40
        assert weights.gamma == 0.20
        assert weights.delta == 0.15
    
    def test_validate_sum(self):
        """Test that default weights sum to 1.0."""
        weights = DEFAULT_WEIGHTS
        assert weights.validate_sum()
    
    def test_normalize(self):
        """Test weight normalization."""
        weights = ULFRWeights(
            alpha=0.5,
            beta=0.5,
            gamma=0.3,
            delta=0.2
        )
        
        # Sum = 1.5, should normalize to 1.0
        normalized = weights.normalize()
        
        assert abs(normalized.alpha - 0.5/1.5) < 0.01
        assert abs(normalized.beta - 0.5/1.5) < 0.01
        assert normalized.validate_sum()
    
    def test_weight_validation(self):
        """Test that weights must be in [0, 1] range."""
        with pytest.raises(ValueError):
            ULFRWeights(
                alpha=1.5,  # Invalid
                beta=0.4,
                gamma=0.2,
                delta=0.15
            )


class TestWeightPresets:
    """Test preset weight configurations."""
    
    def test_utility_focused(self):
        """Test utility-focused preset."""
        from backend.core.models.ulfr import UTILITY_FOCUSED
        
        assert UTILITY_FOCUSED.alpha == 0.50
        assert UTILITY_FOCUSED.alpha > UTILITY_FOCUSED.beta
    
    def test_care_focused(self):
        """Test care-focused preset."""
        from backend.core.models.ulfr import CARE_FOCUSED
        
        assert CARE_FOCUSED.beta == 0.55
        assert CARE_FOCUSED.beta > CARE_FOCUSED.alpha
    
    def test_rights_focused(self):
        """Test rights-focused preset."""
        from backend.core.models.ulfr import RIGHTS_FOCUSED
        
        assert RIGHTS_FOCUSED.delta == 0.40
        assert RIGHTS_FOCUSED.delta > RIGHTS_FOCUSED.alpha
    
    def test_balanced(self):
        """Test balanced preset."""
        from backend.core.models.ulfr import BALANCED
        
        assert BALANCED.alpha == BALANCED.beta == BALANCED.gamma == BALANCED.delta
