import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.api.app import app, startup_event

async def test_startup():
    print("🧪 Testing Startup Event...")
    try:
        await startup_event()
        print("✅ Startup Event Completed Successfully!")
    except Exception as e:
        print(f"❌ Startup Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_startup())
