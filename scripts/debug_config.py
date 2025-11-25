import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.core.config import ConfigManager
    print("✅ Imported ConfigManager")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def test_config():
    print("🔧 Testing ConfigManager...")
    try:
        cm = ConfigManager()
        print(f"   Loaded config from: {cm.config_path}")
        
        config = cm.get_config()
        print(f"   Config object: {config}")
        
        # Test model_dump (Pydantic v2) or dict (Pydantic v1)
        try:
            dump = config.model_dump()
            print("   ✅ model_dump() successful")
            print(json.dumps(dump, indent=2))
        except AttributeError:
            print("   ⚠️ model_dump() failed, trying dict()...")
            dump = config.dict()
            print("   ✅ dict() successful")
            print(json.dumps(dump, indent=2))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config()
