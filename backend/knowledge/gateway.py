"""Knowledge Purification Gateway."""

import uuid
from datetime import datetime
from typing import List, Set

from .models import RawKnowledge, VerifiedKnowledge

class AccessDenied(Exception):
    """Raised when source is not in the allowed list."""
    pass

class IntegrityError(Exception):
    """Raised when cryptographic signature is invalid."""
    pass

class KnowledgeGateway:
    """
    The Gatekeeper of Orbis Ethica.
    Filters raw information before it reaches the cognitive core.
    """
    
    def __init__(self, verified_sources: List[str] = None):
        self.verified_sources: Set[str] = set(verified_sources or [])
    
    def add_verified_source(self, source_id: str):
        """Add a source to the allowlist."""
        self.verified_sources.add(source_id)

    def process_knowledge(self, raw: RawKnowledge) -> VerifiedKnowledge:
        """
        Main pipeline:
        1. Verify Source (Provenance)
        2. Verify Signature (Integrity)
        3. Mint VerifiedKnowledge
        """
        print(f"🛡️ [GATEWAY] Processing incoming knowledge from: {raw.source_id}")
        
        # 1. Provenance Check
        self._verify_source(raw.source_id)
        
        # 2. Integrity Check
        self._verify_signature(raw.content, raw.signature)
        
        # 3. Minting
        print(f"✅ [GATEWAY] Knowledge verified. Minting atom.")
        return VerifiedKnowledge(
            id=str(uuid.uuid4()),
            content=raw.content,
            source_id=raw.source_id,
            verification_timestamp=datetime.utcnow(),
            purity_score=1.0, # Initial score for fully verified sources
            signature_verified=True
        )

    def _verify_source(self, source_id: str):
        """Check if source is in the trusted list."""
        if source_id not in self.verified_sources:
            print(f"⛔ [GATEWAY] BLOCKED: Unknown source '{source_id}'")
            raise AccessDenied(f"Source '{source_id}' is not verified.")
        print(f"✓ [GATEWAY] Source '{source_id}' is verified.")

    def _verify_signature(self, content: str, signature: str):
        """
        Verify cryptographic signature.
        
        NOTE: For this learning phase, we use a simple mock.
        Real implementation would use public/private key crypto (e.g., Ed25519).
        
        Mock Logic: Valid signature must be 'SIG_' + reverse(content).
        """
        # Simple mock verification logic
        expected_signature = f"SIG_{content[::-1]}"
        
        if signature != expected_signature:
            print(f"⚠️ [GATEWAY] INTEGRITY ALERT: Signature mismatch!")
            raise IntegrityError("Invalid cryptographic signature.")
            
        print(f"✓ [GATEWAY] Signature verified.")
