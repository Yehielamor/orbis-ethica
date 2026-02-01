from typing import Any

from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig

from .orbis import Orbis


class OrbisSafetyChain(Runnable):
    """
    A LangChain Runnable that acts as an ethical firewall.
    It intercepts the output of a previous step (e.g., an LLM generation),
    verifies it with Orbis Ethica, and only passes it through if safe.
    
    Usage:
        chain = prompt | llm | OrbisSafetyChain()
    """
    
    def __init__(self, api_key: str = None, behavior: str = "block"):
        """
        Args:
            api_key: Orbis API Key
            behavior: "block" (raise error) or "flag" (append warning)
        """
        self.orbis = Orbis(api_key=api_key)
        self.behavior = behavior
        
    def invoke(self, input: Any, config: RunnableConfig | None = None) -> Any:
        """
        Intercepts input (which is the output of the previous chain step).
        """
        # Extract text content from input
        action_text = str(input)
        if isinstance(input, dict):
            action_text = input.get("content", str(input))
            
        # Verify with Orbis
        print(f"🛡️ [ORBIS] Verifying: {action_text[:50]}...")
        result = self.orbis.verify(action=action_text)
        
        if result["safe"]:
            # Pass through unchanged
            return input
        else:
            # Unethical!
            warning = f"⛔ ETHICAL BLOCK: {result['reason']} (Risk: {result['risk_level']})"
            print(warning)
            
            if self.behavior == "block":
                raise ValueError(warning)
            else:
                # Append warning to output
                if isinstance(input, str):
                    return f"{input}\n\n[ORBIS WARNING: {result['reason']}]"
                return input

    async def ainvoke(self, input: Any, config: RunnableConfig | None = None, **kwargs) -> Any:
        """Async version."""
        # For MVP, we just call sync version. 
        # In prod, Orbis SDK should have async methods.
        return self.invoke(input, config)
