from _typeshed import Incomplete
from dataclasses import dataclass, field
from enum import Enum
from modules.common.interfaces import IPropertyOwner as IPropertyOwner
from modules.finance.api import IBank as IBank, IFinancialAgent as IFinancialAgent, ISettlementSystem as ISettlementSystem
from modules.finance.dtos import MoneyDTO as MoneyDTO
from modules.government.api import IGovernment as IGovernment
from modules.market.safety_dtos import PriceLimitConfigDTO as PriceLimitConfigDTO, ValidationResultDTO as ValidationResultDTO
from modules.simulation.api import IAgent as IAgent
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from pydantic import BaseModel
from simulation.core_agents import Household as Household
from simulation.dtos.api import SimulationState as SimulationState
from simulation.models import Transaction as Transaction
from typing import Any, Protocol, TypedDict

class MarketSide(str, Enum):
    BUY = 'BUY'
    SELL = 'SELL'

@dataclass(frozen=True)
class CanonicalOrderDTO:
    """
    Standardized Market Order Data Transfer Object (Engine Layer).
    Immutable to prevent side-effects during processing.

    Adheres to [SEO_PATTERN.md] - Pure Data.
    """
    agent_id: int | str
    side: str
    item_id: str
    quantity: float
    price_pennies: int
    market_id: str
    price_limit: float = ...
    target_agent_id: int | None = ...
    brand_info: dict[str, Any] | None = ...
    metadata: dict[str, Any] | None = ...
    monetary_amount: MoneyDTO | None = ...
    currency: CurrencyCode = ...
    id: str = field(default_factory=Incomplete)
    @property
    def price(self) -> float:
        """Alias for legacy compatibility. Returns float dollars."""
    @property
    def order_type(self) -> str:
        """Alias for legacy compatibility."""

class OrderTelemetrySchema(BaseModel):
    """
    Pydantic model for strictly typed UI/Websocket serialization.
    Satisfies [TD-UI-DTO-PURITY].
    """
    id: str
    agent_id: int | str
    side: MarketSide
    item_id: str
    quantity: float
    price_pennies: int
    price_display: float
    market_id: str
    currency: str
    timestamp: int
    @classmethod
    def normalize_side(cls, v): ...
    @classmethod
    def from_canonical(cls, dto: CanonicalOrderDTO, timestamp: int = 0) -> OrderTelemetrySchema:
        """Adapter: CanonicalOrderDTO -> OrderTelemetrySchema"""
OrderDTO = CanonicalOrderDTO

def convert_legacy_order_to_canonical(order: Any) -> CanonicalOrderDTO:
    """
    Adapter to convert legacy order objects (like StockOrder) or dictionaries
    to the CanonicalOrderDTO format.
    """

class StockIDHelper:
    """Helper for Stock ID formatting and parsing."""
    PREFIX: str
    SEPARATOR: str
    @staticmethod
    def is_valid_stock_id(item_id: str) -> bool:
        """Checks if the item_id matches the 'stock_{int}' format."""
    @staticmethod
    def parse_firm_id(item_id: str) -> int:
        """
        Parses the firm_id from a stock item_id.
        Raises ValueError if format is invalid.
        """
    @staticmethod
    def format_stock_id(firm_id: int | str) -> str:
        """Formats a firm_id into a stock item_id."""

class HousingConfigDTO(TypedDict):
    """Configuration parameters for housing market transactions."""
    max_ltv_ratio: float
    mortgage_term_ticks: int

@dataclass
class MarketConfigDTO:
    """Configuration DTO for market mechanics."""
    transaction_fee: float = ...
    housing_max_ltv: float = ...
    housing_mortgage_term: int = ...

@dataclass
class HousingTransactionContextDTO:
    """
    DTO capturing the system state required to process a housing transaction.
    Decouples the handler from the monolithic 'simulation' object.
    """
    settlement_system: ISettlementSystem
    bank: IBank | None
    government: IPropertyOwner | None
    real_estate_units: list[Any]
    agents: dict[Any, 'IAgent']
    config_module: Any
    time: int
    transaction_queue: list[Any]

class TransactionType(Enum):
    HOUSING = 'housing'
    GOODS = 'goods'
    LABOR = 'labor'

@dataclass
class TransactionResultDTO:
    """Result of a transaction processing attempt."""
    success: bool
    reason: str | None = ...
    transaction_id: str | None = ...
    metadata: dict[str, Any] | None = ...

@dataclass
class OrderBookStateDTO:
    """State DTO for generic OrderBook markets (Goods, Labor)."""
    buy_orders: dict[str, list[CanonicalOrderDTO]]
    sell_orders: dict[str, list[CanonicalOrderDTO]]
    market_id: str

@dataclass
class StockMarketStateDTO:
    """State DTO for Stock Markets."""
    buy_orders: dict[int, list[CanonicalOrderDTO]]
    sell_orders: dict[int, list[CanonicalOrderDTO]]
    market_id: str

@dataclass
class MatchingResultDTO:
    """Result DTO returned by stateless matching engines."""
    transactions: list['Transaction']
    unfilled_buy_orders: dict[str, list[CanonicalOrderDTO]]
    unfilled_sell_orders: dict[str, list[CanonicalOrderDTO]]
    market_stats: dict[str, Any]

