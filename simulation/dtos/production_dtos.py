from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass(frozen=True)
class ProductionInputDTO:
    """Inputs required for production calculation."""
    total_labor_skill: float
    avg_skill: float
    input_inventory: Dict[str, float]
    productivity_multiplier: float = 1.0
    firm_id: int = 0
    current_time: int = 0

@dataclass(frozen=True)
class ProductionResultDTO:
    """Output results from production engine."""
    quantity: float
    quality: float
    specialization: str
    consumed_inputs: Dict[str, float] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
