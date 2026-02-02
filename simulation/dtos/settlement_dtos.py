from typing import List, Dict, Any, Literal
from dataclasses import dataclass, field
import uuid

@dataclass
class EstateValuationDTO:
    """A read-only snapshot of the deceased's wealth."""
    cash: float
    real_estate_value: float
    stock_value: float
    total_wealth: float
    tax_due: float
    stock_holdings: Dict[int, float] # {firm_id: quantity}
    property_holdings: List[int] # [property_id]

@dataclass
class EstateSettlementSaga:
    """The complete, atomic unit of work for settling an estate."""
    deceased_id: int
    heir_ids: List[int]
    government_id: int
    valuation: EstateValuationDTO
    current_tick: int
    saga_type: Literal["ESTATE_SETTLEMENT"] = "ESTATE_SETTLEMENT"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
