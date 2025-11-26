import os
import json
import base64
from typing import Optional, Tuple
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import HexEncoder, Base64Encoder
from nacl.exceptions import BadSignatureError

# Cryptography for KMS
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

class NodeIdentity:
    """
    Manages the cryptographic identity of a P2P node.
    Uses Ed25519 for signing and verification.
    Supports AES-256-GCM encryption for private keys at rest.
    """
    
    def __init__(self, key_dir: str = ".keys", node_id: str = "default_node", password: Optional[str] = None):
        self.key_dir = key_dir
        self.node_id = node_id
        self.password = password
        self.signing_key: Optional[SigningKey] = None
        self.verify_key: Optional[VerifyKey] = None
        
        # Ensure key directory exists
        os.makedirs(self.key_dir, exist_ok=True)
        
        # Load or Generate Keys
        self._load_or_generate_keys()

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive a 32-byte key from the password using Scrypt."""
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
        )
        return kdf.derive(password.encode())

    def _encrypt_private_key(self, key_bytes: bytes, password: str) -> str:
        """Encrypt private key bytes using AES-256-GCM."""
        salt = os.urandom(16)
        derived_key = self._derive_key(password, salt)
        aesgcm = AESGCM(derived_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, key_bytes, None)
        
        return json.dumps({
            "version": 1,
            "salt": base64.b64encode(salt).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "tag": "aes-256-gcm"
        })

    def _decrypt_private_key(self, encrypted_json: str, password: str) -> bytes:
        """Decrypt private key from JSON string."""
        try:
            data = json.loads(encrypted_json)
            salt = base64.b64decode(data['salt'])
            nonce = base64.b64decode(data['nonce'])
            ciphertext = base64.b64decode(data['ciphertext'])
            
            derived_key = self._derive_key(password, salt)
            aesgcm = AESGCM(derived_key)
            return aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            raise ValueError(f"Decryption failed: {e} (Wrong password?)")

    def _load_or_generate_keys(self):
        """Load keys from disk or generate new ones if they don't exist."""
        private_key_path = os.path.join(self.key_dir, f"{self.node_id}.sk")
        public_key_path = os.path.join(self.key_dir, f"{self.node_id}.pk")
        
        if os.path.exists(private_key_path):
            # Load existing
            with open(private_key_path, "rb") as f:
                content = f.read()
                
            try:
                # Try to parse as JSON (Encrypted)
                # Check if it looks like JSON
                if content.strip().startswith(b'{'):
                    if not self.password:
                        raise ValueError(f"Key for {self.node_id} is encrypted but no password provided.")
                    
                    decrypted_bytes = self._decrypt_private_key(content.decode('utf-8'), self.password)
                    # The decrypted bytes are the hex string of the key (based on how we save it)
                    # Wait, let's check how we save. 
                    # If we save hex string as bytes, then decrypt gives bytes of hex string.
                    # SigningKey expects bytes (raw) or hex string.
                    # Let's assume we encrypt the RAW bytes or the HEX bytes.
                    # In generate below, we write hex encoded bytes.
                    # So decrypted_bytes will be the hex string bytes.
                    self.signing_key = SigningKey(decrypted_bytes, encoder=HexEncoder)
                    print(f"🔒 Loaded ENCRYPTED identity for {self.node_id}")
                else:
                    # Legacy (Plain Hex)
                    self.signing_key = SigningKey(content, encoder=HexEncoder)
                    print(f"⚠️  Loaded UNENCRYPTED identity for {self.node_id}")
                    
            except Exception as e:
                print(f"❌ Failed to load identity: {e}")
                raise e
                
        else:
            # Generate new
            self.signing_key = SigningKey.generate()
            key_hex_bytes = self.signing_key.encode(encoder=HexEncoder)
            
            # Save to disk
            if self.password:
                # Encrypt
                encrypted_data = self._encrypt_private_key(key_hex_bytes, self.password)
                with open(private_key_path, "w") as f:
                    f.write(encrypted_data)
                print(f"🔒 Generated NEW ENCRYPTED identity for {self.node_id}")
            else:
                # Plaintext (Legacy)
                with open(private_key_path, "wb") as f:
                    f.write(key_hex_bytes)
                print(f"⚠️  Generated NEW UNENCRYPTED identity for {self.node_id}")
            
            # Public key is always plain
            with open(public_key_path, "wb") as f:
                f.write(self.signing_key.verify_key.encode(encoder=HexEncoder))
            
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

    def sign_request(self, method: str, path: str, body: dict) -> dict:
        """
        Sign an API request.
        Returns a dictionary of headers: X-Pubkey, X-Timestamp, X-Signature.
        Payload format: f"{method}:{path}:{timestamp}:{json_body}"
        """
        import time
        timestamp = str(int(time.time()))
        
        # Canonicalize body
        body_str = json.dumps(body, sort_keys=True)
        
        # Construct payload to sign
        payload = f"{method.upper()}:{path}:{timestamp}:{body_str}"
        
        # Sign
        signed = self.signing_key.sign(payload.encode('utf-8'))
        signature = signed.signature.hex()
        
        return {
            "X-Pubkey": self.public_key_hex,
            "X-Timestamp": timestamp,
            "X-Signature": signature
        }

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
