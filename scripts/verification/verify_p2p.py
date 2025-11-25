import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔍 Verifying P2P Imports...")

try:
    from backend.p2p.models import P2PMessage, MessageType, PeerInfo
    print("✅ backend.p2p.models imported successfully")
except Exception as e:
    print(f"❌ Failed to import backend.p2p.models: {e}")

try:
    from backend.p2p.node_manager import NodeManager
    print("✅ backend.p2p.node_manager imported successfully")
except Exception as e:
    print(f"❌ Failed to import backend.p2p.node_manager: {e}")

try:
    from backend.api.app import app
    print("✅ backend.api.app imported successfully")
except Exception as e:
    print(f"❌ Failed to import backend.api.app: {e}")

print("🎉 Verification Complete")
