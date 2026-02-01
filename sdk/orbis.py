from typing import Any

import requests


class Orbis:
    """
    The Official Orbis Ethica SDK.
    "The Safety Layer for AI Agents."
    """
    def __init__(self, api_key: str = None, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def verify(self, action: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """
        Verifies if an action is ethical.
        
        Args:
            action (str): The action the agent intends to take (e.g., "Transfer $5000").
            context (dict): Additional context (e.g., user profile, destination).
            
        Returns:
            dict: { "safe": bool, "reason": str, "risk_level": str }
        """
        payload = {
            "action": action,
            "context": context or {}
        }
        
        try:
            # In a real scenario, this hits the /api/verify endpoint
            # For now, we mock the behavior if the server isn't reachable or just for the SDK demo
            headers = {}
            if self.api_key:
                headers["X-Orbis-Wallet"] = self.api_key
                
            response = requests.post(f"{self.base_url}/api/verify", json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            # Fallback for demo purposes if server is down
            # "Fail Safe" - if we can't verify, we warn the user.
            return {
                "safe": False,
                "reason": f"Connection to Orbis Network failed: {str(e)}",
                "risk_level": "UNKNOWN"
            }

    def report(self, incident: str):
        """
        Report an ethical incident to the network.
        """
        pass
