from dataclasses import dataclass
from typing import List, Any
from simulation.models import Order

@dataclass
class DecisionOutputDTO:
    """Standardized output from decision engines."""
    orders: List[Order]
    metadata: Any = None
