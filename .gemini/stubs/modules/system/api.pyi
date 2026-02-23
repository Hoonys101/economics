from dataclasses import dataclass, field
from enum import IntEnum, auto as auto
from pydantic import BaseModel
from typing import Any, Protocol, TypedDict

CurrencyCode = str
DEFAULT_CURRENCY: CurrencyCode
AgentID = int

class IWorldState(Protocol):
    """Module B: Protocol for decoupled world state management."""
    def get_agent(self, agent_id: AgentID) -> IAgent | None:
        """Retrieves an agent by ID or None if not found."""
    def register_government(self, gov: Any) -> None:
        """Registers a government entity to the multi-gov pool."""
    def get_governments(self) -> list[Any]:
        """Returns the list of all active government entities."""

class IGovernmentRegistry(Protocol):
    """Module B: Protocol for specialized government lifecycle management."""
    def get_primary_government(self) -> Any:
        """SSoT for the main government entity."""
    def sync_multi_gov_state(self) -> None:
        """Synchronizes policies across multiple government entities."""

@dataclass
class MarketContextDTO:
    """
    Context object passed to agents for making decisions.
    Contains strictly external market data (prices, rates, signals).
    """
    market_data: dict[str, Any] = field(default_factory=dict)
    market_signals: dict[str, int] = field(default_factory=dict)
    tick: int = ...
    exchange_rates: dict[str, float] | None = ...
    benchmark_rates: dict[str, float] = field(default_factory=dict)
    fiscal_policy: Any | None = ...

@dataclass(frozen=True)
class MarketSignalDTO:
    market_id: str
    item_id: str
    best_bid: int | None
    best_ask: int | None
    last_traded_price: int | None
    last_trade_tick: int
    price_history_7d: list[int]
    volatility_7d: float
    order_book_depth_buy: int
    order_book_depth_sell: int
    total_bid_quantity: float
    total_ask_quantity: float
    is_frozen: bool

@dataclass(frozen=True)
class HousingMarketUnitDTO:
    unit_id: str
    price: int
    quality: float
    rent_price: int | None = ...

@dataclass(frozen=True)
class HousingMarketSnapshotDTO:
    for_sale_units: list[HousingMarketUnitDTO]
    units_for_rent: list[HousingMarketUnitDTO]
    avg_rent_price: float
    avg_sale_price: float

@dataclass(frozen=True)
class LoanMarketSnapshotDTO:
    interest_rate: float

@dataclass(frozen=True)
class LaborMarketSnapshotDTO:
    avg_wage: float

@dataclass(frozen=True)
class MarketSnapshotDTO:
    """
    A pure-data snapshot of the state of all markets at a point in time.
    """
    tick: int
    market_signals: dict[str, MarketSignalDTO]
    market_data: dict[str, Any]
    housing: HousingMarketSnapshotDTO | None = ...
    loan: LoanMarketSnapshotDTO | None = ...
    labor: LaborMarketSnapshotDTO | None = ...

class AgentBankruptcyEventDTO(TypedDict):
    agent_id: int
    tick: int
    inventory: dict[str, float]
    total_debt: int
    creditor_ids: list[int]

@dataclass(frozen=True)
class AssetBuyoutRequestDTO:
    """
    Request payload for the PublicManager to purchase assets from a distressed entity.
    """
    seller_id: AgentID
    inventory: dict[str, float]
    market_prices: dict[str, int]
    distress_discount: float = ...

@dataclass(frozen=True)
class AssetBuyoutResultDTO:
    """
    Result of an asset buyout operation.
    """
    success: bool
    total_paid_pennies: int
    items_acquired: dict[str, float]
    buyer_id: AgentID
    transaction_id: str | None = ...

@dataclass(frozen=True)
class PublicManagerReportDTO:
    tick: int
    newly_recovered_assets: dict[str, float]
    liquidation_revenue: dict[str, int]
    managed_inventory_count: float
    system_treasury_balance: dict[str, int]
    cumulative_deficit: int = ...

class OriginType(IntEnum):
    """
    Priority Level for Parameter Updates.
    Higher value = Higher Priority.
    """
    SYSTEM = 0
    CONFIG = 10
    USER = 50
    GOD_MODE = 100

class RegistryValueDTO(BaseModel):
    """
    Data Transfer Object for Registry Values.
    Replaces the legacy RegistryEntry dataclass.
    """
    key: str
    value: Any
    domain: str
    origin: OriginType
    is_locked: bool
    last_updated_tick: int
    metadata: dict[str, Any]
RegistryEntry = RegistryValueDTO

class RegistryObserver(Protocol):
    def on_registry_update(self, key: str, value: Any, origin: OriginType) -> None: ...

