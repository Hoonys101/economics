from dataclasses import dataclass
from modules.finance.api import MortgageApplicationDTO as MortgageApplicationDTO
from modules.simulation.api import HouseholdSnapshotDTO as HouseholdSnapshotDTO
from typing import Literal, Protocol
from uuid import UUID

@dataclass(frozen=True)
class MortgageApprovalDTO:
    """
    Represents the confirmed details of an approved mortgage.
    """
    loan_id: str
    lien_id: str
    approved_principal: float
    monthly_payment: float

@dataclass(frozen=True)
class HousingSagaAgentContext:
    id: int
    monthly_income: float
    existing_monthly_debt: float

@dataclass
class HousingTransactionSagaStateDTO:
    """
    State object for the multi-tick housing purchase Saga.
    This object is persisted across ticks to manage the transaction lifecycle.
    """
    saga_id: UUID
    status: Literal['INITIATED', 'CREDIT_CHECK', 'APPROVED', 'ESCROW_LOCKED', 'TRANSFER_TITLE', 'COMPLETED', 'FAILED_ROLLED_BACK', 'CANCELLED']
    buyer_context: HouseholdSnapshotDTO
    seller_context: HousingSagaAgentContext
    property_id: int
    offer_price: float
    down_payment_amount: float
    loan_application: MortgageApplicationDTO | None = ...
    mortgage_approval: MortgageApprovalDTO | None = ...
    staged_loan_id: str | None = ...
    error_message: str | None = ...
    last_processed_tick: int = ...
    logs: list[str] = ...

class IProperty(Protocol):
    id: int
    owner_id: int
    is_under_contract: bool
    liens: list[str]

class IPropertyRegistry(Protocol):
    """
    Interface for a system managing property ownership and status.
    Alias or refinement of IRealEstateRegistry for the Saga context.
    """
    def set_under_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Locks a property, preventing other sales. Returns False if already locked."""
    def release_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Releases the lock on a property."""
    def add_lien(self, property_id: int, loan_id: str) -> str | None:
        """Adds a lien to a property, returns a unique lien_id."""
    def remove_lien(self, property_id: int, lien_id: str) -> bool:
        """Removes a lien from a property."""
    def transfer_ownership(self, property_id: int, new_owner_id: int) -> bool:
        """Finalizes the transfer of the property."""

class ILoanMarket(Protocol):
    """
    Interface for the loan market.
    """
    def stage_mortgage_application(self, application: MortgageApplicationDTO) -> str | None:
        """
        Submits an application for asynchronous credit check.
        Returns a unique `staged_loan_id` for tracking, or None if invalid.
        """
    def check_staged_application_status(self, staged_loan_id: str) -> Literal['PENDING', 'APPROVED', 'REJECTED']:
        """Checks the status of a pending mortgage application."""
    def convert_staged_to_loan(self, staged_loan_id: str) -> MortgageApprovalDTO | None:
        """
        Finalizes an approved application, creating an official loan and lien.
        Returns the final loan details or None on failure.
        """
    def void_staged_application(self, staged_loan_id: str) -> bool:
        """Cancels a pending or approved application before funds are disbursed."""

class IHousingTransactionSagaHandler(Protocol):
    """
    The refactored Saga Handler, now a state machine processor.
    """
    def execute_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        """Processes a single step of the saga based on its current status."""
    def compensate_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        """Triggers the rollback/compensation logic for the saga's current status."""

class ISagaManager(Protocol):
    """
    A new system responsible for managing all active sagas.
    """
    def process_sagas(self) -> None:
        """Iterates through all active sagas and executes the next step."""
    def register_saga(self, saga_state: HousingTransactionSagaStateDTO) -> None:
        """Adds a new saga to the manager."""
    def find_and_compensate_by_agent(self, agent_id: int) -> None:
        """Finds all sagas involving a specific agent and triggers their compensation."""
