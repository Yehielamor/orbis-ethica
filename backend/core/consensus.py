"""
Consensus Manager
Handles cryptographic signing and verification for Distributed Oracle Consensus.
Uses Ed25519 signatures (via PyNaCl) to ensure proposal authenticity.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError
from .models.proposal import Proposal

logger = logging.getLogger(__name__)

class ConsensusManager:
    """
    Manages cryptographic identity and consensus verification.
    """
    
    def __init__(self, key_path: str = "node_key.json"):
        self.key_path = key_path
        self._load_or_generate_keys()
        
    def _load_or_generate_keys(self):
        """Load Ed25519 keypair from disk or generate new one."""
        if os.path.exists(self.key_path):
            try:
                with open(self.key_path, 'r') as f:
                    data = json.load(f)
                    self.signing_key = SigningKey(data['private_key'], encoder=HexEncoder)
                    self.verify_key = self.signing_key.verify_key
                    logger.info(f"🔑 Loaded Node Identity: {self.get_public_key()[:16]}...")
            except Exception as e:
                logger.error(f"❌ Failed to load keys: {e}. Generating new ones.")
                self._generate_keys()
        else:
            self._generate_keys()
            
    def _generate_keys(self):
        """Generate a new Ed25519 keypair."""
        self.signing_key = SigningKey.generate()
        self.verify_key = self.signing_key.verify_key
        
        # Save to disk
        data = {
            "private_key": self.signing_key.encode(encoder=HexEncoder).decode('utf-8'),
            "public_key": self.verify_key.encode(encoder=HexEncoder).decode('utf-8')
        }
        
        # Ensure secure permissions (600)
        with open(self.key_path, 'w') as f:
            json.dump(data, f, indent=2)
        os.chmod(self.key_path, 0o600)
        
        logger.info(f"🔑 Generated New Node Identity: {data['public_key'][:16]}...")

    def get_public_key(self) -> str:
        """Get the public key in hex format."""
        return self.verify_key.encode(encoder=HexEncoder).decode('utf-8')

    def sign_proposal(self, proposal: Proposal) -> Proposal:
        """
        Sign a proposal with the node's private key.
        Updates the proposal with signature and content hash.
        """
        # 1. Create canonical content string
        content = self._get_canonical_content(proposal)
        
        # 2. Sign
        signed = self.signing_key.sign(content.encode('utf-8'))
        signature = signed.signature
        
        # 3. Update Proposal
        proposal.signature = HexEncoder.encode(signature).decode('utf-8')
        
        # Calculate content hash (SHA256 of canonical content)
        import hashlib
        proposal.content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Also set the submitter_id to our public key if not set (or we can append it)
        proposal.submitter_id = self.get_public_key()
        
        return proposal

    def sign_data(self, data: Dict[str, Any]) -> str:
        """
        Sign an arbitrary dictionary. Returns the signature in hex.
        """
        # 1. Canonicalize
        content = json.dumps(data, sort_keys=True)
        
        # 2. Sign
        signed = self.signing_key.sign(content.encode('utf-8'))
        return HexEncoder.encode(signed.signature).decode('utf-8')

    def verify_proposal(self, proposal: Proposal) -> bool:
        """
        Verify the signature of a proposal.
        """
        if not proposal.signature or not proposal.submitter_id:
            logger.warning("⚠️ Proposal missing signature or submitter_id")
            return False
            
        try:
            # 1. Reconstruct canonical content
            content = self._get_canonical_content(proposal)
            
            # 2. Get Verify Key from submitter_id (assuming submitter_id IS the public key)
            # In a real system, we'd look up the public key from a registry or PKI.
            # Here we assume the ID is the key itself (hex).
            verify_key = VerifyKey(proposal.submitter_id, encoder=HexEncoder)
            
            # 3. Verify
            verify_key.verify(content.encode('utf-8'), HexEncoder.decode(proposal.signature))
            return True
            
        except BadSignatureError:
            logger.error(f"❌ Invalid Signature for proposal {proposal.id}")
            return False
        except Exception as e:
            logger.error(f"❌ Verification error: {e}")
            return False

    def _get_canonical_content(self, proposal: Proposal) -> str:
        """
        Create a deterministic string representation of the proposal for signing.
        Excludes mutable fields like status, updated_at, etc.
        """
        data = {
            "id": str(proposal.id),
            "title": proposal.title,
            "description": proposal.description,
            "category": proposal.category.value,
            "domain": proposal.domain.value,
            "context": proposal.context
        }
        # Sort keys for determinism
        return json.dumps(data, sort_keys=True)

    def verify_poi(self, payload: Dict[str, Any], signature: str, miner_id: str) -> bool:
        """
        Verify a Proof of Inference (PoI) signature.
        Payload must include: shard_id, result_hash, miner_id, model, timestamp.
        """
        try:
            # 1. Reconstruct canonical content (must match Miner's signing logic)
            # We only sign the critical fields to avoid payload bloat issues
            sign_payload = {
                "shard_id": payload.get("shard_id"),
                "result_hash": payload.get("result_hash"), # Hash of the result content
                "miner_id": miner_id,
                "model": payload.get("model"),
                "timestamp": payload.get("timestamp")
            }
            
            content = json.dumps(sign_payload, sort_keys=True)
            
            # 2. Verify
            verify_key = VerifyKey(miner_id, encoder=HexEncoder)
            verify_key.verify(content.encode('utf-8'), HexEncoder.decode(signature))
            return True
            
        except BadSignatureError:
            logger.warning(f"❌ Invalid PoI Signature from {miner_id[:8]}")
            return False
        except Exception as e:
            logger.error(f"❌ PoI Verification error: {e}")
            return False
