from dataclasses import dataclass, field
from enum import IntEnum, auto as auto
from pydantic import BaseModel
from typing import Any, Protocol, TypedDict

CurrencyCode = str
DEFAULT_CURRENCY: CurrencyCode
AgentID = int

class IAgent(Protocol):
    id: AgentID
    is_active: bool

class IWorldState(Protocol):
    def get_agent(self, agent_id: AgentID) -> IAgent | None: ...
    def register_government(self, gov: Any) -> None: ...
    def get_governments(self) -> list[Any]: ...

class IGovernmentRegistry(Protocol):
    def get_primary_government(self) -> Any: ...
    def sync_multi_gov_state(self) -> None: ...

@dataclass
class MarketContextDTO:
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
    seller_id: AgentID
    inventory: dict[str, float]
    market_prices: dict[str, int]
    distress_discount: float = ...

@dataclass(frozen=True)
class AssetBuyoutResultDTO:
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
    SYSTEM = 0
    CONFIG = 10
    USER = 50
    GOD_MODE = 100

class RegistryValueDTO(BaseModel):
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
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any, origin: OriginType = ...) -> bool: ...
    def snapshot(self) -> dict[str, Any]: ...
    def reset_to_defaults(self) -> None: ...

class IGlobalRegistry(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any, origin: OriginType = ...) -> bool: ...
    def lock(self, key: str) -> None: ...
    def unlock(self, key: str) -> None: ...
    def subscribe(self, observer: RegistryObserver, keys: list[str] | None = None) -> None: ...
    def snapshot(self) -> dict[str, RegistryValueDTO]: ...
    def get_metadata(self, key: str) -> Any: ...
    def get_entry(self, key: str) -> RegistryValueDTO | None: ...

class IRestorableRegistry(IGlobalRegistry, Protocol):
    def delete_entry(self, key: str) -> bool: ...
    def restore_entry(self, key: str, entry: RegistryValueDTO) -> bool: ...

class IProtocolEnforcer(Protocol):
    def assert_implements_protocol(self, instance: Any, protocol: Any) -> None: ...

class ISystemAgentRegistry(Protocol):
    def register_system_agent(self, agent: IAgent) -> None: ...
    def get_system_agent(self, agent_id: AgentID) -> IAgent | None: ...

class IAgentRegistry(Protocol):
    def get_agent(self, agent_id: Any) -> Any: ...
    def get_all_financial_agents(self) -> list[Any]: ...
    def set_state(self, state: Any) -> None: ...
    def register(self, agent: Any) -> None: ...
    def get_all_agents(self) -> list[Any]: ...
    def is_agent_active(self, agent_id: int) -> bool: ...

class ICurrencyHolder(Protocol):
    def get_balance(self, currency: CurrencyCode = ...) -> int: ...
    def get_assets_by_currency(self) -> dict[CurrencyCode, int]: ...

class IAssetRecoverySystem(Protocol):
    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None: ...
    def execute_asset_buyout(self, request: AssetBuyoutRequestDTO) -> AssetBuyoutResultDTO: ...
    def receive_liquidated_assets(self, inventory: dict[str, float]) -> None: ...
    def generate_liquidation_orders(self, market_signals: dict[str, MarketSignalDTO], core_config: Any = None, engine: Any = None) -> list[Any]: ...
    def get_deficit(self) -> int: ...

class ISystemFinancialAgent(Protocol):
    def is_system_agent(self) -> bool: ...

@dataclass(frozen=True)
class MigrationReportDTO:
    success: bool
    migrated_tables: list[str]
    rows_affected: int
    errors: list[str]
    timestamp: float
    schema_version: str = ...

class IDatabaseMigrator(Protocol):
    def check_schema_health(self) -> dict[str, bool]: ...
    def migrate(self) -> MigrationReportDTO: ...
