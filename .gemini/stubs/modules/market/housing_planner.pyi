from _typeshed import Incomplete
from modules.housing.api import IHousingPlanner as IHousingPlanner
from modules.housing.dtos import HousingDecisionDTO as HousingDecisionDTO, HousingDecisionRequestDTO as HousingDecisionRequestDTO, HousingPurchaseDecisionDTO as HousingPurchaseDecisionDTO, HousingRentalDecisionDTO as HousingRentalDecisionDTO, HousingStayDecisionDTO as HousingStayDecisionDTO
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY

logger: Incomplete

class HousingPlanner(IHousingPlanner):
    """
    Stateless component that contains all business logic for housing decisions.
    Centralizes logic for Buying, Renting, and Staying.
    """
    DEFAULT_DOWN_PAYMENT_PCT: float
    def evaluate_housing_options(self, request: HousingDecisionRequestDTO) -> HousingDecisionDTO: ...
