from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TypedDict, Protocol, TYPE_CHECKING, List, runtime_checkable, Union
from enum import Enum
import uuid
from modules.finance.dtos import MoneyDTO
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from modules.common.interfaces import IPropertyOwner
from modules.finance.api import IFinancialAgent

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.models import Transaction
    from simulation.core_agents import Household
    from modules.finance.api import IBank, ISettlementSystem
    from modules.simulation.api import IGovernment, IAgent

@dataclass(frozen=True)
class CanonicalOrderDTO:
    """Standardized Market Order Data Transfer Object.
    Replaces legacy dictionary/tuple usage in decision engines.
    Immutable to prevent side-effects during processing.
    """
    agent_id: int | str
    side: str  # "BUY" or "SELL" (formerly order_type)
    item_id: str
    quantity: float
    price_pennies: int # Integer pennies (The SSoT)
    price_limit: float # Legacy float representation (for UI/Logging) - DEPRECATED
    market_id: str

    # Phase 6/7 Extensions
    target_agent_id: Optional[int] = None  # Brand Loyalty / Supply Chain
    brand_info: Optional[Dict[str, Any]] = None # Quality, Awareness
    metadata: Optional[Dict[str, Any]] = None # Side-effects (e.g. Loans)

    # TD-213: Multi-Currency Support
    monetary_amount: Optional[MoneyDTO] = None
    currency: CurrencyCode = DEFAULT_CURRENCY

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

# Alias for backward compatibility
OrderDTO = CanonicalOrderDTO

def convert_legacy_order_to_canonical(order: Any) -> CanonicalOrderDTO:
    """
    Adapter to convert legacy order objects (like StockOrder) or dictionaries
    to the CanonicalOrderDTO format.
    """
    if isinstance(order, CanonicalOrderDTO):
        return order

    # Handle dictionary input
    if isinstance(order, dict):
        item_id = order.get("item_id")
        if not item_id and order.get("firm_id"):
             item_id = f"stock_{order.get('firm_id')}"

        # Determine price
        raw_price = order.get("price_limit") or order.get("price", 0)
        price_pennies = order.get("price_pennies")

        if price_pennies is None:
            if isinstance(raw_price, float):
                 # Assume Dollars -> Convert to Pennies
                 price_pennies = int(raw_price * 100)
            elif isinstance(raw_price, str):
                 # Try convert to float first
                 try:
                     val = float(raw_price)
                     # Heuristic: if it looks like an int (e.g. "1050"), treat as pennies?
                     # But "10.50" becomes 10.5.
                     # If string has decimal, assume dollars.
                     if "." in raw_price:
                         price_pennies = int(val * 100)
                     else:
                         price_pennies = int(val)
                 except ValueError:
                     price_pennies = 0
            else:
                 # Assume Pennies (int)
                 price_pennies = int(raw_price)

        return CanonicalOrderDTO(
            agent_id=order.get("agent_id"),
            side=order.get("side") or order.get("order_type"),
            item_id=item_id,
            quantity=order.get("quantity"),
            price_pennies=price_pennies,
            price_limit=float(raw_price),
            market_id=order.get("market_id", "stock_market"),
            target_agent_id=order.get("target_agent_id"),
            brand_info=order.get("brand_info"),
            metadata=order.get("metadata"),
            monetary_amount=order.get("monetary_amount"),
            currency=order.get("currency", DEFAULT_CURRENCY)
        )

    # Handle Legacy StockOrder (duck typing to avoid circular import)
    if hasattr(order, "firm_id") and hasattr(order, "order_type") and hasattr(order, "price"):
        # StockOrder.price was int (pennies)
        return CanonicalOrderDTO(
            agent_id=order.agent_id,
            side=order.order_type,
            item_id=f"stock_{order.firm_id}",
            quantity=order.quantity,
            price_pennies=int(order.price),
            price_limit=float(order.price),
            market_id=getattr(order, "market_id", "stock_market"),
        )

    raise ValueError(f"Cannot convert object of type {type(order)} to CanonicalOrderDTO")

