from __future__ import annotations
from typing import Protocol, List, Dict, Optional, Any, TypedDict, Tuple, Deque, DefaultDict, runtime_checkable
from dataclasses import dataclass, field
from collections import deque

from simulation.models import Order
from modules.household.dtos import (
    BioStateDTO,
    EconStateDTO,
    SocialStateDTO,
    CloningRequestDTO,
    HouseholdSnapshotDTO
)
from simulation.dtos.config_dtos import HouseholdConfigDTO
from modules.system.api import MarketSnapshotDTO
from simulation.dtos import StressScenarioConfig, LaborResult, ConsumptionResult

# --- Engine DTOs ---

@dataclass
class PrioritizedNeed:
    """Represents a single, prioritized need for budget allocation."""
    need_id: str
    urgency: float  # A score from 0.0 to 1.0+ indicating importance
    deficit: float  # How much is needed to reach satisfaction
    target_quantity: float = 0.0

@dataclass
class BudgetPlan:
    """A concrete allocation of funds for the current tick."""
    allocations: Dict[str, int]  # MIGRATION: int pennies. e.g., {"food": 10000}
    discretionary_spending: int # MIGRATION: int pennies.
    orders: List[Order] = field(default_factory=list) # Orders approved by budget

@dataclass
class HousingActionDTO:
    """
    Represents an action related to housing (Purchase, Rent).
    Used to decouple side effects from the engine.
    """
    action_type: str  # "INITIATE_PURCHASE", "MAKE_RENTAL_OFFER", "STAY"
    property_id: Optional[str] = None
    offer_price: int = 0
    down_payment_amount: int = 0
    buyer_id: Optional[int] = None

# --- Engine Input DTOs ---

@dataclass
class LifecycleInputDTO:
    bio_state: BioStateDTO
    econ_state: EconStateDTO # Needed for reproduction viability checks
    config: HouseholdConfigDTO
    current_tick: int

@dataclass
class NeedsInputDTO:
    bio_state: BioStateDTO
    econ_state: EconStateDTO
    social_state: SocialStateDTO
    config: HouseholdConfigDTO
    current_tick: int
    goods_data: Dict[str, Any] # Added for durable asset utility
    market_data: Optional[Dict[str, Any]] = None

@dataclass
class SocialInputDTO:
    social_state: SocialStateDTO
    econ_state: EconStateDTO
    bio_state: BioStateDTO # For children count in leisure
    all_items: Dict[str, float]
    config: HouseholdConfigDTO
    current_tick: int
    market_data: Optional[Dict[str, Any]] = None # Added for political update

@dataclass
class BudgetInputDTO:
    econ_state: EconStateDTO
    prioritized_needs: List[PrioritizedNeed]
    abstract_plan: List[Order]  # The AI's initial, abstract order intentions
    market_snapshot: MarketSnapshotDTO # For housing prices/rent
    config: HouseholdConfigDTO
    current_tick: int

@dataclass
class ConsumptionInputDTO:
    econ_state: EconStateDTO
    bio_state: BioStateDTO # To know current needs
    budget_plan: BudgetPlan
    market_snapshot: MarketSnapshotDTO
    config: HouseholdConfigDTO
    current_tick: int
    stress_scenario_config: Optional[StressScenarioConfig] = None # For panic selling

@dataclass
class BeliefInputDTO:
    current_tick: int
    perceived_prices: Dict[str, float]
    expected_inflation: Dict[str, float]
    price_history: DefaultDict[str, Deque[float]]
    adaptation_rate: float
    goods_info_map: Dict[str, Any]
    config: HouseholdConfigDTO
    market_data: Dict[str, Any]
    stress_scenario_config: Optional[StressScenarioConfig] = None

@dataclass
class PanicSellingInputDTO:
    owner_id: int
    portfolio_holdings: Dict[int, Any] # Using Any for Share to avoid circular imports if needed, but imported Share from models in core_agents. Here we can use Any or Import Share locally/globally.
    inventory: Dict[str, float]
    market_data: Optional[Dict[str, Any]] = None

# --- Engine Output DTOs ---

@dataclass
class LifecycleOutputDTO:
    bio_state: BioStateDTO
    cloning_requests: List[CloningRequestDTO]
    death_occurred: bool = False

@dataclass
class NeedsOutputDTO:
    bio_state: BioStateDTO  # Needs decay might affect bio state
    prioritized_needs: List[PrioritizedNeed]

@dataclass
class SocialOutputDTO:
    social_state: SocialStateDTO

@dataclass
class BudgetOutputDTO:
    econ_state: EconStateDTO # May be updated with savings goals, housing mode, etc.
    budget_plan: BudgetPlan
    housing_action: Optional[HousingActionDTO] = None

@dataclass
class ConsumptionOutputDTO:
    econ_state: EconStateDTO # Updated inventory and balances (conceptually)
    bio_state: BioStateDTO # Updated needs after consumption
    orders: List[Order] # The final, concrete orders to be placed
    social_state: Optional[SocialStateDTO] = None # Updated if leisure consumption affects social state

@dataclass
class BeliefResultDTO:
    new_perceived_prices: Dict[str, float]
    new_expected_inflation: Dict[str, float]
    # Price history is mutable (deque), but we return reference or updated structure.
    # Ideally we wouldn't return deque if we want strict DTO, but for efficiency we keep it.

@dataclass
class PanicSellingResultDTO:
    orders: List[Order]

# --- Stateless Engine Interfaces (Protocols) ---

@runtime_checkable
class ILifecycleEngine(Protocol):
    """Manages aging, death, and reproduction."""
    def process_tick(self, input_dto: LifecycleInputDTO) -> LifecycleOutputDTO: ...

