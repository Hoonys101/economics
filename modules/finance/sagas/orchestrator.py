from typing import Dict, Any, Optional, cast
from uuid import UUID
import logging

from modules.finance.kernel.api import ISagaOrchestrator, IHousingTransactionSagaHandler, IMonetaryLedger
from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO
from modules.finance.saga_handler import HousingTransactionSagaHandler
from modules.simulation.api import ISimulationState, IAgent, HouseholdSnapshotDTO
from modules.government.api import IGovernment
from modules.system.api import IAgentRegistry

logger = logging.getLogger(__name__)

class SagaOrchestrator(ISagaOrchestrator):
    """
    Manages the lifecycle of long-running business transactions (Sagas).
    Extracts saga logic from SettlementSystem.
    Strictly enforces HousingTransactionSagaStateDTO usage.
    """

    def __init__(self, monetary_ledger: Optional[IMonetaryLedger] = None, agent_registry: Optional[IAgentRegistry] = None):
        self.active_sagas: Dict[UUID, HousingTransactionSagaStateDTO] = {}
        self.monetary_ledger = monetary_ledger
        self.agent_registry = agent_registry
        self._simulation_state: Optional[ISimulationState] = None

    @property
    def simulation_state(self) -> Optional[ISimulationState]:
        return self._simulation_state

    @simulation_state.setter
    def simulation_state(self, value: ISimulationState):
        self._simulation_state = value

    def submit_saga(self, saga: HousingTransactionSagaStateDTO) -> bool:
        """
        Submits a new saga to be processed.
        Strictly accepts HousingTransactionSagaStateDTO.
        """
        if not saga:
            return False
        
        if not isinstance(saga, HousingTransactionSagaStateDTO):
            logger.error(f"SAGA_SUBMIT_FAIL | Invalid saga type: {type(saga)}. Expected HousingTransactionSagaStateDTO.")
            return False

        saga_id = saga.saga_id
        if not saga_id:
            return False

        # Validate Critical IDs
        if not saga.buyer_context.household_id:
            logger.error(f"SAGA_SUBMIT_FAIL | Saga {saga_id} missing buyer ID.")
            return False

        if saga.seller_context.id is None:
            logger.error(f"SAGA_SUBMIT_FAIL | Saga {saga_id} missing seller ID.")
            return False

        self.active_sagas[saga_id] = saga
        logger.info(
            f"SAGA_SUBMITTED | Saga {saga_id} submitted.",
            extra={"saga_id": str(saga_id)}
        )
        return True

    def process_sagas(self) -> None:
        """
        Processes active sagas. Implements the Housing Transaction Saga state machine.
        Called by TickOrchestrator (via Phase_HousingSaga).
        """
        if not self.active_sagas or not self.simulation_state:
            return

        sim_state = self.simulation_state

        # Initialize Handler with the current simulation state
        handler = HousingTransactionSagaHandler(sim_state)

        # Inject MonetaryLedger
        if self.monetary_ledger:
            handler.monetary_ledger = self.monetary_ledger

        # Iterate over copy to allow modification/deletion
        for saga_id, saga in list(self.active_sagas.items()):
            try:
                # 1. Agent Liveness Check
                # Extract IDs strictly from DTO
                buyer_id_raw = saga.buyer_context.household_id
                seller_id = saga.seller_context.id
                status = saga.status

                try:
                    buyer_id = int(buyer_id_raw)
                except (ValueError, TypeError):
                    logger.error(f"SAGA_CANCELLED | Saga {saga_id} has invalid buyer ID: {buyer_id_raw}")
                    if saga_id in self.active_sagas:
                        del self.active_sagas[saga_id]
                    continue

                if seller_id is None:
                    logger.warning(f"SAGA_CANCELLED | Saga {saga_id} missing seller ID.")
                    if saga_id in self.active_sagas:
                        del self.active_sagas[saga_id]
                    continue

                is_buyer_inactive = False
                is_seller_inactive = False

                if self.agent_registry:
                    is_buyer_inactive = not self.agent_registry.is_agent_active(buyer_id)

                    # Special handling for System Agents or Genesis (-1)
                    if seller_id == -1:
                        is_seller_inactive = False
                    else:
                        is_seller_inactive = not self.agent_registry.is_agent_active(seller_id)
                else:
                    # Fallback Logic (Legacy)
                    buyer = sim_state.agents.get(buyer_id)
                    seller = sim_state.agents.get(seller_id)

                    is_buyer_inactive = not buyer or not getattr(buyer, 'is_active', False)
                    is_seller_inactive = not seller or not getattr(seller, 'is_active', False)

                    # Special handling for System/Government agents
                    if seller_id == -1:
                        is_seller_inactive = False
                    elif seller and isinstance(seller, IGovernment):
                        is_seller_inactive = False

                    # Fallback check for Government singleton via simulation state
                    if not seller and sim_state.government and hasattr(sim_state.government, 'id') and sim_state.government.id == seller_id:
                        is_seller_inactive = False

                if is_buyer_inactive or is_seller_inactive:
                    saga.status = "CANCELLED"
                    if not saga.logs:
                        saga.logs = []
                    saga.logs.append("Cancelled due to inactive participant.")

                    logger.info(
                         f"SAGA_CLEANUP | Saga {saga_id} cancelled due to inactive participant. "
                         f"Buyer Active: {not is_buyer_inactive}, Seller Active: {not is_seller_inactive}",
                         extra={"saga_id": str(saga_id)}
                    )

                    # Attempt compensation if funds might be locked
                    if status not in ["INITIATED", "STARTED", "PENDING_OFFER"]:
                         try:
                             handler.compensate_step(saga)
                         except Exception as comp_err:
                             logger.error(f"SAGA_COMPENSATE_FAIL | {comp_err}", extra={"saga_id": str(saga_id)})

                    if saga_id in self.active_sagas:
                        del self.active_sagas[saga_id]
                    continue

                # 2. Execute Step
                updated_saga = handler.execute_step(saga)
                self.active_sagas[saga_id] = updated_saga

                # 3. Cleanup Terminal States
                status = updated_saga.status

                if status == "COMPLETED":
                    logger.info(f"SAGA_ARCHIVED | Saga {saga_id} completed successfully.")
                    del self.active_sagas[saga_id]
                elif status == "FAILED_ROLLED_BACK":
                    logger.info(f"SAGA_ARCHIVED | Saga {saga_id} ended with {status}.")
                    del self.active_sagas[saga_id]

            except Exception as e:
                logger.error(f"SAGA_PROCESS_ERROR | Saga {saga_id} failed. {e}")
                # Try to compensate
                try:
                    handler.compensate_step(saga)
                except Exception:
                    pass
                if saga_id in self.active_sagas:
                    del self.active_sagas[saga_id]

    def find_and_compensate_by_agent(self, agent_id: int, handler: IHousingTransactionSagaHandler) -> None:
        """
        Finds all sagas involving a specific agent and triggers their compensation.
        """
        if not self.active_sagas:
            return

        if not handler:
             logger.error("SAGA_COMPENSATE_FAIL | No handler provided for find_and_compensate_by_agent")
             return

        for saga_id, saga in list(self.active_sagas.items()):
            try:
                buyer_id = int(saga.buyer_context.household_id)
                seller_id = saga.seller_context.id

                if buyer_id == agent_id or seller_id == agent_id:
                    logger.warning(f"SAGA_AGENT_DEATH | Triggering compensation for Saga {saga_id} due to agent {agent_id} death.")
                    try:
                        updated_saga = handler.compensate_step(saga)
                        if updated_saga.status == "FAILED_ROLLED_BACK":
                            del self.active_sagas[saga_id]
                    except Exception as e:
                        logger.critical(f"SAGA_AGENT_DEATH_FAIL | Failed to compensate saga {saga_id}. {e}")
            except (ValueError, TypeError, AttributeError):
                continue

    def get_active_sagas(self) -> Dict[UUID, HousingTransactionSagaStateDTO]:
        return self.active_sagas
