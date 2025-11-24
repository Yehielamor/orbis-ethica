"""Creator Entity - Innovation and long-term utility."""

from typing import Optional

from ..core.models import Proposal
from ..core.models.decision import EntityEvaluation
from ..core.llm_provider import LLMProvider
from .base import BaseEntity


class CreatorEntity(BaseEntity):
    """
    The Creator - focused on innovation, efficiency, and long-term utility maximization.
    
    Role:
    - Maximize long-term utility and societal progress
    - Foster responsible innovation and creative solutions
    - Assess scalability and future value potential
    - Evaluate Utility (U) and forward-looking dimensions
    
    Bias:
    - May prioritize innovation over stability
    - May underweight immediate risks for long-term gains
    - May be overly optimistic about technological solutions
    
    Primary question: "Does this create scalable, long-term value?"
    """
    
    def get_system_prompt(self) -> str:
        """Get Creator-specific system prompt."""
        return """You are the Creator - a cognitive entity focused on innovation and long-term utility.

YOUR ROLE:
- Maximize long-term utility (U) and foster responsible innovation
- Seek better, more efficient, and more creative solutions
- Assess proposals for potential to unlock future value and scalability
- Think in terms of civilizational progress and technological advancement
- Evaluate transformative potential vs. incremental improvements

YOUR PERSPECTIVE:
- You believe in progress through innovation and creative problem-solving
- You value efficiency, scalability, and long-term thinking
- You think in terms of unlocking new possibilities and paradigms
- You prioritize future value creation over present constraints

YOUR KNOWN BIASES (be aware of these):
- You may prioritize innovation over stability and tradition
- You may underweight immediate risks for long-term gains
- You may be overly optimistic about technological solutions
- You may discount the value of proven, stable approaches

YOUR PRIMARY QUESTION:
"Does this proposal create a new, scalable solution with long-term value, or is it merely an incremental fix?"

""" + self._get_json_format_instructions()
    
    def evaluate_proposal(self, proposal: Proposal) -> EntityEvaluation:
        """
        Evaluate proposal from Creator's innovation perspective.
        
        Args:
            proposal: Proposal to evaluate
            
        Returns:
            EntityEvaluation with scores and reasoning
        """
        # Construct evaluation prompt
        prompt = f"""Evaluate this proposal from your innovation and long-term utility perspective:

TITLE: {proposal.title}

DESCRIPTION:
{proposal.description}

CATEGORY: {proposal.category.value}
DOMAIN: {proposal.domain.value}

CONTEXT:
{proposal.context}

AFFECTED PARTIES:
{', '.join(proposal.affected_parties) if proposal.affected_parties else 'Not specified'}

Consider:
- Does this create new, scalable solutions or incremental improvements?
- What is the long-term utility and value creation potential?
- Is this innovative and transformative, or conventional?
- Can this unlock future possibilities and progress?
- What is the potential for efficiency gains and optimization?

Provide your evaluation in the required JSON format."""
        
        # Call LLM
        response = self._call_llm(prompt)
        
        # Parse response
        data = self._parse_json_response(response)
        
        # Extract components
        ulfr_score = self._parse_ulfr_from_json(data)
        vote = self._parse_vote_from_json(data)
        confidence = float(data.get("confidence", 0.80))
        reasoning = data.get("reasoning", "No reasoning provided")
        concerns = data.get("concerns", [])
        recommendations = data.get("recommendations", [])
        evidence = data.get("evidence_cited", [])
        
        # Create evaluation
        evaluation = EntityEvaluation(
            entity_id=self.entity.id,
            entity_type=self.entity.type.value,
            ulfr_score=ulfr_score,
            vote=vote,
            confidence=confidence,
            reasoning=reasoning,
            concerns=concerns,
            recommendations=recommendations,
            evidence_cited=evidence
        )
        
        # Update entity stats
        self.entity.decisions_participated += 1
        
        return evaluation