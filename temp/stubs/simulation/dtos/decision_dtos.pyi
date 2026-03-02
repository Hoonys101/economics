from dataclasses import dataclass
from simulation.models import Order as Order
from typing import Any

@dataclass
class DecisionOutputDTO:
    """Standardized output from decision engines."""
    orders: list[Order]
    metadata: Any = ...
