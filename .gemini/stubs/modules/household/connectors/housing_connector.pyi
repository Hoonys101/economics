from _typeshed import Incomplete
from modules.household.api import HousingActionDTO as HousingActionDTO
from typing import Any, Protocol

logger: Incomplete

class IHousingSystem(Protocol):
    def initiate_purchase(self, decision: dict[str, Any], buyer_id: int) -> None: ...

class HousingConnector:
    """
    Connects Household Agent to the Housing System.
    Abstracts the details of system interaction.
    """
    def execute_action(self, action: HousingActionDTO, housing_system: Any, buyer_id: int) -> None:
        """
        Executes a housing action by calling the appropriate method on the housing system.
        Moved from Household._execute_housing_action.
        """
