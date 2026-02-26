from _typeshed import Incomplete
from dataclasses import dataclass, field as field
from modules.api.protocols import ISectorAgent as ISectorAgent
from modules.finance.api import IBank as IBank
from modules.simulation.api import IInventoryHandler as IInventoryHandler
from modules.system.api import IAgentRegistry as IAgentRegistry, IGlobalRegistry as IGlobalRegistry, IRestorableRegistry as IRestorableRegistry, OriginType as OriginType, RegistryEntry as RegistryEntry
from modules.system.constants import ID_CENTRAL_BANK as ID_CENTRAL_BANK
from simulation.dtos.commands import GodCommandDTO as GodCommandDTO, GodResponseDTO
from simulation.finance.api import IMonetaryAuthority as IMonetaryAuthority, ISettlementSystem as ISettlementSystem
from typing import Any
from uuid import UUID

logger: Incomplete

@dataclass
class UndoRecord:
    command_id: UUID
    command_type: str
    target_domain: str | None = ...
    parameter_key: str | None = ...
    previous_entry: RegistryEntry | None = ...
    target_agent_id: int | str | None = ...
    amount: int | None = ...
    new_value: Any = ...
    origin: OriginType | None = ...

class UndoStack:
    def __init__(self, maxlen: int = 50) -> None: ...
    def start_batch(self) -> None: ...
    def push(self, record: UndoRecord): ...
    def commit_batch(self) -> None: ...
    def pop_batch(self) -> list[UndoRecord]: ...

class CommandService:
    registry: Incomplete
    settlement_system: Incomplete
    agent_registry: Incomplete
    undo_stack: Incomplete
    def __init__(self, registry: IGlobalRegistry, settlement_system: IMonetaryAuthority, agent_registry: IAgentRegistry) -> None: ...
    def execute_command_batch(self, commands: list[GodCommandDTO], tick: int, baseline_m2: int) -> list[GodResponseDTO]:
        """
        Executes a batch of God-Mode commands with atomic rollback on audit failure.
        Lifecycle: Validation -> Snapshot -> Mutation -> Audit -> Commit/Rollback
        """
    def commit_last_tick(self) -> None:
        """
        Commits the last batch of commands.
        Modified for INT-02: We keep the history to allow manual UNDO (ST-004).
        Uses deque with maxlen to prevent memory leak.
        """
    def rollback_last_tick(self) -> bool: ...
