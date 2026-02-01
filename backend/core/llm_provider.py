"""
LLM Provider Interface - Enhanced for Swarm Load Balancing.
Allows switching between Mock, Cloud (Groq), and Local Swarm (Ollama via Tailscale).
"""
import json
import os
import random
from abc import ABC, abstractmethod

import httpx
from dotenv import load_dotenv

load_dotenv()

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_role: str = "You are a helpful assistant.") -> str:
        pass

class MockLLM(LLMProvider):
    """
    Offline provider for testing logic without API calls.
    """
    async def generate(self, prompt: str, system_role: str = "") -> str:
        print("🤖 [MOCK] Generating response...")
        if "JSON" in system_role:
            return json.dumps({
                "vote": "APPROVE", 
                "confidence": 0.9, 
                "reasoning": "Mock Logic Approved",
                "ulfr": {"utility": 0.8, "life": 0.8, "fairness_penalty": 0.1, "rights_risk": 0.1},
                "concerns": [], "recommendations": [], "evidence_cited": []
            })
        return "Mock text response."

class GroqProvider(LLMProvider):
    """
    Cloud Provider (Fast & Cheap) - Used as Fallback.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        
    async def generate(self, prompt: str, system_role: str = "") -> str:
        if not self.api_key:
            raise ValueError("Groq API Key is missing.")
            
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama3-70b-8192", 
            "messages": [{"role": "system", "content": system_role}, {"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=30.0)
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"❌ [GROQ ERROR]: {e}")
                raise e

class DeepSeekSwarmProvider(LLMProvider):
    """
    Manages a Swarm of local Ollama nodes via Tailscale/VPN.
    Implements: Round-Robin Load Balancing + Failover.
    """
    def __init__(self, worker_nodes: list[str], fallback_provider: LLMProvider | None = None):
        self.worker_nodes = worker_nodes
        self.fallback_provider = fallback_provider
        self.timeout = 20.0  # Seconds to wait for home PC response

    async def generate(self, prompt: str, system_role: str = "") -> str:
        # 1. Load Balancing: Shuffle nodes to distribute traffic randomly
        shuffled_nodes = self.worker_nodes.copy()
        random.shuffle(shuffled_nodes)

        # Standard OpenAI-compatible payload for Ollama
        payload = {
            "model": "deepseek-r1:8b", 
            "messages": [{"role": "system", "content": system_role}, {"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.2} 
        }

        # 2. Try workers one by one
        async with httpx.AsyncClient() as client:
            for node_url in shuffled_nodes:
                try:
                    # Clean URL logic
                    target_url = f"{node_url}/chat/completions"
                    print(f"🐝 [SWARM] Dispatching to Worker: {node_url}...")
                    
                    resp = await client.post(target_url, json=payload, timeout=self.timeout)
                    resp.raise_for_status()
                    
                    # Return success immediately
                    return resp.json()["choices"][0]["message"]["content"]
                    
                except Exception as e:
                    print(f"⚠️ [SWARM WARN] Worker {node_url} failed: {str(e)}")
                    continue # Try next node

        # 3. Fallback Mechanism
        if self.fallback_provider:
            print("🚨 [SWARM ALERT] All local nodes failed. Falling back to Cloud (Groq)...")
            return await self.fallback_provider.generate(prompt, system_role)
        
        return "Error: Swarm failed and no fallback configured."

def get_llm_provider() -> LLMProvider:
    """
    Factory method to initialize the correct provider based on config.
    """
    config_path = "system_config.json"
    worker_nodes = []
    
    # Load Swarm Config
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                data = json.load(f)
                worker_nodes = data.get("swarm", {}).get("worker_nodes", [])
        except Exception as e:
            print(f"⚠️ Config load error: {e}")

    # Initialize Fallback (Groq)
    groq_key = os.getenv("GROQ_API_KEY")
    fallback = GroqProvider(groq_key) if groq_key else MockLLM()

    # Return Swarm if workers exist
    if worker_nodes:
        return DeepSeekSwarmProvider(worker_nodes, fallback_provider=fallback)
    
    # Default to Fallback
    return fallback