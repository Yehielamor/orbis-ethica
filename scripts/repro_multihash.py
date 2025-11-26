import sys
import os

# Mimic app.py imports
try:
    import multihash
    print(f"Initial multihash: {multihash}")
    print(f"Has Func? {hasattr(multihash, 'Func')}")
except ImportError:
    print("multihash not found initially")

try:
    import pymultihash
    print(f"pymultihash: {pymultihash}")
except ImportError:
    print("pymultihash not found")

# Now try libp2p import which triggers the error
try:
    from libp2p import new_host
    print("✅ libp2p imported successfully")
except Exception as e:
    print(f"❌ libp2p import failed: {e}")

# Check multihash again
import multihash
print(f"Final multihash: {multihash}")
print(f"Has Func? {hasattr(multihash, 'Func')}")
print(f"Dir: {dir(multihash)}")
