from dataclasses import dataclass, field
from modules.household.dtos import BioStateDTO as BioStateDTO, CloningRequestDTO as CloningRequestDTO, EconStateDTO as EconStateDTO, HouseholdSnapshotDTO as HouseholdSnapshotDTO, SocialStateDTO as SocialStateDTO
from modules.simulation.dtos.api import HouseholdConfigDTO as HouseholdConfigDTO
from modules.system.api import MarketSnapshotDTO as MarketSnapshotDTO
from simulation.dtos import ConsumptionResult as ConsumptionResult, LaborResult as LaborResult, LeisureEffectDTO as LeisureEffectDTO, StressScenarioConfig as StressScenarioConfig
from simulation.models import Order as Order
from typing import Any, DefaultDict, Deque, Protocol

@dataclass
class PrioritizedNeed:
    """Represents a single, prioritized need for budget allocation."""
    need_id: str
    urgency: float
    deficit: float
    target_quantity: float = ...

@dataclass
class BudgetPlan:
    """A concrete allocation of funds for the current tick."""
    allocations: dict[str, int]
    discretionary_spending: int
    orders: list[Order] = field(default_factory=list)

@dataclass
class HousingActionDTO:
    """
    Represents an action related to housing (Purchase, Rent).
    Used to decouple side effects from the engine.
    """
    action_type: str
    property_id: str | None = ...
    offer_price: int = ...
    down_payment_amount: int = ...
    buyer_id: int | None = ...

@dataclass
class LifecycleInputDTO:
    bio_state: BioStateDTO
    econ_state: EconStateDTO
    config: HouseholdConfigDTO
    current_tick: int

@dataclass
class NeedsInputDTO:
    bio_state: BioStateDTO
    econ_state: EconStateDTO
    social_state: SocialStateDTO
    config: HouseholdConfigDTO
    current_tick: int
    goods_data: dict[str, Any]
    market_data: dict[str, Any] | None = ...

@dataclass
class SocialInputDTO:
    social_state: SocialStateDTO
    econ_state: EconStateDTO
    bio_state: BioStateDTO
    all_items: dict[str, float]
    config: HouseholdConfigDTO
    current_tick: int
    market_data: dict[str, Any] | None = ...

@dataclass
class BudgetInputDTO:
    econ_state: EconStateDTO
    prioritized_needs: list[PrioritizedNeed]
    abstract_plan: list[Order]
    market_snapshot: MarketSnapshotDTO
    config: HouseholdConfigDTO
    current_tick: int
    agent_id: int | None = ...

@dataclass
class ConsumptionInputDTO:
    econ_state: EconStateDTO
    bio_state: BioStateDTO
    budget_plan: BudgetPlan
    market_snapshot: MarketSnapshotDTO
    config: HouseholdConfigDTO
    current_tick: int
    stress_scenario_config: StressScenarioConfig | None = ...

@dataclass
class BeliefInputDTO:
    current_tick: int
    perceived_prices: dict[str, float]
    expected_inflation: dict[str, float]
    price_history: DefaultDict[str, Deque[float]]
    adaptation_rate: float
    goods_info_map: dict[str, Any]
    config: HouseholdConfigDTO
    market_data: dict[str, Any]
    stress_scenario_config: StressScenarioConfig | None = ...

@dataclass
class PanicSellingInputDTO:
    owner_id: int
    portfolio_holdings: dict[int, Any]
    inventory: dict[str, float]
    market_data: dict[str, Any] | None = ...

@dataclass
class LifecycleOutputDTO:
    bio_state: BioStateDTO
    cloning_requests: list[CloningRequestDTO]
    death_occurred: bool = ...

@dataclass
class NeedsOutputDTO:
    bio_state: BioStateDTO
    prioritized_needs: list[PrioritizedNeed]

@dataclass
class SocialOutputDTO:
    social_state: SocialStateDTO

@dataclass
class BudgetOutputDTO:
    econ_state: EconStateDTO
    budget_plan: BudgetPlan
    housing_action: HousingActionDTO | None = ...

@dataclass
class ConsumptionOutputDTO:
    econ_state: EconStateDTO
    bio_state: BioStateDTO
    orders: list[Order]
    social_state: SocialStateDTO | None = ...

@dataclass
class BeliefResultDTO:
    new_perceived_prices: dict[str, float]
    new_expected_inflation: dict[str, float]

@dataclass
class PanicSellingResultDTO:
    orders: list[Order]

class ILifecycleEngine(Protocol):
    """Manages aging, death, and reproduction."""
    def process_tick(self, input_dto: LifecycleInputDTO) -> LifecycleOutputDTO: ...

