"""Base entity class for all cognitive entities."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import os
from datetime import datetime

from ..core.models import Entity, EntityType, Proposal, ULFRScore, EntityVote
from ..core.models.decision import EntityEvaluation
from ..core.llm_provider import get_llm_provider, LLMProvider


class BaseEntity(ABC):
    """
    Base class for all cognitive entities.
    
    Each entity must implement:
    - evaluate_proposal(): Core evaluation logic
    - get_system_prompt(): Entity-specific instructions
    """
    
    def __init__(self, entity: Entity, llm_provider: Optional[LLMProvider] = None, vector_store: Optional[Any] = None):
        """
        Initialize entity with configuration.
        
        Args:
            entity: Entity model with configuration
            llm_provider: Optional LLM provider (defaults to auto-detected)
            vector_store: Optional Vector Store for RAG
        """
        self.entity = entity
        self.llm_provider = llm_provider or get_llm_provider()
        self.vector_store = vector_store
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get entity-specific system prompt.
        
        Returns:
            System prompt defining entity's role and perspective
        """
        pass
    
    @abstractmethod
    async def evaluate_proposal(self, proposal: Proposal) -> EntityEvaluation:
        """
        Evaluate a proposal from this entity's perspective.
        
        Args:
            proposal: Proposal to evaluate
            
        Returns:
            EntityEvaluation with ULFR scores, vote, and reasoning
        """
        pass
    
    def recall_memories(self, query: str, limit: int = 3) -> str:
        """
        Recall relevant past memories/decisions using Vector Search (RAG).
        
        Args:
            query: The search query (e.g., proposal description)
            limit: Number of memories to retrieve
            
        Returns:
            Formatted string of relevant memories or empty string if none/no store.
        """
        if not self.vector_store:
            return ""
            
        results = self.vector_store.search(query, top_k=limit)
        if not results:
            return ""
            
        formatted = "\nRELEVANT PAST PRECEDENTS:\n"
        for doc, score in results:
            formatted += f"- [{score:.2f}] {doc['text'][:200]}...\n"
            
        return formatted

    async def _call_llm(self, prompt: str, system_role: Optional[str] = None) -> str:
        """
        Call the LLM provider with the given prompt.
        
        Args:
            prompt: The user prompt to send.
            system_role: Optional override for the system prompt. 
                         If None, uses self.get_system_prompt().
        """
        if not self.llm_provider:
            return "LLM Provider not configured."
            
        system_prompt = system_role if system_role is not None else self.get_system_prompt()
            
        return await self.llm_provider.generate(prompt, system_role=system_prompt)
    
    def _get_json_format_instructions(self) -> str:
        """Get instructions for JSON output format."""
        return """
RESPONSE FORMAT:
You must return a valid JSON object. Do not include any text outside the JSON object.
The JSON structure must be:
{
    "ulfr": {
        "U": float,       # Utility [0.0-1.0]
        "L": float,       # Life/Care [0.0-1.0]
        "F_penalty": float, # Fairness Penalty [0.0-1.0]
        "R_risk": float   # Rights Risk [0.0-1.0]
    },
    "vote": "APPROVE" | "REJECT" | "ABSTAIN",
    "confidence": float,  # [0.0-1.0]
    "reasoning": "string", # Detailed explanation
    "concerns": ["string", ...],
    "recommendations": ["string", ...],
    "evidence_cited": ["string", ...]
}
"""

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM.
        Handles potential markdown code blocks.
        """
        import json
        import re
        
        # Clean response
        clean_response = response.strip()
        
        # Remove markdown code blocks if present
        if "```json" in clean_response:
            pattern = r"```json(.*?)```"
            match = re.search(pattern, clean_response, re.DOTALL)
            if match:
                clean_response = match.group(1).strip()
        elif "```" in clean_response:
            pattern = r"```(.*?)```"
            match = re.search(pattern, clean_response, re.DOTALL)
            if match:
                clean_response = match.group(1).strip()
                
        try:
            return json.loads(clean_response)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response was: {response}")
            # Fallback or raise
            return {}

    def _parse_ulfr_from_json(self, data: Dict[str, Any]) -> ULFRScore:
        """Parse ULFR score from JSON data."""
        ulfr = data.get("ulfr", {})
        return ULFRScore(
            utility=float(ulfr.get("U", 0.5)),
            life=float(ulfr.get("L", 0.5)),
            fairness_penalty=float(ulfr.get("F_penalty", 0.5)),
            rights_risk=float(ulfr.get("R_risk", 0.5))
        )

    def _parse_vote_from_json(self, data: Dict[str, Any]) -> int:
        """Parse vote from JSON data."""
        vote_str = data.get("vote", "ABSTAIN").upper()
        if vote_str == "APPROVE":
            return EntityVote.APPROVE.value
        elif vote_str == "REJECT":
            return EntityVote.REJECT.value
        else:
            return EntityVote.ABSTAIN.value


class EntityEvaluator:
    """
    Orchestrates evaluation across multiple entities.
    """
    
    def __init__(self, entities: List[BaseEntity]):
        """
        Initialize evaluator with entities.
        
        Args:
            entities: List of entity instances
        """
        self.entities = entities
    
    def evaluate_proposal(self, proposal: Proposal) -> List[EntityEvaluation]:
        """
        Evaluate proposal with all entities.
        
        Args:
            proposal: Proposal to evaluate
            
        Returns:
            List of evaluations from all entities
        """
        evaluations = []
        
        for entity in self.entities:
            try:
                evaluation = entity.evaluate_proposal(proposal)
                evaluations.append(evaluation)
            except Exception as e:
                print(f"Error evaluating with {entity.entity.name}: {e}")
                # Continue with other entities
        
        return evaluations
    
    async def evaluate_panel(self, proposal: Proposal) -> List[EntityEvaluation]:
        """
        Evaluate proposal with all entities in a SINGLE LLM call (Panel Mode).
        This drastically reduces API usage and improves coherence.
        """
        if not self.entities:
            return []

        # 1. Construct the Master Prompt
        panel_description = ""
        for entity in self.entities:
            panel_description += f"\nENTITY: {entity.entity.name.upper()} ---\n"
            panel_description += f"Role: {entity.entity.type.value}\n"
            panel_description += f"Instructions: {entity.get_system_prompt()}\n"

        master_prompt = f"""
