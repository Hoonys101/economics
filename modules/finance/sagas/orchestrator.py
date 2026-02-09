from typing import Dict, Any, Optional, cast
from uuid import UUID
import logging

from modules.finance.kernel.api import ISagaOrchestrator, IHousingTransactionSagaHandler, IMonetaryLedger
from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO
from modules.finance.saga_handler import HousingTransactionSagaHandler

logger = logging.getLogger(__name__)

class SagaOrchestrator(ISagaOrchestrator):
    """
    Manages the lifecycle of long-running business transactions (Sagas).
    Extracts saga logic from SettlementSystem.
    """

    def __init__(self, monetary_ledger: Optional[IMonetaryLedger] = None):
        self.active_sagas: Dict[UUID, HousingTransactionSagaStateDTO] = {}
        self.monetary_ledger = monetary_ledger

    def submit_saga(self, saga: HousingTransactionSagaStateDTO) -> bool:
        """
        Submits a new saga to be processed.
        """
        if not saga or 'saga_id' not in saga:
            return False

        # Ensure ID is handled as UUID if possible, but dict key usage prevails
        saga_id = saga['saga_id']
        self.active_sagas[saga_id] = saga
        logger.info(
            f"SAGA_SUBMITTED | Saga {saga_id} submitted.",
            extra={"saga_id": str(saga_id)}
        )
        return True

    def process_sagas(self, simulation_state: Any) -> None:
        """
        Processes active sagas. Implements the Housing Transaction Saga state machine.
        Called by TickOrchestrator (via Phase_HousingSaga).
        """
        if not self.active_sagas:
            return

        # Initialize Handler with the current simulation state
        handler = HousingTransactionSagaHandler(simulation_state)

        # Inject MonetaryLedger if the handler supports it (we will refactor handler later to use it)
        # For now, the handler might still use legacy methods, but we'll prepare for injection.
        if hasattr(handler, 'monetary_ledger') and self.monetary_ledger:
            handler.monetary_ledger = self.monetary_ledger

        # Iterate over copy to allow modification/deletion
        for saga_id, saga in list(self.active_sagas.items()):
            try:
                # 1. Agent Liveness Check
                buyer = simulation_state.agents.get(saga['buyer_id'])
                seller = simulation_state.agents.get(saga['seller_id'])

                is_buyer_inactive = not buyer or not getattr(buyer, 'is_active', False)
                is_seller_inactive = not seller or not getattr(seller, 'is_active', False)

                # Special handling for System/Government agents
                if saga['seller_id'] == -1:
                    is_seller_inactive = False
                elif seller and hasattr(seller, 'agent_type') and seller.agent_type == 'government':
                    is_seller_inactive = False
                # Fallback check for Government singleton
                if not seller and hasattr(simulation_state, 'government') and simulation_state.government.id == saga['seller_id']:
                    is_seller_inactive = False

                if is_buyer_inactive or is_seller_inactive:
                    saga['status'] = "CANCELLED"
                    if 'logs' in saga and isinstance(saga['logs'], list):
                        saga['logs'].append("Cancelled due to inactive participant.")

                    logger.warning(
                         f"SAGA_CANCELLED | Saga {saga_id} cancelled due to inactive participant. "
                         f"Buyer Active: {not is_buyer_inactive}, Seller Active: {not is_seller_inactive}",
                         extra={"saga_id": str(saga_id)}
                    )

                    # Attempt compensation if funds might be locked
                    if saga['status'] not in ["INITIATED", "STARTED", "PENDING_OFFER"]:
                         try:
                             handler.compensate_step(saga)
                         except Exception as comp_err:
                             logger.error(f"SAGA_COMPENSATE_FAIL | {comp_err}")

                    del self.active_sagas[saga_id]
                    continue

                # 2. Execute Step
                updated_saga = handler.execute_step(saga)
                self.active_sagas[saga_id] = updated_saga

                # 3. Cleanup Terminal States
                status = updated_saga['status']
                if status == "COMPLETED":
                    logger.info(f"SAGA_ARCHIVED | Saga {saga_id} completed successfully.")
                    del self.active_sagas[saga_id]
                elif status == "FAILED_ROLLED_BACK":
                    logger.info(f"SAGA_ARCHIVED | Saga {saga_id} ended with {status}.")
                    # Keep it in active_sagas for inspection or delete?
                    # Original logic deleted it. But test expects it to remain?
                    # Wait, test asserts: assert saga_id in orchestrator.active_sagas
                    # So for testing purposes, we might want to keep failed ones?
                    # Or fix the test?
                    # If failed/rolled back, it is technically done.
                    # But if the test expects it to be there, maybe it expects a different status?
                    # The test expects CREDIT_CHECK.
                    # If it rolled back, it means execute_step failed.

                    # If execute_step failed, it means mock setup was insufficient.
                    # We should fix the test setup or understand why it failed.

                    # Deleting failed sagas is correct behavior for production cleanup.
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
            if saga['buyer_id'] == agent_id or saga['seller_id'] == agent_id:
                logger.warning(f"SAGA_AGENT_DEATH | Triggering compensation for Saga {saga_id} due to agent {agent_id} death.")
                try:
                    updated_saga = handler.compensate_step(saga)
                    if updated_saga['status'] == "FAILED_ROLLED_BACK":
                        del self.active_sagas[saga_id]
                except Exception as e:
                    logger.critical(f"SAGA_AGENT_DEATH_FAIL | Failed to compensate saga {saga_id}. {e}")

    def get_active_sagas(self) -> Dict[UUID, HousingTransactionSagaStateDTO]:
        return self.active_sagas
