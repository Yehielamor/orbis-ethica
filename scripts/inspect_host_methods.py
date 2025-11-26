from libp2p import new_host
from multiaddr import Multiaddr
import inspect

print("🔍 Inspecting Libp2p Host...")
try:
    h = new_host()
    print(f"Host Type: {type(h)}")
    print("Methods:")
    for name in dir(h):
        if not name.startswith("_"):
            print(f" - {name}")
            
    print("\nNetwork Methods:")
    if hasattr(h, 'get_network'):
        net = h.get_network()
        print(f"Network Type: {type(net)}")
        for name in dir(net):
            if not name.startswith("_"):
                print(f" - {name}")
except Exception as e:
    print(f"Error: {e}")
