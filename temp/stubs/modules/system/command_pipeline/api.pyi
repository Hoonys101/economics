from dataclasses import dataclass, field
from modules.governance.api import SystemCommand as SystemCommand
from modules.governance.cockpit.api import CockpitCommand as CockpitCommand
from simulation.dtos.commands import GodCommandDTO as GodCommandDTO
from typing import Protocol

@dataclass
class CommandBatchDTO:
    tick: int
    god_commands: list[GodCommandDTO] = field(default_factory=list)
    system_commands: list[SystemCommand] = field(default_factory=list)

class ICommandIngressService(Protocol):
    def enqueue_command(self, command: CockpitCommand) -> None:
        """
        Ingests a raw CockpitCommand, validates it, maps it to internal DTOs,
        and buffers it for the next tick.
        """
    def drain_for_tick(self, tick: int) -> CommandBatchDTO:
        """
        Atomically drains all buffered TICK commands and returns a frozen batch for the given tick.
        Does NOT include Control commands (PAUSE/RESUME/STEP).
        """
    def drain_control_commands(self) -> list[GodCommandDTO]:
        """
        Drains pending Control commands (PAUSE, RESUME, STEP).
        These should be processed immediately by the Engine loop.
        """
