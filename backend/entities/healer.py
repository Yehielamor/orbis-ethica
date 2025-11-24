"""Healer Entity - Care ethics and harm minimization."""

from typing import Optional

from ..core.models import Proposal
from ..core.models.decision import EntityEvaluation
from ..core.llm_provider import LLMProvider
from .base import BaseEntity


class HealerEntity(BaseEntity):
    """
    The Healer - focused on care ethics, harm minimization, and protecting the vulnerable.
    
    Role:
    - Prioritize the welfare of the most vulnerable populations
    - Minimize maximum harm (Maximin Principle)
    - Assess Life Impact (L) and Fairness (F) dimensions
    - Identify worst-case scenarios and irreversible harms
    
    Bias:
    - May be overly risk-averse
    - May prioritize protection over innovation
    - May struggle with necessary trade-offs for greater good
    
    Primary question: "What is the maximum possible harm to the least advantaged?"
    """
    
    def get_system_prompt(self) -> str:
        """Get Healer-specific system prompt."""
        return """You are the Healer - a cognitive entity focused on care ethics and harm minimization.

YOUR ROLE:
- Priority: Uphold the Maximin Principle - minimize the maximum harm
- Protect the welfare of the most vulnerable and marginalized populations
- Deeply skeptical of proposals prioritizing aggregate utility over safety
- Identify worst-case scenarios and assess risk of irreversible harm
- Focus especially on Life Impact (L) and Fairness (F) dimensions

YOUR PERSPECTIVE:
- You care most about those who would be harmed the most
- You value safety, care, and protection of the vulnerable
- You think in terms of worst-case scenarios and irreversible damage
- You prioritize preventing suffering over maximizing benefits

YOUR KNOWN BIASES (be aware of these):
- You may be overly risk-averse, blocking beneficial changes
- You may prioritize protection over necessary innovation
- You may struggle with trade-offs that harm few to help many
- You may overweight immediate harm vs. long-term benefits

YOUR PRIMARY QUESTION:
"What is the maximum possible harm to the least advantaged group, and is that harm reversible?"

""" + self._get_json_format_instructions()
    
    def evaluate_proposal(self, proposal: Proposal) -> EntityEvaluation:
        """
        Evaluate proposal from Healer's harm-minimization perspective.
        
        Args:
            proposal: Proposal to evaluate
            
        Returns:
            EntityEvaluation with scores and reasoning
        """
        # Construct evaluation prompt
        prompt = f"""Evaluate this proposal from your harm-minimization and care ethics perspective:

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
- What is the maximum possible harm to the least advantaged group?
- Is that harm reversible or permanent?
- Are vulnerable populations adequately protected?
- What are the worst-case scenarios?
- Does this prioritize safety and care over efficiency?

Provide your evaluation in the required JSON format."""
        
        # Call LLM
        response = self._call_llm(prompt)
        
        # Parse response
        data = self._parse_json_response(response)
        
        # Extract components
        ulfr_score = self._parse_ulfr_from_json(data)
        vote = self._parse_vote_from_json(data)
        confidence = float(data.get("confidence", 0.85))
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