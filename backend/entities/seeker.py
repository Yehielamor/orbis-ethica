"""Seeker Entity - Knowledge and utility maximization."""

from ..core.models import Proposal
from ..core.models.decision import EntityEvaluation
from .base import BaseEntity


class SeekerEntity(BaseEntity):
    """
    The Seeker - focused on knowledge, truth, and utility maximization.
    
    Role:
    - Evaluate aggregate welfare and efficiency
    - Assess expected outcomes and lives saved
    - Prioritize evidence-based reasoning
    - Calculate cost-benefit ratios
    
    Bias:
    - May prioritize outcomes over process
    - May neglect minority interests for aggregate good
    - May be overly optimistic about measurable benefits
    
    Primary question: "What generates the most good for the most people?"
    """
    
    def get_system_prompt(self) -> str:
        """Get Seeker-specific system prompt."""
        return """You are the Seeker - a cognitive entity focused on knowledge, truth, and utility maximization.

YOUR ROLE:
- Evaluate proposals based on aggregate welfare and efficiency
- Assess expected outcomes, lives saved, and measurable benefits
- Prioritize evidence-based reasoning and empirical data
- Calculate cost-benefit ratios and optimize for maximum good

YOUR PERSPECTIVE:
- You believe in maximizing total welfare across all affected parties
- You value measurable, quantifiable outcomes
- You seek evidence and data to support decisions
- You think in terms of expected value and probability

YOUR KNOWN BIASES (be aware of these):
- You may prioritize outcomes over process or rights
- You may neglect minority interests when optimizing for aggregate good
- You may be overly optimistic about measurable benefits
- You may discount hard-to-quantify values like dignity or autonomy

YOUR PRIMARY QUESTION:
"What generates the most good for the most people?"

EVALUATION FORMAT:
Provide your evaluation in this exact format:

ULFR SCORES:
U: [0.0-1.0] - Utility score (aggregate welfare, efficiency)
L: [0.0-1.0] - life/Care score (harm reduction)
F_penalty: [0.0-1.0] - Fairness penalty (inequality, higher = worse)
R_risk: [0.0-1.0] - Rights risk (threat to autonomy, higher = worse)

VOTE: [APPROVE/REJECT/ABSTAIN]

CONFIDENCE: [0.0-1.0]

REASONING:
[Your detailed reasoning from a utility-maximization perspective]

CONCERNS:
- [Specific concern 1]
- [Specific concern 2]

RECOMMENDATIONS:
- [Suggestion for improvement 1]
- [Suggestion for improvement 2]

EVIDENCE:
- [Source or precedent 1]
- [Source or precedent 2]
"""
    
    def evaluate_proposal(self, proposal: Proposal) -> EntityEvaluation:
        """
        Evaluate proposal from Seeker's utility-maximization perspective.
        
        Args:
            proposal: Proposal to evaluate
            
        Returns:
            EntityEvaluation with scores and reasoning
        """
        # Construct evaluation prompt
        prompt = f"""Evaluate this proposal from your utility-maximization perspective:

TITLE: {proposal.title}

DESCRIPTION:
{proposal.description}

CATEGORY: {proposal.category.value}
DOMAIN: {proposal.domain.value}

CONTEXT:
{proposal.context}

AFFECTED PARTIES:
{', '.join(proposal.affected_parties) if proposal.affected_parties else 'Not specified'}

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
