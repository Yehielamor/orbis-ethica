import os
import json
import base64
from typing import Optional, Tuple
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import HexEncoder, Base64Encoder
from nacl.exceptions import BadSignatureError

class NodeIdentity:
    """
    Manages the cryptographic identity of a P2P node.
    Uses Ed25519 for signing and verification.
    """
    
    def __init__(self, key_dir: str = ".keys", node_id: str = "default_node"):
        self.key_dir = key_dir
        self.node_id = node_id
        self.signing_key: Optional[SigningKey] = None
        self.verify_key: Optional[VerifyKey] = None
        
        # Ensure key directory exists
        os.makedirs(self.key_dir, exist_ok=True)
        
        # Load or Generate Keys
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        """Load keys from disk or generate new ones if they don't exist."""
        private_key_path = os.path.join(self.key_dir, f"{self.node_id}.sk")
        public_key_path = os.path.join(self.key_dir, f"{self.node_id}.pk")
        
        if os.path.exists(private_key_path) and os.path.exists(public_key_path):
            # Load existing
            with open(private_key_path, "rb") as f:
                self.signing_key = SigningKey(f.read(), encoder=HexEncoder)
            with open(public_key_path, "r") as f:
                # We don't strictly need to read the public key file as we can derive it,
                # but it's good to check consistency.
                pass
            print(f"🔑 Loaded existing identity for {self.node_id}")
        else:
            # Generate new
            self.signing_key = SigningKey.generate()
            
            # Save to disk
            with open(private_key_path, "wb") as f:
                f.write(self.signing_key.encode(encoder=HexEncoder))
            
            with open(public_key_path, "wb") as f:
                f.write(self.signing_key.verify_key.encode(encoder=HexEncoder))
                
            print(f"🔑 Generated NEW identity for {self.node_id}")
            
        self.verify_key = self.signing_key.verify_key

    @property
    def public_key_hex(self) -> str:
        """Return public key as hex string."""
        return self.verify_key.encode(encoder=HexEncoder).decode('utf-8')

    def sign(self, message: dict) -> str:
        """
        Sign a dictionary message.
        Returns the signature as a hex string.
        The message is canonicalized (sorted keys) before signing.
        """
        # Canonicalize JSON
        message_bytes = json.dumps(message, sort_keys=True).encode('utf-8')
        signed = self.signing_key.sign(message_bytes)
        return signed.signature.hex()

    @staticmethod
    def verify(message: dict, signature: str, public_key_hex: str) -> bool:
        """
        Verify a signature for a message.
        """
        try:
            verify_key = VerifyKey(public_key_hex, encoder=HexEncoder)
            message_bytes = json.dumps(message, sort_keys=True).encode('utf-8')
            signature_bytes = bytes.fromhex(signature)
            verify_key.verify(message_bytes, signature_bytes)
            return True
        except (BadSignatureError, ValueError):
            return False
