from typing import TypedDict, List, Optional, Literal
from abc import ABC, abstractmethod
from modules.household.dtos import HouseholdStateDTO
from modules.system.api import HousingMarketSnapshotDTO

class LoanApplicationDTO(TypedDict):
    """
    Represents a formal loan application to be sent to the LoanMarket.
    """
    applicant_id: int
    principal: float
    purpose: str # e.g., "MORTGAGE"
    property_id: Optional[str] # item_id (e.g., "unit_123")
    offer_price: float

class HousingOfferRequestDTO(TypedDict):
    """
    Input for the HousingPlanner, containing all necessary state for a decision.
    """
    household_state: HouseholdStateDTO
    housing_market_snapshot: HousingMarketSnapshotDTO

class HousingDecisionDTO(TypedDict):
    """
    Output of the HousingPlanner, detailing the agent's next action.
    """
    decision_type: Literal["MAKE_OFFER", "RENT", "STAY", "DO_NOTHING"]
    target_property_id: Optional[str] # item_id (e.g., "unit_123")
    offer_price: Optional[float]
    loan_application: Optional[LoanApplicationDTO]

class IHousingPlanner(ABC):
    """
    Stateless interface for making housing decisions.
    """

    @abstractmethod
    def evaluate_housing_options(self, request: HousingOfferRequestDTO) -> HousingDecisionDTO:
        """
        Analyzes the housing market and the agent's financial state to recommend
        a housing action (buy, rent, or stay).

        Args:
            request: A DTO containing the agent's state and a market snapshot.

        Returns:
            A DTO representing the chosen action, which may include a loan application.
        """
        ...
