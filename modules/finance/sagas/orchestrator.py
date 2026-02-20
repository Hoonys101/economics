from typing import Dict, Any, Optional, cast
from uuid import UUID
import logging

from modules.finance.kernel.api import ISagaOrchestrator, IHousingTransactionSagaHandler, IMonetaryLedger
from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO
from modules.finance.saga_handler import HousingTransactionSagaHandler
from modules.simulation.api import ISimulationState, IAgent, IGovernment

logger = logging.getLogger(__name__)

class SagaOrchestrator(ISagaOrchestrator):
    """
    Manages the lifecycle of long-running business transactions (Sagas).
    Extracts saga logic from SettlementSystem.
    """

    def __init__(self, monetary_ledger: Optional[IMonetaryLedger] = None):
        self.active_sagas: Dict[UUID, HousingTransactionSagaStateDTO] = {}
        self.monetary_ledger = monetary_ledger
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
        """
        if not saga:
            return False
        
        # Handle dict case for flexibility
        if isinstance(saga, dict):
            saga_id = saga.get('saga_id')
        else:
            saga_id = getattr(saga, 'saga_id', None)
            
        if not saga_id:
            return False

        # saga_id is already extracted safely above
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
        for saga_id, saga_val in list(self.active_sagas.items()):
            try:
                # 1. DTO Conversion if needed (for dict-based test payloads)
                saga: Any = saga_val
                if isinstance(saga, dict):
                    # Minimal conversion for compatibility with handler
                    # Handler uses .status, .saga_id, .buyer_context, .seller_context
                    
                    # Convert contexts
                    def make_ctx(cid):
                        if cid is None: return None
                        # Mock context that matches HouseholdSnapshotDTO property access
                        from types import SimpleNamespace
                        return SimpleNamespace(household_id=cid, id=cid)

                    # Update dict with what handler needs if missing
                    if 'buyer_context' not in saga:
                        saga['buyer_context'] = make_ctx(saga.get('buyer_id'))
                    if 'seller_context' not in saga:
                        saga['seller_context'] = make_ctx(saga.get('seller_id'))
                    
                    # Try to create DTO
                    try:
                        saga_obj = HousingTransactionSagaStateDTO(**saga)
                        saga = saga_obj
                    except Exception:
                        # Fallback: keep as dict or SimpleNamespace
                        pass

                # 2. Agent Liveness Check
                # Extract IDs safely
                buyer_id = None
                seller_id = None
                status = "UNKNOWN"

                if isinstance(saga, dict):
                    buyer_id = saga.get('buyer_id')
                    seller_id = saga.get('seller_id')
                    status = saga.get('status', "UNKNOWN")
                else:
                    # DTO or SimpleNamespace
                    try:
                        buyer_id = int(saga.buyer_context.household_id)
                        seller_id = saga.seller_context.id
                        status = saga.status
                    except (AttributeError, TypeError):
                        buyer_id = getattr(saga, 'buyer_id', None)
                        seller_id = getattr(saga, 'seller_id', None)
                        status = getattr(saga, 'status', "UNKNOWN")

                if buyer_id is None or seller_id is None:
                    logger.warning(f"SAGA_SKIP | Saga {saga_id} missing participant IDs.")
                    continue

                buyer = sim_state.agents.get(buyer_id)
                seller = sim_state.agents.get(seller_id)

                is_buyer_inactive = not buyer or not buyer.is_active
                is_seller_inactive = not seller or not seller.is_active

                # Special handling for System/Government agents
                if seller_id == -1:
                    is_seller_inactive = False
                elif seller and isinstance(seller, IGovernment):
                    is_seller_inactive = False
                # Fallback check for Government singleton via simulation state
                if not seller and sim_state.government and hasattr(sim_state.government, 'id') and sim_state.government.id == seller_id:
                    is_seller_inactive = False

                if is_buyer_inactive or is_seller_inactive:
                    if isinstance(saga, dict):
                        saga['status'] = "CANCELLED"
                        if saga.get('logs') is None:
                            saga['logs'] = []
                        saga['logs'].append("Cancelled due to inactive participant.")
                    else:
                        saga.status = "CANCELLED"
                        if not hasattr(saga, 'logs') or saga.logs is None:
                            saga.logs = []
                        saga.logs.append("Cancelled due to inactive participant.")

                    logger.warning(
                         f"SAGA_CANCELLED | Saga {saga_id} cancelled due to inactive participant. "
                         f"Buyer Active: {not is_buyer_inactive}, Seller Active: {not is_seller_inactive}",
                         extra={"saga_id": str(saga_id)}
                    )

                    # Attempt compensation if funds might be locked
                    # Use status variable defined above
                    if status not in ["INITIATED", "STARTED", "PENDING_OFFER"]:
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
                if isinstance(updated_saga, dict):
                    status = updated_saga.get('status')
                else:
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

    def get_active_sagas(self) -> Dict[UUID, HousingTransactionSagaStateDTO]:
        return self.active_sagas
