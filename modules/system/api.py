from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable, TYPE_CHECKING, TypedDict
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from modules.simulation.dtos.api import MoneySupplyDTO
    from modules.simulation.api import EconomicIndicatorsDTO

# Define Currency Code (Usually String "USD")
CurrencyCode = str
DEFAULT_CURRENCY: CurrencyCode = "USD"
AgentID = int

@runtime_checkable
class IAgent(Protocol):
    id: AgentID
    is_active: bool

@runtime_checkable
class IWorldStateMetricsProvider(Protocol):
    """
    Protocol extension for IWorldState to safely provide metrics to Scenario Judges
    without exposing God Class internals or mutable Trackers.
    """
    def calculate_total_money(self) -> MoneySupplyDTO:
        """Provides Physics-tier monetary aggregates (M2, System Debt) in integer pennies."""
        ...

    def get_economic_indicators(self) -> EconomicIndicatorsDTO:
        """Provides Macro-tier indicators (GDP, CPI, Unemployment) safely."""
        ...

    def get_market_panic_index(self) -> float:
        """Provides Micro-tier sentiment and panic indices safely."""
        ...

@runtime_checkable
class IWorldState(IWorldStateMetricsProvider, Protocol):
    """Module B: Protocol for decoupled world state management."""
    def get_agent(self, agent_id: AgentID) -> Optional[IAgent]:
        """Retrieves an agent by ID or None if not found."""
        ...

    def register_government(self, gov: Any) -> None:
        """Registers a government entity to the multi-gov pool."""
        ...

    def get_governments(self) -> List[Any]:
        """Returns the list of all active government entities."""
        ...

    # --- NEW: Read-Only System Expositions for Scenario Judges ---

    def get_technology_system(self) -> Any:
        """
        Provides read-only access to the technology diffusion state.
        Replaces direct `sim.technology_manager` access in legacy verifiers.
        """
        ...

    def get_monetary_ledger(self) -> Any:
        """
        Provides read-only access to the SSoT for money supply (M2) and debt.
        Replaces direct `sim._calculate_total_money()` access.
        """
        ...

    def get_all_firms(self) -> Sequence[Any]:
        """
        Returns a sequence of all firm agents adhering to IFirm protocol.
        """
        ...

    def get_all_households(self) -> Sequence[Any]:
        """
        Returns a sequence of all household agents adhering to IHousehold protocol.
        """
        ...

@runtime_checkable
class IGovernmentRegistry(Protocol):
    """Module B: Protocol for specialized government lifecycle management."""
    def get_primary_government(self) -> Any:
        """SSoT for the main government entity."""
        ...

    def sync_multi_gov_state(self) -> None:
        """Synchronizes policies across multiple government entities."""
        ...

@dataclass
class MarketContextDTO:
    """
    Context object passed to agents for making decisions.
    Contains strictly external market data (prices, rates, signals).
    """
    market_data: Dict[str, Any] = field(default_factory=dict)
    market_signals: Dict[str, int] = field(default_factory=dict)
    tick: int = 0
    # Represents currency exchange rates relative to base currency
    exchange_rates: Optional[Dict[str, float]] = None
    # Added for DTO Hygiene
    benchmark_rates: Dict[str, float] = field(default_factory=dict)
    fiscal_policy: Optional[Any] = None

@dataclass(frozen=True)
class MarketSignalDTO:
    market_id: str
    item_id: str
    best_bid: Optional[int]
    best_ask: Optional[int]
    last_traded_price: Optional[int]
    last_trade_tick: int
    price_history_7d: List[int]
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
    rent_price: Optional[int] = None

@dataclass(frozen=True)
class HousingMarketSnapshotDTO:
    for_sale_units: List[HousingMarketUnitDTO]
    units_for_rent: List[HousingMarketUnitDTO]
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
    market_signals: Dict[str, MarketSignalDTO]
    market_data: Dict[str, Any]
    housing: Optional[HousingMarketSnapshotDTO] = None
    loan: Optional[LoanMarketSnapshotDTO] = None
    labor: Optional[LaborMarketSnapshotDTO] = None

