from typing import TypedDict, List, Optional, Literal
from abc import ABC, abstractmethod

# Import external DTOs
# Note: Adjust imports based on actual file structure
from modules.household.dtos import HouseholdStateDTO
from modules.system.api import HousingMarketSnapshotDTO
from modules.finance.api import MortgageApplicationDTO

class LoanMarketSnapshotDTO(TypedDict):
    """
    Snapshot of the loan market conditions.
    """
    interest_rate: float
    max_ltv: float
    max_dti: float

class HousingOfferRequestDTO(TypedDict):
    """
    Input for the HousingPlanner, containing all necessary state for a decision.
    """
    household_state: HouseholdStateDTO
    housing_market_snapshot: HousingMarketSnapshotDTO
    loan_market_snapshot: LoanMarketSnapshotDTO # To assess credit availability
    applicant_current_debt: float # Total outstanding debt
    applicant_annual_income: float # Estimated annual income

class HousingDecisionDTO(TypedDict):
    """
    Output of the HousingPlanner, detailing the agent's next action.
    This DTO is a command, not a state update.
    """
    decision_type: Literal["MAKE_OFFER", "RENT", "STAY"]
    target_property_id: Optional[int]
    offer_price: Optional[float]
    mortgage_application: Optional[MortgageApplicationDTO]

class HousingBubbleMetricsDTO(TypedDict):
    """
    Data structure for monitoring housing market stability.
    """
    tick: int
    house_price_index: float
    m2_growth_rate: float
    new_mortgage_volume: float
    average_ltv: float
    average_dti: float
    pir: float # Price-to-Income Ratio

# --- Interfaces ---

class IHousingPlanner(ABC):
    """
    Stateless interface for making housing decisions. Extracts orphaned logic
    from the old DecisionUnit.
    """
    @abstractmethod
    def evaluate_housing_options(self, request: HousingOfferRequestDTO) -> HousingDecisionDTO:
        """
        Analyzes the market and agent's finances to recommend a housing action.
        This method MUST NOT mutate state.
        """
        ...

class ILoanMarket(ABC):
    """
    Expanded interface for the LoanMarket to include regulatory checks.
    """
    @abstractmethod
    def evaluate_mortgage_application(self, application: MortgageApplicationDTO) -> bool:
        """
        Performs hard LTV/DTI checks. Returns True if approved, False if rejected.
        """
        ...

    @abstractmethod
    def stage_mortgage(self, application: MortgageApplicationDTO) -> Optional[dict]:
         """
         Stages a mortgage (creates loan record) without disbursing funds.
         Returns LoanInfoDTO (as dict) if successful, None otherwise.
         """
         ...

class IBubbleObservatory(ABC):
    """
    Interface for the new market monitoring system.
    """
    @abstractmethod
    def collect_metrics(self) -> HousingBubbleMetricsDTO:
        """
        Collects and returns key indicators of a housing bubble.
        """
        ...
