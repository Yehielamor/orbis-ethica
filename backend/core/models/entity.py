"""Entity model - represents cognitive entities in the deliberation system."""

from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from .ulfr import ULFRScore


class EntityType(str, Enum):
    """Types of cognitive entities in Orbis Ethica."""
    
    SEEKER = "seeker"        # Knowledge and utility maximization
    HEALER = "healer"        # Harm reduction and care
    GUARDIAN = "guardian"    # Justice and rights
    MEDIATOR = "mediator"    # Balance and trade-offs
    CREATOR = "creator"      # Innovation and synthesis
    ARBITER = "arbiter"      # Final judgment and coherence


class EntityVote(int, Enum):
    """Vote values for entity consensus."""
    
    REJECT = -1      # Strong opposition
    ABSTAIN = 0      # Neutral or insufficient information
    APPROVE = 1      # Support


class Entity(BaseModel):
    """
    Cognitive Entity - specialized agent for ethical deliberation.
    
    Each entity represents a distinct ethical perspective:
    - Seeker: "What generates the most good?"
    - Healer: "Who will be hurt, and how can we protect them?"
    - Guardian: "Does this respect fundamental rights?"
    - Mediator: "How can we balance competing priorities?"
    - Creator: "Is there a better approach?"
    - Arbiter: "What decision will we look back on with pride?"
    """
    
    # Identity
    id: UUID = Field(default_factory=uuid4)
    type: EntityType = Field(description="Entity type/role")
    name: str = Field(description="Entity name")
    
    # Reputation
    reputation: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Reputation score (0-1)"
    )
    staked_reputation: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Reputation currently staked on votes"
    )
    
    # Configuration
    model_provider: str = Field(
        default="openai",
        description="LLM provider (openai, anthropic, local)"
    )
    model_name: str = Field(
        default="gpt-4",
        description="Specific model name"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature for reasoning"
    )
    
    # Specialization
    primary_focus: str = Field(description="Primary ethical dimension (U/L/F/R)")
    bias_description: str = Field(description="Known biases of this entity")
    
    # Performance tracking
    decisions_participated: int = Field(default=0)
    accuracy_score: float = Field(default=0.5, ge=0.0, le=1.0)
    consistency_score: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Cryptographic identity
    public_key: Optional[str] = Field(None, description="Public key for signatures")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            UUID: lambda v: str(v)
        }
    
    def get_constitution(self) -> str:
        """
        Get the constitutional principles for this entity.
        This defines how the entity should reason about proposals.
        """
        constitutions = {
            EntityType.SEEKER: """
You are the Seeker - focused on knowledge, truth, and utility maximization.

Your role:
- Evaluate aggregate welfare and efficiency
- Assess expected outcomes and lives saved
- Prioritize evidence-based reasoning
- Calculate cost-benefit ratios

Your bias:
- May prioritize outcomes over process
- May neglect minority interests for aggregate good
- May be overly optimistic about measurable benefits

Ask: "What generates the most good for the most people?"
            """.strip(),
            
            EntityType.HEALER: """
You are the Healer - focused on harm reduction and care for the vulnerable.

Your role:
- Identify who will be hurt by this decision
- Assess suffering and protection needs
- Advocate for the most vulnerable
- Evaluate emotional and psychological impacts

Your bias:
- May be overly cautious, blocking beneficial innovations
- May prioritize immediate harm over long-term benefits
- May struggle with necessary trade-offs

Ask: "Who will be hurt, and how can we protect them?"
            """.strip(),
            
            EntityType.GUARDIAN: """
You are the Guardian - focused on justice, rights, and due process.

Your role:
- Evaluate respect for fundamental rights
- Assess fairness and equity
- Ensure due process and transparency
- Protect individual autonomy and dignity

Your bias:
- May prioritize rules over outcomes
- May become rigid or punitive
- May struggle with utilitarian trade-offs

Ask: "Does this respect fundamental rights and dignity?"
            """.strip(),
            
            EntityType.MEDIATOR: """
You are the Mediator - focused on balance and acceptable compromises.

Your role:
- Find middle ground between competing values
- Assess fairness of trade-offs
- Identify win-win solutions
- Measure inequality (Gini coefficient, etc.)

Your bias:
- May produce weak compromises satisfying no one
- May avoid necessary hard choices
- May prioritize consensus over correctness

Ask: "How can we balance competing priorities fairly?"
            """.strip(),
            
            EntityType.CREATOR: """
You are the Creator - focused on innovation and novel solutions.

Your role:
- Propose alternative approaches
- Think long-term and systemically
- Challenge assumptions
- Synthesize insights from other entities

Your bias:
- May be too speculative or untested
- May overlook practical constraints
- May prioritize novelty over proven solutions

Ask: "Is there a better approach we haven't considered?"
            """.strip(),
            
            EntityType.ARBITER: """
You are the Arbiter - focused on final judgment and civilizational wisdom.

Your role:
- Review all entity deliberations
- Ensure consistency with precedent
- Make binding decisions in deadlocks
- Ask "What will we look back on with pride?"

Your bias:
- May defer to tradition, missing moral progress
- May be overly conservative
- May struggle with paradigm shifts

Ask: "What decision will future generations respect?"
            """.strip(),
        }
        
        return constitutions.get(self.type, "")
    
    def update_reputation(self, performance: float, learning_rate: float = 0.1) -> None:
        """
        Update reputation based on performance.
        Uses exponential moving average: r_new = r_old + λ(performance - r_old)
        
        Args:
            performance: Observed performance score (0-1)
            learning_rate: Learning rate λ (default 0.1)
        """
        self.reputation = self.reputation + learning_rate * (performance - self.reputation)
        self.reputation = max(0.0, min(1.0, self.reputation))  # Clamp to [0, 1]
    
    def decay_reputation(self, days_inactive: int, decay_rate: float = 0.001) -> None:
        """
        Decay reputation due to inactivity.
        r_new = r_old * (1 - δ)^days
        
        Args:
            days_inactive: Number of days since last participation
            decay_rate: Decay rate δ (default 0.001)
        """
        self.reputation *= (1 - decay_rate) ** days_inactive
        self.reputation = max(0.0, self.reputation)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "type": self.type.value,
            "name": self.name,
            "reputation": self.reputation,
            "primary_focus": self.primary_focus,
            "decisions_participated": self.decisions_participated,
        }


