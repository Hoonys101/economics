import logging
from _typeshed import Incomplete
from dataclasses import dataclass, field
from enum import Enum
from modules.finance.api import IBankService as IBankService
from modules.finance.kernel.api import IMonetaryLedger as IMonetaryLedger
from modules.housing.api import IHousingService as IHousingService
from modules.memory.api import MemoryV2Interface as MemoryV2Interface
from modules.system.api import CurrencyCode as CurrencyCode
from simulation.finance.api import ISettlementSystem as ISettlementSystem
from simulation.interfaces.market_interface import IMarket as IMarket
from simulation.systems.api import IRegistry as IRegistry
from typing import Any, Protocol, TypedDict

class LifecycleState(Enum):
    """Module C: Standardized agent lifecycle states."""
    CREATED = ...
    REGISTERED = ...
    ACTIVE = ...
    LIQUIDATING = ...
    DELETED = ...

class ILifecycleRegistry(Protocol):
    """Module C: Registry protocol for atomic state transitions."""
    def transition_agent(self, agent_id: AgentID, next_state: LifecycleState) -> bool:
        """Atomically transitions an agent to a new state."""
    def get_state(self, agent_id: AgentID) -> LifecycleState:
        """Retrieves the current lifecycle state of an agent."""

AgentID: Incomplete
SpecialAgentRole: Incomplete
AnyAgentID = AgentID | SpecialAgentRole

@dataclass
class AgentCoreConfigDTO:
    """Defines the immutable, core properties of an agent."""
    id: AgentID
    value_orientation: str
    initial_needs: dict[str, float]
    name: str
    logger: logging.Logger
    memory_interface: MemoryV2Interface | None

@dataclass
class ItemDTO:
    name: str
    quantity: float
    quality: float = ...

@dataclass
class InventorySlotDTO:
    items: list[ItemDTO] = field(default_factory=list)

@dataclass
class AgentStateDTO:
    """A snapshot of an agent's mutable state."""
    assets: dict[CurrencyCode, float]
    is_active: bool
    inventories: dict[str, InventorySlotDTO] = field(default_factory=dict)
    inventory: dict[str, float] | None = ...

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
    tfp_multiplier: float
    baseline_tfp: float

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
    initial_prices: dict[str, float]
    default_price: float
    market_prices: dict[str, float]

class IConfigurable(Protocol):
    """Protocol for agents that expose a configuration DTO for liquidation."""
    def get_liquidation_config(self) -> LiquidationConfigDTO: ...

class ISensoryDataProvider(Protocol):
    """
    Protocol for agents to expose their state safely to observer systems.
    """
    def get_sensory_snapshot(self) -> AgentSensorySnapshotDTO: ...

class InventorySlot(Enum):
    """Defines distinct inventory categories within an agent."""
    MAIN = ...
    INPUT = ...

class IInventoryHandler(Protocol):
    """
    Protocol for strict transactional inventory management.
    Abstracts direct dictionary access to enforce business rules and logging.
    """
    def add_item(self, item_id: str, quantity: float, transaction_id: str | None = None, quality: float = 1.0, slot: InventorySlot = ...) -> bool: ...
    def remove_item(self, item_id: str, quantity: float, transaction_id: str | None = None, slot: InventorySlot = ...) -> bool: ...
    def get_quantity(self, item_id: str, slot: InventorySlot = ...) -> float: ...
    def get_quality(self, item_id: str, slot: InventorySlot = ...) -> float: ...
    def get_all_items(self, slot: InventorySlot = ...) -> dict[str, float]: ...
    def clear_inventory(self, slot: InventorySlot = ...) -> None: ...

class IDecisionEngine(Protocol):
    """Interface for the 'brain' of an agent."""
    def make_decision(self, state: AgentStateDTO, world_context: Any) -> DecisionDTO | Any: ...

class IAgent(Protocol):
    id: AgentID
    is_active: bool

