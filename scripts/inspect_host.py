import trio
from libp2p import new_host
from multiaddr import Multiaddr

async def main():
    print("🔍 Inspecting Libp2p Host...")
    host = new_host()
    print(f"Host Type: {type(host)}")
    print(f"Dir(host): {dir(host)}")
    
    # Check for peerstore or network
    if hasattr(host, 'get_network'):
        net = host.get_network()
        print(f"Network: {net}")
        print(f"Dir(net): {dir(net)}")
        
    if hasattr(host, 'get_peerstore'):
        ps = host.get_peerstore()
        print(f"PeerStore: {ps}")
        print(f"Dir(ps): {dir(ps)}")

if __name__ == "__main__":
    trio.run(main)
