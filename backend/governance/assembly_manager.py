"""
Assembly Manager - Handles Sortition and Sybil Resistance.
Implements Proof-of-Attention (PoA) and Random Selection.
"""

import time
import random
import hashlib
from typing import List, Dict, Optional, Any
from uuid import uuid4, UUID
from pydantic import BaseModel, Field

class HumanCandidate(BaseModel):
    """Represents a verified human candidate for the assembly."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    verified_at: float
    poa_score: float  # Proof of Attention score


class PoolManager:
    """
    Manages the pool of human candidates for the Global Ethical Assembly.
    """
    
    def __init__(self):
        self.pool: Dict[str, HumanCandidate] = {}
        self.min_poa_time = 7.0  # Seconds required for PoA (mock)

    def verify_proof_of_attention(self, time_spent: float, challenge_response: str) -> bool:
        """
        Verify Proof-of-Attention.
        In a real system, this would verify CAPTCHA and interaction logs.
        """
        # Mock verification
        if time_spent < self.min_poa_time:
            return False
            
        # Mock challenge verification (e.g., hash matching)
        # For now, just check if response is not empty
        return bool(challenge_response)

    def enroll_human(self, name: str, attestation: Dict[str, Any]) -> Optional[HumanCandidate]:
        """
        Enroll a human into the pool after verification.
        
        Args:
            name: Candidate name
            attestation: Proof data (time_spent, challenge_response)
            
        Returns:
            HumanCandidate if successful, None otherwise
        """
        time_spent = attestation.get("time_spent", 0.0)
        challenge_response = attestation.get("challenge_response", "")
        
        if not self.verify_proof_of_attention(time_spent, challenge_response):
            print(f"Failed PoA for {name}: Insufficient attention or invalid challenge.")
            return None
            
        # Create candidate
        candidate = HumanCandidate(
            name=name,
            verified_at=time.time(),
            poa_score=time_spent / self.min_poa_time  # Simple score
        )
        
        self.pool[candidate.id] = candidate
        print(f"Enrolled {name} (ID: {candidate.id}) into the pool.")
        return candidate

    def select_assembly(self, size: int, seed: Optional[str] = None) -> List[HumanCandidate]:
        """
        Select a random assembly from the pool using Sortition.
        
        Args:
            size: Number of members to select
            seed: Cryptographic seed for reproducibility
            
        Returns:
            List of selected candidates
        """
        candidates = list(self.pool.values())
        
        if len(candidates) < size:
            print(f"Warning: Pool size ({len(candidates)}) is smaller than requested assembly size ({size}). Returning all.")
            return candidates
            
        # Use cryptographic seed if provided
        if seed:
            random.seed(seed)
            
        selected = random.sample(candidates, size)
        return selected

    def get_pool_size(self) -> int:
        return len(self.pool)
