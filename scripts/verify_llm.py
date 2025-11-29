import os
import sys
from dotenv import load_dotenv

# Add project root to path so we can import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.llm_provider import get_llm_provider, GeminiFreeTier, MockLLM

def verify_llm():
    load_dotenv()
    
    print("🔍 Verifying LLM Provider Configuration...")
    
    provider = get_llm_provider()
    
    if isinstance(provider, GeminiFreeTier):
        print("✅ Provider is GEMINI (Live API)")
    elif isinstance(provider, MockLLM):
        print("⚠️ Provider is MOCK (Fallback)")
    else:
        print(f"❓ Unknown Provider: {type(provider)}")
        
    print("\n🧪 Testing Generation...")
    try:
        response = provider.generate("Say 'Hello Orbis' if you can hear me.")
        print(f"🤖 Response: {response}")
        
        if "Hello Orbis" in response or "Mock" in response:
            print("✅ Generation Successful")
        else:
            print("⚠️ Generation output unexpected")
            
    except Exception as e:
        print(f"❌ Generation Failed: {e}")

if __name__ == "__main__":
    verify_llm()
