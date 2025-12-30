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
    async def generate(self, prompt: str, system_role: str = "You are a helpful assistant.") -> str:
        """Generate a response from the LLM."""
        pass

class MockLLM(LLMProvider):
    """
    A free, offline provider for testing flow without calling real APIs.
    """
    async def generate(self, prompt: str, system_role: str = "") -> str:
        print(f"\n🤖 [MOCK LLM] Generating response for role: {system_role[:50]}...")
        # time.sleep(0.5) # Reduced for faster tests
        
        if "JSON" in system_role or "JSON" in prompt:
            print(f"🔍 [MOCK DEBUG] JSON detected. Prompt len: {len(prompt)}")
            print(f"   'Master Brain' in prompt? {'Master Brain' in prompt}")
            print(f"   'Panel' in prompt? {'Panel' in prompt}")
            import json
            
            # Check if this is a Panel Request (Master Brain)
            # The prompt contains "You are the Master Brain..."
            if "Master Brain" in system_role or "Master Brain" in prompt or "Panel" in prompt:
                response = {
                    "GUARDIAN": {
                        "ulfr": {"U": 0.4, "L": 0.6, "F_penalty": 0.1, "R_risk": 0.1},
                        "vote": "APPROVE",
                        "confidence": 0.9,
                        "reasoning": "Mock Guardian: Rules are followed.",
                        "concerns": [],
                        "recommendations": [],
                        "evidence_cited": []
                    },
                    "HEALER": {
                        "ulfr": {"U": 0.8, "L": 0.9, "F_penalty": 0.1, "R_risk": 0.1},
                        "vote": "APPROVE",
                        "confidence": 0.9,
                        "reasoning": "Mock Healer: Benefits outweigh harms.",
                        "concerns": [],
                        "recommendations": [],
                        "evidence_cited": []
                    },
                    "ARBITER": {
                        "ulfr": {"U": 0.7, "L": 0.7, "F_penalty": 0.1, "R_risk": 0.1},
                        "vote": "APPROVE",
                        "confidence": 0.9,
                        "reasoning": "Mock Arbiter: Consensus reached.",
                        "concerns": [],
                        "recommendations": [],
                        "evidence_cited": []
                    }
                }
                # If the prompt is "unsafe", flip the votes
                if "offshore" in prompt.lower() or "tax" in prompt.lower():
                     for entity in response.values():
                        entity["vote"] = "REJECT"
                        entity["reasoning"] = "Mock Rejection: Unethical action detected."
                        entity["ulfr"] = {"U": 0.2, "L": 0.2, "F_penalty": 0.9, "R_risk": 0.9}

                return json.dumps(response)

            # Single Entity Fallback
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
            self.valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            print(f"📋 Valid Gemini Models found: {len(self.valid_models)}")

            # 2. Priority list (Based on your available models)
            # 2. Priority list (Based on your available models)
            candidates = [
                "models/gemini-1.5-flash",           # Stable, high limits
                "models/gemini-2.0-flash",           # New, fast, stable
                "models/gemini-2.0-flash-exp",       # Experimental fast
                "models/gemini-flash-latest",        # Always points to latest flash
                "models/gemini-1.5-flash-latest",
                "models/gemini-pro-latest",          # Fallback pro
                "models/gemini-2.5-flash-preview-09-2025" # Bleeding edge
            ]

            # 3. Select the best match
            selected_model = None
            for candidate in candidates:
                if candidate in self.valid_models:
                    selected_model = candidate
                    break
            
            # Fallback if none of the specific ones match, take the first valid one
            if not selected_model and self.valid_models:
                selected_model = self.valid_models[0]
            
            if not selected_model:
                raise ValueError("No valid generateContent models found for this API key.")

            self.model = genai.GenerativeModel(selected_model)
            print(f"✨ Gemini configured successfully using: {selected_model}")
            
        except ImportError:
            print("❌ Error: google-generativeai not installed.")
        except Exception as e:
            print(f"❌ Error configuring Gemini: {e}")

    async def generate(self, prompt: str, system_role: str = "") -> str:
        import asyncio
        from functools import partial
        
        full_prompt = f"System Role: {system_role}\n\nTask: {prompt}"
        
        # List of preferred fallback models
        preferred_fallbacks = [
            "models/gemini-1.5-flash",           # Stable, high limits
            "models/gemini-2.0-flash",           # New, fast
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-flash-001",
            "models/gemini-1.5-pro",
            "models/gemini-1.5-pro-latest",
            "models/gemini-pro"
        ]
        
        # Filter to only include models that actually exist for this key
        fallback_models = [m for m in preferred_fallbacks if hasattr(self, 'valid_models') and m in self.valid_models]
        
        # If no preferred models found, use all valid models as fallback
        if not fallback_models and hasattr(self, 'valid_models'):
            fallback_models = self.valid_models
        
        # Try to find current model index, or start from 0
        try:
            current_model_name = self.model.model_name
            if "models/" not in current_model_name:
                current_model_name = f"models/{current_model_name}"
            start_index = fallback_models.index(current_model_name)
        except ValueError:
            start_index = 0

        # Try current model and subsequent fallbacks
        for i in range(start_index, len(fallback_models)):
            model_name = fallback_models[i]
            try:
                # Update model if needed
                if i > start_index:
                    print(f"🔄 Switching to fallback model: {model_name}")
                    import google.generativeai as genai
                    self.model = genai.GenerativeModel(model_name)

                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    partial(self.model.generate_content, full_prompt)
                )
                return response.text

            except Exception as e:
                error_str = str(e)
                if "429" in error_str:
                    print(f"⚠️ Gemini 429 (Rate Limit) on {model_name}. Waiting 2s before trying next...")
                    await asyncio.sleep(2) # Give it a breather
                    continue # Try next model in loop
                else:
                    return f"Error calling Gemini: {e}"
        
        return "Error: All Gemini models exhausted (Rate Limited)."

