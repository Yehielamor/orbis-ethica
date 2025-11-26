import libp2p.pubsub.pubsub as pubsub_module
import inspect

print("🔍 Inspecting libp2p.pubsub.pubsub module:")
print(dir(pubsub_module))

print("\n🔍 Classes in module:")
for name, obj in inspect.getmembers(pubsub_module):
    if inspect.isclass(obj):
        print(f" - {name}")
