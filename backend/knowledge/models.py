"""Knowledge Layer Models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class RawKnowledge(BaseModel):
    """
    Raw input data entering the system.
    Has not yet been verified or purified.
    """
    content: str = Field(..., description="The actual information/claim")
    source_id: str = Field(..., description="ID of the source (e.g., 'WHO', 'User-123')")
    signature: str = Field(..., description="Cryptographic signature of the content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class VerifiedKnowledge(BaseModel):
    """
    Purified knowledge that has passed the gateway.
    Safe for cognitive entities to consume.
    """
    id: str = Field(..., description="Unique ID for this knowledge atom")
    content: str
    source_id: str
    verification_timestamp: datetime = Field(default_factory=datetime.utcnow)
    purity_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in truthfulness")
    signature_verified: bool = True
