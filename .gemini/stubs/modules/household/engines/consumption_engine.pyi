from _typeshed import Incomplete
from modules.household.api import ConsumptionInputDTO as ConsumptionInputDTO, ConsumptionOutputDTO as ConsumptionOutputDTO, IConsumptionEngine as IConsumptionEngine
from modules.household.dtos import BioStateDTO as BioStateDTO, EconStateDTO as EconStateDTO, SocialStateDTO as SocialStateDTO
from modules.simulation.dtos.api import HouseholdConfigDTO as HouseholdConfigDTO
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.dtos import LeisureEffectDTO

logger: Incomplete
DEFAULT_FOOD_PRICE: float
DEFAULT_FOOD_UTILITY: float
PRICE_LIMIT_MULTIPLIER: float

class ConsumptionEngine(IConsumptionEngine):
    """
    Stateless engine responsible for executing consumption from inventory,
    generating market orders based on budget, and handling panic selling.
    Logic migrated from ConsumptionManager and DecisionUnit.
    """
    def generate_orders(self, input_dto: ConsumptionInputDTO) -> ConsumptionOutputDTO: ...
    def apply_leisure_effect(self, leisure_hours: float, consumed_items: dict[str, float], social_state: SocialStateDTO, econ_state: EconStateDTO, bio_state: BioStateDTO, config: HouseholdConfigDTO) -> tuple[SocialStateDTO, EconStateDTO, LeisureEffectDTO]: ...
