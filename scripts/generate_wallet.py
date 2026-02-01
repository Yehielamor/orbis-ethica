
import os

import nacl.encoding
import nacl.signing


def generate_wallet():
    # Generate a new random signing key (Private Key)
    signing_key = nacl.signing.SigningKey.generate()
    
    # Extract the verify key (Public Key)
    verify_key = signing_key.verify_key
    
    # Encode as Hex strings
    private_key_hex = signing_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')
    public_key_hex = verify_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')
    
    print("\n🔐 GENERATED SECURE WALLET 🔐")
    print("==============================")
    print(f"💰 Public Key (Wallet Address): 0x{public_key_hex}")
    print(f"🔑 Private Key (SAVE THIS!):    {private_key_hex}")
    print("==============================")
    print("⚠️  Keep your Private Key safe. Anyone with this key can spend your Genesis tokens.")

if __name__ == "__main__":
    try:
        generate_wallet()
    except ImportError:
        print("Installing PyNaCl...")
        os.system("pip install pynacl")
        generate_wallet()