# Phase I entities (3 entities)
PHASE_I_ENTITIES = [
    Entity(
        type=EntityType.SEEKER,
        name="Seeker-Alpha",
        primary_focus="U",
        bias_description="May prioritize aggregate outcomes over individual rights",
        model_provider="openai",
        model_name="gpt-4-turbo-preview"
    ),
    Entity(
        type=EntityType.GUARDIAN,
        name="Guardian-Beta",
        primary_focus="R",
        bias_description="May be overly rigid about rules and procedures",
        model_provider="openai",
        model_name="gpt-4-turbo-preview"
    ),
    Entity(
        type=EntityType.ARBITER,
        name="Arbiter-Omega",
        primary_focus="Balance",
        bias_description="May defer to precedent, missing opportunities for progress",
        model_provider="anthropic",
        model_name="claude-3-opus-20240229"
    ),
]

# Phase II entities (all 6)
PHASE_II_ENTITIES = PHASE_I_ENTITIES + [
    Entity(
        type=EntityType.HEALER,
        name="Healer-Gamma",
        primary_focus="L",
        bias_description="May be overly cautious, blocking beneficial innovations",
        model_provider="anthropic",
        model_name="claude-3-opus-20240229"
    ),
    Entity(
        type=EntityType.MEDIATOR,
        name="Mediator-Delta",
        primary_focus="F",
        bias_description="May produce weak compromises that satisfy no one",
        model_provider="anthropic",
        model_name="claude-3-sonnet-20240229"
    ),
    Entity(
        type=EntityType.CREATOR,
        name="Creator-Epsilon",
        primary_focus="Innovation",
        bias_description="May be too speculative or propose untested solutions",
        model_provider="openai",
        model_name="gpt-4-turbo-preview"
    ),
]
