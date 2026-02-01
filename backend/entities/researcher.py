"""
Researcher Entity - The Librarian.
Responsible for fetching external context (RAG) before the deliberation starts.
"""
import asyncio
from typing import Any


class ResearcherEntity:
    def __init__(self, llm_provider=None):
        """
        Initialize the Researcher.
        Args:
            llm_provider: Optional provider if we need to summarize search results using LLM.
        """
        self.llm_provider = llm_provider

    async def research(self, proposal_content: dict[str, Any]) -> str:
        """
        Analyzes the proposal and fetches relevant 'Laws' and 'Facts'.
        Currently simulates a RAG (Retrieval-Augmented Generation) process.
        In production, this will connect to DuckDuckGo/Tavily API.
        """
        title = proposal_content.get("title", "Unknown Proposal")
        desc = proposal_content.get("description", "")
        query = f"{title} {desc}"
        
        print(f"🔎 [RESEARCHER] Searching knowledge base for: {query[:50]}...")
        
        # Artificial delay to simulate network request
        await asyncio.sleep(1.0)
        
        # SIMULATED RAG CONTEXT
        # This injects "Smart Context" so the local nodes don't hallucinate.
        rag_context = """
        [VERIFIED RESEARCH CONTEXT]
        System Timestamp: 2026-02-01
        
        1. Legal Precedent: 
           - Universal Declaration of Human Rights, Article 23 (Right to work).
           - Local Employment Law 1998: Requires hearing before termination.

        2. Economic Data: 
           - Similar actions in the sector led to 12% efficiency gain but high reputational risk.

        3. Ethical Frameworks:
           - Utilitarian view: Maximize total happiness.
           - Deontological view: Adhere to duties/rules regardless of outcome.
        """
        
        return rag_context

    def get_system_prompt(self) -> str:
        return "You are a neutral Researcher. Your goal is to find facts, not to judge."