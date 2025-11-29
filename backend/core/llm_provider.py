"""
LLM Provider Interface.
Allows switching between different LLM backends (Mock, Ollama, Gemini)
without changing the core entity logic.
"""

from abc import ABC, abstractmethod
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
        print(f"\n🤖 [MOCK LLM] Generating response for role: {system_role[:50]}...")
        # time.sleep(0.5) # Reduced for faster tests
        
        if "JSON" in system_role or "JSON" in prompt:
            import json
            response = {
                "ulfr": {
                    "U": 0.8,
                    "L": 0.6,
                    "F_penalty": 0.1,
                    "R_risk": 0.2
                },
                "vote": "APPROVE",
                "confidence": 0.9,
                "reasoning": "Mock reasoning based on utility.",
                "concerns": ["Mock concern 1"],
                "recommendations": ["Mock recommendation 1"],
                "evidence_cited": ["Mock evidence 1"]
            }
            return json.dumps(response)
            
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

class LocalLLM(LLMProvider):
    """
    Swarm Intelligence Provider.
    Connects to a local Ollama instance running lightweight models (e.g., TinyLlama).
    """
    def __init__(self, model_name: str = "tinyllama"):
        self.model_name = model_name
        try:
            import ollama
            # quick check if model exists
            host = os.getenv("OLLAMA_HOST", "localhost")
            print(f"🧠 [LOCAL LLM] Connecting to Ollama ({model_name}) at {host}...")
            # We don't block here, just assume it works.
        except ImportError:
            print("❌ Error: 'ollama' library not installed.")

    def generate(self, prompt: str, system_role: str = "") -> str:
        import ollama
        try:
            # Combine system role into the messages list
            response = ollama.chat(model=self.model_name, messages=[
                {
                    'role': 'system',
                    'content': system_role
                },
                {
                    'role': 'user',
                    'content': prompt
                },
            ])
            return response['message']['content']
        except Exception as e:
            print(f"❌ Local Inference Failed: {e}")
            return f"Error: {e}"

# --- FACTORY ---
def get_llm_provider() -> LLMProvider:
    # 1. Priority: Local Swarm (if configured)
    # For now, we enable it if OLLAMA_MODEL is set in env, otherwise fallback
    ollama_model = os.getenv("OLLAMA_MODEL")
    if ollama_model:
        return LocalLLM(model_name=ollama_model)

    # 2. Priority: Cloud (Gemini)
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        return GeminiFreeTier(gemini_key)
    
    # 3. Fallback: Mock
    print("⚠️ No LLM Configured. Using Mock Provider.")
    return MockLLM()