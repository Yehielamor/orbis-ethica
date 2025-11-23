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

EVALUATION FORMAT:
Provide your evaluation in this exact format:

ULFR SCORES:
U: [0.0-1.0] - Utility score (long-term aggregate welfare)
L: [0.0-1.0] - life/Care score (compassion and protection)
F_penalty: [0.0-1.0] - Fairness penalty (injustice, higher = worse)
R_risk: [0.0-1.0] - Rights risk (threat to dignity, higher = worse)

VOTE: [APPROVE/REJECT/ABSTAIN]

CONFIDENCE: [0.0-1.0]

REASONING:
[Your detailed reasoning from a long-term, civilizational perspective]

SYNTHESIS:
[How you synthesize the perspectives of other entities]

PRECEDENT ANALYSIS:
[How this relates to past decisions and established principles]

CONCERNS:
- [Long-term concern 1]
- [Long-term concern 2]

RECOMMENDATIONS:
- [Wisdom-based recommendation 1]
- [Wisdom-based recommendation 2]

EVIDENCE:
- [Historical precedent or philosophical principle 1]
- [Historical precedent or philosophical principle 2]
"""
    
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

Provide your evaluation following the format specified in your role."""
        
        # Call LLM
        response = self._call_llm(prompt)
        
        # Parse response
        ulfr_score = self._parse_ulfr_from_response(response)
        vote = self._parse_vote_from_response(response)
        
        # Extract sections
        reasoning = self._extract_section(response, "REASONING")
        synthesis = self._extract_section(response, "SYNTHESIS")
        precedent = self._extract_section(response, "PRECEDENT ANALYSIS")
        concerns = self._extract_list_section(response, "CONCERNS")
        recommendations = self._extract_list_section(response, "RECOMMENDATIONS")
        evidence = self._extract_list_section(response, "EVIDENCE")
        
        # Combine reasoning with synthesis and precedent analysis
        full_reasoning = reasoning
        if synthesis:
            full_reasoning += f"\n\nSYNTHESIS:\n{synthesis}"
        if precedent:
            full_reasoning += f"\n\nPRECEDENT ANALYSIS:\n{precedent}"
        
        # Parse confidence
        confidence = 0.85  # Arbiter typically has high confidence
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
            reasoning=full_reasoning or "No reasoning provided",
            concerns=concerns,
            recommendations=recommendations,
            evidence_cited=evidence
        )
        
        # Update entity stats
        self.entity.decisions_participated += 1
        
        return evaluation
