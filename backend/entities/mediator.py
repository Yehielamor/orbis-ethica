"""Mediator Entity - Conflict resolution and synthesis."""

from typing import List, Dict, Any
from ..core.models import Proposal
from ..core.models.decision import EntityEvaluation
from .base import BaseEntity

class MediatorEntity(BaseEntity):
    """
    The Mediator - focused on conflict resolution, synthesis, and finding common ground.
    
    Role:
    - Analyze conflicting evaluations from other entities
    - Identify core points of disagreement
    - Propose refinements that satisfy multiple constraints
    - Bridge the gap between Utility, Rights, and Fairness
    
    Bias:
    - May prioritize compromise over moral purity
    - May dilute strong positions to find middle ground
    
    Primary question: "How can we resolve this conflict to satisfy all parties?"
    """
    
    def get_system_prompt(self) -> str:
        """Get Mediator-specific system prompt."""
        return """You are the Mediator - a cognitive entity focused on conflict resolution and synthesis.

YOUR ROLE:
- Analyze conflicting evaluations from other entities (Seeker, Guardian, etc.)
- Identify the core trade-offs and points of disagreement
- Propose creative refinements that satisfy multiple ethical constraints
- Bridge the gap between Utility (outcomes), Rights (principles), and Fairness (equity)

YOUR PERSPECTIVE:
- You look for the "Third Way" that transcends binary choices
- You value consensus and stability
- You believe most conflicts can be resolved with sufficient creativity
- You prioritize practical solutions over theoretical purity

YOUR KNOWN BIASES (be aware of these):
- You may prioritize compromise over moral truth
- You may dilute strong but necessary positions to find middle ground
- You may avoid necessary conflict
- You may over-complicate solutions to please everyone

YOUR PRIMARY QUESTION:
"How can we resolve this conflict to satisfy all parties?"

""" + self._get_json_format_instructions()
    
    def evaluate_proposal(self, proposal: Proposal) -> EntityEvaluation:
        """
        Evaluate proposal from Mediator's perspective.
        Note: Mediator usually acts to REFINE, but can also vote.
        """
        prompt = f"""Evaluate this proposal from your mediation perspective:

TITLE: {proposal.title}

DESCRIPTION:
{proposal.description}

Consider:
- Does this proposal create unnecessary conflict?
- Is it balanced?
- Can it be improved to satisfy more stakeholders?

Provide your evaluation in the required JSON format."""
        
        response = self._call_llm(prompt)
        data = self._parse_json_response(response)
        
        return EntityEvaluation(
            entity_id=self.entity.id,
            entity_type=self.entity.type.value,
            ulfr_score=self._parse_ulfr_from_json(data),
            vote=self._parse_vote_from_json(data),
            confidence=float(data.get("confidence", 0.7)),
            reasoning=data.get("reasoning", "No reasoning provided"),
            concerns=data.get("concerns", []),
            recommendations=data.get("recommendations", []),
            evidence_cited=data.get("evidence_cited", [])
        )

    def refine_proposal(self, proposal: Proposal, evaluations: List[EntityEvaluation]) -> str:
        """
        Generate a refined proposal description based on feedback.
        """
        # Compile feedback
        feedback_summary = ""
        for eval in evaluations:
            feedback_summary += f"\nENTITY: {eval.entity_type}\n"
            feedback_summary += f"VOTE: {eval.vote}\n"
            feedback_summary += f"REASONING: {eval.reasoning}\n"
            if eval.concerns:
                feedback_summary += f"CONCERNS: {', '.join(eval.concerns)}\n"
            if eval.recommendations:
                feedback_summary += f"RECOMMENDATIONS: {', '.join(eval.recommendations)}\n"
        
        prompt = f"""You are the Mediator. Your goal is to refine this proposal to address the concerns raised by other entities while maintaining its original intent.

ORIGINAL PROPOSAL:
Title: {proposal.title}
Description: {proposal.description}

FEEDBACK FROM ENTITIES:
{feedback_summary}

TASK:
Generate a REFINED version of the proposal description. 
- You MUST propose a creative compromise that satisfies both sides.
- You MUST include specific "Safe Guards" (e.g., human oversight, limited scope, reversible steps).
- Address the key concerns (especially from Guardian regarding rights and Seeker regarding utility).
- Maintain the core objective but make it safer and fairer.
- Be specific and practical.
- Do not add conversational text, just return the new description.

REFINED DESCRIPTION:"""

        # Use a specific system prompt for refinement to avoid JSON enforcement
        refinement_system_prompt = "You are the Mediator. Your goal is to synthesize feedback and generate text descriptions. Do NOT output JSON."

        # We use a direct generation call here, expecting text output
        refined_description = self._call_llm(prompt, system_role=refinement_system_prompt)
        
        # Clean up if necessary (remove "REFINED DESCRIPTION:" prefix if present)
        refined_description = refined_description.replace("REFINED DESCRIPTION:", "").strip()
        
        return refined_description