class AgentBankruptcyEventDTO(TypedDict):
    agent_id: int
    tick: int
    inventory: Dict[str, float]
    total_debt: int
    creditor_ids: List[int]

@dataclass(frozen=True)
class AssetBuyoutRequestDTO:
    """
    Request payload for the PublicManager to purchase assets from a distressed entity.
    """
    seller_id: AgentID
    inventory: Dict[str, float]
    market_prices: Dict[str, int]  # Current market price (pennies) for valuation
    distress_discount: float = 0.5 # e.g., 50% of market value

@dataclass(frozen=True)
class AssetBuyoutResultDTO:
    """
    Result of an asset buyout operation.
    """
    success: bool
    total_paid_pennies: int
    items_acquired: Dict[str, float]
    buyer_id: AgentID  # PublicManager ID
    transaction_id: Optional[str] = None

@dataclass(frozen=True)
class PublicManagerReportDTO:
    tick: int
    newly_recovered_assets: Dict[str, float]
    liquidation_revenue: Dict[str, int]
    managed_inventory_count: float
    system_treasury_balance: Dict[str, int]
    cumulative_deficit: int = 0  # Added to track total "bailout" funding injected

class OriginType(IntEnum):
    """
    Priority Level for Parameter Updates.
    Higher value = Higher Priority.
    """
    SYSTEM = 0          # Internal logic (Hardcoded defaults)
    CONFIG = 10         # Loaded from file (User Configuration)
    USER = 50           # Dashboard/UI manual override
    GOD_MODE = 100      # Absolute override (Scenario Injection)

class RegistryValueDTO(BaseModel):
    """
    Data Transfer Object for Registry Values.
    Replaces the legacy RegistryEntry dataclass.
    """
    key: str
    value: Any
    domain: str = "global"
    origin: OriginType
    is_locked: bool = False
    last_updated_tick: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Alias for backward compatibility if needed, but we prefer RegistryValueDTO
RegistryEntry = RegistryValueDTO

class RegistryObserver(Protocol):
    def on_registry_update(self, key: str, value: Any, origin: OriginType) -> None:
        ...

@runtime_checkable
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
        ...

    def set(self, key: str, value: Any, origin: OriginType = OriginType.USER) -> bool:
        """
        Updates a configuration value with a specified origin.
        Should trigger any registered listeners for this key.
        """
        ...

    def snapshot(self) -> Dict[str, Any]:
        """
        Returns a complete snapshot of the current configuration state.
        Useful for serialization or debugging.
        """
        ...

    def reset_to_defaults(self) -> None:
        """
        Resets all configuration values to their SYSTEM or CONFIG defaults,
        clearing USER overrides.
        """
        ...

@runtime_checkable
class IGlobalRegistry(Protocol):
    """
    Interface for the Global Parameter Registry.
    FOUND-01: Centralized Configuration Management.
    """
    def get(self, key: str, default: Any = None) -> Any:
        ...

    def set(self, key: str, value: Any, origin: OriginType = OriginType.CONFIG) -> bool:
        ...

    def lock(self, key: str) -> None:
        ...

    def unlock(self, key: str) -> None:
        ...

    def subscribe(self, observer: RegistryObserver, keys: Optional[List[str]] = None) -> None:
        ...

    def snapshot(self) -> Dict[str, RegistryValueDTO]:
        ...

    def get_metadata(self, key: str) -> Any:
        ...

    def get_entry(self, key: str) -> Optional[RegistryValueDTO]:
        ...

@runtime_checkable
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
        ...

    def restore_entry(self, key: str, entry: RegistryValueDTO) -> bool:
        """
        Restores a specific entry state (value + origin + lock).
        Used when rolling back a modification.
        Returns True if successful.
        """
        ...

@runtime_checkable
class IProtocolEnforcer(Protocol):
    """
    Interface for test utilities that enforce strict protocol adherence.
    """

    def assert_implements_protocol(self, instance: Any, protocol: Any) -> None:
        """
        Verifies that an instance implements all methods and attributes
        defined in the protocol. Raises AssertionError if not.
        """
        ...

