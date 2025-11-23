"""
LLM Provider Interface.
Allows switching between different LLM backends (Mock, Ollama, Gemini)
without changing the core entity logic.
"""

from abc import ABC, abstractmethod
import os
import time

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_role: str = "You are a helpful assistant.") -> str:
        """Generate a response from the LLM."""
        pass

class MockLLM(LLMProvider):
    """
    A free, offline provider for testing flow without calling real APIs.
    """
    def generate(self, prompt: str, system_role: str = "") -> str:
        print(f"\n🤖 [MOCK LLM] Generating response for role: {system_role}...")
        time.sleep(1)
        
        if "seeker" in system_role.lower():
            return "Based on the data, the utility is high (U=0.85). We must proceed."
        elif "healer" in system_role.lower():
            return "The risk of harm is too great (L=0.9). I advise caution."
        else:
            return "I am neutral on this proposal."

class GeminiFreeTier(LLMProvider):
    """
    Robust Implementation for Google's Gemini API.
    Automatically detects the available model from the user's specific key.
    """
    def __init__(self, api_key: str):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # 1. List valid models for this key
            valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            print(f"📋 Valid Gemini Models found: {len(valid_models)}")

            # 2. Priority list (Based on your available models)
            candidates = [
                "models/gemini-2.0-flash",           # New, fast, stable
                "models/gemini-2.0-flash-exp",       # Experimental fast
                "models/gemini-flash-latest",        # Always points to latest flash
                "models/gemini-1.5-flash",           # Older stable
                "models/gemini-pro-latest",          # Fallback pro
                "models/gemini-2.5-flash-preview-09-2025" # Bleeding edge
            ]

            # 3. Select the best match
            selected_model = None
            for candidate in candidates:
                if candidate in valid_models:
                    selected_model = candidate
                    break
            
            # Fallback if none of the specific ones match, take the first valid one
            if not selected_model and valid_models:
                selected_model = valid_models[0]
            
            if not selected_model:
                raise ValueError("No valid generateContent models found for this API key.")

            self.model = genai.GenerativeModel(selected_model)
            print(f"✨ Gemini configured successfully using: {selected_model}")
            
        except ImportError:
            print("❌ Error: google-generativeai not installed.")
        except Exception as e:
            print(f"❌ Error configuring Gemini: {e}")

    def generate(self, prompt: str, system_role: str = "") -> str:
        # Combining system instruction into prompt for broader compatibility
        full_prompt = f"System Role: {system_role}\n\nTask: {prompt}"
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Error calling Gemini: {e}"

# --- FACTORY ---
def get_llm_provider() -> LLMProvider:
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if gemini_key:
        return GeminiFreeTier(gemini_key)
    else:
        print("⚠️ No GEMINI_API_KEY found. Using Mock Provider.")
        return MockLLM()