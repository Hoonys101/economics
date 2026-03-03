import logging
from typing import List
from uuid import UUID

from modules.finance.saga.api import ISagaCaretaker, ISagaRepository, ISagaOrchestrator, OrphanedSagaDTO
from modules.system.api import IAgentRegistry, AgentID
from modules.finance.api import SagaStateDTO

logger = logging.getLogger(__name__)

class SagaCaretaker:
    """
    Acts as a garbage collector for the Saga Orchestration system.
    Observes active transactions via ISagaRepository, queries IAgentRegistry
    to verify participant vitality, and commands ISagaOrchestrator to execute
    safe compensations if participants are dead/stale.
    """
    def __init__(self, saga_repository: ISagaRepository, saga_orchestrator: ISagaOrchestrator, agent_registry: IAgentRegistry):
        self._saga_repository = saga_repository
        self._saga_orchestrator = saga_orchestrator
        self._agent_registry = agent_registry

    def _extract_participant_ids(self, saga: SagaStateDTO) -> List[AgentID]:
        """
        Extracts participant IDs from the unstructured payload dictionary.
        Supports both generic transaction roles (buyer_id, seller_id)
        and other potential legacy keys.
        """
        participants = set()

        if not saga.payload:
            return []

        # Direct explicit key
        if "participant_ids" in saga.payload and isinstance(saga.payload["participant_ids"], list):
            for pid in saga.payload["participant_ids"]:
                participants.add(AgentID(int(pid)))

        # Housing specific roles
        if "buyer_id" in saga.payload:
            participants.add(AgentID(int(saga.payload["buyer_id"])))
        if "seller_id" in saga.payload:
            participants.add(AgentID(int(saga.payload["seller_id"])))

        # Bond/Financial roles
        if "issuer_id" in saga.payload:
            participants.add(AgentID(int(saga.payload["issuer_id"])))
        if "investor_id" in saga.payload:
            participants.add(AgentID(int(saga.payload["investor_id"])))

        return list(participants)

    def sweep_orphaned_sagas(self, current_tick: int) -> List[OrphanedSagaDTO]:
        purged_sagas: List[OrphanedSagaDTO] = []

        active_sagas = self._saga_repository.get_all_active_sagas()

        for saga in active_sagas:
            if saga.state in ("FAILED", "COMPLETED", "COMPENSATING", "COMPENSATED"):
                continue

            participant_ids = self._extract_participant_ids(saga)
            if not participant_ids:
                logger.warning(f"SagaCaretaker: Could not extract participant IDs for saga {saga.saga_id}.")
                continue

            dead_agents = []
            for agent_id in participant_ids:
                if not self._agent_registry.is_agent_active(agent_id):
                    dead_agents.append(agent_id)

            if dead_agents:
                try:
                    reason = f"Participant(s) Dead: {dead_agents}"
                    self._saga_orchestrator.compensate_and_fail_saga(saga.saga_id, reason)

                    orphaned_dto = OrphanedSagaDTO(
                        saga_id=saga.saga_id,
                        dead_participant_ids=dead_agents,
                        state="COMPENSATING",
                        last_updated_tick=current_tick
                    )
                    purged_sagas.append(orphaned_dto)
                    logger.info(f"SagaCaretaker: Purged orphaned saga {saga.saga_id} due to dead agents: {dead_agents}")
                except Exception as e:
                    logger.error(f"SagaCaretaker: Failed to compensate orphaned saga {saga.saga_id} safely. Error: {e}")

        return purged_sagas

# Verify protocol implementation
_caretaker: ISagaCaretaker = SagaCaretaker(None, None, None) # type: ignore
