"""
LLM Provider Interface.
Allows switching between different LLM backends (Mock, Ollama, Gemini, Groq, DeepSeek Swarm).
"""

from abc import ABC, abstractmethod
import os
import json
import asyncio
import time
from typing import List, Optional
from dotenv import load_dotenv
import httpx # Async HTTP client

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
        if "JSON" in system_role:
            return json.dumps({
                "vote": "APPROVE",
                "confidence": 0.9,
                "reasoning": "Mock logic",
                "ulfr": {"U": 0.8, "L": 0.8, "F_penalty": 0.1, "R_risk": 0.1},
                "concerns": [],
                "recommendations": [],
                "evidence_cited": []
            })
        return "Mock response."

class GeminiFreeTier(LLMProvider):
    """
    Robust Implementation for Google's Gemini API.
    """
    def __init__(self, api_key: str):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("models/gemini-1.5-flash")
            print("✨ Gemini configured successfully.")
        except Exception as e:
            print(f"❌ Error configuring Gemini: {e}")

    async def generate(self, prompt: str, system_role: str = "") -> str:
        try:
            full_prompt = f"System Role: {system_role}\n\nTask: {prompt}"
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.model.generate_content, full_prompt)
            return response.text
        except Exception as e:
            return f"Error calling Gemini: {e}"

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
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.api_url, headers=headers, json=payload, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                elif response.status_code == 429:
                    return "Error: Groq Rate Limit Exceeded."
                else:
                    return f"Error: Groq API {response.status_code} - {response.text}"
            except Exception as e:
                return f"Error calling Groq: {e}"

class DeepSeekSwarmProvider(LLMProvider):
    """
    Hybrid Swarm Provider.
    Prioritizes P2P Workers (e.g., Home PC via Tailscale).
    Falls back to Groq/Gemini if workers are offline.
    """
    def __init__(self, worker_nodes: List[str], fallback_provider: Optional[LLMProvider] = None):
        self.worker_nodes = worker_nodes
        self.fallback_provider = fallback_provider
        self.model_name = "deepseek-r1" # Or whatever is running on Ollama
        print(f"🕸️ [SWARM] Hybrid Swarm Initialized with {len(worker_nodes)} workers.")
        print(f"   Fallback Provider: {type(fallback_provider).__name__ if fallback_provider else 'None'}")

    async def _check_health(self, node_url: str) -> bool:
        """Ping the node to see if it's alive (Timeout: 1s)."""
        try:
            # Remove /v1 if present for base ping, or just ping /v1/models
            # Adjusting URL for standard Ollama check
            base_url = node_url.replace("/v1", "")
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{base_url}/", timeout=1.0)
                return resp.status_code == 200
        except:
            return False

    async def generate(self, prompt: str, system_role: str = "") -> str:
        # 1. Try Workers First
        for node_url in self.worker_nodes:
            is_alive = await self._check_health(node_url)
            if is_alive:
                print(f"🚀 [SWARM] Offloading task to Worker: {node_url}")
                try:
                    # OpenAI Compatible API Request (Ollama supports this)
                    payload = {
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": system_role},
                            {"role": "user", "content": prompt}
                        ],
                        "stream": False
                    }
                    
                    async with httpx.AsyncClient() as client:
                        # 30s timeout for deep thinking models
                        response = await client.post(f"{node_url}/chat/completions", json=payload, timeout=60.0)
                        
                        if response.status_code == 200:
                            data = response.json()
                            content = data['choices'][0]['message']['content']
                            print(f"✅ [SWARM] Worker {node_url} finished successfully.")
                            return content
                        else:
                            print(f"⚠️ [SWARM] Worker error {response.status_code}: {response.text}")
                            
                except Exception as e:
                    print(f"⚠️ [SWARM] Worker failed during execution: {e}")
            else:
                 pass # print(f"💤 [SWARM] Worker {node_url} is offline.")

        # 2. Fallback
        if self.fallback_provider:
            print("🔄 [SWARM] All workers busy/offline. Switching to Cloud Fallback...")
            return await self.fallback_provider.generate(prompt, system_role)
        
        return "Error: Swarm failed and no fallback configured."

# FACTORY 
def get_llm_provider() -> LLMProvider:
    # 1. Load Config
    config_path = "system_config.json"
    swarm_config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            full_config = json.load(f)
            swarm_config = full_config.get("swarm", {})

    # 2. Initialize Fallback (Groq is best)
    groq_key = os.getenv("GROQ_API_KEY")
    fallback = GroqProvider(groq_key) if groq_key else None
    
    # 3. Check System Mode
    # If config says "hybrid" and we have workers, return DeepSeekSwarm
    if swarm_config.get("mode") == "hybrid" and swarm_config.get("worker_nodes"):
        return DeepSeekSwarmProvider(
            worker_nodes=swarm_config["worker_nodes"],
            fallback_provider=fallback
        )
        
    # 4. Default to Groq if no Swarm configured
    if fallback:
        return fallback

    # 5. Last Resort Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        return GeminiFreeTier(gemini_key)

    raise RuntimeError("❌ No valid LLM Provider found (Groq, Swarm, or Gemini).")