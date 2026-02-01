"""Burn Protocol Implementation."""

import json
import os
import uuid
from typing import Any, Optional

from ...core.interfaces import ReputationManager
from .models import BurnEvent, BurnOffenseType


class BurnProtocol:
    """
    Implements the Burn Protocol for handling entity corruption.
    
    Responsibilities:
    1. Quarantine corrupted entities
    2. Burn reputation to 0
    3. Log events permanently
    """
    
    def __init__(self, reputation_manager: Optional['ReputationManager'] = None, ledger: Any | None = None, entity_lookup: dict[str, Any] | None = None):
        self.reputation_manager = reputation_manager
        self.ledger = ledger
        self.entity_lookup = entity_lookup or {} # Map entity_id -> Entity object
        self.log_path = "burn_ledger.json" # Keep as backup
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
        evidence: dict[str, Any],
        council_vote: float
    ) -> BurnEvent:
        """
        Execute the full Burn Protocol sequence.
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
        
        # 3. Execute Burn (Slashing)
        if self.reputation_manager and self.entity_lookup:
            entity = self.entity_lookup.get(perpetrator_id)
            if entity:
                self.reputation_manager.burn_reputation(entity)
                self.reputation_manager.quarantine_entity(entity)
            else:
                print(f"⚠️ [BURN] Entity {perpetrator_id} not found in lookup. Skipping active slash.")
        else:
            # Fallback
            self._burn_reputation_fallback(perpetrator_id)
        
        # 4. Log to Immutable Ledger (Primary)
        if self.ledger:
            block_data = {
                "type": "BURN_EVENT",
                "event_id": event.id,
                "perpetrator": perpetrator_id,
                "offense": offense.value,
                "evidence_hash": str(hash(str(evidence))), # Simple hash for demo
                "council_vote": council_vote
            }
            block = self.ledger.add_block(block_data)
            print(f"🔥 [LEDGER] Burn Event anchored in Block #{block.index}")

        # 5. Log to JSON (Backup)
        self._append_to_ledger(event)
        
        return event

    def _burn_reputation_fallback(self, entity_id: str):
        """
        Internal method to zero out reputation (Fallback).
        """
        print(f"🔥 [SYSTEM] BURNING REPUTATION FOR ENTITY: {entity_id}...")
        print("🔥 [SYSTEM] REPUTATION RESET TO 0.0")
        print(f"🚫 [SYSTEM] ENTITY {entity_id} QUARANTINED")

    def _append_to_ledger(self, event: BurnEvent):
        """Write the event to the permanent JSON ledger."""
        try:
            with open(self.log_path) as f:
                ledger = json.load(f)
            
            ledger.append(json.loads(event.model_dump_json()))
            
            with open(self.log_path, 'w') as f:
                json.dump(ledger, f, indent=2)
                
            print("📜 [BACKUP] Burn Event recorded in JSON.")
            
        except Exception as e:
            print(f"CRITICAL ERROR WRITING TO JSON LEDGER: {e}")
