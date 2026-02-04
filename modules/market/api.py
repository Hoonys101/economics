from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TypedDict, Protocol, TYPE_CHECKING
import uuid
from modules.finance.dtos import MoneyDTO

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.models import Transaction
    from simulation.core_agents import Household

@dataclass(frozen=True)
class OrderDTO:
    """Standardized Market Order Data Transfer Object.
    Replaces legacy dictionary/tuple usage in decision engines.
    Immutable to prevent side-effects during processing.
    """
    agent_id: int | str
    side: str  # "BUY" or "SELL" (formerly order_type)
    item_id: str
    quantity: float
    price_limit: float # (formerly price) - Max for BUY, Min for SELL
    market_id: str

    # Phase 6/7 Extensions
    target_agent_id: Optional[int] = None  # Brand Loyalty / Supply Chain
    brand_info: Optional[Dict[str, Any]] = None # Quality, Awareness
    metadata: Optional[Dict[str, Any]] = None # Side-effects (e.g. Loans)

    # TD-213: Multi-Currency Support
    monetary_amount: Optional[MoneyDTO] = None

    # Auto-generated ID
    id: str = field(default_factory=lambda: str(uuid.uuid4()), init=False)

    @property
    def price(self) -> float:
        """Alias for legacy compatibility during migration."""
        return self.price_limit

    @property
    def order_type(self) -> str:
        """Alias for legacy compatibility during migration."""
        return self.side

# --- Data Transfer Objects (DTOs) ---

class HousingConfigDTO(TypedDict):
    """Configuration parameters for housing market transactions."""
    max_ltv_ratio: float
    mortgage_term_ticks: int
    # Note: Interest rate is handled by the banking/lending system config

# --- Interfaces ---

class ISpecializedTransactionHandler(Protocol):
    """
    Interface for handlers that manage specific, complex transaction types.
    This is a pre-existing interface that we will implement.
    """
    def handle(
        self,
        tx: "Transaction",
        buyer: "Household",
        seller: Any, # Can be Household or Firm
        state: "SimulationState"
    ) -> bool:
        """
        Executes the specialized transaction logic.
        Returns True on success, False on failure.
        """
        ...

class IHousingTransactionHandler(ISpecializedTransactionHandler, Protocol):
    """Explicit protocol for the housing transaction handler."""
    ...
