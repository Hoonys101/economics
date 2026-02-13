from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable, TYPE_CHECKING, TypedDict
from dataclasses import dataclass, field
from enum import IntEnum, auto

# Define Currency Code (Usually String "USD")
CurrencyCode = str
DEFAULT_CURRENCY: CurrencyCode = "USD"
AgentID = int

@dataclass
class MarketContextDTO:
    """
    Context object passed to agents for making decisions.
    Contains strictly external market data (prices, rates, signals).
    """
    market_data: Dict[str, Any]
    market_signals: Dict[str, float]
    tick: int

@dataclass(frozen=True)
class MarketSignalDTO:
    market_id: str
    item_id: str
    best_bid: Optional[float]
    best_ask: Optional[float]
    last_traded_price: Optional[float]
    last_trade_tick: int
    price_history_7d: List[float]
    volatility_7d: float
    order_book_depth_buy: int
    order_book_depth_sell: int
    total_bid_quantity: float
    total_ask_quantity: float
    is_frozen: bool

@dataclass(frozen=True)
class HousingMarketUnitDTO:
    unit_id: str
    price: float
    quality: float
    rent_price: Optional[float] = None

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

@dataclass(frozen=True)
class PublicManagerReportDTO:
    tick: int
    newly_recovered_assets: Dict[str, float]
    liquidation_revenue: Dict[str, int]
    managed_inventory_count: float
    system_treasury_balance: Dict[str, int]

class OriginType(IntEnum):
    """
    Priority Level for Parameter Updates.
    Higher value = Higher Priority.
    """
    CONFIG = 0          # Loaded from file
    SYSTEM = 10         # Internal logic (e.g. adaptive systems)
    USER = 50           # Dashboard/UI manual override
    GOD_MODE = 100      # Absolute override (Scenario Injection)

@dataclass
class RegistryEntry:
    value: Any
    origin: OriginType
    is_locked: bool = False
    last_updated_tick: int = 0

class RegistryObserver(Protocol):
    def on_registry_update(self, key: str, value: Any, origin: OriginType) -> None:
        ...

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

    def snapshot(self) -> Dict[str, RegistryEntry]:
        ...

    def get_metadata(self, key: str) -> Any:
        ...

    def get_entry(self, key: str) -> Optional[RegistryEntry]:
        ...

    def delete_entry(self, key: str) -> bool:
        """Deletes an entry completely (for rollback purposes)."""
        ...

    def restore_entry(self, key: str, entry: RegistryEntry) -> None:
        """Restores a full entry state (for rollback purposes)."""
        ...

class IAgentRegistry(Protocol):
    def get_agent(self, agent_id: Any) -> Any:
        ...

    def get_all_financial_agents(self) -> List[Any]:
        ...

    def set_state(self, state: Any) -> None:
        ...

@runtime_checkable
class ICurrencyHolder(Protocol):
    """
    Protocol for agents/systems that hold currency.
    Used for M2 Money Supply calculation.
    """
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
        ...

    def get_assets_by_currency(self) -> Dict[CurrencyCode, float]:
        ...

class IAssetRecoverySystem(Protocol):
    """
    Interface for Public Manager (Asset Recovery / Liquidation).
    """
    def liquidate_assets(self, agent: Any) -> float:
        ...
