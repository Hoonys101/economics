from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Callable, Protocol, runtime_checkable, Optional

# --- Exceptions ---
class ProtocolViolationError(Exception):
    """Raised when an agent does not adhere to the expected Protocol."""
    pass

class InvalidIndicatorError(Exception):
    """Raised when a requested indicator key is not available."""
    pass

class AgentNotFoundError(Exception):
    """Raised when a requested agent ID is not found in the repository."""
    pass

# --- DTOs ---

@dataclass(frozen=True)
class MarketSnapshotDTO:
    """
    A pure-data snapshot of the state of all markets at a point in time.
    Distinct from simulation.dtos.api.MarketSnapshotDTO for now.
    """
    timestamp: int
    average_prices: Dict[str, float]
    total_trade_volume: float
    unemployment_rate: float

@dataclass(frozen=True)
class IndicatorSubscriptionDTO:
    """DTO for subscribing to economic indicators."""
    subscriber_id: str
    indicator_keys: List[str]
    callback: Callable[[Dict[str, float]], None]


# --- Protocols ---

@runtime_checkable
class IAgent(Protocol):
    @property
    def id(self) -> int: ... # Using int as AgentID is typically int in this codebase

@runtime_checkable
class IFirm(IAgent, Protocol):
    @property
    def inventory(self) -> dict: ...

    @property
    def capital(self) -> float: ...

    # Added for FirmMapper compatibility (which accesses capital_stock)
    # Using @property ensures isinstance checks for existence at runtime if Python < 3.12
    # (actually Python Protocol checks are limited for properties, but it's better semantics)
    @property
    def capital_stock(self) -> float: ...

    def get_all_items(self) -> Dict[str, int]: ...

@runtime_checkable
class IHousehold(IAgent, Protocol):
    @property
    def wealth(self) -> float: ...

    @property
    def skills(self) -> dict: ...

@runtime_checkable
class ISimulationRepository(Protocol):
    """
    Interface for retrieving agents from the simulation kernel.
    """
    def get_agent(self, agent_id: int) -> IAgent: ...
    def get_all_firms(self) -> List[IFirm]: ...
    def get_all_households(self) -> List[IHousehold]: ...

@runtime_checkable
class IMetricsProvider(Protocol):
    """
    Interface for retrieving global economic indicators.
    Enables ISP (Interface Segregation Principle).
    """
    def get_economic_indicators(self) -> Any: ... # Returns Kernel DTO (EconomicIndicatorsDTO)

@runtime_checkable
class IEventBroker(Protocol):
    """
    Interface for a simple event broker to handle subscriptions.
    """
    def subscribe(self, topic: str, callback: Callable[[Any], None]) -> None: ...
    def publish(self, topic: str, payload: Any) -> None: ...

@runtime_checkable
class IPublicSimulationService(Protocol):
    """
    Public API Service Protocol.
    """
    def subscribe_to_indicators(self, request: IndicatorSubscriptionDTO) -> bool: ...
    def query_indicators(self, keys: List[str]) -> Dict[str, float]: ...
