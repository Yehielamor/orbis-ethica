"""
Real Ed25519 Signer utilizing the verified NodeIdentity system.
Replaces the old stub.
"""
from ...core.identity import NodeIdentity


class Signer:
    def __init__(self):
        self.identity = NodeIdentity() 
        
    def sign_message(self, message: str) -> str:
        """Signs a message using the real Ed25519 private key."""
        return self.identity.sign_data(message)

    def get_public_key(self) -> str:
        return self.identity.public_key