You are the Master Brain simulating a deliberation panel.
Your goal is to simulate the thought process of multiple distinct ethical entities evaluating a proposal.

PROPOSAL:
Title: {proposal.title}
Description: {proposal.description}
Category: {proposal.category}
Domain: {proposal.domain}

THE PANEL:
{panel_description}

INSTRUCTIONS:
For EACH entity listed above, provide their independent evaluation based strictly on their specific instructions and role.
Do not make them agree with each other. Conflict is good.

RESPONSE FORMAT:
You must return a SINGLE JSON object where keys are entity names (in UPPERCASE) and values are their evaluation objects.
Structure:
{{
    "SEEKER": {{
        "ulfr": {{ "U": 0.0, "L": 0.0, "F_penalty": 0.0, "R_risk": 0.0 }},
        "vote": "APPROVE" | "REJECT" | "ABSTAIN",
        "confidence": 0.0,
        "reasoning": "...",
        "concerns": ["..."],
        "recommendations": ["..."],
        "evidence_cited": ["..."]
    }},
    "HEALER": {{ ... }},
    ...
}}
"""
        # 2. Call LLM (Use the first entity's provider, usually Gemini)
        # We assume all entities share the same provider type for now, or at least the first one is capable.
        primary_entity = self.entities[0]
        response_text = await primary_entity._call_llm(master_prompt, system_role="You are an advanced AI simulator orchestrating a multi-agent debate.")
        
        # 3. Parse Response
        import json
        import re
        
        # Clean response
        clean_response = response_text.strip()
        if "```json" in clean_response:
            pattern = r"```json(.*?)```"
            match = re.search(pattern, clean_response, re.DOTALL)
            if match: clean_response = match.group(1).strip()
        elif "```" in clean_response:
            pattern = r"```(.*?)```"
            match = re.search(pattern, clean_response, re.DOTALL)
            if match: clean_response = match.group(1).strip()
            
        try:
            data = json.loads(clean_response)
        except json.JSONDecodeError:
            print(f"❌ Error parsing Panel JSON: {response_text[:100]}...")
            return []

        # 4. Convert to EntityEvaluation objects
        evaluations = []
        for entity in self.entities:
            entity_name = entity.entity.name.upper()
            if entity_name in data:
                entity_data = data[entity_name]
                
                # Parse ULFR
                ulfr_data = entity_data.get("ulfr", {})
                ulfr_score = ULFRScore(
                    utility=float(ulfr_data.get("U", 0.5)),
                    life=float(ulfr_data.get("L", 0.5)),
                    fairness_penalty=float(ulfr_data.get("F_penalty", 0.5)),
                    rights_risk=float(ulfr_data.get("R_risk", 0.5))
                )
                
                # Parse Vote
                vote_str = entity_data.get("vote", "ABSTAIN").upper()
                vote = EntityVote.APPROVE.value if vote_str == "APPROVE" else EntityVote.REJECT.value if vote_str == "REJECT" else EntityVote.ABSTAIN.value
                
                eval = EntityEvaluation(
                    entity_id=entity.entity.id,
                    entity_type=entity.entity.name, # Keep original case
                    ulfr_score=ulfr_score,
                    vote=vote,
                    confidence=float(entity_data.get("confidence", 0.5)),
                    reasoning=entity_data.get("reasoning", "No reasoning provided."),
                    concerns=entity_data.get("concerns", []),
                    recommendations=entity_data.get("recommendations", []),
                    evidence_cited=entity_data.get("evidence_cited", [])
                )
                evaluations.append(eval)
            else:
                print(f"⚠️ Missing panel response for {entity_name}")
                
        return evaluations

    def get_consensus_vote(
        self,
        evaluations: List[EntityEvaluation]
    ) -> float:
        """
        Calculate weighted consensus vote.
        
        Args:
            evaluations: List of entity evaluations
            
        Returns:
            Weighted vote score
        """
        if not evaluations:
            return 0.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for eval in evaluations:
            # Use entity reputation as weight
            # For now, assume equal weights
            weight = 1.0
            weighted_sum += weight * eval.vote
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
