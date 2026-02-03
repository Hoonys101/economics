from typing import TypedDict, List, Optional, Literal, Union, Dict, Any
from abc import ABC, abstractmethod
from modules.household.dtos import HouseholdStateDTO
from modules.system.api import HousingMarketSnapshotDTO
from modules.finance.api import LoanInfoDTO as LoanDTO
from modules.market.housing_planner_api import MortgageApplicationDTO
from modules.market.loan_api import MortgageApplicationRequestDTO

# Pre-existing DTOs (Aliases if needed, or imported elsewhere)
# from modules.market.housing_planner_api import HousingOfferRequestDTO, HousingDecisionDTO

class HousingPurchaseSagaDataDTO(TypedDict):
    """
    The data payload for the housing purchase saga.
    Carries all necessary information through the saga steps.
    """
    household_id: int
    property_id: int
    offer_price: float
    down_payment: float
    mortgage_application: MortgageApplicationRequestDTO
    # This will be populated once the loan is approved
    approved_loan_id: Optional[int]
    seller_id: int

class HousingPurchaseSagaDTO(TypedDict):
    """
    The stateful object representing a single housing purchase transaction.
    This will be managed by the SettlementSystem.
    """
    saga_id: str
    saga_type: Literal["HOUSING_PURCHASE"]
    status: Literal[
        "STARTED",
        "LOAN_APPLICATION_PENDING",
        "LOAN_APPROVED",
        "LOAN_REJECTED",
        "PROPERTY_TRANSFER_PENDING",
        "COMPLETED",
        "FAILED_COMPENSATED"
    ]
    current_step: int
    data: HousingPurchaseSagaDataDTO
    start_tick: int

# Interfaces

class ILoanMarket(ABC):
    """
    Interface for the LoanMarket, now including regulatory checks.
    """
    @abstractmethod
    def apply_for_mortgage(self, application: MortgageApplicationRequestDTO) -> Optional[LoanDTO]:
        """
        Processes a mortgage application.
        - Enforces hard LTV/DTI limits from SimulationConfig.
        - Returns a new LoanDTO if approved, None otherwise.
        """
        ...

    @abstractmethod
    def evaluate_mortgage_application(self, application: MortgageApplicationRequestDTO) -> bool:
        """
        Performs hard LTV/DTI checks. Returns True if approved, False if rejected.
        """
        ...

class ISettlementSystem(ABC):
    """
    Interface for the system that guarantees atomic, multi-step transactions.
    """
    @abstractmethod
    def submit_saga(self, saga: HousingPurchaseSagaDTO) -> bool:
        """
        Submits a new saga to be processed.
        """
        ...

    @abstractmethod
    def process_sagas(self, tick: int) -> None:
        """
        Processes active sagas.
        """
        ...