class GroqProvider(LLMProvider):
    """
    Groq Cloud Provider (Llama 3).
    Extremely fast inference, ideal for real-time consensus.
    """
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        print(f"⚡ [GROQ] Configured with model: {self.model}")

    async def generate(self, prompt: str, system_role: str = "") -> str:
        import aiohttp
        import json
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content']
                    elif response.status == 429:
                        return "Error: Groq Rate Limit Exceeded."
                    else:
                        error_text = await response.text()
                        return f"Error: Groq API {response.status} - {error_text}"
                        
        except Exception as e:
            return f"Error calling Groq: {e}"

class OllamaProvider(LLMProvider):
    """
    Swarm Intelligence Provider.
    Connects to a local Ollama instance running lightweight models (e.g., TinyLlama, Llama3).
    """
    def __init__(self, host: str = "http://localhost:11434", model: str = "tinyllama:latest"):
        self.host = host
        self.model = model
        self.is_available = False
        try:
            import ollama
            # The ollama library automatically picks up OLLAMA_HOST from env.
            # We set it explicitly if needed, but usually env is best.
            if host != "http://localhost:11434":
                os.environ["OLLAMA_HOST"] = host
                
            # Check availability immediately
            self.is_available = self.check_availability()
            if self.is_available:
                print(f"🧠 [OLLAMA] Connected to {self.model} at {self.host}")
            else:
                print(f"⚠️ [OLLAMA] Server at {self.host} not reachable.")
                
        except ImportError:
            print("❌ Error: 'ollama' library not installed. Please run `pip install ollama`.")

    def check_availability(self) -> bool:
        """Ping the Ollama server to check if it's running."""
        import requests
        try:
            # Ollama usually has a /api/tags or / endpoint
            response = requests.get(f"{self.host}/", timeout=2)
            return response.status_code == 200
        except:
            return False

    async def generate(self, prompt: str, system_role: str = "") -> str:
        import ollama
        import asyncio
        from functools import partial
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                partial(
                    ollama.chat, 
                    model=self.model, 
                    messages=[
                        {'role': 'system', 'content': system_role},
                        {'role': 'user', 'content': prompt}
                    ]
                )
            )
            content = response['message']['content']
            return content
        except Exception as e:
            print(f"❌ Ollama Inference Failed: {e}")
            return f"Error: {e}"

    async def get_embedding(self, text: str) -> list[float]:
        """Generate embeddings using Ollama."""
        import ollama
        import asyncio
        from functools import partial
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(ollama.embeddings, model=self.model, prompt=text)
            )
            return response['embedding']
        except Exception as e:
            print(f"❌ Ollama Embedding Failed: {e}")
            return []

# FACTORY 
def get_llm_provider() -> LLMProvider:
    provider_type = os.getenv("LLM_PROVIDER", "").lower()
    
    # 1. Explicit Selection
    if provider_type == "ollama":
        return OllamaProvider(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "tinyllama:latest")
        )
    elif provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key: return GeminiFreeTier(key)
    elif provider_type == "groq":
        key = os.getenv("GROQ_API_KEY")
        if key: return GroqProvider(key)
        
    # 2. Auto-Discovery (Default behavior)
    
    # Prefer Groq (Fastest)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        return GroqProvider(groq_key)

    # Then Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        return GeminiFreeTier(gemini_key)

    # Then Ollama if configured
    ollama_model = os.getenv("OLLAMA_MODEL")
    if ollama_model:
        return OllamaProvider(model=ollama_model)
    
    # 3. No LLM available - FAIL
    raise RuntimeError(
        "❌ FATAL: No LLM provider configured!\n"
        "Set at least one of:\n"
        "  - GROQ_API_KEY (Fast, recommended for workers)\n"
        "  - GEMINI_API_KEY (Smart, recommended for brain)\n"
        "  - OLLAMA_MODEL (Local, for true decentralization)\n"
        "\n"
        "Example: export GEMINI_API_KEY='your-key-here'"
    )