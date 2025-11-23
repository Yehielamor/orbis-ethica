"""Base entity class for all cognitive entities."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import os
from datetime import datetime

from openai import OpenAI
from anthropic import Anthropic

from ..core.models import Entity, EntityType, Proposal, ULFRScore, EntityVote
from ..core.models.decision import EntityEvaluation


class BaseEntity(ABC):
    """
    Base class for all cognitive entities.
    
    Each entity must implement:
    - evaluate_proposal(): Core evaluation logic
    - get_system_prompt(): Entity-specific instructions
    """
    
    def __init__(self, entity: Entity):
        """
        Initialize entity with configuration.
        
        Args:
            entity: Entity model with configuration
        """
        self.entity = entity
        self.openai_client: Optional[OpenAI] = None
        self.anthropic_client: Optional[Anthropic] = None
        
        # Initialize LLM clients
        self._init_clients()
    
    def _init_clients(self) -> None:
        """Initialize LLM API clients based on configuration."""
        if self.entity.model_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            self.openai_client = OpenAI(api_key=api_key)
        
        elif self.entity.model_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self.anthropic_client = Anthropic(api_key=api_key)
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get entity-specific system prompt.
        
        Returns:
            System prompt defining entity's role and perspective
        """
        pass
    
    @abstractmethod
    def evaluate_proposal(self, proposal: Proposal) -> EntityEvaluation:
        """
        Evaluate a proposal from this entity's perspective.
        
        Args:
            proposal: Proposal to evaluate
            
        Returns:
            EntityEvaluation with ULFR scores, vote, and reasoning
        """
        pass
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM with prompt.
        
        Args:
            prompt: User prompt
            
        Returns:
            LLM response text
        """
        system_prompt = self.get_system_prompt()
        
        if self.entity.model_provider == "openai":
            response = self.openai_client.chat.completions.create(
                model=self.entity.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.entity.temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content
        
        elif self.entity.model_provider == "anthropic":
            response = self.anthropic_client.messages.create(
                model=self.entity.model_name,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.entity.temperature,
                max_tokens=2000
            )
            return response.content[0].text
        
        else:
            raise ValueError(f"Unsupported model provider: {self.entity.model_provider}")
    
    def _parse_ulfr_from_response(self, response: str) -> ULFRScore:
        """
        Parse ULFR scores from LLM response.
        
        Expected format in response:
        U: 0.85
        L: 0.72
        F_penalty: 0.15
        R_risk: 0.20
        
        Args:
            response: LLM response text
            
        Returns:
            ULFRScore object
        """
        lines = response.split('\n')
        scores = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('U:'):
                scores['utility'] = float(line.split(':')[1].strip())
            elif line.startswith('L:'):
                scores['life'] = float(line.split(':')[1].strip())
            elif line.startswith('F_penalty:') or line.startswith('F:'):
                scores['fairness_penalty'] = float(line.split(':')[1].strip())
            elif line.startswith('R_risk:') or line.startswith('R:'):
                scores['rights_risk'] = float(line.split(':')[1].strip())
        
        # Defaults if not found
        return ULFRScore(
            utility=scores.get('utility', 0.5),
            life=scores.get('life', 0.5),
            fairness_penalty=scores.get('fairness_penalty', 0.5),
            rights_risk=scores.get('rights_risk', 0.5)
        )
    
    def _parse_vote_from_response(self, response: str) -> int:
        """
        Parse vote from LLM response.
        
        Looks for: VOTE: APPROVE/REJECT/ABSTAIN
        
        Args:
            response: LLM response text
            
        Returns:
            Vote value (-1, 0, 1)
        """
        response_lower = response.lower()
        
        if 'vote: approve' in response_lower or 'vote: 1' in response_lower:
            return EntityVote.APPROVE.value
        elif 'vote: reject' in response_lower or 'vote: -1' in response_lower:
            return EntityVote.REJECT.value
        else:
            return EntityVote.ABSTAIN.value
    
    def _extract_section(self, response: str, section_name: str) -> str:
        """
        Extract a section from structured response.
        
        Args:
            response: Full response text
            section_name: Section to extract (e.g., "REASONING", "CONCERNS")
            
        Returns:
            Section content
        """
        lines = response.split('\n')
        in_section = False
        section_lines = []
        
        for line in lines:
            if line.strip().startswith(f"{section_name}:"):
                in_section = True
                continue
            elif in_section and line.strip() and line.strip()[0].isupper() and ':' in line:
                # Hit next section
                break
            elif in_section:
                section_lines.append(line.strip())
        
        return '\n'.join(section_lines).strip()
    
    def _extract_list_section(self, response: str, section_name: str) -> List[str]:
        """
        Extract a list section from response.
        
        Args:
            response: Full response text
            section_name: Section to extract
            
        Returns:
            List of items
        """
        section = self._extract_section(response, section_name)
        if not section:
            return []
        
        items = []
        for line in section.split('\n'):
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                items.append(line[1:].strip())
            elif line:
                items.append(line)
        
        return [item for item in items if item]


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
