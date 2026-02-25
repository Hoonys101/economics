from simulation.dtos.commands import GodCommandDTO as GodCommandDTO, GodResponseDTO as GodResponseDTO
from typing import Protocol

class ICommandService(Protocol):
    def execute_command_batch(self, commands: list[GodCommandDTO], tick: int, baseline_m2: int) -> list[GodResponseDTO]: ...
    def commit_last_tick(self) -> None: ...

class ISectorAgent(Protocol):
    sector: str
