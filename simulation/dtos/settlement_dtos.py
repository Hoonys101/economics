from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class LegacySettlementAccount:
    """
    TD-160: Transient escrow account for atomic inheritance resolution.
    Holds assets of a deceased agent during the settlement process.
    """
    deceased_agent_id: int
    escrow_cash: float = 0.0
    escrow_portfolio: Dict[str, Any] = field(default_factory=dict) # firm_id -> Share object/Mock
    escrow_real_estate: List[Any] = field(default_factory=list) # List of RealEstateUnit objects
    status: str = "OPEN" # OPEN, PROCESSING, CLOSED, ERROR
    heir_ids: List[int] = field(default_factory=list)
    created_at: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