@runtime_checkable
class ISystemAgentRegistry(Protocol):
    """
    Protocol for system agent registration and retrieval.
    Explicitly supports IDs that might evaluate to False (e.g., Agent 0).
    """
    def register_system_agent(self, agent: IAgent) -> None:
        """Registers a system agent bypassing standard initialization constraints."""
        ...

    def get_system_agent(self, agent_id: AgentID) -> Optional[IAgent]:
        """Retrieves a system agent, supporting ID 0."""
        ...

@runtime_checkable
class IAgentRegistry(Protocol):
    def get_agent(self, agent_id: Any) -> Any:
        ...

    def get_all_financial_agents(self) -> List[Any]:
        ...

    def set_state(self, state: Any) -> None:
        ...

    def register(self, agent: Any) -> None:
        """
        Registers an agent into the registry's state.
        Ensures atomic registration visibility.
        """
        ...

    def get_all_agents(self) -> List[Any]:
        ...

    def is_agent_active(self, agent_id: int) -> bool:
        """Returns True if the agent exists and has not been marked INACTIVE/DEAD."""
        ...

@runtime_checkable
class ICurrencyHolder(Protocol):
    """
    Protocol for agents/systems that hold currency.
    Used for M2 Money Supply calculation.
    """
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        ...

    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]:
        ...

@runtime_checkable
class IAssetRecoverySystem(Protocol):
    """
    Interface for the Public Manager acting as a receiver of assets.
    Now supports active buyout logic to inject liquidity.
    """
    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None:
        """
        Legacy ingestion of assets (deprecated in favor of execute_asset_buyout).
        """
        ...

    def execute_asset_buyout(self, request: AssetBuyoutRequestDTO) -> AssetBuyoutResultDTO:
        """
        Purchases assets from a distressed agent to provide liquidity for creditor repayment.
        Allowed to go into overdraft (Soft Budget Constraint).
        """
        ...

    def rollback_asset_buyout(self, request: AssetBuyoutRequestDTO) -> bool:
        """
        Reverses an asset buyout by returning assets from the recovery system's inventory.
        Also attempts to return currency to the recovery system.
        """
        ...

    def set_agent_registry(self, registry: IAgentRegistry) -> None:
        """
        Injects the Agent Registry for lookups during rollback.
        """
        ...

    def receive_liquidated_assets(self, inventory: Dict[str, float]) -> None:
        """
        Receives inventory from a firm undergoing liquidation (Asset Buyout).
        """
        ...

    def generate_liquidation_orders(self, market_signals: Dict[str, MarketSignalDTO], core_config: Any = None, engine: Any = None) -> List[Any]:
        """
        Generates SELL orders to liquidate managed assets into the market.
        """
        ...

    def get_deficit(self) -> int:
        """
        Returns the cumulative deficit (negative balance) incurred by operations.
        """
        ...

@runtime_checkable
class ISystemFinancialAgent(Protocol):
    """
    Marker interface for system agents (like PublicManager) that are exempt
    from strict solvency checks during specific system operations.
    """
    def is_system_agent(self) -> bool:
        ...

# ==============================================================================
# New: Database & Migration Protocols
# ==============================================================================

@dataclass(frozen=True)
class MigrationReportDTO:
    """
    Report generated after a database schema migration attempt.
    """
    success: bool
    migrated_tables: List[str]
    rows_affected: int
    errors: List[str]
    timestamp: float
    schema_version: str = "1.0.0"

@runtime_checkable
class IDatabaseMigrator(Protocol):
    """
    Protocol for the Database Migration Service.
    Responsible for ensuring the database schema matches the codebase's expectations.
    """
    def check_schema_health(self) -> Dict[str, bool]:
        """
        Verifies if critical tables and columns exist.
        Returns a dict mapping 'Table.Column' to Boolean existence.
        """
        ...

    def migrate(self) -> MigrationReportDTO:
        """
        Executes pending migrations (e.g., adding missing columns).
        Must be idempotent.
        """
        ...
