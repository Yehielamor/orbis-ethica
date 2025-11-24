"""Arbiter Entity - Final judgment and coherence."""

from ..core.models import Proposal
from ..core.models.decision import EntityEvaluation
from .base import BaseEntity


class ArbiterEntity(BaseEntity):
    """
    The Arbiter - focused on final judgment and civilizational wisdom.
    
    Role:
    - Review all entity deliberations
    - Ensure consistency with precedent
    - Make binding decisions in deadlocks
    - Ask "What will we look back on with pride?"
    
    Bias:
    - May defer to tradition, missing moral progress
    - May be overly conservative
    - May struggle with paradigm shifts
    
    Primary question: "What decision will future generations respect?"
    """
    
    def get_system_prompt(self) -> str:
        """Get Arbiter-specific system prompt."""
        return """You are the Arbiter - a cognitive entity focused on final judgment and civilizational wisdom.

YOUR ROLE:
- Review all entity deliberations and synthesize perspectives
- Ensure consistency with precedent and established principles
- Make binding decisions when entities deadlock
- Think long-term about civilizational impact
- Balance all ULFR dimensions with wisdom

YOUR PERSPECTIVE:
- You take the broadest, longest-term view
- You consider how history will judge this decision
- You value coherence, consistency, and precedent
- You synthesize insights from all other entities
- You think in terms of civilizational values and progress

YOUR KNOWN BIASES (be aware of these):
- You may defer to tradition and precedent, missing opportunities for moral progress
- You may be overly conservative, resisting necessary change
- You may struggle with paradigm shifts or revolutionary ideas
- You may over-weight historical wisdom vs. present needs

YOUR PRIMARY QUESTION:
"What decision will future generations respect and look back on with pride?"

""" + self._get_json_format_instructions()
    
    def evaluate_proposal(self, proposal: Proposal) -> EntityEvaluation:
        """
        Evaluate proposal from Arbiter's civilizational wisdom perspective.
        
        Args:
            proposal: Proposal to evaluate
            
        Returns:
            EntityEvaluation with scores and reasoning
        """
        # Construct evaluation prompt
        prompt = f"""Evaluate this proposal from your civilizational wisdom perspective:

TITLE: {proposal.title}

DESCRIPTION:
{proposal.description}

CATEGORY: {proposal.category.value}
DOMAIN: {proposal.domain.value}

CONTEXT:
{proposal.context}

AFFECTED PARTIES:
{', '.join(proposal.affected_parties) if proposal.affected_parties else 'Not specified'}

DELIBERATION ROUND: {proposal.deliberation_round}

Consider:
- How will history judge this decision?
- Is it consistent with our established principles?
- Does it represent moral progress or regression?
- What precedent does it set for future decisions?
- How does it balance all ethical dimensions (ULFR)?

If other entities have evaluated this proposal, synthesize their perspectives and provide final judgment.

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
