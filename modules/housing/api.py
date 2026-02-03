from abc import ABC, abstractmethod
from modules.housing.dtos import HousingDecisionRequestDTO, HousingDecisionDTO, HousingTransactionSagaStateDTO

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
