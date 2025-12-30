"""ULFR Framework - Core ethical evaluation model."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ULFRScore(BaseModel):
    """
    ULFR Score represents the four dimensions of ethical evaluation.
    
    - U (Utility): Aggregate welfare, efficiency, lives saved
    - L (Life/Care): Harm reduction, protection of vulnerable
    - F (Fairness): Equity, justice, distribution (as penalty)
    - R (Rights): Risk to autonomy, dignity, due process (as penalty)
    """
    
    utility: float = Field(
        ge=0.0,
        le=1.0,
        description="Utility score: aggregate welfare and efficiency"
    )
    life: float = Field(
        ge=0.0,
        le=1.0,
        description="Life/Care score: harm reduction and protection"
    )
    fairness_penalty: float = Field(
        ge=0.0,
        le=1.0,
        description="Fairness penalty: inequality and injustice (higher = worse)"
    )
    rights_risk: float = Field(
        ge=0.0,
        le=1.0,
        description="Rights risk: threat to autonomy and dignity (higher = worse)"
    )
    
    @field_validator('utility', 'life', 'fairness_penalty', 'rights_risk')
    @classmethod
    def validate_range(cls, v: float) -> float:
        """Ensure all scores are in [0, 1] range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Score must be between 0 and 1, got {v}")
        return v
    
    def calculate_weighted_score(self, weights: 'ULFRWeights') -> float:
        """
        Calculate weighted decision score using Deductive ULFR formula:
        Score starts at 1.0 (Perfect) and is penalized for:
        - Missing Utility (1-U)
        - Missing Life/Care (1-L)
        - Presence of Unfairness (F)
        - Presence of Rights Risk (R)
        
        Score = 1.0 - α(1-U) - β(1-L) - γ(F) - δ(R)
        
        Args:
            weights: ULFRWeights object with α, β, γ, δ parameters
            
        Returns:
            Weighted score in range [0.0, 1.0] (clamped)
        """
        penalty = (
            weights.alpha * (1.0 - self.utility) +
            weights.beta * (1.0 - self.life) +
            weights.gamma * self.fairness_penalty +
            weights.delta * self.rights_risk
        )
        
        return max(0.0, 1.0 - penalty)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "U": self.utility,
            "L": self.life,
            "F_penalty": self.fairness_penalty,
            "R_risk": self.rights_risk
        }


class ULFRWeights(BaseModel):
    """
    Weights for ULFR decision function.
    
    Default values from whitepaper:
    - α (alpha) = 0.25 - Utility weight
    - β (beta) = 0.40 - Life/Care weight
    - γ (gamma) = 0.20 - Fairness penalty weight
    - δ (delta) = 0.15 - Rights risk penalty weight
    
    Sum of weights should typically equal 1.0 for normalized scoring.
    """
    
    alpha: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight for Utility dimension"
    )
    beta: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description="Weight for Life/Care dimension"
    )
    gamma: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Weight for Fairness penalty"
    )
    delta: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Weight for Rights risk penalty"
    )
    
    @field_validator('alpha', 'beta', 'gamma', 'delta')
    @classmethod
    def validate_weight(cls, v: float) -> float:
        """Ensure weights are in valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Weight must be between 0 and 1, got {v}")
        return v
    
    def validate_sum(self) -> bool:
        """
        Check if weights sum to approximately 1.0.
        This is a soft constraint - weights can sum to other values
        for special cases, but typically should sum to 1.0.
        """
        total = self.alpha + self.beta + self.gamma + self.delta
        return abs(total - 1.0) < 0.01
    
    def normalize(self) -> 'ULFRWeights':
        """
        Normalize weights to sum to 1.0.
        
        Returns:
            New ULFRWeights object with normalized values
        """
        total = self.alpha + self.beta + self.gamma + self.delta
        if total == 0:
            raise ValueError("Cannot normalize weights that sum to zero")
        
        return ULFRWeights(
            alpha=self.alpha / total,
            beta=self.beta / total,
            gamma=self.gamma / total,
            delta=self.delta / total
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "α": self.alpha,
            "β": self.beta,
            "γ": self.gamma,
            "δ": self.delta
        }


# Default weights from whitepaper
DEFAULT_WEIGHTS = ULFRWeights()

# Context-specific weight presets
UTILITY_FOCUSED = ULFRWeights(alpha=0.50, beta=0.25, gamma=0.15, delta=0.10)
CARE_FOCUSED = ULFRWeights(alpha=0.15, beta=0.55, gamma=0.20, delta=0.10)
RIGHTS_FOCUSED = ULFRWeights(alpha=0.20, beta=0.20, gamma=0.20, delta=0.40)
BALANCED = ULFRWeights(alpha=0.25, beta=0.25, gamma=0.25, delta=0.25)
