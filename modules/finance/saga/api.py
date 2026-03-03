from __future__ import annotations
from typing import List, Protocol, runtime_checkable, Dict, Any
from dataclasses import dataclass
from uuid import UUID

from modules.system.api import AgentID, IAgentRegistry
from modules.finance.api import SagaStateDTO
from modules.finance.kernel.api import ISagaOrchestrator

@dataclass(frozen=True)
class OrphanedSagaDTO:
    """DTO representing a saga identified for purging due to dead participants."""
    saga_id: UUID
    dead_participant_ids: List[AgentID]
    state: str
    last_updated_tick: int

@runtime_checkable
class ISagaRepository(Protocol):
    """Provides read-only access to saga states. Separates data fetching from execution."""
    def get_all_active_sagas(self) -> List[SagaStateDTO]:
        """Returns a list of all currently active (non-terminal) sagas."""
        ...

@runtime_checkable
class ISagaCaretaker(Protocol):
    """
    Analyzes active sagas and identifies those with stale/dead agents.
    Commands the orchestrator to purge them, ensuring no direct state mutation.
    """
    def sweep_orphaned_sagas(self, current_tick: int) -> List[OrphanedSagaDTO]:
        """
        Scans all active sagas, identifies orphans via IAgentRegistry,
        and triggers orchestrator compensation. Returns a list of swept sagas for logging.
        """
        ...
