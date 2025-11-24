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

""" + self._get_json_format_instructions()
    
    def _format_evidence(self, evidence_list) -> str:
        """Format verified evidence for the prompt."""
        if not evidence_list:
            return "No verified evidence provided."
        
        formatted = []
        for ev in evidence_list:
            formatted.append(f"- {ev.content} (Source: {ev.source_id}, Purity: {ev.purity_score})")
        return "\n".join(formatted)

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

VERIFIED EVIDENCE (From Knowledge Gateway):
{self._format_evidence(proposal.evidence)}

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