@runtime_checkable
class INeedsEngine(Protocol):
    """Calculates need decay, satisfaction, and prioritizes needs."""
    def evaluate_needs(self, input_dto: NeedsInputDTO) -> NeedsOutputDTO: ...

@runtime_checkable
class ISocialEngine(Protocol):
    """Manages social status, discontent, and other social metrics."""
    def update_status(self, input_dto: SocialInputDTO) -> SocialOutputDTO: ...

@runtime_checkable
class IBudgetEngine(Protocol):
    """Allocates financial resources based on needs and strategic goals."""
    def allocate_budget(self, input_dto: BudgetInputDTO) -> BudgetOutputDTO: ...

@runtime_checkable
class IConsumptionEngine(Protocol):
    """Transforms a budget plan into concrete consumption and market orders."""
    def generate_orders(self, input_dto: ConsumptionInputDTO) -> ConsumptionOutputDTO: ...

    def apply_leisure_effect(
        self,
        leisure_hours: float,
        consumed_items: Dict[str, float],
        social_state: SocialStateDTO,
        econ_state: EconStateDTO,
        bio_state: BioStateDTO,
        config: HouseholdConfigDTO
    ) -> Tuple[SocialStateDTO, EconStateDTO, LeisureEffectDTO]: ...

@runtime_checkable
class IBeliefEngine(Protocol):
    """Updates agent beliefs about prices and inflation."""
    def update_beliefs(self, input_dto: BeliefInputDTO) -> BeliefResultDTO: ...

@runtime_checkable
class ICrisisEngine(Protocol):
    """Handles emergency situations like panic selling."""
    def evaluate_distress(self, input_dto: PanicSellingInputDTO) -> PanicSellingResultDTO: ...

# --- Deprecated / Legacy Support ---
# OrchestrationContextDTO is kept if needed for transition, but Engines use specific inputs.
class OrchestrationContextDTO(TypedDict):
    market_snapshot: MarketSnapshotDTO
    current_time: int
    stress_scenario_config: Optional[StressScenarioConfig]
    config: HouseholdConfigDTO
    household_state: HouseholdSnapshotDTO
    housing_system: Optional[Any]

class IConsumptionManager(Protocol):
    """
    Stateless manager responsible for consumption logic.
    """
    def consume(
        self,
        state: EconStateDTO,
        needs: Dict[str, float],
        item_id: str,
        quantity: float,
        current_time: int,
        goods_info: Dict[str, Any],
        config: HouseholdConfigDTO
    ) -> Tuple[EconStateDTO, Dict[str, float], ConsumptionResult]: ...

    def decide_and_consume(
        self,
        state: EconStateDTO,
        needs: Dict[str, float],
        current_time: int,
        goods_info_map: Dict[str, Any],
        config: HouseholdConfigDTO
    ) -> Tuple[EconStateDTO, Dict[str, float], Dict[str, float]]: ...

class IDecisionUnit(Protocol):
    """
    Stateless unit responsible for coordinating decision making.
    """
    def orchestrate_economic_decisions(
        self,
        state: EconStateDTO,
        context: OrchestrationContextDTO,
        initial_orders: List[Order]
    ) -> Tuple[EconStateDTO, List[Order]]: ...

class IEconComponent(Protocol):
    """
    Stateless component managing economic aspects of the Household.
    """
    def update_wage_dynamics(self, state: EconStateDTO, config: HouseholdConfigDTO, is_employed: bool) -> EconStateDTO: ...
    def work(self, state: EconStateDTO, hours: float, config: HouseholdConfigDTO) -> Tuple[EconStateDTO, LaborResult]: ...
    def update_skills(self, state: EconStateDTO, config: HouseholdConfigDTO) -> EconStateDTO: ...
    def update_perceived_prices(
        self,
        state: EconStateDTO,
        market_data: Dict[str, Any],
        goods_info_map: Dict[str, Any],
        stress_scenario_config: Optional[StressScenarioConfig],
        config: HouseholdConfigDTO
    ) -> EconStateDTO: ...
    def prepare_clone_state(
        self,
        parent_state: EconStateDTO,
        parent_skills: Dict[str, Any],
        config: HouseholdConfigDTO
    ) -> Dict[str, Any]: ...


# --- Household Factory Interfaces ---

@dataclass
class HouseholdFactoryContext:
    """DTO to provide all necessary dependencies for household creation."""
    # Configs
    core_config_module: Any
    household_config_dto: HouseholdConfigDTO
    goods_data: List[Dict[str, Any]]
    # Systems & Global State
    loan_market: Optional[Any] # Avoiding circular import with LoanMarket
    # Required for AI engine instantiation
    ai_training_manager: Any
    # Required for dependency injection post-creation
    settlement_system: Any
    markets: Dict[str, Any]
    memory_system: Optional[Any] = None
    central_bank: Optional[Any] = None
    demographic_manager: Optional[Any] = None


class IHouseholdFactory(Protocol):
    """Interface for creating Household agents."""

    def create_newborn(
        self,
        parent: Any, # Household
        new_id: int,
        initial_assets: int,
        current_tick: int
    ) -> Any: # Household
        """Creates a new household as a child of an existing one."""
        ...

    def create_immigrant(
        self,
        new_id: int,
        current_tick: int,
        initial_assets: int
    ) -> Any: # Household
        """Creates a new household representing an immigrant."""
        ...

    def create_initial_population(
        self,
        num_agents: int
    ) -> List[Any]: # List[Household]
        """Creates the initial population of households for the simulation."""
        ...
