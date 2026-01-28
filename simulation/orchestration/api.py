from __future__ import annotations
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState

class IPhaseStrategy(Protocol):
    """Interface for a single phase of the simulation tick."""

    def execute(self, state: SimulationState) -> SimulationState:
        """
        Executes the logic for this phase.

        Args:
            state: The current simulation state DTO for the tick.

        Returns:
            The potentially modified simulation state DTO.
        """
        ...
