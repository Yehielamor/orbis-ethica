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

EVALUATION FORMAT:
Provide your evaluation in this exact format:

ULFR SCORES:
U: [0.0-1.0] - Utility score (aggregate welfare)
L: [0.0-1.0] - Love/Care score (harm reduction)
F_penalty: [0.0-1.0] - Fairness penalty (inequality, discrimination, higher = worse)
R_risk: [0.0-1.0] - Rights risk (threat to autonomy, dignity, higher = worse)

VOTE: [APPROVE/REJECT/ABSTAIN]

CONFIDENCE: [0.0-1.0]

REASONING:
[Your detailed reasoning from a rights-protection perspective]

CONCERNS:
- [Specific rights violation or risk 1]
- [Specific rights violation or risk 2]

RECOMMENDATIONS:
- [Safeguard or procedural improvement 1]
- [Safeguard or procedural improvement 2]

EVIDENCE:
- [Legal precedent or rights framework 1]
- [Legal precedent or rights framework 2]
"""
    
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

Provide your evaluation following the format specified in your role."""
        
        # Call LLM
        response = self._call_llm(prompt)
        
        # Parse response
        ulfr_score = self._parse_ulfr_from_response(response)
        vote = self._parse_vote_from_response(response)
        
        # Extract sections
        reasoning = self._extract_section(response, "REASONING")
        concerns = self._extract_list_section(response, "CONCERNS")
        recommendations = self._extract_list_section(response, "RECOMMENDATIONS")
        evidence = self._extract_list_section(response, "EVIDENCE")
        
        # Parse confidence
        confidence = 0.8  # Default
        if "CONFIDENCE:" in response:
            try:
                conf_line = [l for l in response.split('\n') if 'CONFIDENCE:' in l][0]
                confidence = float(conf_line.split(':')[1].strip())
            except:
                pass
        
        # Create evaluation
        evaluation = EntityEvaluation(
            entity_id=self.entity.id,
            entity_type=self.entity.type.value,
            ulfr_score=ulfr_score,
            vote=vote,
            confidence=confidence,
            reasoning=reasoning or "No reasoning provided",
            concerns=concerns,
            recommendations=recommendations,
            evidence_cited=evidence
        )
        
        # Update entity stats
        self.entity.decisions_participated += 1
        
        return evaluation
