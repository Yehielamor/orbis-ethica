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
        self.active_challenges: Dict[str, str] = {} # source_id -> nonce

    def add_verified_source(self, source_id: str):
        """Add a source to the allowlist."""
        self.verified_sources.add(source_id)

    def create_challenge(self, source_id: str) -> str:
        """Generate a cryptographic nonce for the source to sign."""
        nonce = f"NONCE_{uuid.uuid4().hex}"
        self.active_challenges[source_id] = nonce
        print(f"🎲 [GATEWAY] Challenge created for {source_id}: {nonce}")
        return nonce

    def process_knowledge(self, raw: RawKnowledge) -> VerifiedKnowledge:
        """
        Main pipeline:
        1. Verify Source (Provenance)
        2. Verify Challenge Response (Integrity)
        3. Mint VerifiedKnowledge
        """
        print(f"🛡️ [GATEWAY] Processing incoming knowledge from: {raw.source_id}")
        
        # 1. Provenance Check
        self._verify_source(raw.source_id)
        
        # 2. Integrity Check (Challenge Response)
        self._verify_challenge_response(raw.source_id, raw.signature)
        
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

    def _verify_challenge_response(self, source_id: str, signature: str):
        """
        Verify that the source signed the active challenge.
        """
        # 1. Get active challenge
        nonce = self.active_challenges.get(source_id)
        if not nonce:
            print(f"⚠️ [GATEWAY] REJECTED: No active challenge for {source_id}")
            raise IntegrityError("No active challenge found. Request a challenge first.")

        # 2. Verify Signature
        # Mock Logic: Valid signature must be 'SIG_' + nonce
        # In production: verify_ed25519(nonce, signature, public_key)
        expected_signature = f"SIG_{nonce}"
        
        if signature != expected_signature:
            print(f"⚠️ [GATEWAY] INTEGRITY ALERT: Signature mismatch! Expected signature of {nonce}")
            raise IntegrityError("Invalid cryptographic signature for the challenge.")
            
        # 3. Consume challenge (replay protection)
        del self.active_challenges[source_id]
        print(f"✓ [GATEWAY] Challenge response verified.")
