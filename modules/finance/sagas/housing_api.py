from typing import TypedDict, Literal, Optional, Protocol, List, Dict
from uuid import UUID
from dataclasses import dataclass

from modules.market.housing_planner_api import MortgageApplicationDTO

# --- DTOs for Saga State & Payloads ---

class MortgageApprovalDTO(TypedDict):
    """
    Represents the confirmed details of an approved mortgage.
    """
    loan_id: str  # Bank-issued unique loan identifier (string)
    lien_id: str  # Registry-issued unique lien identifier
    approved_principal: float
    monthly_payment: float

class HousingSagaAgentContext(TypedDict):
    id: int
    monthly_income: float
    existing_monthly_debt: float

class HousingTransactionSagaStateDTO(TypedDict):
    """
    State object for the multi-tick housing purchase Saga.
    This object is persisted across ticks to manage the transaction lifecycle.
    """
    saga_id: UUID
    status: Literal[
        # Staging & Validation
        "INITIATED",            # -> Awaiting credit check
        "CREDIT_CHECK",         # -> Loan Approved or Rejected
        "APPROVED",             # -> Awaiting funds lock in escrow
        # Execution & Settlement
        "ESCROW_LOCKED",        # -> Awaiting final title transfer
        "TRANSFER_TITLE",       # -> Completed or Failed
        # Terminal States
        "COMPLETED",
        "FAILED_ROLLED_BACK"
    ]
    buyer_context: HousingSagaAgentContext
    seller_context: HousingSagaAgentContext
    property_id: int
    offer_price: float
    down_payment_amount: float

    # State-specific payloads, populated as the saga progresses
    loan_application: Optional[MortgageApplicationDTO]
    mortgage_approval: Optional[MortgageApprovalDTO]

    # Tracking IDs for compensation
    staged_loan_id: Optional[str]

    # Error logging
    error_message: Optional[str]
    last_processed_tick: int

# --- System Interfaces ---

class IProperty(Protocol):
    id: int
    owner_id: int
    is_under_contract: bool
    liens: List[str]

class IPropertyRegistry(Protocol):
    """
    Interface for a system managing property ownership and status.
    Alias or refinement of IRealEstateRegistry for the Saga context.
    """
    def set_under_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Locks a property, preventing other sales. Returns False if already locked."""
        ...

    def release_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Releases the lock on a property."""
        ...

    def add_lien(self, property_id: int, loan_id: str) -> Optional[str]:
        """Adds a lien to a property, returns a unique lien_id."""
        ...

    def remove_lien(self, property_id: int, lien_id: str) -> bool:
        """Removes a lien from a property."""
        ...

    def transfer_ownership(self, property_id: int, new_owner_id: int) -> bool:
        """Finalizes the transfer of the property."""
        ...

class ILoanMarket(Protocol):
    """
    Interface for the loan market.
    """
    def stage_mortgage_application(self, application: MortgageApplicationDTO) -> Optional[str]:
        """
        Submits an application for asynchronous credit check.
        Returns a unique `staged_loan_id` for tracking, or None if invalid.
        """
        ...

    def check_staged_application_status(self, staged_loan_id: str) -> Literal["PENDING", "APPROVED", "REJECTED"]:
        """Checks the status of a pending mortgage application."""
        ...

    def convert_staged_to_loan(self, staged_loan_id: str) -> Optional[MortgageApprovalDTO]:
        """
        Finalizes an approved application, creating an official loan and lien.
        Returns the final loan details or None on failure.
        """
        ...

    def void_staged_application(self, staged_loan_id: str) -> bool:
        """Cancels a pending or approved application before funds are disbursed."""
        ...

class IHousingTransactionSagaHandler(Protocol):
    """
    The refactored Saga Handler, now a state machine processor.
    """
    def execute_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        """Processes a single step of the saga based on its current status."""
        ...

    def compensate_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        """Triggers the rollback/compensation logic for the saga's current status."""
        ...

class ISagaManager(Protocol):
    """
    A new system responsible for managing all active sagas.
    """
    def process_sagas(self) -> None:
        """Iterates through all active sagas and executes the next step."""
        ...

    def register_saga(self, saga_state: HousingTransactionSagaStateDTO) -> None:
        """Adds a new saga to the manager."""
        ...

    def find_and_compensate_by_agent(self, agent_id: int) -> None:
        """Finds all sagas involving a specific agent and triggers their compensation."""
        ...
