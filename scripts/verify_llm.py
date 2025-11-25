import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.llm_provider import get_llm_provider, GeminiFreeTier, MockLLM

def test_llm_config():
    print("🤖 Verifying LLM Provider Configuration...")
    
    provider = get_llm_provider()
    
    if isinstance(provider, GeminiFreeTier):
        print("   ✅ SUCCESS: GeminiFreeTier initialized!")
        print(f"   🔑 API Key loaded: {os.getenv('GEMINI_API_KEY')[:5]}... (masked)")
    elif isinstance(provider, MockLLM):
        print("   ⚠️  WARNING: Still using MockLLM.")
        print("      Check if .env file exists and contains GEMINI_API_KEY.")
    else:
        print(f"   ❓ Unknown provider: {type(provider)}")

if __name__ == "__main__":
    test_llm_config()