class IConfigurationRegistry(Protocol):
    """
    Interface for the Global Registry acting as the Single Source of Truth (SSoT)
    for all simulation parameters.
    """
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value.
        Must support dynamic resolution (always fetch current value).
        """
    def set(self, key: str, value: Any, origin: OriginType = ...) -> None:
        """
        Updates a configuration value with a specified origin.
        Should trigger any registered listeners for this key.
        """
    def snapshot(self) -> dict[str, Any]:
        """
        Returns a complete snapshot of the current configuration state.
        Useful for serialization or debugging.
        """
    def reset_to_defaults(self) -> None:
        """
        Resets all configuration values to their SYSTEM or CONFIG defaults,
        clearing USER overrides.
        """

class IGlobalRegistry(Protocol):
    """
    Interface for the Global Parameter Registry.
    FOUND-01: Centralized Configuration Management.
    """
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any, origin: OriginType = ...) -> bool: ...
    def lock(self, key: str) -> None: ...
    def unlock(self, key: str) -> None: ...
    def subscribe(self, observer: RegistryObserver, keys: list[str] | None = None) -> None: ...
    def snapshot(self) -> dict[str, RegistryValueDTO]: ...
    def get_metadata(self, key: str) -> Any: ...
    def get_entry(self, key: str) -> RegistryValueDTO | None: ...

class IRestorableRegistry(IGlobalRegistry, Protocol):
    """
    Extended interface for Registries that support state restoration/undo operations.
    Required for CommandService rollback functionality.
    """
    def delete_entry(self, key: str) -> bool:
        """
        Removes an entry completely. Used when rolling back a creation.
        Returns True if successful.
        """
    def restore_entry(self, key: str, entry: RegistryValueDTO) -> bool:
        """
        Restores a specific entry state (value + origin + lock).
        Used when rolling back a modification.
        Returns True if successful.
        """

class IProtocolEnforcer(Protocol):
    """
    Interface for test utilities that enforce strict protocol adherence.
    """
    def assert_implements_protocol(self, instance: Any, protocol: Any) -> None:
        """
        Verifies that an instance implements all methods and attributes
        defined in the protocol. Raises AssertionError if not.
        """

class IAgentRegistry(Protocol):
    def get_agent(self, agent_id: Any) -> Any: ...
    def get_all_financial_agents(self) -> list[Any]: ...
    def set_state(self, state: Any) -> None: ...

class ICurrencyHolder(Protocol):
    """
    Protocol for agents/systems that hold currency.
    Used for M2 Money Supply calculation.
    """
    def get_balance(self, currency: CurrencyCode = ...) -> int: ...
    def get_assets_by_currency(self) -> dict[CurrencyCode, int]: ...

class IAssetRecoverySystem(Protocol):
    """
    Interface for the Public Manager acting as a receiver of assets.
    Now supports active buyout logic to inject liquidity.
    """
    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None:
        """
        Legacy ingestion of assets (deprecated in favor of execute_asset_buyout).
        """
    def execute_asset_buyout(self, request: AssetBuyoutRequestDTO) -> AssetBuyoutResultDTO:
        """
        Purchases assets from a distressed agent to provide liquidity for creditor repayment.
        Allowed to go into overdraft (Soft Budget Constraint).
        """
    def receive_liquidated_assets(self, inventory: dict[str, float]) -> None:
        """
        Receives inventory from a firm undergoing liquidation (Asset Buyout).
        """
    def generate_liquidation_orders(self, market_signals: dict[str, MarketSignalDTO], core_config: Any = None, engine: Any = None) -> list[Any]:
        """
        Generates SELL orders to liquidate managed assets into the market.
        """
    def get_deficit(self) -> int:
        """
        Returns the cumulative deficit (negative balance) incurred by operations.
        """

class ISystemFinancialAgent(Protocol):
    """
    Marker interface for system agents (like PublicManager) that are exempt
    from strict solvency checks during specific system operations.
    """
    def is_system_agent(self) -> bool: ...

@dataclass(frozen=True)
class MigrationReportDTO:
    """
    Report generated after a database schema migration attempt.
    """
    success: bool
    migrated_tables: list[str]
    rows_affected: int
    errors: list[str]
    timestamp: float
    schema_version: str = ...

class IDatabaseMigrator(Protocol):
    """
    Protocol for the Database Migration Service.
    Responsible for ensuring the database schema matches the codebase's expectations.
    """
    def check_schema_health(self) -> dict[str, bool]:
        """
        Verifies if critical tables and columns exist.
        Returns a dict mapping 'Table.Column' to Boolean existence.
        """
    def migrate(self) -> MigrationReportDTO:
        """
        Executes pending migrations (e.g., adding missing columns).
        Must be idempotent.
        """
