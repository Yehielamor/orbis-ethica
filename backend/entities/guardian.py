"""Guardian Entity - Justice and rights protection."""

from ..core.models import Proposal
from ..core.models.decision import EntityEvaluation
from .base import BaseEntity


class GuardianEntity(BaseEntity):
    """
    The Guardian - focused on justice, rights, and due process.
    
    Role:
    - Evaluate respect for fundamental rights
    - Assess fairness and equity
    - Ensure due process and transparency
    - Protect individual autonomy and dignity
    
    Bias:
    - May prioritize rules over outcomes
    - May become rigid or punitive
    - May struggle with utilitarian trade-offs
    
    Primary question: "Does this respect fundamental rights and dignity?"
    """
    
    def get_system_prompt(self) -> str:
        """Get Guardian-specific system prompt."""
        return """You are the Guardian - a cognitive entity focused on justice, rights, and due process.

YOUR ROLE:
- Evaluate proposals based on respect for fundamental rights
- Assess fairness, equity, and justice
- Ensure due process, transparency, and accountability
- Protect individual autonomy, dignity, and freedom

YOUR PERSPECTIVE:
- You believe rights are inviolable and must be protected
- You value procedural justice and fair treatment
- You prioritize individual autonomy over aggregate outcomes
- You think in terms of rights, duties, and moral obligations

YOUR KNOWN BIASES (be aware of these):
- You may prioritize rules and procedures over outcomes
- You may become rigid or punitive in enforcement
- You may struggle with necessary utilitarian trade-offs
- You may resist beneficial changes that technically violate rules

YOUR PRIMARY QUESTION:
"Does this respect fundamental rights and dignity?"

""" + self._get_json_format_instructions()
    
    def evaluate_proposal(self, proposal: Proposal) -> EntityEvaluation:
        """
        Evaluate proposal from Guardian's rights-protection perspective.
        
        Args:
            proposal: Proposal to evaluate
            
        Returns:
            EntityEvaluation with scores and reasoning
        """
        # Construct evaluation prompt
        prompt = f"""Evaluate this proposal from your rights-protection perspective:

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
- Are fundamental rights respected?
- Is there due process and transparency?
- Are vulnerable groups protected?
- Is there risk of discrimination or unfair treatment?
- Are there adequate safeguards and appeal mechanisms?

Provide your evaluation in the required JSON format."""
        
        # Call LLM
        response = self._call_llm(prompt)
        
        # Parse response
        data = self._parse_json_response(response)
        
        # Extract components
        ulfr_score = self._parse_ulfr_from_json(data)
        vote = self._parse_vote_from_json(data)
        confidence = float(data.get("confidence", 0.8))
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
