from __future__ import annotations
from typing import Protocol, List, Dict, Optional, Any, TypedDict
from dataclasses import dataclass, field

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
from simulation.dtos import StressScenarioConfig

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
    allocations: Dict[str, float]  # e.g., {"food": 100, "housing": 500, "savings": 50}
    discretionary_spending: float
    orders: List[Order] = field(default_factory=list) # Orders approved by budget

@dataclass
class HousingActionDTO:
    """
    Represents an action related to housing (Purchase, Rent).
    Used to decouple side effects from the engine.
    """
    action_type: str  # "INITIATE_PURCHASE", "MAKE_RENTAL_OFFER", "STAY"
    property_id: Optional[str] = None
    offer_price: float = 0.0
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

# --- Engine Output DTOs ---

@dataclass
class LifecycleOutputDTO:
    bio_state: BioStateDTO
    cloning_requests: List[CloningRequestDTO]

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

# --- Stateless Engine Interfaces (Protocols) ---

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

# --- Deprecated / Legacy Support ---
# OrchestrationContextDTO is kept if needed for transition, but Engines use specific inputs.
class OrchestrationContextDTO(TypedDict):
    market_snapshot: MarketSnapshotDTO
    current_time: int
    stress_scenario_config: Optional[StressScenarioConfig]
    config: HouseholdConfigDTO
    household_state: HouseholdSnapshotDTO
    housing_system: Optional[Any]
