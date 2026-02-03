from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from modules.finance.api import PortfolioDTO

@dataclass
class LegacySettlementAccount:
    """
    TD-160: Transient escrow account for atomic inheritance resolution.
    Holds assets of a deceased agent during the settlement process.
    """
    deceased_agent_id: int
    escrow_cash: float
    escrow_portfolio: PortfolioDTO  # Structurally holds all non-cash assets
    escrow_real_estate: List[Any]  # List of RealEstateUnit objects
    status: str  # OPEN, PROCESSING, CLOSED, ERROR
    created_at: int
    heir_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_escheatment: bool = False

@dataclass
class SettlementResultDTO:
    """
    Result of a settlement execution.
    Used for recording revenue and auditing.
    """
    original_transaction: Any # Transaction
    success: bool
    amount_settled: float
    error: Optional[str] = None
