from libp2p.pubsub.gossipsub import GossipSub
import inspect

print("🔍 Inspecting GossipSub.__init__ signature:")
try:
    sig = inspect.signature(GossipSub.__init__)
    print(sig)
except Exception as e:
    print(f"Error: {e}")

print("\n🔍 Inspecting GossipSub class docstring:")
print(GossipSub.__doc__)
