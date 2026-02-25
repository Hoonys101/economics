from _typeshed import Incomplete
from simulation.dtos.api import SimulationState as SimulationState
from simulation.orchestration.api import IPhaseStrategy as IPhaseStrategy
from simulation.world_state import WorldState as WorldState

logger: Incomplete

class Phase_SystemCommands(IPhaseStrategy):
    """
    Orchestration phase for executing manual system commands (Cockpit interventions).
    This phase runs early in the tick to ensure interventions apply before agent decisions.
    """
    world_state: Incomplete
    processor: Incomplete
    def __init__(self, world_state: WorldState) -> None: ...
    def execute(self, state: SimulationState) -> SimulationState: ...
