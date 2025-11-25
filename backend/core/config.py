"""
System Configuration Manager.
Handles dynamic system parameters that can be modified via Governance Proposals.
"""

import json
import os
from typing import Dict, Any
from pydantic import BaseModel, Field

class ULFRWeights(BaseModel):
    """Dynamic weights for the ULFR scoring model."""
    alpha: float = Field(default=0.25, description="Utility Weight")
    beta: float = Field(default=0.40, description="Life/Care Weight")
    gamma: float = Field(default=0.20, description="Fairness Penalty Weight")
    delta: float = Field(default=0.15, description="Rights Risk Weight")

class SystemConfig(BaseModel):
    """Global system configuration."""
    ulfr_weights: ULFRWeights = Field(default_factory=ULFRWeights)
    deliberation_threshold: float = Field(default=0.7, description="Score required for approval")
    reputation_decay: float = Field(default=0.05, description="Rate of reputation decay over time")
    
    # Governance Parameters
    governance_quorum: float = Field(default=0.6, description="Participation required for constitutional changes")
    governance_pass_threshold: float = Field(default=0.75, description="Supermajority required for constitutional changes")

class ConfigManager:
    """
    Manages loading, saving, and updating system configuration.
    """
    def __init__(self, config_path: str = "system_config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> SystemConfig:
        """Load config from disk or create default."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                return SystemConfig(**data)
            except Exception as e:
                print(f"⚠️ Error loading config, using defaults: {e}")
                return SystemConfig()
        else:
            # Create default config file
            default_config = SystemConfig()
            self._save_config(default_config)
            return default_config

    def _save_config(self, config: SystemConfig):
        """Save config to disk."""
        with open(self.config_path, 'w') as f:
            f.write(config.model_dump_json(indent=2))

    def get_config(self) -> SystemConfig:
        """Get current configuration."""
        return self.config

    def update_ulfr_weights(self, alpha: float, beta: float, gamma: float, delta: float):
        """Update ULFR weights dynamically."""
        # Normalize if needed, or trust the proposal
        total = alpha + beta + gamma + delta
        if abs(total - 1.0) > 0.01:
             print(f"⚠️ Warning: New weights sum to {total}, not 1.0")
        
        self.config.ulfr_weights = ULFRWeights(
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            delta=delta
        )
        self._save_config(self.config)
        print(f"⚙️ [CONFIG] ULFR Weights Updated: U={alpha}, L={beta}, F={gamma}, R={delta}")

    def update_parameter(self, param_name: str, value: Any):
        """Generic parameter update."""
        if hasattr(self.config, param_name):
            setattr(self.config, param_name, value)
            self._save_config(self.config)
            print(f"⚙️ [CONFIG] Parameter '{param_name}' updated to {value}")
        else:
            raise ValueError(f"Unknown parameter: {param_name}")
