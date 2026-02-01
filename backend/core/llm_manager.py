"""
Multi-LLM Manager for Orbis Ethica AGI 3.0
Separates LLM roles according to the vision:
- Gemini: Master Brain (user deliberations, introspection)
- Groq: Fast Workers (distributed shards, learning from Gemini)
- Ollama: Local Nodes (future micro-models)
"""

import os

from .llm_provider import GeminiFreeTier, GroqProvider, LLMProvider, OllamaProvider


class MultiLLMManager:
    """
    Manages multiple LLM providers with role-based selection.
    Ensures Gemini handles high-value deliberations while Groq learns.
    """
    
    def __init__(self):
        self.gemini: LLMProvider | None = None
        self.groq: LLMProvider | None = None
        self.ollama: LLMProvider | None = None
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Load all available LLM providers from environment."""
        
        # 1. Gemini (Master Brain)
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                self.gemini = GeminiFreeTier(gemini_key)
                print("✅ Gemini (Master Brain): Loaded")
            except Exception as e:
                print(f"⚠️ Gemini failed to load: {e}")
        
        # 2. Groq (Fast Workers)
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                self.groq = GroqProvider(groq_key)
                print("✅ Groq (Fast Worker): Loaded")
            except Exception as e:
                print(f"⚠️ Groq failed to load: {e}")
        
        # 3. Ollama (Local Nodes - Hybrid Mode)
        # Auto-discover even if not explicitly set
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        try:
            # Attempt connection
            candidate_ollama = OllamaProvider(host=ollama_host, model=ollama_model)
            if candidate_ollama.is_available:
                self.ollama = candidate_ollama
                print(f"✅ Ollama (Local Node): Active (Model: {ollama_model})")
            else:
                print(f"⚠️ Ollama (Local Node): Not detected at {ollama_host}")
        except Exception as e:
            print(f"⚠️ Ollama failed to load: {e}")
        
        # Critical Check: At least ONE LLM must be available
        if not self.gemini and not self.groq and not self.ollama:
            raise RuntimeError(
                "❌ FATAL: No LLM providers available!\n"
                "Please configure at least one of:\n"
                "  - GEMINI_API_KEY (Recommended)\n"
                "  - GROQ_API_KEY\n"
                "  - OLLAMA_HOST + OLLAMA_MODEL\n"
                "System cannot start without an LLM."
            )
    
    def get_for_deliberation(self) -> LLMProvider:
        """
        Get LLM for user-submitted deliberations.
        Uses Gemini (most intelligent) for high-quality ethical reasoning.
        """
        if self.gemini:
            return self.gemini
        
        # Fallback chain
        if self.groq:
            print("⚠️ Gemini unavailable, using Groq for deliberation")
            return self.groq
        
        if self.ollama:
            print("⚠️ Gemini unavailable, using Ollama for deliberation")
            return self.ollama
        
        raise RuntimeError(
            "❌ No LLM available for DELIBERATION.\n"
            "Gemini, Groq, and Ollama are all unavailable."
        )
    
    def get_for_shard(self) -> LLMProvider:
        """
        Get LLM for distributed shard processing (Mining).
        PRIORITY: Local (Ollama) -> Groq (Cloud Worker) -> Gemini (Cloud Brain)
        """
        # 1. Prefer Local Compute (True Decentralization)
        if self.ollama and self.ollama.is_available:
            return self.ollama

        # 2. Fallback to Groq (Fast Cloud Worker)
        if self.groq:
            return self.groq
        
        # 3. Last Resort: Gemini
        if self.gemini:
            print("⚠️ Groq unavailable, using Gemini for shards")
            return self.gemini
        
        raise RuntimeError(
            "❌ No LLM available for SHARD MINING.\n"
            "Ollama, Groq, and Gemini are all unavailable."
        )
    
    def get_for_introspection(self) -> LLMProvider:
        """
        Get LLM for consciousness/introspection tasks.
        Uses Gemini (best reasoning) for self-reflection.
        """
        if self.gemini:
            return self.gemini
        
        if self.groq:
            print("⚠️ Gemini unavailable, using Groq for introspection")
            return self.groq
        
        raise RuntimeError(
            "❌ No LLM available for INTROSPECTION.\n"
            "Gemini and Groq are both unavailable."
        )
    
    def get_for_oracle(self) -> LLMProvider:
        """
        Get LLM for autonomous oracle (dilemma detection).
        Uses Gemini (best for understanding context).
        """
        if self.gemini:
            return self.gemini
        
        if self.groq:
            print("⚠️ Gemini unavailable, using Groq for oracle")
            return self.groq
        
        raise RuntimeError(
            "❌ No LLM available for ORACLE.\n"
            "Gemini and Groq are both unavailable."
        )
    
    def get_status(self) -> dict:
        """Get status of all LLM providers."""
        return {
            "gemini": "✅ Ready" if self.gemini else "❌ Not Available",
            "groq": "✅ Ready" if self.groq else "❌ Not Available",
            "ollama": "✅ Ready" if self.ollama else "❌ Not Available",
            "default_deliberation": self.get_for_deliberation().__class__.__name__,
            "default_shard": self.get_for_shard().__class__.__name__,
        }
