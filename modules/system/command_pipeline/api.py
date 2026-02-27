from __future__ import annotations
from typing import List, Protocol, runtime_checkable, Any
from dataclasses import dataclass, field
from simulation.dtos.commands import GodCommandDTO
from modules.governance.api import SystemCommand
from modules.governance.cockpit.api import CockpitCommand
from simulation.dtos.api import CommandBatchDTO

@runtime_checkable
class ICommandIngressService(Protocol):
    def enqueue_command(self, command: CockpitCommand) -> None:
        """
        Ingests a raw CockpitCommand, validates it, maps it to internal DTOs,
        and buffers it for the next tick.
        """
        ...

    def drain_for_tick(self, tick: int) -> CommandBatchDTO:
        """
        Atomically drains all buffered TICK commands and returns a frozen batch for the given tick.
        Does NOT include Control commands (PAUSE/RESUME/STEP).
        """
        ...

    def drain_control_commands(self) -> List[GodCommandDTO]:
        """
        Drains pending Control commands (PAUSE, RESUME, STEP).
        These should be processed immediately by the Engine loop.
        """
        ...
