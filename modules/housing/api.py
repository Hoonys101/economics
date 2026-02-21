from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING, List, Any
from uuid import UUID

from modules.finance.api import LienDTO
from modules.market.housing_planner_api import HousingDecisionRequestDTO, HousingDecisionDTO
from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.models import Transaction

class IHousingPlanner(ABC):
    """
    Stateless interface for making a high-level housing recommendation.
    """
    @abstractmethod
    def evaluate_housing_options(self, request: HousingDecisionRequestDTO) -> HousingDecisionDTO:
        """
        Analyzes market and household state to recommend an action.
        Does NOT orchestrate the transaction.
        """
        ...

class IHousingTransactionSagaHandler(ABC):
    """
    Stateless handler for executing the housing purchase saga.
    This is the core orchestrator, replacing logic previously in DecisionUnit.
    """
    @abstractmethod
    def execute_step(self, saga_state: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        """
        Executes the next step of the saga based on its current status.
        This method is idempotent and handles all financial operations
        via the SettlementSystem, including rollbacks.
        """
        ...

class IHousingService(ABC):
    """
    Manages the lifecycle and state of all real estate and housing units.
    This service is the single source of truth for ownership, liens,
    and contractual status of properties.
    """

    @abstractmethod
    def set_real_estate_units(self, units: List[Any]) -> None:
        """Sets the reference to the list of real estate units."""
        ...

    @abstractmethod
    def process_transaction(self, tx: "Transaction", state: "SimulationState") -> None:
        """
        Primary entry point to process a housing-related transaction and update
        the state of real estate units, owners, and occupants.
        This replaces the logic previously in Registry._handle_housing_registry.
        """
        ...

    @abstractmethod
    def is_under_contract(self, property_id: int) -> bool:
        """Checks if a property is currently locked by a purchase saga."""
        ...

    @abstractmethod
    def set_under_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Locks a property for a purchase saga."""
        ...

    @abstractmethod
    def release_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Releases a property lock from a purchase saga."""
        ...

    @abstractmethod
    def add_lien(self, property_id: int, loan_id: str, lienholder_id: int, principal: int) -> Optional[str]:
        """Adds a lien (e.g., a mortgage) to a property. Principal in pennies."""
        ...

    @abstractmethod
    def remove_lien(self, property_id: int, lien_id: str) -> bool:
        """Removes a lien from a property."""
        ...

    @abstractmethod
    def transfer_ownership(self, property_id: int, new_owner_id: int) -> bool:
        """Transfers ownership of a property."""
        ...