class INeedsEngine(Protocol):
    """Calculates need decay, satisfaction, and prioritizes needs."""
    def evaluate_needs(self, input_dto: NeedsInputDTO) -> NeedsOutputDTO: ...

class ISocialEngine(Protocol):
    """Manages social status, discontent, and other social metrics."""
    def update_status(self, input_dto: SocialInputDTO) -> SocialOutputDTO: ...

class IBudgetEngine(Protocol):
    """Allocates financial resources based on needs and strategic goals."""
    def allocate_budget(self, input_dto: BudgetInputDTO) -> BudgetOutputDTO: ...

class IConsumptionEngine(Protocol):
    """Transforms a budget plan into concrete consumption and market orders."""
    def generate_orders(self, input_dto: ConsumptionInputDTO) -> ConsumptionOutputDTO: ...
    def apply_leisure_effect(self, leisure_hours: float, consumed_items: dict[str, float], social_state: SocialStateDTO, econ_state: EconStateDTO, bio_state: BioStateDTO, config: HouseholdConfigDTO) -> tuple[SocialStateDTO, EconStateDTO, LeisureEffectDTO]: ...

class IBeliefEngine(Protocol):
    """Updates agent beliefs about prices and inflation."""
    def update_beliefs(self, input_dto: BeliefInputDTO) -> BeliefResultDTO: ...

class ICrisisEngine(Protocol):
    """Handles emergency situations like panic selling."""
    def evaluate_distress(self, input_dto: PanicSellingInputDTO) -> PanicSellingResultDTO: ...

@dataclass(frozen=True)
class OrchestrationContextDTO:
    market_snapshot: MarketSnapshotDTO
    current_time: int
    config: HouseholdConfigDTO
    household_state: HouseholdSnapshotDTO
    stress_scenario_config: StressScenarioConfig | None = ...
    housing_system: Any | None = ...

class IConsumptionManager(Protocol):
    """
    Stateless manager responsible for consumption logic.
    """
    def consume(self, state: EconStateDTO, needs: dict[str, float], item_id: str, quantity: float, current_time: int, goods_info: dict[str, Any], config: HouseholdConfigDTO) -> tuple[EconStateDTO, dict[str, float], ConsumptionResult]: ...
    def decide_and_consume(self, state: EconStateDTO, needs: dict[str, float], current_time: int, goods_info_map: dict[str, Any], config: HouseholdConfigDTO) -> tuple[EconStateDTO, dict[str, float], dict[str, float]]: ...

class IDecisionUnit(Protocol):
    """
    Stateless unit responsible for coordinating decision making.
    """
    def orchestrate_economic_decisions(self, state: EconStateDTO, context: OrchestrationContextDTO, initial_orders: list[Order]) -> tuple[EconStateDTO, list[Order]]: ...

class IEconComponent(Protocol):
    """
    Stateless component managing economic aspects of the Household.
    """
    def update_wage_dynamics(self, state: EconStateDTO, config: HouseholdConfigDTO, is_employed: bool) -> EconStateDTO: ...
    def work(self, state: EconStateDTO, hours: float, config: HouseholdConfigDTO) -> tuple[EconStateDTO, LaborResult]: ...
    def update_skills(self, state: EconStateDTO, config: HouseholdConfigDTO) -> EconStateDTO: ...
    def update_perceived_prices(self, state: EconStateDTO, market_data: dict[str, Any], goods_info_map: dict[str, Any], stress_scenario_config: StressScenarioConfig | None, config: HouseholdConfigDTO) -> EconStateDTO: ...
    def prepare_clone_state(self, parent_state: EconStateDTO, parent_skills: dict[str, Any], config: HouseholdConfigDTO) -> dict[str, Any]: ...

@dataclass
class HouseholdFactoryContext:
    """DTO to provide all necessary dependencies for household creation."""
    core_config_module: Any
    household_config_dto: HouseholdConfigDTO
    goods_data: list[dict[str, Any]]
    loan_market: Any | None
    ai_training_manager: Any
    settlement_system: Any
    markets: dict[str, Any]
    memory_system: Any | None = ...
    central_bank: Any | None = ...
    demographic_manager: Any | None = ...

class IHouseholdFactory(Protocol):
    """Interface for creating Household agents."""
    def create_newborn(self, parent: Any, new_id: int, initial_assets: int, current_tick: int) -> Any:
        """Creates a new household as a child of an existing one."""
    def create_immigrant(self, new_id: int, current_tick: int, initial_assets: int) -> Any:
        """Creates a new household representing an immigrant."""
    def create_initial_population(self, num_agents: int) -> list[Any]:
        """Creates the initial population of households for the simulation."""
