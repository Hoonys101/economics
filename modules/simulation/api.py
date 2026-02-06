from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, TypedDict, Any, List, Dict, Optional, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from simulation.systems.api import IRegistry
    from modules.finance.api import IBankService
    from simulation.interfaces.market_interface import IMarket
    from modules.housing.api import IHousingService

# --- DTOs ---

class ShockConfigDTO(TypedDict):
    """Configuration for the economic shock."""
    shock_start_tick: int
    shock_end_tick: int
    tfp_multiplier: float  # The factor to multiply the baseline TFP by (e.g., 0.5 for a 50% drop)
    baseline_tfp: float   # The normal TFP value to restore to

@dataclass
class EconomicIndicatorsDTO:
    """
    Snapshot of key market indicators for analysis modules.
    Formerly MarketSnapshotDTO.
    """
    gdp: float
    cpi: float

@dataclass
class SystemStateDTO:
    """
    Internal system flags and states not meant for agent decision-making but essential for observation.
    """
    is_circuit_breaker_active: bool
    bank_total_reserves: float
    bank_total_deposits: float
    fiscal_policy_last_activation_tick: int
    central_bank_base_rate: float

@dataclass(frozen=True)
class HouseholdSnapshotDTO:
    """
    Read-only snapshot of a household's financial state for saga processing.
    Ensures isolation from live agent state during long-running transactions.
    """
    household_id: str
    cash: float
    income: float
    credit_score: float
    existing_debt: float
    assets_value: float

# --- Protocols ---

@runtime_checkable
class IInventoryHandler(Protocol):
    """
    Protocol for strict transactional inventory management.
    Abstracts direct dictionary access to enforce business rules and logging.
    """
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0) -> bool: ...
    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None) -> bool: ...
    def get_quantity(self, item_id: str) -> float: ...
    def get_quality(self, item_id: str) -> float: ...

class IAgent(Protocol):
    id: int
    is_active: bool

class IFirm(IAgent, Protocol):
    productivity_factor: float

class IHousehold(IAgent, Protocol):
    inventory: Dict[str, float]

@runtime_checkable
class ICentralBank(Protocol):
    base_rate: float

@runtime_checkable
class IGovernment(Protocol):
    expenditure_this_tick: float
    revenue_this_tick: float
    total_debt: float

@runtime_checkable
class IEconomicIndicatorTracker(Protocol):
    """Protocol for the EconomicIndicatorTracker to enable smoothed metrics access."""
    def get_smoothed_values(self) -> Dict[str, float]:
        ...

    def get_latest_indicators(self) -> Dict[str, Any]:
        ...

@runtime_checkable
class IAgentRepository(Protocol):
    """Protocol for the AgentRepository to enable demographic queries."""
    def get_birth_counts(self, start_tick: int, end_tick: int, run_id: Any = None) -> int:
        ...

    def get_attrition_counts(self, start_tick: int, end_tick: int, run_id: Any = None) -> Dict[str, int]:
        ...

class IConfig(Protocol):
    STARVATION_THRESHOLD: float

class ISimulationState(Protocol):
    """
    Protocol defining the subset of simulation state required by observers and injectors.
    Decouples analysis modules from the concrete Simulation engine.
    """
    firms: List[IFirm]
    households: List[IHousehold]
    central_bank: ICentralBank
    government: IGovernment
    config_module: IConfig

    # Extended context for Saga Handlers and System Logic
    time: int
    settlement_system: "ISettlementSystem"
    registry: "IRegistry"
    housing_service: "IHousingService"
    agents: Dict[int, IAgent]
    bank: "IBankService"
    markets: Dict[str, "IMarket"]

    def get_economic_indicators(self) -> EconomicIndicatorsDTO:
        """
        Retrieves the current market snapshot containing economic indicators like GDP.
        """
        ...

    def get_system_state(self) -> SystemStateDTO:
        """
        Retrieves internal system state for phenomena analysis.
        """
        ...

class IShockInjector(Protocol):
    """
    An interface for a component that can inject economic shocks into the simulation.
    It directly manipulates simulation parameters at runtime based on its configuration.
    """
    def __init__(self, config: ShockConfigDTO, simulation: ISimulationState) -> None:
        ...

    def apply(self, current_tick: int) -> None:
        """
        Applies the shock if the simulation is within the shock window.
        This method is expected to be called every tick.
        """
        ...
