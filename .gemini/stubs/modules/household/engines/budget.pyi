from _typeshed import Incomplete
from decimal import Decimal as Decimal
from modules.finance.utils.currency_math import round_to_pennies as round_to_pennies
from modules.household.api import BudgetInputDTO as BudgetInputDTO, BudgetOutputDTO as BudgetOutputDTO, BudgetPlan as BudgetPlan, HousingActionDTO as HousingActionDTO, IBudgetEngine as IBudgetEngine, PrioritizedNeed as PrioritizedNeed
from modules.household.dtos import EconStateDTO as EconStateDTO, HouseholdSnapshotDTO as HouseholdSnapshotDTO
from modules.housing.dtos import HousingDecisionRequestDTO as HousingDecisionRequestDTO
from modules.market.housing_planner import HousingPlanner as HousingPlanner
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY

logger: Incomplete
SHADOW_WAGE_DECAY: float
SHADOW_WAGE_TARGET_WEIGHT: float
SHADOW_WAGE_UNEMPLOYED_DECAY: float
DESPERATION_THRESHOLD_TICKS: int
DESPERATION_WAGE_DECAY: float
HOUSING_CHECK_FREQUENCY: int
DEFAULT_FOOD_PRICE_ESTIMATE: float
DEFAULT_SURVIVAL_BUDGET_PENNIES: int
MARKET_ID_GOODS: str

class BudgetEngine(IBudgetEngine):
    """
    Stateless engine managing financial planning, budgeting, and housing decisions.
    Logic migrated from DecisionUnit and EconComponent.
    MIGRATION: Uses integer pennies for budget allocation.
    """
    housing_planner: Incomplete
    def __init__(self) -> None: ...
    def allocate_budget(self, input_dto: BudgetInputDTO) -> BudgetOutputDTO: ...
