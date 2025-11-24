"""
Extended ULFR Core - Advanced mathematical models for ethical scoring.
Based on Whitepaper V3.2 Appendix A.2.
"""

import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .models.ulfr import ULFRScore, ULFRWeights


class OutcomeGroup(BaseModel):
    """Represents a social group affected by a decision."""
    group_id: str
    impact: float = Field(..., description="Impact on this group (normalized -1 to 1)")
    baseline_welfare: float = Field(..., description="Baseline welfare of this group (0 to 1)")
    population_size: int = Field(default=1, description="Number of individuals in group")


class RiskFactors(BaseModel):
    """Risk factors for a proposal."""
    probability_failure: float = Field(..., ge=0.0, le=1.0)
    magnitude_harm: float = Field(..., ge=0.0, le=1.0)
    irreversibility_score: float = Field(..., ge=0.0, le=1.0)
    security_level: float = Field(default=0.9, ge=0.0, le=1.0, description="System security/reliability")


class ExtendedULFR:
    """
    Extended ULFR Scoring Engine.
    Implements the complex mathematical models for Fairness and Risk.
    """
    
    def __init__(self, weights: Optional[ULFRWeights] = None):
        self.weights = weights or ULFRWeights()
        # Constants from whitepaper
        self.rho = 0.5  # Irreversibility weight factor (example value)
        self.omega_r = 0.6  # Rawlsian weight in F_penalty
        self.omega_e = 0.4  # Equality weight in F_penalty

    def calculate_gini(self, outcomes: List[float]) -> float:
        """
        Calculate Gini coefficient for a list of outcomes.
        Range: [0, 1], where 0 is perfect equality and 1 is perfect inequality.
        """
        if not outcomes:
            return 0.0
        
        # Shift values to be positive if needed (Gini typically requires non-negative values)
        # For impact (-1 to 1), we map to 0-2 range for calculation
        shifted_outcomes = [x + 1.0 for x in outcomes]
        
        n = len(shifted_outcomes)
        if n == 0:
            return 0.0
            
        mean = sum(shifted_outcomes) / n
        if mean == 0:
            return 0.0
            
        # Gini formula: sum(|xi - xj|) / (2 * n^2 * mean)
        diff_sum = 0
        for i in shifted_outcomes:
            for j in shifted_outcomes:
                diff_sum += abs(i - j)
                
        return diff_sum / (2 * n**2 * mean)

    def calculate_rawlsian_impact(self, groups: List[OutcomeGroup]) -> float:
        """
        Calculate Rawlsian component (F_Rawls).
        Measures negative impact on the least advantaged group.
        Formula: -min(Impact_g / Baseline_g)
        """
        if not groups:
            return 0.0
            
        min_ratio = float('inf')
        
        for group in groups:
            # Avoid division by zero
            baseline = max(group.baseline_welfare, 0.01)
            ratio = group.impact / baseline
            if ratio < min_ratio:
                min_ratio = ratio
                
        # The formula is negative min ratio (so worse impact = higher penalty)
        # We clamp it to [0, 1] for the penalty score
        # If min_ratio is negative (harm), penalty is positive.
        # If min_ratio is positive (benefit), penalty is 0 (or low).
        
        # Interpretation: 
        # If impact is -0.5 and baseline is 0.5, ratio is -1.0. Penalty -> 1.0
        # If impact is 0.5 and baseline is 0.5, ratio is 1.0. Penalty -> 0.0
        
        rawls_score = -min_ratio
        return max(0.0, min(1.0, rawls_score))

    def calculate_fairness_penalty(self, groups: List[OutcomeGroup]) -> float:
        """
        Calculate total Fairness Penalty (F_penalty).
        F_penalty = ω_R * F_Rawls + ω_E * F_Equality
        """
        if not groups:
            return 0.0
            
        # 1. Rawlsian Component
        f_rawls = self.calculate_rawlsian_impact(groups)
        
        # 2. Equality Component (Gini of impacts)
        impacts = [g.impact for g in groups]
        f_equality = self.calculate_gini(impacts)
        
        # Weighted sum
        f_penalty = (self.omega_r * f_rawls) + (self.omega_e * f_equality)
        return max(0.0, min(1.0, f_penalty))

    def calculate_risk_score(self, risk_factors: RiskFactors) -> float:
        """
        Calculate Risk Score.
        Risk = [P(Failure) * Magnitude(Harm)] + ρ * Irreversibility
        """
        # Expected Loss
        expected_loss = risk_factors.probability_failure * risk_factors.magnitude_harm
        
        # Irreversibility component
        irreversibility_component = self.rho * risk_factors.irreversibility_score
        
        total_risk = expected_loss + irreversibility_component
        return max(0.0, min(1.0, total_risk))

    def calculate_score(self, 
                       utility: float, 
                       life_care: float, 
                       groups: List[OutcomeGroup],
                       risk_factors: RiskFactors) -> Dict[str, float]:
        """
        Calculate final Extended ULFR Score.
        Returns dictionary with all components and final score.
        """
        # Calculate complex components
        f_penalty = self.calculate_fairness_penalty(groups)
        r_risk = self.calculate_risk_score(risk_factors)
        
        # Create score object to use its calculation method
        ulfr = ULFRScore(
            utility=utility,
            life=life_care,
            fairness_penalty=f_penalty,
            rights_risk=r_risk
        )
        
        final_score = ulfr.calculate_weighted_score(self.weights)
        
        return {
            "score": final_score,
            "U": utility,
            "L": life_care,
            "F_penalty": f_penalty,
            "R_risk": r_risk,
            "details": {
                "F_rawls": self.calculate_rawlsian_impact(groups),
                "F_gini": self.calculate_gini([g.impact for g in groups]),
                "expected_loss": risk_factors.probability_failure * risk_factors.magnitude_harm,
                "irreversibility": risk_factors.irreversibility_score
            }
        }
