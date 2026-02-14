from typing import List, Protocol, runtime_checkable
from simulation.dtos.commands import GodCommandDTO, GodResponseDTO

class ICommandService(Protocol):
    def execute_command_batch(self, commands: List[GodCommandDTO], tick: int, baseline_m2: int) -> List[GodResponseDTO]:
        ...
    def commit_last_tick(self) -> None:
        ...

@runtime_checkable
class ISectorAgent(Protocol):
    sector: str