class IOrchestratorAgent(IAgent, Protocol):
    """Public interface for an agent 'Orchestrator' supporting 2-stage initialization."""
    def get_core_config(self) -> AgentCoreConfigDTO: ...
    def get_current_state(self) -> AgentStateDTO: ...
    def load_state(self, state: AgentStateDTO) -> None: ...
    def update_needs(self, current_tick: int) -> None: ...
    def make_decision(self, input_dto: Any) -> Any: ...

class IFirm(IAgent, Protocol):
    productivity_factor: float
    def reset(self) -> None: ...

class IHousehold(IAgent, Protocol):
    inventory: dict[str, float]
    def reset_tick_state(self) -> None: ...

class IEducated(Protocol):
    """
    Protocol for agents that possess education experience/level.
    """
    @property
    def education_xp(self) -> float:
        """The agent's education experience points."""
    @education_xp.setter
    def education_xp(self, value: float) -> None:
        """Sets the agent's education experience points."""

class ITalented(Protocol):
    """Protocol for agents that possess natural talent."""
    @property
    def talent(self) -> Any: ...

class ICentralBank(Protocol):
    base_rate: float

class IGovernment(Protocol):
    expenditure_this_tick: float
    revenue_this_tick: float
    total_debt: float

class IEconomicIndicatorTracker(Protocol):
    """Protocol for the EconomicIndicatorTracker to enable smoothed metrics access."""
    def get_smoothed_values(self) -> dict[str, float]: ...
    def get_latest_indicators(self) -> dict[str, Any]: ...

class IAgentRepository(Protocol):
    """Protocol for the AgentRepository to enable demographic queries."""
    def get_birth_counts(self, start_tick: int, end_tick: int, run_id: Any = None) -> int: ...
    def get_attrition_counts(self, start_tick: int, end_tick: int, run_id: Any = None) -> dict[str, int]: ...

class ShareholderData(TypedDict):
    agent_id: AgentID
    firm_id: AgentID
    quantity: float

class IShareholderRegistry(Protocol):
    """Single source of truth for stock ownership."""
    def register_shares(self, firm_id: AgentID, agent_id: AgentID, quantity: float) -> None:
        """Adds/removes shares. Zero quantity removes the registry entry."""
    def get_shareholders_of_firm(self, firm_id: AgentID) -> list[ShareholderData]:
        """Returns list of owners for a firm."""
    def get_total_shares(self, firm_id: AgentID) -> float:
        """Returns total outstanding shares."""

class IConfig(Protocol):
    STARVATION_THRESHOLD: float

class ISimulationState(Protocol):
    """
    Protocol defining the subset of simulation state required by observers and injectors.
    Decouples analysis modules from the concrete Simulation engine.
    """
    firms: list[IFirm]
    households: list[IHousehold]
    central_bank: ICentralBank
    government: IGovernment
    config_module: IConfig
    time: int
    settlement_system: ISettlementSystem
    registry: IRegistry
    housing_service: IHousingService
    agents: dict[AgentID, IAgent]
    bank: IBankService
    markets: dict[str, 'IMarket']
    monetary_ledger: IMonetaryLedger | None
    def get_economic_indicators(self) -> EconomicIndicatorsDTO:
        """
        Retrieves the current market snapshot containing economic indicators like GDP.
        """
    def get_system_state(self) -> SystemStateDTO:
        """
        Retrieves internal system state for phenomena analysis.
        """

class IShockInjector(Protocol):
    """
    An interface for a component that can inject economic shocks into the simulation.
    It directly manipulates simulation parameters at runtime based on its configuration.
    """
    def __init__(self, config: ShockConfigDTO, simulation: ISimulationState) -> None: ...
    def apply(self, current_tick: int) -> None:
        """
        Applies the shock if the simulation is within the shock window.
        This method is expected to be called every tick.
        """

@dataclass
class HouseholdFactoryContext:
    core_config_module: Any
    household_config_dto: Any
    goods_data: list[Any]
    loan_market: Any
    ai_training_manager: Any
    settlement_system: Any
    markets: dict[str, Any]
    memory_system: Any
    central_bank: Any

class IHouseholdFactory(Protocol):
    def create_newborn(self, parent: Any, simulation: Any, child_id: int) -> Any: ...
