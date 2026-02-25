from _typeshed import Incomplete
from modules.finance.kernel.api import IHousingTransactionSagaHandler as IHousingTransactionSagaHandler, IMonetaryLedger as IMonetaryLedger, ISagaOrchestrator as ISagaOrchestrator
from modules.finance.saga_handler import HousingTransactionSagaHandler as HousingTransactionSagaHandler
from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO as HousingTransactionSagaStateDTO
from modules.government.api import IGovernment as IGovernment
from modules.simulation.api import HouseholdSnapshotDTO as HouseholdSnapshotDTO, IAgent as IAgent, ISimulationState as ISimulationState
from modules.system.api import IAgentRegistry as IAgentRegistry
from uuid import UUID

logger: Incomplete

class SagaOrchestrator(ISagaOrchestrator):
    """
    Manages the lifecycle of long-running business transactions (Sagas).
    Extracts saga logic from SettlementSystem.
    Strictly enforces HousingTransactionSagaStateDTO usage.
    """
    active_sagas: dict[UUID, HousingTransactionSagaStateDTO]
    monetary_ledger: Incomplete
    agent_registry: Incomplete
    def __init__(self, monetary_ledger: IMonetaryLedger | None = None, agent_registry: IAgentRegistry | None = None) -> None: ...
    @property
    def simulation_state(self) -> ISimulationState | None: ...
    @simulation_state.setter
    def simulation_state(self, value: ISimulationState): ...
    def submit_saga(self, saga: HousingTransactionSagaStateDTO) -> bool:
        """
        Submits a new saga to be processed.
        Strictly accepts HousingTransactionSagaStateDTO.
        """
    def process_sagas(self) -> None:
        """
        Processes active sagas. Implements the Housing Transaction Saga state machine.
        Called by TickOrchestrator (via Phase_HousingSaga).
        """
    def find_and_compensate_by_agent(self, agent_id: int, handler: IHousingTransactionSagaHandler) -> None:
        """
        Finds all sagas involving a specific agent and triggers their compensation.
        """
    def get_active_sagas(self) -> dict[UUID, HousingTransactionSagaStateDTO]: ...
