from typing import Protocol

class ReputationManager(Protocol):
    """Interface for managing entity reputation and status."""
    
    def burn_reputation(self, entity_id: str) -> None:
        """Set entity reputation to 0."""
        ...
        
    def quarantine_entity(self, entity_id: str) -> None:
        """Set entity status to quarantined."""
        ...
