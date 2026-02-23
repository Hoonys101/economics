import abc
from abc import ABC, abstractmethod
from dataclasses import dataclass
from modules.finance.api import MortgageApplicationDTO as MortgageApplicationDTO
from modules.finance.sagas.housing_api import MortgageApprovalDTO as MortgageApprovalDTO
from modules.household.dtos import HouseholdSnapshotDTO as HouseholdSnapshotDTO
from modules.system.api import HousingMarketSnapshotDTO as HousingMarketSnapshotDTO, LoanMarketSnapshotDTO as LoanMarketSnapshotDTO
from typing import Literal

@dataclass(frozen=True)
class HousingDecisionRequestDTO:
    """
    Input for the HousingPlanner, containing all necessary state for a decision.
    """
    household_state: HouseholdSnapshotDTO
    housing_market_snapshot: HousingMarketSnapshotDTO
    loan_market_snapshot: LoanMarketSnapshotDTO
    applicant_current_debt: float
    applicant_annual_income: float

@dataclass(frozen=True)
class HousingDecisionDTO:
    """
    Output of the HousingPlanner, detailing the agent's next action.
    This DTO is a command, not a state update.
    """
    decision_type: Literal['MAKE_OFFER', 'RENT', 'STAY']
    target_property_id: int | None
    offer_price: float | None
    mortgage_application: MortgageApplicationDTO | None

@dataclass(frozen=True)
class HousingBubbleMetricsDTO:
    """
    Data structure for monitoring housing market stability.
    """
    tick: int
    house_price_index: float
    m2_growth_rate: float
    new_mortgage_volume: float
    average_ltv: float
    average_dti: float
    pir: float

class IHousingPlanner(ABC, metaclass=abc.ABCMeta):
    """
    Stateless interface for making housing decisions. Extracts orphaned logic
    from the old DecisionUnit.
    """
    @abstractmethod
    def evaluate_housing_options(self, request: HousingDecisionRequestDTO) -> HousingDecisionDTO:
        """
        Analyzes the market and agent's finances to recommend a housing action.
        This method MUST NOT mutate state.
        """

class ILoanMarket(ABC, metaclass=abc.ABCMeta):
    """
    Expanded interface for the LoanMarket to include regulatory checks.
    """
    @abstractmethod
    def evaluate_mortgage_application(self, application: MortgageApplicationDTO) -> bool:
        """
        Performs hard LTV/DTI checks. Returns True if approved, False if rejected.
        """
    @abstractmethod
    def stage_mortgage_application(self, application: MortgageApplicationDTO) -> str | None:
        """
         Submits an application for asynchronous credit check.
         Returns a unique `staged_loan_id` for tracking, or None if invalid.
         """
    @abstractmethod
    def stage_mortgage(self, application: MortgageApplicationDTO) -> dict | None:
        """
         Stages a mortgage (creates loan record) without disbursing funds.
         Returns LoanInfoDTO (as dict) if successful, None otherwise.
         """
    @abstractmethod
    def check_staged_application_status(self, staged_loan_id: str) -> Literal['PENDING', 'APPROVED', 'REJECTED']:
        """Checks the status of a pending mortgage application."""
    @abstractmethod
    def convert_staged_to_loan(self, staged_loan_id: str) -> dict | None:
        """
        Finalizes an approved application, creating an official loan.
        Returns the final loan details (LoanInfoDTO dict) or None on failure.
        """
    @abstractmethod
    def void_staged_application(self, staged_loan_id: str) -> bool:
        """Cancels a pending or approved application before funds are disbursed."""

class IBubbleObservatory(ABC, metaclass=abc.ABCMeta):
    """
    Interface for the new market monitoring system.
    """
    @abstractmethod
    def collect_metrics(self) -> HousingBubbleMetricsDTO:
        """
        Collects and returns key indicators of a housing bubble.
        """
