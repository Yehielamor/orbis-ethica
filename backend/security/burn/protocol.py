"""Burn Protocol Implementation."""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

from .models import BurnEvent, BurnOffenseType
from ...core.interfaces import ReputationManager

class BurnProtocol:
    """
    Implements the Burn Protocol for handling entity corruption.
    
    Responsibilities:
    1. Quarantine corrupted entities
    2. Burn reputation to 0
    3. Log events permanently
    """
    
    def __init__(self, reputation_manager: Optional['ReputationManager'] = None, log_path: str = "burn_ledger.json"):
        self.reputation_manager = reputation_manager
        self.log_path = log_path
        self._ensure_log_exists()
    
    def _ensure_log_exists(self):
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w') as f:
                json.dump([], f)

    def execute_burn(
        self, 
        perpetrator_id: str, 
        offense: BurnOffenseType, 
        description: str,
        evidence: Dict[str, Any],
        council_vote: float
    ) -> BurnEvent:
        """
        Execute the full Burn Protocol sequence.
        
        Args:
            perpetrator_id: ID of the entity to burn
            offense: Type of offense
            description: Details
            evidence: Proof of corruption
            council_vote: Percentage of council support (must be > 0.66)
            
        Returns:
            The created BurnEvent
        """
        # 1. Validation
        if council_vote < 0.66:
            raise ValueError("Insufficient council vote for Burn (min 66%)")
            
        # 2. Create Event
        event = BurnEvent(
            id=str(uuid.uuid4()),
            perpetrator_id=perpetrator_id,
            offense_type=offense,
            description=description,
            evidence=evidence,
            penalty={
                "reputation_burned": "ALL (Reset to 0.0)",
                "status": "QUARANTINED",
                "ban_duration": "PERMANENT"
            },
            council_vote_percentage=council_vote
        )
        
        # 3. Execute Burn
        if self.reputation_manager:
            self.reputation_manager.burn_reputation(perpetrator_id)
            self.reputation_manager.quarantine_entity(perpetrator_id)
        else:
            # Fallback for when no manager is provided (e.g. simple script run)
            self._burn_reputation_fallback(perpetrator_id)
        
        # 4. Log to Eternal Record
        self._append_to_ledger(event)
        
        return event

    def _burn_reputation_fallback(self, entity_id: str):
        """
        Internal method to zero out reputation (Fallback).
        """
        print(f"🔥 [SYSTEM] BURNING REPUTATION FOR ENTITY: {entity_id}...")
        print(f"🔥 [SYSTEM] REPUTATION RESET TO 0.0")
        print(f"🚫 [SYSTEM] ENTITY {entity_id} QUARANTINED")

    def _append_to_ledger(self, event: BurnEvent):
        """Write the event to the permanent JSON ledger."""
        try:
            with open(self.log_path, 'r') as f:
                ledger = json.load(f)
            
            ledger.append(json.loads(event.model_dump_json()))
            
            with open(self.log_path, 'w') as f:
                json.dump(ledger, f, indent=2)
                
            print(f"📜 [LEDGER] Burn Event #{event.id[:8]} recorded successfully.")
            
        except Exception as e:
            print(f"CRITICAL ERROR WRITING TO LEDGER: {e}")
