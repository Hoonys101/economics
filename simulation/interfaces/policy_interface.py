from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IGovernmentPolicy(ABC):
    """
    Interface for government policy decision engines.
    Allows swapping between Rule-based (Taylor Rule) and AI (Adaptive/RL) policies.
    """
    
    @abstractmethod
    def decide(self, government: Any, sensory_data: Any, current_tick: int, central_bank: Any = None) -> Dict[str, Any]:
        """
        Analyzes economic conditions to determine policy (rates, tax, budget).
        
        Args:
            government: The Government agent instance.
            sensory_data: GovernmentSensoryDTO containing smoothed macro data.
            current_tick: Current simulation tick.
            central_bank: The Central Bank agent instance (optional).

        Returns:
            Dict[str, Any]: Decided policy variables (e.g., {"interest_rate_target": 0.05, ...})
        """
        pass
