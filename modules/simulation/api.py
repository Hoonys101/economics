from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, TypedDict, Any, List, Dict, Optional, TYPE_CHECKING, runtime_checkable, NewType, Literal, Union
from enum import Enum, auto

class LifecycleState(Enum):
    """Module C: Standardized agent lifecycle states."""
    CREATED = auto()
    REGISTERED = auto()
    ACTIVE = auto()
    LIQUIDATING = auto()
    DELETED = auto()

@runtime_checkable
class ILifecycleRegistry(Protocol):
    """Module C: Registry protocol for atomic state transitions."""
    def transition_agent(self, agent_id: AgentID, next_state: LifecycleState) -> bool:
        """Atomically transitions an agent to a new state."""
        ...

    def get_state(self, agent_id: AgentID) -> LifecycleState:
        """Retrieves the current lifecycle state of an agent."""
        ...

import logging

# --- Unified Agent Identifier ---
AgentID = NewType('AgentID', int)
SpecialAgentRole = Literal["GOVERNMENT", "CENTRAL_BANK", "BANK"]
AnyAgentID = Union[AgentID, SpecialAgentRole]

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from simulation.systems.api import IRegistry
    from modules.finance.api import IBankService
    from simulation.interfaces.market_interface import IMarket
    from modules.housing.api import IHousingService
    from modules.memory.api import MemoryV2Interface
    from modules.system.api import CurrencyCode

# --- DTOs ---

@dataclass
class AgentCoreConfigDTO:
    """Defines the immutable, core properties of an agent."""
    id: AgentID
    value_orientation: str
    initial_needs: Dict[str, float]
    name: str
    logger: logging.Logger
    memory_interface: Optional["MemoryV2Interface"]

@dataclass
class ItemDTO:
    name: str
    quantity: float
    quality: float = 1.0

@dataclass
class InventorySlotDTO:
    items: List[ItemDTO] = field(default_factory=list)

@dataclass
class AgentStateDTO:
    """A snapshot of an agent's mutable state."""
    assets: Dict[CurrencyCode, float]
    is_active: bool
    inventories: Dict[str, InventorySlotDTO] = field(default_factory=dict)
    inventory: Optional[Dict[str, float]] = None # Deprecated

class AgentSensorySnapshotDTO(TypedDict):
    """
    A stable, read-only view of an agent's state for observation.
    """
    is_active: bool
    approval_rating: float
    total_wealth: float

@dataclass
class DecisionDTO:
    """(Placeholder) Represents a decision made by an engine."""
    actions: list[Any]

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

@dataclass
class LiquidationConfigDTO:
    """Config for liquidation logic."""
    haircut: float
    initial_prices: Dict[str, float]
    default_price: float
    market_prices: Dict[str, float]

# --- Protocols ---

@runtime_checkable
class IConfigurable(Protocol):
    """Protocol for agents that expose a configuration DTO for liquidation."""
    def get_liquidation_config(self) -> LiquidationConfigDTO:
        ...

@runtime_checkable
class ISensoryDataProvider(Protocol):
    """
    Protocol for agents to expose their state safely to observer systems.
    """
    def get_sensory_snapshot(self) -> AgentSensorySnapshotDTO:
        ...

class InventorySlot(Enum):
    """Defines distinct inventory categories within an agent."""
    MAIN = auto()      # Primary product inventory for sale
    INPUT = auto()     # Raw material inventory for production

@runtime_checkable
class IInventoryHandler(Protocol):
    """
    Protocol for strict transactional inventory management.
    Abstracts direct dictionary access to enforce business rules and logging.
    """
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0, slot: InventorySlot = InventorySlot.MAIN) -> bool: ...
    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, slot: InventorySlot = InventorySlot.MAIN) -> bool: ...
    def get_quantity(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float: ...
    def get_quality(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float: ...
    def get_all_items(self, slot: InventorySlot = InventorySlot.MAIN) -> Dict[str, float]: ...
    def clear_inventory(self, slot: InventorySlot = InventorySlot.MAIN) -> None: ...

class IDecisionEngine(Protocol):
    """Interface for the 'brain' of an agent."""
    def make_decision(self, state: AgentStateDTO, world_context: Any) -> DecisionDTO | Any: ...

@runtime_checkable
class IAgent(Protocol):
    id: AgentID
    is_active: bool

@runtime_checkable
class IOrchestratorAgent(IAgent, Protocol):
    """Public interface for an agent 'Orchestrator' supporting 2-stage initialization."""
    def get_core_config(self) -> AgentCoreConfigDTO: ...
    def get_current_state(self) -> AgentStateDTO: ...
    def load_state(self, state: AgentStateDTO) -> None: ...
    def update_needs(self, current_tick: int) -> None: ...
    def make_decision(self, input_dto: Any) -> Any: ...

class IFirm(IAgent, Protocol):
    productivity_factor: float

class IHousehold(IAgent, Protocol):
    inventory: Dict[str, float]

@runtime_checkable
class IEducated(Protocol):
    """
    Protocol for agents that possess education experience/level.
    """
    @property
    def education_xp(self) -> float:
        """The agent's education experience points."""
        ...

    @education_xp.setter
    def education_xp(self, value: float) -> None:
        """Sets the agent's education experience points."""
        ...

@runtime_checkable
class ITalented(Protocol):
    """Protocol for agents that possess natural talent."""
    @property
    def talent(self) -> Any:
        ...

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

class ShareholderData(TypedDict):
    agent_id: AgentID
    firm_id: AgentID
    quantity: float

@runtime_checkable
class IShareholderRegistry(Protocol):
    """Single source of truth for stock ownership."""
    def register_shares(self, firm_id: AgentID, agent_id: AgentID, quantity: float) -> None:
        """Adds/removes shares. Zero quantity removes the registry entry."""
        ...
    def get_shareholders_of_firm(self, firm_id: AgentID) -> List[ShareholderData]:
        """Returns list of owners for a firm."""
        ...
    def get_total_shares(self, firm_id: AgentID) -> float:
        """Returns total outstanding shares."""
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
    agents: Dict[AgentID, IAgent]
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

@dataclass
class HouseholdFactoryContext:
    core_config_module: Any
    household_config_dto: Any
    goods_data: List[Any]
    loan_market: Any
    ai_training_manager: Any
    settlement_system: Any
    markets: Dict[str, Any]
    memory_system: Any
    central_bank: Any

@runtime_checkable
class IHouseholdFactory(Protocol):
    def create_newborn(self, parent: Any, simulation: Any, child_id: int) -> Any:
        ...