class IMatchingEngine(Protocol):
    """Protocol for stateless market matching engines."""
    def match(self, state: Any, current_tick: int) -> MatchingResultDTO:
        """Executes matching logic on the provided state snapshot."""

class ISpecializedTransactionHandler(Protocol):
    """
    Interface for handlers that manage specific, complex transaction types.
    This is a pre-existing interface that we will implement.
    """
    def handle(self, tx: Transaction, buyer: Household, seller: Any, state: SimulationState) -> bool:
        """
        Executes the specialized transaction logic.
        Returns True on success, False on failure.
        """

class IHousingTransactionHandler(ISpecializedTransactionHandler, Protocol):
    """Explicit protocol for the housing transaction handler."""

class IHousingTransactionParticipant(IPropertyOwner, IFinancialAgent, Protocol):
    """
    Protocol for agents participating in housing transactions as buyers.
    Combines financial capabilities with property ownership and income verification.
    """
    @property
    def current_wage(self) -> int:
        """Current wage for mortgage eligibility calculation."""
    @property
    def residing_property_id(self) -> int | None:
        """ID of the property where the agent currently resides."""
    @residing_property_id.setter
    def residing_property_id(self, value: int | None) -> None:
        """Sets the property where the agent currently resides."""
    @property
    def is_homeless(self) -> bool:
        """Indicates if the agent is currently homeless."""
    @is_homeless.setter
    def is_homeless(self, value: bool) -> None:
        """Sets the homeless status of the agent."""

class IMarket(Protocol):
    """
    Standard interface for all market types.
    TD-271: Enforces strictly typed CanonicalOrderDTOs for public access.
    """
    id: str
    @property
    def buy_orders(self) -> dict[str, list[CanonicalOrderDTO]]:
        """Returns active buy orders as immutable/copy DTOs."""
    @property
    def sell_orders(self) -> dict[str, list[CanonicalOrderDTO]]:
        """Returns active sell orders as immutable/copy DTOs."""
    def place_order(self, order_dto: CanonicalOrderDTO, current_time: int) -> None:
        """Submits a new order to the market."""
    def clear_orders(self) -> None:
        """Clears all orders for the current tick."""
    def cancel_orders(self, agent_id: str) -> None:
        """Cancels all orders for the specified agent."""
    def get_telemetry_snapshot(self) -> list[OrderTelemetrySchema]:
        """Returns Pydantic schemas for UI consumption."""

@dataclass(frozen=True)
class MarriageProposalDTO:
    """
    Represents a proposal for household merger (M&A).
    Financial values in Integer Pennies.
    """
    proposer_id: int
    target_id: int
    combined_wealth_pennies: int
    synergy_score: float

@dataclass(frozen=True)
class MarriageResultDTO:
    """Result of a processed marriage proposal."""
    success: bool
    new_household_id: int | None
    merged_assets_pennies: int
    message: str = ...

class IMarriageMarket(Protocol):
    """
    Protocol for the centralized Marriage Market orchestration.
    Handles matching, proposal validation, and execution of mergers.
    Zero-Sum mandate: Sum(Assets_Before) == Sum(Assets_After).
    """
    def post_proposal(self, proposal: MarriageProposalDTO) -> None:
        """Submits a proposal to the market ledger."""
    def execute_mergers(self) -> list[MarriageResultDTO]:
        """
        Processes all pending proposals, executes valid mergers
        (Zero-Sum asset transfer), and clears the queue.
        """
    def get_proposals_for(self, agent_id: int) -> list[MarriageProposalDTO]:
        """Retrieves proposals targeting a specific agent."""

class IPriceLimitEnforcer(Protocol):
    """
    Stateless enforcer for price limits, strictly adhering to the Penny Standard (int).
    Validates orders against reference prices and configured limits.
    """
    def validate_order(self, order: CanonicalOrderDTO) -> ValidationResultDTO:
        """
        Validates an order's price against active boundaries.
        MUST remain strictly idempotent and side-effect free (SRP).
        """
    def set_reference_price(self, price: int) -> None:
        """
        Sets the reference anchor price used for dynamic boundary calculations.
        """
    def update_config(self, config: PriceLimitConfigDTO) -> None:
        """
        Updates the enforcer's active configuration limits.
        """

class IIndexCircuitBreaker(Protocol):
    """
    Market-wide circuit breaker to monitor macroeconomic health and halt trading.
    """
    def check_market_health(self, market_stats: dict[str, Any]) -> bool:
        """
        Evaluates overall market health statistics to determine if a halt is required.
        Returns True if healthy, False if a halt is triggered.
        """
    def is_active(self) -> bool:
        """
        Returns True if the market is currently halted by the circuit breaker.
        """

class ICircuitBreaker(IPriceLimitEnforcer, Protocol):
    """
    Legacy ICircuitBreaker maintained for backward compatibility.
    Aggregates new safety protocols.
    """
    def get_dynamic_price_bounds(self, item_id: str, current_tick: int, last_trade_tick: int) -> tuple[float, float]:
        """Calculates price bounds with temporal relaxation to prevent liquidity traps."""
    def update_price_history(self, item_id: str, price: float) -> None:
        """Records a traded price to update volatility calculations."""
