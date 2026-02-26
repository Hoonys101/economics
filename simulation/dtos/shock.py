from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class ShockDTO:
    """
    Data Transfer Object representing a Mid-Tick Shock scenario event.
    """
    tick: int
    type: str  # e.g., "TFP", "DEMAND", "FISCAL", "MONETARY"
    target: str # e.g., "ALL", "SECTOR:FOOD", "FIRM:123"
    value: float # The primary magnitude of the shock
    duration: int # Duration in ticks
    parameters: Dict[str, Any] = field(default_factory=dict) # Additional context