# --- Data Transfer Objects (DTOs) ---

class HousingConfigDTO(TypedDict):
    """Configuration parameters for housing market transactions."""
    max_ltv_ratio: float
    mortgage_term_ticks: int
    # Note: Interest rate is handled by the banking/lending system config

@dataclass
class MarketConfigDTO:
    """Configuration DTO for market mechanics."""
    transaction_fee: float = 0.0
    housing_max_ltv: float = 0.8
    housing_mortgage_term: int = 300

@dataclass
class HousingTransactionContextDTO:
    """
    DTO capturing the system state required to process a housing transaction.
    Decouples the handler from the monolithic 'simulation' object.
    """
    settlement_system: "ISettlementSystem"
    bank: Optional["IBank"]
    government: Optional[IPropertyOwner]
    real_estate_units: List[Any] # List[RealEstateUnit]
    agents: Dict[Any, "IAgent"]
    config_module: Any # Should be MarketConfigDTO in strict future
    time: int
    transaction_queue: List[Any] # For side-effect transactions (credit creation)

class TransactionType(Enum):
    HOUSING = "housing"
    GOODS = "goods"
    LABOR = "labor"

@dataclass
class TransactionResultDTO:
    """Result of a transaction processing attempt."""
    success: bool
    reason: Optional[str] = None
    transaction_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class OrderBookStateDTO:
    """State DTO for generic OrderBook markets (Goods, Labor)."""
    buy_orders: Dict[str, List[CanonicalOrderDTO]]
    sell_orders: Dict[str, List[CanonicalOrderDTO]]
    market_id: str

@dataclass
class StockMarketStateDTO:
    """State DTO for Stock Markets."""
    buy_orders: Dict[int, List[CanonicalOrderDTO]] # firm_id -> orders
    sell_orders: Dict[int, List[CanonicalOrderDTO]]
    market_id: str

@dataclass
class MatchingResultDTO:
    """Result DTO returned by stateless matching engines."""
    transactions: List["Transaction"]
    unfilled_buy_orders: Dict[str, List[CanonicalOrderDTO]] # item_id (or firm_id str) -> orders
    unfilled_sell_orders: Dict[str, List[CanonicalOrderDTO]]
    market_stats: Dict[str, Any] # e.g. last_traded_prices, volume

# --- Interfaces ---

class IMatchingEngine(Protocol):
    """Protocol for stateless market matching engines."""
    def match(self, state: Any, current_tick: int) -> MatchingResultDTO:
        """Executes matching logic on the provided state snapshot."""
        ...

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

@runtime_checkable
class IHousingTransactionParticipant(IPropertyOwner, IFinancialAgent, Protocol):
    """
    Protocol for agents participating in housing transactions as buyers.
    Combines financial capabilities with property ownership and income verification.
    """
    @property
    def current_wage(self) -> int: # Changed to int (pennies) for consistency
        """Current wage for mortgage eligibility calculation."""
        ...

    @property
    def residing_property_id(self) -> Optional[int]:
        """ID of the property where the agent currently resides."""
        ...

    @property
    def is_homeless(self) -> bool:
        """Indicates if the agent is currently homeless."""
        ...

class IMarket(Protocol):
    """
    Standard interface for all market types.
    TD-271: Enforces strictly typed CanonicalOrderDTOs for public access.
    """
    id: str

    @property
    def buy_orders(self) -> Dict[str, List[CanonicalOrderDTO]]:
        """Returns active buy orders as immutable/copy DTOs."""
        ...

    @property
    def sell_orders(self) -> Dict[str, List[CanonicalOrderDTO]]:
        """Returns active sell orders as immutable/copy DTOs."""
        ...

    def place_order(self, order_dto: CanonicalOrderDTO, current_time: int) -> None:
        """Submits a new order to the market."""
        ...

    def clear_orders(self) -> None:
        """Clears all orders for the current tick."""
        ...
