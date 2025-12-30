"""Burn Protocol Models."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class BurnOffenseType(str, Enum):
    """Types of offenses that trigger a burn."""
    BIAS_INJECTION = "bias_injection"
    DATA_POISONING = "data_poisoning"
    DRIFT_DETECTED = "drift_detected"
    SIGNATURE_MISMATCH = "signature_mismatch"
    MANIPULATION_ATTEMPT = "manipulation_attempt"

class BurnEvent(BaseModel):
    """
    Represents a Burn Event - a permanent record of corruption and penalty.
    
    White Paper Section 3.6.2:
    - Date
    - Perpetrator
    - Offense
    - Evidence
    - Council Vote
    - Penalty
    """
    id: str = Field(..., description="Unique Burn Event ID (UUID)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    perpetrator_id: str = Field(..., description="ID of the corrupted entity")
    offense_type: BurnOffenseType
    description: str = Field(..., description="Detailed description of the offense")
    
    evidence: Dict[str, Any] = Field(
        ..., 
        description="Forensic evidence (e.g., p-values, logs, signatures)"
    )
    
    penalty: Dict[str, Any] = Field(
        ...,
        description="Applied penalties (e.g., reputation_burned, ban_duration)"
    )
    
    council_vote_percentage: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Percentage of council voting for burn"
    )
    
    is_public: bool = Field(
        default=True,
        description="Burn events are always public by default"
    )

    def to_markdown(self) -> str:
        """Format as a public notice (Eternal Record)."""
        return f"""
# 🔥 BURN EVENT #{self.id[:8]} 🔥
**Date**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Perpetrator**: {self.perpetrator_id}
**Offense**: {self.offense_type.value.upper()} - {self.description}

## 🕵️ Evidence
{self._format_dict(self.evidence)}

## ⚖️ Council Verdict
**Vote**: {self.council_vote_percentage * 100:.1f}% BURN

## 📉 Penalty Applied
{self._format_dict(self.penalty)}

> "No one is above the protocol."
"""

    def _format_dict(self, d: Dict[str, Any]) -> str:
        return "\n".join([f"- **{k}**: {v}" for k, v in d.items()])
